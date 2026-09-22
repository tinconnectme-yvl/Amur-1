"""
Export & Bulletin Download Router.
Provides GeoJSON polygons, zipped Shapefile packages, and official PDF/Markdown bulletins.
"""
from fastapi import APIRouter, HTTPException, Response
from pathlib import Path
import numpy as np
from backend.app.core.pipeline import HydrologicalPipeline
from backend.app.core.vector_exporter import raster_to_geojson, create_shapefile_zip
from backend.app.core.report_builder import generate_markdown_bulletin, generate_pdf_bulletin

router = APIRouter(prefix="/api/export", tags=["Export & Reports"])

DATA_DIR = Path(__file__).resolve().parents[4] / "data" / "hydrowatch_amur"
pipeline = HydrologicalPipeline(str(DATA_DIR))

# Cache vector GeoJSON to ensure fast frontend rendering
_geojson_cache = {}

@router.get("/{pair_id}/geojson")
def export_geojson(pair_id: str, layer: str = "flood"):
    """
    Returns WGS84 GeoJSON FeatureCollection for the requested layer:
    'flood' (default), 'water_pre', 'water_peak'.
    """
    cache_key = f"{pair_id}_{layer}"
    if cache_key in _geojson_cache:
        return _geojson_cache[cache_key]

    try:
        res = pipeline.process_pair(pair_id)
        if layer == "water_pre":
            # Combine pre-flood SAR water and permanent river network so full river bed is rendered in blue
            perm = res.get("mask_permanent", np.zeros_like(res["mask_pre"]))
            mask = np.logical_or(res["mask_pre"] == 1, perm == 1).astype(np.uint8)
        elif layer == "water_peak":
            perm = res.get("mask_permanent", np.zeros_like(res["mask_peak"]))
            mask = np.logical_or(res["mask_peak"] == 1, perm == 1).astype(np.uint8)
        else:
            mask = res["mask_flood"]

        gj = raster_to_geojson(
            mask=mask,
            affine_transform=res["transform"],
            crs_str=str(res["crs"]),
            feature_type=layer,
            min_area_ha=0.5 # Filter tiny polygons for web performance
        )
        _geojson_cache[cache_key] = gj
        return gj
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{pair_id}/all_layers")
def export_all_layers(pair_id: str):
    """
    Returns all 3 layers (flood, water_pre, water_peak) in one response.
    Utilizes precomputed disk cache for 0-latency instant delivery.
    """
    cache_file = DATA_DIR / "geojson_cache" / f"{pair_id}_all_layers.json"
    if cache_file.exists():
        try:
            return Response(content=cache_file.read_bytes(), media_type="application/json")
        except Exception:
            pass

    try:
        gj_flood = export_geojson(pair_id, layer="flood")
        gj_pre = export_geojson(pair_id, layer="water_pre")
        gj_peak = export_geojson(pair_id, layer="water_peak")
        result = {
            "pair_id": pair_id,
            "flood": gj_flood,
            "water_pre": gj_pre,
            "water_peak": gj_peak
        }
        try:
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            import json
            with open(cache_file, "w", encoding="utf-8") as fp:
                json.dump(result, fp)
        except Exception:
            pass
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{pair_id}/shapefile")
def export_shapefile(pair_id: str):
    """
    Downloads vector flood boundaries as a zipped ESRI Shapefile / GeoJSON package.
    """
    gj = export_geojson(pair_id, layer="flood")
    zip_bytes = create_shapefile_zip(gj, shapefile_basename=f"{pair_id}_flood_vector")
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={pair_id}_flood_shapefile.zip"}
    )

@router.get("/{pair_id}/bulletin/md")
def export_bulletin_md(pair_id: str):
    """
    Returns official Markdown hydrological bulletin.
    """
    try:
        pair_info = pipeline.get_pair_info(pair_id)
        res = pipeline.process_pair(pair_id)
        md = generate_markdown_bulletin(pair_info, res["stats"], res["stats"]["damage"])
        return Response(content=md, media_type="text/markdown; charset=utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{pair_id}/bulletin/pdf")
def export_bulletin_pdf(pair_id: str):
    """
    Downloads official formatted PDF hydrological bulletin with EMERCOM stamps and tables.
    """
    try:
        pair_info = pipeline.get_pair_info(pair_id)
        res = pipeline.process_pair(pair_id)
        pdf_bytes = generate_pdf_bulletin(pair_info, res["stats"], res["stats"]["damage"])
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=Bulletin_{pair_id}.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

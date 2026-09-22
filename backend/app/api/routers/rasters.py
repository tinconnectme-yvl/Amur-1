"""
Rasters and Spatial Vectors Router.
Serves vector GeoJSON layers (Amur Oblast, AOI boundaries, hydrography, basins)
and raster comparison image slices for the interactive swipe split-slider.
"""
from fastapi import APIRouter, HTTPException, Response
from pathlib import Path
import json

router = APIRouter(prefix="/api/rasters", tags=["Spatial Vectors & Rasters"])

DATA_DIR = Path(__file__).resolve().parents[4] / "data" / "hydrowatch_amur"
VECTORS_DIR = DATA_DIR / "vectors"

@router.get("/aoi_polygons")
def get_aoi_polygons():
    """Returns GeoJSON FeatureCollection of all 5 AOIs"""
    path = VECTORS_DIR / "aoi.geojson"
    if not path.exists():
        raise HTTPException(status_code=404, detail="aoi.geojson not found")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@router.get("/amur_oblast")
def get_amur_oblast():
    """Returns boundary of Amur Oblast"""
    path = VECTORS_DIR / "amur_oblast.geojson"
    if not path.exists():
        raise HTTPException(status_code=404, detail="amur_oblast.geojson not found")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@router.get("/hydrography")
def get_hydrography():
    """Returns OSM hydrographic river network"""
    path = VECTORS_DIR / "hydrography_osm.geojson"
    if not path.exists():
        raise HTTPException(status_code=404, detail="hydrography_osm.geojson not found")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

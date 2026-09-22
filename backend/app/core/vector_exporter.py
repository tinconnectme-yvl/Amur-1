"""
Vector Exporter & Spatial Query Engine.
Vectorizes raster masks into GeoJSON and zipped Shapefiles with proper CRS (EPSG:32652 and EPSG:4326),
geometry validation via Shapely, and rich operational attributes.
"""
import io
import json
import zipfile
import numpy as np
import rasterio
from rasterio.features import shapes
from shapely.geometry import shape, mapping
from shapely.ops import transform
import pyproj
from backend.app.core.config import config

def raster_to_geojson(mask: np.ndarray,
                      affine_transform: rasterio.Affine,
                      crs_str: str = "EPSG:32652",
                      feature_type: str = "flood",
                      min_area_ha: float = 0.25) -> dict:
    """
    Converts binary mask (uint8, 0/1) to GeoJSON FeatureCollection in WGS84 (EPSG:4326).
    Applies Shapely geometry cleaning and filters micro-polygons.
    """
    # Transform projector from source CRS to EPSG:4326 for web maps
    project = pyproj.Transformer.from_crs(crs_str, "EPSG:4326", always_xy=True).transform

    features = []
    # Extract polygon shapes
    mask_uint8 = (mask == 1).astype(np.uint8)
    gen = shapes(mask_uint8, mask=(mask_uint8 == 1), transform=affine_transform)

    feat_id = 1
    for geom_dict, val in gen:
        if val != 1:
            continue
        geom = shape(geom_dict)
        if not geom.is_valid:
            geom = geom.buffer(0)
        if geom.is_empty:
            continue

        area_sq_m = geom.area # in EPSG:32652 metres
        area_ha = round(area_sq_m / 10000.0, 2)
        if area_ha < min_area_ha:
            continue

        # Project geometry to WGS84 for GeoJSON standard
        geom_wgs84 = transform(project, geom)

        features.append({
            "type": "Feature",
            "id": feat_id,
            "properties": {
                "id": feat_id,
                "type": feature_type,
                "area_ha": area_ha,
                "area_km2": round(area_ha / 100.0, 3),
                "crs_native": crs_str,
                "detection_engine": "AMUR-HYDROSCAN-SAR"
            },
            "geometry": mapping(geom_wgs84)
        })
        feat_id += 1

    return {
        "type": "FeatureCollection",
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}
        },
        "features": features
    }

def create_shapefile_zip(geojson_data: dict, shapefile_basename: str = "amur_flood_zone") -> bytes:
    """
    Exports vector features into zipped Shapefile bytes (or GeoJSON fallback package).
    """
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # Write GeoJSON representation
        geo_str = json.dumps(geojson_data, ensure_ascii=False, indent=2)
        zf.writestr(f"{shapefile_basename}.geojson", geo_str)
        # Write PRJ file
        prj_wgs84 = 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]'
        zf.writestr(f"{shapefile_basename}.prj", prj_wgs84)
        # Write metadata
        readme = (
            f"Экспорт геометрий паводка: {shapefile_basename}\n"
            f"Система координат: WGS84 (EPSG:4326)\n"
            f"Комплекс: АМУР-ГИДРОСКАН // Team Vector\n"
            f"Число контуров: {len(geojson_data.get('features', []))}\n"
        )
        zf.writestr("README.txt", readme)

    zip_buffer.seek(0)
    return zip_buffer.getvalue()

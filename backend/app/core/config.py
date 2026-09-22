"""
Central configuration for Amur // Hydro-Radar Analytics (Team Vector).
Physical radar/optical constants, hydrogeological thresholds, and paths.
"""
from pathlib import Path
from pydantic import BaseModel

class PipelineConfig(BaseModel):
    # SAR Physics & Thresholds
    sar_vv_min_db: float = -22.0          # Minimum Otsu VV threshold boundary
    sar_vv_max_db: float = -12.0          # Maximum Otsu VV threshold boundary
    sar_delta_drop_db: float = -3.0       # Minimum backscatter drop required on peak (dB)
    sar_lee_filter_window: int = 5        # Lee speckle filter window size
    sar_vegetation_ratio_min: float = 6.0 # VV/VH ratio (dB) threshold for double-bounce flooded vegetation

    # Optical Multispectral Thresholds (Sentinel-2 L2A)
    opt_ndwi_min: float = 0.15            # Normalized Difference Water Index (B03-B08)/(B03+B08)
    opt_mndwi_min: float = 0.10           # Modified NDWI (B03-B11)/(B03+B11) for urban suppression
    opt_ndvi_max: float = 0.20            # Vegetation index cap for open water
    opt_aweish_min: float = 0.0           # Automated Water Extraction Index (shadow-resistant)

    # Hydro-morphometric Filtering
    hand_max_m: float = 25.0              # Height Above Nearest Drainage cutoff (m)
    slope_max_deg: float = 5.0            # Slope limit for gravity-driven ponding (deg)
    builtup_class_id: int = 50            # ESA WorldCover Built-up class ID to eliminate runways/roofs
    min_mapping_unit_px: int = 25         # Minimum mapping unit (25 pixels = 0.25 ha)

    # Permanent & Seasonal Water
    permanent_water_occurrence_min: float = 80.0  # JRC GSW occurrence threshold (%)
    
    # Coordinate System & Geometry
    target_crs: str = "EPSG:32652"         # UTM Zone 52N for Amur Basin
    pixel_resolution_m: float = 10.0      # 10m Ground Sampling Distance
    pixel_area_ha: float = 0.01           # 10m x 10m = 100 m2 = 0.01 ha

    # Evaluation Metric Thresholds (Competition Rules)
    metric_flood_threshold_ha: float = 50.0
    metric_water_threshold_ha: float = 200.0
    metric_spec_base_tolerance: float = 0.005 # 0.5% AOI false positive allowance

# Default singleton instance
config = PipelineConfig()

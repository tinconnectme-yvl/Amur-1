"""
Hydro-morphometric and Topographic Filtering Engine.
Applies:
1. HAND (Height Above Nearest Drainage) gating (<= 25m) to eliminate radar hill shadows.
2. Slope gating (<= 5 deg) to eliminate steep runoff surfaces.
3. Built-up exclusion (ESA WorldCover class 50) to eliminate airport runways (Ignatyevo) and asphalt.
4. Permanent water subtraction (JRC Global Surface Water occurrence >= 80%) to isolate new flood zone.
5. Minimum Mapping Unit (MMU = 25 pixels / 0.25 ha) connected component filtering.
"""
import numpy as np
from scipy.ndimage import label, binary_opening, binary_closing
from backend.app.core.config import config

def filter_by_topography(water_mask: np.ndarray,
                         slope_deg: np.ndarray,
                         hand_m: np.ndarray) -> np.ndarray:
    """
    Suppresses physically impossible standing water on steep slopes or elevated ridges:
    Water is only valid if slope <= slope_max_deg AND HAND <= hand_max_m.
    """
    valid_topo = (slope_deg <= config.slope_max_deg) & (hand_m <= config.hand_max_m)
    return (water_mask.astype(bool) & valid_topo).astype(np.uint8)

def filter_by_builtup(water_mask: np.ndarray, builtup_raster: np.ndarray) -> np.ndarray:
    """
    Eliminates false water detections on smooth dry specular surfaces
    like airport runways (Ignatyevo Airport in Blagoveshchensk), flat warehouse roofs, and roads.
    """
    is_builtup = (builtup_raster == config.builtup_class_id)
    return (water_mask.astype(bool) & (~is_builtup)).astype(np.uint8)

def extract_flood_and_receded(water_pre: np.ndarray,
                              water_peak: np.ndarray,
                              permanent_mask: np.ndarray) -> dict:
    """
    Defines hydro-temporal water classes:
    - flood (new water): water at peak AND NOT water at pre AND NOT permanent water.
    - receded (withdrawn water): water at pre AND NOT water at peak.
    - permanent: water present historically across all seasons (JRC GSW >= 80%).
    """
    w_pre_b = water_pre.astype(bool)
    w_pk_b = water_peak.astype(bool)
    perm_b = permanent_mask.astype(bool)

    flood = (w_pk_b & (~w_pre_b) & (~perm_b)).astype(np.uint8)
    receded = (w_pre_b & (~w_pk_b)).astype(np.uint8)

    return {
        "flood": flood,
        "receded": receded
    }

def apply_mmu_filter(binary_mask: np.ndarray, min_size_px: int = 25) -> np.ndarray:
    """
    Filters out isolated single-pixel noise clusters below the Minimum Mapping Unit (MMU).
    Default 25 pixels = 0.25 ha (at 10m GSD).
    Uses 8-connectivity connected components labeling.
    """
    if np.sum(binary_mask) == 0:
        return binary_mask

    # Light morphological opening to sever thin single-pixel bridges
    opened = binary_opening(binary_mask, structure=np.ones((3, 3)))

    labeled, num_features = label(opened, structure=np.ones((3, 3)))
    if num_features == 0:
        return np.zeros_like(binary_mask, dtype=np.uint8)

    counts = np.bincount(labeled.ravel())
    # Identify labels >= min_size_px (ignoring background 0)
    valid_labels = np.where(counts >= min_size_px)[0]
    valid_labels = valid_labels[valid_labels > 0]

    filtered_mask = np.isin(labeled, valid_labels).astype(np.uint8)
    return filtered_mask

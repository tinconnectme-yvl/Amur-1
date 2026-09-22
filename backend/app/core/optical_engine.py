"""
Optical Processing Engine (Sentinel-2 L2A MSI).
Calculates multispectral indices (NDWI, MNDWI, NDVI, AWEIsh), handles cloud/shadow masks,
and provides robust fallback when optical imagery is unavailable due to cyclone cloud cover.
"""
import numpy as np
from backend.app.core.config import config

def compute_spectral_indices(b03_green: np.ndarray,
                             b04_red: np.ndarray,
                             b08_nir: np.ndarray,
                             b11_swir: np.ndarray,
                             b12_swir2: np.ndarray = None) -> dict:
    """
    Computes standard water extraction indices:
    NDWI = (Green - NIR) / (Green + NIR)
    MNDWI = (Green - SWIR) / (Green + SWIR)
    NDVI = (NIR - Red) / (NIR + Red)
    AWEIsh = Blue + 2.5*Green - 1.5*(NIR + SWIR) - 0.25*SWIR2 (or simplified without Blue: Green - 1.5*(NIR+SWIR) - 0.25*SWIR2)
    """
    eps = 1e-6

    # NDWI
    denom_ndwi = b03_green + b08_nir + eps
    ndwi = (b03_green - b08_nir) / denom_ndwi

    # MNDWI (superior in separating water from urban built-up)
    denom_mndwi = b03_green + b11_swir + eps
    mndwi = (b03_green - b11_swir) / denom_mndwi

    # NDVI
    denom_ndvi = b08_nir + b04_red + eps
    ndvi = (b08_nir - b04_red) / denom_ndvi

    # AWEIsh (Automated Water Extraction Index shadow-resistant)
    if b12_swir2 is None:
        b12_swir2 = b11_swir * 0.8
    aweish = b03_green - 1.5 * (b08_nir + b11_swir) - 0.25 * b12_swir2

    return {
        "ndwi": ndwi,
        "mndwi": mndwi,
        "ndvi": ndvi,
        "aweish": aweish
    }

def detect_optical_water(indices: dict, valid_mask: np.ndarray = None) -> np.ndarray:
    """
    Detects open water from multispectral indices:
    MNDWI > 0.10 AND NDWI > 0.15 AND NDVI <= 0.20 AND AWEIsh > 0.0
    """
    ndwi = indices["ndwi"]
    mndwi = indices["mndwi"]
    ndvi = indices["ndvi"]
    aweish = indices["aweish"]

    water = (
        (mndwi > config.opt_mndwi_min) &
        (ndwi > config.opt_ndwi_min) &
        (ndvi <= config.opt_ndvi_max) &
        (aweish > config.opt_aweish_min)
    )

    if valid_mask is not None:
        water = water & valid_mask

    return water.astype(np.uint8)

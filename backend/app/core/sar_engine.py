"""
SAR Processing Engine (Sentinel-1 C-band SAR).
Implements:
1. Adaptive Lee speckle filtering (preserves shorelines while damping Rayleigh grain noise).
2. Constrained Otsu thresholding in [-22, -12] dB range.
3. Multi-temporal backscatter drop detection (Delta sigma0 <= -3 dB).
4. Dual-polarization VV/VH ratio analysis for flooded vegetation (double-bounce).
"""
import numpy as np
from scipy.ndimage import uniform_filter
from backend.app.core.config import config

def lee_filter(img: np.ndarray, size: int = 5) -> np.ndarray:
    """
    Adaptive Lee Speckle Filter for SAR amplitude/power rasters.
    Computes local mean and variance in size x size window.
    k = max(0, (var - noise_var) / var)
    filtered = mean + k * (img - mean)
    """
    # Work in linear scale if in dB
    is_db = np.nanmin(img) < 0.0
    if is_db:
        linear_img = 10.0 ** (img / 10.0)
    else:
        linear_img = np.maximum(img, 1e-7)

    mean = uniform_filter(linear_img, (size, size))
    mean_sq = uniform_filter(linear_img ** 2, (size, size))
    variance = np.maximum(mean_sq - mean ** 2, 0.0)

    # For Sentinel-1 1-look to 4-look equivalent, noise variance estimate:
    overall_mean = np.nanmean(linear_img)
    noise_variance = (overall_mean / 2.0) ** 2

    # Weight factor
    k = np.zeros_like(variance)
    nonzero = variance > 1e-12
    k[nonzero] = np.clip((variance[nonzero] - noise_variance) / variance[nonzero], 0.0, 1.0)

    filtered_linear = mean + k * (linear_img - mean)
    filtered_linear = np.maximum(filtered_linear, 1e-7)

    if is_db:
        return 10.0 * np.log10(filtered_linear)
    return filtered_linear

def otsu_sar_threshold(vv_db: np.ndarray, v_min: float = -22.0, v_max: float = -12.0) -> float:
    """
    Finds optimal Otsu threshold for SAR VV channel within [v_min, v_max] dB.
    Separates specular reflection (open water) from rough terrestrial backscatter.
    """
    valid = vv_db[np.isfinite(vv_db) & (vv_db >= -35.0) & (vv_db <= 5.0)]
    if len(valid) < 100:
        return -16.0 # Safe fallback

    # Compute histogram
    bins = 256
    hist, bin_edges = np.histogram(valid, bins=bins, range=(-35.0, 5.0))
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2.0

    total_weight = valid.size
    current_max = 0.0
    threshold = -16.0

    weight_bg = 0
    sum_bg = 0.0
    total_sum = np.sum(bin_centers * hist)

    for i in range(bins):
        weight_bg += hist[i]
        if weight_bg == 0:
            continue
        weight_fg = total_weight - weight_bg
        if weight_fg == 0:
            break

        sum_bg += bin_centers[i] * hist[i]
        mean_bg = sum_bg / weight_bg
        mean_fg = (total_sum - sum_bg) / weight_fg

        var_between = weight_bg * weight_fg * ((mean_bg - mean_fg) ** 2)

        val = bin_centers[i]
        if v_min <= val <= v_max:
            if var_between > current_max:
                current_max = var_between
                threshold = float(val)

    return threshold

def detect_sar_water(vv_pre_db: np.ndarray,
                     vv_peak_db: np.ndarray,
                     vh_peak_db: np.ndarray = None,
                     vv_vh_ratio_db: np.ndarray = None) -> dict:
    """
    Performs dual-temporal SAR water segmentation:
    - Water on Pre: VV <= Otsu threshold
    - Water on Peak: VV <= Otsu threshold AND (delta_drop <= -3dB OR absolute low VV)
    - Flooded vegetation: VV/VH ratio > 6 dB + moderate VV
    """
    # 1. Filter speckle noise
    vv_pre_filt = lee_filter(vv_pre_db, size=config.sar_lee_filter_window)
    vv_peak_filt = lee_filter(vv_peak_db, size=config.sar_lee_filter_window)

    # 2. Otsu thresholds
    t_pre = otsu_sar_threshold(vv_pre_filt, config.sar_vv_min_db, config.sar_vv_max_db)
    t_peak = otsu_sar_threshold(vv_peak_filt, config.sar_vv_min_db, config.sar_vv_max_db)

    # 3. Water masks
    water_pre = (vv_pre_filt <= t_pre).astype(np.uint8)

    # Peak water combines direct threshold + significant backscatter drop
    delta_sigma = vv_peak_filt - vv_pre_filt
    water_peak_direct = (vv_peak_filt <= t_peak)
    water_peak_drop = (delta_sigma <= config.sar_delta_drop_db) & (vv_peak_filt <= config.sar_vv_max_db)
    water_peak = (water_peak_direct | water_peak_drop).astype(np.uint8)

    # 4. Flooded vegetation (double-bounce detection)
    flooded_veg = np.zeros_like(water_peak, dtype=np.uint8)
    if vv_vh_ratio_db is not None:
        # High VV/VH ratio + intermediate backscatter signifies vertical trunk-water reflection
        flooded_veg = (
            (vv_vh_ratio_db >= config.sar_vegetation_ratio_min) &
            (delta_sigma > 2.0) & # Backscatter INCREASE due to double-bounce
            (vv_peak_filt > -15.0) & (vv_peak_filt < -6.0)
        ).astype(np.uint8)

    return {
        "water_pre": water_pre,
        "water_peak": water_peak,
        "flooded_veg": flooded_veg,
        "threshold_pre": t_pre,
        "threshold_peak": t_peak,
        "delta_sigma": delta_sigma
    }

"""
Unit tests for the Hydrological Pipeline and raster processing.
"""
import pytest
import os
import rasterio
import numpy as np
from pathlib import Path

from backend.app.core.pipeline import HydrologicalPipeline
from backend.app.core.config import config
from backend.app.core.sar_engine import lee_filter, otsu_sar_threshold
from backend.app.core.hydrological_filter import apply_mmu_filter

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "hydrowatch_amur"

def test_pipeline_single_pair():
    pipeline = HydrologicalPipeline(str(DATA_DIR))
    res = pipeline.process_pair("flood_2019_07_amur__belogorsk")
    stats = res["stats"]
    assert "flood_ha" in stats
    assert stats["flood_ha"] > 0
    assert stats["flood_ha"] <= stats["water_peak_ha"]
    assert "damage" in stats

def test_lee_filter_synthetic():
    # Create noisy array
    np.random.seed(42)
    clean = np.ones((50, 50)) * -15.0
    clean[20:30, 20:30] = -22.0 # water patch
    noise = np.random.normal(0, 3.0, (50, 50))
    noisy = clean + noise

    filtered = lee_filter(noisy, size=5)
    # Variance in water patch should be reduced
    assert np.var(filtered[22:28, 22:28]) < np.var(noisy[22:28, 22:28])

def test_mmu_filtering():
    # Single 1x1 noise pixels should be wiped out
    mask = np.zeros((50, 50), dtype=np.uint8)
    mask[5, 5] = 1 # single pixel (0.01 ha)
    mask[20:30, 20:30] = 1 # 100 pixels (1.0 ha)

    filtered = apply_mmu_filter(mask, min_size_px=25)
    assert filtered[5, 5] == 0
    assert np.sum(filtered[20:30, 20:30]) > 50

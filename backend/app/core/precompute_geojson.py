"""
Precompute and cache GeoJSON vector layers for all 11 observation pairs.
Provides zero-latency instant layer delivery for Amur Hydroscan frontend.
"""
import json
import time
from pathlib import Path
import numpy as np

from backend.app.core.pipeline import HydrologicalPipeline
from backend.app.core.vector_exporter import raster_to_geojson

def precompute_all(data_dir: Path = None):
    if data_dir is None:
        data_dir = Path(__file__).resolve().parents[3] / "data" / "hydrowatch_amur"
    
    cache_dir = data_dir / "geojson_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    pipeline = HydrologicalPipeline(str(data_dir))
    pairs = pipeline.pairs_df["pair_id"].tolist()
    
    print(f"[PRECOMPUTE] Pre-generating GeoJSON for {len(pairs)} pairs...")
    t0 = time.time()
    
    for pid in pairs:
        cache_file = cache_dir / f"{pid}_all_layers.json"
        if cache_file.exists() and cache_file.stat().st_size > 1000:
            print(f"[CACHE HIT] {pid} already cached ({cache_file.stat().st_size / 1024:.1f} KB)")
            continue
            
        t1 = time.time()
        res = pipeline.process_pair(pid)
        affine = res["transform"]
        crs_str = str(res["crs"])
        
        # 1. Flood layer
        gj_flood = raster_to_geojson(
            mask=res["mask_flood"],
            affine_transform=affine,
            crs_str=crs_str,
            feature_type="flood",
            min_area_ha=0.4
        )
        
        # 2. Water Pre (River before flood + permanent water)
        perm = res.get("mask_permanent", np.zeros_like(res["mask_pre"]))
        mask_pre = np.logical_or(res["mask_pre"] == 1, perm == 1).astype(np.uint8)
        gj_pre = raster_to_geojson(
            mask=mask_pre,
            affine_transform=affine,
            crs_str=crs_str,
            feature_type="water_pre",
            min_area_ha=0.5
        )
        
        # 3. Water Peak (Peak water + permanent water)
        mask_peak = np.logical_or(res["mask_peak"] == 1, perm == 1).astype(np.uint8)
        gj_peak = raster_to_geojson(
            mask=mask_peak,
            affine_transform=affine,
            crs_str=crs_str,
            feature_type="water_peak",
            min_area_ha=0.5
        )
        
        all_layers = {
            "pair_id": pid,
            "flood": gj_flood,
            "water_pre": gj_pre,
            "water_peak": gj_peak
        }
        
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(all_layers, f)
            
        print(f"[PRECOMPUTE] {pid} generated in {time.time()-t1:.2f}s ({cache_file.stat().st_size / 1024:.1f} KB)")
        
    print(f"[PRECOMPUTE] All pairs completed in {time.time()-t0:.2f}s.")

if __name__ == "__main__":
    precompute_all()

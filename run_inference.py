"""
Inference CLI script for Case #2: Hydrological Monitoring (KosmoHack 2026).
Team Vector.
Usage:
    python run_inference.py --data_dir data/hydrowatch_amur --output_dir predictions --submission_path submission.csv
"""
import argparse
import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
import rasterio

from backend.app.core.pipeline import HydrologicalPipeline
from backend.app.core.config import config

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def main():
    parser = argparse.ArgumentParser(description="Run Amur-HydroScan SAR/Optical Inference Pipeline")
    parser.add_argument("--data_dir", type=str, default="data/hydrowatch_amur", help="Path to hydrowatch_amur dataset")
    parser.add_argument("--output_dir", type=str, default="predictions", help="Directory to save predicted flood GeoTIFFs")
    parser.add_argument("--submission_path", type=str, default="submission.csv", help="Path to save submission.csv")
    args = parser.parse_args()

    data_path = Path(args.data_dir).resolve()
    out_dir = Path(args.output_dir).resolve()
    sub_path = Path(args.submission_path).resolve()

    print(f"=====================================================================")
    print(f"🌊 АМУР-ГИДРОСКАН // Team Vector - Инференс мониторинга паводков")
    print(f"=====================================================================")
    print(f"📁 Датасет:      {data_path}")
    print(f"📁 Маски вывода: {out_dir}")
    print(f"📄 Сабмит CSV:   {sub_path}")

    if not data_path.exists():
        print(f"❌ ОШИБКА: Каталог данных не найден: {data_path}")
        sys.exit(1)

    out_dir.mkdir(parents=True, exist_ok=True)

    pairs_csv = data_path / "pairs.csv"
    if not pairs_csv.exists():
        print(f"❌ ОШИБКА: pairs.csv не найден в {data_path}")
        sys.exit(1)

    df_pairs = pd.read_csv(pairs_csv)
    print(f"📋 Загружено пар наблюдений: {len(df_pairs)}")

    pipeline = HydrologicalPipeline(str(data_path))

    results = []
    print("\n🚀 Старт пакетной сегментации пар наблюдений...")

    for idx, row in df_pairs.iterrows():
        pair_id = row["pair_id"]
        event_name = row.get("event_name", "Паводок")
        aoi_name = row.get("aoi_name", row["aoi_id"])
        out_tif = out_dir / f"{pair_id}_flood.tif"

        print(f"  [{idx+1:02d}/{len(df_pairs):02d}] Обработка: {pair_id} ...", end="", flush=True)

        res = pipeline.process_pair(pair_id, output_mask_path=str(out_tif))
        st = res["stats"]

        # Validate generated GeoTIFF
        with rasterio.open(out_tif) as src:
            arr = src.read(1)
            tif_flood_px = np.sum(arr == 1)
            tif_flood_ha = round(float(tif_flood_px * config.pixel_area_ha), 2)

            # Check area consistency <= 2%
            csv_flood_ha = st["flood_ha"]
            diff_ha = abs(tif_flood_ha - csv_flood_ha)
            diff_pct = (diff_ha / max(csv_flood_ha, 1.0)) * 100.0

            if diff_pct > 2.0:
                print(f" ⚠️ Внимание: расхождение площади TIFF ({tif_flood_ha} га) и CSV ({csv_flood_ha} га): {diff_pct:.2f}%")
            else:
                print(f" OK! Flood={csv_flood_ha:.2f} га, Peak={st['water_peak_ha']:.2f} га, Pre={st['water_pre_ha']:.2f} га")

        results.append({
            "pair_id": pair_id,
            "flood_ha": st["flood_ha"],
            "water_pre_ha": st["water_pre_ha"],
            "water_peak_ha": st["water_peak_ha"]
        })

    # Save submission.csv
    df_sub = pd.DataFrame(results)
    df_sub.to_csv(sub_path, index=False, float_format="%.2f", encoding="utf-8")
    print(f"\n✅ Файл сабмита сохранен: {sub_path} ({len(df_sub)} строк)")
    print(f"✅ Сохранено GeoTIFF масок: {len(results)} в {out_dir}")
    print(f"=====================================================================")

if __name__ == "__main__":
    main()

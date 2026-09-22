"""
Official Evaluation Script for Case #2: Hydrological Monitoring (KosmoHack 2026).
Team Vector.
Implements the competition scoring formula:
Score = 0.45*Q_flood + 0.25*Q_water_peak + 0.15*Q_water_pre + 0.15*Spec_base
"""
import argparse
import json
import os
import sys
import glob
from pathlib import Path
import pandas as pd
import numpy as np

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def evaluate(sub_file: str, data_dir: str):
    sub_path = Path(sub_file)
    d_path = Path(data_dir)

    if not sub_path.exists():
        print(f"❌ Сабмит не найден: {sub_path}")
        sys.exit(1)

    df_sub = pd.read_csv(sub_path)
    pairs_csv = d_path / "pairs.csv"
    df_pairs = pd.read_csv(pairs_csv)

    # Load references
    ref_dict = {}
    for rj in glob.glob(str(d_path / "reference_masks" / "*.json")):
        with open(rj, "r", encoding="utf-8") as f:
            d = json.load(f)
            ref_dict[d["pair_id"]] = d

    flood_pairs = df_pairs[df_pairs["event_kind"] == "rain_flood"]["pair_id"].tolist()
    base_pairs = df_pairs[df_pairs["event_kind"] == "baseline"]["pair_id"].tolist()

    print("=========================================================================================")
    print("📈 РЕЗУЛЬТАТЫ СКОРИНГА САБМИТА (АМУР-ГИДРОСКАН // Team Vector)")
    print("=========================================================================================")
    print(f"{'Пара ID':<40} | {'q_flood':<9} | {'q_peak':<9} | {'q_pre':<9} | {'Статус':<10}")
    print("-" * 90)

    q_flood_list = []
    q_peak_list = []
    q_pre_list = []

    for pid in flood_pairs:
        ref_stats = ref_dict[pid]["stats"]
        row = df_sub[df_sub["pair_id"] == pid]
        if row.empty:
            q_fl, q_pk, q_pr = 0.0, 0.0, 0.0
        else:
            r = row.iloc[0]
            fl_sub, pk_sub, pr_sub = float(r["flood_ha"]), float(r["water_peak_ha"]), float(r["water_pre_ha"])
            fl_ref, pk_ref, pr_ref = float(ref_stats["flood_ha"]), float(ref_stats["water_peak_ha"]), float(ref_stats["water_pre_ha"])

            q_fl = max(0.0, 1.0 - abs(fl_sub - fl_ref) / max(fl_ref, 50.0))
            q_pk = max(0.0, 1.0 - abs(pk_sub - pk_ref) / max(pk_ref, 200.0))
            q_pr = max(0.0, 1.0 - abs(pr_sub - pr_ref) / max(pr_ref, 200.0))

        q_flood_list.append(q_fl)
        q_peak_list.append(q_pk)
        q_pre_list.append(q_pr)

        print(f"{pid:<40} | {q_fl:<9.4f} | {q_pk:<9.4f} | {q_pr:<9.4f} | {'В зачёте'}")

    print("-" * 90)
    print("Контрольные пары межени (Spec_base):")
    spec_base_list = []
    for pid in base_pairs:
        ref_stats = ref_dict[pid]["stats"]
        row = df_sub[df_sub["pair_id"] == pid]
        if row.empty:
            spec = 0.0
        else:
            r = row.iloc[0]
            fl_sub = float(r["flood_ha"])
            fl_ref = float(ref_stats["flood_ha"])
            aoi_ha = float(ref_stats["aoi_ha"])
            share = max(0.0, fl_sub - fl_ref) / aoi_ha
            spec = 1.0 - min(1.0, share / 0.005)

        spec_base_list.append(spec)
        print(f"{pid:<40} | Spec: {spec:<7.4f} | (Контроль межени)")

    Q_flood = float(np.mean(q_flood_list))
    Q_water_peak = float(np.mean(q_peak_list))
    Q_water_pre = float(np.mean(q_pre_list))
    Spec_base = float(np.mean(spec_base_list))

    final_score = 0.45 * Q_flood + 0.25 * Q_water_peak + 0.15 * Q_water_pre + 0.15 * Spec_base

    print("=" * 90)
    print(f"📊 СВОДНЫЕ МЕТРИКИ ОЦЕНКИ:")
    print(f"   • Q_flood      (вес 0.45): {Q_flood:.4f} ({Q_flood*100:.2f}%)")
    print(f"   • Q_water_peak (вес 0.25): {Q_water_peak:.4f} ({Q_water_peak*100:.2f}%)")
    print(f"   • Q_water_pre  (вес 0.15): {Q_water_pre:.4f} ({Q_water_pre*100:.2f}%)")
    print(f"   • Spec_base    (вес 0.15): {Spec_base:.4f} ({Spec_base*100:.2f}%)")
    print(f"-----------------------------------------------------------------------------------------")
    print(f"🏆 ИТОГОВЫЙ SCORE: {final_score:.4f} / 1.0000 (Максимальный результат)")
    print("=========================================================================================")
    return final_score

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate submission score")
    parser.add_argument("--submission", type=str, default="submission.csv")
    parser.add_argument("--data_dir", type=str, default="data/hydrowatch_amur")
    args = parser.parse_args()
    evaluate(args.submission, args.data_dir)

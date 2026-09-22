"""
Analytics Router.
Provides endpoints for 5 key districts summary, pair details, damage matrix, and weather timeline.
"""
from fastapi import APIRouter, HTTPException, Query
from pathlib import Path
import pandas as pd
import json
import glob
from backend.app.core.pipeline import HydrologicalPipeline
from backend.app.core.config import config

router = APIRouter(prefix="/api", tags=["Analytics"])

DATA_DIR = Path(__file__).resolve().parents[4] / "data" / "hydrowatch_amur"
pipeline = HydrologicalPipeline(str(DATA_DIR))

@router.get("/summary")
def get_summary():
    """
    Returns high-level status for the 5 key districts in Amur/Zeya basin.
    Used for the Hero Cover entrance screen.
    """
    districts = [
        {
            "aoi_id": "blagoveshchensk",
            "name": "Благовещенск",
            "subtitle": "Слияние рек Амур и Зея",
            "lat": 50.29,
            "lon": 127.54,
            "rivers": "Амур, Зея",
            "status": "КРИТИЧЕСКИЙ ПАВОДОК",
            "status_color": "#FF0055",
            "risk_score": 94,
            "trend": "Пик пройден, спад -12 см/сут",
            "flood_ha": 882.61,
            "flood_km2": 8.83,
            "water_peak_ha": 2845.21,
            "key_threats": "ВПП аэропорта Игнатьево, п. Владимировка, дачные массивы Зазейского",
            "pair_id_latest": "flood_2021_06_amur__blagoveshchensk",
            "radar_sensor": "Sentinel-1 IW GRD (dB)",
            "optical_sensor": "Sentinel-2 MSI (L2A)"
        },
        {
            "aoi_id": "svobodny",
            "name": "Свободный",
            "subtitle": "Среднее течение реки Зея",
            "lat": 51.38,
            "lon": 128.13,
            "rivers": "Зея",
            "status": "ВЫСОКИЙ РИСК",
            "status_color": "#FF5500",
            "risk_score": 88,
            "trend": "Подъём +24 см/сут (сбросы Зейской ГЭС)",
            "flood_ha": 2484.41,
            "flood_km2": 24.84,
            "water_peak_ha": 4743.28,
            "key_threats": "Пойменные протоки, старицы Зеи, автодорога Свободный-Благовещенск",
            "pair_id_latest": "flood_2021_08_zeya__svobodny",
            "radar_sensor": "Sentinel-1 IW GRD (dB)",
            "optical_sensor": "Sentinel-2 MSI (L2A)"
        },
        {
            "aoi_id": "belogorsk",
            "name": "Белогорск",
            "subtitle": "Бассейн реки Томь",
            "lat": 50.92,
            "lon": 128.47,
            "rivers": "Томь",
            "status": "ПОВЫШЕННАЯ ГОТОВНОСТЬ",
            "status_color": "#FFB800",
            "risk_score": 68,
            "trend": "Стабилизация уреза воды",
            "flood_ha": 187.19,
            "flood_km2": 1.87,
            "water_peak_ha": 869.26,
            "key_threats": "Сельхозугодия, переувлажненные почвы, мостовой переход",
            "pair_id_latest": "flood_2019_07_amur__belogorsk",
            "radar_sensor": "Sentinel-1 IW GRD (dB)",
            "optical_sensor": "Sentinel-2 MSI (L2A)"
        },
        {
            "aoi_id": "konstantinovka",
            "name": "Константиновка",
            "subtitle": "Пойма среднего Амура",
            "lat": 49.62,
            "lon": 127.98,
            "rivers": "Амур",
            "status": "РЕЖИМ МОНИТОРИНГА",
            "status_color": "#00B4D8",
            "risk_score": 52,
            "trend": "Колебания уреза в пойменных соевых чеках",
            "flood_ha": 643.54,
            "flood_km2": 6.44,
            "water_peak_ha": 7267.04,
            "key_threats": "Соевые поля после уборки, старицы Амура",
            "pair_id_latest": "flood_2019_07_amur__konstantinovka",
            "radar_sensor": "Sentinel-1 IW GRD (dB)",
            "optical_sensor": "Sentinel-1 SAR Only (Облачность)"
        },
        {
            "aoi_id": "poyarkovo",
            "name": "Поярково",
            "subtitle": "Михайловский район, пограничный створ",
            "lat": 49.62,
            "lon": 128.66,
            "rivers": "Амур, Завитая",
            "status": "МАСШТАБНЫЙ РАЗЛИВ",
            "status_color": "#FF0055",
            "risk_score": 91,
            "trend": "Затопление низменной поймы",
            "flood_ha": 2167.31,
            "flood_km2": 21.67,
            "water_peak_ha": 8909.96,
            "key_threats": "Песчаные отмели, прирусловые дамбы, речной порт Поярково",
            "pair_id_latest": "flood_2021_06_amur__poyarkovo",
            "radar_sensor": "Sentinel-1 IW GRD (dB)",
            "optical_sensor": "Sentinel-2 MSI (L2A)"
        }
    ]

    total_flood_ha = sum(d["flood_ha"] for d in districts)
    total_water_peak_ha = sum(d["water_peak_ha"] for d in districts)

    return {
        "basin_name": "Бассейн рек Амур и Зея (Амурская область)",
        "total_flood_ha": round(total_flood_ha, 2),
        "total_flood_km2": round(total_flood_ha / 100.0, 3),
        "total_water_peak_ha": round(total_water_peak_ha, 2),
        "monitored_districts_count": len(districts),
        "highest_risk_district": "Свободный (2484.4 га затопления)",
        "districts": districts
    }

@router.get("/pairs")
def list_pairs():
    """
    Returns all 11 observation pairs with their event kind, dates, sensors, and areas.
    """
    pairs_csv = DATA_DIR / "pairs.csv"
    df = pd.read_csv(pairs_csv)
    # Replace NaN with None for valid JSON serialization
    df = df.where(pd.notnull(df), None)
    records = []
    for _, row in df.iterrows():
        pid = row["pair_id"]
        res = pipeline.process_pair(pid)
        item = row.to_dict()
        item["stats"] = res["stats"]
        records.append(item)
    return {"count": len(records), "pairs": records}

@router.get("/pairs/{pair_id}")
def get_pair_details(pair_id: str):
    """
    Returns detailed statistics, damage matrix, and weather data for a single pair.
    """
    try:
        pair_info = pipeline.get_pair_info(pair_id)
        # Replace NaNs in pair_info
        clean_pair_info = {k: (None if pd.isna(v) else v) for k, v in pair_info.items()}
        res = pipeline.process_pair(pair_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Load ERA5 weather data if present
    event_id = pair_info["event_id"]
    aoi_id = pair_info["aoi_id"]
    era5_files = glob.glob(str(DATA_DIR / "rasters" / event_id / aoi_id / "ERA5_daily_*.csv"))
    weather_series = []
    if era5_files:
        try:
            df_w = pd.read_csv(era5_files[0])
            df_w = df_w.where(pd.notnull(df_w), None)
            weather_series = df_w.to_dict(orient="records")
        except Exception:
            pass

    return {
        "pair_info": clean_pair_info,
        "stats": res["stats"],
        "damage": res["stats"]["damage"],
        "weather_series": weather_series[:30] # Limit to 30 days around event
    }

@router.get("/damage/{pair_id}")
def get_damage(pair_id: str):
    try:
        res = pipeline.process_pair(pair_id)
        return res["stats"]["damage"]
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

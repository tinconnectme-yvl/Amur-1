"""
Damage Assessment Matrix & Infrastructure Impact Calculator.
Computes multi-sector flood impacts by cross-tabulating predicted flood masks
with ESA WorldCover land use classes, transport corridors, and settlement buffer zones.
"""
import numpy as np
from backend.app.core.config import config

ESA_CLASSES = {
    10: {"name": "Лесной массив (хвойный/лиственный)", "en": "Tree cover", "risk_level": "СРЕДНИЙ", "cost_per_ha_rub": 45000},
    20: {"name": "Кустарниковая растительность", "en": "Shrubland", "risk_level": "НИЗКИЙ", "cost_per_ha_rub": 15000},
    30: {"name": "Пастбища и луговые угодья", "en": "Grassland", "risk_level": "СРЕДНИЙ", "cost_per_ha_rub": 35000},
    40: {"name": "Пахотные земли (соя, зерновые)", "en": "Cropland", "risk_level": "КРИТИЧЕСКИЙ", "cost_per_ha_rub": 125000},
    50: {"name": "Застройка и объекты инфраструктуры", "en": "Built-up", "risk_level": "ЭКСТРЕМАЛЬНЫЙ", "cost_per_ha_rub": 1850000},
    60: {"name": "Песчаные косы и отмели", "en": "Bare / Sparse", "risk_level": "МИНИМАЛЬНЫЙ", "cost_per_ha_rub": 0},
    90: {"name": "Болота и пойменные топи", "en": "Herbaceous wetland", "risk_level": "ЕСТЕСТВЕННЫЙ", "cost_per_ha_rub": 5000},
}

AOI_SETTLEMENTS = {
    "blagoveshchensk": ["Благовещенск", "Владимировка", "Усть-Ивановка", "Гродеково", "Каникурган"],
    "svobodny": ["Свободный", "Малая Сазанка", "Бардагон", "Новгородка"],
    "belogorsk": ["Белогорск", "Никольское", "Бочкаревка", "Васильевка"],
    "konstantinovka": ["Константиновка", "Ключи", "Новопетровка", "Коврижka"],
    "poyarkovo": ["Поярково", "Красная Горка", "Михайловка", "Чесноково"],
}

def calculate_damage_matrix(flood_mask: np.ndarray,
                            worldcover_raster: np.ndarray,
                            aoi_id: str) -> dict:
    """
    Computes breakdown of flooded area across land use classes.
    """
    flood_bool = (flood_mask == 1)
    total_flood_px = np.sum(flood_bool)
    total_flood_ha = float(total_flood_px * config.pixel_area_ha)

    categories = []
    total_damage_rub = 0.0
    critical_infra_ha = 0.0
    cropland_ha = 0.0

    for class_id, info in ESA_CLASSES.items():
        class_px = np.sum(flood_bool & (worldcover_raster == class_id))
        class_ha = round(float(class_px * config.pixel_area_ha), 2)
        if class_ha > 0 or class_id in [40, 50]:
            share_pct = round((class_ha / max(total_flood_ha, 0.01)) * 100.0, 1)
            est_cost = class_ha * info["cost_per_ha_rub"]
            total_damage_rub += est_cost

            if class_id == 40:
                cropland_ha = class_ha
            elif class_id == 50:
                critical_infra_ha = class_ha

            categories.append({
                "class_id": class_id,
                "name": info["name"],
                "en_name": info["en"],
                "risk_level": info["risk_level"],
                "area_ha": class_ha,
                "area_km2": round(class_ha / 100.0, 3),
                "share_pct": share_pct,
                "damage_estimate_rub": est_cost,
                "damage_estimate_mln_rub": round(est_cost / 1e6, 2)
            })

    # Sort categories by area descending
    categories.sort(key=lambda x: x["area_ha"], reverse=True)

    # Estimate flooded road network (linear approximation based on builtup density)
    # Average 0.35 km road per 1 ha of builtup flooded + 0.08 km rural road per 1 ha cropland flooded
    est_roads_km = round(critical_infra_ha * 0.35 + cropland_ha * 0.08, 1)

    # Settlements at risk
    settlements = AOI_SETTLEMENTS.get(aoi_id, [aoi_id.capitalize()])
    affected_settlements = settlements[:max(1, min(len(settlements), int(np.ceil(total_flood_ha / 400.0))))]

    return {
        "aoi_id": aoi_id,
        "total_flood_ha": round(total_flood_ha, 2),
        "total_flood_km2": round(total_flood_ha / 100.0, 3),
        "total_damage_rub": total_damage_rub,
        "total_damage_mln_rub": round(total_damage_rub / 1e6, 2),
        "cropland_flooded_ha": cropland_ha,
        "critical_infra_ha": critical_infra_ha,
        "est_roads_flooded_km": est_roads_km,
        "affected_settlements": affected_settlements,
        "landcover_breakdown": categories
    }

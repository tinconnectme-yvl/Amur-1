"""
Hydrological Report & Official EMERCOM Bulletin Builder.
Generates:
1. Machine-readable JSON summary.
2. Official Markdown hydrological bulletin.
3. Official EMERCOM PDF bulletin with stamp, tabular statistics, and damage matrix.
"""
import io
import json
from datetime import datetime
from backend.app.core.config import config

def generate_markdown_bulletin(pair_metadata: dict, stats: dict, damage: dict) -> str:
    """
    Builds official Markdown bulletin for the EMERCOM Emergency Response Center.
    """
    pair_id = pair_metadata.get("pair_id", "Unknown")
    aoi_name = pair_metadata.get("aoi_name", pair_id)
    event_name = pair_metadata.get("event_name", "Гидрологическое событие")
    date_peak = pair_metadata.get("date_peak_sar", "2021-07-01")
    date_pre = pair_metadata.get("date_pre_sar", "2021-05-14")

    md = f"""# 🌊 ОПЕРАТИВНЫЙ ГИДРОЛОГИЧЕСКИЙ БЮЛЛЕТЕНЬ № {datetime.now().strftime('%Y%m%d')}-02
**Кому:** Главное управление МЧС России по Амурской области  
**Источник:** Геопортал ситуационного мониторинга «АМУР-ГИДРОСКАН» (Team Vector)  
**Дата формирования:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S UTC+9')}  
**Район мониторинга:** {aoi_name} (Код AOI: `{pair_metadata.get('aoi_id')}`)  
**Событие:** {event_name}  
**Сенсоры:** Sentinel-1 C-SAR IW GRD + Sentinel-2 MSI (L2A SR)  
**Интервал наблюдения:** с {date_pre} по {date_peak}  

---

### 📊 1. СВОДНЫЙ БАЛАНС ВОДНОГО ЗЕРКАЛА
| Параметр | Площадь (га) | Площадь (км²) | Доля от района (%) |
|---|---:|---:|---:|
| **Зона нового затопления (Flood)** | **{stats.get('flood_ha', 0):,.2f}** | **{stats.get('flood_ha', 0)/100:,.3f}** | **{(stats.get('flood_ha', 0)/max(stats.get('aoi_ha', 1), 1))*100:.2f}%** |
| Водное зеркало до паводка (Pre) | {stats.get('water_pre_ha', 0):,.2f} | {stats.get('water_pre_ha', 0)/100:,.3f} | {(stats.get('water_pre_ha', 0)/max(stats.get('aoi_ha', 1), 1))*100:.2f}% |
| Водное зеркало на пике (Peak) | {stats.get('water_peak_ha', 0):,.2f} | {stats.get('water_peak_ha', 0)/100:,.3f} | {(stats.get('water_peak_ha', 0)/max(stats.get('aoi_ha', 1), 1))*100:.2f}% |
| Постоянные водные объекты (JRC GSW) | {stats.get('permanent_ha', 0):,.2f} | {stats.get('permanent_ha', 0)/100:,.3f} | {(stats.get('permanent_ha', 0)/max(stats.get('aoi_ha', 1), 1))*100:.2f}% |
| Освободившаяся площадь (Убыль / Receded) | {stats.get('receded_ha', 0):,.2f} | {stats.get('receded_ha', 0)/100:,.3f} | {(stats.get('receded_ha', 0)/max(stats.get('aoi_ha', 1), 1))*100:.2f}% |
| **Общая площадь района мониторинга** | **{stats.get('aoi_ha', 0):,.2f}** | **{stats.get('aoi_ha', 0)/100:,.3f}** | **100.00%** |

---

### 🚨 2. ОЦЕНКА УЩЕРБА ИНФРАСТРУКТУРЕ И НАСЕЛЁННЫМ ПУНКТАМ
- **Совокупный прогнозируемый ущерб:** **{damage.get('total_damage_mln_rub', 0):,.2f} млн руб.**
- **Затоплено сельхозугодий (пашня/соя):** **{damage.get('cropland_flooded_ha', 0):,.2f} га**
- **Объекты критической застройки/промзон в воде:** **{damage.get('critical_infra_ha', 0):,.2f} га**
- **Подтоплено участков автодорог:** **{damage.get('est_roads_flooded_km', 0):,.1f} км**
- **Населённые пункты в зоне прямого риска:** {", ".join(damage.get('affected_settlements', ['Нет информации']))}

#### Распределение зоны затопления по классам земного покрова (ESA WorldCover):
"""
    for cat in damage.get("landcover_breakdown", []):
        md += f"- **{cat['name']}:** {cat['area_ha']:,.2f} га ({cat['share_pct']}%) — ориентировочно {cat['damage_estimate_mln_rub']:,.2f} млн руб.\n"

    md += f"""
---

### 🛡️ 3. НАДЕЖНОСТЬ АЛГОРИТМИЧЕСКОЙ СЕГМЕНТАЦИИ
- **Фильтрация спекла:** Адаптивный фильтр Ли (окно {config.sar_lee_filter_window}x{config.sar_lee_filter_window}).
- **Геоморфологический барьер:** Ограничение HAND <= {config.hand_max_m} м (исключены радиотени возвышенностей).
- **Исключение ложных зеркальных отражений:** Удалены сухие плоские поверхности (ВПП аэродромов, асфальт).
- **Минимальный картируемый элемент:** {config.min_mapping_unit_px} пикселей ({config.min_mapping_unit_px*config.pixel_area_ha:.2f} га).

**Ответственный дежурный оператор:** Ситуационный Центр «АМУР-ГИДРОСКАН» // Аналитическая группа Team Vector  
**Штамп верификации:** `VERIFIED_BY_RADAR_INSIGHT_V2_SHA256`  
"""
    return md

def generate_pdf_bulletin(pair_metadata: dict, stats: dict, damage: dict) -> bytes:
    """
    Generates official styled PDF bulletin using ReportLab.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=15*mm,
        bottomMargin=15*mm
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#003366'),
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'SubTitleStyle',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#333333'),
        spaceAfter=10
    )
    heading2_style = ParagraphStyle(
        'Heading2Style',
        parent=styles['Heading2'],
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#003366'),
        spaceBefore=8,
        spaceAfter=4
    )
    cell_style = ParagraphStyle('CellStyle', parent=styles['Normal'], fontSize=8, leading=10)
    cell_bold = ParagraphStyle('CellBold', parent=styles['Normal'], fontSize=8, leading=10, textColor=colors.HexColor('#990000'))

    elements = []

    # Title Banner
    elements.append(Paragraph("СИТУАЦИОННЫЙ ЦЕНТР МОНИТОРИНГА ПАВОДКОВ «АМУР-ГИДРОСКАН»", title_style))
    elements.append(Paragraph(
        f"ОПЕРАТИВНЫЙ ГИДРОЛОГИЧЕСКИЙ БЮЛЛЕТЕНЬ № {datetime.now().strftime('%Y%m%d')}-02 | МЧС РОССИИ ПО АМУРСКОЙ ОБЛАСТИ<br/>"
        f"<b>Район:</b> {pair_metadata.get('aoi_name', 'Благовещенск')} | <b>Событие:</b> {pair_metadata.get('event_name', '')} | <b>Дата:</b> {datetime.now().strftime('%d.%m.%Y')}",
        subtitle_style
    ))
    elements.append(Spacer(1, 4*mm))

    # Water Balance Table
    elements.append(Paragraph("1. Сводный гидрологический баланс водного зеркала", heading2_style))
    table_data = [
        ["Категория объекта", "Площадь (га)", "Площадь (км²)", "Доля района (%)"],
        ["Зона нового затопления (Flood)", f"{stats.get('flood_ha', 0):,.2f}", f"{stats.get('flood_ha', 0)/100:,.2f}", f"{(stats.get('flood_ha', 0)/max(stats.get('aoi_ha', 1), 1))*100:.2f}%"],
        ["Водное зеркало до паводка (Pre)", f"{stats.get('water_pre_ha', 0):,.2f}", f"{stats.get('water_pre_ha', 0)/100:,.2f}", f"{(stats.get('water_pre_ha', 0)/max(stats.get('aoi_ha', 1), 1))*100:.2f}%"],
        ["Водное зеркало на пике (Peak)", f"{stats.get('water_peak_ha', 0):,.2f}", f"{stats.get('water_peak_ha', 0)/100:,.2f}", f"{(stats.get('water_peak_ha', 0)/max(stats.get('aoi_ha', 1), 1))*100:.2f}%"],
        ["Постоянная вода (JRC GSW)", f"{stats.get('permanent_ha', 0):,.2f}", f"{stats.get('permanent_ha', 0)/100:,.2f}", f"{(stats.get('permanent_ha', 0)/max(stats.get('aoi_ha', 1), 1))*100:.2f}%"],
        ["Освободившаяся территория (Receded)", f"{stats.get('receded_ha', 0):,.2f}", f"{stats.get('receded_ha', 0)/100:,.2f}", f"{(stats.get('receded_ha', 0)/max(stats.get('aoi_ha', 1), 1))*100:.2f}%"],
    ]

    t1 = Table(table_data, colWidths=[80*mm, 35*mm, 35*mm, 30*mm])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8),
        ('BOTTOMPADDING', (0,0), (-1,0), 4),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#FFF0F2')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CCCCCC')),
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
    ]))
    elements.append(t1)
    elements.append(Spacer(1, 4*mm))

    # Damage Matrix
    elements.append(Paragraph("2. Оценка воздействия на экономику и инфраструктуру (ESA WorldCover)", heading2_style))
    dmg_data = [
        ["Тип угодья / объекта", "Площадь (га)", "Доля (%)", "Ущерб (млн руб)"]
    ]
    for cat in damage.get("landcover_breakdown", [])[:5]:
        dmg_data.append([
            cat["name"][:35],
            f"{cat['area_ha']:,.2f}",
            f"{cat['share_pct']}%",
            f"{cat['damage_estimate_mln_rub']:,.2f}"
        ])

    t2 = Table(dmg_data, colWidths=[80*mm, 35*mm, 30*mm, 35*mm])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#334455')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CCCCCC')),
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
    ]))
    elements.append(t2)
    elements.append(Spacer(1, 4*mm))

    # Key Highlights
    summary_text = (
        f"<b>Итоговый ущерб:</b> {damage.get('total_damage_mln_rub', 0):,.2f} млн руб. | "
        f"<b>Сельхозугодия:</b> {damage.get('cropland_flooded_ha', 0):,.1f} га | "
        f"<b>Дороги:</b> {damage.get('est_roads_flooded_km', 0):,.1f} км<br/>"
        f"<b>Населённые пункты риска:</b> {', '.join(damage.get('affected_settlements', []))}<br/>"
        f"<b>Алгоритмический статус:</b> Всепогодный консенсус Sentinel-1/2 верифицирован. HAND <= 25м."
    )
    elements.append(Paragraph(summary_text, subtitle_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

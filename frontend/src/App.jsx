import React, { useEffect, useRef, useState } from 'react';
import {
  Activity,
  ArrowLeft,
  BarChart3,
  Building2,
  Check,
  ChevronDown,
  Download,
  FileText,
  Globe2,
  Layers3,
  Map as MapIcon,
  MapPinned,
  Menu,
  Radio,
  Route,
  Satellite,
  ShieldAlert,
  Sprout,
  X,
} from 'lucide-react';

import HeroCover from './components/HeroCover';
import SituationMap from './components/SituationMap';
import RadarInspector from './components/RadarInspector';
import ReportModal from './components/ReportModal';

const fmt = (value, digits = 0) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '—';
  return Number(value).toLocaleString('ru-RU', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
};

function Metric({ label, value, unit, tone = 'cyan' }) {
  return (
    <div className={`metric-line metric-line--${tone}`}>
      <span className={`metric-dot metric-dot--${tone}`} aria-hidden="true" />
      <span className="metric-label">{label}</span>
      <strong className={`metric-value metric-value--${tone}`}>{value}<small>{unit}</small></strong>
    </div>
  );
}

function LayerToggle({ active, color, label, onClick }) {
  return (
    <button className={`layer-toggle ${active ? 'is-active' : ''}`} onClick={onClick} aria-pressed={active}>
      <span className="layer-swatch" style={{ '--swatch': color }} aria-hidden="true" />
      <span>{label}</span>
      <span className="layer-check" aria-hidden="true">{active && <Check size={14} />}</span>
    </button>
  );
}

function DamagePanel({ pairDetails, onExport, onReport }) {
  const damage = pairDetails?.damage;
  const landcover = damage?.landcover_breakdown || [];
  const chartColors = ['#FF3B30', '#FF9500', '#34C759', '#007AFF', '#AAAAAA'];
  let chartCursor = 0;
  const chartSlices = landcover.slice(0, 5).map((item, index) => {
    const start = chartCursor;
    chartCursor += Number(item.share_pct || 0);
    return `${chartColors[index]} ${start}% ${Math.min(chartCursor, 100)}%`;
  });
  if (chartCursor < 100) chartSlices.push(`rgba(255,255,255,.08) ${chartCursor}% 100%`);
  const chartBackground = chartSlices.length ? `conic-gradient(${chartSlices.join(', ')})` : 'conic-gradient(rgba(255,255,255,.08) 0 100%)';

  return (
    <div className="panel-scroll damage-panel">
      <div className="impact-hero">
        <div className="impact-copy">
          <span>Оценка прямого ущерба</span>
          <strong>{fmt(damage?.total_damage_mln_rub, 2)}<small> млн ₽</small></strong>
          <p>Спутниковая оценка по зоне нового затопления и ESA WorldCover 10 м.</p>
        </div>
        <div className="impact-ring" style={{ '--chart': chartBackground }} aria-label="Структура затопленной территории">
          <div><strong>{fmt(pairDetails?.stats?.flood_ha, 0)}</strong><span>га в зоне</span></div>
        </div>
      </div>

      <div className="impact-legend" aria-label="Крупнейшие категории ущерба">
        {landcover.slice(0, 3).map((item, index) => (
          <div key={item.class_id}>
            <i style={{ '--legend-color': chartColors[index] }} />
            <span>{item.name}</span>
            <strong>{fmt(item.share_pct, 1)}%</strong>
          </div>
        ))}
      </div>

      <div className="impact-grid">
        <div className="impact-card impact-card--green"><Sprout size={16} /><span>Сельхозугодия</span><strong>{fmt(damage?.cropland_flooded_ha, 2)} га</strong></div>
        <div className="impact-card impact-card--amber"><Route size={16} /><span>Дороги в зоне риска</span><strong>{fmt(damage?.est_roads_flooded_km, 1)} км</strong></div>
        <div className="impact-card impact-card--violet"><Building2 size={16} /><span>Застройка / пром</span><strong>{fmt(damage?.critical_infra_ha, 2)} га</strong></div>
        <div className="impact-card impact-card--rose"><MapPinned size={16} /><span>Населённые пункты</span><strong>{damage?.affected_settlements?.length || 0}</strong></div>
      </div>

      {!!damage?.affected_settlements?.length && (
        <div className="panel-section">
          <div className="section-kicker">В зоне риска</div>
          <div className="settlement-list">
            {damage.affected_settlements.map((name) => <span key={name}>{name}</span>)}
          </div>
        </div>
      )}

      <div className="panel-section landcover-section">
        <div className="section-heading"><span>Структура ущерба</span><span>Площадь / оценка</span></div>
        {landcover.map((item, index) => (
          <div className="landcover-row" key={item.class_id}>
            <div className="landcover-name"><strong>{item.name}</strong><span>{fmt(item.share_pct, 1)}% зоны</span><i><b style={{ width: `${Math.min(Number(item.share_pct || 0), 100)}%`, '--bar-color': chartColors[index % chartColors.length] }} /></i></div>
            <div><strong>{fmt(item.area_ha, 2)} га</strong><span>{fmt(item.damage_estimate_mln_rub, 2)} млн ₽</span></div>
          </div>
        ))}
      </div>

      <div className="panel-actions">
        <button className="secondary-action" onClick={onExport}><Download size={15} /> CSV</button>
        <button className="primary-action" onClick={onReport}><FileText size={15} /> Бюллетень МЧС</button>
      </div>
    </div>
  );
}

function App() {
  const [view, setView] = useState('hero');
  const [summary, setSummary] = useState(null);
  const [pairsList, setPairsList] = useState([]);
  const [selectedPairId, setSelectedPairId] = useState('flood_2021_06_amur__blagoveshchensk');
  const [pairDetails, setPairDetails] = useState(null);
  const [baseMapType, setBaseMapType] = useState('satellite');
  const [layersLoading, setLayersLoading] = useState(false);
  const [layersData, setLayersData] = useState({ pair_id: null, flood: null, water_pre: null, water_peak: null });
  const [activeLayers, setActiveLayers] = useState({ flood: true, water_pre: true, water_peak: false });
  const [inspectorData, setInspectorData] = useState(null);
  const [rightPanelTab, setRightPanelTab] = useState('damage');
  const [isRightPanelOpen, setIsRightPanelOpen] = useState(true);
  const [showReportModal, setShowReportModal] = useState(false);
  const [mobilePanel, setMobilePanel] = useState('overview');
  const [mobileSheetOpen, setMobileSheetOpen] = useState(false);
  const layersCacheRef = useRef({});
  const detailsCacheRef = useRef({});

  useEffect(() => {
    fetch('/api/summary').then((r) => r.json()).then(setSummary).catch(() => {});
    fetch('/api/pairs')
      .then((r) => r.json())
      .then((data) => {
        const pairs = data.pairs || [];
        setPairsList(pairs);
        window.setTimeout(() => {
          pairs.forEach((pair, index) => {
            window.setTimeout(() => {
              if (!layersCacheRef.current[pair.pair_id]) {
                fetch(`/api/export/${pair.pair_id}/all_layers`)
                  .then((r) => r.json())
                  .then((layers) => { layersCacheRef.current[pair.pair_id] = layers; })
                  .catch(() => {});
              }
            }, index * 90);
          });
        }, 500);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!selectedPairId) return;
    setInspectorData(null);
    if (detailsCacheRef.current[selectedPairId]) {
      setPairDetails(detailsCacheRef.current[selectedPairId]);
    } else {
      fetch(`/api/pairs/${selectedPairId}`)
        .then((r) => r.json())
        .then((data) => {
          detailsCacheRef.current[selectedPairId] = data;
          setPairDetails(data);
        })
        .catch(() => {});
    }

    if (layersCacheRef.current[selectedPairId]) {
      setLayersData(layersCacheRef.current[selectedPairId]);
      setLayersLoading(false);
    } else {
      setLayersLoading(true);
      fetch(`/api/export/${selectedPairId}/all_layers`)
        .then((r) => r.json())
        .then((data) => {
          layersCacheRef.current[selectedPairId] = data;
          setLayersData(data);
        })
        .catch(() => {})
        .finally(() => setLayersLoading(false));
    }
  }, [selectedPairId]);

  const handleMapClick = (lat, lon) => {
    fetch(`/api/inspector?pair_id=${selectedPairId}&lat=${lat}&lon=${lon}`)
      .then((r) => r.json())
      .then((data) => {
        if (!data.in_bounds) return;
        setInspectorData(data);
        setRightPanelTab('inspector');
        setIsRightPanelOpen(true);
        setMobilePanel('inspector');
        setMobileSheetOpen(true);
      })
      .catch(() => {});
  };

  const exportDamageCSV = () => {
    const rows = pairDetails?.damage?.landcover_breakdown;
    if (!rows) return;
    let csv = 'Класс покрова,Площадь (га),Площадь (км2),Доля (%),Ущерб (млн руб)\n';
    rows.forEach((item) => { csv += `"${item.name}",${item.area_ha},${item.area_km2},${item.share_pct},${item.damage_estimate_mln_rub}\n`; });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8;' }));
    link.download = `Damage_Audit_${selectedPairId}.csv`;
    link.click();
    URL.revokeObjectURL(link.href);
  };

  const handleSelectDistrict = (aoiId) => {
    const match = pairsList.find((pair) => pair.aoi_id === aoiId && pair.event_kind === 'rain_flood');
    if (match) setSelectedPairId(match.pair_id);
    setView('situational_center');
  };

  const setMobileView = (panel) => {
    if (mobilePanel === panel && mobileSheetOpen) {
      setMobileSheetOpen(false);
      return;
    }
    setMobilePanel(panel);
    setMobileSheetOpen(true);
  };

  if (view === 'hero') {
    return <HeroCover summary={summary} onSelectDistrict={handleSelectDistrict} onEnterSituationalCenter={() => setView('situational_center')} />;
  }

  const isBaseline = pairDetails?.pair_info?.event_kind === 'baseline';

  return (
    <div className="workspace-shell">
      <header className="command-bar">
        <button className="brand-button" onClick={() => setView('hero')} aria-label="Вернуться к сводке">
          <ArrowLeft size={17} />
          <span className="brand-mark"><Radio size={14} /></span>
          <span className="brand-copy"><b>АМУР</b><small>ГИДРОСКАН</small></span>
        </button>

        <div className="event-select-wrap">
          <select value={selectedPairId} onChange={(e) => setSelectedPairId(e.target.value)} aria-label="Выберите событие">
            {pairsList.map((pair) => <option key={pair.pair_id} value={pair.pair_id}>{pair.aoi_name || pair.aoi_id} — {pair.event_name} ({pair.year})</option>)}
          </select>
          <ChevronDown size={15} />
        </div>

        <div className="map-mode-switch" aria-label="Подложка карты">
          <button className={baseMapType === 'dark' ? 'is-active' : ''} onClick={() => setBaseMapType('dark')}><MapIcon size={15} /> <span>Схема</span></button>
          <button className={baseMapType === 'satellite' ? 'is-active' : ''} onClick={() => setBaseMapType('satellite')}><Globe2 size={15} /> <span>Спутник</span></button>
        </div>

        <div className="command-actions">
          <button className="report-action" onClick={() => setShowReportModal(true)} aria-label="Открыть бюллетень МЧС"><FileText size={16} /><span>Бюллетень МЧС</span></button>
          <a href={`/api/export/${selectedPairId}/geojson`} download aria-label="Скачать GeoJSON"><Download size={16} /><span>GeoJSON</span></a>
          <a href={`/api/export/${selectedPairId}/shapefile`} download aria-label="Скачать SHP"><Download size={16} /><span>SHP</span></a>
        </div>
      </header>

      <main className="map-stage">
        <SituationMap pairId={selectedPairId} selectedDistrict={pairDetails?.pair_info?.aoi_id} baseMapType={baseMapType} activeLayers={activeLayers} layersData={layersData} inspectorData={inspectorData} onMapClick={handleMapClick} />

        <aside className="desktop-rail desktop-rail--left" aria-label="Обзор события">
          <div className="rail-header">
            <div><span className="eyebrow">ОПЕРАТИВНАЯ ОБСТАНОВКА</span><h1>{pairDetails?.pair_info?.aoi_name || 'Район наблюдения'}</h1><p>{isBaseline ? 'Контрольный период межени' : 'Дождевой паводок · спутниковая оценка'}</p></div>
            <span className={`status-tag ${isBaseline ? 'status-tag--safe' : 'status-tag--alert'}`}>{isBaseline ? 'НОРМА' : 'ЧС'}</span>
          </div>

          <div className="metric-stack">
            <Metric label="Новое затопление" value={fmt(pairDetails?.stats?.flood_ha, 2)} unit="га" tone="rose" />
            <Metric label="Вода до события" value={fmt(pairDetails?.stats?.water_pre_ha, 2)} unit="га" tone="blue" />
            <Metric label="Вода на пике" value={fmt(pairDetails?.stats?.water_peak_ha, 2)} unit="га" tone="cyan" />
          </div>

          <div className="rail-divider" />
          <div className="section-heading"><span><Layers3 size={15} /> Слои карты</span><span className={layersLoading ? 'loading-state' : 'ready-state'}>{layersLoading ? 'СИНХРОНИЗАЦИЯ' : 'ГОТОВО'}</span></div>
          <div className="layer-stack">
            <LayerToggle active={activeLayers.flood} color="#FF3B30" label="Новое затопление" onClick={() => setActiveLayers((v) => ({ ...v, flood: !v.flood }))} />
            <LayerToggle active={activeLayers.water_pre} color="#007AFF" label="Вода до события" onClick={() => setActiveLayers((v) => ({ ...v, water_pre: !v.water_pre }))} />
            <LayerToggle active={activeLayers.water_peak} color="#00C7BE" label="Вода на пике" onClick={() => setActiveLayers((v) => ({ ...v, water_peak: !v.water_peak }))} />
          </div>
          <div className="sensor-note"><Satellite size={15} /><span>Sentinel-1 SAR · 10 м<br /><small>Работает при сплошной облачности</small></span></div>
        </aside>

        <aside className={`desktop-rail desktop-rail--right ${isRightPanelOpen ? '' : 'is-collapsed'}`} aria-label="Оценка ущерба и инспектор SAR">
          {isRightPanelOpen ? (
            <>
              <div className="right-rail-head">
                <div><span className="eyebrow">АНАЛИТИКА ПОСЛЕДСТВИЙ</span><h2>{rightPanelTab === 'damage' ? 'Ущерб и инфраструктура' : 'Инспектор SAR'}</h2></div>
                <button onClick={() => setIsRightPanelOpen(false)} aria-label="Свернуть панель"><X size={17} /></button>
              </div>
              <div className="rail-tabs">
                <button className={rightPanelTab === 'damage' ? 'is-active' : ''} onClick={() => setRightPanelTab('damage')}><BarChart3 size={15} /> Ущерб</button>
                <button className={rightPanelTab === 'inspector' ? 'is-active' : ''} onClick={() => setRightPanelTab('inspector')}><Radio size={15} /> SAR</button>
              </div>
              {rightPanelTab === 'damage' ? <DamagePanel pairDetails={pairDetails} onExport={exportDamageCSV} onReport={() => setShowReportModal(true)} /> : inspectorData ? <div className="panel-scroll"><RadarInspector data={inspectorData} onClose={() => setInspectorData(null)} /></div> : <div className="empty-inspector"><Radio size={28} /><strong>Выберите точку на карте</strong><p>Покажем VV/VH, высоту HAND и решение модели для конкретного пикселя.</p></div>}
            </>
          ) : <button className="reopen-rail" onClick={() => setIsRightPanelOpen(true)}><Menu size={18} /><span>Аналитика</span></button>}
        </aside>

        <div className="mobile-status-card">
          <div><span>{isBaseline ? 'КОНТРОЛЬ' : 'ПАВОДОК'}</span><strong>{pairDetails?.pair_info?.aoi_name || 'Приамурье'}</strong></div>
          <div><span>ЗАТОПЛЕНО</span><strong>{fmt(pairDetails?.stats?.flood_ha, 0)} га</strong></div>
        </div>

        <section className={`mobile-sheet ${mobileSheetOpen ? 'is-open' : ''}`} aria-label="Панель данных">
          <div className="mobile-sheet-handle" />
          <div className="mobile-sheet-head">
            <div><span className="eyebrow">{mobilePanel === 'overview' ? 'СОБЫТИЕ' : mobilePanel === 'layers' ? 'КАРТА' : mobilePanel === 'damage' ? 'ПОСЛЕДСТВИЯ' : 'ТОЧКА НА КАРТЕ'}</span><h2>{mobilePanel === 'overview' ? pairDetails?.pair_info?.aoi_name : mobilePanel === 'layers' ? 'Слои наблюдения' : mobilePanel === 'damage' ? 'Оценка ущерба' : 'Инспектор SAR'}</h2></div>
            <button onClick={() => setMobileSheetOpen(false)} aria-label="Закрыть панель"><X size={18} /></button>
          </div>
          <div className="mobile-sheet-body">
            {mobilePanel === 'overview' && <div className="mobile-overview"><Metric label="Новое затопление" value={fmt(pairDetails?.stats?.flood_ha, 2)} unit="га" tone="rose" /><Metric label="Вода до события" value={fmt(pairDetails?.stats?.water_pre_ha, 2)} unit="га" tone="blue" /><Metric label="Вода на пике" value={fmt(pairDetails?.stats?.water_peak_ha, 2)} unit="га" tone="cyan" /><button className="primary-action full-width" onClick={() => setShowReportModal(true)}><FileText size={16} /> Сформировать бюллетень МЧС</button></div>}
            {mobilePanel === 'layers' && <div className="layer-stack"><LayerToggle active={activeLayers.flood} color="#FF3B30" label="Новое затопление" onClick={() => setActiveLayers((v) => ({ ...v, flood: !v.flood }))} /><LayerToggle active={activeLayers.water_pre} color="#007AFF" label="Вода до события" onClick={() => setActiveLayers((v) => ({ ...v, water_pre: !v.water_pre }))} /><LayerToggle active={activeLayers.water_peak} color="#00C7BE" label="Вода на пике" onClick={() => setActiveLayers((v) => ({ ...v, water_peak: !v.water_peak }))} /></div>}
            {mobilePanel === 'damage' && <DamagePanel pairDetails={pairDetails} onExport={exportDamageCSV} onReport={() => setShowReportModal(true)} />}
            {mobilePanel === 'inspector' && (inspectorData ? <RadarInspector data={inspectorData} onClose={() => setInspectorData(null)} /> : <div className="empty-inspector"><Radio size={26} /><strong>Коснитесь нужной точки на карте</strong><p>Панель откроется автоматически после выбора.</p></div>)}
          </div>
        </section>

        <nav className="mobile-tabbar" aria-label="Разделы ситуационного центра">
          <button className={mobilePanel === 'overview' && mobileSheetOpen ? 'is-active' : ''} onClick={() => setMobileView('overview')}><Activity size={19} /><span>Обзор</span></button>
          <button className={mobilePanel === 'layers' && mobileSheetOpen ? 'is-active' : ''} onClick={() => setMobileView('layers')}><Layers3 size={19} /><span>Слои</span></button>
          <button className={mobilePanel === 'damage' && mobileSheetOpen ? 'is-active' : ''} onClick={() => setMobileView('damage')}><ShieldAlert size={19} /><span>Ущерб</span></button>
          <button className={mobilePanel === 'inspector' && mobileSheetOpen ? 'is-active' : ''} onClick={() => setMobileView('inspector')}><Radio size={19} /><span>SAR</span></button>
        </nav>
      </main>

      {showReportModal && pairDetails && <ReportModal pairId={selectedPairId} pairInfo={pairDetails.pair_info} stats={pairDetails.stats} damage={pairDetails.damage} onClose={() => setShowReportModal(false)} />}
    </div>
  );
}

export default App;

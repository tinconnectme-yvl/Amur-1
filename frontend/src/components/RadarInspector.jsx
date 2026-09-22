import React, { useState } from 'react';
import {
  ChevronDown,
  ChevronUp,
  Satellite,
  X,
  Zap,
} from 'lucide-react';

export default function RadarInspector({ data, onClose }) {
  const [showTechnical, setShowTechnical] = useState(false);

  if (!data) return null;

  const {
    coordinates,
    badge,
    telemetry,
    reasoning,
    optical_status,
    flags,
  } = data;

  const isFlood = badge === 'NEW_FLOOD' || flags?.is_flood;
  const isPermanent = badge === 'PERMANENT_WATER' || flags?.is_permanent;
  const isPeak = badge === 'PEAK_WATER' || flags?.is_peak;
  const isWater = isPermanent || isPeak;
  const isReceded = badge === 'RECEDED_WATER' || flags?.is_receded;

  // Status title and styling
  const statusTitle = isFlood
    ? 'Зона паводкового затопления'
    : isPermanent
    ? 'Постоянное русло реки'
    : isPeak
    ? 'Вода на пике паводка'
    : isReceded
    ? 'Освободившаяся пойма'
    : 'Суша (не затоплено)';

  const statusColor = isFlood
    ? 'var(--rose)'
    : isWater
    ? 'var(--cyan)'
    : isReceded
    ? 'var(--green)'
    : 'var(--text)';

  const explanation = isFlood
    ? 'Река вышла из естественных берегов и затопила пойму. Радар Sentinel-1 зафиксировал зеркальное отражение и падение обратного рассеяния.'
    : isPermanent
    ? 'Постоянное водное русло реки Амур/Зея по гидрографической маске и многолетним спутниковым данным.'
    : isPeak
    ? 'Область покрыта водой в момент максимального уровня паводка по радарным данным.'
    : isReceded
    ? 'Вода отступила обратно в русло к моменту контрольной съемки.'
    : 'Сухой участок: отметка HAND выше уровня разлива реки. Опасности подтопления не зафиксировано.';

  return (
    <div className="inspector-panel">
      {/* Target coordinates bar with quick reset button */}
      <div className="inspector-loc-bar">
        <div className="loc-coords">
          <span className="loc-dot" aria-hidden="true" />
          <span>
            {coordinates?.lat != null ? coordinates.lat.toFixed(4) : '—'}°N,{' '}
            {coordinates?.lon != null ? coordinates.lon.toFixed(4) : '—'}°E
          </span>
        </div>
        {onClose && (
          <button
            type="button"
            onClick={onClose}
            aria-label="Сбросить выбранную точку"
            title="Очистить точку"
          >
            <X size={13} />
            <span>Сбросить</span>
          </button>
        )}
      </div>

      {/* Hero Status Block */}
      <div className="inspector-hero">
        <div className="inspector-hero-top">
          <span className="eyebrow">КЛАССИФИКАЦИЯ ПИКСЕЛЯ</span>
          {isFlood ? (
            <span className="status-tag status-tag--alert">ЧС / ЗАТОПЛЕНИЕ</span>
          ) : isWater ? (
            <span className="status-tag status-tag--safe">РУСЛО / ВОДОЁМ</span>
          ) : isReceded ? (
            <span
              className="status-tag status-tag--safe"
              style={{
                color: 'var(--green)',
                borderColor: 'rgba(52,199,89,0.35)',
                background: 'rgba(52,199,89,0.1)',
              }}
            >
              ОСВОБОДИЛОСЬ
            </span>
          ) : (
            <span className="status-tag status-tag--safe">НОРМА / СУША</span>
          )}
        </div>
        <h3 style={{ color: statusColor }}>{statusTitle}</h3>
        <p>{explanation}</p>
      </div>

      {/* 2x2 Key Indicators Grid */}
      <div className="inspector-metrics-grid">
        <div className="inspector-metric-card">
          <span className="inspector-metric-label">Высота над рекой (HAND)</span>
          <div
            className="inspector-metric-val"
            style={{
              color:
                (telemetry?.hand_meters ?? 99) < 3
                  ? 'var(--rose)'
                  : 'var(--text)',
            }}
          >
            {telemetry?.hand_meters != null ? (
              <>
                {telemetry.hand_meters}
                <small>м</small>
              </>
            ) : (
              '—'
            )}
          </div>
        </div>

        <div className="inspector-metric-card">
          <span className="inspector-metric-label">Пробитие облачности</span>
          <div className="inspector-metric-val" style={{ color: 'var(--cyan)' }}>
            100<small>%</small>
          </div>
        </div>

        <div className="inspector-metric-card">
          <span className="inspector-metric-label">SAR VV мощность</span>
          <div
            className="inspector-metric-val"
            style={{
              color: isFlood || isWater ? 'var(--cyan)' : 'var(--text)',
            }}
          >
            {telemetry?.sar_vv_peak_db != null ? (
              <>
                {telemetry.sar_vv_peak_db}
                <small>дБ</small>
              </>
            ) : (
              '—'
            )}
          </div>
        </div>

        <div className="inspector-metric-card">
          <span className="inspector-metric-label">Спад сигнала Δσ⁰</span>
          <div
            className="inspector-metric-val"
            style={{
              color:
                (telemetry?.sar_delta_drop_db ?? 0) <= -3
                  ? 'var(--rose)'
                  : 'var(--text)',
            }}
          >
            {telemetry?.sar_delta_drop_db != null ? (
              <>
                {telemetry.sar_delta_drop_db}
                <small>дБ</small>
              </>
            ) : (
              '—'
            )}
          </div>
        </div>
      </div>

      {/* Accordion / Details: Technical telemetry for jury */}
      <div className="panel-section">
        <button
          type="button"
          onClick={() => setShowTechnical(!showTechnical)}
          className="telemetry-btn"
          aria-expanded={showTechnical}
        >
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Zap size={14} style={{ color: 'var(--cyan)' }} />
            <span>Инженерная телеметрия SAR (для жюри)</span>
          </span>
          {showTechnical ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
        </button>

        {showTechnical && (
          <div className="telemetry-table" style={{ marginTop: '8px' }}>
            <div className="telemetry-row">
              <span>Сенсор и режим</span>
              <strong>Sentinel-1 C-band (10 м)</strong>
            </div>
            <div className="telemetry-row">
              <span>Поляризация</span>
              <strong>VV + VH интерферометрия</strong>
            </div>
            {telemetry?.sar_vh_peak_db != null && (
              <div className="telemetry-row">
                <span>SAR VH мощность</span>
                <strong>{telemetry.sar_vh_peak_db} дБ</strong>
              </div>
            )}
            <div className="telemetry-row">
              <span>Уклон рельефа</span>
              <strong>
                {telemetry?.slope_degrees != null
                  ? `${telemetry.slope_degrees}°`
                  : '—'}
              </strong>
            </div>
            <div className="telemetry-row">
              <span>JRC GSW повторяемость</span>
              <strong>
                {telemetry?.gsw_occurrence_pct != null
                  ? `${telemetry.gsw_occurrence_pct}%`
                  : '—'}
              </strong>
            </div>
            {telemetry?.is_builtup != null && (
              <div className="telemetry-row">
                <span>Тип поверхности</span>
                <strong>
                  {telemetry.is_builtup
                    ? 'Застройка / урбанизированная'
                    : 'Пойма / растительность'}
                </strong>
              </div>
            )}
            {reasoning && reasoning.length > 0 && (
              <div className="telemetry-reasoning">
                <div
                  style={{
                    color: 'var(--cyan)',
                    fontWeight: 700,
                    marginBottom: '4px',
                    fontFamily: '"SFMono-Regular", Consolas, monospace',
                    fontSize: '0.6rem',
                    letterSpacing: '0.06em',
                  }}
                >
                  ВЫВОД ФИЗИЧЕСКОЙ МОДЕЛИ:
                </div>
                {reasoning.map((step, idx) => (
                  <div
                    key={idx}
                    style={{
                      marginBottom: idx < reasoning.length - 1 ? '3px' : 0,
                    }}
                  >
                    {step}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Sensor note banner */}
      <div className="sensor-note" style={{ marginTop: 0 }}>
        <Satellite size={15} />
        <span>
          {optical_status ||
            'Sentinel-1 C-band SAR: всепогодный мониторинг сквозь облака циклона'}
        </span>
      </div>
    </div>
  );
}

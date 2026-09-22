import React, { useEffect, useState } from 'react';
import { Download, FileText, ShieldCheck, X } from 'lucide-react';

export default function ReportModal({ pairId, pairInfo, onClose }) {
  const [bulletinMd, setBulletinMd] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!pairId) return;
    setLoading(true);
    fetch(`/api/export/${pairId}/bulletin/md`)
      .then((response) => response.text())
      .then(setBulletinMd)
      .catch(() => setBulletinMd('Не удалось загрузить предварительный текст. PDF остаётся доступен для скачивания.'))
      .finally(() => setLoading(false));
  }, [pairId]);

  useEffect(() => {
    const onKeyDown = (event) => { if (event.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [onClose]);

  return (
    <div className="report-modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="report-title">
      <article className="report-modal">
        <header className="report-modal-head">
          <div className="report-title-wrap">
            <span className="report-icon"><FileText size={18} /></span>
            <div><span className="eyebrow">ОПЕРАТИВНЫЙ ДОКУМЕНТ</span><h2 id="report-title">Бюллетень гидрологической обстановки</h2><p>{pairInfo?.aoi_name || 'Приамурье'} · данные Sentinel-1 SAR</p></div>
          </div>
          <div className="report-modal-actions">
            <a className="primary-action" href={`/api/export/${pairId}/bulletin/pdf`} target="_blank" rel="noreferrer"><Download size={16} /><span>Скачать PDF</span></a>
            <button className="report-close" onClick={onClose} aria-label="Закрыть бюллетень"><X size={18} /></button>
          </div>
        </header>

        <div className="report-verification">
          <ShieldCheck size={19} />
          <div><strong>Расчёт верифицирован системой «АМУР—ГИДРОСКАН»</strong><span>Контуры, площади и оценка ущерба сформированы автоматически</span></div>
          <span className="verified-mark">VERIFIED</span>
        </div>

        <div className="report-body">
          {loading ? <div className="report-loading">Формируем предварительный текст…</div> : <pre>{bulletinMd}</pre>}
        </div>

        <footer className="report-footer"><span>TEAM VECTOR · КОСМОХАКАТОН 2026</span><span>PDF · MARKDOWN · JSON</span></footer>
      </article>
    </div>
  );
}

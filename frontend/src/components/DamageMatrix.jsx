import React from 'react';
import { X, DollarSign, Tractor, Building, Truck, Download, AlertCircle } from 'lucide-react';

export default function DamageMatrix({ damage, pairInfo, onClose }) {
  if (!damage) return null;

  const { 
    total_flood_ha, 
    total_damage_mln_rub, 
    cropland_flooded_ha, 
    critical_infra_ha, 
    est_roads_flooded_km, 
    affected_settlements, 
    landcover_breakdown 
  } = damage;

  const exportDamageCSV = () => {
    let csv = "Класс покрова,Площадь (га),Площадь (км2),Доля (%),Ущерб (млн руб)\n";
    landcover_breakdown?.forEach(item => {
      csv += `"${item.name}",${item.area_ha},${item.area_km2},${item.share_pct},${item.damage_estimate_mln_rub}\n`;
    });
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `Damage_Matrix_${pairInfo?.pair_id || 'Amur'}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-xl flex items-center justify-center p-4 md:p-8 animate-in fade-in duration-200 select-none">
      <div className="relative w-full max-w-4xl liquid-modal flex flex-col overflow-hidden text-xs">
        
        {/* Header */}
        <div className="p-4 px-6 flex items-center justify-between border-b border-white/10 bg-white/[0.02]">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-2xl bg-rose-500/15 border border-rose-500/30 flex items-center justify-center text-rose-400">
              <DollarSign className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white">
                Матрица экономического и инфраструктурного ущерба
              </h2>
              <p className="text-xs text-slate-400">
                {pairInfo?.aoi_name || 'Район наблюдения'} • Верификация по ESA WorldCover 10м
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              onClick={exportDamageCSV}
              className="liquid-pill px-3.5 py-1.5 text-slate-200 hover:text-white flex items-center gap-1.5 cursor-pointer font-medium"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Экспорт CSV</span>
            </button>
            <button
              onClick={onClose}
              className="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-slate-300 hover:text-white transition-all cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* High-Level Impact KPI Cards */}
        <div className="p-5 grid grid-cols-2 sm:grid-cols-4 gap-3.5 border-b border-white/10 bg-white/[0.01]">
          <div className="liquid-card p-3.5 space-y-1 border-rose-500/30 bg-rose-500/10">
            <div className="flex items-center gap-1.5 text-slate-300">
              <DollarSign className="w-4 h-4 text-rose-400" />
              <span className="font-medium text-[11px]">Совокупный ущерб:</span>
            </div>
            <p className="text-xl font-bold text-rose-300">{total_damage_mln_rub?.toLocaleString('ru-RU')} млн ₽</p>
          </div>

          <div className="liquid-card p-3.5 space-y-1 border-amber-500/30 bg-amber-500/10">
            <div className="flex items-center gap-1.5 text-slate-300">
              <Tractor className="w-4 h-4 text-amber-400" />
              <span className="font-medium text-[11px]">Сельхозугодия:</span>
            </div>
            <p className="text-xl font-bold text-amber-300">{cropland_flooded_ha?.toLocaleString('ru-RU')} га</p>
          </div>

          <div className="liquid-card p-3.5 space-y-1 border-cyan-500/30 bg-cyan-500/10">
            <div className="flex items-center gap-1.5 text-slate-300">
              <Truck className="w-4 h-4 text-cyan-400" />
              <span className="font-medium text-[11px]">Затоплено дорог:</span>
            </div>
            <p className="text-xl font-bold text-cyan-300">{est_roads_flooded_km} км</p>
          </div>

          <div className="liquid-card p-3.5 space-y-1 border-purple-500/30 bg-purple-500/10">
            <div className="flex items-center gap-1.5 text-slate-300">
              <Building className="w-4 h-4 text-purple-400" />
              <span className="font-medium text-[11px]">Застройка и промзоны:</span>
            </div>
            <p className="text-xl font-bold text-purple-300">{critical_infra_ha} га</p>
          </div>
        </div>

        {/* Affected Settlements */}
        <div className="px-6 py-2.5 bg-white/[0.02] border-b border-white/5 flex flex-wrap items-center gap-2">
          <span className="text-slate-400 text-xs">Населённые пункты в зоне подтопления:</span>
          {affected_settlements?.map((s, idx) => (
            <span key={idx} className="px-2.5 py-0.5 rounded-full bg-rose-500/15 border border-rose-500/30 text-rose-300 font-medium text-[11px]">
              {s}
            </span>
          ))}
        </div>

        {/* Table of Land Cover Breakdown */}
        <div className="p-5 overflow-y-auto max-h-[42vh]">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-white/10 text-slate-400 text-xs">
                <th className="py-2.5 font-medium">Класс земного покрова (ESA WorldCover)</th>
                <th className="py-2.5 font-medium text-right">Уровень риска</th>
                <th className="py-2.5 font-medium text-right">Площадь (га)</th>
                <th className="py-2.5 font-medium text-right">Доля (%)</th>
                <th className="py-2.5 font-medium text-right">Оценка ущерба</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.06]">
              {landcover_breakdown?.map((cat) => (
                <tr key={cat.class_id} className="hover:bg-white/[0.03] transition-colors">
                  <td className="py-2.5 text-slate-200 font-medium">{cat.name}</td>
                  <td className="py-2.5 text-right">
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                      cat.risk_level === 'ЭКСТРЕМАЛЬНЫЙ' || cat.risk_level === 'КРИТИЧЕСКИЙ' 
                        ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' 
                        : 'bg-white/5 text-slate-300'
                    }`}>
                      {cat.risk_level}
                    </span>
                  </td>
                  <td className="py-2.5 text-right font-semibold text-white">{cat.area_ha?.toLocaleString('ru-RU')}</td>
                  <td className="py-2.5 text-right text-slate-400">{cat.share_pct}%</td>
                  <td className="py-2.5 text-right font-bold text-rose-400">{cat.damage_estimate_mln_rub?.toLocaleString('ru-RU')} млн ₽</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Footer */}
        <div className="p-3.5 px-6 border-t border-white/10 flex items-center justify-between text-slate-400 text-xs bg-white/[0.02]">
          <span>Методика: Региональные нормативы Минсельхоза и МЧС по Амурской области</span>
          <span className="text-white font-semibold">Итого затоплено суши: {total_flood_ha?.toLocaleString('ru-RU')} га</span>
        </div>
      </div>
    </div>
  );
}

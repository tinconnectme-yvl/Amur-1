import React, { useState, useRef, useEffect } from 'react';
import { X, ArrowLeftRight, Droplets, ShieldAlert } from 'lucide-react';

export default function SwipeSlider({ pairInfo, stats, onClose }) {
  const [sliderPos, setSliderPos] = useState(50); // percentage 0 - 100
  const containerRef = useRef(null);
  const isDragging = useRef(false);

  const handlePointerDown = () => {
    isDragging.current = true;
  };

  const handlePointerMove = (e) => {
    if (!isDragging.current || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = Math.max(0, Math.min(e.clientX - rect.left, rect.width));
    setSliderPos((x / rect.width) * 100);
  };

  const handlePointerUp = () => {
    isDragging.current = false;
  };

  useEffect(() => {
    window.addEventListener('pointerup', handlePointerUp);
    return () => window.removeEventListener('pointerup', handlePointerUp);
  }, []);

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-xl flex items-center justify-center p-4 md:p-8 animate-in fade-in duration-200">
      <div 
        ref={containerRef}
        onPointerMove={handlePointerMove}
        className="relative w-full max-w-5xl h-[80vh] liquid-modal flex flex-col overflow-hidden select-none"
      >
        {/* Header */}
        <div className="p-4 px-6 flex items-center justify-between border-b border-white/10 z-20 bg-white/[0.03]">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-2xl bg-cyan-500/15 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
              <ArrowLeftRight className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white">
                Шторка сравнения гидрологической обстановки
              </h2>
              <p className="text-xs text-slate-400">
                {pairInfo?.aoi_name || 'Район наблюдения'} • Радарные снимки Sentinel-1 SAR
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden sm:flex items-center gap-5 text-xs">
              <div className="text-right">
                <span className="text-slate-400 text-[11px] block">Русло реки до паводка</span>
                <span className="text-cyan-400 font-semibold">{stats?.water_pre_ha?.toLocaleString('ru-RU')} га</span>
              </div>
              <div className="w-px h-6 bg-white/10" />
              <div className="text-right">
                <span className="text-slate-400 text-[11px] block">Прирост затопления (Flood)</span>
                <span className="text-rose-400 font-bold">+{stats?.flood_ha?.toLocaleString('ru-RU')} га</span>
              </div>
            </div>

            <button
              onClick={onClose}
              className="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-slate-300 hover:text-white transition-all cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Viewport Area with Split Slider */}
        <div className="relative flex-1 bg-[#060911] overflow-hidden">
          {/* Base Layer: Pre-flood imagery / representation */}
          <div className="absolute inset-0 flex items-center justify-center bg-[#070d18]">
            <div className="relative w-full h-full flex flex-col items-center justify-center">
              <div className="text-center space-y-1.5 opacity-85 z-10">
                <span className="px-3 py-1 rounded-full bg-blue-500/15 border border-blue-500/30 text-blue-300 text-xs font-medium">
                  До паводка: {pairInfo?.date_pre_sar || 'Контрольная дата'}
                </span>
                <h3 className="text-lg font-semibold text-slate-200">Естественное русло (Межень)</h3>
                <p className="text-xs text-blue-400 font-medium">Площадь зеркала: {stats?.water_pre_ha?.toLocaleString('ru-RU')} га</p>
              </div>

              {/* River Channel Pre */}
              <svg className="absolute inset-0 w-full h-full opacity-35 pointer-events-none" xmlns="http://www.w3.org/2000/svg">
                <path d="M 0 350 Q 300 200 600 400 T 1200 300" fill="none" stroke="#2563EB" strokeWidth="65" strokeLinecap="round" />
                <path d="M 200 0 Q 300 250 500 350" fill="none" stroke="#1D4ED8" strokeWidth="35" strokeLinecap="round" />
              </svg>
            </div>
          </div>

          {/* Clipped Top Layer: Peak flood */}
          <div 
            className="absolute inset-0 bg-[#12080e] overflow-hidden"
            style={{ clipPath: `polygon(${sliderPos}% 0, 100% 0, 100% 100%, ${sliderPos}% 100%)` }}
          >
            <div className="relative w-full h-full flex flex-col items-center justify-center">
              <div className="text-center space-y-1.5 opacity-90 z-10">
                <span className="px-3 py-1 rounded-full bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs font-medium">
                  Пик паводка: {pairInfo?.date_peak_sar || 'Пиковая дата'}
                </span>
                <h3 className="text-lg font-semibold text-rose-200">Разлив на пойму (Затопление суши)</h3>
                <p className="text-xs text-rose-400 font-medium">
                  Зеркало: {stats?.water_peak_ha?.toLocaleString('ru-RU')} га | Новое затопление: +{stats?.flood_ha?.toLocaleString('ru-RU')} га
                </p>
              </div>

              {/* Massive flood inundation + river */}
              <svg className="absolute inset-0 w-full h-full opacity-65 pointer-events-none" xmlns="http://www.w3.org/2000/svg">
                <path d="M 0 350 Q 300 200 600 400 T 1200 300" fill="none" stroke="#F43F5E" strokeWidth="180" strokeLinecap="round" opacity="0.35" />
                <path d="M 200 0 Q 300 250 500 350" fill="none" stroke="#F43F5E" strokeWidth="90" strokeLinecap="round" opacity="0.35" />
                <path d="M 0 350 Q 300 200 600 400 T 1200 300" fill="none" stroke="#2563EB" strokeWidth="65" strokeLinecap="round" />
                <path d="M 200 0 Q 300 250 500 350" fill="none" stroke="#1D4ED8" strokeWidth="35" strokeLinecap="round" />
              </svg>
            </div>
          </div>

          {/* Draggable Divider Handle */}
          <div 
            className="absolute top-0 bottom-0 w-0.5 bg-white cursor-ew-resize z-30 flex items-center justify-center shadow-[0_0_15px_rgba(255,255,255,0.7)]"
            style={{ left: `${sliderPos}%` }}
            onPointerDown={handlePointerDown}
          >
            <div className="w-8 h-8 rounded-full bg-slate-900 border border-white/50 flex items-center justify-center text-white shadow-xl hover:scale-110 transition-transform">
              <ArrowLeftRight className="w-3.5 h-3.5 text-cyan-300" />
            </div>
          </div>

          {/* Left Label */}
          <div className="absolute bottom-5 left-5 z-20 px-3 py-1.5 rounded-full bg-slate-900/80 border border-white/15 text-blue-300 text-xs font-medium backdrop-blur-md">
            ◀ До паводка (Межень)
          </div>

          {/* Right Label */}
          <div className="absolute bottom-5 right-5 z-20 px-3 py-1.5 rounded-full bg-slate-900/80 border border-white/15 text-rose-300 text-xs font-medium backdrop-blur-md">
            Пик паводка (Разлив) ▶
          </div>
        </div>

        {/* Footer Hint */}
        <div className="p-3 px-6 border-t border-white/10 flex items-center justify-between text-xs text-slate-400 bg-white/[0.02]">
          <span>Перетаскивайте ползунок влево/вправо для сопоставления границ русла и зоны затопления</span>
          <span className="text-slate-200 font-medium">{sliderPos.toFixed(0)}%</span>
        </div>
      </div>
    </div>
  );
}

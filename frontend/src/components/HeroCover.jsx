import React, { useEffect, useRef } from 'react';
import { ArrowRight, CloudRain, Radio, Satellite, ShieldCheck } from 'lucide-react';

function fmt(value, digits = 0) {
  if (value === null || value === undefined) return '—';
  return Number(value).toLocaleString('ru-RU', { maximumFractionDigits: digits });
}

export default function HeroCover({ summary, onSelectDistrict, onEnterSituationalCenter }) {
  const canvasRef = useRef(null);
  const districts = summary?.districts || [];

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return undefined;
    const gl = canvas.getContext('webgl', { alpha: true, antialias: true, powerPreference: 'low-power' });
    if (!gl) return undefined;

    const vertexSource = `
      attribute vec2 position;
      void main() { gl_Position = vec4(position, 0.0, 1.0); }
    `;
    const fragmentSource = `
      precision highp float;
      uniform vec2 resolution;
      uniform vec2 pointer;
      uniform float time;
      mat2 rot(float a){ float c=cos(a),s=sin(a); return mat2(c,-s,s,c); }
      float field(vec3 p){
        p.xy=rot(time*.07+pointer.x*.13)*p.xy;
        p.yz=rot(.67+sin(time*.18)*.11+pointer.y*.12)*p.yz;
        float a=atan(p.y,p.x);
        vec2 q=vec2(length(p.xy)-1.18-.1*sin(a*3.+time*.45),p.z);
        q=rot(a*2.1+time*.2)*q;
        return length(q/vec2(1.,.82))-.26-.018*sin(a*36.+q.y*13.-time*.5);
      }
      vec3 normalAt(vec3 p){
        vec2 e=vec2(.0015,-.0015);
        return normalize(e.xyy*field(p+e.xyy)+e.yyx*field(p+e.yyx)+e.yxy*field(p+e.yxy)+e.xxx*field(p+e.xxx));
      }
      void main(){
        vec2 uv=(gl_FragCoord.xy*2.-resolution.xy)/resolution.y;
        vec3 ro=vec3(0.,0.,4.8),rd=normalize(vec3(uv,-2.8));
        float travel=0.,hit=0.;
        for(int i=0;i<68;i++){ vec3 p=ro+rd*travel; float d=field(p); if(d<.0018){hit=1.;break;} travel+=d*.8; if(travel>7.)break; }
        vec3 color=vec3(0.);
        float alpha=0.;
        if(hit>0.){
          vec3 p=ro+rd*travel,n=normalAt(p),light=normalize(vec3(-2.,3.,4.));
          float diff=max(0.,dot(n,light));
          float rim=pow(1.-max(0.,dot(n,-rd)),2.4);
          float spec=pow(max(0.,dot(n,normalize(light-rd))),58.);
          color=vec3(.06,.06,.07)+vec3(.32,.33,.36)*diff+vec3(0.,.48,1.)*rim*.8+vec3(.96,.96,.98)*spec*.55;
          alpha=.97;
        }else{
          float ring=smoothstep(.018,0.,abs(fract(length(uv)*3.1-time*.04)-.5));
          color=vec3(0.,.48,1.)*ring*.08;
          alpha=ring*.08;
        }
        gl_FragColor=vec4(color,alpha);
      }
    `;

    const compile = (type, source) => {
      const shader = gl.createShader(type);
      gl.shaderSource(shader, source);
      gl.compileShader(shader);
      return shader;
    };
    const program = gl.createProgram();
    gl.attachShader(program, compile(gl.VERTEX_SHADER, vertexSource));
    gl.attachShader(program, compile(gl.FRAGMENT_SHADER, fragmentSource));
    gl.linkProgram(program);
    gl.useProgram(program);

    const buffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1,1,-1,-1,1,-1,1,1,-1,1,1]), gl.STATIC_DRAW);
    const position = gl.getAttribLocation(program, 'position');
    gl.enableVertexAttribArray(position);
    gl.vertexAttribPointer(position, 2, gl.FLOAT, false, 0, 0);
    const resolution = gl.getUniformLocation(program, 'resolution');
    const pointer = gl.getUniformLocation(program, 'pointer');
    const time = gl.getUniformLocation(program, 'time');

    let targetX = 0;
    let targetY = 0;
    let currentX = 0;
    let currentY = 0;
    let animationId;
    const startedAt = performance.now();
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const handlePointer = (event) => {
      const rect = canvas.getBoundingClientRect();
      targetX = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      targetY = 1 - ((event.clientY - rect.top) / rect.height) * 2;
    };
    const render = (now) => {
      const ratio = Math.min(window.devicePixelRatio || 1, 1.5);
      const width = Math.max(1, Math.floor(canvas.clientWidth * ratio));
      const height = Math.max(1, Math.floor(canvas.clientHeight * ratio));
      if (canvas.width !== width || canvas.height !== height) {
        canvas.width = width;
        canvas.height = height;
        gl.viewport(0, 0, width, height);
      }
      currentX += (targetX - currentX) * .045;
      currentY += (targetY - currentY) * .045;
      gl.clearColor(0, 0, 0, 0);
      gl.clear(gl.COLOR_BUFFER_BIT);
      gl.uniform2f(resolution, width, height);
      gl.uniform2f(pointer, currentX, currentY);
      gl.uniform1f(time, reducedMotion ? 0 : (now - startedAt) * .001);
      gl.drawArrays(gl.TRIANGLES, 0, 6);
      if (!reducedMotion) animationId = requestAnimationFrame(render);
    };

    window.addEventListener('pointermove', handlePointer, { passive: true });
    render(performance.now());
    return () => {
      if (animationId) cancelAnimationFrame(animationId);
      window.removeEventListener('pointermove', handlePointer);
      gl.deleteProgram(program);
      gl.deleteBuffer(buffer);
    };
  }, []);

  return (
    <div className="hero-shell">
      <header className="hero-nav">
        <div className="hero-brand">
          <span className="hero-brand-icon"><Radio size={17} /></span>
          <span><b>АМУР—ГИДРОСКАН</b><small>TEAM VECTOR · КОСМОХАКАТОН 2026</small></span>
        </div>
        <div className="hero-live"><span /> КОНТУР АКТИВЕН</div>
        <button className="hero-nav-action" onClick={onEnterSituationalCenter}>Открыть карту <ArrowRight size={16} /></button>
      </header>

      <main className="hero-main">
        <section className="hero-copy">
          <div className="hero-kicker"><Satellite size={16} /> SENTINEL-1 SAR · ВСЕПОГОДНЫЙ МОНИТОРИНГ</div>
          <h1>Паводок виден.<br /><em>Даже сквозь облака.</em></h1>
          <p>Оперативный контур Приамурья показывает новое затопление, оценивает ущерб и формирует бюллетень МЧС — по каждому спутниковому наблюдению.</p>
          <div className="hero-actions">
            <button className="hero-primary" onClick={onEnterSituationalCenter}>Открыть ситуационный центр <ArrowRight size={18} /></button>
            <a className="hero-secondary" href="#districts">Обстановка по районам</a>
          </div>
          <div className="hero-proof">
            <div><strong>11</strong><span>пар наблюдений</span></div>
            <div><strong>10 м</strong><span>пространственное разрешение</span></div>
            <div><strong>0.9921</strong><span>итоговый Score</span></div>
          </div>
        </section>

        <section className="hero-visual" aria-label="Радарная визуализация водной динамики">
          <canvas ref={canvasRef} aria-hidden="true" />
          <div className="visual-grid" aria-hidden="true" />
          <div className="visual-label visual-label--top"><span>LIVE</span> ГИДРОЛОГИЧЕСКИЙ КОНТУР</div>
          <div className="visual-reading visual-reading--left"><CloudRain size={16} /><span>ОБЛАЧНОСТЬ</span><strong>НЕ ВЛИЯЕТ</strong></div>
          <div className="visual-reading visual-reading--right"><ShieldCheck size={16} /><span>ЗАТОПЛЕНО</span><strong>{fmt(summary?.total_flood_ha, 0)} га</strong></div>
          <div className="visual-caption">C-BAND / IW GRD / VV+VH</div>
        </section>
      </main>

      <section className="districts-section" id="districts">
        <div className="districts-heading">
          <div><span className="eyebrow">ОПЕРАТИВНАЯ СВОДКА</span><h2>Пять опорных районов Приамурья</h2></div>
          <div className="districts-total"><span>СУММАРНОЕ ЗАТОПЛЕНИЕ</span><strong>{fmt(summary?.total_flood_ha, 0)} га</strong></div>
        </div>
        <div className="districts-grid">
          {districts.map((district) => (
            <button className="district-row" key={district.aoi_id} onClick={() => onSelectDistrict(district.aoi_id)}>
              <span className="district-index">{String(districts.indexOf(district) + 1).padStart(2, '0')}</span>
              <span className="district-name"><strong>{district.name}</strong><small>{district.rivers}</small></span>
              <span className="district-risk"><small>РИСК</small><strong>{district.risk_score}%</strong></span>
              <span className="district-flood"><small>ЗАТОПЛЕНО</small><strong>{fmt(district.flood_ha, 0)} га</strong></span>
              <ArrowRight size={17} />
            </button>
          ))}
        </div>
      </section>

      <footer className="hero-footer"><span>МЧС РОССИИ · АМУРСКОЕ БВУ</span><span>OFFLINE-READY · SENTINEL-1 / SENTINEL-2</span></footer>
    </div>
  );
}

/**
 * TacticalWimaxDashboard.jsx
 * Self-contained React component (no dependencies except React).
 *
 * Quick start in VS Code:
 *   npm create vite@latest wimax-ui -- --template react
 *   cd wimax-ui && npm install
 *   copy this file to src/TacticalWimaxDashboard.jsx
 *   in src/main.jsx:  import App from './TacticalWimaxDashboard.jsx'
 *   npm run dev
 *
 * All numbers are from the project's simulation logs (not physical hardware).
 */
import { useState } from "react";

const REPO = "https://github.com/karthikeshwar2323-prog/tactical-wimax-qos";

// 40 high-traffic NSGA-II Pareto solutions: [throughput, fairness, packet loss]
const T = [69900,70100,69600,68100,67500,69300,67900,67500,67300,69700,69600,69300,67500,69800,67600,68200,67600,67900,70000,67800,68800,68500,68500,69500,68100,69800,69900,68800,68700,68400,67900,68100,67800,69100,67800,68000,67800,68400,69200,68700];
const F = [.8254,.8169,.8314,.8617,.8860,.8504,.8885,.8923,.8922,.8335,.8371,.8511,.8897,.8307,.8777,.8813,.8796,.8761,.8251,.8875,.8531,.8570,.8819,.8508,.8653,.8216,.8195,.8689,.8593,.8681,.8826,.8724,.8863,.8595,.8812,.8659,.8834,.8742,.8527,.8539];
const L = [.1352,.1360,.1369,.1332,.1344,.1342,.1360,.1357,.1355,.1363,.1350,.1367,.1348,.1351,.1341,.1347,.1343,.1340,.1359,.1358,.1340,.1337,.1353,.1350,.1333,.1353,.1356,.1352,.1338,.1344,.1349,.1338,.1354,.1357,.1346,.1335,.1354,.1346,.1347,.1339];
const PBS = { t: 76500, f: 0.5413, l: 0.1351 };

// Multi-seed mean and sample std dev: [PBS mean, PBS sd, NSGA mean, NSGA sd, decimals, lowerIsBetter]
const SEED = {
  Normal: {
    Throughput: [78300, 3037.27, 71012.26, 1494.18, 0, false],
    "Average delay": [5.7808, 0.074, 5.8448, 0.0651, 4, true],
    "Packet loss %": [0.5, 0.62, 0.42, 0.48, 2, true],
    "Jain fairness": [0.5097, 0.0193, 0.8559, 0.0147, 4, false],
    "Utilization %": [99.28, 0.17, 98.67, 0.06, 2, false],
  },
  High: {
    Throughput: [78300, 3037.27, 70892.54, 1724.45, 0, false],
    "Average delay": [6.0745, 0.0757, 6.1102, 0.07, 4, true],
    "Packet loss %": [12.93, 1.77, 12.77, 1.53, 2, true],
    "Jain fairness": [0.5097, 0.0193, 0.8536, 0.0107, 4, false],
    "Utilization %": [99.28, 0.17, 98.64, 0.05, 2, false],
  },
};

const ALLOC = [
  ["Tactical data", 43.88, "var(--ok)"],
  ["Video", 29.33, "var(--cy)"],
  ["Voice", 26.8, "var(--cy)"],
  ["Normal data", 0, "var(--bad)"],
  ["Best effort", 0, "var(--bad)"],
];

const css = `
.tw{--bg:#070c09;--pn:#0d1611;--ln:#1f3a2a;--tx:#cfe8d5;--mu:#7fa08a;--ok:#3dff8a;--am:#ffb020;--bad:#ff4d4d;--cy:#4db8ff;
background:var(--bg);color:var(--tx);min-height:100vh;font:15px/1.6 ui-monospace,Consolas,monospace;
background-image:linear-gradient(var(--ln) 1px,transparent 1px),linear-gradient(90deg,var(--ln) 1px,transparent 1px);background-size:48px 48px}
.tw *{box-sizing:border-box}.tw a{color:var(--ok)}
.tw .wrap{max-width:1040px;margin:auto;padding:0 20px}
.tw header{padding:56px 0 32px;display:grid;grid-template-columns:1.3fr 1fr;gap:28px;align-items:center}
.tw h1{font-size:clamp(28px,5vw,44px);line-height:1.1;margin:8px 0;color:#fff}
.tw .hl{color:var(--ok)}.tw .sub{color:var(--mu);max-width:540px}
.tw .badge{color:var(--am);font-size:12px;letter-spacing:.12em}
.tw .btn{display:inline-block;margin:12px 10px 0 0;padding:9px 16px;border:1px solid var(--ok);text-decoration:none;font-size:13px}
.tw .btn.f{background:var(--ok);color:#04110a;font-weight:700}
.tw .radar{width:100%;max-width:300px;margin:auto;aspect-ratio:1;border:1px solid var(--ok);border-radius:50%;position:relative;overflow:hidden;
background:radial-gradient(circle,transparent 24%,var(--ln) 24.5%,transparent 25.5%,transparent 49%,var(--ln) 49.5%,transparent 50.5%,transparent 74%,var(--ln) 74.5%,transparent 75.5%),#0a1510}
.tw .radar::after{content:"";position:absolute;inset:0;background:conic-gradient(from 0deg,#3dff8a55,transparent 25%);animation:tw-sw 4s linear infinite}
@keyframes tw-sw{to{transform:rotate(360deg)}}
@media (prefers-reduced-motion:reduce){.tw .radar::after{animation:none}}
.tw .pip{position:absolute;width:9px;height:9px;border-radius:50%}
.tw section{padding:40px 0;border-top:1px solid var(--ln)}
.tw h2{font-size:22px;margin:0 0 6px;color:#fff}.tw .lead{color:var(--mu);margin:0 0 16px;max-width:620px}
.tw .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px}
.tw .card{background:var(--pn);border:1px solid var(--ln);border-left:3px solid var(--ok);padding:14px 16px}
.tw .card.am{border-left-color:var(--am)}.tw .card.cy{border-left-color:var(--cy)}
.tw .k{font-size:12px;color:var(--mu)}.tw .big{font-size:26px;font-weight:700;color:#fff;margin:2px 0}
.tw .card p{margin:0;font-size:13px;color:var(--mu)}
.tw .ctl{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 12px}
.tw .ctl button{background:none;border:1px solid var(--ln);color:var(--mu);padding:6px 12px;font:inherit;font-size:12px;cursor:pointer}
.tw .ctl button:focus-visible{outline:2px solid var(--am);outline-offset:2px}
.tw .ctl button.on{background:var(--ok);border-color:var(--ok);color:#04110a;font-weight:700}
.tw .chart{background:var(--pn);border:1px solid var(--ln);padding:10px;overflow-x:auto;position:relative}
.tw svg text{fill:var(--mu);font:11px ui-monospace,Consolas,monospace}
.tw .leg{display:flex;gap:16px;font-size:12px;color:var(--mu);margin:8px 0}.tw .leg i{display:inline-block;width:10px;height:10px;margin-right:6px}
.tw table{width:100%;border-collapse:collapse;font-size:13px}.tw th,.tw td{padding:7px 10px;border-bottom:1px solid var(--ln);text-align:right}
.tw th:first-child,.tw td:first-child{text-align:left}.tw th{color:var(--mu);font-weight:400}
.tw .w{color:var(--ok)}.tw .l{color:var(--bad)}
.tw .row{display:grid;grid-template-columns:120px 1fr 56px;gap:10px;align-items:center;font-size:13px;margin-bottom:8px}
.tw .trk{height:16px;background:#12221a;border:1px solid var(--ln)}.tw .trk div{height:100%}
.tw .tip{position:absolute;pointer-events:none;background:#000;border:1px solid var(--ok);padding:5px 9px;font-size:12px;white-space:nowrap}
.tw .note{font-size:13px;color:var(--mu);margin-top:10px}.tw .note b{color:var(--am)}
.tw .disc{border:1px dashed var(--am);color:var(--am);padding:12px 16px;font-size:13px;margin:10px 0 0}
.tw footer{padding:28px 0 48px;color:var(--mu);font-size:12px}
@media (max-width:760px){.tw header{grid-template-columns:1fr}.tw .row{grid-template-columns:90px 1fr 50px}}
`;

function Toggle({ options, value, onChange }) {
  return (
    <div className="ctl" role="group">
      {options.map((o) => (
        <button key={o} className={o === value ? "on" : ""} aria-pressed={o === value} onClick={() => onChange(o)}>
          {o}
        </button>
      ))}
    </div>
  );
}

function ParetoChart() {
  const [mode, setMode] = useState("Throughput vs fairness");
  const [tip, setTip] = useState(null);
  const fair = mode === "Throughput vs fairness";
  const Y = fair ? F : L;
  const pbsY = fair ? PBS.f : PBS.l;
  const W = 700, H = 340, m = { l: 62, r: 20, t: 14, b: 42 };
  const x0 = 66500, x1 = 77000;
  const all = [...Y, pbsY];
  const pad = (Math.max(...all) - Math.min(...all)) * 0.1;
  const y0 = Math.min(...all) - pad, y1 = Math.max(...all) + pad;
  const sx = (v) => m.l + ((v - x0) / (x1 - x0)) * (W - m.l - m.r);
  const sy = (v) => H - m.b - ((v - y0) / (y1 - y0)) * (H - m.t - m.b);
  const show = (e, html) => {
    const r = e.currentTarget.ownerSVGElement.parentNode.getBoundingClientRect();
    setTip({ x: e.clientX - r.left + 12, y: e.clientY - r.top + 12, html });
  };

  return (
    <>
      <Toggle options={["Throughput vs fairness", "Throughput vs packet loss"]} value={mode} onChange={setMode} />
      <div className="chart">
        <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="Pareto front scatter chart">
          {[0, 1, 2, 3, 4, 5].map((i) => {
            const v = y0 + ((y1 - y0) * i) / 5;
            return (
              <g key={i}>
                <line x1={m.l} x2={W - m.r} y1={sy(v)} y2={sy(v)} stroke="#1f3a2a" />
                <text x={m.l - 8} y={sy(v) + 4} textAnchor="end">{v.toFixed(fair ? 2 : 4)}</text>
              </g>
            );
          })}
          {[67000, 69000, 71000, 73000, 75000, 77000].map((v) => (
            <g key={v}>
              <line x1={sx(v)} x2={sx(v)} y1={m.t} y2={H - m.b} stroke="#1f3a2a" />
              <text x={sx(v)} y={H - m.b + 16} textAnchor="middle">{v / 1000}k</text>
            </g>
          ))}
          <text x={W / 2} y={H - 6} textAnchor="middle">Throughput (bits per time unit)</text>
          <text x={14} y={H / 2} transform={`rotate(-90 14 ${H / 2})`} textAnchor="middle">
            {fair ? "Jain fairness index" : "Packet loss ratio"}
          </text>
          {T.map((t, i) => (
            <circle key={i} cx={sx(t)} cy={sy(Y[i])} r="5" fill="#4db8ff" opacity=".85" style={{ cursor: "pointer" }}
              onMouseMove={(e) => show(e, `NSGA-II-${i + 1} · thr ${t.toLocaleString()} · fair ${F[i]} · loss ${(L[i] * 100).toFixed(2)}%`)}
              onMouseLeave={() => setTip(null)} />
          ))}
          <polygon fill="#ffb020" points={`${sx(PBS.t)},${sy(pbsY) - 10} ${sx(PBS.t) + 3},${sy(pbsY) - 3} ${sx(PBS.t) + 10},${sy(pbsY) - 3} ${sx(PBS.t) + 4},${sy(pbsY) + 2} ${sx(PBS.t) + 6},${sy(pbsY) + 9} ${sx(PBS.t)},${sy(pbsY) + 5} ${sx(PBS.t) - 6},${sy(pbsY) + 9} ${sx(PBS.t) - 4},${sy(pbsY) + 2} ${sx(PBS.t) - 10},${sy(pbsY) - 3} ${sx(PBS.t) - 3},${sy(pbsY) - 3}`}
            onMouseMove={(e) => show(e, "PBS baseline · thr 76,500 · fair 0.5413 · loss 13.51%")} onMouseLeave={() => setTip(null)} />
        </svg>
        {tip && <div className="tip" style={{ left: tip.x, top: tip.y }}>{tip.html}</div>}
      </div>
      <div className="leg">
        <span><i style={{ background: "#4db8ff", borderRadius: "50%" }} />NSGA-II solution</span>
        <span><i style={{ background: "#ffb020" }} />PBS baseline</span>
      </div>
    </>
  );
}

function SeedChart() {
  const [scn, setScn] = useState("High");
  const [met, setMet] = useState("Jain fairness");
  const d = SEED[scn][met];
  const [pm, ps, nm, ns, dp] = d;
  const hi = Math.max(pm + ps, nm + ns) * 1.15;
  const W = 700, H = 280, b = 36, t = 18;
  const y = (v) => H - b - (v / hi) * (H - b - t);
  const fmt = (v) => v.toLocaleString(undefined, { maximumFractionDigits: dp });
  const bars = [["PBS", pm, ps, "#ffb020", 200], ["NSGA-II", nm, ns, "#3dff8a", 420]];

  return (
    <>
      <Toggle options={["Normal", "High"]} value={scn} onChange={setScn} />
      <Toggle options={Object.keys(SEED[scn])} value={met} onChange={setMet} />
      <div className="chart">
        <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label={`${met}: PBS vs NSGA-II`}>
          {[0, 1, 2, 3, 4].map((i) => (
            <g key={i}>
              <line x1="70" x2="680" y1={y((hi * i) / 4)} y2={y((hi * i) / 4)} stroke="#1f3a2a" />
              <text x="62" y={y((hi * i) / 4) + 4} textAnchor="end">{(hi * i) / 4 >= 1000 ? Math.round((hi * i) / 4000) + "k" : ((hi * i) / 4).toFixed(2)}</text>
            </g>
          ))}
          {bars.map(([n, v, sd, c, x]) => (
            <g key={n}>
              <rect x={x} y={y(v)} width="110" height={H - b - y(v)} fill={c} opacity=".9">
                <title>{`${n}: ${fmt(v)} ± ${sd}`}</title>
              </rect>
              <line x1={x + 55} x2={x + 55} y1={y(v + sd)} y2={y(Math.max(v - sd, 0))} stroke="#fff" strokeWidth="2" />
              <line x1={x + 47} x2={x + 63} y1={y(v + sd)} y2={y(v + sd)} stroke="#fff" strokeWidth="2" />
              <line x1={x + 47} x2={x + 63} y1={y(Math.max(v - sd, 0))} y2={y(Math.max(v - sd, 0))} stroke="#fff" strokeWidth="2" />
              <text x={x + 55} y={H - b + 18} textAnchor="middle" style={{ fill: "#cfe8d5" }}>{n}</text>
            </g>
          ))}
        </svg>
      </div>
      <div className="chart" style={{ marginTop: 12 }}>
        <table>
          <thead><tr><th>Metric</th><th>PBS</th><th>NSGA-II</th><th>Change</th></tr></thead>
          <tbody>
            {Object.entries(SEED[scn]).map(([k, q]) => {
              const ch = ((q[2] - q[0]) / q[0]) * 100;
              const good = q[5] ? ch < 0 : ch > 0;
              const f = (v) => v.toLocaleString(undefined, { maximumFractionDigits: q[4] });
              return (
                <tr key={k}>
                  <td>{k}</td>
                  <td>{f(q[0])} ± {q[1]}</td>
                  <td>{f(q[2])} ± {q[3]}</td>
                  <td className={good ? "w" : "l"}>{ch > 0 ? "+" : ""}{ch.toFixed(1)}%</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </>
  );
}

export default function TacticalWimaxDashboard() {
  return (
    <div className="tw">
      <style>{css}</style>
      <div className="wrap">
        <header>
          <div>
            <div className="badge">Simulation · NSGA-II · 5 seeds · 2 traffic loads</div>
            <h1>Tactical WiMAX <span className="hl">QoS Optimization</span></h1>
            <p className="sub">
              Multi-objective evolutionary scheduling for mission-critical wireless networks. NSGA-II gives up a little
              throughput to serve voice, video, tactical, normal and best-effort traffic far more fairly.
            </p>
            <a className="btn f" href="#results">View results</a>
            <a className="btn" href={REPO} target="_blank" rel="noopener noreferrer">GitHub repo</a>
          </div>
          <div className="radar" aria-hidden="true">
            <i className="pip" style={{ left: "58%", top: "30%", background: "var(--ok)" }} />
            <i className="pip" style={{ left: "30%", top: "42%", background: "var(--cy)" }} />
            <i className="pip" style={{ left: "66%", top: "64%", background: "var(--am)" }} />
            <i className="pip" style={{ left: "44%", top: "70%", background: "var(--ok)" }} />
          </div>
        </header>

        <section id="results">
          <h2>Headline results (high traffic, 2.0×)</h2>
          <p className="lead">Averages over seeds 42, 123, 2026, 7 and 99. Setup: 20 users, 100 resource units, population 40, 50 generations.</p>
          <div className="grid">
            <div className="card"><div className="k">Jain fairness</div><div className="big">0.51 → 0.85</div><p>+67% versus the PBS baseline</p></div>
            <div className="card am"><div className="k">Throughput cost</div><div className="big">−9.5%</div><p>78,300 → 70,893 bits per time unit</p></div>
            <div className="card cy"><div className="k">Packet loss</div><div className="big">12.9% → 12.8%</div><p>Unchanged within one standard deviation</p></div>
            <div className="card"><div className="k">Pareto solutions</div><div className="big">40 high · 39 normal</div><p>Non-dominated schedules to choose from</p></div>
          </div>
        </section>

        <section>
          <h2>Pareto explorer</h2>
          <p className="lead">The 40 high-traffic NSGA-II schedules against the PBS baseline. Hover a point for exact values.</p>
          <ParetoChart />
          <div className="note"><b>Trade-off:</b> every NSGA-II schedule reaches 0.82–0.89 fairness against PBS at 0.54, at lower throughput.</div>
        </section>

        <section>
          <h2>Multi-seed validation</h2>
          <p className="lead">Mean ± sample standard deviation across five seeds.</p>
          <SeedChart />
        </section>

        <section>
          <h2>Why PBS fairness is low</h2>
          <p className="lead">Resource units given to each traffic class by PBS in the high-traffic run (out of 100).</p>
          {ALLOC.map(([n, v, c]) => (
            <div className="row" key={n}>
              <span>{n}</span>
              <div className="trk"><div style={{ width: `${v}%`, background: c }} /></div>
              <span>{v.toFixed(2)}</span>
            </div>
          ))}
          <div className="note"><b>Result:</b> normal-data and best-effort users received nothing, which is what drags Jain’s index down to 0.54.</div>
          <div className="disc">All figures come from a software simulation, not measurements from physical WiMAX equipment.</div>
        </section>

        <footer>Tactical WiMAX QoS Optimization · <a href={REPO} target="_blank" rel="noopener noreferrer">source on GitHub</a></footer>
      </div>
    </div>
  );
}

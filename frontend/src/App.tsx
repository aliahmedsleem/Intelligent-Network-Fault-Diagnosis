import { useState } from "react";
import { Activity, Network, ShieldAlert, GitBranch, Play, RotateCcw, CheckCircle2 } from "lucide-react";

type Link = {id:string;source:string;target:string;medium:string;capacity_mbps:number;delay_ms:number;loss_percent?:number};
type Experiment = {network:{nodes:string[];links:Link[]};source:string;target:string;offered_load_mbps:number;failed_link_id:string};
type Result = {mode:string;before:{path:string[];estimated_throughput_mbps:number;baseline_delay_ms:number;estimated_loss_percent:number};after:{path:string[];estimated_throughput_mbps:number;baseline_delay_ms:number;estimated_loss_percent:number;connected:boolean;diagnosis:string};route_changed:boolean};
const scenario:Experiment={network:{nodes:["CORE","SW-01","FIBER","EDGE","WIFI"],links:[
{id:"eth-01",source:"CORE",target:"SW-01",medium:"ethernet",capacity_mbps:1000,delay_ms:1},
{id:"fiber-01",source:"SW-01",target:"FIBER",medium:"fiber",capacity_mbps:500,delay_ms:2},
{id:"fiber-02",source:"FIBER",target:"EDGE",medium:"fiber",capacity_mbps:500,delay_ms:2},
{id:"wifi-01",source:"CORE",target:"WIFI",medium:"wifi_5",capacity_mbps:100,delay_ms:4},
{id:"wifi-02",source:"WIFI",target:"EDGE",medium:"wifi_2_4",capacity_mbps:50,delay_ms:5}
]},source:"CORE",target:"EDGE",offered_load_mbps:200,failed_link_id:"fiber-02"};
const positions:Record<string,[number,number]>={CORE:[85,145],"SW-01":[245,70],FIBER:[410,70],EDGE:[575,145],WIFI:[310,225]};
const metrics=(v:number|undefined,unit:string)=>v===undefined?"—":v.toFixed(2)+" "+unit;
export default function App(){
 const [fault,setFault]=useState("fiber-02");
 const [load,setLoad]=useState(200);
 const [result,setResult]=useState<Result|null>(null);
 const [busy,setBusy]=useState(false);
 const [error,setError]=useState("");
 async function run(){
  setBusy(true);setError("");
  try{
   const response=await fetch("/api/experiments/link-fault",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({...scenario,failed_link_id:fault,offered_load_mbps:load})});
   if(!response.ok)throw new Error("API returned "+response.status+". Check backend service.");
   setResult(await response.json());
  }catch(e){setError(e instanceof Error?e.message:"Unknown error");}finally{setBusy(false);}
 }
 return <div className="shell">
  <aside className="sidebar"><div className="brand"><Network size={23}/> <span>NETWORK <b>INTELLIGENCE</b></span></div><div className="nav active"><Activity size={17}/> Overview</div><div className="nav"><GitBranch size={17}/> Topology Laboratory</div><div className="nav"><ShieldAlert size={17}/> Fault Experiments</div><div className="asidefoot">SCIENTIFIC LABORATORY <small>Analytical baseline · v0.1</small></div></aside>
  <main><header><div><div className="eyebrow">ENGINEERING WORKSPACE / EXPERIMENTS</div><h1>Network Fault Laboratory</h1><p>Deterministic path and link-failure analysis</p></div><div className="status"><span className="dot"/> Analytical engine</div></header>
  <section className="stats"><article><small>NETWORK NODES</small><strong>05</strong><span>Sample topology</span></article><article><small>ACTIVE LINKS</small><strong>05</strong><span>Hybrid media</span></article><article><small>OFFERED LOAD</small><strong>{load} <em>Mbps</em></strong><span>Configurable experiment</span></article><article><small>EXPERIMENT STATE</small><strong>{result?"Complete":"Ready"}</strong><span>No real packet traffic yet</span></article></section>
  <div className="columns"><section className="panel topology"><div className="panelhead"><div><h2>Network Topology</h2><p>Five-node reference scenario</p></div><span className="tag">GRAPH MODEL</span></div>
   <svg viewBox="0 0 660 300" role="img" aria-label="Reference network topology">
   {scenario.network.links.map(l=>{const a=positions[l.source],b=positions[l.target];return <line key={l.id} x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]} stroke={result&&fault===l.id?"#f87171":"#3f79ad"} strokeWidth="3" strokeDasharray={result&&fault===l.id?"7 5":"none"}/>})}
   {Object.entries(positions).map(([id,[x,y]])=><g key={id}><rect x={x-43} y={y-20} width="86" height="40" rx="9" fill="#19334d" stroke="#3977a8"/><text x={x} y={y+5} fill="#e8f3ff" textAnchor="middle" fontSize="13" fontWeight="600">{id}</text></g>)}
   </svg><div className="legend"><span><i className="blue"/> Available link</span><span><i className="red"/> Injected fault</span></div></section>
   <section className="panel controls"><div className="panelhead"><div><h2>Fault Injection</h2><p>Controlled analytical experiment</p></div><ShieldAlert size={20}/></div>
   <label htmlFor="fault">Failed link</label><select id="fault" value={fault} onChange={e=>{setFault(e.target.value);setResult(null)}}>{scenario.network.links.map(l=><option key={l.id} value={l.id}>{l.id} · {l.medium}</option>)}</select>
   <label htmlFor="load">Offered load (Mbps)</label><input id="load" type="number" min="1" max="1000000" value={load} onChange={e=>{setLoad(Number(e.target.value));setResult(null)}}/>
   <button disabled={busy||load<=0} onClick={run}><Play size={16}/>{busy?"Running...":"Run experiment"}</button><button className="secondary" onClick={()=>{setResult(null);setError("");setLoad(200);setFault("fiber-02")}}><RotateCcw size={16}/> Reset</button>
   {error&&<div className="error" role="alert">{error}</div>}</section></div>
   <section className="panel results"><div className="panelhead"><div><h2>Experiment Results</h2><p>Estimated values — not measured network traffic</p></div>{result&&<span className="tag"><CheckCircle2 size={14}/> COMPLETED</span>}</div>
   {result?<><div className="comparison"><div><small>BASELINE THROUGHPUT</small><strong>{metrics(result.before.estimated_throughput_mbps,"Mbps")}</strong></div><div><small>AFTER FAULT</small><strong>{metrics(result.after.estimated_throughput_mbps,"Mbps")}</strong></div><div><small>BASELINE DELAY</small><strong>{metrics(result.before.baseline_delay_ms,"ms")}</strong></div><div><small>POST-FAULT DELAY</small><strong>{result.after.connected?metrics(result.after.baseline_delay_ms,"ms"):"No route"}</strong></div></div><p className="path">Before: {result.before.path.join(" → ")}<br/>After: {result.after.path.length?result.after.path.join(" → "):"Disconnected"}</p></>:<div className="empty">Run a controlled experiment to compare the baseline path with a failed-link scenario.</div>}
   </section><footer>RESEARCH MODE · Analytical estimates only · No production network changes</footer>
  </main></div>;
}

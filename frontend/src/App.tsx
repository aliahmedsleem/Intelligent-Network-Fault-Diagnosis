import Ns3ResultsLab from "./Ns3ResultsLab";
import ReferenceTopology from "./ReferenceTopology";
import LinkBudgetLab from "./LinkBudgetLab";
import { useState } from "react";
import { Activity, ArrowRight, CheckCircle2, CircleAlert, Cpu, GitBranch, Network, Play, RadioTower, RotateCcw, ShieldAlert, Zap } from "lucide-react";

type Medium="ethernet"|"fiber"|"wifi_2_4"|"wifi_5"|"microwave";
type Link={id:string;source:string;target:string;medium:Medium;capacity_mbps:number;delay_ms:number;loss_percent?:number};
type NetworkData={nodes:string[];links:Link[]};
type Report={mode:string;before:Result;after:Result;route_changed:boolean;localization:{known_injected_link_id:string;warning:string}};
type Result={path:string[];link_ids:string[];connected:boolean;bottleneck_mbps:number;offered_load_mbps:number;estimated_throughput_mbps:number;baseline_delay_ms:number;estimated_loss_percent:number;diagnosis:string};
type View="overview"|"topology"|"experiments"|"measurements"|"localization"|"closed_loop"|"link_budget"|"ns3_wifi";
type ClosedLoopResult={mode:string;reported_status:string;audit_status:string;quality_flags:string[];inference:LocalizationResult;execution_policy_reported:{authorized:boolean;reason:string;candidate:string|null};probes:{source:string;target:string;baseline_loss_percent:number;observed_loss_percent:number;recovered_loss_percent:number|null}[];ground_truth_evaluation:{link_id:string;top1_correct_recomputed:boolean}};
type LocalizationResult={status:string;suspected_link_id:string|null;tied_candidates:string[];rankings:{link_id:string;score:number;degraded_paths_covered:number;healthy_paths_contradicted:number}[]};
type MeasurementReport={mode:string;topology:string;measurements:{before:{throughput_mbps:number|null;loss_percent:number|null;rtt_avg_ms:number|null};after:{throughput_mbps:number|null;loss_percent:number|null;rtt_avg_ms:number|null};throughput_change_mbps:number|null;loss_change_percentage_points:number|null};evidence:string[];quality_flags:string[];localization:{status:string}};
const network:NetworkData={nodes:["CORE","SW-01","FIBER","EDGE","WIFI"],links:[
{id:"eth-01",source:"CORE",target:"SW-01",medium:"ethernet",capacity_mbps:1000,delay_ms:1},
{id:"fiber-01",source:"SW-01",target:"FIBER",medium:"fiber",capacity_mbps:500,delay_ms:2},
{id:"fiber-02",source:"FIBER",target:"EDGE",medium:"fiber",capacity_mbps:500,delay_ms:2},
{id:"wifi-01",source:"CORE",target:"WIFI",medium:"wifi_5",capacity_mbps:100,delay_ms:4},
{id:"wifi-02",source:"WIFI",target:"EDGE",medium:"wifi_2_4",capacity_mbps:50,delay_ms:5}
]};
const mediumNames:Record<Medium,string>={ethernet:"Ethernet",fiber:"Fiber optic",wifi_2_4:"Wi-Fi 2.4 GHz",wifi_5:"Wi-Fi 5 GHz",microwave:"Microwave"};
const fmt=(v:number,unit="")=>v.toLocaleString("en-US",{maximumFractionDigits:2})+(unit?" "+unit:"");
export default function App(){
 const [view,setView]=useState<View>("overview");
 const [measured,setMeasured]=useState<MeasurementReport|null>(null);
 const [measurementFile,setMeasurementFile]=useState<File|null>(null);
 const [measurementError,setMeasurementError]=useState("");
 const [measurementBusy,setMeasurementBusy]=useState(false);
 const [localization,setLocalization]=useState<LocalizationResult|null>(null);
 const [localizationBusy,setLocalizationBusy]=useState(false);
 const [localizationError,setLocalizationError]=useState("");
 const [closedLoopFile,setClosedLoopFile]=useState<File|null>(null);
 const [closedLoopResult,setClosedLoopResult]=useState<ClosedLoopResult|null>(null);
 const [closedLoopBusy,setClosedLoopBusy]=useState(false);
 const [closedLoopError,setClosedLoopError]=useState("");
 const [source,setSource]=useState("CORE");
 const [target,setTarget]=useState("EDGE");
 const [fault,setFault]=useState("fiber-02");
 const [load,setLoad]=useState(200);
 const [report,setReport]=useState<Report|null>(null);
 const [busy,setBusy]=useState(false);
 const [error,setError]=useState("");
 const [selected,setSelected]=useState<string|null>("fiber-02");
 const affected=report?.after.link_ids||[];
 const isValid=Number.isFinite(load)&&load>0&&load<=1_000_000&&source!==target;
 const nav:[View,string,typeof Activity][]=[["overview","Overview",Activity],["topology","Topology",Network],["experiments","Experiments",ShieldAlert],["measurements","Measurements",Activity],["localization","Localization",GitBranch],["closed_loop","Closed Loop",RotateCcw],["link_budget","Link Budgets",RadioTower],["ns3_wifi","ns-3 Wi-Fi",Activity]];
 function reset(){setSource("CORE");setTarget("EDGE");setFault("fiber-02");setLoad(200);setReport(null);setError("");setSelected("fiber-02");}
 async function inspectClosedLoop(){
  if(!closedLoopFile)return;
  setClosedLoopBusy(true);setClosedLoopError("");setClosedLoopResult(null);
  try{
   if(closedLoopFile.size>2_000_000)throw new Error("JSON file exceeds 2 MB limit");
   const raw=JSON.parse(await closedLoopFile.text());
   const response=await fetch("/api/lifecycle/inspect",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(raw)});
   if(!response.ok)throw new Error("Closed-loop inspection failed (HTTP "+response.status+")");
   setClosedLoopResult(await response.json());
  }catch(e){setClosedLoopError(e instanceof Error?e.message:"Could not inspect file");}finally{setClosedLoopBusy(false);}
 }
 async function runLocalization(){
  setLocalizationBusy(true);setLocalizationError("");
  try{
   const probes=[
    {source:"CORE",target:"FIBER",baseline_loss_percent:0,observed_loss_percent:18},
    {source:"SW-01",target:"EDGE",baseline_loss_percent:0,observed_loss_percent:22},
    {source:"CORE",target:"SW-01",baseline_loss_percent:0,observed_loss_percent:0},
    {source:"FIBER",target:"EDGE",baseline_loss_percent:0,observed_loss_percent:0}
   ];
   const response=await fetch("/api/localization/analyze",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({network,probes})});
   if(!response.ok)throw new Error("Localization API returned HTTP "+response.status);
   setLocalization(await response.json());
  }catch(e){setLocalizationError(e instanceof Error?e.message:"Localization failed");}finally{setLocalizationBusy(false);}
 }
 async function importMeasurements(){
  if(!measurementFile)return;
  setMeasurementBusy(true);setMeasurementError("");
  try{
   if(measurementFile.size>2_000_000)throw new Error("JSON file exceeds 2 MB limit");
   const raw=JSON.parse(await measurementFile.text());
   const response=await fetch("/api/measurements/analyze",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(raw)});
   if(!response.ok)throw new Error("Invalid measurement data (HTTP "+response.status+")");
   setMeasured(await response.json());
  }catch(e){setMeasurementError(e instanceof Error?e.message:"Import failed");}finally{setMeasurementBusy(false);}
 }
 async function run(){
  if(!isValid)return;
  setBusy(true);setError("");setReport(null);
  try{
   const response=await fetch("/api/experiments/link-fault",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({network,source,target,offered_load_mbps:load,failed_link_id:fault})});
   if(!response.ok){const body=await response.json().catch(()=>null);throw new Error(typeof body?.detail==="string"?body.detail:"Experiment failed (HTTP "+response.status+")");}
   const data:Report=await response.json();setReport(data);setView("experiments");
  }catch(e){setError(e instanceof Error?e.message:"Unable to complete experiment");}finally{setBusy(false);}
 }
 return <div className="app-shell">
 <aside className="sidebar"><div className="identity"><span className="identity-icon"><Network size={23}/></span><div><strong>NETFAULT<span> / LAB</span></strong><small>ENGINEERING CONSOLE</small></div></div>
 <div className="nav-heading">WORKSPACE</div><nav aria-label="Primary navigation">{nav.map(([id,label,Icon])=><button key={id} className={"nav-item "+(view===id?"active":"")} onClick={()=>setView(id)} aria-current={view===id?"page":undefined}><Icon size={18}/>{label}{view===id&&<span className="nav-active-dot"/>}</button>)}</nav>
 <div className="side-spacer"/><div className="system-card"><div className="system-row"><span className="pulse"/> SYSTEM STATUS</div><strong>Analytical engine</strong><small>API-connected experiments</small><div className="system-divider"/><span className="system-version">RESEARCH BUILD · 0.2</span></div><div className="side-bottom">NETWORK FAULT DIAGNOSIS<br/>VIRTUAL LABORATORY</div></aside>
 <main className="main-content"><header className="topbar"><div><div className="breadcrumbs">LABORATORY <span>/</span> {view.toUpperCase()}</div><h1>{view==="overview"?"Network Overview":view==="topology"?"Network Topology":view==="experiments"?"Fault Experiments":view==="measurements"?"Measured Results":view==="localization"?"Fault Localization":view==="closed_loop"?"Closed Loop":view==="link_budget"?"Link Budgets":"ns-3 Wi-Fi Results"}</h1><p className="subtitle">{view==="overview"?"Observe the topology and run controlled fault scenarios":view==="topology"?"Inspect virtual links, media and reference parameters":view==="experiments"?"Compare baseline and fault-injected analytical outcomes":view==="measurements"?"Inspect imported Mininet packet measurements":view==="localization"?"Explainable multi-path link ranking":view==="closed_loop"?"Measured diagnosis, gated repair and recovery audit":view==="link_budget"?"Fiber and wireless engineering budgets":"Inspect packet-level simulated Wi-Fi output"}</p></div><div className="topbar-right"><span className="mode-label"><span className="pulse"/> ANALYTICAL MODE</span><span className="version-label">v0.2</span></div></header>
 <div className="notice"><CircleAlert size={16}/><span>{view==="measurements"||view==="closed_loop"?"Imported Mininet observations are measured inside a virtual network; source files are not independently authenticated.":view==="link_budget"?"Power budgets are analytical calculations, not packet-level simulations or physical measurements.":view==="ns3_wifi"?"ns-3 outputs are simulated packet observations, not physical measurements.":"Analytical network results are estimates. Packet-level Mininet and ns-3 experiments are separate pipelines."}</span></div>
 {(view==="overview")&&<>
<section className="metrics"><div className="metric"><div className="metric-top"><span>NETWORK NODES</span><Cpu size={18}/></div><strong>{String(network.nodes.length).padStart(2,"0")}</strong><small>Reference topology</small></div><div className="metric"><div className="metric-top"><span>VIRTUAL LINKS</span><GitBranch size={18}/></div><strong>{String(network.links.length).padStart(2,"0")}</strong><small>Mixed connectivity</small></div><div className="metric"><div className="metric-top"><span>OFFERED LOAD</span><Activity size={18}/></div><strong>{fmt(load)} <em>Mbps</em></strong><small>Configured traffic</small></div><div className="metric"><div className="metric-top"><span>EXPERIMENT</span><Zap size={18}/></div><strong className="metric-state">{busy?"Running":report?"Complete":"Ready"}</strong><small>{report?"Last run available":"Awaiting execution"}</small></div></section>
 </>}
{(view==="overview"||view==="topology"||view==="experiments")&&<>
<div className={"workspace-grid "+(view==="topology"?"topology-only":"")}><ReferenceTopology nodes={network.nodes} links={network.links} selected={selected} onSelect={setSelected} source={source} target={target} failedLink={fault} affectedLinks={affected} hasExperiment={Boolean(report)}/>
 {view!=="topology"&&<section className="panel experiment-panel"><div className="section-header"><div><div className="section-kicker">CONTROL CENTER</div><h2>Fault Injection</h2></div><ShieldAlert size={20} className="panel-icon"/></div>
 <div className="field-pair"><div className="field"><label htmlFor="source">Source</label><select id="source" value={source} onChange={e=>{setSource(e.target.value);setReport(null)}}>{network.nodes.map(n=><option key={n}>{n}</option>)}</select></div><div className="field"><label htmlFor="target">Destination</label><select id="target" value={target} onChange={e=>{setTarget(e.target.value);setReport(null)}}>{network.nodes.map(n=><option key={n}>{n}</option>)}</select></div></div>
 <div className="field"><label htmlFor="fault">Faulted link</label><select id="fault" value={fault} onChange={e=>{setFault(e.target.value);setSelected(e.target.value);setReport(null)}}>{network.links.map(l=><option key={l.id} value={l.id}>{l.id} · {mediumNames[l.medium]}</option>)}</select></div>
 <div className="field"><div className="label-row"><label htmlFor="load">Offered load</label><span>{fmt(load,"Mbps")}</span></div><input id="load" type="range" min="10" max="1000" step="10" value={Math.min(1000,Math.max(10,load))} onChange={e=>{setLoad(Number(e.target.value));setReport(null)}}/><div className="range-labels"><span>10 Mbps</span><span>1000 Mbps</span></div></div>
 <div className="experiment-actions"><button className="primary-button" disabled={!isValid||busy} onClick={run}><Play size={16}/>{busy?"Running experiment...":"Run Experiment"}<ArrowRight size={16}/></button><button className="reset-button" onClick={reset} title="Reset scenario"><RotateCcw size={17}/></button></div>{source===target&&<p className="form-error">Source and destination must differ.</p>}{error&&<p className="form-error" role="alert">{error}</p>}
 <div className="control-footer"><RadioTower size={15}/> Fault injection is restricted to the analytical model.</div></section>}</div>
 </>}
{(view==="overview"||view==="experiments")&&<>
<section className="panel results-panel"><div className="section-header"><div><div className="section-kicker">OBSERVABILITY</div><h2>Experiment Results</h2></div>{report?<span className="success-tag"><CheckCircle2 size={14}/> COMPLETED</span>:<span className="soft-tag">NO RESULTS</span>}</div>
 {report?<><div className="results-grid"><div className="result-cell"><small>BASELINE THROUGHPUT</small><strong>{fmt(report.before.estimated_throughput_mbps)} <em>Mbps</em></strong></div><div className="result-cell"><small>AFTER FAULT</small><strong>{fmt(report.after.estimated_throughput_mbps)} <em>Mbps</em></strong></div><div className="result-cell"><small>BASELINE DELAY</small><strong>{fmt(report.before.baseline_delay_ms)} <em>ms</em></strong></div><div className="result-cell"><small>POST-FAULT DELAY</small><strong>{report.after.connected?fmt(report.after.baseline_delay_ms):"No route"} <em>{report.after.connected?"ms":""}</em></strong></div></div><div className="route-summary"><div><span>BASELINE PATH</span><strong>{report.before.path.join(" → ")||"Disconnected"}</strong></div><div><span>AFTER FAULT</span><strong>{report.after.path.join(" → ")||"Disconnected"}</strong></div><div><span>DIAGNOSIS</span><strong>{report.after.diagnosis.replace(/_/g," ")}</strong></div></div></>:<div className="empty-results"><Activity size={28}/><strong>No experiment data yet</strong><span>Configure a link fault and run an experiment to populate the comparison.</span></div>}</section>
 </>}
{(view==="measurements")&&<>
<section className="panel measured-panel"><div className="section-header"><div><div className="section-kicker">MININET / IMPORT</div><h2>Measured Network Traffic</h2></div><span className="soft-tag">ICMP + TCP</span></div>
 <p className="measured-intro">Import the JSON generated by the Ubuntu Mininet experiment. This is a separate measurement pipeline; it does not simulate traffic in the browser.</p>
 <div className="measurement-actions"><input aria-label="Select Mininet JSON file" type="file" accept=".json,application/json" onChange={e=>{setMeasurementFile(e.target.files?.[0]||null);setMeasurementError("");}}/><button className="primary-button" disabled={!measurementFile||measurementBusy} onClick={importMeasurements}>{measurementBusy?"Analyzing...":"Analyze measurements"}</button></div>
 {measurementError&&<p className="form-error" role="alert">{measurementError}</p>}
 {measured?<><div className="results-grid"><div className="result-cell"><small>BASELINE TCP</small><strong>{measured.measurements.before.throughput_mbps===null?"N/A":fmt(measured.measurements.before.throughput_mbps)} <em>Mbps</em></strong></div><div className="result-cell"><small>FAULT TCP</small><strong>{measured.measurements.after.throughput_mbps===null?"N/A":fmt(measured.measurements.after.throughput_mbps)} <em>Mbps</em></strong></div><div className="result-cell"><small>BASELINE ICMP LOSS</small><strong>{measured.measurements.before.loss_percent===null?"N/A":fmt(measured.measurements.before.loss_percent)} <em>%</em></strong></div><div className="result-cell"><small>FAULT ICMP LOSS</small><strong>{measured.measurements.after.loss_percent===null?"N/A":fmt(measured.measurements.after.loss_percent)} <em>%</em></strong></div></div><div className="measurement-evidence"><strong>Evidence</strong><span>{measured.evidence.join(" · ")||"No threshold evidence"}</span><strong>Data quality</strong><span>{measured.quality_flags.length?measured.quality_flags.join(" · "):"No parser flags"}</span></div></>:<div className="empty-results"><Activity size={26}/><strong>No Mininet measurement imported</strong><span>Generate an experiment JSON on Ubuntu, then select it above.</span></div>}</section>
 </>}
{(view==="localization")&&<>
<section className="panel measured-panel"><div className="section-header"><div><div className="section-kicker">TOPOLOGY INFERENCE</div><h2>Fault Localization</h2></div><span className="soft-tag">EXPLAINABLE HEURISTIC</span></div>
 <p className="measured-intro">Evaluate a fixed four-probe illustrative dataset. These probe losses are synthetic demonstration inputs, not imported Mininet measurements. The inference engine does not receive the injected fault identity.</p>
 <div className="measurement-actions"><button className="primary-button" disabled={localizationBusy} onClick={runLocalization}><GitBranch size={16}/>{localizationBusy?"Analyzing...":"Analyze probe paths"}</button></div>
 {localizationError&&<p className="form-error" role="alert">{localizationError}</p>}
 {localization?<><div className="localization-summary"><div><small>STATUS</small><strong>{localization.status.replace(/_/g," ")}</strong></div><div><small>SUSPECTED LINK</small><strong>{localization.suspected_link_id||"Not uniquely identified"}</strong></div></div><div className="ranking-list">{localization.rankings.map((r,i)=><div className="ranking-item" key={r.link_id}><span>{String(i+1).padStart(2,"0")}</span><strong>{r.link_id}</strong><div className="ranking-track"><i style={{width:(Math.max(0,r.score)*100)+"%"}}/></div><em>{r.score.toFixed(2)}</em></div>)}</div><p className="measured-intro">Scores are relative evidence, not probabilities. Equal top candidates remain ambiguous.</p></>:<div className="empty-results"><GitBranch size={26}/><strong>No localization analysis yet</strong><span>Run the illustrative multi-path example to inspect ranked candidate links.</span></div>}</section>
 </>}
{(view==="closed_loop")&&<>
<section className="panel measured-panel"><div className="section-header"><div><div className="section-kicker">CLOSED-LOOP / IMPORT</div><h2>Diagnosis to Recovery Audit</h2></div><span className="soft-tag">MEASURED LAB</span></div>
 <p className="measured-intro">Import a JSON report produced by the dedicated Ubuntu Mininet closed-loop experiment. The API audits recorded data; it does not execute privileged network operations.</p>
 <div className="measurement-actions"><input aria-label="Select closed-loop experiment JSON" type="file" accept=".json,application/json" onChange={e=>{setClosedLoopFile(e.target.files?.[0]||null);setClosedLoopError("");setClosedLoopResult(null)}}/><button className="primary-button" disabled={!closedLoopFile||closedLoopBusy} onClick={inspectClosedLoop}><RotateCcw size={16}/>{closedLoopBusy?"Inspecting...":"Inspect closed loop"}</button></div>
 {closedLoopError&&<p className="form-error" role="alert">{closedLoopError}</p>}
 {closedLoopResult?<><div className="localization-summary"><div><small>AUDIT</small><strong>{closedLoopResult.audit_status}</strong></div><div><small>REPORTED VERIFICATION</small><strong>{closedLoopResult.reported_status}</strong></div><div><small>INFERRED LINK</small><strong>{closedLoopResult.inference.suspected_link_id||"Ambiguous / none"}</strong></div><div><small>LAB ACTION</small><strong>{closedLoopResult.execution_policy_reported.authorized?"Authorized":"Blocked"}</strong></div></div><div className="measurement-evidence"><strong>Quality flags</strong><span>{closedLoopResult.quality_flags.length?closedLoopResult.quality_flags.join(" · "):"No contract inconsistencies detected"}</span><strong>Top-1 match</strong><span>{closedLoopResult.ground_truth_evaluation.top1_correct_recomputed?"Match":"No match"} (evaluation only)</span></div><div className="probe-table-wrap"><table className="probe-table"><thead><tr><th>Path</th><th>Baseline loss</th><th>Fault loss</th><th>Recovery loss</th></tr></thead><tbody>{closedLoopResult.probes.map((p,i)=><tr key={p.source+"-"+p.target+"-"+i}><td>{p.source} → {p.target}</td><td>{fmt(p.baseline_loss_percent)}%</td><td>{fmt(p.observed_loss_percent)}%</td><td>{p.recovered_loss_percent===null?"Not measured":fmt(p.recovered_loss_percent)+"%"}</td></tr>)}</tbody></table></div><p className="measured-intro">A consistent artifact is not proof of physical execution or statistically validated recovery.</p></>:<div className="empty-results"><RotateCcw size={26}/><strong>No closed-loop report imported</strong><span>Run the isolated Mininet experiment, then import its JSON output.</span></div>}</section>
 </>}
{(view==="link_budget")&&<>
<LinkBudgetLab/>
 </>}
{view==="ns3_wifi"&&<Ns3ResultsLab/>}
<footer className="page-footer"><span>NETFAULT LAB · SCIENTIFIC RESEARCH ENVIRONMENT</span><span>ESTIMATES ≠ MEASUREMENTS</span></footer>
 </main></div>;
}

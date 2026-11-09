import { useState } from "react";
import { Activity, FileJson, ShieldCheck, Wifi } from "lucide-react";

type Run = {mode:string;standard:string;seed:number;run:number;distance_m:number;duration_s:number;offered_mbps:number;tx_packets:number;rx_packets:number;packet_loss_percent:number;throughput_mbps:number;mean_delay_ms:number};
type Audit = {mode:string;audit_status:"consistent"|"inconsistent";quality_flags:string[];experiment:Run;caveats:string[]};
const fmt=(n:number)=>n.toLocaleString("en-US",{maximumFractionDigits:3});
const fields:[keyof Run,string,string][]=[["distance_m","Distance","m"],["offered_mbps","Offered load","Mbps"],["throughput_mbps","Throughput","Mbps"],["packet_loss_percent","Packet loss","%"],["mean_delay_ms","Mean delay","ms"],["tx_packets","TX packets",""],["rx_packets","RX packets",""],["seed","Seed",""],["run","Run",""]];
export default function Ns3ResultsLab(){
 const [file,setFile]=useState<File|null>(null);
 const [audit,setAudit]=useState<Audit|null>(null);
 const [error,setError]=useState("");
 const [busy,setBusy]=useState(false);
 async function inspect(){
  if(!file)return;
  setBusy(true);setError("");setAudit(null);
  try{
   if(file.size>1024*1024)throw Error("JSON file must be smaller than 1 MB");
   const parsed:unknown=JSON.parse(await file.text());
   if(!parsed||typeof parsed!=="object"||Array.isArray(parsed))throw Error("Expected a JSON object");
   const res=await fetch("/api/ns3/wifi/inspect",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(parsed)});
   const data=await res.json();
   if(!res.ok)throw Error("Invalid ns-3 artifact: "+JSON.stringify(data.detail??res.status).slice(0,320));
   setAudit(data as Audit);
  }catch(e){setError(e instanceof Error?e.message:"Import failed");}
  finally{setBusy(false);}
 }
 return <section className="panel ns3-panel">
  <div className="section-header"><div><div className="section-kicker">PACKET-LEVEL SIMULATION</div><h2>ns-3 Wi-Fi Results</h2></div><Wifi size={19} className="panel-icon"/></div>
  <p className="measured-intro">Import the JSON output from the independent ns-3 802.11a (5 GHz) UDP simulation. This audits reported counters; it does not run ns-3 or verify physical wireless performance.</p>
  <div className="ns3-upload"><label htmlFor="ns3-json"><FileJson size={16}/> Simulation JSON</label><input id="ns3-json" type="file" accept=".json,application/json" onChange={e=>{setFile(e.target.files?.[0]??null);setAudit(null);setError("");}}/><button type="button" className="primary-button" disabled={!file||busy} onClick={inspect}>{busy?"Inspecting...":"Inspect result"}</button></div>
  {error&&<p className="form-error" role="alert">{error}</p>}
  {audit&&<><div className="ns3-status"><ShieldCheck size={17}/><strong>{audit.audit_status==="consistent"?"Counters internally consistent":"Consistency warnings detected"}</strong><span>{audit.experiment.standard}</span></div>
   <div className="ns3-grid">{fields.map(([key,label,unit])=><div className="ns3-stat" key={key}><small>{label}</small><strong>{fmt(audit.experiment[key] as number)} {unit&&<em>{unit}</em>}</strong></div>)}</div>
   {audit.quality_flags.length>0&&<div className="ns3-flags" role="status">{audit.quality_flags.map(f=><span key={f}>{f.replaceAll("_"," ")}</span>)}</div>}
   <p className="measured-intro"><Activity size={14}/> {audit.caveats.join(" ")}</p>
  </>}
  {!audit&&!error&&<div className="empty-results"><FileJson size={23}/><strong>No ns-3 simulation imported</strong><span>Run the experiment in ns-3 and import its output JSON.</span></div>}
 </section>;
}

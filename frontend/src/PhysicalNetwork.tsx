import { useState } from "react";
import { Cable, RefreshCw, Wifi } from "lucide-react";
type Active={source:string;interface:{interface_name:string;connection_type:string;ipv4:string;gateway:string;dns_servers:string[];link_speed:string;status:string};wifi:Record<string,string>|null;note:string};
type Assessment={connection:Active;status:string;findings:string[];checks:{gateway_icmp:{exit_code:number;output:string};dns_lookup:{success:boolean}};note:string};
type Diagnostic={source:string;platform?:string;target?:string;result:{exit_code:number;output:string};note?:string};
export default function PhysicalNetwork(){
 const [active,setActive]=useState<Active|null>(null);
 const [assessment,setAssessment]=useState<Assessment|null>(null);
 const [autoBusy,setAutoBusy]=useState(false);
 async function inspect(diagnose:boolean){setAutoBusy(true);setError("");try{const r=await fetch(diagnose?"/api/physical/diagnose":"/api/physical/active");const d=await r.json();if(!r.ok)throw Error(d.detail||"Inspection failed");if(diagnose){setAssessment(d);setActive(d.connection)}else{setActive(d);setAssessment(null)}}catch(e){setError(e instanceof Error?e.message:"Unable to inspect network")}finally{setAutoBusy(false)}}
 const [mode,setMode]=useState<"lan"|"wifi">("lan");
 const [target,setTarget]=useState("192.168.1.1");
 const [result,setResult]=useState<Diagnostic|null>(null);
 const [error,setError]=useState("");
 const [busy,setBusy]=useState(false);
 async function check(kind:"interfaces"|"routes"|"ping"){
  setBusy(true);setError("");setResult(null);
  try{
   const response=await fetch(kind==="ping"?"/api/physical/ping":"/api/physical/"+kind,{method:kind==="ping"?"POST":"GET",headers:{"Content-Type":"application/json"},...(kind==="ping"?{body:JSON.stringify({target})}:{})});
   const data=await response.json();if(!response.ok)throw Error(data.detail||"Diagnostic failed");setResult(data);
  }catch(e){setError(e instanceof Error?e.message:"Network request failed")}finally{setBusy(false)}
 }
 return <section className="panel physical-network">
  <div className="section-header"><div><div className="section-kicker">AUTHORIZED PHYSICAL NETWORK DIAGNOSTICS</div><h2>Physical Network</h2></div><Cable size={20}/></div>
  <p className="measured-intro">Automatically inspect the active network of the Windows computer running the backend, diagnose its gateway and DNS, and view OS-reported Wi-Fi quality where available. No remote agent required.</p>
  <div className="physical-actions"><button type="button" disabled={autoBusy} onClick={()=>void inspect(false)}><RefreshCw size={14}/> Detect active connection</button><button type="button" disabled={autoBusy} onClick={()=>void inspect(true)}>{autoBusy?"Checking...":"Diagnose this computer's network"}</button></div>
  {active&&<div className="physical-result"><strong>Active Windows connection</strong><div className="physical-facts"><span>Adapter: {active.interface.interface_name}</span><span>Type: {active.interface.connection_type}</span><span>IP: {active.interface.ipv4||"Unavailable"}</span><span>Gateway: {active.interface.gateway||"Unavailable"}</span><span>DNS: {(active.interface.dns_servers||[]).join(", ")||"Unavailable"}</span><span>Link: {active.interface.link_speed||"Unknown"}</span>{active.wifi&&Object.entries(active.wifi).map(([key,value])=><span key={key}>{key.replaceAll("_"," ")}: {value}</span>)}</div></div>}
  {assessment&&<div className="physical-result"><strong>Preliminary diagnosis: {assessment.status.replaceAll("_"," ")}</strong>{assessment.findings.length?<ul>{assessment.findings.map((x,i)=><li key={i}>{x}</li>)}</ul>:<p>No issues detected by the limited checks.</p>}<p>Gateway ICMP: {assessment.checks.gateway_icmp.exit_code===0?"responded":"no response"} · DNS: {assessment.checks.dns_lookup.success?"resolved":"failed"}</p><p>{assessment.note}</p></div>}
  <div className="physical-modes"><button type="button" aria-pressed={mode==="lan"} className={mode==="lan"?"active":""} onClick={()=>setMode("lan")}><Cable size={15}/> Wired LAN</button><button type="button" aria-pressed={mode==="wifi"} className={mode==="wifi"?"active":""} onClick={()=>setMode("wifi")}><Wifi size={15}/> Wi-Fi</button></div>
  <p className="measured-intro">{mode==="wifi"?"Wi-Fi transport selected. Host interface information and ICMP probes are available; RSSI and AP telemetry are not yet implemented.":"Ethernet transport selected. Host interface information and ICMP probes are available."} The selected tab describes the intended connection; the backend does not force probes through a specific adapter.</p>
  <div className="physical-actions"><button type="button" disabled={busy} onClick={()=>void check("interfaces")}><RefreshCw size={14}/> Interfaces</button><button type="button" disabled={busy} onClick={()=>void check("routes")}>Routing table</button></div>
  <div className="physical-probe"><label htmlFor="physical-target">Authorized target IP / hostname</label><input id="physical-target" value={target} onChange={e=>setTarget(e.target.value)} placeholder="192.168.1.1"/><button type="button" disabled={busy||!target.trim()} onClick={()=>void check("ping")}>{busy?"Checking...":"Run 3 pings"}</button></div>
  {error&&<p role="alert" className="gns3-error">{error}</p>}
  {result&&<div className="physical-result"><div><strong>{result.source.replaceAll("_"," ")}</strong><span>{result.result.exit_code===0?"Command completed":"Command returned a non-zero exit code"}</span></div><pre>{result.result.output}</pre>{result.note&&<p>{result.note}</p>}</div>}
 </section>;
}

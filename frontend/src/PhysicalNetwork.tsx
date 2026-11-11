import { useState } from "react";
import { Cable, RefreshCw, Wifi } from "lucide-react";
type Diagnostic={source:string;platform?:string;target?:string;result:{exit_code:number;output:string};note?:string};
export default function PhysicalNetwork(){
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
  <p className="measured-intro">Inspect the network interfaces and routes of the machine running the backend, and run a short ICMP probe to a device you are authorized to test. Wi-Fi signal metrics require an additional operating-system adapter.</p>
  <div className="physical-modes"><button type="button" aria-pressed={mode==="lan"} className={mode==="lan"?"active":""} onClick={()=>setMode("lan")}><Cable size={15}/> Wired LAN</button><button type="button" aria-pressed={mode==="wifi"} className={mode==="wifi"?"active":""} onClick={()=>setMode("wifi")}><Wifi size={15}/> Wi-Fi</button></div>
  <p className="measured-intro">{mode==="wifi"?"Wi-Fi transport selected. Host interface information and ICMP probes are available; RSSI and AP telemetry are not yet implemented.":"Ethernet transport selected. Host interface information and ICMP probes are available."} The selected tab describes the intended connection; the backend does not force probes through a specific adapter.</p>
  <div className="physical-actions"><button type="button" disabled={busy} onClick={()=>void check("interfaces")}><RefreshCw size={14}/> Interfaces</button><button type="button" disabled={busy} onClick={()=>void check("routes")}>Routing table</button></div>
  <div className="physical-probe"><label htmlFor="physical-target">Authorized target IP / hostname</label><input id="physical-target" value={target} onChange={e=>setTarget(e.target.value)} placeholder="192.168.1.1"/><button type="button" disabled={busy||!target.trim()} onClick={()=>void check("ping")}>{busy?"Checking...":"Run 3 pings"}</button></div>
  {error&&<p role="alert" className="gns3-error">{error}</p>}
  {result&&<div className="physical-result"><div><strong>{result.source.replaceAll("_"," ")}</strong><span>{result.result.exit_code===0?"Command completed":"Command returned a non-zero exit code"}</span></div><pre>{result.result.output}</pre>{result.note&&<p>{result.note}</p>}</div>}
 </section>;
}

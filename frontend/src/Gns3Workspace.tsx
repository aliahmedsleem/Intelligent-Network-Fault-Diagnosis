import { useEffect, useState } from "react";
import { Network, RefreshCw, Server } from "lucide-react";
type Project={project_id:string;name:string;status:string};
type Node={id:string;name:string;type:string;status:string;x:number;y:number};
type Link={id:string;nodes:{node_id:string;adapter_number:number;port_number:number}[]};
type Topology={source:string;nodes:Node[];links:Link[];note:string};
export default function Gns3Workspace(){
 const [projects,setProjects]=useState<Project[]>([]);
 const [selected,setSelected]=useState("");
 const [topology,setTopology]=useState<Topology|null>(null);
 const [error,setError]=useState("");
 const [busy,setBusy]=useState(false);
 async function loadProjects(){
  setBusy(true);setError("");
  try{const r=await fetch("/api/gns3/projects");const d=await r.json();if(!r.ok)throw Error(d.detail||"GNS3 unavailable");setProjects(d);setSelected(old=>d.some((p:Project)=>p.project_id===old)?old:(d[0]?.project_id||""));}
  catch(e){setError(e instanceof Error?e.message:"Connection failed");setProjects([]);setSelected("");setTopology(null);}
  finally{setBusy(false);}
 }
 useEffect(()=>{void loadProjects()},[]);
 useEffect(()=>{
  if(!selected){setTopology(null);return}
  let cancelled=false;setTopology(null);
  fetch("/api/gns3/projects/"+encodeURIComponent(selected)+"/topology").then(async r=>{const d=await r.json();if(!r.ok)throw Error(d.detail||"Unable to load topology");if(!cancelled)setTopology(d)}).catch(e=>{if(!cancelled)setError(String(e))});
  return ()=>{cancelled=true};
 },[selected]);
 const byId=new Map(topology?.nodes.map(n=>[n.id,n])??[]);
 return <section className="panel gns3-workspace">
  <div className="section-header"><div><div className="section-kicker">LIVE CONTROLLER METADATA</div><h2>GNS3 Network Workspace</h2></div><Network size={20}/></div>
  <p className="measured-intro">Read projects, devices and links from your local GNS3 controller. Device status is not a substitute for network-health probes.</p>
  <div className="gns3-toolbar"><label htmlFor="gns3-project">Project</label><select id="gns3-project" value={selected} onChange={e=>{setError("");setSelected(e.target.value)}}><option value="">Select a project</option>{projects.map(p=><option value={p.project_id} key={p.project_id}>{p.name} ({p.status})</option>)}</select><button type="button" onClick={()=>void loadProjects()} disabled={busy}><RefreshCw size={14}/>{busy?"Connecting...":"Refresh"}</button></div>
  {error&&<p role="alert" className="gns3-error">{error}. Start GNS3 and check its local controller.</p>}
  {topology&&<><div className="gns3-summary"><span><Server size={15}/> {topology.nodes.length} devices</span><span><Network size={15}/> {topology.links.length} links</span><span>Read-only</span></div><div className="gns3-devices">{topology.nodes.map(n=><div className="gns3-device" key={n.id}><strong>{n.name}</strong><small>{n.type} · {n.status}</small></div>)}</div><h3 className="gns3-links-title">Connections</h3><div className="gns3-link-list">{topology.links.map(l=><div key={l.id}>{l.nodes.map(e=>byId.get(e.node_id)?.name||e.node_id).join(" ↔ ")}</div>)}</div><p className="measured-intro">{topology.note}</p></>}
  {!topology&&!error&&<div className="empty-results"><Network size={25}/><strong>{selected?"Loading topology...":"No project selected"}</strong><span>Connect GNS3 and choose a project to view its nodes and links.</span></div>}
 </section>;
}

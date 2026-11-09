import { useMemo, useState } from "react";
import { Activity, ArrowUpRight, Cable, CircleDot, GitBranch, Layers3, Maximize2, RadioTower, RotateCcw } from "lucide-react";
import "./ReferenceTopology.css";

type Medium = "ethernet"|"fiber"|"wifi_2_4"|"wifi_5"|"microwave";
type Link = {id:string;source:string;target:string;medium:Medium;capacity_mbps:number;delay_ms:number;loss_percent?:number};
type Props = {nodes:string[];links:Link[];selected:string|null;onSelect:(id:string|null)=>void;
 source:string;target:string;failedLink:string|null;affectedLinks:string[];hasExperiment:boolean};

const points:Record<string,[number,number]>={
 CORE:[105,198],"SW-01":[292,94],FIBER:[505,94],EDGE:[690,198],WIFI:[392,310]
};
const mediumLabel:Record<Medium,string>={ethernet:"Ethernet",fiber:"Optical fiber",wifi_2_4:"Wi-Fi · 2.4 GHz",wifi_5:"Wi-Fi · 5 GHz",microwave:"Microwave"};
const wireless=(m:Medium)=>m.startsWith("wifi")||m==="microwave";
const fmt=(n:number)=>n.toLocaleString("en-US",{maximumFractionDigits:2});

export default function ReferenceTopology({nodes,links,selected,onSelect,source,target,failedLink,affectedLinks,hasExperiment}:Props){
 const [showLabels,setShowLabels]=useState(true);
 const [focus,setFocus]=useState(false);
 const chosen=useMemo(()=>links.find(l=>l.id===selected)||null,[links,selected]);
 const kinds=new Set(links.map(l=>l.medium));
 const status=(l:Link)=>hasExperiment&&l.id===failedLink?"fault":hasExperiment&&affectedLinks.includes(l.id)?"route":"normal";
 const visible=links.filter(l=>points[l.source]&&points[l.target]);
 return <section className={"panel reference-topology "+(focus?"topology-focus":"")}>
  <header className="rt-head">
   <div className="rt-heading"><div className="section-kicker">NETWORK INTELLIGENCE / TOPOLOGY</div>
    <h2>Reference Topology</h2><p>Explore the virtual network and inspect each connection.</p></div>
   <div className="rt-head-actions"><span className="rt-live"><span/> ANALYTICAL MODEL</span>
    <button type="button" className="rt-icon-button" onClick={()=>setFocus(x=>!x)} aria-label={focus?"Exit expanded topology":"Expand topology"} title={focus?"Exit expanded view":"Expand view"}><Maximize2 size={17}/></button></div>
  </header>
  <div className="rt-stats">
   <div><Layers3 size={17}/><span>Nodes</span><strong>{nodes.length.toString().padStart(2,"0")}</strong></div>
   <div><GitBranch size={17}/><span>Links</span><strong>{links.length.toString().padStart(2,"0")}</strong></div>
   <div><RadioTower size={17}/><span>Media types</span><strong>{kinds.size.toString().padStart(2,"0")}</strong></div>
   <div><Activity size={17}/><span>Scenario</span><strong className="rt-scenario">{hasExperiment?"Evaluated":"Reference"}</strong></div>
  </div>
  <div className="rt-canvas">
   <div className="rt-canvas-top"><span><CircleDot size={13}/> INTERACTIVE NETWORK MAP</span>
    <span>CLICK A CONNECTION <ArrowUpRight size={12}/></span></div>
   <svg viewBox="0 0 800 390" role="group" aria-label="Interactive five-node network topology. Use Tab and Enter to select a connection.">
    <defs>
     <pattern id="rt-dots" width="24" height="24" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="1" fill="#537895" opacity=".25"/></pattern>
     <filter id="rt-glow"><feGaussianBlur stdDeviation="5"/></filter>
    </defs>
    <rect width="800" height="390" fill="url(#rt-dots)"/>
    {visible.map(l=>{const [x1,y1]=points[l.source],[x2,y2]=points[l.target];const state=status(l);const active=selected===l.id;const color=state==="fault"?"#fb7185":state==="route"?"#4ce2b5":wireless(l.medium)?"#a18bff":"#62b9ef";return <g key={l.id} className="rt-edge" role="button" tabIndex={0} aria-pressed={active} aria-label={l.id+" "+mediumLabel[l.medium]} onClick={()=>onSelect(l.id)} onKeyDown={e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();onSelect(l.id)}}}>
      <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="transparent" strokeWidth="32"/>
      {active&&<line x1={x1} y1={y1} x2={x2} y2={y2} stroke={color} strokeWidth="11" opacity=".3" filter="url(#rt-glow)"/>}
      <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={color} strokeWidth={active?4:2.8} strokeLinecap="round" strokeDasharray={state==="fault"?"9 8":wireless(l.medium)?"6 9":undefined} opacity={active||!selected?1:.48}/>
      <circle cx={(x1+x2)/2} cy={(y1+y2)/2} r={active?6:4} fill={color} stroke="#0c1b2c" strokeWidth="2"/>
      {showLabels&&<g transform={`translate(${(x1+x2)/2},${(y1+y2)/2-17})`}><rect x="-42" y="-13" width="84" height="24" rx="7" fill="#11253b" stroke={active?color:"#35516a"} strokeWidth="1"/><text y="3" textAnchor="middle" fill={active?"#ffffff":"#a8c5df"} fontSize="10.5" fontWeight="600">{l.id}</text></g>}
     </g>})}
    {nodes.filter(n=>points[n]).map(n=>{const [x,y]=points[n];const primary=n===source,endpoint=n===target;return <g key={n} className="rt-node" transform={`translate(${x},${y})`}>
      <circle r="36" fill={primary?"#2d9ce5":endpoint?"#44d5ae":"#5685b4"} opacity=".09"/>
      <rect x="-57" y="-29" width="114" height="58" rx="13" fill={primary?"#193d5b":endpoint?"#173d43":"#142b43"} stroke={primary?"#58baff":endpoint?"#5cdcb8":"#527b9e"} strokeWidth="1.5"/>
      <rect x="-46" y="-18" width="28" height="36" rx="7" fill={primary?"#285c80":endpoint?"#25615d":"#25445f"}/>
      {n==="WIFI"?<g stroke="#a6a0ff" strokeWidth="2" fill="none"><path d="M-42 -3q10 -9 20 0M-39 1q7 -6 14 0"/><circle cx="-32" cy="7" r="2" fill="#a6a0ff" stroke="none"/></g>:<g stroke="#91d7ff" strokeWidth="1.5" fill="none"><rect x="-40" y="-8" width="16" height="15" rx="2"/><path d="M-36 -11v3m7 -3v3M-36 7v3m7 -3v3"/></g>}
      <text x="6" y="5" fill="#f0f7ff" fontSize="13" fontWeight="700" textAnchor="middle">{n}</text>
      {(primary||endpoint)&&<g transform="translate(0,43)"><rect x="-29" y="-9" width="58" height="18" rx="9" fill={primary?"#163f54":"#17483d"}/><text y="4" textAnchor="middle" fontSize="9" fontWeight="700" fill={primary?"#8ad8ff":"#7af0c2"}>{primary?"SOURCE":"TARGET"}</text></g>}
     </g>})}
   </svg>
   <div className="rt-map-footer"><div className="rt-legend"><span><i className="rt-line rt-cable"/> Wired</span><span><i className="rt-line rt-wireless"/> Wireless</span><span><i className="rt-line rt-route"/> Active path</span><span><i className="rt-line rt-fault"/> Fault</span></div><div className="rt-map-controls"><button type="button" aria-pressed={showLabels} onClick={()=>setShowLabels(x=>!x)}>{showLabels?"Hide labels":"Show labels"}</button><button type="button" onClick={()=>{onSelect(null);setShowLabels(true)}}><RotateCcw size={12}/> Reset</button></div></div>
  </div>
  <div className="rt-bottom">
   <div className="rt-inspector"><div className="rt-inspector-title"><span className="rt-indicator"/><strong>{chosen?"LINK INSPECTOR":"CONNECTION INSPECTOR"}</strong><small>{chosen?"SELECTED":"AWAITING SELECTION"}</small></div>
    {chosen?<><div className="rt-link-name"><Cable size={18}/><strong>{chosen.id}</strong><span>{mediumLabel[chosen.medium]}</span></div><div className="rt-details"><div><small>CONNECTION</small><strong>{chosen.source} → {chosen.target}</strong></div><div><small>CAPACITY</small><strong>{fmt(chosen.capacity_mbps)} Mbps</strong></div><div><small>DELAY</small><strong>{fmt(chosen.delay_ms)} ms</strong></div><div><small>SCENARIO</small><strong className={status(chosen)==="fault"?"rt-danger":""}>{status(chosen)==="fault"?"Fault injected":status(chosen)==="route"?"On evaluated path":"Reference link"}</strong></div></div></>:<p>Choose a connection in the network map to inspect its medium, capacity, delay and experiment status.</p>}
   </div>
   
  </div>
 </section>;
}

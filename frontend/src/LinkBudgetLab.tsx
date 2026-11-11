import { useState } from "react";

type Medium = "fiber" | "wifi_2_4" | "wifi_5" | "microwave";
type BudgetResult = {
 mode:string;medium:Medium;method:string;path_loss_db:number;received_power_dbm:number;
 link_margin_db:number;margin_sufficient:boolean;one_way_propagation_ms:number;
 components:Record<string,number>;limitations:string[];
};
type Settings = {
 medium:Medium;length_km:number;wavelength_nm:1310|1550;
 connector_count:number;splice_count:number;
 distance_m:number;frequency_ghz:number;
 tx_power_dbm:number;receiver_sensitivity_dbm:number;
 tx_gain_dbi:number;rx_gain_dbi:number;additional_loss_db:number;
};
const initial:Settings={medium:"fiber",length_km:10,wavelength_nm:1550,
 connector_count:2,splice_count:0,distance_m:100,frequency_ghz:2.45,
 tx_power_dbm:0,receiver_sensitivity_dbm:-15,
 tx_gain_dbi:0,rx_gain_dbi:0,additional_loss_db:0};
const presets:Record<Medium,Partial<Settings>>={
 fiber:{tx_power_dbm:0,receiver_sensitivity_dbm:-15},
 wifi_2_4:{frequency_ghz:2.45,tx_power_dbm:20,receiver_sensitivity_dbm:-90,distance_m:100},
 wifi_5:{frequency_ghz:5.5,tx_power_dbm:20,receiver_sensitivity_dbm:-90,distance_m:100},
 microwave:{frequency_ghz:18,tx_power_dbm:20,receiver_sensitivity_dbm:-90,distance_m:5000}
};
const labels:Record<Medium,string>={fiber:"Fiber optic",wifi_2_4:"Wi-Fi 2.4 GHz",wifi_5:"Wi-Fi 5 GHz",microwave:"Microwave"};
const fmt=(n:number)=>n.toLocaleString("en-US",{maximumFractionDigits:5});

export default function LinkBudgetLab(){
 const [settings,setSettings]=useState<Settings>(initial);
 const [result,setResult]=useState<BudgetResult|null>(null);
 const [busy,setBusy]=useState(false);
 const [error,setError]=useState("");
 const [history,setHistory]=useState<BudgetResult[]>([]);
 const change=(field:keyof Settings,value:number)=>{setSettings(s=>({...s,[field]:value}));setResult(null);};
 const numeric=(label:string,field:keyof Settings,min:number,max:number,step=1)=><label className="budget-field">
   <span>{label}</span><input type="number" min={min} max={max} step={step} value={settings[field]}
    onChange={e=>change(field,Number(e.target.value))}/>
  </label>;
 async function calculate(){
  setBusy(true);setError("");setResult(null);
  const s=settings;
  const link=s.medium==="fiber"?
   {medium:s.medium,length_km:s.length_km,wavelength_nm:s.wavelength_nm,
    tx_power_dbm:s.tx_power_dbm,receiver_sensitivity_dbm:s.receiver_sensitivity_dbm,
    connector_count:s.connector_count,splice_count:s.splice_count}:
   {medium:s.medium,distance_m:s.distance_m,frequency_ghz:s.frequency_ghz,
    tx_power_dbm:s.tx_power_dbm,receiver_sensitivity_dbm:s.receiver_sensitivity_dbm,
    tx_gain_dbi:s.tx_gain_dbi,rx_gain_dbi:s.rx_gain_dbi,
    additional_loss_db:s.additional_loss_db};
  try{
   const response=await fetch("/api/models/link-budget",{method:"POST",
    headers:{"Content-Type":"application/json"},body:JSON.stringify({link})});
   if(!response.ok){const body=await response.json().catch(()=>null);
    throw new Error(typeof body?.detail==="string"?body.detail:"Invalid budget parameters (HTTP "+response.status+")");}
   const data:BudgetResult=await response.json();
   setResult(data);setHistory(old=>[data,...old].slice(0,8));
  }catch(e){setError(e instanceof Error?e.message:"Calculation failed");}
  finally{setBusy(false);}
 }
 return <section className="panel budget-panel">
  <div className="section-header"><div><div className="section-kicker">PHYSICAL LINK MODELS</div>
   <h2>Link Budget Laboratory</h2></div><span className="soft-tag">ANALYTICAL ONLY</span></div>
  <p className="measured-intro">Calculate engineering power budgets and propagation delay.
   No packets are generated here; these are not measured loss or throughput values.</p>
  <div className="budget-mediums" role="group" aria-label="Select link medium">
   {(Object.keys(labels) as Medium[]).map(m=><button type="button" key={m}
    className={"budget-medium "+(settings.medium===m?"selected":"")}
    aria-pressed={settings.medium===m}
    onClick={()=>{setSettings(s=>({...s,...presets[m],medium:m}));setResult(null);setError("");}}>
    {labels[m]}</button>)}
  </div>
  <div className="budget-fields">
   {settings.medium==="fiber"?<>
    {numeric("Fiber length (km)","length_km",0.001,500,0.1)}
    <label className="budget-field"><span>Wavelength</span>
     <select value={settings.wavelength_nm} onChange={e=>change("wavelength_nm",Number(e.target.value))}>
      <option value={1310}>1310 nm</option><option value={1550}>1550 nm</option>
     </select></label>
    {numeric("Connectors","connector_count",0,100)}
    {numeric("Splices","splice_count",0,1000)}
   </>:<>
    {numeric("Distance (m)","distance_m",0.001,100000,1)}
    {numeric("Frequency (GHz)","frequency_ghz",0.001,100,0.01)}
    {numeric("TX antenna gain (dBi)","tx_gain_dbi",-30,70,0.5)}
    {numeric("RX antenna gain (dBi)","rx_gain_dbi",-30,70,0.5)}
    {numeric("Additional loss (dB)","additional_loss_db",0,100,0.5)}
   </>}
   {numeric("Transmit power (dBm)","tx_power_dbm",settings.medium==="fiber"?-40:-60,settings.medium==="fiber"?30:60,0.5)}
   {numeric("Receiver sensitivity (dBm)","receiver_sensitivity_dbm",settings.medium==="fiber"?-50:-130,settings.medium==="fiber"?10:0,0.5)}
  </div>
  <div className="measurement-actions"><button className="primary-button" type="button" disabled={busy}
   onClick={calculate}>{busy?"Calculating...":"Calculate link budget"}</button></div>
  {error&&<p className="form-error" role="alert">{error}</p>}
  {result&&<><div className="results-grid">
   <div className="result-cell"><small>PATH LOSS</small><strong>{fmt(result.path_loss_db)} <em>dB</em></strong></div>
   <div className="result-cell"><small>RECEIVED POWER</small><strong>{fmt(result.received_power_dbm)} <em>dBm</em></strong></div>
   <div className="result-cell"><small>LINK MARGIN</small><strong>{fmt(result.link_margin_db)} <em>dB</em></strong></div>
   <div className="result-cell"><small>ONE-WAY PROPAGATION</small><strong>{fmt(result.one_way_propagation_ms)} <em>ms</em></strong></div>
  </div><div className="measurement-evidence"><strong>Margin criterion</strong>
   <span>{result.margin_sufficient?"Passes configured reserve":"Below configured reserve"}</span>
   <strong>Method</strong><span>{result.method}</span></div></>}
  {history.length>0&&<div className="probe-table-wrap"><table className="probe-table">
   <thead><tr><th>Medium</th><th>Loss (dB)</th><th>RX (dBm)</th><th>Margin (dB)</th><th>Reserve</th></tr></thead>
   <tbody>{history.map((r,i)=><tr key={i}><td>{labels[r.medium]}</td><td>{fmt(r.path_loss_db)}</td>
    <td>{fmt(r.received_power_dbm)}</td><td>{fmt(r.link_margin_db)}</td>
    <td>{r.margin_sufficient?"Pass":"Below"}</td></tr>)}</tbody></table></div>}
  <p className="measured-intro">Comparison history uses the parameters entered for each run.
   No fading, interference, MAC behavior, BER, PER or physical measurement is modeled.</p>
 </section>;
}

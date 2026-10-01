'use client';
import { useEffect, useState } from 'react';
import { getAlerts } from '../../lib/api';
export default function Alerts(){const [alerts,setAlerts]=useState<any[]>([]);useEffect(()=>{const load=()=>getAlerts().then(setAlerts).catch(()=>{});load();const timer=setInterval(load,4000);return()=>clearInterval(timer)},[]);return <><div className="eyebrow">Operations / real-time</div><h1>Live alerts</h1><div className="panel">{alerts.map(a=><div className="alert" key={a.alert_id}><span><b>{a.vehicle_id}</b><br/><small>{a.detected_at}</small></span><span>{a.anomaly_type}</span><span><b>{a.score}</b> <i className={`badge ${a.severity}`}>{a.severity}</i></span></div>)}{!alerts.length&&<p className="empty">No alerts received yet.</p>}</div></>}

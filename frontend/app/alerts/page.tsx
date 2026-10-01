'use client';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { getAlerts } from '../../lib/api';

function AlertRow({ alert }: { alert: any }) {
	const content = <><span><b>{alert.vehicle_id || 'Unknown vehicle'}</b><br/><small>{alert.detected_at}</small></span><span>{alert.anomaly_type}</span><span><b>{alert.score}</b> <i className={`badge ${alert.severity}`}>{alert.severity}</i></span></>;
	if (!alert.vehicle_id) return <div className="alert">{content}</div>;
	return <Link href={`/vehicles/${encodeURIComponent(alert.vehicle_id)}`} className="alert transition-opacity hover:opacity-75" style={{ color: 'inherit', cursor: 'pointer', textDecoration: 'none' }}>{content}</Link>;
}

export default function Alerts(){const [alerts,setAlerts]=useState<any[]>([]);useEffect(()=>{const load=()=>getAlerts().then(setAlerts).catch(()=>{});load();const timer=setInterval(load,4000);return()=>clearInterval(timer)},[]);return <><div className="eyebrow">Operations / real-time</div><h1>Live alerts</h1><div className="panel">{alerts.map((alert,index)=><AlertRow alert={alert} key={alert.alert_id || index}/>)}{!alerts.length&&<p className="empty">No alerts received yet.</p>}</div></>}

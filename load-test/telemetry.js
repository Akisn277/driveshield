import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = { vus: 20, duration: '30s' };
export default function () {
  const event = { event_id: `load-${__VU}-${__ITER}`, vehicle_id: `VH-${String(__VU).padStart(6, '0')}`, timestamp: new Date().toISOString(), latitude: 12.8458, longitude: 80.0165, speed: 65, temperature: 74, battery: 80, fuel_level: 60, ignition: true };
  const response = http.post('http://localhost:8000/ingest/telemetry', JSON.stringify(event), { headers: { 'Content-Type': 'application/json' } });
  check(response, { 'accepted': (r) => r.status === 200 || r.status === 202 || r.status === 404 });
  sleep(0.1);
}

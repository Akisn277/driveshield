const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
export async function getSummary() { const response = await fetch(`${API_URL}/api/dashboard/summary`, { cache: 'no-store' }); return response.json(); }
export async function getAlerts() { const response = await fetch(`${API_URL}/api/alerts/recent`, { cache: 'no-store' }); return response.json(); }
export async function getAnalytics() { const response = await fetch(`${API_URL}/api/analytics/anomalies`, { cache: 'no-store' }); return response.json(); }

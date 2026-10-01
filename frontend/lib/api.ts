const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const TOKEN_KEY = 'driveshield_access_token';

export function getToken() { return typeof window === 'undefined' ? null : window.localStorage.getItem(TOKEN_KEY); }
export function logout() { window.localStorage.removeItem(TOKEN_KEY); window.location.href = '/login'; }

export async function login(username: string, password: string) {
	const response = await fetch(`${API_URL}/api/auth/login`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password }) });
	if (!response.ok) throw new Error('Invalid username or password');
	const body = await response.json();
	window.localStorage.setItem(TOKEN_KEY, body.access_token);
	return body;
}

export async function signup(name: string, username: string, email: string, password: string, confirmPassword: string) {
	const response = await fetch(`${API_URL}/api/auth/signup`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, username, email, password, confirm_password: confirmPassword }) });
	if (!response.ok) {
		const body = await response.json().catch(() => ({}));
		throw new Error(body.detail || 'Unable to create account');
	}
	return response.json();
}

async function apiFetch(path: string) {
	const token = getToken();
	const response = await fetch(`${API_URL}${path}`, { cache: 'no-store', headers: token ? { Authorization: `Bearer ${token}` } : {} });
	if (response.status === 401) {
		 if (typeof window !== 'undefined') window.localStorage.removeItem(TOKEN_KEY);
		if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) window.location.href = '/login';
		throw new Error('Authentication required');
	}
	if (!response.ok) throw new Error(`API request failed: ${response.status}`);
	return response.json();
}

export function getSummary() { return apiFetch('/api/dashboard/summary'); }
export function getAlerts() { return apiFetch('/api/alerts/recent'); }
export function getAnalytics() { return apiFetch('/api/analytics/anomalies'); }
export function getVehicle(vehicleId: string) { return apiFetch(`/api/vehicles/${encodeURIComponent(vehicleId)}`); }

'use client';

import { FormEvent, useState } from 'react';
import { login } from '../../lib/api';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError('');
    try {
      await login(username, password);
      window.location.href = '/';
    } catch {
      setError('Invalid username or password.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="auth-page">
      <div className="eyebrow">DriveShield / fleet manager access</div>
      <h1>Sign in to your fleet.</h1>
      <form className="auth-form" onSubmit={submit}>
        <label htmlFor="username">Username</label>
        <input id="username" placeholder="Enter your username" value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" required />
        <label htmlFor="password">Password</label>
        <input id="password" type="password" placeholder="Enter your password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" required />
        {error && <p className="auth-error">{error}</p>}
        <button type="submit" disabled={busy}>{busy ? 'Signing in...' : 'Sign in'}</button>
        <p className="auth-helper">Fleet manager access</p>
      </form>
    </section>
  );
}

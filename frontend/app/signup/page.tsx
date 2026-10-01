'use client';

import Link from 'next/link';
import { FormEvent, useState } from 'react';

import { signup } from '../../lib/api';

export default function Signup() {
  const [name, setName] = useState('');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError('');
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    setBusy(true);
    try {
      await signup(name, username, email, password, confirmPassword);
      window.location.href = '/login';
    } catch (signupError) {
      setError(signupError instanceof Error ? signupError.message : 'Unable to create account.');
    } finally {
      setBusy(false);
    }
  }

  return <section className="auth-page"><div className="eyebrow">DriveShield / fleet manager access</div><h1>Create your fleet account.</h1><form className="auth-form" onSubmit={submit}><label>Name<input value={name} onChange={(event) => setName(event.target.value)} autoComplete="name" required /></label><label>Username<input value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" required /></label><label>Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" required /></label><label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="new-password" minLength={8} required /></label><label>Confirm password<input type="password" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} autoComplete="new-password" minLength={8} required /></label>{error && <p className="auth-error">{error}</p>}<button type="submit" disabled={busy}>{busy ? 'Creating account...' : 'Create account'}</button><Link href="/login">Back to sign in</Link></form></section>;
}
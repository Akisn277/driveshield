'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

import { getToken, logout } from '../lib/api';

export default function AuthNav() {
  const [signedIn, setSignedIn] = useState(false);

  useEffect(() => {
    setSignedIn(Boolean(getToken()));
  }, []);

  if (!signedIn) return <Link href="/login">Sign in</Link>;
  return <button type="button" onClick={() => { logout(); setSignedIn(false); }}>Sign out</button>;
}

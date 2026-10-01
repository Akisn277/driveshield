'use client';

import { useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';

import { getToken } from '../lib/api';

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [checking, setChecking] = useState(pathname !== '/login');

  useEffect(() => {
    if (pathname === '/login') {
      setChecking(false);
      return;
    }
    if (!getToken()) {
      router.replace('/login');
      return;
    }
    setChecking(false);
  }, [pathname, router]);

  if (pathname !== '/login' && checking) return null;
  return <>{children}</>;
}

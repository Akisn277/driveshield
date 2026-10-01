import './globals.css';
import Link from 'next/link';
import AuthGuard from '../components/auth-guard';
import AuthNav from '../components/auth-nav';

export default function Layout({ children }: { children: React.ReactNode }) { return <html lang="en"><body><header><Link href="/" className="brand">DRIVESHIELD <span>FLEET INTELLIGENCE</span></Link><nav><Link href="/">Overview</Link><Link href="/alerts">Live alerts</Link><Link href="/analytics">Analytics</Link><AuthNav /></nav></header><AuthGuard><main>{children}</main></AuthGuard></body></html>; }

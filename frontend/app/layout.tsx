import './globals.css';
import Link from 'next/link';

export default function Layout({ children }: { children: React.ReactNode }) { return <html lang="en"><body><header><Link href="/" className="brand">DRIVESHIELD <span>FLEET INTELLIGENCE</span></Link><nav><Link href="/">Overview</Link><Link href="/alerts">Live alerts</Link><Link href="/analytics">Analytics</Link></nav></header><main>{children}</main></body></html>; }

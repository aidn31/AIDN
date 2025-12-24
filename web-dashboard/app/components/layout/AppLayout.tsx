'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ReactNode } from 'react';

interface AppLayoutProps {
  children: ReactNode;
}

const AppLayout = ({ children }: AppLayoutProps) => {
  const pathname = usePathname();
  const [activeNav, setActiveNav] = useState(pathname);

  const navItems = [
    { name: 'Dashboard', href: '/', icon: '⌘', path: '/' },
    { name: 'Leads', href: '/leads', icon: '◉', path: '/leads' },
    { name: 'Campaigns', href: '/campaigns', icon: '▤', path: '/campaigns' },
    { name: 'Call History', href: '/call-history', icon: '◎', path: '/call-history' },
    { name: 'Scripts', href: '/scripts', icon: '☰', path: '/scripts' },
    { name: 'Analytics', href: '/analytics', icon: '◈', path: '/analytics' },
  ];

  return (
    <div className="flex h-screen bg-slate-50">
      {/* Fixed Sidebar */}
      <div className="w-60 bg-slate-900 flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 bg-emerald-500 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">A</span>
            </div>
            <div>
              <div className="text-white font-semibold text-sm">AIDN</div>
              <div className="text-slate-400 text-xs">Insurance Network</div>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-6">
          <div className="space-y-1">
            {navItems.map((item) => (
              <Link
                key={item.name}
                href={item.href}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  pathname === item.path || (pathname === '/' && item.path === '/')
                    ? 'bg-slate-800 text-white'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                }`}
              >
                <span className="text-base">{item.icon}</span>
                {item.name}
              </Link>
            ))}
          </div>
        </nav>

        {/* User Profile */}
        <div className="p-4 border-t border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-slate-700 rounded-full flex items-center justify-center">
              <span className="text-white text-xs font-medium">JS</span>
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-white text-sm font-medium">John Smith</div>
              <div className="text-slate-400 text-xs">Agent</div>
            </div>
            <button className="text-slate-400 hover:text-white">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {children}
      </div>
    </div>
  );
};

export default AppLayout;
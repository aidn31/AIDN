'use client';

import React, { useState } from 'react';

const AIDNDashboard = () => {
  const [activeNav, setActiveNav] = useState('Dashboard');

  const leads = [
    {
      initials: 'SM',
      name: 'Sarah Miller',
      location: 'DuPage, IL',
      type: 'Final Expense',
      status: 'fresh',
      date: '12/24/2025'
    },
    {
      initials: 'MB',
      name: 'Michael Brown',
      location: 'Winnebago, IL',
      type: 'Mortgage Protection',
      status: 'fresh',
      date: '12/24/2025'
    },
    {
      initials: 'JW',
      name: 'Jennifer Wilson',
      location: 'Peoria, IL',
      type: 'Whole Life',
      status: 'callback',
      date: '12/24/2025'
    },
    {
      initials: 'RD',
      name: 'Robert Davis',
      location: 'Sangamon, IL',
      type: 'Term Life',
      status: 'no answer',
      date: '12/24/2025'
    },
    {
      initials: 'MJ',
      name: 'Mary Johnson',
      location: 'Cook, IL',
      type: 'Final Expense',
      status: 'fresh',
      date: '12/24/2025'
    },
  ];

  const stats = [
    { label: 'Total Leads', value: '247', change: '+12%', up: true },
    { label: 'Calls Today', value: '34', change: '+8%', up: true },
    { label: 'Appointments Set', value: '12', change: '+23%', up: true },
    { label: 'Show Rate', value: '75.5%', change: '-2%', up: false },
  ];

  const getStatusStyle = (status: string) => {
    switch(status) {
      case 'fresh':
        return 'bg-emerald-50 text-emerald-700 border border-emerald-200';
      case 'callback':
        return 'bg-amber-50 text-amber-700 border border-amber-200';
      case 'no answer':
        return 'bg-slate-50 text-slate-600 border border-slate-200';
      default:
        return 'bg-slate-50 text-slate-600 border border-slate-200';
    }
  };

  const navItems = [
    { name: 'Dashboard', icon: '⌘', active: true },
    { name: 'Leads', icon: '◉', active: false },
    { name: 'Campaigns', icon: '▤', active: false },
    { name: 'Call History', icon: '◎', active: false },
    { name: 'Scripts', icon: '☰', active: false },
    { name: 'Analytics', icon: '◈', active: false },
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
              <button
                key={item.name}
                onClick={() => setActiveNav(item.name)}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeNav === item.name
                    ? 'bg-slate-800 text-white'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                }`}
              >
                <span className="text-base">{item.icon}</span>
                {item.name}
              </button>
            ))}
          </div>
        </nav>

        {/* User Profile */}
        <div className="p-4 border-t border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-slate-700 rounded-full flex items-center justify-center">
              <span className="text-white text-xs font-medium">TN</span>
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-white text-sm font-medium">Tommy Nguyen</div>
              <div className="text-slate-400 text-xs">Admin</div>
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
        {/* Header */}
        <header className="bg-white border-b border-slate-200 px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold text-slate-900">Dashboard</h1>
              <p className="text-slate-500 text-sm mt-1">Tuesday, December 24, 2025</p>
            </div>
            <div className="flex items-center gap-3">
              <button className="px-4 py-2 text-sm text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors">
                Export
              </button>
              <button className="px-4 py-2 text-sm text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 transition-colors">
                + New Campaign
              </button>
            </div>
          </div>
        </header>

        {/* Main Content Area */}
        <div className="flex-1 overflow-auto">
          <div className="p-8">
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              {stats.map((stat, i) => (
                <div key={i} className="bg-white rounded-xl border border-slate-200 p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-slate-500 text-sm font-medium">{stat.label}</p>
                      <p className="text-slate-900 text-2xl font-semibold mt-2">{stat.value}</p>
                    </div>
                    <div className={`text-sm font-medium ${stat.up ? 'text-emerald-600' : 'text-red-500'}`}>
                      {stat.change}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
              {/* Recent Activity */}
              <div className="lg:col-span-3">
                <div className="bg-white rounded-xl border border-slate-200">
                  <div className="px-6 py-4 border-b border-slate-200">
                    <div className="flex items-center justify-between">
                      <h2 className="text-lg font-semibold text-slate-900">Recent Activity</h2>
                      <button className="text-sm text-emerald-600 hover:text-emerald-700 font-medium">
                        View all →
                      </button>
                    </div>
                  </div>
                  <div className="divide-y divide-slate-100">
                    {leads.map((lead, i) => (
                      <div key={i} className="px-6 py-4 flex items-center gap-4 hover:bg-slate-50/50 transition-colors">
                        <div className="w-10 h-10 bg-slate-100 rounded-full flex items-center justify-center flex-shrink-0">
                          <span className="text-slate-700 text-sm font-medium">{lead.initials}</span>
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="text-slate-900 font-medium">{lead.name}</div>
                          <div className="text-slate-500 text-sm">{lead.location} • {lead.type}</div>
                        </div>
                        <div className="flex items-center gap-4">
                          <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${getStatusStyle(lead.status)}`}>
                            {lead.status}
                          </span>
                          <span className="text-slate-400 text-sm font-mono w-20 text-right">{lead.date}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Performance Sidebar */}
              <div className="lg:col-span-1">
                <div className="bg-white rounded-xl border border-slate-200 p-6">
                  <h3 className="text-lg font-semibold text-slate-900 mb-6">Today's Performance</h3>

                  <div className="space-y-6">
                    <div>
                      <div className="flex justify-between items-center mb-3">
                        <span className="text-slate-700 text-sm font-medium">Calls Completed</span>
                        <span className="text-slate-900 text-sm font-semibold">34/50</span>
                      </div>
                      <div className="w-full bg-slate-100 rounded-full h-2">
                        <div className="bg-emerald-500 h-2 rounded-full transition-all duration-300" style={{width: '68%'}}></div>
                      </div>
                    </div>

                    <div>
                      <div className="flex justify-between items-center mb-3">
                        <span className="text-slate-700 text-sm font-medium">Appointments Set</span>
                        <span className="text-slate-900 text-sm font-semibold">12/20</span>
                      </div>
                      <div className="w-full bg-slate-100 rounded-full h-2">
                        <div className="bg-emerald-500 h-2 rounded-full transition-all duration-300" style={{width: '60%'}}></div>
                      </div>
                    </div>

                    <div>
                      <div className="flex justify-between items-center mb-3">
                        <span className="text-slate-700 text-sm font-medium">Show Rate</span>
                        <span className="text-slate-900 text-sm font-semibold">75.5%</span>
                      </div>
                      <div className="w-full bg-slate-100 rounded-full h-2">
                        <div className="bg-emerald-500 h-2 rounded-full transition-all duration-300" style={{width: '75.5%'}}></div>
                      </div>
                    </div>
                  </div>

                  <div className="mt-8 pt-6 border-t border-slate-100">
                    <h4 className="text-slate-700 text-sm font-medium mb-4">Call Outcomes</h4>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
                          <span className="text-slate-600 text-sm">Appointments</span>
                        </div>
                        <span className="text-slate-900 text-sm font-medium">35%</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-2 h-2 rounded-full bg-amber-500"></div>
                          <span className="text-slate-600 text-sm">Callbacks</span>
                        </div>
                        <span className="text-slate-900 text-sm font-medium">28%</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-2 h-2 rounded-full bg-slate-300"></div>
                          <span className="text-slate-600 text-sm">No Answer</span>
                        </div>
                        <span className="text-slate-900 text-sm font-medium">37%</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIDNDashboard;
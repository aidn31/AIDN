'use client';

import React, { useState, useEffect } from 'react';
import AppLayout from './components/layout/AppLayout';
import Header from './components/ui/Header';
import Link from 'next/link';
import { apiClient } from './lib/api';

const DashboardPage = () => {
  const [leads, setLeads] = useState([]);
  const [stats, setStats] = useState({
    totalLeads: 0,
    callsToday: 0,
    appointmentsSet: 0,
    showRate: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        // Load leads
        const leadsData = await apiClient.getLeads('1');
        setLeads(leadsData.slice(0, 5)); // Show only recent 5

        // Load stats (mock for now)
        setStats({
          totalLeads: leadsData.length,
          callsToday: 34,
          appointmentsSet: 12,
          showRate: 75.5
        });
      } catch (error) {
        console.error('Error loading dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadDashboardData();
  }, []);

  const getStatusStyle = (status: string) => {
    switch(status) {
      case 'fresh':
        return 'bg-emerald-50 text-emerald-700 border border-emerald-200';
      case 'callback':
        return 'bg-amber-50 text-amber-700 border border-amber-200';
      case 'no_answer':
        return 'bg-slate-50 text-slate-600 border border-slate-200';
      default:
        return 'bg-slate-50 text-slate-600 border border-slate-200';
    }
  };

  const handleExport = async () => {
    try {
      // Export functionality will be implemented
      alert('Export functionality will be available soon!');
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  const statsData = [
    { label: 'Total Leads', value: stats.totalLeads.toString(), change: '+12%', up: true },
    { label: 'Calls Today', value: stats.callsToday.toString(), change: '+8%', up: true },
    { label: 'Appointments Set', value: stats.appointmentsSet.toString(), change: '+23%', up: true },
    { label: 'Show Rate', value: `${stats.showRate}%`, change: '-2%', up: false },
  ];

  if (loading) {
    return (
      <AppLayout>
        <Header title="Dashboard" subtitle="Tuesday, December 24, 2025" />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-slate-500">Loading dashboard...</div>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <Header
        title="Dashboard"
        subtitle="Tuesday, December 24, 2025"
      >
        <button
          onClick={handleExport}
          className="px-4 py-2 text-sm text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
        >
          Export
        </button>
        <Link href="/campaigns">
          <button className="px-4 py-2 text-sm text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 transition-colors">
            + New Campaign
          </button>
        </Link>
      </Header>

      {/* Main Content Area */}
      <div className="flex-1 overflow-auto">
        <div className="p-8">
          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {statsData.map((stat, i) => (
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
                    <Link href="/leads" className="text-sm text-emerald-600 hover:text-emerald-700 font-medium">
                      View all →
                    </Link>
                  </div>
                </div>
                <div className="divide-y divide-slate-100">
                  {leads.map((lead, i) => (
                    <div key={i} className="px-6 py-4 flex items-center gap-4 hover:bg-slate-50/50 transition-colors">
                      <div className="w-10 h-10 bg-slate-100 rounded-full flex items-center justify-center flex-shrink-0">
                        <span className="text-slate-700 text-sm font-medium">
                          {lead.first_name?.[0]}{lead.last_name?.[0]}
                        </span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-slate-900 font-medium">{lead.first_name} {lead.last_name}</div>
                        <div className="text-slate-500 text-sm">{lead.county}, {lead.state} • {lead.lead_type}</div>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${getStatusStyle(lead.call_outcome)}`}>
                          {lead.call_outcome}
                        </span>
                        <span className="text-slate-400 text-sm font-mono w-20 text-right">
                          {new Date(lead.created_at).toLocaleDateString()}
                        </span>
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
    </AppLayout>
  );
};

export default DashboardPage;
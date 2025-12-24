'use client';

import React, { useState, useEffect } from 'react';
import AppLayout from '../components/layout/AppLayout';
import Header from '../components/ui/Header';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, BarChart, Bar, PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

const AnalyticsPage = () => {
  const [timeframe, setTimeframe] = useState('7days');
  const [loading, setLoading] = useState(true);

  // Mock analytics data
  const callVolumeData = [
    { date: '12/18', calls: 45, appointments: 12 },
    { date: '12/19', calls: 52, appointments: 15 },
    { date: '12/20', calls: 38, appointments: 9 },
    { date: '12/21', calls: 41, appointments: 11 },
    { date: '12/22', calls: 36, appointments: 8 },
    { date: '12/23', calls: 48, appointments: 14 },
    { date: '12/24', calls: 34, appointments: 12 }
  ];

  const outcomeDistribution = [
    { name: 'Appointment Booked', value: 35, color: '#10b981' },
    { name: 'Callback Requested', value: 28, color: '#f59e0b' },
    { name: 'No Answer', value: 25, color: '#94a3b8' },
    { name: 'Not Interested', value: 12, color: '#ef4444' }
  ];

  const conversionByLeadType = [
    { type: 'Final Expense', calls: 156, appointments: 45, rate: 28.8 },
    { type: 'Term Life', calls: 89, appointments: 22, rate: 24.7 },
    { type: 'Whole Life', calls: 67, appointments: 15, rate: 22.4 },
    { type: 'Mortgage Protection', calls: 43, appointments: 8, rate: 18.6 }
  ];

  const performanceMetrics = {
    totalCalls: 294,
    totalAppointments: 90,
    conversionRate: 30.6,
    avgCallDuration: 142,
    showRate: 75.5,
    avgAppointmentsPerDay: 12.9
  };

  const hourlyActivity = [
    { hour: '9 AM', calls: 12 },
    { hour: '10 AM', calls: 18 },
    { hour: '11 AM', calls: 22 },
    { hour: '12 PM', calls: 15 },
    { hour: '1 PM', calls: 19 },
    { hour: '2 PM', calls: 25 },
    { hour: '3 PM', calls: 28 },
    { hour: '4 PM', calls: 22 },
    { hour: '5 PM', calls: 16 }
  ];

  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      setLoading(false);
    }, 1000);
  }, [timeframe]);

  if (loading) {
    return (
      <AppLayout>
        <Header title="Analytics" subtitle="Performance insights and metrics" />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-slate-500">Loading analytics...</div>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <Header
        title="Analytics"
        subtitle="Performance insights and metrics"
      >
        <select
          value={timeframe}
          onChange={(e) => setTimeframe(e.target.value)}
          className="px-4 py-2 text-sm border border-slate-300 rounded-lg focus:ring-emerald-500 focus:border-emerald-500"
        >
          <option value="7days">Last 7 Days</option>
          <option value="30days">Last 30 Days</option>
          <option value="90days">Last 90 Days</option>
        </select>
        <button className="px-4 py-2 text-sm text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors">
          Export Report
        </button>
      </Header>

      <div className="flex-1 overflow-auto">
        <div className="p-8">
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-6 mb-8">
            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <div className="text-slate-500 text-sm font-medium">Total Calls</div>
              <div className="text-slate-900 text-2xl font-semibold mt-2">{performanceMetrics.totalCalls}</div>
              <div className="text-emerald-600 text-sm font-medium mt-1">+12% vs last period</div>
            </div>
            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <div className="text-slate-500 text-sm font-medium">Appointments</div>
              <div className="text-slate-900 text-2xl font-semibold mt-2">{performanceMetrics.totalAppointments}</div>
              <div className="text-emerald-600 text-sm font-medium mt-1">+23% vs last period</div>
            </div>
            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <div className="text-slate-500 text-sm font-medium">Conversion Rate</div>
              <div className="text-slate-900 text-2xl font-semibold mt-2">{performanceMetrics.conversionRate}%</div>
              <div className="text-emerald-600 text-sm font-medium mt-1">+5.2% vs last period</div>
            </div>
            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <div className="text-slate-500 text-sm font-medium">Avg Duration</div>
              <div className="text-slate-900 text-2xl font-semibold mt-2">{Math.floor(performanceMetrics.avgCallDuration / 60)}m {performanceMetrics.avgCallDuration % 60}s</div>
              <div className="text-red-500 text-sm font-medium mt-1">-8s vs last period</div>
            </div>
            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <div className="text-slate-500 text-sm font-medium">Show Rate</div>
              <div className="text-slate-900 text-2xl font-semibold mt-2">{performanceMetrics.showRate}%</div>
              <div className="text-red-500 text-sm font-medium mt-1">-2.3% vs last period</div>
            </div>
            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <div className="text-slate-500 text-sm font-medium">Daily Avg</div>
              <div className="text-slate-900 text-2xl font-semibold mt-2">{performanceMetrics.avgAppointmentsPerDay}</div>
              <div className="text-emerald-600 text-sm font-medium mt-1">+1.2 vs last period</div>
            </div>
          </div>

          {/* Charts Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
            {/* Call Volume Trend */}
            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <h3 className="text-lg font-semibold text-slate-900 mb-6">Call Volume & Appointments</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={callVolumeData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="date" stroke="#64748b" fontSize={12} />
                  <YAxis stroke="#64748b" fontSize={12} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#ffffff',
                      border: '1px solid #e2e8f0',
                      borderRadius: '8px'
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="calls"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    dot={{ fill: '#3b82f6', strokeWidth: 2 }}
                    name="Total Calls"
                  />
                  <Line
                    type="monotone"
                    dataKey="appointments"
                    stroke="#10b981"
                    strokeWidth={2}
                    dot={{ fill: '#10b981', strokeWidth: 2 }}
                    name="Appointments"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Call Outcomes */}
            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <h3 className="text-lg font-semibold text-slate-900 mb-6">Call Outcomes Distribution</h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={outcomeDistribution}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    dataKey="value"
                    label={({ name, value }) => `${name}: ${value}%`}
                  >
                    {outcomeDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Conversion by Lead Type */}
            <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 p-6">
              <h3 className="text-lg font-semibold text-slate-900 mb-6">Performance by Lead Type</h3>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-slate-100">
                      <th className="text-left text-sm font-medium text-slate-500 pb-3">Lead Type</th>
                      <th className="text-right text-sm font-medium text-slate-500 pb-3">Calls</th>
                      <th className="text-right text-sm font-medium text-slate-500 pb-3">Appointments</th>
                      <th className="text-right text-sm font-medium text-slate-500 pb-3">Conversion Rate</th>
                    </tr>
                  </thead>
                  <tbody>
                    {conversionByLeadType.map((type, index) => (
                      <tr key={index} className="border-b border-slate-50">
                        <td className="py-3 text-sm font-medium text-slate-900">{type.type}</td>
                        <td className="py-3 text-right text-sm text-slate-600">{type.calls}</td>
                        <td className="py-3 text-right text-sm text-slate-600">{type.appointments}</td>
                        <td className="py-3 text-right">
                          <span className="text-sm font-medium text-slate-900">{type.rate}%</span>
                          <div className="w-16 h-2 bg-slate-100 rounded-full mt-1 ml-auto">
                            <div
                              className="h-2 bg-emerald-500 rounded-full"
                              style={{ width: `${(type.rate / 30) * 100}%` }}
                            />
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Hourly Activity */}
            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <h3 className="text-lg font-semibold text-slate-900 mb-6">Hourly Activity</h3>
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={hourlyActivity} layout="horizontal">
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis type="number" stroke="#64748b" fontSize={12} />
                  <YAxis dataKey="hour" type="category" stroke="#64748b" fontSize={12} width={60} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#ffffff',
                      border: '1px solid #e2e8f0',
                      borderRadius: '8px'
                    }}
                  />
                  <Bar dataKey="calls" fill="#3b82f6" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Insights & Recommendations */}
          <div className="mt-8 bg-white rounded-xl border border-slate-200 p-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">AI Insights & Recommendations</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 bg-emerald-100 rounded-full flex items-center justify-center flex-shrink-0">
                    <svg className="w-4 h-4 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                    </svg>
                  </div>
                  <div>
                    <h4 className="font-medium text-emerald-900">Peak Performance Window</h4>
                    <p className="text-sm text-emerald-700 mt-1">2-4 PM shows highest conversion rates. Consider scheduling more calls during this window.</p>
                  </div>
                </div>
              </div>

              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 bg-amber-100 rounded-full flex items-center justify-center flex-shrink-0">
                    <svg className="w-4 h-4 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 15.5c-.77.833.192 2.5 1.732 2.5z" />
                    </svg>
                  </div>
                  <div>
                    <h4 className="font-medium text-amber-900">Show Rate Declining</h4>
                    <p className="text-sm text-amber-700 mt-1">Show rate has dropped 2.3%. Review appointment confirmation process and follow-up scripts.</p>
                  </div>
                </div>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                    <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div>
                    <h4 className="font-medium text-blue-900">Final Expense Lead Success</h4>
                    <p className="text-sm text-blue-700 mt-1">Final Expense leads show 28.8% conversion rate. Consider increasing volume for this lead type.</p>
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

export default AnalyticsPage;
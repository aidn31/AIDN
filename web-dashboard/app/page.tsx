'use client';

import { useEffect, useState } from 'react';
import Navigation from './components/Navigation';
import UploadLeadsModal from './components/UploadLeadsModal';
import { apiClient, mockData } from './lib/api';
import { DashboardStats, Agent, Lead } from './types';
import {
  UsersIcon,
  PhoneIcon,
  CalendarIcon,
  ChartBarIcon,
  ClockIcon,
  ArrowTrendingUpIcon,
  PlayIcon,
  DocumentArrowUpIcon,
  EyeIcon,
} from '@heroicons/react/24/outline';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
  trend?: number[];
}

function StatCard({ title, value, icon: Icon, change, changeType, trend }: StatCardProps) {
  const changeColor = changeType === 'positive' ? 'text-emerald-600' :
                     changeType === 'negative' ? 'text-red-600' : 'text-gray-500';

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg transition-shadow duration-200">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <div className="flex items-baseline space-x-2">
            <p className="text-2xl font-bold text-gray-900">{value}</p>
            {change && (
              <span className={`text-sm font-semibold ${changeColor} flex items-center`}>
                {changeType === 'positive' ? '↗' : changeType === 'negative' ? '↘' : ''} {change}
              </span>
            )}
          </div>
        </div>
        <div className="p-3 bg-blue-50 rounded-lg">
          <Icon className="h-6 w-6 text-blue-600" />
        </div>
      </div>
      {trend && (
        <div className="mt-4 flex items-center space-x-1">
          {trend.map((value, index) => (
            <div
              key={index}
              className="h-8 bg-blue-100 rounded-sm flex-1 relative overflow-hidden"
            >
              <div
                className="absolute bottom-0 left-0 right-0 bg-blue-500 rounded-sm transition-all duration-300"
                style={{ height: `${value}%` }}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

interface RecentActivityProps {
  leads: Lead[];
}

function RecentActivity({ leads }: RecentActivityProps) {
  const recentLeads = leads.slice(0, 5);

  const getStatusBadge = (outcome: string) => {
    const statusStyles = {
      fresh: 'bg-blue-50 text-blue-700 ring-blue-600/20',
      no_answer: 'bg-amber-50 text-amber-700 ring-amber-600/20',
      not_interested: 'bg-gray-50 text-gray-700 ring-gray-600/20',
      callback: 'bg-orange-50 text-orange-700 ring-orange-600/20',
      booked: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
    };

    const style = statusStyles[outcome as keyof typeof statusStyles] || statusStyles.fresh;

    return (
      <span className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset ${style}`}>
        {outcome.replace('_', ' ')}
      </span>
    );
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Recent Activity</h3>
        <button className="text-sm text-blue-600 hover:text-blue-500 font-medium">
          View all
        </button>
      </div>
      <div className="space-y-4">
        {recentLeads.map((lead) => (
          <div key={lead.id} className="flex items-center space-x-4 p-3 rounded-lg hover:bg-gray-50 transition-colors duration-150">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center">
                <span className="text-white text-sm font-semibold">
                  {lead.first_name[0]}{lead.last_name[0]}
                </span>
              </div>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">
                {lead.first_name} {lead.last_name}
              </p>
              <p className="text-sm text-gray-500">
                {lead.county}, {lead.state} • {lead.lead_type.replace('_', ' ')}
              </p>
            </div>
            <div className="flex items-center space-x-3">
              {getStatusBadge(lead.call_outcome)}
              <span className="text-xs text-gray-400">
                {new Date(lead.created_at).toLocaleDateString()}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats>(mockData.dashboardStats);
  const [agent, setAgent] = useState<Agent | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);

      try {
        // Load agents first
        const agents = await apiClient.getAgents();
        if (agents.length > 0) {
          const currentAgent = agents[0];
          setAgent(currentAgent);

          // Load data for the current agent
          const [leads, stats] = await Promise.all([
            apiClient.getLeads(currentAgent.id),
            apiClient.getDashboardStats(currentAgent.id)
          ]);

          setLeads(leads);
          setStats(stats);
        }
      } catch (error) {
        console.error('Failed to load dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  const handleUploadSuccess = async () => {
    // Reload leads data after successful upload
    if (agent) {
      try {
        const updatedLeads = await apiClient.getLeads(agent.id);
        setLeads(updatedLeads);
        const updatedStats = await apiClient.getDashboardStats(agent.id);
        setStats(updatedStats);
      } catch (error) {
        console.error('Failed to reload data after upload:', error);
      }
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen">
        <Navigation />
        <div className="flex-1 lg:ml-64">
          <div className="p-8">
            <div className="animate-pulse">
              <div className="h-8 bg-gray-200 rounded w-1/4 mb-8"></div>
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4 mb-8">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="bg-gray-200 h-32 rounded-xl"></div>
                ))}
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 bg-gray-200 h-96 rounded-xl"></div>
                <div className="bg-gray-200 h-96 rounded-xl"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-50">
      <Navigation />
      <div className="flex-1 lg:ml-64 overflow-auto">
        <div className="p-8">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
                <p className="mt-2 text-gray-600">
                  Welcome back, {agent?.agent_name}. Here's your performance overview.
                </p>
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={() => setUploadModalOpen(true)}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors duration-200"
                >
                  <DocumentArrowUpIcon className="h-4 w-4 mr-2" />
                  Upload Leads
                </button>
                <button className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors duration-200">
                  <PlayIcon className="h-4 w-4 mr-2" />
                  Start Calling
                </button>
              </div>
            </div>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4 mb-8">
            <StatCard
              title="Total Leads"
              value={stats.totalLeads}
              icon={UsersIcon}
              change="+12%"
              changeType="positive"
              trend={[45, 52, 48, 61, 70, 58, 65]}
            />
            <StatCard
              title="Fresh Leads"
              value={stats.freshLeads}
              icon={ClockIcon}
              change="+3 today"
              changeType="positive"
              trend={[30, 35, 40, 42, 38, 45, 48]}
            />
            <StatCard
              title="Appointments Today"
              value={stats.appointmentsToday}
              icon={CalendarIcon}
              trend={[20, 25, 30, 35, 40, 38, 42]}
            />
            <StatCard
              title="Conversion Rate"
              value={`${stats.conversionRate}%`}
              icon={ArrowTrendingUpIcon}
              change="+2.1%"
              changeType="positive"
              trend={[15, 18, 16, 22, 20, 25, 23]}
            />
          </div>

          {/* Main Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Recent Activity */}
            <div className="lg:col-span-2">
              <RecentActivity leads={leads} />
            </div>

            {/* Quick Actions & Performance */}
            <div className="space-y-6">
              {/* Performance Summary */}
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-6">Performance</h3>
                <div className="space-y-6">
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium text-gray-700">Show Rate</span>
                      <span className="text-sm font-bold text-gray-900">{stats.showRate}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-gradient-to-r from-emerald-500 to-emerald-400 h-2 rounded-full transition-all duration-500 ease-out"
                        style={{ width: `${stats.showRate}%` }}
                      ></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium text-gray-700">Conversion Rate</span>
                      <span className="text-sm font-bold text-gray-900">{stats.conversionRate}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-gradient-to-r from-blue-500 to-blue-400 h-2 rounded-full transition-all duration-500 ease-out"
                        style={{ width: `${stats.conversionRate}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Quick Stats */}
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-6">Today's Summary</h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between py-2">
                    <div className="flex items-center space-x-3">
                      <PhoneIcon className="h-5 w-5 text-blue-600" />
                      <span className="text-sm font-medium text-gray-700">Calls Made</span>
                    </div>
                    <span className="text-sm font-bold text-gray-900">23</span>
                  </div>
                  <div className="flex items-center justify-between py-2">
                    <div className="flex items-center space-x-3">
                      <UsersIcon className="h-5 w-5 text-emerald-600" />
                      <span className="text-sm font-medium text-gray-700">Contacts Reached</span>
                    </div>
                    <span className="text-sm font-bold text-gray-900">8</span>
                  </div>
                  <div className="flex items-center justify-between py-2">
                    <div className="flex items-center space-x-3">
                      <CalendarIcon className="h-5 w-5 text-purple-600" />
                      <span className="text-sm font-medium text-gray-700">Appointments Set</span>
                    </div>
                    <span className="text-sm font-bold text-gray-900">{stats.appointmentsToday}</span>
                  </div>
                </div>
              </div>

              {/* Action Card */}
              <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-6 text-white">
                <h3 className="text-lg font-semibold mb-2">Ready to Call?</h3>
                <p className="text-blue-100 text-sm mb-4">
                  You have {stats.freshLeads} fresh leads waiting. Start your calling session to maximize conversions.
                </p>
                <button className="w-full bg-white text-blue-600 font-semibold py-2 px-4 rounded-lg hover:bg-blue-50 transition-colors duration-200 flex items-center justify-center space-x-2">
                  <PlayIcon className="h-4 w-4" />
                  <span>Begin Calling Session</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Upload Modal */}
      <UploadLeadsModal
        isOpen={uploadModalOpen}
        onClose={() => setUploadModalOpen(false)}
        onSuccess={handleUploadSuccess}
      />
    </div>
  );
}
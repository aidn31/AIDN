'use client';

import React, { useState, useEffect } from 'react';
import AppLayout from '../components/layout/AppLayout';
import Header from '../components/ui/Header';

const CallHistoryPage = () => {
  const [callLogs, setCallLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCall, setSelectedCall] = useState(null);
  const [filters, setFilters] = useState({
    outcome: 'all',
    dateRange: '7days'
  });

  // Mock call logs data
  const mockCallLogs = [
    {
      id: '1',
      lead_id: '1',
      agent_id: '1',
      call_sid: 'CA123456789',
      started_at: '2025-12-24T14:30:00Z',
      ended_at: '2025-12-24T14:32:30Z',
      duration_seconds: 150,
      outcome: 'appointment_booked',
      recording_url: 'https://example.com/recording1.mp3',
      transcript: 'Agent: Hi Mary, this is John from AIDN calling about the life insurance information you requested...',
      notes: 'Very interested, scheduled for tomorrow 2PM',
      lead: {
        first_name: 'Mary',
        last_name: 'Johnson',
        phone: '+15551234567',
        county: 'Cook',
        lead_type: 'final_expense'
      }
    },
    {
      id: '2',
      lead_id: '2',
      agent_id: '1',
      call_sid: 'CA123456790',
      started_at: '2025-12-24T13:15:00Z',
      ended_at: '2025-12-24T13:15:45Z',
      duration_seconds: 45,
      outcome: 'no_answer',
      recording_url: null,
      transcript: null,
      notes: 'Phone rang 3 times, no answer',
      lead: {
        first_name: 'Robert',
        last_name: 'Davis',
        phone: '+15552345678',
        county: 'Sangamon',
        lead_type: 'term_life'
      }
    },
    {
      id: '3',
      lead_id: '3',
      agent_id: '1',
      call_sid: 'CA123456791',
      started_at: '2025-12-24T12:45:00Z',
      ended_at: '2025-12-24T12:47:20Z',
      duration_seconds: 140,
      outcome: 'callback_requested',
      recording_url: 'https://example.com/recording3.mp3',
      transcript: 'Agent: Hi Jennifer, this is John calling about...\nProspect: Can you call me back tomorrow at 3 PM?',
      notes: 'Requested callback tomorrow 3PM, seemed interested',
      lead: {
        first_name: 'Jennifer',
        last_name: 'Wilson',
        phone: '+15553456789',
        county: 'Peoria',
        lead_type: 'whole_life'
      }
    },
    {
      id: '4',
      lead_id: '4',
      agent_id: '1',
      call_sid: 'CA123456792',
      started_at: '2025-12-24T11:20:00Z',
      ended_at: '2025-12-24T11:22:10Z',
      duration_seconds: 130,
      outcome: 'not_interested',
      recording_url: 'https://example.com/recording4.mp3',
      transcript: 'Agent: Hi Michael, this is John calling about...\nProspect: Not interested, please remove me from your list.',
      notes: 'Not interested, marked as Do Not Call',
      lead: {
        first_name: 'Michael',
        last_name: 'Brown',
        phone: '+15554567890',
        county: 'Winnebago',
        lead_type: 'mortgage_protection'
      }
    }
  ];

  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      setCallLogs(mockCallLogs);
      setLoading(false);
    }, 1000);
  }, []);

  const getOutcomeStyle = (outcome: string) => {
    switch(outcome) {
      case 'appointment_booked':
        return 'bg-emerald-50 text-emerald-700 border border-emerald-200';
      case 'callback_requested':
        return 'bg-amber-50 text-amber-700 border border-amber-200';
      case 'no_answer':
        return 'bg-slate-50 text-slate-600 border border-slate-200';
      case 'not_interested':
        return 'bg-red-50 text-red-700 border border-red-200';
      case 'wrong_number':
        return 'bg-slate-50 text-slate-600 border border-slate-200';
      default:
        return 'bg-slate-50 text-slate-600 border border-slate-200';
    }
  };

  const formatDuration = (seconds: number) => {
    if (!seconds) return '0:00';
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const filteredCalls = callLogs.filter(call => {
    if (filters.outcome !== 'all' && call.outcome !== filters.outcome) return false;

    // Date filtering
    const callDate = new Date(call.started_at);
    const now = new Date();
    switch(filters.dateRange) {
      case '1day':
        return callDate >= new Date(now.setDate(now.getDate() - 1));
      case '7days':
        return callDate >= new Date(now.setDate(now.getDate() - 7));
      case '30days':
        return callDate >= new Date(now.setDate(now.getDate() - 30));
      default:
        return true;
    }
  });

  if (loading) {
    return (
      <AppLayout>
        <Header title="Call History" subtitle="Review call logs and recordings" />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-slate-500">Loading call history...</div>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <Header
        title="Call History"
        subtitle={`${filteredCalls.length} calls shown`}
      >
        <button className="px-4 py-2 text-sm text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors">
          Export Calls
        </button>
      </Header>

      <div className="flex-1 overflow-auto">
        <div className="p-8">
          {/* Filters */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 mb-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Filters</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Outcome</label>
                <select
                  value={filters.outcome}
                  onChange={(e) => setFilters({...filters, outcome: e.target.value})}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-emerald-500 focus:border-emerald-500"
                >
                  <option value="all">All Outcomes</option>
                  <option value="appointment_booked">Appointment Booked</option>
                  <option value="callback_requested">Callback Requested</option>
                  <option value="no_answer">No Answer</option>
                  <option value="not_interested">Not Interested</option>
                  <option value="wrong_number">Wrong Number</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Date Range</label>
                <select
                  value={filters.dateRange}
                  onChange={(e) => setFilters({...filters, dateRange: e.target.value})}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-emerald-500 focus:border-emerald-500"
                >
                  <option value="1day">Last 24 Hours</option>
                  <option value="7days">Last 7 Days</option>
                  <option value="30days">Last 30 Days</option>
                  <option value="all">All Time</option>
                </select>
              </div>
            </div>
          </div>

          {/* Call History Table */}
          <div className="bg-white rounded-xl border border-slate-200">
            <div className="px-6 py-4 border-b border-slate-200">
              <h2 className="text-lg font-semibold text-slate-900">Call History</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Contact
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Date & Time
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Duration
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Outcome
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Recording
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredCalls.map((call) => (
                    <tr key={call.id} className="hover:bg-slate-50/50 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="w-10 h-10 bg-slate-100 rounded-full flex items-center justify-center flex-shrink-0">
                            <span className="text-slate-700 text-sm font-medium">
                              {call.lead?.first_name?.[0]}{call.lead?.last_name?.[0]}
                            </span>
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-slate-900">
                              {call.lead?.first_name} {call.lead?.last_name}
                            </div>
                            <div className="text-sm text-slate-500">{call.lead?.phone}</div>
                            <div className="text-xs text-slate-400">{call.lead?.county} • {call.lead?.lead_type}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-slate-900">
                          {new Date(call.started_at).toLocaleDateString()}
                        </div>
                        <div className="text-sm text-slate-500">
                          {new Date(call.started_at).toLocaleTimeString()}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-900">
                        {formatDuration(call.duration_seconds)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${getOutcomeStyle(call.outcome)}`}>
                          {call.outcome.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {call.recording_url ? (
                          <button className="text-blue-600 hover:text-blue-900 text-sm font-medium">
                            🎵 Play
                          </button>
                        ) : (
                          <span className="text-slate-400 text-sm">No recording</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button
                          onClick={() => setSelectedCall(call)}
                          className="text-emerald-600 hover:text-emerald-900"
                        >
                          View Details
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      {/* Call Details Modal */}
      {selectedCall && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-lg font-semibold text-slate-900">
                Call Details - {selectedCall.lead?.first_name} {selectedCall.lead?.last_name}
              </h3>
              <button
                onClick={() => setSelectedCall(null)}
                className="text-slate-400 hover:text-slate-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              <div>
                <h4 className="text-sm font-medium text-slate-700 mb-3">Call Information</h4>
                <div className="space-y-2 text-sm">
                  <div><span className="font-medium">Started:</span> {new Date(selectedCall.started_at).toLocaleString()}</div>
                  <div><span className="font-medium">Duration:</span> {formatDuration(selectedCall.duration_seconds)}</div>
                  <div><span className="font-medium">Outcome:</span>
                    <span className={`ml-2 px-2 py-0.5 rounded-full text-xs ${getOutcomeStyle(selectedCall.outcome)}`}>
                      {selectedCall.outcome.replace('_', ' ')}
                    </span>
                  </div>
                  <div><span className="font-medium">Call ID:</span> {selectedCall.call_sid}</div>
                </div>
              </div>

              <div>
                <h4 className="text-sm font-medium text-slate-700 mb-3">Contact Information</h4>
                <div className="space-y-2 text-sm">
                  <div><span className="font-medium">Name:</span> {selectedCall.lead?.first_name} {selectedCall.lead?.last_name}</div>
                  <div><span className="font-medium">Phone:</span> {selectedCall.lead?.phone}</div>
                  <div><span className="font-medium">County:</span> {selectedCall.lead?.county}</div>
                  <div><span className="font-medium">Lead Type:</span> {selectedCall.lead?.lead_type}</div>
                </div>
              </div>
            </div>

            {selectedCall.transcript && (
              <div className="mb-6">
                <h4 className="text-sm font-medium text-slate-700 mb-3">Call Transcript</h4>
                <div className="bg-slate-50 p-4 rounded-lg text-sm whitespace-pre-wrap">
                  {selectedCall.transcript}
                </div>
              </div>
            )}

            {selectedCall.notes && (
              <div className="mb-6">
                <h4 className="text-sm font-medium text-slate-700 mb-3">Notes</h4>
                <div className="bg-slate-50 p-4 rounded-lg text-sm">
                  {selectedCall.notes}
                </div>
              </div>
            )}

            {selectedCall.recording_url && (
              <div className="mb-6">
                <h4 className="text-sm font-medium text-slate-700 mb-3">Recording</h4>
                <div className="bg-slate-50 p-4 rounded-lg">
                  <div className="flex items-center gap-4">
                    <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm">
                      🎵 Play Recording
                    </button>
                    <button className="px-4 py-2 bg-slate-600 text-white rounded-lg hover:bg-slate-700 text-sm">
                      Download
                    </button>
                  </div>
                </div>
              </div>
            )}

            <div className="flex justify-end gap-3">
              <button
                onClick={() => setSelectedCall(null)}
                className="px-4 py-2 text-sm text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </AppLayout>
  );
};

export default CallHistoryPage;
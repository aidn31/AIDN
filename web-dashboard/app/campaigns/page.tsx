'use client';

import React, { useState, useEffect } from 'react';
import AppLayout from '../components/layout/AppLayout';
import Header from '../components/ui/Header';

const CampaignsPage = () => {
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedCampaign, setSelectedCampaign] = useState(null);
  const [newCampaign, setNewCampaign] = useState({
    name: '',
    leadTypes: [],
    counties: [],
    dailyCallLimit: 50,
    startTime: '09:00',
    endTime: '17:00'
  });

  // Mock campaigns data
  const mockCampaigns = [
    {
      id: '1',
      name: 'Final Expense - Cook County',
      agent_id: '1',
      lead_types: ['final_expense'],
      counties: ['Cook'],
      is_active: true,
      created_at: '2025-12-20T10:00:00Z',
      updated_at: '2025-12-20T10:00:00Z',
      leads_count: 45,
      appointments_count: 12,
      calls_count: 134
    },
    {
      id: '2',
      name: 'Term Life - Multi County',
      agent_id: '1',
      lead_types: ['term_life'],
      counties: ['DuPage', 'Lake', 'Will'],
      is_active: true,
      created_at: '2025-12-18T14:30:00Z',
      updated_at: '2025-12-18T14:30:00Z',
      leads_count: 23,
      appointments_count: 8,
      calls_count: 67
    },
    {
      id: '3',
      name: 'Whole Life - Sangamon',
      agent_id: '1',
      lead_types: ['whole_life'],
      counties: ['Sangamon'],
      is_active: false,
      created_at: '2025-12-15T09:15:00Z',
      updated_at: '2025-12-15T09:15:00Z',
      leads_count: 12,
      appointments_count: 3,
      calls_count: 28
    }
  ];

  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      setCampaigns(mockCampaigns);
      setLoading(false);
    }, 1000);
  }, []);

  const handleCreateCampaign = () => {
    const campaign = {
      id: Date.now().toString(),
      name: newCampaign.name,
      agent_id: '1',
      lead_types: newCampaign.leadTypes,
      counties: newCampaign.counties,
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      leads_count: 0,
      appointments_count: 0,
      calls_count: 0
    };

    setCampaigns([...campaigns, campaign]);
    setNewCampaign({
      name: '',
      leadTypes: [],
      counties: [],
      dailyCallLimit: 50,
      startTime: '09:00',
      endTime: '17:00'
    });
    setShowCreateModal(false);
  };

  const toggleCampaignStatus = (campaignId: string) => {
    setCampaigns(campaigns.map(campaign =>
      campaign.id === campaignId
        ? { ...campaign, is_active: !campaign.is_active }
        : campaign
    ));
  };

  const deleteCampaign = (campaignId: string) => {
    if (confirm('Are you sure you want to delete this campaign?')) {
      setCampaigns(campaigns.filter(campaign => campaign.id !== campaignId));
    }
  };

  const getStatusColor = (isActive: boolean) => {
    return isActive
      ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
      : 'bg-slate-50 text-slate-600 border border-slate-200';
  };

  if (loading) {
    return (
      <AppLayout>
        <Header title="Campaigns" subtitle="Manage your calling campaigns" />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-slate-500">Loading campaigns...</div>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <Header
        title="Campaigns"
        subtitle={`${campaigns.length} campaigns total`}
      >
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 text-sm text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 transition-colors"
        >
          + New Campaign
        </button>
      </Header>

      <div className="flex-1 overflow-auto">
        <div className="p-8">
          {/* Campaigns Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {campaigns.map((campaign) => (
              <div key={campaign.id} className="bg-white rounded-xl border border-slate-200 p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-slate-900 mb-2">{campaign.name}</h3>
                    <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${getStatusColor(campaign.is_active)}`}>
                      {campaign.is_active ? 'Active' : 'Paused'}
                    </span>
                  </div>
                  <div className="relative">
                    <button
                      onClick={() => setSelectedCampaign(selectedCampaign === campaign.id ? null : campaign.id)}
                      className="text-slate-400 hover:text-slate-600"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                      </svg>
                    </button>
                    {selectedCampaign === campaign.id && (
                      <div className="absolute right-0 top-8 bg-white border border-slate-200 rounded-lg shadow-lg py-1 z-10">
                        <button
                          onClick={() => toggleCampaignStatus(campaign.id)}
                          className="block px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 w-full text-left"
                        >
                          {campaign.is_active ? 'Pause' : 'Resume'}
                        </button>
                        <button
                          onClick={() => deleteCampaign(campaign.id)}
                          className="block px-4 py-2 text-sm text-red-600 hover:bg-slate-50 w-full text-left"
                        >
                          Delete
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                <div className="space-y-3">
                  <div>
                    <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">Lead Types</div>
                    <div className="text-sm text-slate-900 mt-1">
                      {campaign.lead_types.map(type => type.replace('_', ' ')).join(', ')}
                    </div>
                  </div>

                  <div>
                    <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">Counties</div>
                    <div className="text-sm text-slate-900 mt-1">
                      {campaign.counties.join(', ')}
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-4 pt-4 border-t border-slate-100">
                    <div className="text-center">
                      <div className="text-lg font-semibold text-slate-900">{campaign.leads_count}</div>
                      <div className="text-xs text-slate-500">Leads</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-semibold text-slate-900">{campaign.calls_count}</div>
                      <div className="text-xs text-slate-500">Calls</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-semibold text-slate-900">{campaign.appointments_count}</div>
                      <div className="text-xs text-slate-500">Appts</div>
                    </div>
                  </div>

                  <div className="text-xs text-slate-500 pt-2">
                    Created {new Date(campaign.created_at).toLocaleDateString()}
                  </div>
                </div>
              </div>
            ))}

            {/* Add Campaign Card */}
            <div
              onClick={() => setShowCreateModal(true)}
              className="bg-slate-50 border-2 border-dashed border-slate-300 rounded-xl p-6 flex flex-col items-center justify-center min-h-[280px] cursor-pointer hover:border-emerald-400 hover:bg-emerald-50/50 transition-colors"
            >
              <div className="w-12 h-12 bg-emerald-100 rounded-full flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">Create New Campaign</h3>
              <p className="text-sm text-slate-500 text-center">Set up a new calling campaign with specific lead types and territories</p>
            </div>
          </div>
        </div>
      </div>

      {/* Create Campaign Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-lg font-semibold text-slate-900">Create New Campaign</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Campaign Name</label>
                <input
                  type="text"
                  value={newCampaign.name}
                  onChange={(e) => setNewCampaign({...newCampaign, name: e.target.value})}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-emerald-500 focus:border-emerald-500"
                  placeholder="e.g., Final Expense - Cook County"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Lead Types</label>
                <div className="space-y-2">
                  {['final_expense', 'term_life', 'whole_life', 'mortgage_protection'].map(type => (
                    <label key={type} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={newCampaign.leadTypes.includes(type)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setNewCampaign({...newCampaign, leadTypes: [...newCampaign.leadTypes, type]});
                          } else {
                            setNewCampaign({...newCampaign, leadTypes: newCampaign.leadTypes.filter(t => t !== type)});
                          }
                        }}
                        className="mr-3 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                      />
                      <span className="text-sm text-slate-700">{type.replace('_', ' ')}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Counties</label>
                <div className="grid grid-cols-2 gap-2">
                  {['Cook', 'DuPage', 'Lake', 'Will', 'Sangamon', 'Peoria', 'Winnebago'].map(county => (
                    <label key={county} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={newCampaign.counties.includes(county)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setNewCampaign({...newCampaign, counties: [...newCampaign.counties, county]});
                          } else {
                            setNewCampaign({...newCampaign, counties: newCampaign.counties.filter(c => c !== county)});
                          }
                        }}
                        className="mr-3 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                      />
                      <span className="text-sm text-slate-700">{county}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Daily Call Limit</label>
                  <input
                    type="number"
                    value={newCampaign.dailyCallLimit}
                    onChange={(e) => setNewCampaign({...newCampaign, dailyCallLimit: parseInt(e.target.value)})}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-emerald-500 focus:border-emerald-500"
                  />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">Start Time</label>
                    <input
                      type="time"
                      value={newCampaign.startTime}
                      onChange={(e) => setNewCampaign({...newCampaign, startTime: e.target.value})}
                      className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-emerald-500 focus:border-emerald-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">End Time</label>
                    <input
                      type="time"
                      value={newCampaign.endTime}
                      onChange={(e) => setNewCampaign({...newCampaign, endTime: e.target.value})}
                      className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-emerald-500 focus:border-emerald-500"
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="flex justify-end mt-6 gap-3">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 text-sm text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateCampaign}
                disabled={!newCampaign.name || newCampaign.leadTypes.length === 0 || newCampaign.counties.length === 0}
                className="px-4 py-2 text-sm text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Create Campaign
              </button>
            </div>
          </div>
        </div>
      )}
    </AppLayout>
  );
};

export default CampaignsPage;
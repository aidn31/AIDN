'use client';

import React, { useState, useEffect } from 'react';
import AppLayout from '../components/layout/AppLayout';
import Header from '../components/ui/Header';
import { apiClient } from '../lib/api';

const LeadsPage = () => {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedLead, setSelectedLead] = useState(null);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [filters, setFilters] = useState({
    status: 'all',
    leadType: 'all',
    county: 'all'
  });

  useEffect(() => {
    const loadLeads = async () => {
      try {
        const leadsData = await apiClient.getLeads('1');
        setLeads(leadsData);
      } catch (error) {
        console.error('Error loading leads:', error);
      } finally {
        setLoading(false);
      }
    };

    loadLeads();
  }, []);

  const getStatusStyle = (status: string) => {
    switch(status) {
      case 'fresh':
        return 'bg-emerald-50 text-emerald-700 border border-emerald-200';
      case 'callback':
        return 'bg-amber-50 text-amber-700 border border-amber-200';
      case 'no_answer':
        return 'bg-slate-50 text-slate-600 border border-slate-200';
      case 'booked':
        return 'bg-blue-50 text-blue-700 border border-blue-200';
      default:
        return 'bg-slate-50 text-slate-600 border border-slate-200';
    }
  };

  const handleUploadFile = async (file: File) => {
    try {
      const result = await apiClient.uploadLeads(file);
      // Refresh leads list
      const leadsData = await apiClient.getLeads('1');
      setLeads(leadsData);
      alert(`Successfully imported ${result.imported} leads!`);
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Upload failed. Please try again.');
    }
  };

  const filteredLeads = leads.filter(lead => {
    if (filters.status !== 'all' && lead.call_outcome !== filters.status) return false;
    if (filters.leadType !== 'all' && lead.lead_type !== filters.leadType) return false;
    if (filters.county !== 'all' && lead.county !== filters.county) return false;
    return true;
  });

  const leadTypes = [...new Set(leads.map(lead => lead.lead_type))];
  const counties = [...new Set(leads.map(lead => lead.county))];

  if (loading) {
    return (
      <AppLayout>
        <Header title="Leads" subtitle="Manage your lead pipeline" />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-slate-500">Loading leads...</div>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <Header
        title="Leads"
        subtitle={`${filteredLeads.length} leads total`}
      >
        <button
          onClick={() => setShowUploadModal(true)}
          className="px-4 py-2 text-sm text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
        >
          Upload Leads
        </button>
        <button className="px-4 py-2 text-sm text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 transition-colors">
          Add Lead
        </button>
      </Header>

      <div className="flex-1 overflow-auto">
        <div className="p-8">
          {/* Filters */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 mb-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Filters</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Status</label>
                <select
                  value={filters.status}
                  onChange={(e) => setFilters({...filters, status: e.target.value})}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-emerald-500 focus:border-emerald-500"
                >
                  <option value="all">All Statuses</option>
                  <option value="fresh">Fresh</option>
                  <option value="no_answer">No Answer</option>
                  <option value="callback">Callback</option>
                  <option value="booked">Booked</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Lead Type</label>
                <select
                  value={filters.leadType}
                  onChange={(e) => setFilters({...filters, leadType: e.target.value})}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-emerald-500 focus:border-emerald-500"
                >
                  <option value="all">All Types</option>
                  {leadTypes.map(type => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">County</label>
                <select
                  value={filters.county}
                  onChange={(e) => setFilters({...filters, county: e.target.value})}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-emerald-500 focus:border-emerald-500"
                >
                  <option value="all">All Counties</option>
                  {counties.map(county => (
                    <option key={county} value={county}>{county}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Leads Table */}
          <div className="bg-white rounded-xl border border-slate-200">
            <div className="px-6 py-4 border-b border-slate-200">
              <h2 className="text-lg font-semibold text-slate-900">All Leads</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Contact
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Location
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Calls
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredLeads.map((lead) => (
                    <tr key={lead.id} className="hover:bg-slate-50/50 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="w-10 h-10 bg-slate-100 rounded-full flex items-center justify-center flex-shrink-0">
                            <span className="text-slate-700 text-sm font-medium">
                              {lead.first_name?.[0]}{lead.last_name?.[0]}
                            </span>
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-slate-900">
                              {lead.first_name} {lead.last_name}
                            </div>
                            <div className="text-sm text-slate-500">{lead.phone}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-slate-900">{lead.county}, {lead.state}</div>
                        <div className="text-sm text-slate-500">{lead.city} {lead.zip_code}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-slate-900">{lead.lead_type}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${getStatusStyle(lead.call_outcome)}`}>
                          {lead.call_outcome}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-900">
                        {lead.call_count || 0}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
                        {new Date(lead.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button
                          onClick={() => setSelectedLead(lead)}
                          className="text-emerald-600 hover:text-emerald-900 mr-3"
                        >
                          View
                        </button>
                        <button className="text-blue-600 hover:text-blue-900">
                          Call
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

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Upload Leads</h3>
            <div className="border-2 border-dashed border-slate-300 rounded-lg p-6 text-center">
              <input
                type="file"
                accept=".csv,.xlsx,.xls"
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    handleUploadFile(e.target.files[0]);
                    setShowUploadModal(false);
                  }
                }}
                className="hidden"
                id="file-upload"
              />
              <label
                htmlFor="file-upload"
                className="cursor-pointer text-slate-600 hover:text-slate-900"
              >
                <div className="text-4xl mb-2">📄</div>
                <div className="text-sm">Click to upload CSV or Excel file</div>
              </label>
            </div>
            <div className="flex justify-end mt-4 gap-3">
              <button
                onClick={() => setShowUploadModal(false)}
                className="px-4 py-2 text-sm text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Lead Details Modal */}
      {selectedLead && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-lg font-semibold text-slate-900">
                Lead Details - {selectedLead.first_name} {selectedLead.last_name}
              </h3>
              <button
                onClick={() => setSelectedLead(null)}
                className="text-slate-400 hover:text-slate-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="grid grid-cols-2 gap-6">
              <div>
                <h4 className="text-sm font-medium text-slate-700 mb-3">Contact Information</h4>
                <div className="space-y-2 text-sm">
                  <div><span className="font-medium">Phone:</span> {selectedLead.phone}</div>
                  <div><span className="font-medium">Address:</span> {selectedLead.address}</div>
                  <div><span className="font-medium">City:</span> {selectedLead.city}</div>
                  <div><span className="font-medium">County:</span> {selectedLead.county}</div>
                  <div><span className="font-medium">State:</span> {selectedLead.state}</div>
                  <div><span className="font-medium">Zip:</span> {selectedLead.zip_code}</div>
                </div>
              </div>

              <div>
                <h4 className="text-sm font-medium text-slate-700 mb-3">Lead Details</h4>
                <div className="space-y-2 text-sm">
                  <div><span className="font-medium">Type:</span> {selectedLead.lead_type}</div>
                  <div><span className="font-medium">Source:</span> {selectedLead.lead_source}</div>
                  <div><span className="font-medium">Status:</span>
                    <span className={`ml-2 px-2 py-0.5 rounded-full text-xs ${getStatusStyle(selectedLead.call_outcome)}`}>
                      {selectedLead.call_outcome}
                    </span>
                  </div>
                  <div><span className="font-medium">Calls:</span> {selectedLead.call_count || 0}</div>
                  <div><span className="font-medium">Created:</span> {new Date(selectedLead.created_at).toLocaleDateString()}</div>
                </div>
              </div>
            </div>

            <div className="flex justify-end mt-6 gap-3">
              <button className="px-4 py-2 text-sm text-white bg-blue-600 rounded-lg hover:bg-blue-700">
                Make Call
              </button>
              <button className="px-4 py-2 text-sm text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50">
                Edit Lead
              </button>
            </div>
          </div>
        </div>
      )}
    </AppLayout>
  );
};

export default LeadsPage;
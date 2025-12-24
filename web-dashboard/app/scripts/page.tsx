'use client';

import React, { useState, useEffect } from 'react';
import AppLayout from '../components/layout/AppLayout';
import Header from '../components/ui/Header';

const ScriptsPage = () => {
  const [scripts, setScripts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedScript, setSelectedScript] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingScript, setEditingScript] = useState(null);

  // Mock scripts data
  const mockScripts = [
    {
      id: '1',
      name: 'Main Greeting Script',
      script_type: 'greeting',
      content: `Hey [First Name]! This is [Agent Name] calling about the life insurance benefits information you requested. Did I catch you at a good time?

[Wait for response]

Great! I noticed you showed interest in learning more about your options. I'm calling because [Agent Name] is going to be in [County] this week helping folks just like you understand their life insurance benefits.

Let me check when they're available...`,
      is_active: true,
      created_at: '2025-12-20T10:00:00Z',
      updated_at: '2025-12-20T10:00:00Z'
    },
    {
      id: '2',
      name: 'Not Interested Objection',
      script_type: 'objection',
      objection_type: 'not_interested',
      content: `I completely understand, and I appreciate your time.

Before I let you go, can I ask - was it the timing that's not right, or are you pretty well covered with your current situation?

[If timing]: I totally get that. Life gets busy. Would it be helpful if I had [Agent Name] give you a quick call next week instead? It would just be a 15-minute conversation to make sure you're getting the best value.

[If covered]: That's great that you're thinking ahead! A lot of folks think they're covered until they realize their work policy isn't portable or doesn't cover final expenses. Would it hurt to just have a quick review to make sure there are no gaps?`,
      is_active: true,
      created_at: '2025-12-18T14:30:00Z',
      updated_at: '2025-12-18T14:30:00Z'
    },
    {
      id: '3',
      name: 'How Did You Get My Number?',
      script_type: 'objection',
      objection_type: 'source_inquiry',
      content: `That's a great question! You filled out a form requesting information about life insurance benefits. Do you remember looking into coverage options recently?

[If yes]: Perfect! That's exactly why I'm calling. You expressed interest in learning more about your options.

[If no]: No problem - sometimes we fill things out online and forget. The important thing is you were smart to look into this. A lot of people put it off until it's too late.

The good news is [Agent Name] specializes in helping people in [County] find affordable coverage that actually fits their budget...`,
      is_active: true,
      created_at: '2025-12-15T09:15:00Z',
      updated_at: '2025-12-15T09:15:00Z'
    },
    {
      id: '4',
      name: 'Appointment Scheduling',
      script_type: 'closing',
      content: `Perfect! [Agent Name] is going to love working with you.

Let me see what they have available... I can get you in tomorrow at 2 PM or Thursday at 10 AM. Which works better for your schedule?

[Get confirmation]

Excellent! So that's [Day] at [Time] at [Address].

Now, [Agent Name] drives a [Car Description] and is [Physical Description], so you'll recognize them right away.

They'll bring some options that fit your budget and explain everything in plain English - no insurance jargon.

Can I get a good callback number in case anything comes up?

[Confirm details]

Perfect! [Agent Name] is really looking forward to meeting with you. Have a great rest of your day!`,
      is_active: true,
      created_at: '2025-12-12T16:20:00Z',
      updated_at: '2025-12-12T16:20:00Z'
    }
  ];

  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      setScripts(mockScripts);
      setLoading(false);
    }, 1000);
  }, []);

  const getScriptTypeColor = (type: string) => {
    switch(type) {
      case 'greeting':
        return 'bg-blue-50 text-blue-700 border border-blue-200';
      case 'objection':
        return 'bg-amber-50 text-amber-700 border border-amber-200';
      case 'closing':
        return 'bg-emerald-50 text-emerald-700 border border-emerald-200';
      default:
        return 'bg-slate-50 text-slate-600 border border-slate-200';
    }
  };

  const handleCreateScript = () => {
    const newScript = {
      id: Date.now().toString(),
      name: 'New Script',
      script_type: 'greeting',
      content: 'Your script content here...',
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    setScripts([...scripts, newScript]);
    setEditingScript(newScript);
    setShowCreateModal(false);
  };

  const handleSaveScript = (script) => {
    setScripts(scripts.map(s =>
      s.id === script.id ? { ...script, updated_at: new Date().toISOString() } : s
    ));
    setEditingScript(null);
  };

  const handleDeleteScript = (scriptId: string) => {
    if (confirm('Are you sure you want to delete this script?')) {
      setScripts(scripts.filter(script => script.id !== scriptId));
    }
  };

  const toggleScriptStatus = (scriptId: string) => {
    setScripts(scripts.map(script =>
      script.id === scriptId
        ? { ...script, is_active: !script.is_active }
        : script
    ));
  };

  if (loading) {
    return (
      <AppLayout>
        <Header title="Scripts" subtitle="Manage call scripts and objection handlers" />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-slate-500">Loading scripts...</div>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <Header
        title="Scripts"
        subtitle={`${scripts.length} scripts configured`}
      >
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 text-sm text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 transition-colors"
        >
          + New Script
        </button>
      </Header>

      <div className="flex-1 overflow-auto">
        <div className="p-8">
          {/* Scripts Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {scripts.map((script) => (
              <div key={script.id} className="bg-white rounded-xl border border-slate-200 p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-slate-900 mb-2">{script.name}</h3>
                    <div className="flex items-center gap-3">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${getScriptTypeColor(script.script_type)}`}>
                        {script.script_type}
                      </span>
                      {script.objection_type && (
                        <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-600">
                          {script.objection_type.replace('_', ' ')}
                        </span>
                      )}
                      <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                        script.is_active
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : 'bg-slate-50 text-slate-600 border border-slate-200'
                      }`}>
                        {script.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setEditingScript(script)}
                      className="text-blue-600 hover:text-blue-800 text-sm"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => toggleScriptStatus(script.id)}
                      className="text-amber-600 hover:text-amber-800 text-sm"
                    >
                      {script.is_active ? 'Deactivate' : 'Activate'}
                    </button>
                    <button
                      onClick={() => handleDeleteScript(script.id)}
                      className="text-red-600 hover:text-red-800 text-sm"
                    >
                      Delete
                    </button>
                  </div>
                </div>

                <div className="bg-slate-50 rounded-lg p-4 mb-4">
                  <div className="text-sm text-slate-600 line-clamp-4">
                    {script.content.substring(0, 200)}
                    {script.content.length > 200 && '...'}
                  </div>
                </div>

                <div className="flex items-center justify-between text-xs text-slate-500">
                  <span>Updated {new Date(script.updated_at).toLocaleDateString()}</span>
                  <button
                    onClick={() => setSelectedScript(script)}
                    className="text-emerald-600 hover:text-emerald-800 font-medium"
                  >
                    View Full Script →
                  </button>
                </div>
              </div>
            ))}

            {/* Add Script Card */}
            <div
              onClick={() => setShowCreateModal(true)}
              className="bg-slate-50 border-2 border-dashed border-slate-300 rounded-xl p-6 flex flex-col items-center justify-center min-h-[280px] cursor-pointer hover:border-emerald-400 hover:bg-emerald-50/50 transition-colors"
            >
              <div className="w-12 h-12 bg-emerald-100 rounded-full flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">Create New Script</h3>
              <p className="text-sm text-slate-500 text-center">Add a new call script or objection handler</p>
            </div>
          </div>
        </div>
      </div>

      {/* View Script Modal */}
      {selectedScript && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-lg font-semibold text-slate-900">{selectedScript.name}</h3>
              <button
                onClick={() => setSelectedScript(null)}
                className="text-slate-400 hover:text-slate-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="mb-6">
              <div className="flex items-center gap-3 mb-4">
                <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${getScriptTypeColor(selectedScript.script_type)}`}>
                  {selectedScript.script_type}
                </span>
                {selectedScript.objection_type && (
                  <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-600">
                    {selectedScript.objection_type.replace('_', ' ')}
                  </span>
                )}
              </div>
              <div className="bg-slate-50 p-6 rounded-lg">
                <pre className="text-sm text-slate-700 whitespace-pre-wrap font-mono">
                  {selectedScript.content}
                </pre>
              </div>
            </div>

            <div className="flex justify-end gap-3">
              <button
                onClick={() => {
                  setEditingScript(selectedScript);
                  setSelectedScript(null);
                }}
                className="px-4 py-2 text-sm text-white bg-blue-600 rounded-lg hover:bg-blue-700"
              >
                Edit Script
              </button>
              <button
                onClick={() => setSelectedScript(null)}
                className="px-4 py-2 text-sm text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Script Modal */}
      {editingScript && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-lg font-semibold text-slate-900">
                {editingScript.id.length > 5 ? 'Edit Script' : 'Create Script'}
              </h3>
              <button
                onClick={() => setEditingScript(null)}
                className="text-slate-400 hover:text-slate-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Script Name</label>
                <input
                  type="text"
                  value={editingScript.name}
                  onChange={(e) => setEditingScript({...editingScript, name: e.target.value})}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-emerald-500 focus:border-emerald-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Script Type</label>
                  <select
                    value={editingScript.script_type}
                    onChange={(e) => setEditingScript({...editingScript, script_type: e.target.value})}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-emerald-500 focus:border-emerald-500"
                  >
                    <option value="greeting">Greeting</option>
                    <option value="objection">Objection Handler</option>
                    <option value="closing">Closing</option>
                  </select>
                </div>

                {editingScript.script_type === 'objection' && (
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">Objection Type</label>
                    <select
                      value={editingScript.objection_type || ''}
                      onChange={(e) => setEditingScript({...editingScript, objection_type: e.target.value})}
                      className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-emerald-500 focus:border-emerald-500"
                    >
                      <option value="not_interested">Not Interested</option>
                      <option value="source_inquiry">How Did You Get My Number?</option>
                      <option value="too_busy">Too Busy Right Now</option>
                      <option value="already_covered">Already Have Insurance</option>
                      <option value="send_information">Send Me Information</option>
                    </select>
                  </div>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Script Content</label>
                <textarea
                  value={editingScript.content}
                  onChange={(e) => setEditingScript({...editingScript, content: e.target.value})}
                  rows={12}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-emerald-500 focus:border-emerald-500 font-mono text-sm"
                  placeholder="Enter your script content here..."
                />
                <div className="text-xs text-slate-500 mt-2">
                  Use placeholders like [First Name], [Agent Name], [County] for dynamic content.
                </div>
              </div>
            </div>

            <div className="flex justify-end mt-6 gap-3">
              <button
                onClick={() => setEditingScript(null)}
                className="px-4 py-2 text-sm text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                onClick={() => handleSaveScript(editingScript)}
                className="px-4 py-2 text-sm text-white bg-emerald-600 rounded-lg hover:bg-emerald-700"
              >
                Save Script
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Script Type Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-lg font-semibold text-slate-900">Choose Script Type</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-3">
              {[
                { type: 'greeting', name: 'Greeting Script', desc: 'Opening script for initial contact' },
                { type: 'objection', name: 'Objection Handler', desc: 'Response to common objections' },
                { type: 'closing', name: 'Closing Script', desc: 'Appointment scheduling and close' }
              ].map(option => (
                <button
                  key={option.type}
                  onClick={() => {
                    setEditingScript({
                      id: Date.now().toString(),
                      name: `New ${option.name}`,
                      script_type: option.type,
                      content: '',
                      is_active: true,
                      created_at: new Date().toISOString(),
                      updated_at: new Date().toISOString()
                    });
                    setShowCreateModal(false);
                  }}
                  className="w-full text-left p-4 border border-slate-200 rounded-lg hover:border-emerald-300 hover:bg-emerald-50/50 transition-colors"
                >
                  <div className="font-medium text-slate-900">{option.name}</div>
                  <div className="text-sm text-slate-500 mt-1">{option.desc}</div>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </AppLayout>
  );
};

export default ScriptsPage;
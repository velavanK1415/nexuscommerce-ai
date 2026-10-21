import React, { useState } from 'react';
import { X, ShieldAlert, CheckCircle, FileSignature, ArrowRight, Sparkles } from './icons';
import Tooltip from './Tooltip';

export default function MandateConfigModal({ isOpen, onClose, onMandateCreated }) {
  const [formData, setFormData] = useState({
    buyer_name: 'Apex Global Logistics Corp',
    buyer_email: 'procurement@apexlogistics.io',
    title: 'Autonomous Sourcing: AI Cluster GPUs (NVIDIA H100)',
    item_name: 'NVIDIA H100 SXM5 80GB Server Node',
    target_categories: ['AI Compute Hardware', 'Data Center Equipment'],
    quantity: 100,
    max_unit_price: 32000.0,
    max_total_budget: 3200000.0,
    quality_tier: 'Enterprise',
    notes: 'Tier-1 enterprise warranty, authentic serial tracking, 2-step authorization hold & milestone captures required.',
  });

  const templates = [
    {
      label: '⚡ AI Cluster GPUs',
      title: 'Autonomous Sourcing: AI Cluster GPUs (NVIDIA H100)',
      item_name: 'NVIDIA H100 SXM5 80GB Server Node',
      target_categories: ['AI Compute Hardware', 'Data Center Equipment'],
      quantity: 100,
      max_unit_price: 32000.0,
      max_total_budget: 3200000.0,
      quality_tier: 'Enterprise',
      notes: 'Tier-1 enterprise warranty, authentic serial tracking, 2-step authorization hold & milestone captures required.',
    },
    {
      label: '🛡️ Strict Defense HW',
      title: 'Autonomous Sourcing: Strict Defense Tactical Gateways',
      item_name: 'Ruggedized Quantum-Resistant Tactical Gateway',
      target_categories: ['Edge Infrastructure', 'Networking Hardware'],
      quantity: 50,
      max_unit_price: 4500.0,
      max_total_budget: 225000.0,
      quality_tier: 'Enterprise',
      notes: 'Strict 7-day delivery SLA. Zero tolerance for unverified carrier scan.',
    },
    {
      label: '🏢 Urgent Office Refresh',
      title: 'Autonomous Sourcing: Urgent Office Hardware Refresh',
      item_name: 'Nexus UltraWide 5K Thunderbolt Professional Displays',
      target_categories: ['Enterprise Hardware'],
      quantity: 200,
      max_unit_price: 850.0,
      max_total_budget: 170000.0,
      quality_tier: 'Standard',
      notes: 'Fast commercial delivery. Bulk volume pricing expected.',
    },
  ];

  const applyTemplate = (t) => {
    setFormData((prev) => ({
      ...prev,
      title: t.title,
      item_name: t.item_name,
      target_categories: t.target_categories,
      quantity: t.quantity,
      max_unit_price: t.max_unit_price,
      max_total_budget: t.max_total_budget,
      quality_tier: t.quality_tier,
      notes: t.notes,
    }));
  };

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await onMandateCreated(formData);
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to submit mandate');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in">
      <div className="bg-[#111827] border border-slate-700 w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center">
              <FileSignature className="w-4 h-4 text-indigo-400" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Configure Procurement Mandate</h3>
              <p className="text-xs text-slate-400">Deterministic code boundary: Autonomous agents cannot violate this envelope</p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* 1-Click Mandate Templates Strip */}
        <div className="px-6 py-2.5 bg-slate-900/40 border-b border-slate-800 flex items-center space-x-2 text-xs overflow-x-auto">
          <span className="text-slate-400 font-semibold shrink-0">1-Click Presets:</span>
          {templates.map((t, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => applyTemplate(t)}
              className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-indigo-600 hover:text-white text-slate-300 font-medium text-[11px] border border-slate-700 hover:border-indigo-500 transition-all shrink-0"
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4 overflow-y-auto flex-1">
          {error && (
            <div className="p-3 rounded-lg bg-red-950/40 border border-red-500/40 text-red-300 text-xs flex items-center space-x-2">
              <ShieldAlert className="w-4 h-4 shrink-0 text-red-400" />
              <span>{error}</span>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Buyer Organization</label>
              <input
                type="text"
                value={formData.buyer_name}
                onChange={(e) => setFormData({ ...formData, buyer_name: e.target.value })}
                className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-indigo-500"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Buyer Email</label>
              <input
                type="email"
                value={formData.buyer_email}
                onChange={(e) => setFormData({ ...formData, buyer_email: e.target.value })}
                className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-indigo-500"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Mandate Title</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-indigo-500"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Item / Asset Specification</label>
            <input
              type="text"
              value={formData.item_name}
              onChange={(e) => setFormData({ ...formData, item_name: e.target.value })}
              className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-indigo-500"
              required
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Quantity</label>
              <input
                type="number"
                min="1"
                value={formData.quantity}
                onChange={(e) => {
                  const q = parseInt(e.target.value) || 1;
                  setFormData({
                    ...formData,
                    quantity: q,
                    max_total_budget: Math.round(q * formData.max_unit_price),
                  });
                }}
                className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-indigo-500"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Max Unit Price (USD $)</label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                value={formData.max_unit_price}
                onChange={(e) => {
                  const p = parseFloat(e.target.value) || 0;
                  setFormData({
                    ...formData,
                    max_unit_price: p,
                    max_total_budget: Math.round(formData.quantity * p),
                  });
                }}
                className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-indigo-500"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Max Total Budget (USD $)</label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                value={formData.max_total_budget}
                onChange={(e) => setFormData({ ...formData, max_total_budget: parseFloat(e.target.value) || 0 })}
                className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-indigo-500"
                required
              />
            </div>
          </div>

          <div className="p-3 rounded-xl bg-indigo-950/20 border border-indigo-500/20">
            <h4 className="text-xs font-semibold text-indigo-300 mb-1 flex items-center space-x-1.5">
              <CheckCircle className="w-3.5 h-3.5 text-indigo-400" />
              <span>Cryptographic Tamper-Proof Invariant</span>
            </h4>
            <p className="text-[11px] text-slate-400">
              Upon submission, a SHA-256 digital signature binds this mandate into the PolicyEngine. 
              Neither buyer nor vendor agent can authorize a settlement that exceeds these budget ceiling rules.
            </p>
          </div>

          <div className="pt-2 flex items-center justify-end space-x-3 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-slate-300 hover:bg-slate-800 rounded-lg"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 text-xs font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-lg shadow-md shadow-indigo-600/30 flex items-center space-x-1.5"
            >
              <span>{loading ? 'Signing Mandate...' : 'Sign & Activate Mandate'}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

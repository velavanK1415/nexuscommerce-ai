import React, { useState } from 'react';
import { Zap, ShieldAlert, CheckCircle2, Play, AlertTriangle, ArrowRight, Bot, Lock, Sparkles } from './icons';

export default function ZeroKeyDemoPanel({ onRunLifecycle, isRunning, demoMode, onToggleDemoMode }) {
  // Default to NVIDIA H100 GPU cluster matching TEMPLATE-AI-GPUS and chart scale ($3.2M cap)
  const [simulateHitl, setSimulateHitl] = useState(false);
  const [itemName, setItemName] = useState('NVIDIA H100 SXM5 80GB Server Node');
  const [quantity, setQuantity] = useState(100);
  const [maxUnitPrice, setMaxUnitPrice] = useState(32000.0);
  const [result, setResult] = useState(null);

  const budgetCap = Math.round((parseInt(quantity) || 100) * (parseFloat(maxUnitPrice) || 32000.0));

  const handleRun = async (overrideHitl = null) => {
    const isHitl = overrideHitl !== null ? overrideHitl : simulateHitl;
    try {
      const res = await onRunLifecycle({
        item_name: itemName,
        quantity: parseInt(quantity) || 100,
        max_unit_price: parseFloat(maxUnitPrice) || 32000.0,
        max_total_budget: budgetCap,
        simulate_hitl_hold: isHitl,
      });
      setResult(res);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="bg-[#111827] border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
      
      {/* Banner */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <Zap className="w-5 h-5 text-slate-950 font-bold" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-base font-bold text-white">Zero-Key Evaluation Panel</h3>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                Judge Ready
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                PayPal Orders v2 Two-Step
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Run the full autonomous lifecycle end-to-end without supplying any live credentials.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* Quick Adversarial Surge Wow Trigger */}
          <button
            onClick={() => {
              setSimulateHitl(true);
              handleRun(true);
            }}
            disabled={isRunning}
            className="px-3 py-1.5 rounded-lg bg-amber-500/15 hover:bg-amber-500/25 border border-amber-500/40 text-amber-300 text-xs font-bold flex items-center space-x-1.5 transition-all disabled:opacity-50"
            title="Immediately trigger Adversarial Surge Spike to test PolicyEngine circuit breaker"
          >
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
            <span>Test Adversarial Surge Trap</span>
          </button>

          <button
            onClick={onToggleDemoMode}
            className="text-xs text-cyan-400 hover:text-cyan-300 underline font-medium pl-2"
          >
            {demoMode ? 'Switch to Live Mode' : 'Switch to Zero-Key Mock'}
          </button>
        </div>
      </div>

      {/* Mode Selector - Adversarial Surge Trap elevated to top prominence */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        
        {/* Option A: Adversarial Policy Violation Test (WOW BEAT) */}
        <div
          onClick={() => setSimulateHitl(true)}
          className={`p-4 rounded-xl border cursor-pointer transition-all ${
            simulateHitl
              ? 'bg-gradient-to-r from-amber-950/40 to-slate-900 border-amber-500/70 ring-2 ring-amber-500/30 shadow-md'
              : 'bg-slate-900/40 border-slate-800 hover:border-slate-700'
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-white flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              <span>Adversarial Policy Violation Test</span>
            </span>
            <span className="text-[10px] px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-bold uppercase border border-amber-500/30">
              ⭐ Evaluate First
            </span>
          </div>
          <p className="text-[11px] text-slate-300 leading-relaxed">
            Simulates supplier proposing a predatory price spike (+50%). PolicyEngine catches violation deterministically and places the order into a Human-in-the-Loop review hold with $0.00 treasury exposure.
          </p>
        </div>

        {/* Option B: Full Autonomous Settlement */}
        <div
          onClick={() => setSimulateHitl(false)}
          className={`p-4 rounded-xl border cursor-pointer transition-all ${
            !simulateHitl
              ? 'bg-gradient-to-r from-indigo-950/40 to-slate-900 border-indigo-500/60 ring-2 ring-indigo-500/20 shadow-md'
              : 'bg-slate-900/40 border-slate-800 hover:border-slate-700'
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-white flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Full Autonomous Settlement</span>
            </span>
            <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-semibold uppercase">
              Happy Path
            </span>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            ProcureBot & VendorBot negotiate bounded terms; PolicyEngine places 29-day authorization hold; ingests carrier tracking proof; releases 30% mobilization and 70% final delivery captures.
          </p>
        </div>

      </div>

      {/* 1-Click Mandate Preset Selector */}
      <div className="flex flex-wrap items-center gap-2 pt-1 pb-1">
        <span className="text-[11px] font-semibold text-slate-400">1-Click Mandate Presets:</span>
        <button
          type="button"
          onClick={() => {
            setItemName('NVIDIA H100 SXM5 80GB Server Node');
            setQuantity(100);
            setMaxUnitPrice(32000.0);
          }}
          className={`px-2.5 py-1 rounded-lg text-[11px] font-medium border transition-all ${
            quantity === 100 && maxUnitPrice === 32000.0
              ? 'bg-indigo-950 border-indigo-500 text-indigo-200 ring-1 ring-indigo-500/30'
              : 'bg-slate-900 hover:bg-indigo-950 text-indigo-300 border-indigo-500/40'
          }`}
        >
          ⚡ AI Cluster GPUs (100x @ $32k = $3.2M Cap)
        </button>
        <button
          type="button"
          onClick={() => {
            setItemName('NexusEdge Pro 100G Modular Edge Router');
            setQuantity(50);
            setMaxUnitPrice(1200.0);
          }}
          className={`px-2.5 py-1 rounded-lg text-[11px] font-medium border transition-all ${
            quantity === 50 && maxUnitPrice === 1200.0
              ? 'bg-slate-800 border-slate-500 text-white ring-1 ring-slate-500/30'
              : 'bg-slate-900 hover:bg-slate-800 text-slate-300 border-slate-700'
          }`}
        >
          🌐 100G Modular Router (50x @ $1,200 = $60k Cap)
        </button>
        <button
          type="button"
          onClick={() => {
            setItemName('Ruggedized Quantum-Resistant Tactical Gateway');
            setQuantity(50);
            setMaxUnitPrice(4500.0);
          }}
          className={`px-2.5 py-1 rounded-lg text-[11px] font-medium border transition-all ${
            quantity === 50 && maxUnitPrice === 4500.0
              ? 'bg-cyan-950 border-cyan-500 text-cyan-200 ring-1 ring-cyan-500/30'
              : 'bg-slate-900 hover:bg-cyan-950 text-cyan-300 border-cyan-500/40'
          }`}
        >
          🛡️ Strict Defense HW (50x @ $4.5k = $225k Cap)
        </button>
      </div>

      {/* Input parameters with explicit budget calculation */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="sm:col-span-2">
          <label className="block text-[11px] font-semibold text-slate-400 mb-1">Target Asset</label>
          <input
            type="text"
            value={itemName}
            onChange={(e) => setItemName(e.target.value)}
            className="w-full px-3 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded-lg text-white"
          />
        </div>
        <div>
          <label className="block text-[11px] font-semibold text-slate-400 mb-1">Batch Quantity</label>
          <input
            type="number"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            className="w-full px-3 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded-lg text-white font-mono"
          />
        </div>
        <div>
          <label className="block text-[11px] font-semibold text-slate-400 mb-1">Max Price Cap ($)</label>
          <input
            type="number"
            value={maxUnitPrice}
            onChange={(e) => setMaxUnitPrice(e.target.value)}
            className="w-full px-3 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded-lg text-white font-mono"
          />
        </div>
      </div>

      {/* Reconciled Budget Badge */}
      <div className="flex items-center justify-between px-3.5 py-2 rounded-xl bg-slate-900/90 border border-slate-800 text-xs">
        <div className="flex items-center space-x-2 text-slate-400">
          <span>Deterministic Budget Cap Formula:</span>
          <span className="font-mono text-cyan-300 font-bold">
            {quantity} units × ${parseFloat(maxUnitPrice || 0).toLocaleString()} = ${budgetCap.toLocaleString()} Cap
          </span>
        </div>
        <span className="text-[10px] font-mono text-emerald-400 uppercase">
          Reconciled across Mandate & Orders
        </span>
      </div>

      {/* Trigger Button */}
      <button
        onClick={() => handleRun(null)}
        disabled={isRunning}
        className="w-full py-3 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-cyan-500 hover:from-blue-500 hover:to-cyan-400 text-white font-bold text-xs shadow-lg shadow-indigo-600/30 flex items-center justify-center space-x-2 transition-all disabled:opacity-50"
      >
        <Play className={`w-4 h-4 fill-current ${isRunning ? 'animate-spin' : ''}`} />
        <span>{isRunning ? 'Running Autonomous Pipeline...' : `Execute 1-Click Autonomous Lifecycle (${simulateHitl ? 'Adversarial Surge Test' : 'Happy Path'})`}</span>
      </button>

      {/* Lifecycle Result Feedback */}
      {result && (
        <div className={`p-4 rounded-xl border text-xs space-y-2 ${
          result.lifecycle_status === 'COMPLETED_SETTLED'
            ? 'bg-emerald-950/30 border-emerald-500/40 text-emerald-300'
            : 'bg-amber-950/30 border-amber-500/40 text-amber-300'
        }`}>
          <div className="font-bold flex items-center space-x-1.5">
            {result.lifecycle_status === 'COMPLETED_SETTLED' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            ) : (
              <ShieldAlert className="w-4 h-4 text-amber-400" />
            )}
            <span>Status: {result.lifecycle_status}</span>
          </div>
          <p className="text-slate-300">{result.message || 'Complete lifecycle processed and verified.'}</p>
          {result.verification_result && (
            <div className="font-mono text-[11px] text-cyan-300 pt-1 border-t border-emerald-500/30 flex flex-wrap items-center justify-between gap-2">
              <span>Audit Root: {result.verification_result.root_sha256?.slice(0, 32)}...</span>
              <span className="text-emerald-400 font-bold">Grade: {result.verification_result.dispute_defense_grade}</span>
            </div>
          )}
        </div>
      )}

    </div>
  );
}

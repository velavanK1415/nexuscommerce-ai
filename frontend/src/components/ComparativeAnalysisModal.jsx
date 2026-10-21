import React, { useState, useEffect } from 'react';
import { 
  X, 
  Scale, 
  CheckCircle2, 
  AlertTriangle, 
  ShieldCheck, 
  ShieldAlert, 
  Zap, 
  ArrowRight,
  TrendingUp,
  RefreshCw
} from './icons';
import { api } from '../services/api';

/**
 * Multi-Run Comparative Analysis
 * Enables side-by-side forensic comparison of runs:
 * 1. Standard Autonomous Procurement (Happy Path)
 * 2. Adversarial Price Surge Injection (HITL Safety)
 * 3. Strict Defense Mandate (Tighter SLA & Hard Cap)
 */
export default function ComparativeAnalysisModal({ isOpen, onClose, onLaunchScenario }) {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedRunIds, setSelectedRunIds] = useState(['RUN-STD-001', 'RUN-ADV-002', 'RUN-STR-003']);

  const fetchRuns = async () => {
    setLoading(true);
    try {
      const data = await api.getComparativeRuns();
      if (data?.runs) {
        setRuns(data.runs);
      }
    } catch (e) {
      console.error('Failed to load comparative runs:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchRuns();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const activeRuns = runs.filter((r) => selectedRunIds.includes(r.id));

  const toggleSelectRun = (id) => {
    if (selectedRunIds.includes(id)) {
      if (selectedRunIds.length > 1) {
        setSelectedRunIds(selectedRunIds.filter((item) => item !== id));
      }
    } else {
      setSelectedRunIds([...selectedRunIds, id]);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
      <div className="bg-[#111827] border border-slate-700 w-full max-w-6xl rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">
        
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/80">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <Scale className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-base font-bold text-white">Multi-Run Comparative Analysis</h3>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-indigo-500/20 text-cyan-300 border border-indigo-500/30">
                  Agent Policy Adaptation
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Side-by-side comparison of agent behavior under standard pricing vs adversarial prompt injection vs tightened SLA policies.
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={fetchRuns}
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-all"
              title="Refresh runs"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-all"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Run Selector Pills */}
        <div className="px-6 py-3 bg-slate-900/40 border-b border-slate-800 flex flex-wrap items-center gap-2 text-xs">
          <span className="text-slate-400 font-semibold mr-1">Select Runs to Compare:</span>
          {runs.map((r) => {
            const isSelected = selectedRunIds.includes(r.id);
            return (
              <button
                key={r.id}
                onClick={() => toggleSelectRun(r.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium border flex items-center space-x-1.5 transition-all ${
                  isSelected
                    ? 'bg-indigo-600 text-white border-indigo-500 shadow-md shadow-indigo-600/30'
                    : 'bg-slate-900 text-slate-400 border-slate-800 hover:border-slate-700'
                }`}
              >
                <span>{r.name}</span>
                <span className="text-[10px] opacity-75 font-mono">({r.tag})</span>
              </button>
            );
          })}
        </div>

        {/* Side-by-Side Comparison Grid */}
        <div className="p-6 overflow-y-auto flex-1 space-y-6">
          <div className={`grid grid-cols-1 ${
            activeRuns.length === 1 ? 'md:grid-cols-1 max-w-lg mx-auto' : activeRuns.length === 2 ? 'md:grid-cols-2' : 'md:grid-cols-3'
          } gap-4`}>
            {activeRuns.map((run) => {
              const isHitl = run.hitl_triggered;
              const isStrict = run.tag === 'Strict Policy';

              return (
                <div
                  key={run.id}
                  className={`rounded-2xl border p-5 flex flex-col justify-between space-y-4 transition-all ${
                    isHitl
                      ? 'bg-slate-900/90 border-red-500/50 shadow-lg shadow-red-500/5'
                      : isStrict
                      ? 'bg-slate-900/90 border-indigo-500/50 shadow-lg shadow-indigo-500/5'
                      : 'bg-slate-900/90 border-emerald-500/50 shadow-lg shadow-emerald-500/5'
                  }`}
                >
                  {/* Card Header */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        isHitl
                          ? 'bg-red-500/20 text-red-300 border border-red-500/30'
                          : isStrict
                          ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                          : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                      }`}>
                        {run.tag}
                      </span>
                      <span className="text-[10px] font-mono text-slate-500">{run.id}</span>
                    </div>

                    <h4 className="text-base font-bold text-white leading-tight">{run.name}</h4>
                    <p className="text-xs text-slate-400 mt-1 leading-relaxed">{run.scenario}</p>
                  </div>

                  {/* Financial & Metric Specs */}
                  <div className="space-y-2 py-3 border-y border-slate-800 text-xs">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Asset & Qty:</span>
                      <span className="font-semibold text-white">{run.quantity}x {run.item_name}</span>
                    </div>

                    <div className="flex justify-between">
                      <span className="text-slate-400">Authorized Cap:</span>
                      <span className="font-mono text-amber-400 font-bold">${run.budget_cap.toLocaleString()}</span>
                    </div>

                    <div className="flex justify-between">
                      <span className="text-slate-400">Catalog Ask:</span>
                      <span className="font-mono text-slate-400">${run.catalog_ask.toFixed(2)} / unit</span>
                    </div>

                    <div className="flex justify-between">
                      <span className="text-slate-400">Final Settled Unit:</span>
                      <span className={`font-mono font-bold ${isHitl ? 'text-red-400 line-through' : 'text-emerald-400'}`}>
                        ${run.settled_unit_price.toFixed(2)}
                      </span>
                    </div>

                    <div className="flex justify-between">
                      <span className="text-slate-400">Total Settled Spend:</span>
                      <span className="font-mono font-bold text-white">
                        {isHitl ? '$0.00 (Halted Safe)' : `$${run.total_settled.toLocaleString()}`}
                      </span>
                    </div>

                    <div className="flex justify-between">
                      <span className="text-slate-400">Alpha Value Captured:</span>
                      <span className="font-mono font-bold text-emerald-400">
                        +${run.savings_achieved.toLocaleString()} ({run.savings_pct}%)
                      </span>
                    </div>

                    <div className="flex justify-between">
                      <span className="text-slate-400">Rounds Taken:</span>
                      <span className="font-mono text-cyan-400 font-bold">{run.rounds_taken} rounds</span>
                    </div>

                    <div className="flex justify-between">
                      <span className="text-slate-400">Policy Interventions:</span>
                      <span className={`font-mono font-bold ${run.policy_interventions > 0 ? 'text-amber-400' : 'text-slate-400'}`}>
                        {run.policy_interventions} {run.policy_interventions > 0 ? '(HITL Hold)' : '(None)'}
                      </span>
                    </div>

                    <div className="flex justify-between">
                      <span className="text-slate-400">Lead Time SLA:</span>
                      <span className="font-mono text-white">{run.lead_time_days > 0 ? `${run.lead_time_days} days` : 'N/A'}</span>
                    </div>

                    <div className="flex justify-between">
                      <span className="text-slate-400">Dispute Defense Grade:</span>
                      <span className="font-mono font-bold text-cyan-300">{run.evidence_grade} (Valid)</span>
                    </div>
                  </div>

                  {/* Key Takeaway & Scenario Quick Run */}
                  <div className="space-y-3">
                    <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800/80 text-[11px] text-slate-300">
                      <strong className="text-white block mb-0.5">Key Evaluator Takeaway:</strong>
                      {run.key_takeaway}
                    </div>

                    {onLaunchScenario && (
                      <button
                        onClick={() => {
                          onLaunchScenario(run);
                          onClose();
                        }}
                        className="w-full py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold flex items-center justify-center space-x-1.5 transition-all"
                      >
                        <Zap className="w-3.5 h-3.5 text-cyan-400" />
                        <span>Re-simulate This Scenario</span>
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-800 bg-slate-900/80 flex items-center justify-between text-xs text-slate-400">
          <div>
            Insight: PolicyEngine guarantees 0% false authorization under prompt injection while securing double-digit alpha under standard conditions.
          </div>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-medium"
          >
            Close Comparison
          </button>
        </div>
      </div>
    </div>
  );
}

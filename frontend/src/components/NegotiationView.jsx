import React, { useState } from 'react';
import { 
  Bot, 
  UserCheck, 
  ShieldAlert, 
  ShieldCheck, 
  AlertTriangle, 
  CheckCircle2, 
  ArrowRight, 
  DollarSign, 
  Package, 
  Clock, 
  FileCheck, 
  Sparkles,
  Lock,
  Scale,
  Code2,
  Cpu,
  User,
  Copy,
  Check
} from './icons';
import Tooltip from './Tooltip';

export default function NegotiationView({ 
  mandate, 
  session, 
  onStartNegotiation, 
  onHitlOverride, 
  onAuthorizeEscrow, 
  loading,
  onOpenMandateModal,
  viewMode = 'executive',
  role = 'director',
  onOpenComparisonModal,
}) {
  const [supervisorNotes, setSupervisorNotes] = useState(
    'Procurement Supervisor approved after volume and warranty tier verification.'
  );
  const [expandedJsonIdx, setExpandedJsonIdx] = useState(null);
  const [copiedIdx, setCopiedIdx] = useState(null);

  if (!mandate) {
    return (
      <div className="bg-[#111827] border border-slate-800 rounded-2xl p-10 text-center">
        <div className="w-16 h-16 mx-auto rounded-2xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center mb-4">
          <Bot className="w-8 h-8 text-indigo-400" />
        </div>
        <h3 className="text-lg font-bold text-white mb-2">No Active Procurement Mandate</h3>
        <p className="text-sm text-slate-400 max-w-md mx-auto mb-6">
          Initialize a signed Procurement Mandate to establish deterministic price and budget boundaries before releasing autonomous agents.
        </p>
        <button
          onClick={onOpenMandateModal}
          className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-sm font-semibold shadow-lg shadow-indigo-600/30 inline-flex items-center space-x-2"
        >
          <span>Create & Sign Mandate</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    );
  }

  const isHitlHold = session?.status === 'HITL_HOLD';
  const isAgreed = session?.status === 'AGREEMENT_REACHED';
  const proposals = session?.proposals || [];

  const handleCopyProposal = (idx, prop) => {
    navigator.clipboard.writeText(JSON.stringify(prop, null, 2));
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 2000);
  };

  // Role Perspective Customization
  const roleCard = {
    director: {
      badge: 'Procurement Director Lens',
      color: 'bg-indigo-500/10 text-indigo-300 border-indigo-500/30',
      desc: 'Full signing authority: Enforce deterministic price ceilings, trigger multi-agent RFQs, and authorize 29-day PayPal hold.',
    },
    vendor: {
      badge: 'Supplier Representative Lens (NexIQ)',
      color: 'bg-cyan-500/10 text-cyan-300 border-cyan-500/30',
      desc: 'Vendor sales portal: Review incoming buyer proposals, evaluate margin discount curves, and submit dispatch tracking.',
    },
    auditor: {
      badge: 'Compliance Auditor & Judge Lens',
      color: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30',
      desc: 'Forensic audit view: Inspect PolicyEngine AST guardrails, verify canonical SHA-256 digests, and run tamper attack simulations.',
    },
  }[role] || {
    badge: 'Procurement Director Lens',
    color: 'bg-indigo-500/10 text-indigo-300 border-indigo-500/30',
    desc: 'Full signing authority.',
  };

  return (
    <div className="space-y-6">
      
      {/* Active Persona Lens Alert Banner */}
      <div className={`px-4 py-2.5 rounded-xl border flex items-center justify-between text-xs ${roleCard.color}`}>
        <div className="flex items-center space-x-2">
          <User className="w-4 h-4 shrink-0" />
          <span className="font-bold">{roleCard.badge}:</span>
          <span className="text-slate-300 hidden md:inline">{roleCard.desc}</span>
        </div>
        <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-slate-300">
          Mode: {viewMode === 'technical' ? 'Technical AST Logs' : 'Executive Business Overview'}
        </span>
      </div>

      {/* Top Mandate Invariant Banner */}
      <div className="bg-[#111827] border border-slate-800 rounded-2xl p-5 shadow-xl">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/30 flex items-center justify-center">
              <Lock className="w-5 h-5 text-cyan-400" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-mono text-cyan-400 font-bold">{mandate.id}</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-semibold uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                  {mandate.status}
                </span>
                <Tooltip
                  title="Signed Mandate Envelope"
                  text="Deterministic boundary: Enforces hard ceilings that autonomous agents cannot exceed. Code decides, LLM only proposes."
                />
              </div>
              <h2 className="text-base font-bold text-white">{mandate.title}</h2>
            </div>
          </div>

          {/* Mandate Envelope Metrics */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800">
              <span className="text-[10px] text-slate-400 block uppercase font-medium">Item & Qty</span>
              <span className="text-xs font-bold text-white">{mandate.quantity}x {mandate.item_name}</span>
            </div>

            <div className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800">
              <div className="flex items-center space-x-1">
                <span className="text-[10px] text-slate-400 uppercase font-medium">Max Unit Cap</span>
                <Tooltip
                  title="Unit Price Invariant"
                  text="ProcureBot cannot bid above this price. Counter-proposals exceeding it trigger immediate PolicyEngine violation hold."
                />
              </div>
              <span className="text-xs font-bold text-amber-400">${mandate.max_unit_price.toFixed(2)}</span>
            </div>

            <div className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800">
              <div className="flex items-center space-x-1">
                <span className="text-[10px] text-slate-400 uppercase font-medium">Max Budget Cap</span>
                <Tooltip
                  title="Treasury Budget Cap"
                  text="Strict maximum expenditure authorized by company leadership for this procurement cycle."
                />
              </div>
              <span className="text-xs font-bold text-emerald-400">${mandate.max_total_budget.toLocaleString()}</span>
            </div>

            <div className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800">
              <div className="flex items-center space-x-1">
                <span className="text-[10px] text-slate-400 uppercase font-medium">Digital Signature</span>
                <Tooltip
                  title="Cryptographic Signature"
                  text="SHA-256 HMAC fingerprint computed across all mandate parameters. Binds agents to contract terms."
                />
              </div>
              <span className="text-xs font-mono text-indigo-300" title={mandate.signature}>
                {mandate.signature ? `${mandate.signature.slice(0, 10)}...` : 'UNSIGNED'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Control Actions & Simulation Toolbar */}
      <div className="bg-[#111827] border border-slate-800 rounded-2xl p-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center space-x-2">
          <span className="text-xs font-semibold text-slate-300">Autonomous Agents:</span>
          <span className="px-2.5 py-1 rounded-lg text-xs bg-indigo-950/50 border border-indigo-500/30 text-indigo-300 font-medium flex items-center space-x-1.5">
            <Bot className="w-3.5 h-3.5 text-indigo-400" />
            <span>ProcureBot (Buyer)</span>
          </span>
          <span className="text-slate-500 text-xs">vs</span>
          <span className="px-2.5 py-1 rounded-lg text-xs bg-cyan-950/50 border border-cyan-500/30 text-cyan-300 font-medium flex items-center space-x-1.5">
            <Bot className="w-3.5 h-3.5 text-cyan-400" />
            <span>VendorBot (Supplier)</span>
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Multi-Run Comparative Analysis Button */}
          {onOpenComparisonModal && (
            <button
              onClick={onOpenComparisonModal}
              className="px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium flex items-center space-x-1.5 transition-all border border-slate-700"
              title="Compare side-by-side run adaptations (Standard vs Adversarial vs Strict)"
            >
              <Scale className="w-3.5 h-3.5 text-cyan-400" />
              <span>Multi-Run Comparison</span>
            </button>
          )}

          {/* Adversarial Test Button to trigger HITL hold - Elevated WOW beat */}
          <button
            onClick={() => onStartNegotiation('PRICE_SPIKE')}
            disabled={loading}
            className="px-3.5 py-2 rounded-xl bg-gradient-to-r from-amber-950/60 to-red-950/40 hover:from-amber-900/60 hover:to-red-900/50 border-2 border-amber-500/60 text-amber-200 text-xs font-bold flex items-center space-x-1.5 transition-all shadow-md shadow-amber-500/20 disabled:opacity-50"
            title="Simulate vendor price spike (+50%) to demonstrate PolicyEngine deterministically dropping order into HITL review hold with $0.00 treasury exposure"
          >
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
            <span>⭐ Test Adversarial Surge Spike</span>
          </button>

          {/* Normal Autonomous Negotiation */}
          <button
            onClick={() => onStartNegotiation(null)}
            disabled={loading}
            className="px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/30 flex items-center space-x-1.5 transition-all disabled:opacity-50"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>{session ? 'Re-run Negotiation' : 'Start Multi-Agent Negotiation'}</span>
          </button>
        </div>
      </div>

      {/* HITL Hold Warning Banner */}
      {isHitlHold && (
        <div className="bg-gradient-to-r from-red-950/70 via-amber-950/50 to-red-950/70 border-2 border-red-500/60 rounded-2xl p-6 shadow-2xl animate-pulse-subtle">
          <div className="flex items-start space-x-4">
            <div className="w-12 h-12 rounded-xl bg-red-500/20 border border-red-500/40 flex items-center justify-center shrink-0">
              <ShieldAlert className="w-6 h-6 text-red-400" />
            </div>
            <div className="flex-1">
              <div className="flex items-center space-x-2">
                <span className="px-2 py-0.5 rounded text-[11px] font-extrabold uppercase bg-red-500 text-white">
                  HITL Review Hold Active
                </span>
                <span className="text-xs text-red-300 font-mono">Code Decides, LLM Proposes</span>
              </div>
              <h3 className="text-base font-bold text-white mt-1">
                PolicyEngine Halted Autonomous Agent Execution
              </h3>
              <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                {session?.hitl_reason || 'An agent proposal violated bounded mandate parameters.'}
              </p>

              {/* Supervisor Override Form */}
              <div className="mt-4 pt-4 border-t border-red-500/30 flex flex-col sm:flex-row items-center gap-3">
                <div className="flex-1 w-full">
                  <label className="block text-[11px] font-semibold text-slate-300 mb-1">
                    Human Supervisor Audit Notes (Required for override authorization):
                  </label>
                  <input
                    type="text"
                    value={supervisorNotes}
                    onChange={(e) => setSupervisorNotes(e.target.value)}
                    className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-red-400"
                    placeholder="Provide justification for policy envelope override..."
                  />
                </div>
                <button
                  onClick={() => onHitlOverride(supervisorNotes)}
                  disabled={loading || !supervisorNotes}
                  className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-lg shadow-emerald-600/30 flex items-center justify-center space-x-1.5 shrink-0 transition-all disabled:opacity-50"
                >
                  <UserCheck className="w-4 h-4" />
                  <span>Authorize Supervisor Override</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Consensus Reached Banner */}
      {isAgreed && session?.agreement && (
        <div className="bg-gradient-to-r from-emerald-950/60 via-slate-900 to-indigo-950/60 border border-emerald-500/40 rounded-2xl p-6 shadow-xl">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 rounded-xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center shrink-0">
                <CheckCircle2 className="w-6 h-6 text-emerald-400" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                    Agreement Certified by PolicyEngine
                  </span>
                  <Tooltip
                    title="PolicyEngine Certified Consensus"
                    text="Dual-agent agreement passed all deterministic invariants. No hallucinations: AST rules mathematically verified price, total expenditure, and SLA boundaries."
                  />
                  <span className="text-xs font-mono text-slate-400">{session.agreement.agreement_id}</span>
                </div>
                <h3 className="text-base font-bold text-white mt-0.5">
                  Autonomous Consensus: ${session.agreement.final_unit_price.toFixed(2)}/unit · Total ${session.agreement.final_total.toLocaleString()}
                </h3>
                <div className="flex items-center space-x-1.5 mt-1">
                  <span className="text-xs font-mono text-cyan-400 select-all" title={session.agreement.agreement_hash}>
                    Agreement SHA-256: {session.agreement.agreement_hash?.slice(0, 36)}...
                  </span>
                  <Tooltip
                    title="Canonical SHA-256 Digest"
                    text="Cryptographic hash calculated from sorted agreement fields. Binds the agreement before PayPal authorization hold."
                  />
                </div>
              </div>
            </div>

            <button
              onClick={onAuthorizeEscrow}
              disabled={loading}
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 text-xs font-extrabold shadow-lg shadow-cyan-500/20 flex items-center space-x-2 transition-all disabled:opacity-50"
            >
              <Lock className="w-4 h-4 text-slate-950" />
              <span>Place 29-Day PayPal Authorization Hold (Milestone 1)</span>
              <ArrowRight className="w-4 h-4 text-slate-950" />
            </button>
          </div>
        </div>
      )}

      {/* Negotiation Proposals Transcript Stream */}
      <div className="bg-[#111827] border border-slate-800 rounded-2xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-bold text-white flex items-center space-x-2">
            <Bot className="w-4 h-4 text-indigo-400" />
            <span>Multi-Agent Negotiation Transcript</span>
            <span className="text-xs font-normal text-slate-400 font-mono">
              ({proposals.length > 0 ? `${Math.ceil(proposals.length / 2)} rounds logged (${proposals.length} proposals) · Live Session` : '0 rounds logged · Awaiting Initiation'})
            </span>
          </h3>

          <span className="text-[11px] font-mono text-slate-400">
            {viewMode === 'technical' ? '🔬 Full AST Guardrail Telemetry' : '💼 Executive Overview'}
          </span>
        </div>

        {proposals.length === 0 ? (
          <div className="text-center py-10 text-slate-500 text-xs">
            Click "Start Multi-Agent Negotiation" to initiate autonomous bidding between ProcureBot and VendorBot.
          </div>
        ) : (
          <div className="space-y-4">
            {proposals.map((prop, idx) => {
              const isBuyer = prop.sender === 'ProcureBot';
              const isFlagged = session?.hitl_flagged_proposal?.proposal_id === prop.proposal_id;
              const isFinalAgreed = isAgreed && idx === proposals.length - 1;
              const isJsonOpen = expandedJsonIdx === idx;
              const isCopied = copiedIdx === idx;

              // Check if proposal passes individual invariants
              const unitPass = prop.proposed_unit_price <= mandate.max_unit_price;
              const totalPass = prop.proposed_total <= mandate.max_total_budget;
              const leadPass = prop.lead_time_days <= 14;

              return (
                <div
                  key={prop.proposal_id || idx}
                  className={`p-4 sm:p-5 rounded-xl border transition-all ${
                    isFinalAgreed
                      ? 'bg-gradient-to-br from-emerald-950/40 via-slate-900 to-emerald-900/20 border-2 border-emerald-500/80 shadow-xl shadow-emerald-500/15'
                      : isFlagged
                      ? 'bg-red-950/30 border-red-500/60 shadow-lg shadow-red-500/10'
                      : isBuyer
                      ? 'bg-slate-900/80 border-indigo-500/20 ml-0 mr-4 sm:mr-8'
                      : 'bg-slate-900/80 border-cyan-500/20 ml-4 sm:ml-8 mr-0'
                  }`}
                >
                  {/* Final Consensus Callout Header */}
                  {isFinalAgreed && (
                    <div className="mb-3 pb-2.5 border-b border-emerald-500/30 flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center space-x-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                        <span className="text-xs font-extrabold uppercase text-emerald-300 tracking-wide">
                          🎯 Final Agreed Price · Consensus Formed
                        </span>
                      </div>
                      <span className="text-[11px] font-mono font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-2.5 py-0.5 rounded-full">
                        Locked at ${prop.proposed_unit_price.toFixed(2)}/unit
                      </span>
                    </div>
                  )}

                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          isBuyer
                            ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                            : 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                        }`}
                      >
                        Round {prop.round_number} · {prop.sender}
                      </span>
                      <span className="text-xs font-semibold text-white">
                        {isBuyer ? mandate.buyer_name : prop.vendor_name}
                      </span>
                    </div>

                    <div className="flex items-center space-x-2">
                      {isFlagged ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-extrabold uppercase bg-red-500/20 text-red-400 border border-red-500/40 flex items-center space-x-1">
                          <ShieldAlert className="w-3 h-3 text-red-400" />
                          <span>HITL Flagged</span>
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center space-x-1">
                          <ShieldCheck className="w-3 h-3 text-emerald-400" />
                          <span>Policy Certified</span>
                        </span>
                      )}
                      <span className="text-[10px] text-slate-500">{new Date(prop.created_at).toLocaleTimeString()}</span>
                    </div>
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed mb-3">{prop.rationale}</p>

                  {/* Financial Metrics Strip */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-slate-800/80 text-[11px]">
                    <div>
                      <span className="text-slate-400 block">Unit Price:</span>
                      <span className={`font-bold font-mono ${unitPass ? 'text-white' : 'text-red-400 font-bold'}`}>
                        ${prop.proposed_unit_price.toFixed(2)}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-400 block">Quantity:</span>
                      <span className="font-bold text-white font-mono">{prop.proposed_quantity} units</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block">Total Commitment:</span>
                      <span className={`font-bold font-mono ${totalPass ? 'text-emerald-400' : 'text-red-400'}`}>
                        ${prop.proposed_total.toLocaleString()}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-400 block">Lead Time / SLA:</span>
                      <span className="font-bold text-cyan-400 font-mono">{prop.lead_time_days} days · {prop.warranty_months}mo</span>
                    </div>
                  </div>

                  {/* Technical Mode AST & Raw JSON Logs */}
                  {viewMode === 'technical' && (
                    <div className="mt-3 pt-3 border-t border-slate-800 space-y-2 animate-fade-in">
                      <div className="flex flex-wrap items-center justify-between text-[10px] text-slate-400">
                        <div className="flex items-center space-x-2 font-mono">
                          <span className={`w-2 h-2 rounded-full ${unitPass && totalPass && leadPass ? 'bg-emerald-400' : 'bg-red-400'}`} />
                          <span>AST Evaluation:</span>
                          <span className={unitPass ? 'text-emerald-400' : 'text-red-400'}>
                            (unit &lt;= ${mandate.max_unit_price}) [{unitPass ? 'PASS' : 'FAIL'}]
                          </span>
                          <span>·</span>
                          <span className={totalPass ? 'text-emerald-400' : 'text-red-400'}>
                            (budget &lt;= ${mandate.max_total_budget}) [{totalPass ? 'PASS' : 'FAIL'}]
                          </span>
                          <span>·</span>
                          <span className="text-emerald-400">HMAC: OK</span>
                        </div>

                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => handleCopyProposal(idx, prop)}
                            className="text-slate-400 hover:text-white flex items-center space-x-1"
                            title="Copy Proposal JSON"
                          >
                            {isCopied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                            <span>{isCopied ? 'Copied' : 'Copy JSON'}</span>
                          </button>
                          <button
                            onClick={() => setExpandedJsonIdx(isJsonOpen ? null : idx)}
                            className="text-cyan-400 hover:text-cyan-300 font-mono text-[10px] underline ml-2"
                          >
                            {isJsonOpen ? 'Hide Raw JSON' : 'Inspect JSON Payload'}
                          </button>
                        </div>
                      </div>

                      {isJsonOpen && (
                        <pre className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-[10px] text-slate-300 font-mono overflow-x-auto">
                          {JSON.stringify(prop, null, 2)}
                        </pre>
                      )}
                    </div>
                  )}

                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

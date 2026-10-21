import React, { useState } from 'react';
import { 
  ShieldCheck, 
  AlertTriangle, 
  CheckCircle2, 
  Lock, 
  Clock, 
  ChevronDown, 
  ChevronUp, 
  Zap, 
  FileCheck 
} from './icons';

export default function ExecutiveCaptionBar({ session, order, mandate, bundle }) {
  const [isExpanded, setIsExpanded] = useState(false);

  const isHitlHold = session?.status === 'HITL_HOLD';
  const isSettled = order?.status === 'COMPLETED' || order?.status === 'SETTLED' || order?.milestone_state === 'DELIVERED';
  const isInTransit = order?.status === 'IN_TRANSIT' || order?.milestone_state === 'IN_TRANSIT';
  const isAuthorized = order?.status === 'FUNDS_AUTHORIZED' || order?.milestone_state === 'AUTHORIZED' || order?.status === 'FUNDS_LOCKED';
  const isAgreed = session?.status === 'AGREEMENT_REACHED' && !order;

  // Single source of truth calculation
  const quantity = order?.quantity || session?.agreement?.final_quantity || session?.agreement?.quantity || mandate?.quantity || 100;
  const unitCap = mandate?.max_unit_price || 32000;
  const budgetCap = mandate?.max_total_budget || unitCap * quantity;
  const settledUnit = order?.unit_price || session?.agreement?.final_unit_price || (isAgreed || isAuthorized || isSettled ? 29850 : unitCap);
  const settledTotal = order?.total_amount || (isAgreed || isAuthorized || isSettled ? Math.round(settledUnit * quantity) : budgetCap);
  const catalogAskUnit = order?.catalog_ask_price ? (order.catalog_ask_price / quantity) : (unitCap >= 10000 ? 33500 : unitCap * 1.08);
  const catalogAskTotal = order?.catalog_ask_price || (catalogAskUnit * quantity);
  
  const negotiatedAlpha = (!session?.agreement && !order)
    ? 0
    : (order?.negotiated_alpha !== undefined 
        ? order.negotiated_alpha 
        : Math.max(0, Math.round((catalogAskUnit - settledUnit) * quantity)));
  const budgetHeadroom = order?.budget_headroom !== undefined 
    ? order.budget_headroom 
    : Math.max(0, budgetCap - settledTotal);

  // Determine stage and narrative
  let stageBadge = {
    text: 'AWAITING EVALUATION',
    color: 'bg-slate-800 text-slate-300 border-slate-700',
    icon: Clock,
  };
  let headline = 'System Initialized · Zero-Key Demo Ready';
  let narrative = `Mandate active for ${quantity}x ${mandate?.item_name || 'Enterprise Hardware'} with a ceiling of $${unitCap.toLocaleString()}/unit (Cap $${budgetCap.toLocaleString()}). Choose '⭐ Evaluate First: Adversarial Surge Trap' or 'Run Autonomous Full Lifecycle' below to test deterministic safety and PayPal two-step milestone captures.`;

  if (isHitlHold) {
    stageBadge = {
      text: 'ADVERSARIAL SURGE DEFLECTED',
      color: 'bg-red-500/20 text-red-300 border-red-500/40 animate-pulse',
      icon: AlertTriangle,
    };
    headline = 'Deterministic PolicyEngine Blocked Unauthorized Price Escalation';
    narrative = `VendorBot injected a +50% price spike ($${((session?.proposals?.slice(-1)[0]?.proposed_unit_price) || (unitCap * 1.5)).toLocaleString()}/unit), attempting to breach the cryptographically sealed $${unitCap.toLocaleString()} ceiling. PolicyEngine circuit breaker tripped instantly without hallucinating: $0.00 unauthorized funds moved. A human supervisor override is required to resume.`;
  } else if (isSettled) {
    stageBadge = {
      text: 'FULL LIFECYCLE SETTLED (100%)',
      color: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
      icon: CheckCircle2,
    };
    headline = 'Autonomous Negotiation & Multi-Stage Capture Completed';
    narrative = `Dual agents closed ${quantity}x units at $${settledUnit.toLocaleString()}/unit (Settled: $${settledTotal.toLocaleString()} vs Budget Cap: $${budgetCap.toLocaleString()}). Secured via PayPal 29-day authorization hold (${order?.paypal_authorization_id || 'AUTH-ID'}), followed by Milestone 2 mobilization partial capture (30%: $${(settledTotal * 0.3).toLocaleString()}) and Milestone 3 delivery final capture (70%: $${(settledTotal * 0.7).toLocaleString()}). Dispute defense grade: A+ Merkle seal.`;
  } else if (isInTransit) {
    stageBadge = {
      text: 'PARTIAL CAPTURE MOBILIZED (30%)',
      color: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40',
      icon: Zap,
    };
    headline = 'Carrier Proof Verified · Milestone 2 Partial Capture Disbursed';
    narrative = `Carrier ${order?.carrier_name || 'FedEx Priority Freight'} tracking #${order?.tracking_number || 'TRK-98214'} verified. PayPal Orders v2 partial capture executed for 30% mobilization ($${(settledTotal * 0.3).toLocaleString()}) with idempotency key '${order?.paypal_request_id_partial || 'REQ-MS2'}'. Remaining 70% ($${(settledTotal * 0.7).toLocaleString()}) stays held under 29-day authorization until final delivery.`;
  } else if (isAuthorized) {
    stageBadge = {
      text: '29-DAY AUTHORIZATION HOLD (100%)',
      color: 'bg-blue-500/20 text-blue-300 border-blue-500/40',
      icon: Lock,
    };
    headline = '100% Funds Held via PayPal Orders v2 · 0% Disbursed Prematurely';
    narrative = `Dual-agent consensus reached at $${settledUnit.toLocaleString()}/unit. PolicyEngine placed a 100% authorization hold of $${settledTotal.toLocaleString()} (PayPal Auth ID: ${order?.paypal_authorization_id || 'AUTH-SECURED'}). Buyer capital is locked for up to 29 days with zero funds released until verifiable carrier tracking proof is ingested.`;
  } else if (isAgreed) {
    stageBadge = {
      text: 'DUAL-AGENT CONSENSUS CERTIFIED',
      color: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/40',
      icon: FileCheck,
    };
    headline = 'ProcureBot & VendorBot Converged on Verified Terms';
    narrative = `Autonomous negotiation converged at $${settledUnit.toLocaleString()}/unit across ${session?.current_round || 3} bidding rounds. Canonical HMAC-SHA256 digest ${session?.agreement?.agreement_hash?.slice(0, 16)}... sealed. Ready to trigger Milestone 1 29-Day PayPal Authorization Hold.`;
  }

  const BadgeIcon = stageBadge.icon;

  return (
    <div className="rounded-2xl border border-indigo-500/30 bg-gradient-to-r from-[#0f172a] via-[#111827] to-[#0f172a] p-4 sm:p-5 shadow-xl relative overflow-hidden">
      {/* Decorative background glow */}
      <div className="absolute -right-16 -top-16 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -left-16 -bottom-16 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Main Bar Content */}
      <div className="relative z-10">
        <div className="flex flex-wrap items-center justify-between gap-3 pb-2 border-b border-slate-800/80">
          <div className="flex items-center space-x-2.5">
            <div className="px-2.5 py-1 rounded-md bg-gradient-to-r from-blue-600/30 to-indigo-600/30 border border-blue-500/40 text-cyan-300 text-[11px] font-extrabold uppercase tracking-wider flex items-center space-x-1.5 shadow-sm">
              <Zap className="w-3.5 h-3.5 text-cyan-400" />
              <span>30-Second Executive Debrief</span>
            </div>
            <span className={`px-2.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border flex items-center space-x-1 ${stageBadge.color}`}>
              <BadgeIcon className="w-3 h-3" />
              <span>{stageBadge.text}</span>
            </span>
          </div>

          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-slate-400 hover:text-white text-xs font-medium flex items-center space-x-1 transition-colors"
          >
            <span>{isExpanded ? 'Less Context' : 'Explain Architecture'}</span>
            {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>

        {/* Dynamic Headline & Narrative */}
        <div className="mt-3">
          <h3 className="text-sm sm:text-base font-bold text-white tracking-tight flex items-center space-x-2">
            <span>{headline}</span>
          </h3>
          <p className="mt-1 text-xs sm:text-sm text-slate-300 leading-relaxed font-normal">
            {narrative}
          </p>
        </div>

        {/* Key Invariant Metric Chips */}
        <div className="mt-3.5 grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
          <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-2.5">
            <span className="text-[10px] uppercase font-bold text-slate-400 block">Single Source Math</span>
            <div className="font-mono font-bold text-slate-100 text-[11px] sm:text-[12px] whitespace-normal break-words mt-0.5">
              {quantity} × ${settledUnit.toLocaleString()} = <span className="text-cyan-400 font-extrabold">${settledTotal.toLocaleString()}</span>
            </div>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-2">
            <span className="text-[10px] uppercase font-bold text-emerald-400 block">Budget Headroom</span>
            <div className="font-mono font-bold text-emerald-300 text-[12px] truncate">
              ${budgetHeadroom.toLocaleString()} <span className="text-[10px] text-slate-400">vs Cap</span>
            </div>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-2">
            <span className="text-[10px] uppercase font-bold text-cyan-400 block">Negotiated Alpha</span>
            <div className="font-mono font-bold text-cyan-300 text-[12px] truncate">
              ${negotiatedAlpha.toLocaleString()} <span className="text-[10px] text-slate-400">vs Ask</span>
            </div>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-2">
            <span className="text-[10px] uppercase font-bold text-indigo-400 block">PayPal Multi-Stage</span>
            <div className="font-mono font-bold text-indigo-300 text-[12px] truncate">
              {isSettled ? '100% Captured (30/70)' : isInTransit ? '30% Partial Captured' : isAuthorized ? '29-Day Hold (100%)' : 'Pre-Authorization'}
            </div>
          </div>
        </div>

        {/* Architecture Details Dropdown */}
        {isExpanded && (
          <div className="mt-3.5 pt-3 border-t border-slate-800/80 text-xs text-slate-400 space-y-2 animate-fade-in">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="p-2.5 rounded-lg bg-slate-900/50 border border-slate-800">
                <span className="font-semibold text-slate-200 block text-[11px] mb-1">1. LLM Proposes, Code Decides</span>
                <p className="text-[11px] text-slate-400 leading-normal">
                  Agents formulate RFQs and discount curves, but the Python PolicyEngine validates all parameters deterministically. LLMs cannot authorize payments or alter price ceilings.
                </p>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-900/50 border border-slate-800">
                <span className="font-semibold text-slate-200 block text-[11px] mb-1">2. PayPal REST API v2 Multi-Stage</span>
                <p className="text-[11px] text-slate-400 leading-normal">
                  Replaces traditional escrow with PayPal's native 29-day authorization hold and idempotent partial captures (30% mobilization, 70% delivery) with visible <code className="text-cyan-300">PayPal-Request-Id</code>.
                </p>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-900/50 border border-slate-800">
                <span className="font-semibold text-slate-200 block text-[11px] mb-1">3. Merkle Evidence Bundle Diff</span>
                <p className="text-[11px] text-slate-400 leading-normal">
                  All mandate constraints, agreed counter-offers, carrier scans, and capture receipts are hashed into a tamper-evident Merkle root with an explicit Mandate-vs-Agreement invariant diff.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

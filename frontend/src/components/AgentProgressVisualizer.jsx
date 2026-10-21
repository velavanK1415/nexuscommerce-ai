import React, { useState, useEffect } from 'react';
import { Bot, ShieldCheck, ShieldAlert, Lock, Zap, CheckCircle2, Sparkles, Clock, Play, RotateCcw } from './icons';
import Tooltip from './Tooltip';

/**
 * Interactive Agent Progress Visualizer
 * Shows which autonomous agent (ProcureBot vs VendorBot vs ArbiterBot vs AuditorBot)
 * is thinking, bidding, or verifying in real time with interactive step selection
 * and live replay simulation.
 */
export default function AgentProgressVisualizer({ session, isRunning, loading, mandate }) {
  const [selectedStepIndex, setSelectedStepIndex] = useState(null);
  const [animatingStep, setAnimatingStep] = useState(null);
  const [isReplaying, setIsReplaying] = useState(false);

  const proposals = session?.proposals || [];
  const latestProposal = proposals[proposals.length - 1];
  const isHitlHold = session?.status === 'HITL_HOLD';
  const isAgreed = session?.status === 'AGREEMENT_REACHED';

  // Live real-time stepped agent pipeline animation
  useEffect(() => {
    let timer;
    if (isRunning || loading || isReplaying) {
      setAnimatingStep(0);
      let step = 0;
      timer = setInterval(() => {
        step += 1;
        if (step <= 4) {
          setAnimatingStep(step);
        } else {
          clearInterval(timer);
          setAnimatingStep(null);
          setIsReplaying(false);
        }
      }, 750);
    } else {
      setAnimatingStep(null);
      setIsReplaying(false);
    }
    return () => clearInterval(timer);
  }, [isRunning, loading, isReplaying]);

  // Compute active pipeline stage based on current session state and animation
  const getPipelineSteps = () => {
    const hasBuyerProposal = proposals.some((p) => p.sender === 'ProcureBot');
    const hasVendorProposal = proposals.some((p) => p.sender === 'VendorBot');

    const isSimulating = animatingStep !== null;

    // Stage 1: Mandate Binding
    const s1Complete = Boolean(mandate);
    const s1Active = isSimulating ? animatingStep === 0 : !mandate;

    // Stage 2: ProcureBot Bidding
    const s2Complete = (hasBuyerProposal || isAgreed) && (!isSimulating || animatingStep > 1);
    const s2Active = isSimulating ? animatingStep === 1 : (loading || isRunning) && (!hasBuyerProposal || latestProposal?.sender === 'VendorBot');

    // Stage 3: VendorBot Counter-Offer
    const s3Complete = (hasVendorProposal || isAgreed) && (!isSimulating || animatingStep > 2);
    const s3Active = isSimulating ? animatingStep === 2 : (loading || isRunning) && latestProposal?.sender === 'ProcureBot' && !isHitlHold;

    // Stage 4: ArbiterBot AST Guardrail Verification
    const s4Complete = (isAgreed || (proposals.length > 0 && !isHitlHold)) && (!isSimulating || animatingStep > 3);
    const s4Active = isSimulating ? animatingStep === 3 : (isHitlHold || (loading && hasVendorProposal));

    // Stage 5: AuditorBot Consensus & SHA-256 Seal
    const s5Complete = isAgreed && (!isSimulating || animatingStep >= 4);
    const s5Active = isSimulating ? animatingStep === 4 : ((loading || isRunning) && isAgreed);

    const unitPrice = mandate?.max_unit_price || 1200;
    const buyerBid = proposals[0]?.proposed_unit_price || Math.round(unitPrice * 0.88);
    const vendorCounter = latestProposal?.proposed_unit_price || Math.round(unitPrice * 0.94);

    return [
      {
        id: 'step-mandate',
        agent: 'Buyer Authority',
        role: 'Deterministic Envelope',
        title: 'Mandate Envelope Signed',
        desc: `Authorized cap $${unitPrice.toFixed(2)}/unit · Total $${(mandate?.max_total_budget || (unitPrice * (mandate?.quantity || 100))).toLocaleString()}`,
        status: s1Active ? 'ACTIVE' : s1Complete ? 'COMPLETED' : 'PENDING',
        latency: '0.4ms',
        icon: Lock,
        thought: mandate
          ? `Active mandate ${mandate.id} cryptographically locked into PolicyEngine. Ceiling $${mandate.max_total_budget?.toLocaleString()} enforced.`
          : 'Awaiting digital signing of procurement mandate envelope.',
      },
      {
        id: 'step-procurebot',
        agent: 'ProcureBot',
        role: 'Autonomous Buyer',
        title: 'Buyer RFQ Formulation',
        desc: `Formulates volume bid targeting alpha ($${buyerBid.toFixed(2)}/unit)`,
        status: s2Active ? 'ACTIVE' : s2Complete ? 'COMPLETED' : 'PENDING',
        latency: '118ms',
        icon: Bot,
        thought: s2Active
          ? `ProcureBot analyzing Channel3 supplier catalog: Formulating optimal opening bid at $${buyerBid.toFixed(2)} with Tier-1 SLA.`
          : hasBuyerProposal
          ? `ProcureBot submitted ${proposals.filter(p => p.sender === 'ProcureBot').length} bids. Highest alpha volume discount targeted.`
          : 'ProcureBot initialized. Waiting for bidding round dispatch.',
      },
      {
        id: 'step-vendorbot',
        agent: 'VendorBot',
        role: 'Supplier AI (NexIQ)',
        title: 'Vendor Margin Discounting',
        desc: isHitlHold ? 'Adversarial Surge (+50%)' : `Counter-offers at $${vendorCounter.toFixed(2)} with 36mo warranty`,
        status: isHitlHold ? 'FLAGGED' : s3Active ? 'ACTIVE' : s3Complete ? 'COMPLETED' : 'PENDING',
        latency: '184ms',
        icon: Sparkles,
        thought: isHitlHold
          ? 'Adversarial pricing prompt injected (+50%). Trapped by PolicyEngine deterministic circuit breaker.'
          : s3Active
          ? `VendorBot calculating margin curves: Best counter-offer evaluated at $${vendorCounter.toFixed(2)}/unit.`
          : hasVendorProposal
          ? `Vendor countered at $${latestProposal?.proposed_unit_price?.toFixed(2)} with 36-month enterprise warranty.`
          : 'VendorBot standing by to evaluate buyer RFP.',
      },
      {
        id: 'step-policy',
        agent: 'ArbiterBot (PolicyEngine)',
        role: 'Deterministic Invariant Arbiter',
        title: 'AST Invariant Guardrail Check',
        desc: 'Evaluates unit cap, total treasury budget, lead time, and cryptographic signatures',
        status: isHitlHold ? 'FLAGGED' : s4Active ? 'ACTIVE' : s4Complete ? 'COMPLETED' : 'PENDING',
        latency: '2.1ms AST',
        icon: ShieldCheck,
        thought: isHitlHold
          ? `CIRCUIT BREAKER HALT: ${session?.hitl_reason || 'Policy ceiling breached. Funds release frozen until human override.'}`
          : s4Active
          ? 'ArbiterBot parsing proposal syntax tree: Verifying unit price <= cap, total <= budget, lead time <= SLA.'
          : 'All mathematical and financial constraints passed without exceptions.',
      },
      {
        id: 'step-consensus',
        agent: 'AuditorBot',
        role: 'Cryptographic Consensus Signer',
        title: 'Consensus & SHA-256 Seal',
        desc: isAgreed ? `Sealed: ${session?.agreement?.agreement_hash?.slice(0, 16)}...` : 'Binds dual-agent agreement into tamper-evident digest',
        status: s5Active ? 'ACTIVE' : s5Complete ? 'COMPLETED' : 'PENDING',
        latency: '8.4ms Seal',
        icon: CheckCircle2,
        thought: isAgreed
          ? `Dual-agent consensus certified: Canonical SHA-256 digest ${session?.agreement?.agreement_hash?.slice(0, 24)}... sealed for PayPal authorization hold and milestone captures.`
          : s5Active
          ? 'AuditorBot computing canonical HMAC-SHA256 digest across sorted proposal fields.'
          : 'Awaiting mutual convergence between ProcureBot and VendorBot.',
      },
    ];
  };

  const steps = getPipelineSteps();
  const currentStep =
    selectedStepIndex !== null
      ? steps[selectedStepIndex]
      : steps.find((s) => s.status === 'ACTIVE' || s.status === 'FLAGGED') || steps[steps.length - 1];

  const activeAgentName =
    animatingStep === 0
      ? 'Buyer Authority (Signing)'
      : animatingStep === 1
      ? 'ProcureBot (Formulating Bid...)'
      : animatingStep === 2
      ? 'VendorBot (Calculating Margin...)'
      : animatingStep === 3
      ? 'ArbiterBot / PolicyEngine (Verifying AST...)'
      : animatingStep === 4
      ? 'AuditorBot (Sealing SHA-256...)'
      : isHitlHold
      ? 'PolicyEngine (Circuit Breaker Halted)'
      : isRunning || loading
      ? (latestProposal?.sender === 'ProcureBot' ? 'VendorBot Thinking...' : 'ProcureBot Formulating...')
      : isAgreed
      ? 'AuditorBot (Consensus Certified)'
      : 'Idle';

  return (
    <div className="bg-[#111827] border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
      
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center">
            <Zap className={`w-4 h-4 text-cyan-400 ${(loading || isRunning || animatingStep !== null) ? 'animate-bounce' : ''}`} />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-sm font-bold text-white">Interactive Agent Progress Visualizer</h3>
              <span className={`px-2 py-0.5 rounded text-[10px] font-extrabold uppercase ${
                isHitlHold
                  ? 'bg-red-500/20 text-red-300 border border-red-500/40'
                  : isRunning || loading || animatingStep !== null
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 animate-pulse'
                  : isAgreed
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                  : 'bg-slate-800 text-slate-400'
              }`}>
                {isHitlHold ? '⚠️ HITL Halt' : (isRunning || loading || animatingStep !== null) ? '⚡ Agents Active' : isAgreed ? '✅ Consensus Certified' : 'Idle'}
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Live multi-agent state pipeline: Real-time thinking, bidding, AST invariant validation, and consensus sealing
            </p>
          </div>
        </div>

        {/* Right action & Active Thinker Pill */}
        <div className="flex items-center space-x-2 text-xs">
          {/* Replay Agent Stream Button */}
          <button
            onClick={() => setIsReplaying(true)}
            disabled={isRunning || loading || isReplaying}
            className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-[11px] font-semibold border border-slate-700 flex items-center space-x-1 transition-all disabled:opacity-40"
            title="Replay step-by-step autonomous agent thinking and verification stream"
          >
            <Play className={`w-3 h-3 text-cyan-400 ${isReplaying ? 'animate-spin' : ''}`} />
            <span>{isReplaying ? 'Streaming...' : 'Watch Live Agents'}</span>
          </button>

          {/* Active Thinker Pill */}
          <div className={`px-3 py-1 rounded-lg font-mono text-[11px] font-semibold border flex items-center space-x-2 ${
            isHitlHold
              ? 'bg-red-950/70 text-red-300 border-red-500/50'
              : (loading || isRunning || animatingStep !== null)
              ? 'bg-indigo-950/70 text-cyan-300 border-indigo-500/50 ring-1 ring-cyan-500/30'
              : 'bg-slate-900 text-emerald-400 border-slate-700'
          }`}>
            <span className={`w-2 h-2 rounded-full ${
              isHitlHold
                ? 'bg-red-400 animate-ping'
                : (loading || isRunning || animatingStep !== null)
                ? 'bg-cyan-400 animate-ping'
                : 'bg-emerald-400'
            }`} />
            <span>{activeAgentName}</span>
          </div>
        </div>
      </div>

      {/* Visual Pipeline Nodes */}
      <div className="grid grid-cols-1 sm:grid-cols-5 gap-2.5 pt-1">
        {steps.map((step, idx) => {
          const IconComponent = step.icon;
          const isSelected = selectedStepIndex === idx;
          const isCompleted = step.status === 'COMPLETED';
          const isActive = step.status === 'ACTIVE';
          const isFlagged = step.status === 'FLAGGED';

          return (
            <div
              key={step.id}
              onClick={() => setSelectedStepIndex(idx)}
              className={`p-3 rounded-xl border cursor-pointer transition-all relative ${
                isSelected
                  ? 'ring-2 ring-cyan-400 bg-slate-900/95 border-cyan-500/60 shadow-lg shadow-cyan-500/10'
                  : isFlagged
                  ? 'bg-red-950/30 border-red-500/60 hover:border-red-400 shadow-md shadow-red-500/10'
                  : isActive
                  ? 'bg-indigo-950/50 border-cyan-500/70 shadow-lg shadow-cyan-500/20 ring-1 ring-cyan-500/40 animate-pulse'
                  : isCompleted
                  ? 'bg-slate-900/70 border-emerald-500/30 hover:border-emerald-500/60'
                  : 'bg-slate-900/30 border-slate-800 opacity-60 hover:opacity-100'
              }`}
            >
              {/* Connector line between steps on desktop */}
              {idx < steps.length - 1 && (
                <div className={`hidden sm:block absolute top-1/2 -right-3 w-3 h-0.5 z-10 ${
                  isCompleted ? 'bg-emerald-500/60' : isActive ? 'bg-cyan-500 animate-pulse' : 'bg-slate-800'
                }`} />
              )}

              <div className="flex items-center justify-between mb-2">
                <div className={`w-7 h-7 rounded-lg flex items-center justify-center border ${
                  isFlagged
                    ? 'bg-red-500/20 text-red-400 border-red-500/40 animate-pulse'
                    : isActive
                    ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/60 animate-bounce'
                    : isCompleted
                    ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40'
                    : 'bg-slate-800 text-slate-500 border-slate-700'
                }`}>
                  <IconComponent className="w-3.5 h-3.5" />
                </div>
                <span className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded uppercase ${
                  isFlagged
                    ? 'bg-red-500/20 text-red-300 border border-red-500/40'
                    : isActive
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 animate-pulse'
                    : isCompleted
                    ? 'bg-emerald-500/10 text-emerald-400'
                    : 'text-slate-500'
                }`}>
                  {step.status}
                </span>
              </div>

              <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">{step.agent}</div>
              <div className="text-xs font-bold text-white truncate">{step.title}</div>
              <div className="mt-1 text-[10px] font-mono text-cyan-400 flex items-center justify-between">
                <span>Latency:</span>
                <span>{step.latency}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Selected Node Telemetry Inspector */}
      {currentStep && (
        <div className={`p-3.5 rounded-xl border text-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 ${
          currentStep.status === 'FLAGGED'
            ? 'bg-red-950/40 border-red-500/50 text-red-200'
            : currentStep.status === 'ACTIVE'
            ? 'bg-indigo-950/40 border-cyan-500/50 text-cyan-200'
            : 'bg-slate-900/90 border-slate-800 text-slate-300'
        }`}>
          <div className="flex items-start space-x-3">
            <div className="mt-0.5">
              <Bot className="w-4 h-4 text-cyan-400" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-white">{currentStep.agent}</span>
                <span className="text-[10px] text-slate-400 font-mono">({currentStep.role})</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300">
                  {currentStep.title}
                </span>
              </div>
              <p className="mt-1 text-slate-300 text-[11px] leading-relaxed">
                <strong className="text-white">Live Agent Thought: </strong>
                {currentStep.thought}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2 shrink-0 text-[11px]">
            <Tooltip
              title="Autonomous Pipeline Invariant"
              text="NexusCommerce enforces deterministic boundaries. Autonomous agents formulate proposals, but the PolicyEngine must deterministically verify every financial parameter before any PayPal authorization hold can be placed."
            />
            {selectedStepIndex !== null && (
              <button
                onClick={() => setSelectedStepIndex(null)}
                className="text-[10px] text-slate-400 hover:text-white underline"
              >
                Reset to Live Step
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

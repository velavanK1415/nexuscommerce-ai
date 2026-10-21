import React, { useState } from 'react';
import { 
  CheckCircle2, 
  Circle, 
  Clock, 
  Truck, 
  Lock, 
  DollarSign, 
  ArrowRight, 
  ShieldCheck, 
  ExternalLink,
  Radio,
  FileCheck2,
  Sparkles,
  RotateCcw
} from './icons';
import Tooltip from './Tooltip';

export default function MilestoneTimeline({ 
  order, 
  onAdvanceShipment, 
  onAdvanceDelivery, 
  onSimulateWebhook,
  loading,
  onStartStepByStepMilestones 
}) {
  const [carrierName, setCarrierName] = useState('FedEx Priority Freight');
  const [trackingNumber, setTrackingNumber] = useState('');
  const [activeWebhook, setActiveWebhook] = useState('CHECKOUT.ORDER.APPROVED');

  if (!order) {
    return (
      <div className="bg-[#111827] border border-blue-500/30 rounded-2xl p-6 sm:p-8 text-center space-y-4 shadow-xl">
        <div className="w-12 h-12 mx-auto rounded-xl bg-blue-500/20 border border-blue-500/40 flex items-center justify-center">
          <Lock className="w-6 h-6 text-cyan-400" />
        </div>
        <div>
          <h3 className="text-base font-bold text-white mb-1">
            PayPal 3-Milestone Two-Step Settlement Timeline
          </h3>
          <p className="text-xs text-slate-300 max-w-lg mx-auto leading-relaxed">
            PayPal Orders v2 requires placing a 29-day authorization hold (Milestone 1) before Milestone 2 (Carrier Proof) and Milestone 3 (Delivery Release) can be unlocked.
          </p>
        </div>

        <div className="pt-1">
          <button
            onClick={onStartStepByStepMilestones}
            disabled={loading}
            className="px-6 py-3 rounded-xl bg-gradient-to-r from-amber-500 via-cyan-500 to-blue-600 hover:from-amber-400 hover:to-blue-500 text-slate-950 font-extrabold text-xs shadow-lg shadow-cyan-500/20 flex items-center space-x-2 mx-auto transition-all transform hover:scale-[1.02] disabled:opacity-50"
          >
            <Sparkles className="w-4 h-4 text-slate-950" />
            <span>⚡ Unlock & Test Milestone 2 & Milestone 3 Buttons Now</span>
          </button>
        </div>

        <div className="flex flex-wrap items-center justify-center gap-3 text-[11px] text-slate-400 font-mono pt-1">
          <span className="text-blue-300 font-bold">• Step 1: Pre-Auth Hold (100%)</span>
          <span className="text-amber-300 font-bold">• Step 2: 30% Partial on Dispatch</span>
          <span className="text-emerald-300 font-bold">• Step 3: 70% Final on Delivery</span>
        </div>
      </div>
    );
  }

  const milestones = order.milestones || [];
  const ms1 = milestones[0] || {};
  const ms2 = milestones[1] || {};
  const ms3 = milestones[2] || {};

  const round = (val) => Math.round(val * 100) / 100;
  const totalAmount = order.total_amount || 2985000.0;
  const partialAmount = ms2.allocated_amount || round(totalAmount * 0.30);
  const finalAmount = ms3.allocated_amount || round(totalAmount - partialAmount);

  const partialCaptureId = order.paypal_partial_capture_id || (ms2.paypal_reference_id && ms2.paypal_reference_id.startsWith('CAP') ? ms2.paypal_reference_id : null);
  const partialRequestId = order.paypal_request_id_partial || ms2.paypal_request_id || `REQ-MS2-${order.order_id}`;
  const finalCaptureId = order.paypal_capture_id || (ms3.paypal_reference_id && ms3.paypal_reference_id.startsWith('CAP') ? ms3.paypal_reference_id : null);
  const finalRequestId = order.paypal_request_id_final || ms3.paypal_request_id || `REQ-MS3-${order.order_id}`;

  return (
    <div className="bg-[#111827] border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
      
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xs font-mono text-cyan-400 font-bold">{order.order_id}</span>
            <span className="px-2 py-0.5 rounded text-[10px] font-extrabold uppercase bg-indigo-500/10 text-indigo-300 border border-indigo-500/30">
              {order.status}
            </span>
            <Tooltip
              title="Two-Step Authorization & Milestone State Machine"
              text="Tracks real-time transitions under PayPal Orders v2 authorization. Intent: AUTHORIZE reserves buyer funds for 29 days. Milestone 2 releases a 30% mobilization partial capture, and Milestone 3 releases the remaining 70% upon delivery verification."
            />
          </div>
          <h3 className="text-base font-bold text-white mt-1">
            PayPal Two-Step Authorization & Milestone Captures
          </h3>
          <p className="text-[11px] text-slate-400">
            Secured under PayPal REST API v2 Orders Authorization Hold (29-day window) · Intent: AUTHORIZE
          </p>
        </div>

        {/* PayPal Credentials & Tracking Pills with Idempotency Detail */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          {order.paypal_authorization_id && (
            <div className="px-3 py-1 rounded-lg bg-blue-950/40 border border-blue-500/30 text-blue-300 flex items-center space-x-1.5 font-mono">
              <Lock className="w-3 h-3 text-cyan-400" />
              <span>Auth: {order.paypal_authorization_id}</span>
              <Tooltip
                title="PayPal 29-Day Authorization Hold"
                text="Funds are held by PayPal with intent=AUTHORIZE. Valid for 29 days. Can be captured partially (e.g. 30% on dispatch) and finally (70% on delivery)."
              />
            </div>
          )}
          {order.tracking_number && (
            <div className="px-3 py-1 rounded-lg bg-amber-950/40 border border-amber-500/30 text-amber-300 flex items-center space-x-1.5 font-mono">
              <Truck className="w-3 h-3 text-amber-400" />
              <span>{order.carrier_name}: {order.tracking_number}</span>
            </div>
          )}
          {partialCaptureId && (
            <div className="px-3 py-1 rounded-lg bg-cyan-950/40 border border-cyan-500/30 text-cyan-300 flex items-center space-x-1.5 font-mono">
              <DollarSign className="w-3 h-3 text-cyan-400" />
              <span>Partial #1: {partialCaptureId}</span>
            </div>
          )}
          {finalCaptureId && (
            <div className="px-3 py-1 rounded-lg bg-emerald-950/40 border border-emerald-500/30 text-emerald-300 flex items-center space-x-1.5 font-mono">
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
              <span>Final #2: {finalCaptureId}</span>
            </div>
          )}

          {order.status === 'COMPLETED' && onStartStepByStepMilestones && (
            <button
              onClick={onStartStepByStepMilestones}
              disabled={loading}
              className="px-3 py-1 rounded-lg bg-indigo-600/30 hover:bg-indigo-600/50 border border-indigo-500/50 text-indigo-300 hover:text-white flex items-center space-x-1.5 transition-all text-xs font-semibold"
              title="Reset order to Milestone 2 to demonstrate manual carrier dispatch click again"
            >
              <RotateCcw className="w-3 h-3 text-indigo-400" />
              <span>Re-Arm Milestones for Demo Video</span>
            </button>
          )}
        </div>
      </div>

      {/* Visual Timeline Steps: 3-Milestone Two-Step Authorization Model */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        
        {/* Step 1: 100% Authorization Hold */}
        <div className={`p-4 rounded-xl border relative transition-all ${
          ms1.status === 'COMPLETED'
            ? 'bg-slate-900/90 border-emerald-500/40'
            : ms1.status === 'IN_PROGRESS'
            ? 'bg-slate-900/90 border-blue-500/40 ring-1 ring-blue-500/30'
            : 'bg-slate-900/40 border-slate-800 opacity-60'
        }`}>
          <div className="flex items-center justify-between mb-3">
            <span className="w-7 h-7 rounded-lg bg-indigo-500/20 text-indigo-400 border border-indigo-500/40 text-xs font-bold flex items-center justify-center">
              1
            </span>
            <span className={`text-[10px] font-extrabold uppercase px-2 py-0.5 rounded ${
              ms1.status === 'COMPLETED'
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                : 'bg-blue-500/20 text-blue-300'
            }`}>
              {ms1.status === 'COMPLETED' ? 'HOLD ACTIVE' : ms1.status}
            </span>
          </div>
          <h4 className="text-xs font-bold text-white mb-1">29-Day Authorization Hold (100%)</h4>
          <p className="text-[11px] text-slate-400 mb-3 leading-relaxed">
            Buyer authorizes full deal amount (${totalAmount.toLocaleString()}) with intent: AUTHORIZE under PayPal Orders v2. Held securely for up to 29 days.
          </p>
          <div className="space-y-1 pt-2 border-t border-slate-800 text-[10px] text-slate-400 font-mono">
            <div>Auth Ref: <span className="text-cyan-300">{order.paypal_authorization_id || 'Generating...'}</span></div>
            <div>Held Amount: <span className="text-white font-bold">${totalAmount.toLocaleString()} USD</span></div>
            <div>Hold Window: <span className="text-emerald-400">29 Days Active</span></div>
          </div>
        </div>

        {/* Step 2: Carrier Proof & 30% Mobilization Partial Capture */}
        <div className={`p-4 rounded-xl border relative transition-all ${
          ms2.status === 'COMPLETED'
            ? 'bg-slate-900/90 border-emerald-500/40'
            : ms2.status === 'IN_PROGRESS'
            ? 'bg-slate-900/90 border-amber-500/50 ring-1 ring-amber-500/30'
            : 'bg-slate-900/40 border-slate-800 opacity-60'
        }`}>
          <div className="flex items-center justify-between mb-3">
            <span className="w-7 h-7 rounded-lg bg-amber-500/20 text-amber-400 border border-amber-500/40 text-xs font-bold flex items-center justify-center">
              2
            </span>
            <span className={`text-[10px] font-extrabold uppercase px-2 py-0.5 rounded ${
              ms2.status === 'COMPLETED'
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                : ms2.status === 'IN_PROGRESS'
                ? 'bg-amber-500/20 text-amber-300'
                : 'bg-slate-800 text-slate-500'
            }`}>
              {ms2.status === 'COMPLETED' ? '30% CAPTURED' : ms2.status}
            </span>
          </div>
          <h4 className="text-xs font-bold text-white mb-1">Carrier Proof & 30% Partial Capture</h4>
          <p className="text-[11px] text-slate-400 mb-3 leading-relaxed">
            Vendor dispatches hardware; verifiable carrier origin scan unlocks partial capture #1 (30% mobilization = ${partialAmount.toLocaleString()}) with is_final_capture: false.
          </p>

          {ms2.status === 'IN_PROGRESS' && (
            <div className="space-y-2 pt-2 border-t border-slate-800">
              <input
                type="text"
                placeholder="Optional custom tracking #"
                value={trackingNumber}
                onChange={(e) => setTrackingNumber(e.target.value)}
                className="w-full px-2 py-1 text-[11px] bg-slate-950 border border-slate-700 rounded text-white"
              />
              <button
                onClick={() => onAdvanceShipment(carrierName, trackingNumber || null)}
                disabled={loading}
                className="w-full py-2 rounded-lg bg-amber-600 hover:bg-amber-500 text-slate-950 font-bold text-[11px] flex items-center justify-center space-x-1 transition-all"
              >
                <Truck className="w-3.5 h-3.5" />
                <span>Submit Carrier Scan & Release 30% (${partialAmount.toLocaleString()})</span>
              </button>
            </div>
          )}

          {ms2.status === 'COMPLETED' && (
            <div className="space-y-1 pt-2 border-t border-slate-800 text-[10px] font-mono">
              <div className="text-emerald-400 font-bold">Disbursed: ${partialAmount.toLocaleString()} USD (30%)</div>
              <div className="text-slate-400">Tracking: {order.tracking_number}</div>
              <div className="text-cyan-300 truncate" title={partialRequestId}>
                PayPal-Request-Id: <span className="text-amber-300">{partialRequestId.slice(0, 18)}...</span>
              </div>
              <div className="text-[9px] text-slate-500">API Parameter: is_final_capture = false</div>
            </div>
          )}
        </div>

        {/* Step 3: Delivery Verification & Final 70% Capture */}
        <div className={`p-4 rounded-xl border relative transition-all ${
          ms3.status === 'COMPLETED'
            ? 'bg-slate-900/90 border-emerald-500/40'
            : ms3.status === 'IN_PROGRESS'
            ? 'bg-slate-900/90 border-cyan-500/50 ring-1 ring-cyan-500/30'
            : 'bg-slate-900/40 border-slate-800 opacity-60'
        }`}>
          <div className="flex items-center justify-between mb-3">
            <span className="w-7 h-7 rounded-lg bg-cyan-500/20 text-cyan-400 border border-cyan-500/40 text-xs font-bold flex items-center justify-center">
              3
            </span>
            <span className={`text-[10px] font-extrabold uppercase px-2 py-0.5 rounded ${
              ms3.status === 'COMPLETED'
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                : ms3.status === 'IN_PROGRESS'
                ? 'bg-cyan-500/20 text-cyan-300'
                : 'bg-slate-800 text-slate-500'
            }`}>
              {ms3.status === 'COMPLETED' ? '70% SETTLED' : ms3.status}
            </span>
          </div>
          <h4 className="text-xs font-bold text-white mb-1">Delivery Acceptance & Final 70% Capture</h4>
          <p className="text-[11px] text-slate-400 mb-3 leading-relaxed">
            Carrier confirms delivery scan or buyer signs acceptance; PolicyEngine executes final capture #2 (remaining 70% = ${finalAmount.toLocaleString()}) with is_final_capture: true.
          </p>

          {ms3.status === 'IN_PROGRESS' && (
            <button
              onClick={onAdvanceDelivery}
              disabled={loading}
              className="w-full py-2.5 rounded-lg bg-gradient-to-r from-emerald-600 to-cyan-600 hover:from-emerald-500 hover:to-cyan-500 text-white font-bold text-xs shadow-md shadow-emerald-600/30 flex items-center justify-center space-x-1.5 transition-all"
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Verify Delivery & Release Final 70% (${finalAmount.toLocaleString()})</span>
            </button>
          )}

          {ms3.status === 'COMPLETED' && (
            <div className="space-y-1 pt-2 border-t border-slate-800 text-[10px] font-mono">
              <div className="text-emerald-400 font-bold">Disbursed: ${finalAmount.toLocaleString()} USD (70%)</div>
              <div className="text-slate-400">Total Settled: ${totalAmount.toLocaleString()} (100%)</div>
              <div className="text-cyan-300 truncate" title={finalRequestId}>
                PayPal-Request-Id: <span className="text-amber-300">{finalRequestId.slice(0, 18)}...</span>
              </div>
              <div className="text-[9px] text-slate-500">API Parameter: is_final_capture = true (Deal Complete)</div>
            </div>
          )}
        </div>
      </div>

      {/* Interactive Webhook Event Simulator */}
      <div className="p-4 rounded-xl bg-slate-900/80 border border-amber-500/30 shadow-md shadow-amber-500/5 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-extrabold uppercase bg-amber-500/20 text-amber-300 border border-amber-500/40">
              SIMULATOR TOOL
            </span>
            <Radio className="w-4 h-4 text-cyan-400 animate-pulse" />
            <span className="font-bold text-slate-100">
              Interactive Webhook Event Simulator (Judge Audit Harness)
            </span>
          </div>
          <p className="text-[11px] text-slate-400">
            <strong className="text-slate-300">Guide for Judges:</strong> Dispatches real PayPal Orders v2 webhook payloads directly into the backend receiver to deterministically audit state transitions, idempotency checks, and multi-stage captures.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <select
            value={activeWebhook}
            onChange={(e) => setActiveWebhook(e.target.value)}
            className="px-2.5 py-1.5 text-xs bg-slate-950 border border-slate-700 rounded-lg text-white font-mono"
          >
            <option value="CHECKOUT.ORDER.APPROVED">CHECKOUT.ORDER.APPROVED</option>
            <option value="PAYMENT.AUTHORIZATION.CREATED">PAYMENT.AUTHORIZATION.CREATED</option>
            <option value="PAYMENT.CAPTURE.COMPLETED">PAYMENT.CAPTURE.COMPLETED</option>
          </select>

          <button
            onClick={() => onSimulateWebhook(activeWebhook, order.order_id)}
            disabled={loading}
            className="px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs transition-all shadow-sm shadow-blue-500/20"
          >
            Dispatch Event
          </button>
        </div>
      </div>

    </div>
  );
}

import React, { useState, useEffect } from 'react';
import { ShieldAlert, ShieldCheck, AlertTriangle, CheckCircle2, DollarSign, Truck, Lock, X } from './icons';

/**
 * Proactive Visual Alert System
 * Displays prominent status banners and dismissible toast alerts for:
 * 1. Adversarial surge price detection
 * 2. Deterministic policy violations
 * 3. Milestone escrow locks and release captures
 */
export default function AlertBannerSystem({ session, order, bundle, toasts = [], onDismissToast }) {
  const isHitlHold = session?.status === 'HITL_HOLD';
  const isAgreed = session?.status === 'AGREEMENT_REACHED';
  const isCaptured = order?.status === 'COMPLETED';
  const isInTransit = order?.status === 'IN_TRANSIT';
  const isFundsAuthorized = order?.status === 'FUNDS_AUTHORIZED';
  const isTamperDetected = bundle && bundle.tamper_evident_valid === false;

  return (
    <div className="space-y-3">
      {/* 1. Critical Tamper Detected Banner */}
      {isTamperDetected && (
        <div className="p-4 rounded-xl bg-gradient-to-r from-red-950 via-rose-950 to-red-950 border-2 border-red-500 text-white shadow-2xl flex items-center justify-between animate-pulse">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-red-500/20 border border-red-500/40 flex items-center justify-center shrink-0">
              <ShieldAlert className="w-5 h-5 text-red-400" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-black uppercase tracking-wider bg-red-600 px-2 py-0.5 rounded text-white">
                  CRITICAL FRAUD ALERT
                </span>
                <span className="text-xs text-red-300 font-mono">SHA-256 Hash Mismatch</span>
              </div>
              <p className="text-xs text-red-200 mt-1">
                Contract payload was altered! PolicyEngine cryptographic dispute verification flagged a root hash discrepancy.
              </p>
            </div>
          </div>
          <span className="text-xs font-mono font-bold text-red-300 px-3 py-1 bg-red-900/50 rounded-lg border border-red-500/30">
            PayPal Capture Blocked
          </span>
        </div>
      )}

      {/* 2. Adversarial Price Surge HITL Hold Banner */}
      {isHitlHold && (
        <div className="p-4 rounded-xl bg-gradient-to-r from-amber-950/80 via-red-950/70 to-amber-950/80 border border-amber-500/60 shadow-xl flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-amber-500/20 border border-amber-500/40 flex items-center justify-center shrink-0">
              <AlertTriangle className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-extrabold uppercase bg-amber-500 text-slate-950 px-2 py-0.5 rounded">
                  ADVERSARIAL SURGE DETECTED
                </span>
                <span className="text-xs text-amber-300 font-mono">PolicyEngine Circuit Breaker Active</span>
              </div>
              <p className="text-xs text-slate-200 mt-0.5">
                Vendor proposed price exceeding authorized mandate ceiling. Execution halted. Requires Supervisor Audit Sign-Off.
              </p>
            </div>
          </div>
          <div className="hidden sm:block text-right">
            <span className="text-[11px] font-mono text-amber-300 block">Treasury Loss: $0.00</span>
            <span className="text-[10px] text-slate-400">Protected by Code</span>
          </div>
        </div>
      )}

      {/* 3. Escrow Milestone Release Success Banner (when captured) */}
      {isCaptured && order?.paypal_capture_id && (
        <div className="p-4 rounded-xl bg-gradient-to-r from-emerald-950/70 via-slate-900 to-indigo-950/70 border border-emerald-500/50 shadow-xl flex items-center justify-between animate-fade-in">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center shrink-0">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-bold uppercase bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 rounded">
                  MILESTONE 3 SETTLED ON PAYPAL
                </span>
                <span className="text-xs font-mono text-cyan-300">Capture ID: {order.paypal_capture_id}</span>
              </div>
              <p className="text-xs text-slate-300 mt-0.5">
                Delivery verified via carrier tracking. ${order.total_amount?.toLocaleString()} successfully captured and disbursed to vendor.
              </p>
            </div>
          </div>
          <span className="text-xs font-mono font-bold text-emerald-400 px-3 py-1 bg-emerald-950/50 rounded-lg border border-emerald-500/30">
            Dispute Grade: A+
          </span>
        </div>
      )}

      {/* 4. Milestone 1: Funds Locked in Escrow Banner */}
      {isFundsAuthorized && !isInTransit && !isCaptured && (
        <div className="p-4 rounded-xl bg-gradient-to-r from-blue-950/70 via-indigo-950/70 to-slate-900 border border-blue-500/50 shadow-xl flex items-center justify-between animate-fade-in">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-blue-500/20 border border-blue-500/40 flex items-center justify-center shrink-0">
              <Lock className="w-5 h-5 text-cyan-400" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-bold uppercase bg-blue-500/20 text-blue-300 border border-blue-500/30 px-2 py-0.5 rounded">
                  MILESTONE 1: 29-DAY AUTHORIZATION HOLD PLACED
                </span>
                <span className="text-xs font-mono text-cyan-300">Auth ID: {order.paypal_authorization_id}</span>
              </div>
              <p className="text-xs text-slate-300 mt-0.5">
                Buyer funds (${order.total_amount?.toLocaleString()}) are secured under PayPal 29-day authorization hold. Awaiting supplier shipment dispatch proof.
              </p>
            </div>
          </div>
          <span className="text-xs font-mono font-bold text-blue-400 px-3 py-1 bg-blue-950/50 rounded-lg border border-blue-500/30">
            Auth Hold Active
          </span>
        </div>
      )}

      {/* 5. Milestone 2: Carrier Proof Ingested Banner */}
      {isInTransit && !isCaptured && (
        <div className="p-4 rounded-xl bg-gradient-to-r from-amber-950/60 via-slate-900 to-indigo-950/60 border border-amber-500/50 shadow-xl flex items-center justify-between animate-fade-in">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-amber-500/20 border border-amber-500/40 flex items-center justify-center shrink-0">
              <Truck className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-bold uppercase bg-amber-500/20 text-amber-300 border border-amber-500/30 px-2 py-0.5 rounded">
                  MILESTONE 2: CARRIER PROOF VERIFIED
                </span>
                <span className="text-xs font-mono text-amber-300">{order.carrier_name}: #{order.tracking_number}</span>
              </div>
              <p className="text-xs text-slate-300 mt-0.5">
                Shipment departure scan verified. Milestone 1 partial capture (30%) released; final 70% capture will execute upon confirmed delivery.
              </p>
            </div>
          </div>
          <span className="text-xs font-mono font-bold text-amber-400 px-3 py-1 bg-amber-950/50 rounded-lg border border-amber-500/30">
            In-Transit
          </span>
        </div>
      )}

      {/* Toast Notification Container (Floating Bottom-Right) */}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col space-y-2 pointer-events-none max-w-sm w-full">
        {toasts.map((toast) => {
          const type = toast.type || 'info';
          const bgColors = {
            success: 'bg-emerald-950/90 border-emerald-500/60 text-emerald-200',
            warning: 'bg-amber-950/90 border-amber-500/60 text-amber-200',
            error: 'bg-red-950/90 border-red-500/60 text-red-200',
            info: 'bg-slate-900/90 border-cyan-500/60 text-cyan-200',
          }[type];

          const IconComp = {
            success: CheckCircle2,
            warning: AlertTriangle,
            error: ShieldAlert,
            info: CheckCircle2,
          }[type];

          return (
            <div
              key={toast.id}
              className={`p-3.5 rounded-xl border shadow-2xl backdrop-blur-md pointer-events-auto flex items-start justify-between space-x-3 transition-all transform animate-fade-in ${bgColors}`}
            >
              <div className="flex items-start space-x-2.5">
                <IconComp className="w-4 h-4 shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-xs font-bold text-white">{toast.title}</h4>
                  <p className="text-[11px] text-slate-300 mt-0.5 leading-relaxed">{toast.message}</p>
                  {toast.meta && (
                    <span className="text-[9px] font-mono text-slate-400 block mt-1">{toast.meta}</span>
                  )}
                </div>
              </div>
              <button
                onClick={() => onDismissToast && onDismissToast(toast.id)}
                className="text-slate-400 hover:text-white p-1 rounded hover:bg-slate-800/50"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}

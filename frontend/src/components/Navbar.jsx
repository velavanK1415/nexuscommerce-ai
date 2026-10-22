import React from 'react';
import { 
  ShieldCheck, 
  Zap, 
  Activity, 
  Database, 
  BarChart3, 
  Lock, 
  CheckCircle2,
  Sliders,
  Eye,
  EyeOff,
  User,
  Scale,
  Download
} from './icons';
import Tooltip from './Tooltip';

export default function Navbar({ 
  activeTab, 
  setActiveTab, 
  demoMode, 
  onToggleDemoMode, 
  onQuickDemo, 
  isRunningDemo,
  viewMode = 'executive',
  onToggleViewMode,
  role = 'director',
  onSelectRole,
  onOpenComparisonModal,
  onDownloadAuditBundle
}) {
  return (
    <header className="border-b border-slate-800 bg-[#0E1322]/90 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Brand */}
        <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('cockpit')}>
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-500 to-cyan-400 p-0.5 shadow-lg shadow-indigo-500/20 flex items-center justify-center">
            <div className="w-full h-full bg-[#0B0F19] rounded-[10px] flex items-center justify-center">
              <Zap className="w-5 h-5 text-cyan-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
                NexusCommerce
              </span>
              <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold tracking-wider uppercase bg-blue-500/10 text-cyan-400 border border-cyan-500/30">
                AI Agentic
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-medium">PayPal Autonomous B2B Sourcing & Milestone Captures</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="hidden lg:flex items-center space-x-1 bg-slate-900/80 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setActiveTab('cockpit')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center space-x-2 ${
              activeTab === 'cockpit'
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            <span>Procurement Cockpit</span>
          </button>

          <button
            onClick={() => setActiveTab('analytics')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center space-x-2 ${
              activeTab === 'analytics'
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5 text-cyan-400" />
            <span>AG Studio Analytics</span>
            <span className="text-[9px] px-1 py-0.2 rounded bg-amber-500/20 text-amber-300 font-bold border border-amber-500/30">
              $5k Prize
            </span>
          </button>

          <button
            onClick={() => setActiveTab('evidence')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center space-x-2 ${
              activeTab === 'evidence'
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>Evidence Bundle Vault</span>
          </button>
        </nav>

        {/* Right Action Tools */}
        <div className="flex items-center space-x-2 sm:space-x-3">
          
          {/* Mock Role Switcher Dropdown */}
          <div className="hidden sm:flex items-center space-x-1.5 bg-slate-900/90 border border-slate-800 rounded-lg px-2 py-1">
            <User className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={role}
              onChange={(e) => onSelectRole && onSelectRole(e.target.value)}
              className="bg-transparent text-[11px] text-slate-200 font-semibold focus:outline-none cursor-pointer"
              title="Role-Based Access: Switch persona to test as Buyer, Supplier, or Auditor"
            >
              <option value="director" className="bg-slate-900 text-white">👔 Procurement Director</option>
              <option value="vendor" className="bg-slate-900 text-white">🏭 Supplier Rep (NexIQ)</option>
              <option value="auditor" className="bg-slate-900 text-white">⚖️ Compliance Auditor</option>
            </select>
          </div>

          {/* Executive Summary vs Technical Deep-Dive Toggle */}
          <button
            onClick={onToggleViewMode}
            className={`px-2.5 py-1 rounded-lg text-xs font-semibold border flex items-center space-x-1.5 transition-all ${
              viewMode === 'technical'
                ? 'bg-cyan-950/60 text-cyan-300 border-cyan-500/40 shadow-sm shadow-cyan-500/20'
                : 'bg-slate-900 text-slate-300 border-slate-700 hover:border-slate-600'
            }`}
            title={`Toggle View Mode (Currently: ${viewMode === 'technical' ? 'Technical Deep-Dive' : 'Executive Business Overview'})`}
          >
            {viewMode === 'technical' ? (
              <>
                <Eye className="w-3.5 h-3.5 text-cyan-400" />
                <span className="hidden md:inline">Technical Mode</span>
              </>
            ) : (
              <>
                <Sliders className="w-3.5 h-3.5 text-indigo-400" />
                <span className="hidden md:inline">Executive Mode</span>
              </>
            )}
          </button>

          {/* Dedicated Download Audit Bundle Button */}
          <div className="relative group/export">
            <button
              onClick={() => onDownloadAuditBundle && onDownloadAuditBundle('json')}
              className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-emerald-950/60 hover:bg-emerald-900/70 border border-emerald-500/40 text-emerald-300 flex items-center space-x-1.5 transition-all shadow-sm shadow-emerald-500/10"
              title="Download Compliance Audit Bundle (Signed JSON & Dispute Defense Certificate)"
            >
              <Download className="w-3.5 h-3.5 text-emerald-400" />
              <span className="hidden xl:inline">Audit Bundle</span>
            </button>
            <div className="hidden group-hover/export:flex absolute right-0 top-full mt-1.5 w-48 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl p-1.5 flex-col space-y-1 z-50 animate-fade-in">
              <button
                onClick={() => onDownloadAuditBundle && onDownloadAuditBundle('json')}
                className="w-full text-left px-2.5 py-1.5 rounded-lg hover:bg-slate-800 text-[11px] text-slate-200 hover:text-white flex items-center space-x-2"
              >
                <Download className="w-3 h-3 text-cyan-400" />
                <span>Export Signed JSON</span>
              </button>
              <button
                onClick={() => onDownloadAuditBundle && onDownloadAuditBundle('pdf')}
                className="w-full text-left px-2.5 py-1.5 rounded-lg hover:bg-slate-800 text-[11px] text-slate-200 hover:text-white flex items-center space-x-2"
              >
                <ShieldCheck className="w-3 h-3 text-emerald-400" />
                <span>Print Dispute Certificate (PDF)</span>
              </button>
            </div>
          </div>

          {/* Side-by-side Comparative Analysis Trigger */}
          {onOpenComparisonModal && (
            <button
              onClick={onOpenComparisonModal}
              className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-800 transition-all flex items-center"
              title="Multi-Run Comparative Analysis: View side-by-side agent performance across scenarios"
            >
              <Scale className="w-4 h-4 text-cyan-400" />
            </button>
          )}

          {/* Zero-Key Demo Mode Badge */}
          <button
            onClick={onToggleDemoMode}
            className={`px-2.5 py-1 rounded-lg text-xs font-medium border hidden md:flex items-center space-x-1.5 transition-all ${
              demoMode
                ? 'bg-emerald-950/40 text-emerald-300 border-emerald-500/40 hover:bg-emerald-900/40'
                : 'bg-blue-950/40 text-blue-300 border-blue-500/40 hover:bg-blue-900/40'
            }`}
            title="Toggle between Zero-Key Mock Demo and Live PayPal REST API v2"
          >
            <div className={`w-2 h-2 rounded-full ${demoMode ? 'bg-emerald-400 animate-pulse' : 'bg-blue-400'}`} />
            <span>{demoMode ? 'Zero-Key Demo' : 'Live PayPal v2'}</span>
          </button>

          {/* Quick Demo Button */}
          <button
            onClick={onQuickDemo}
            disabled={isRunningDemo}
            className="px-3 py-1.5 rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/20 flex items-center space-x-1.5 transition-all disabled:opacity-50"
          >
            <Zap className={`w-3.5 h-3.5 ${isRunningDemo ? 'animate-spin' : ''}`} />
            <span>{isRunningDemo ? 'Simulating...' : '1-Click Lifecycle'}</span>
          </button>
        </div>
      </div>
    </header>
  );
}

import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import MandateConfigModal from './components/MandateConfigModal';
import NegotiationView from './components/NegotiationView';
import MilestoneTimeline from './components/MilestoneTimeline';
import AGStudioSpendGrid from './components/AGStudioSpendGrid';
import EvidenceBundleViewer from './components/EvidenceBundleViewer';
import ZeroKeyDemoPanel from './components/ZeroKeyDemoPanel';
import AgentProgressVisualizer from './components/AgentProgressVisualizer';
import AlertBannerSystem from './components/AlertBannerSystem';
import NegotiationAnalyticsDashboard from './components/NegotiationAnalyticsDashboard';
import ComparativeAnalysisModal from './components/ComparativeAnalysisModal';
import ExecutiveCaptionBar from './components/ExecutiveCaptionBar';
import { User, ShieldCheck, Download, Sparkles, Scale } from './components/icons';
import { api } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('cockpit'); // 'cockpit' | 'analytics' | 'evidence'
  const [demoMode, setDemoMode] = useState(true);
  const [mandate, setMandate] = useState(null);
  const [session, setSession] = useState(null);
  const [order, setOrder] = useState(null);
  const [bundle, setBundle] = useState(null);
  const [summary, setSummary] = useState(null);
  const [gridData, setGridData] = useState({ rows: [] });
  const [isMandateModalOpen, setIsMandateModalOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [isRunningDemo, setIsRunningDemo] = useState(false);

  // New UI/UX states
  const [viewMode, setViewMode] = useState('executive'); // 'executive' | 'technical'
  const [role, setRole] = useState('director'); // 'director' | 'vendor' | 'auditor'
  const [isComparisonModalOpen, setIsComparisonModalOpen] = useState(false);
  const [toasts, setToasts] = useState([]);

  // Toast Notification Manager
  const addToast = ({ type = 'info', title, message, meta }) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).substr(2, 4)}`;
    const newToast = { id, type, title, message, meta };
    setToasts((prev) => [...prev.slice(-3), newToast]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 5500);
  };

  const handleDismissToast = (id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  // Initial Data Fetch
  const refreshData = async () => {
    try {
      const [sumRes, gridRes, ordersRes, mandatesRes, sessionsRes] = await Promise.all([
        api.getSpendSummary().catch(() => null),
        api.getAgGridData().catch(() => ({ rows: [] })),
        api.getOrders().catch(() => []),
        api.getMandates().catch(() => []),
        api.getSessions().catch(() => []),
      ]);

      if (sumRes) setSummary(sumRes);
      if (gridRes) setGridData(gridRes);

      if (mandatesRes && mandatesRes.length > 0 && !mandate) {
        setMandate(mandatesRes[mandatesRes.length - 1]);
      }

      if (sessionsRes && sessionsRes.length > 0 && !session) {
        setSession(sessionsRes[sessionsRes.length - 1]);
      }

      if (ordersRes && ordersRes.length > 0 && !order) {
        const latestOrder = ordersRes[ordersRes.length - 1];
        setOrder(latestOrder);
        if (latestOrder.evidence_bundle_id) {
          const b = await api.getEvidenceBundle(latestOrder.evidence_bundle_id).catch(() => null);
          if (b) setBundle(b);
        }
      }
    } catch (err) {
      console.error('Error fetching initial dashboard data:', err);
    }
  };

  useEffect(() => {
    refreshData();
  }, []);

  // Handlers with Proactive Visual Alerts
  const handleCreateMandate = async (formData) => {
    setLoading(true);
    try {
      const newMandate = await api.createMandate(formData);
      setMandate(newMandate);
      setSession(null);
      setOrder(null);
      setBundle(null);
      await refreshData();
      addToast({
        type: 'success',
        title: 'Procurement Mandate Signed',
        message: `Mandate ${newMandate.id} (${newMandate.item_name}) cryptographically bound into PolicyEngine.`,
        meta: `Cap: $${newMandate.max_total_budget.toLocaleString()}`,
      });
    } catch (err) {
      addToast({
        type: 'error',
        title: 'Failed to Create Mandate',
        message: err.message || 'Signature rejected.',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleStartNegotiation = async (simulateViolation = null) => {
    if (!mandate) return;
    setLoading(true);
    addToast({
      type: 'info',
      title: simulateViolation ? 'Adversarial Surge Injection Started' : 'Multi-Agent Negotiation Active',
      message: simulateViolation
        ? 'VendorBot attempting +50% price escalation above mandate ceiling.'
        : 'ProcureBot & VendorBot formulating bids within signed envelope.',
    });

    try {
      const newSession = await api.startNegotiation({
        mandate_id: mandate.id,
        simulate_violation: simulateViolation,
        max_rounds: 4,
      });
      setSession(newSession);
      await refreshData();

      if (newSession.status === 'HITL_HOLD') {
        addToast({
          type: 'warning',
          title: '⚠️ Adversarial Price Spike Halted',
          message: newSession.hitl_reason || 'Proposal breached mandate ceiling. Order placed in HITL hold.',
          meta: 'Treasury loss prevented: $0.00',
        });
      } else if (newSession.status === 'AGREEMENT_REACHED') {
        addToast({
          type: 'success',
          title: 'Dual-Agent Consensus Certified',
          message: `Mutual agreement finalized at $${newSession.agreement?.final_unit_price?.toFixed(2)}/unit.`,
        });
      }
    } catch (err) {
      addToast({
        type: 'error',
        title: 'Negotiation Failed',
        message: err.message || 'Agent negotiation error.',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleHitlOverride = async (supervisorNotes) => {
    if (!session) return;
    setLoading(true);
    try {
      const agreement = await api.submitHitlOverride(session.session_id, supervisorNotes);
      setSession((prev) => ({
        ...prev,
        status: 'AGREEMENT_REACHED',
        agreement,
        hitl_reason: null,
      }));
      await refreshData();
      addToast({
        type: 'success',
        title: 'Supervisor Override Authorized',
        message: 'Procurement supervisor audit signature appended. Agreement released for PayPal authorization hold.',
      });
    } catch (err) {
      addToast({
        type: 'error',
        title: 'Override Authorization Failed',
        message: err.message,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleAuthorizeEscrow = async () => {
    if (!session) return;
    setLoading(true);
    try {
      const res = await api.authorizeEscrow(session.session_id);
      setOrder(res.order);
      if (res.evidence_bundle_id) {
        const b = await api.getEvidenceBundle(res.evidence_bundle_id);
        setBundle(b);
      }
      await refreshData();
      addToast({
        type: 'success',
        title: 'Milestone 1: 29-Day Authorization Hold Placed',
        message: `$${res.order.total_amount?.toLocaleString()} authorized and secured under PayPal Auth ID ${res.order.paypal_authorization_id || 'v2-AUTH'}.`,
      });
    } catch (err) {
      addToast({
        type: 'error',
        title: 'PayPal Authorization Failed',
        message: err.message,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleAdvanceShipment = async (carrierName, trackingNumber) => {
    if (!order) return;
    setLoading(true);
    try {
      const res = await api.advanceShipment(order.order_id, carrierName, trackingNumber);
      setOrder(res.order);
      if (res.order.evidence_bundle_id) {
        const b = await api.getEvidenceBundle(res.order.evidence_bundle_id);
        setBundle(b);
      }
      await refreshData();
      addToast({
        type: 'info',
        title: 'Milestone 2: Carrier Proof Verified',
        message: `${res.order.carrier_name} tracking #${res.order.tracking_number} ingested into Merkle tree.`,
      });
    } catch (err) {
      addToast({
        type: 'error',
        title: 'Carrier Verification Failed',
        message: err.message,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleAdvanceDelivery = async () => {
    if (!order) return;
    setLoading(true);
    try {
      const res = await api.advanceDeliveryAndCapture(order.order_id);
      setOrder(res.order);
      if (res.order.evidence_bundle_id) {
        const b = await api.getEvidenceBundle(res.order.evidence_bundle_id);
        setBundle(b);
      }
      await refreshData();
      addToast({
        type: 'success',
        title: 'Milestone 3: Delivery Captured & Settled',
        message: `PayPal funds capture completed (ID: ${res.order.paypal_capture_id}). Payout disbursed to supplier.`,
      });
    } catch (err) {
      addToast({
        type: 'error',
        title: 'Delivery Capture Failed',
        message: err.message,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSimulateWebhook = async (eventType, orderId) => {
    setLoading(true);
    try {
      await api.simulateWebhook(eventType, orderId);
      await refreshData();
      const updatedOrders = await api.getOrders();
      const match = updatedOrders.find((o) => o.order_id === orderId);
      if (match) setOrder(match);
      addToast({
        type: 'info',
        title: 'PayPal Webhook Ingested',
        message: `Dispatched event ${eventType}. State machine reconciled.`,
      });
    } catch (err) {
      addToast({
        type: 'error',
        title: 'Webhook Simulation Error',
        message: err.message,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyBundle = async (bundleId) => {
    setLoading(true);
    try {
      const res = await api.verifyEvidenceBundle(bundleId);
      setBundle((prev) => ({ ...prev, tamper_evident_valid: res.tamper_evident_valid }));
      addToast({
        type: res.tamper_evident_valid ? 'success' : 'error',
        title: res.tamper_evident_valid ? 'Cryptographic Seal Verified (A+)' : 'Integrity Check Failed',
        message: res.tamper_evident_valid
          ? 'All 4 constituent artifact hashes match Merkle root. Tamper-evident proof intact.'
          : 'Root hash mismatch! PolicyEngine detected payload modification.',
      });
      return res;
    } finally {
      setLoading(false);
    }
  };

  const handleSimulateTamper = async (bundleId) => {
    setLoading(true);
    try {
      const res = await api.simulateTamperAttack(bundleId);
      setBundle((prev) => ({
        ...prev,
        tamper_evident_valid: false,
        agreement_hash: 'MALICIOUS_TAMPERED_HASH_FORGERY',
      }));
      addToast({
        type: 'error',
        title: '🚨 Tamper Attack Test Injected',
        message: 'Contract unit price altered to $9,999.00. SHA-256 seal failed immediately!',
      });
      return res;
    } finally {
      setLoading(false);
    }
  };

  const handleRestoreBundle = async (bundleId) => {
    setLoading(true);
    try {
      const res = await api.restoreEvidenceBundle(bundleId);
      if (res.bundle) {
        setBundle(res.bundle);
      }
      await refreshData();
      addToast({
        type: 'success',
        title: 'Evidence Bundle Restored',
        message: 'Original cryptographic hashes restored. Verification status is authentic.',
      });
      return res;
    } finally {
      setLoading(false);
    }
  };

  const handleRunLifecycleDemo = async (params) => {
    setIsRunningDemo(true);
    addToast({
      type: 'info',
      title: 'Running Autonomous Full Lifecycle',
      message: 'Executing multi-agent negotiation, 29-day authorization hold, carrier proof, and milestone captures...',
    });

    try {
      const res = await api.runFullLifecycleDemo(params);
      if (res.mandate) setMandate(res.mandate);
      if (res.negotiation_session || res.session) setSession(res.negotiation_session || res.session);
      if (res.escrow_order) setOrder(res.escrow_order);
      if (res.evidence_bundle) setBundle(res.evidence_bundle);
      await refreshData();

      if (res.lifecycle_status === 'COMPLETED_SETTLED') {
        addToast({
          type: 'success',
          title: 'Full Lifecycle Settled & Sealed',
          message: `Dispute defense grade: ${res.verification_result?.dispute_defense_grade || 'A+'}. Funds released.`,
        });
      } else if (res.lifecycle_status === 'HITL_HOLD_TRIGGERED') {
        addToast({
          type: 'warning',
          title: 'Adversarial Surge Trapped in Full Demo',
          message: 'PolicyEngine halted the transaction before funds were committed.',
        });
      }
      return res;
    } catch (err) {
      addToast({
        type: 'error',
        title: 'Lifecycle Execution Failed',
        message: err.message,
      });
    } finally {
      setIsRunningDemo(false);
    }
  };

  const handleToggleDemoMode = async () => {
    const nextState = !demoMode;
    await api.toggleDemoMode(nextState);
    setDemoMode(nextState);
    addToast({
      type: 'info',
      title: nextState ? 'Zero-Key Demo Mode Activated' : 'Live PayPal v2 Mode Activated',
      message: nextState
        ? 'Using simulated PayPal provider for zero-credential hackathon evaluation.'
        : 'Connecting to live PayPal REST API v2 endpoints.',
    });
  };

  const handleLaunchComparativeScenario = async (scenario) => {
    if (scenario.tag === 'HITL Hold') {
      await handleStartNegotiation('PRICE_SPIKE');
    } else {
      await handleRunLifecycleDemo({
        item_name: scenario.item_name,
        quantity: scenario.quantity,
        max_unit_price: scenario.unit_cap,
        max_total_budget: scenario.budget_cap,
        simulate_hitl_hold: false,
      });
    }
  };

  const roleDescriptions = {
    director: {
      title: 'Procurement Director',
      org: 'Apex Global Logistics Corp',
      permission: 'Full Authority: Sign Mandates, Authorize Overrides, Lock Funds',
      color: 'bg-indigo-500/10 text-indigo-300 border-indigo-500/30',
    },
    vendor: {
      title: 'Supplier Representative',
      org: 'NexIQ Enterprise Networks Ltd',
      permission: 'Vendor Portal: Review RFQs, Counter-Offers, Dispatch Tracking Proof',
      color: 'bg-cyan-500/10 text-cyan-300 border-cyan-500/30',
    },
    auditor: {
      title: 'Compliance Auditor / Hackathon Judge',
      org: 'PayPal AI Hackathon Jury',
      permission: 'Forensic Audit: SHA-256 Seal Verification, Tamper Testing, Evidence Export',
      color: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30',
    },
  };

  const activeRoleInfo = roleDescriptions[role] || roleDescriptions.director;

  return (
    <div className="min-h-screen bg-[#0B0F19] text-slate-100 flex flex-col font-sans">
      
      {/* Top Navigation with Role Switcher & View Mode Toggle */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        demoMode={demoMode}
        onToggleDemoMode={handleToggleDemoMode}
        onQuickDemo={() => handleRunLifecycleDemo({
          item_name: mandate?.item_name || 'NVIDIA H100 SXM5 80GB GPU Cluster',
          quantity: mandate?.quantity || 100,
          max_unit_price: mandate?.max_unit_price || 32000.0,
          max_total_budget: mandate?.max_total_budget || 3200000.0,
          simulate_hitl_hold: false,
        })}
        isRunningDemo={isRunningDemo}
        viewMode={viewMode}
        onToggleViewMode={() => setViewMode(viewMode === 'executive' ? 'technical' : 'executive')}
        role={role}
        onSelectRole={setRole}
        onOpenComparisonModal={() => setIsComparisonModalOpen(true)}
        onDownloadAuditBundle={(format = 'json') => {
          const targetId = bundle?.bundle_id || 'latest';
          if (format === 'pdf') {
            window.open(api.getAuditReportUrl(targetId), '_blank');
          } else {
            window.open(api.getAuditBundleExportUrl(targetId), '_blank');
          }
          addToast({
            type: 'success',
            title: format === 'pdf' ? 'Dispute Certificate Generated' : 'Cryptographic Audit Bundle Exported',
            message: `Official compliance package for ${targetId} opened for review.`,
          });
        }}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        
        {/* Active Role & View Mode Status Ribbon */}
        <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs">
          <div className="flex items-center space-x-2.5">
            <span className={`px-2.5 py-1 rounded-lg font-semibold border flex items-center space-x-1.5 ${activeRoleInfo.color}`}>
              <User className="w-3.5 h-3.5" />
              <span>Persona: {activeRoleInfo.title} ({activeRoleInfo.org})</span>
            </span>
            <span className="hidden sm:inline text-slate-400 text-[11px]">
              • {activeRoleInfo.permission}
            </span>
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-[11px] text-slate-400">View Lens:</span>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-800 text-cyan-300 border border-slate-700">
              {viewMode === 'technical' ? '🔬 Technical Deep-Dive' : '💼 Executive Overview'}
            </span>
            <button
              onClick={() => setIsComparisonModalOpen(true)}
              className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px] font-medium border border-slate-700 flex items-center space-x-1 ml-1"
            >
              <Scale className="w-3 h-3 text-cyan-400" />
              <span>Run Comparison</span>
            </button>
          </div>
        </div>

        {/* Proactive Visual Alert System: Status Banners & Floating Toasts */}
        <AlertBannerSystem
          session={session}
          order={order}
          bundle={bundle}
          toasts={toasts}
          onDismissToast={handleDismissToast}
        />

        {/* Cockpit Tab */}
        {activeTab === 'cockpit' && (
          <div className="space-y-6 animate-fade-in">
            
            {/* 0. 30-Second "What Just Happened" Executive Caption Bar */}
            <ExecutiveCaptionBar
              session={session}
              order={order}
              mandate={mandate}
              bundle={bundle}
            />

            {/* 1. Interactive Agent Progress Visualizer */}
            <AgentProgressVisualizer
              session={session}
              isRunning={isRunningDemo}
              loading={loading}
              mandate={mandate}
            />

            {/* 2. Zero Key Quick Panel */}
            <ZeroKeyDemoPanel
              onRunLifecycle={handleRunLifecycleDemo}
              isRunning={isRunningDemo}
              demoMode={demoMode}
              onToggleDemoMode={handleToggleDemoMode}
            />

            {/* 3. Negotiation & HITL Workspace */}
            <NegotiationView
              mandate={mandate}
              session={session}
              onStartNegotiation={handleStartNegotiation}
              onHitlOverride={handleHitlOverride}
              onAuthorizeEscrow={handleAuthorizeEscrow}
              loading={loading}
              onOpenMandateModal={() => setIsMandateModalOpen(true)}
              viewMode={viewMode}
              role={role}
              onOpenComparisonModal={() => setIsComparisonModalOpen(true)}
            />

            {/* 4. Negotiation & Savings Analytics Dashboard */}
            <NegotiationAnalyticsDashboard
              session={session}
              mandate={mandate}
              summary={summary}
              viewMode={viewMode}
            />

            {/* 5. Milestone-Based Escrow Settlement on PayPal */}
            <MilestoneTimeline
              order={order}
              onAdvanceShipment={handleAdvanceShipment}
              onAdvanceDelivery={handleAdvanceDelivery}
              onSimulateWebhook={handleSimulateWebhook}
              loading={loading}
            />
          </div>
        )}

        {/* Analytics Tab (AG Studio & AG Grid + Negotiation KPI Dashboard) */}
        {activeTab === 'analytics' && (
          <div className="space-y-6 animate-fade-in">
            <NegotiationAnalyticsDashboard
              session={session}
              mandate={mandate}
              summary={summary}
              viewMode={viewMode}
            />

            <AGStudioSpendGrid
              summary={summary}
              gridData={gridData}
              onRefresh={refreshData}
            />
          </div>
        )}

        {/* Evidence Vault Tab */}
        {activeTab === 'evidence' && (
          <div className="animate-fade-in">
            <EvidenceBundleViewer
              bundle={bundle}
              onVerifyBundle={handleVerifyBundle}
              onSimulateTamper={handleSimulateTamper}
              onRestoreBundle={handleRestoreBundle}
              loading={loading}
              viewMode={viewMode}
            />
          </div>
        )}

      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-[#0E1322] py-6 text-center text-xs text-slate-500">
        <p>NexusCommerce AI — Built for the PayPal AI Hackathon on Devpost ($60,000+ Prize Pool)</p>
        <p className="mt-1 text-[11px] text-slate-600">
          Architecture: Code Decides, LLM Proposes · Deterministic PolicyEngine · Cryptographic Evidence Bundles · AG Studio Analytics
        </p>
      </footer>

      {/* Mandate Modal with Pre-filled Templates */}
      <MandateConfigModal
        isOpen={isMandateModalOpen}
        onClose={() => setIsMandateModalOpen(false)}
        onMandateCreated={handleCreateMandate}
      />

      {/* Multi-Run Comparative Analysis Modal */}
      <ComparativeAnalysisModal
        isOpen={isComparisonModalOpen}
        onClose={() => setIsComparisonModalOpen(false)}
        onLaunchScenario={handleLaunchComparativeScenario}
      />
    </div>
  );
}

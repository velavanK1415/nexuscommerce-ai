/**
 * NexusCommerce AI - API Client
 * Connects React frontend to FastAPI backend.
 */

const BASE_URL = '/api';

export const api = {
  // Health & Status
  async getHealth() {
    const res = await fetch(`${BASE_URL}/health`);
    return res.json();
  },

  // Mandates
  async getMandates() {
    const res = await fetch(`${BASE_URL}/mandates`);
    return res.json();
  },

  async createMandate(data) {
    const res = await fetch(`${BASE_URL}/mandates`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error((await res.json()).detail || 'Failed to create mandate');
    return res.json();
  },

  // Negotiation & HITL
  async startNegotiation(params) {
    const res = await fetch(`${BASE_URL}/negotiate/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (!res.ok) throw new Error((await res.json()).detail || 'Negotiation failed');
    return res.json();
  },

  async submitHitlOverride(sessionId, supervisorNotes) {
    const res = await fetch(`${BASE_URL}/negotiate/hitl-override`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, supervisor_notes: supervisorNotes }),
    });
    if (!res.ok) throw new Error((await res.json()).detail || 'Failed to submit HITL override');
    return res.json();
  },

  async getSessions() {
    const res = await fetch(`${BASE_URL}/negotiate/sessions`);
    return res.json();
  },

  // Escrow Milestones
  async authorizeEscrow(sessionId) {
    const res = await fetch(`${BASE_URL}/escrow/authorize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId }),
    });
    if (!res.ok) throw new Error((await res.json()).detail || 'Escrow authorization failed');
    return res.json();
  },

  async advanceShipment(orderId, carrierName = 'FedEx Priority Freight', trackingNumber = null) {
    const res = await fetch(`${BASE_URL}/escrow/${orderId}/advance-shipment`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ carrier_name: carrierName, tracking_number: trackingNumber }),
    });
    if (!res.ok) throw new Error((await res.json()).detail || 'Shipment update failed');
    return res.json();
  },

  async advanceDeliveryAndCapture(orderId) {
    const res = await fetch(`${BASE_URL}/escrow/${orderId}/advance-delivery`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) throw new Error((await res.json()).detail || 'Capture release failed');
    return res.json();
  },

  async getOrders() {
    const res = await fetch(`${BASE_URL}/escrow/orders`);
    return res.json();
  },

  // Evidence Bundles
  async getEvidenceBundles() {
    const res = await fetch(`${BASE_URL}/evidence`);
    return res.json();
  },

  async getEvidenceBundle(bundleId) {
    const res = await fetch(`${BASE_URL}/evidence/${bundleId}`);
    return res.json();
  },

  async verifyEvidenceBundle(bundleId) {
    const res = await fetch(`${BASE_URL}/evidence/${bundleId}/verify`, { method: 'POST' });
    return res.json();
  },

  async simulateTamperAttack(bundleId) {
    const res = await fetch(`${BASE_URL}/evidence/${bundleId}/tamper-test`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ field_to_alter: 'final_unit_price', tampered_value: 9999.0 }),
    });
    return res.json();
  },

  async restoreEvidenceBundle(bundleId) {
    const res = await fetch(`${BASE_URL}/evidence/${bundleId}/restore`, {
      method: 'POST',
    });
    return res.json();
  },

  // Webhooks
  async simulateWebhook(eventType, orderId) {
    const res = await fetch(`${BASE_URL}/webhooks/simulate?event_type=${eventType}&order_id=${orderId}`, {
      method: 'POST',
    });
    return res.json();
  },

  // AG Studio Analytics
  async getSpendSummary() {
    const res = await fetch(`${BASE_URL}/analytics/summary`);
    return res.json();
  },

  async getAgGridData() {
    const res = await fetch(`${BASE_URL}/analytics/grid-data`);
    return res.json();
  },

  // Zero-Key Demo
  async runFullLifecycleDemo(params) {
    const res = await fetch(`${BASE_URL}/demo/run-full-lifecycle`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (!res.ok) throw new Error((await res.json()).detail || 'Full lifecycle demo failed');
    return res.json();
  },

  async getCatalog() {
    const res = await fetch(`${BASE_URL}/demo/catalog`);
    return res.json();
  },

  async toggleDemoMode(enabled) {
    const res = await fetch(`${BASE_URL}/demo/toggle-mode?enabled=${enabled}`, {
      method: 'POST',
    });
    return res.json();
  },

  // Mandate Templates
  async getMandateTemplates() {
    const res = await fetch(`${BASE_URL}/mandates/templates`);
    return res.json();
  },

  // Comparative Analytics & Negotiation Metrics
  async getComparativeRuns() {
    const res = await fetch(`${BASE_URL}/analytics/comparative-runs`);
    return res.json();
  },

  async getNegotiationMetrics() {
    const res = await fetch(`${BASE_URL}/analytics/negotiation-metrics`);
    return res.json();
  },

  // Compliance Audit Export URLs
  getAuditBundleExportUrl(bundleId) {
    return `${BASE_URL}/evidence/${bundleId || 'latest'}/export`;
  },

  getAuditReportUrl(bundleId) {
    return `${BASE_URL}/evidence/${bundleId || 'latest'}/export-report`;
  },
};

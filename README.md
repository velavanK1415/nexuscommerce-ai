# ⚡ NexusCommerce AI
### Autonomous Multi-Agent B2B Procurement & Two-Step Authorization & Milestone Captures on PayPal

> **Target Competition:** PayPal AI Hackathon on Devpost ($60,000+ Prize Pool)  
> **Categories Targeted:** Best Autonomous Commerce Agent, AG Studio / AG Grid Spend Intelligence ($5,000 Prize), PayPal REST API v2 Two-Step Authorization & Dispute Defense

---

## 🌟 Executive Summary

In enterprise procurement, traditional purchasing cycles take **14 to 30 days**, suffer from manual price friction, and expose counterparties to delivery disputes or unauthorized vendor charges. 

**NexusCommerce AI** transforms B2B procurement into an autonomous, cryptographically verified pipeline:
1. **Procurement Mandates as Core Invariant**: Buyers establish deterministic envelopes (max unit price, quantity, max total budget, quality grade, delivery deadlines).
2. **"Code Decides, LLM Proposes"**: Generative AI models propose negotiation strategies, but a deterministic Python **`policy_engine.py` is the sole authorized gateway** to execute PayPal API operations. Any out-of-bounds proposal or malformed schema automatically halts execution into a **Human-in-the-Loop (HITL) review hold**.
3. **Two-Step Authorization Hold & Milestone Captures on PayPal**: Funds are authorized and held for 29 days upon agreement (Milestone 1: `intent: AUTHORIZE`), partially captured upon carrier dispatch verification (Milestone 2: 30% mobilization with `is_final_capture: false`), and finally captured upon delivery verification (Milestone 3: 70% delivery with `is_final_capture: true`).
4. **Immutable Evidence Bundles**: Every transaction produces a cryptographically sealed Merkle audit trail containing the digitally signed mandate, negotiation transcript, agreement SHA-256 hash, carrier proof, and PayPal capture receipt for **100% dispute protection**.
5. **Zero-Key Evaluation Mode**: Hackathon judges can evaluate the entire autonomous lifecycle end-to-end with **Zero API Keys required**.
6. **AG Studio & AG Grid Spend Intelligence**: Self-serve spend analytics with pivot-ready data, negotiation alpha KPIs, and automated audit exports targeting the **$5,000 AG Studio hackathon prize**.

---

## 🏛️ Architectural Invariants

### 1. "Code Decides, LLM Proposes"
LLMs are creative but non-deterministic. In financial transactions, hallucinated terms or prompt injections cannot be allowed to move money.
- **Agent Role (`ProcureBot` & `VendorBot`)**: Propose offers, calculate volume discounts, formulate rationales.
- **Engine Role (`PolicyEngine`)**: Evaluates every proposed offer against mathematical invariants:
  - `unit_price <= mandate.max_unit_price`
  - `total_spend <= mandate.max_total_budget`
  - `quantity == mandate.quantity`
  - `lead_time <= mandate.delivery_deadline`
  - Strict JSON schema adherence
- If an agent proposal violates any boundary, the transaction immediately enters `HITL_HOLD`, requiring human supervisor sign-off before any funds can be moved.

### 2. Structured Procurement Mandate
The mandate is a cryptographically signed contract object containing:
- `buyer_id`, `buyer_name`, `buyer_email`
- `target_categories` (e.g. Networking Hardware, Edge Infrastructure)
- `item_name`, `quantity`, `max_unit_price`, `max_total_budget`
- `quality_tier` (Enterprise, Standard, Economy)
- `delivery_deadline`, `expiry_timestamp`
- `signature`: SHA-256 HMAC digital signature ensuring tamper resistance.

### 3. PayPal Orders v2 Two-Step Authorization & Milestone Captures
Funds are governed by a 3-milestone state machine:
- **Milestone 1: 29-Day Authorization Hold**:
  - `POST /v2/checkout/orders` with `intent=AUTHORIZE`
  - Reserves 100% buyer funds under a PayPal 29-day authorization hold. Vendor cannot withdraw prematurely.
- **Milestone 2: Carrier Shipment Proof & 30% Mobilization Partial Capture**:
  - Ingestion of verified carrier tracking (FedEx / UPS / DHL) with origin departure scan.
  - Executes `POST /v2/payments/authorizations/{auth_id}/capture` with `is_final_capture: false` releasing 30% mobilization payment with idempotent `PayPal-Request-Id`.
- **Milestone 3: Delivery Verification & 70% Final Capture**:
  - Confirmed delivery scan or buyer signed acceptance triggers `POST /v2/payments/authorizations/{auth_id}/capture` with `is_final_capture: true`.
  - Disburses remaining 70% final settlement to supplier.

### 4. Webhooks First with Polling Fallback
- PayPal webhook endpoints (`/api/webhooks/paypal`):
  - `CHECKOUT.ORDER.APPROVED`
  - `PAYMENT.AUTHORIZATION.CREATED`
  - `PAYMENT.CAPTURE.COMPLETED`
- Built-in `PollingFallbackService` reconciles order states directly against PayPal REST API v2 if network delays or dropped webhook packets occur.

### 5. Cryptographic Evidence Bundle (`evidence_bundle.py`)
To defend against buyer/seller disputes, an immutable audit trail is compiled:
- **Mandate Snapshot**: Exact signed buyer parameters at initiation.
- **Negotiation Transcript**: Round-by-round proposals, rationales, and timestamps.
- **Agreement SHA-256 Hash**: Canonical contract digest signed by both parties.
- **Carrier Proof**: Dispatch event, tracking ID, route.
- **PayPal Capture Receipt**: Capture ID, gross amount, PayPal fee, and net payout.
- **Merkle Root Seal**: `calculate_root_hash()` computes an aggregate SHA-256 seal. Any tampering with past terms immediately invalidates the bundle.

---

## 📊 AG Studio & AG Grid Spend Intelligence ($5,000 Prize)

Integrated into the dashboard under **AG Studio Analytics**:
- **Procurement Alpha KPI**: Percentage savings negotiated below supplier catalog asking prices.
- **Spend Under Management**: Live volume of transactions backed by PayPal 29-day authorization holds.
- **Interactive AG Grid Component**:
  - Sortable, resizable, pinned columns (`order_ref`, `asset`, `supplier`, `catalog_ask`, `settled_unit`, `savings`, `status`, `bundle_hash`).
  - Text, number, and category filter sets.
  - Instant CSV export for enterprise ERP integration.

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10+ (tested on Python 3.14)
- Node.js 18+ and Yarn / npm

### Automated 1-Click Launch
Run the automated startup script from the project root:
```bash
cd /root/nexuscommerce
./start.sh
```

### Manual Launch

#### 1. Backend (FastAPI)
```bash
cd /root/nexuscommerce/backend
source /root/nexuscommerce/venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
- API Documentation (Swagger): `http://localhost:8000/docs`
- Healthcheck: `http://localhost:8000/api/health`

#### 2. Frontend (React + Vite + Tailwind CSS)
```bash
cd /root/nexuscommerce/frontend
yarn install
yarn dev
```
- Dashboard UI: `http://localhost:5173`

---

## 🧪 Automated Test Suite

Run the full automated test suite verifying PolicyEngine determinism, Mandate validation, cryptographic integrity, and Zero-Key Demo flows:
```bash
cd /root/nexuscommerce
/root/nexuscommerce/venv/bin/pytest -v
```

### Test Coverage Highlights (22 Passing Tests):
- `backend/tests/test_mandate.py`: Mandate creation, digital HMAC-SHA256 signing, and expiry logic.
- `backend/tests/test_policy_engine.py`: Price ceiling breach detection, budget ceiling violations, malformed LLM schema handling, and human supervisor override.
- `backend/tests/test_escrow_and_evidence.py`: Milestone 1-3 progression, Evidence Bundle creation, cryptographic sealing, and tamper-attack detection.
- `backend/tests/test_zero_key_demo.py`: 1-click end-to-end full lifecycle, adversarial HITL trigger, and polling fallback reconciliation.
- `backend/tests/test_comprehensive_edge_cases.py`: Unauthorized PayPal authorization invocation rejection, multi-order webhook isolation & prioritized correlation, polling fallback capture lifecycle, digital signature tamper detection, and canonical agreement hash recalculation.

---

## 🔑 Configuration & Zero-Key Demo Mode

NexusCommerce AI includes a toggleable **Zero-Key Demo Mode**:
- **Zero-Key Demo Mode (Default `True`)**:
  - Evaluators can test every feature without any API keys.
  - Simulates PayPal REST API v2 responses, authorizations, captures, and webhooks deterministically.
  - Uses the Channel3 Retail B2B catalog with real-world enterprise hardware items.
- **Live Mode**:
  - Set `PAYPAL_CLIENT_ID` and `PAYPAL_CLIENT_SECRET` in environment variables.
  - Set `CHANNEL3_API_KEY` for live Channel3 product search.
  - Toggle live mode via the dashboard header or `POST /api/demo/toggle-mode?enabled=false`.

---

## 📁 Repository Structure

```
nexuscommerce/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── procure_bot.py       # Autonomous Buyer Procurement Agent
│   │   │   └── vendor_bot.py        # Autonomous Supplier Sales Agent
│   │   ├── api/
│   │   │   ├── analytics.py         # AG Studio & AG Grid Spend Intelligence
│   │   │   ├── demo.py              # Zero-Key Demo Lifecycle Runner
│   │   │   ├── escrow.py            # PayPal Milestone Authorization & Capture Endpoints
│   │   │   ├── evidence.py          # Evidence Bundle Viewer & Verification
│   │   │   ├── mandates.py          # Procurement Mandate Management
│   │   │   ├── negotiate.py         # Multi-Agent Negotiation & HITL Holds
│   │   │   └── webhooks.py          # PayPal Webhooks First Receiver & Simulator
│   │   ├── core/
│   │   │   ├── evidence_bundle.py   # Immutable Audit Trail & Merkle Root Sealer
│   │   │   ├── orchestrator.py      # Core System Coordinator
│   │   │   ├── policy_engine.py     # Deterministic Gatekeeper ("Code Decides")
│   │   │   └── polling_service.py   # Webhook Polling Fallback Reconciler
│   │   ├── models/
│   │   │   ├── escrow.py            # EscrowOrder & EscrowMilestone State Machine Models
│   │   │   ├── evidence.py          # EvidenceBundle Cryptographic Model
│   │   │   ├── mandate.py           # ProcurementMandate Model
│   │   │   └── negotiation.py       # Proposals, Sessions, & Agreements
│   │   ├── providers/
│   │   │   ├── channel3_provider.py # Channel3 Retail Search Provider
│   │   │   └── paypal_provider.py   # PayPal REST API v2 + Zero-Key Mock
│   │   └── main.py                  # FastAPI Application Entrypoint
│   ├── tests/                       # Complete Pytest Suite (22 passing tests)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AGStudioSpendGrid.jsx    # AG Studio / AG Grid Spend Table
│   │   │   ├── EvidenceBundleViewer.jsx # Dispute Audit & Tamper Tester
│   │   │   ├── MandateConfigModal.jsx   # Mandate Creator & Digital Signer
│   │   │   ├── MilestoneTimeline.jsx    # 3-Stage PayPal Authorization & Capture Timeline
│   │   │   ├── Navbar.jsx               # Header & Mode Toggles
│   │   │   ├── NegotiationView.jsx      # Agent Transcript & HITL Bar
│   │   │   └── ZeroKeyDemoPanel.jsx     # 1-Click Demo Evaluation Panel
│   │   ├── services/
│   │   │   └── api.js                   # REST API Client
│   │   ├── App.jsx                      # Main Dashboard
│   │   ├── index.css                    # Tailwind + AG Grid Alpine Dark
│   │   └── main.jsx
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
├── start.sh                         # 1-Click Startup Script
└── README.md
```

---

## 🏆 Hackathon Alignment Summary

| Requirement / Prize Track | Implementation | Verification |
|---|---|---|
| **Autonomous Commerce Agents** | `ProcureBot` & `VendorBot` negotiating volume, warranty, and pricing within strict mandate boundaries. | Tested in `test_zero_key_demo.py` |
| **"Code Decides, LLM Proposes"** | Deterministic `PolicyEngine` sole gatekeeper to PayPal API. Corrupt or out-of-bounds proposals drop to HITL hold. | Tested in `test_policy_engine.py` |
| **PayPal Two-Step Authorization & Milestone Captures** | 3-stage milestone state machine on PayPal REST API v2 (29-day authorization hold -> 30% mobilization partial capture -> 70% delivery capture). | Tested in `test_escrow_and_evidence.py` |
| **Webhooks First, Polling Fallback** | PayPal webhook receivers (`CHECKOUT.ORDER.APPROVED`, etc.) with `PollingFallbackService`. | Tested in `test_zero_key_demo.py` |
| **Evidence Bundle & Dispute Defense** | Immutable audit trail with SHA-256 agreement hash and Merkle root seal. | Tested in `test_escrow_and_evidence.py` |
| **AG Studio / AG Grid ($5,000 Prize)** | Full AG Grid self-serve spend analytics table with alpha KPI metrics and CSV exports. | Integrated in UI & `/api/analytics` |
| **Zero-Key Demo Mode** | Full end-to-end evaluation with zero credentials required. | Tested in `test_zero_key_demo.py` |

---

Built with ❤️ for the **PayPal AI Hackathon 2026**.

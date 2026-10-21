import pytest
from app.core.orchestrator import NexusOrchestrator
from app.api.mandates import MANDATE_TEMPLATES
from app.api.analytics import get_comparative_runs, get_negotiation_metrics
from app.api.evidence import export_bundle_json, export_bundle_html_report
from fastapi.responses import JSONResponse, HTMLResponse
import json


@pytest.fixture
def orchestrator():
    return NexusOrchestrator()


@pytest.mark.asyncio
async def test_mandate_templates(orchestrator):
    assert len(MANDATE_TEMPLATES) >= 3
    ids = [t["id"] for t in MANDATE_TEMPLATES]
    assert "TEMPLATE-AI-GPUS" in ids
    assert "TEMPLATE-DEFENSE-HW" in ids
    assert "TEMPLATE-OFFICE-REFRESH" in ids
    for t in MANDATE_TEMPLATES:
        assert t["max_unit_price"] > 0
        assert t["max_total_budget"] > 0
        assert t["quantity"] > 0

        # Execute autonomous negotiation for template and verify agreement reached under cap
        mandate = orchestrator.create_mandate({
            "title": t["title"],
            "item_name": t["item_name"],
            "quantity": t["quantity"],
            "max_unit_price": t["max_unit_price"],
            "max_total_budget": t["max_total_budget"],
            "target_categories": t.get("target_categories", ["Enterprise Hardware"]),
        })
        session = await orchestrator.run_autonomous_negotiation(mandate.id)
        assert session.status.value == "AGREEMENT_REACHED", f"Template {t['id']} failed negotiation: {session.hitl_reason}"
        assert session.agreement.final_unit_price <= t["max_unit_price"]
        assert session.agreement.final_total <= t["max_total_budget"]


@pytest.mark.asyncio
async def test_comparative_runs_and_metrics(orchestrator):
    runs_res = await get_comparative_runs(orchestrator)
    assert "runs" in runs_res
    assert runs_res["count"] >= 3
    run_tags = [r["tag"] for r in runs_res["runs"]]
    assert "Happy Path" in run_tags
    assert "HITL Hold" in run_tags
    assert "Strict Policy" in run_tags

    # Now run an adversarial session to trigger HITL hold, and verify it appears in comparative runs
    adv_mandate = orchestrator.create_mandate({
        "item_name": "NexusEdge Pro 100G Modular Edge Router",
        "quantity": 50,
        "max_unit_price": 1200.0,
        "max_total_budget": 60000.0,
    })
    adv_session = await orchestrator.run_autonomous_negotiation(adv_mandate.id, simulate_violation="PRICE_SPIKE")
    assert adv_session.status.value == "HITL_HOLD"

    updated_runs = await get_comparative_runs(orchestrator)
    updated_tags = [r["tag"] for r in updated_runs["runs"]]
    assert "Live HITL Hold" in updated_tags

    metrics_res = await get_negotiation_metrics(orchestrator)
    assert "trajectory" in metrics_res
    assert "kpis" in metrics_res
    assert len(metrics_res["trajectory"]) >= 3
    assert metrics_res["kpis"]["average_rounds_to_consensus"] > 0


@pytest.mark.asyncio
async def test_evidence_export_endpoints(orchestrator):
    # Verify export on empty orchestrator with 'latest' works via seed benchmark bundle
    fresh_orch = NexusOrchestrator()
    fresh_export = await export_bundle_json("latest", fresh_orch)
    assert fresh_export.status_code == 200

    # Run a full negotiation and escrow authorization to produce an evidence bundle
    mandate = orchestrator.create_mandate({
        "item_name": "NexusEdge Pro 100G Modular Edge Router",
        "quantity": 50,
        "max_unit_price": 1200.0,
        "max_total_budget": 60000.0,
    })
    session = await orchestrator.run_autonomous_negotiation(mandate.id)
    order, bundle = await orchestrator.finalize_agreement_and_authorize_escrow(session.session_id)
    # Advance to shipment and delivery so bundle receives complete dispute defense proof
    order, bundle = await orchestrator.advance_to_shipment_milestone(order.order_id, carrier_name="FedEx Priority Freight")
    order, bundle = await orchestrator.advance_to_delivery_and_capture(order.order_id)

    # Test JSON export
    json_resp = await export_bundle_json(bundle.bundle_id, orchestrator)
    assert isinstance(json_resp, JSONResponse)
    body = json.loads(json_resp.body.decode("utf-8"))
    assert body["export_metadata"]["bundle_id"] == bundle.bundle_id
    assert body["export_metadata"]["dispute_defense_grade"] == "A+"
    assert body["cryptographic_verification"]["merkle_root_sha256"] == bundle.bundle_root_hash
    assert body["negotiated_agreement"]["final_unit_price"] <= 1200.0
    assert body["carrier_proof"] is not None
    assert body["paypal_capture_receipt"] is not None

    # Test HTML report export
    html_resp = await export_bundle_html_report(bundle.bundle_id, orchestrator)
    assert isinstance(html_resp, HTMLResponse)
    assert "Compliance Audit Certificate" in html_resp.body.decode("utf-8")
    assert bundle.bundle_id in html_resp.body.decode("utf-8")

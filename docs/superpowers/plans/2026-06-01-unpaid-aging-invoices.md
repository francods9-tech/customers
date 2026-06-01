# Unpaid Aging Invoices Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show all pending invoices per unpaid customer and classify unpaid customers by age without counting them as churn.

**Architecture:** Keep billing state separate from churn. Stripe invoices feed normalized invoice lists into the snapshot; `customer_rules.py` computes the operational unpaid bucket used by summaries and templates.

**Tech Stack:** Flask, Jinja templates, Stripe Python SDK, unittest.

---

### Task 1: Rules And Tests

**Files:**
- Modify: `tests/test_customer_rules.py`
- Modify: `customer_rules.py`

- [ ] Write failing tests for `unpaid_summary` with multiple invoices and for `unpaid_operational_status` at 29, 30, and 90 days.
- [ ] Run `.\.venv\Scripts\python.exe -m unittest tests.test_customer_rules -v` and confirm the tests fail because the helpers do not exist or do not return the new fields.
- [ ] Implement the helpers in `customer_rules.py`.
- [ ] Re-run the same test module and confirm it passes.

### Task 2: Stripe Invoice Collection

**Files:**
- Modify: `tests/test_stripe_unpaid.py`
- Modify: `sync/stripe_unpaid.py`
- Modify: `sync/snapshot.py`

- [ ] Write failing tests proving `merge_unpaid_details` stores `facturas_pendientes`, total pending amount, oldest invoice date, and latest invoice link.
- [ ] Run `.\.venv\Scripts\python.exe -m unittest tests.test_stripe_unpaid -v` and confirm the test fails.
- [ ] Implement normalized pending invoice payloads for partial Stripe refresh and full snapshot refresh.
- [ ] Re-run the Stripe unpaid tests and confirm they pass.

### Task 3: UI Surfacing

**Files:**
- Modify: `templates/bandeja.html`
- Modify: `templates/clientes.html`
- Modify: `templates/ficha.html`
- Modify: `static/style.css`

- [ ] Render invoice count, total pending amount, oldest age label, and invoice links where unpaid data appears.
- [ ] Add badge styles for `pausado_impago` and `inactivo_impago`.
- [ ] Keep `Bajas` untouched; do not add unpaid ageing rows to churn.

### Task 4: Verification And Release

**Files:**
- Modify: `status.md`

- [ ] Run `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`.
- [ ] Run `.\.venv\Scripts\python.exe -c "from app import app; print('imports ok', len(list(app.url_map.iter_rules())))"`.
- [ ] Run authenticated local HTTP checks for `/`, `/clientes?estado=impago`, `/bandeja`.
- [ ] Update `status.md` with commands, results, and open risk.
- [ ] Commit, push, open PR, merge to `main`, and deploy Railway.

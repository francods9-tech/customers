"""Cash-based monthly finance summary.

Mercury is the source of truth for recognized cash income. Stripe explains the
reconciliation only: gross collected, fees, net and payouts.
"""
import datetime as dt
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

import stripe


def month_bounds(month):
    start = dt.datetime.strptime(month, "%Y-%m").replace(tzinfo=dt.timezone.utc)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1)
    else:
        end = start.replace(month=start.month + 1)
    return start, end


def cents_to_money(value):
    return round((value or 0) / 100, 2)


def money(value):
    return round(float(value or 0), 2)


def _txn_amount(transaction):
    amount = transaction.get("amount", 0)
    if isinstance(amount, dict):
        amount = amount.get("amount", 0)
    return float(amount or 0)


def _txn_account_id(transaction):
    return (
        transaction.get("account_id")
        or transaction.get("accountId")
        or transaction.get("account")
        or transaction.get("bank_account_id")
        or ""
    )


def _txn_status(transaction):
    return (transaction.get("status") or transaction.get("state") or "").lower()


def _txn_description(transaction):
    return " ".join(
        str(transaction.get(key) or "")
        for key in ("description", "note", "counterparty_name", "counterpartyName", "merchant_name")
    ).lower()


def _account_id(account):
    return str(account.get("id") or account.get("_id") or account.get("account_id") or "")


def _account_name(account):
    return str(account.get("name") or account.get("nickname") or account.get("legalBusinessName") or "")


def _is_sky_account(account):
    return "sky reputation" in _account_name(account).lower()


def _is_internal_transfer(transaction, own_account_ids, own_account_names):
    counterparty_id = str(transaction.get("counterparty_account_id") or transaction.get("counterpartyAccountId") or "")
    if counterparty_id and counterparty_id in own_account_ids:
        return True
    description = _txn_description(transaction)
    return any(name and name in description for name in own_account_names)


def _transaction_row(transaction, account_by_id):
    account_id = _txn_account_id(transaction)
    return {
        "id": transaction.get("id") or transaction.get("_id") or "",
        "date": transaction.get("date") or transaction.get("postedAt") or transaction.get("createdAt") or "",
        "account_id": account_id,
        "account_name": _account_name(account_by_id.get(account_id, {})),
        "description": transaction.get("description") or transaction.get("note") or "",
        "amount": money(_txn_amount(transaction)),
    }


def calculate_mercury_cash_income(transactions, accounts):
    own_account_ids = {_account_id(account) for account in accounts if _account_id(account)}
    own_account_names = {
        _account_name(account).lower()
        for account in accounts
        if _account_name(account) and not _is_sky_account(account)
    }
    account_by_id = {_account_id(account): account for account in accounts}
    sky_account_ids = {_account_id(account) for account in accounts if _is_sky_account(account)}

    included = []
    excluded = {"sky_reputation": [], "internal_transfers": [], "non_income": []}
    for transaction in transactions:
        amount = _txn_amount(transaction)
        status = _txn_status(transaction)
        account_id = _txn_account_id(transaction)
        row = _transaction_row(transaction, account_by_id)

        if account_id in sky_account_ids or "sky reputation" in _txn_description(transaction):
            excluded["sky_reputation"].append(row)
            continue
        if amount <= 0 or (status and status not in {"sent", "posted", "completed", "paid"}):
            excluded["non_income"].append(row)
            continue
        if _is_internal_transfer(transaction, own_account_ids, own_account_names):
            excluded["internal_transfers"].append(row)
            continue
        included.append(row)

    return {
        "mercury_cash_income": money(sum(row["amount"] for row in included)),
        "mercury_income_detail": included,
        "mercury_internal_transfers": excluded["internal_transfers"],
        "excluded": excluded,
        "source_status": "ok",
    }


def calculate_mercury_expenses(transactions, accounts):
    account_by_id = {_account_id(account): account for account in accounts}
    own_account_ids = set(account_by_id)
    own_account_names = {
        _account_name(account).lower()
        for account in accounts
        if _account_name(account) and not _is_sky_account(account)
    }
    rows = []
    for transaction in transactions:
        amount = _txn_amount(transaction)
        if amount >= 0:
            continue
        if _is_internal_transfer(transaction, own_account_ids, own_account_names):
            continue
        rows.append(_transaction_row(transaction, account_by_id))
    return {"expenses": money(abs(sum(row["amount"] for row in rows))), "expense_detail": rows}


def calculate_stripe_financials(balance_transactions, payouts):
    gross = fee = net = 0
    for item in balance_transactions:
        gross += item.get("amount", 0) or 0
        fee += item.get("fee", 0) or 0
        net += item.get("net", 0) or 0
    payout_total = sum(item.get("amount", 0) or 0 for item in payouts)
    return {
        "stripe_gross_income": cents_to_money(gross),
        "stripe_fees": cents_to_money(fee),
        "stripe_net": cents_to_money(net),
        "stripe_payouts": cents_to_money(payout_total),
        "source_status": "ok",
    }


def build_financial_summary(month, mercury=None, stripe=None, manual_adjustments=0, expenses=0):
    mercury = mercury or {}
    stripe = stripe or {}
    mercury_status = mercury.get("source_status") or "missing"
    stripe_status = stripe.get("source_status") or "missing"
    cash_income = money(mercury.get("mercury_cash_income", 0))
    manual_adjustments = money(manual_adjustments)
    expenses = money(expenses or mercury.get("expenses", 0))
    income = cash_income + manual_adjustments if mercury_status != "missing" else manual_adjustments
    stripe_net = money(stripe.get("stripe_net", 0))
    stripe_payouts = money(stripe.get("stripe_payouts", 0))
    gap = money(stripe_payouts - cash_income) if mercury_status != "missing" and stripe_status != "missing" else None

    return {
        "month": month,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "totals": {
            "income": money(income),
            "expenses": expenses,
            "net_result": money(income - expenses),
        },
        "saas": {
            "mrr": money(stripe.get("mrr", 0)),
            "active_customers": int(stripe.get("active_customers", 0) or 0),
        },
        "reconciliation": {
            "stripe_gross_income": money(stripe.get("stripe_gross_income", 0)),
            "stripe_fees": money(stripe.get("stripe_fees", 0)),
            "stripe_net": stripe_net,
            "stripe_payouts": stripe_payouts,
            "mercury_cash": cash_income,
            "manual_adjustments": manual_adjustments,
            "gap": gap,
        },
        "details": {
            "mercury_income": mercury.get("mercury_income_detail", []),
            "mercury_internal_transfers": mercury.get("mercury_internal_transfers", []),
            "expenses": mercury.get("expense_detail", []),
        },
        "sources": {
            "income": mercury_status if mercury_status != "missing" else ("ok" if manual_adjustments else "missing"),
            "mercury": mercury_status,
            "stripe": stripe_status,
        },
    }


class MercuryApiClient:
    def __init__(self, token=None, base_url=None):
        self.token = token or os.environ.get("MERCURY_API_TOKEN", "")
        self.base_url = (base_url or os.environ.get("MERCURY_API_BASE_URL") or "https://api.mercury.com/api/v1").rstrip("/")

    def _get(self, path, params=None):
        if not self.token:
            raise RuntimeError("MERCURY_API_TOKEN missing")
        query = f"?{urllib.parse.urlencode(params or {})}" if params else ""
        req = urllib.request.Request(
            f"{self.base_url}{path}{query}",
            headers={"Authorization": f"Bearer {self.token}", "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    def list_accounts(self):
        payload = self._get("/accounts")
        return payload.get("accounts") or payload.get("data") or []

    def list_transactions(self, account_id, start, end):
        payload = self._get(
            f"/account/{account_id}/transactions",
            {"start": start.date().isoformat(), "end": end.date().isoformat()},
        )
        return payload.get("transactions") or payload.get("data") or []

    def monthly_transactions(self, month):
        start, end = month_bounds(month)
        accounts = self.list_accounts()
        included_accounts = [account for account in accounts if not _is_sky_account(account)]
        transactions = []
        for account in included_accounts:
            account_id = _account_id(account)
            if account_id:
                transactions.extend(self.list_transactions(account_id, start, end))
        return accounts, transactions


def fetch_mercury_month(month, client=None):
    client = client or MercuryApiClient()
    try:
        accounts, transactions = client.monthly_transactions(month)
    except Exception as exc:
        return {"source_status": "missing", "error": str(exc), "mercury_cash_income": 0}
    income = calculate_mercury_cash_income(transactions, accounts)
    expenses = calculate_mercury_expenses(transactions, accounts)
    return income | expenses


def fetch_stripe_month(month, stripe_key=None):
    stripe_key = stripe_key or os.environ.get("STRIPE_SECRET_KEY", "")
    if not stripe_key:
        return {"source_status": "missing", "error": "STRIPE_SECRET_KEY missing"}
    stripe.api_key = stripe_key
    start, end = month_bounds(month)
    created = {"gte": int(start.timestamp()), "lt": int(end.timestamp())}
    try:
        balance_transactions = [
            item.to_dict() if hasattr(item, "to_dict") else dict(item)
            for item in stripe.BalanceTransaction.list(created=created, limit=100).auto_paging_iter()
            if (getattr(item, "type", None) or item.get("type")) in {"charge", "payment", "refund", "adjustment"}
        ]
        payouts = [
            item.to_dict() if hasattr(item, "to_dict") else dict(item)
            for item in stripe.Payout.list(created=created, limit=100).auto_paging_iter()
        ]
    except Exception as exc:
        return {"source_status": "missing", "error": str(exc)}
    return calculate_stripe_financials(balance_transactions, payouts)


def saas_metrics_from_snapshot(product_snapshot):
    if not product_snapshot:
        return {"mrr": 0, "active_customers": 0, "source_status": "missing"}
    clientes = product_snapshot.get("clientes", [])
    active = [c for c in clientes if c.get("estado") == "activo"]
    return {
        "mrr": money(product_snapshot.get("stripe_metrics", {}).get("mrr", 0)),
        "active_customers": len(active),
        "source_status": "ok",
    }


def snapshot_path(data_dir, month):
    return Path(data_dir) / f"income_{month}.json"


def load_monthly_snapshot(data_dir, month):
    path = snapshot_path(data_dir, month)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_monthly_snapshot(data_dir, summary):
    path = snapshot_path(data_dir, summary["month"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return path

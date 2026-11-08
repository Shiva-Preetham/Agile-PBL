# Module 8 — Refactoring in Agile + Retrospective

> **Syllabus link:** Module 8, *Refactoring in Agile* (CO5)
> **Rule:** refactoring changes the *structure* of code, never its *behaviour*. The 106 automated tests are our safety net.

## 1. Code smells found in the prototype

We reviewed our own Prototype v0.1 code and found these real smells:

| # | Smell | Where | Refactoring technique | Status |
|---|---|---|---|---|
| 1 | **Duplicate Code**: look up a customer and run SHAP, repeated in two endpoints | `backend/app/routers/customers.py` | Extract Method | ✅ Done (example below) |
| 2 | **Duplicate Code** across layers: the 10 customer fields and their ranges are listed in the backend *and* again in the what-if form | `frontend/src/views/ModelView.tsx` vs `backend/app/services/fields.py` | Add a `GET /api/model/fields` endpoint; build the form from it | 📋 Sprint 4 |
| 3 | **Magic numbers**: risk thresholds "40% / 70%" hard-coded in UI text | `Dashboard.tsx`, `CustomerDetail.tsx` | Replace with values from `/api/model/metrics` (`risk_thresholds`) | 📋 Sprint 4 |
| 4 | **Long Method**: `summarize()` builds six different statistics in one function | `backend/app/services/dashboard.py` | Extract Method (`_count_by_risk`, `_count_actions`, `_risk_by_contract`) | 📋 Sprint 4 |
| 5 | **Duplicate Code** in tests: the `features()` helper is defined in two test files | `test_prediction.py`, `test_api_prediction.py` | Move to `conftest.py` | 📋 Sprint 4 |

## 2. Before / after example (smell #1)

**Before:** the same two lines appear in both endpoints.

```python
@router.get("/{customer_id}/explanation")
def get_explanation(customer_id, top, db):
    customer = _find(db, customer_id)
    explanation = explain(customer_service.to_frame(customer))[0]   # duplicated
    ...

@router.get("/{customer_id}/recommendation")
def get_recommendation(customer_id, db):
    customer = _find(db, customer_id)
    explanation = explain(customer_service.to_frame(customer))[0]   # duplicated
    ...
```

**After:** one well-named helper (Extract Method).

```python
def _find_and_explain(db, customer_id) -> tuple[Customer, Explanation]:
    """Look up a stored customer and explain their current prediction."""
    customer = _find(db, customer_id)
    return customer, explain(customer_service.to_frame(customer))[0]

@router.get("/{customer_id}/explanation")
def get_explanation(customer_id, top, db):
    customer, explanation = _find_and_explain(db, customer_id)
    ...

@router.get("/{customer_id}/recommendation")
def get_recommendation(customer_id, db):
    customer, explanation = _find_and_explain(db, customer_id)
    ...
```

| Check | Before | After |
|---|---|---|
| pytest | 106 passed | 106 passed |
| flake8 | clean | clean |
| Behaviour | unchanged | unchanged |

Commit: `refactor: extract _find_and_explain to remove duplicated lookup + SHAP code`

**In VS Code:** select the duplicated lines → right-click → *Refactor…* → **Extract Method**. Rename with **F2** to update every usage safely.

## 3. Sprint retrospective

Format: **Start / Stop / Continue**. The team fills this in together after each Sprint Review.

### Prototype v0.1 retrospective (draft: the team should confirm or change it)

| Start | Stop | Continue |
|---|---|---|
| Automated tests for the React UI (a chart-order bug was found only by manual testing) | Duplicating the same lists in frontend and backend (smells #2 and #3) | Writing tests first: every sprint ended green |
| Using the Kanban board on GitHub Projects every day | | Small commits with clear messages, pushed after each step |
| Logging pairing sessions | | Spikes for risky new libraries (the SHAP spike saved time) |

### Retrospective action items

| Action | Owner | Due |
|---|---|---|
| Fix smells #2–#5 (US12) | | Sprint 4 |
| Add faculty feedback to the backlog as new stories | Product Owner | Right after the review |
| | | |

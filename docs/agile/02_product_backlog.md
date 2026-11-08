# Module 2 — Agile Manifesto & Product Backlog

> **Syllabus link:** Module 2, *Agile Manifesto & User Stories* (CO1)
> Stories are written in the standard **"As a … I want … so that …"** format, checked against **INVEST**, ordered by priority, and each one has measurable acceptance criteria.

## How ChurnSense follows the Agile Manifesto

| Manifesto value | What we do in ChurnSense |
|---|---|
| **Individuals and interactions** over processes and tools | Pair programming; a two-person team with daily stand-ups |
| **Working software** over comprehensive documentation | Every sprint ends with a demo-able increment (Prototype v0.1 is already runnable) |
| **Customer collaboration** over contract negotiation | Faculty feedback at every Sprint Review becomes new backlog items |
| **Responding to change** over following a plan | The backlog is re-ordered after each review; sprint scope is negotiable |

## Personas

- **Analyst**: uploads customer data, inspects profiles, interprets predictions.
- **Customer Retention Manager**: prioritizes follow-ups and tracks retention actions.
- **Tester / Developer**: keeps quality high through automated tests, CI and refactoring.

## Product Backlog (ordered by priority)

SP = story points (relative estimate, Fibonacci scale). Priority uses **MoSCoW**: Must / Should / Could.

| ID | User story | Priority | SP | Sprint | Status |
|---|---|---|---|---|---|
| US01 | As an **Analyst**, I want to upload a customer CSV so that I can analyze customer records. | Must | 5 | S1 | ✅ Prototype |
| US02 | As an **Analyst**, I want to search and filter customers so that I can find relevant records quickly. | Must | 3 | S1 | ✅ Prototype |
| US03 | As an **Analyst**, I want to view an individual customer profile so that I can review key attributes before assessing risk. | Must | 3 | S1 | ✅ Prototype |
| US04 | As an **Analyst**, I want a churn probability for a customer so that I can estimate the likelihood of churn. | Must | 5 | S2 | ✅ Prototype |
| US05 | As a **Retention Manager**, I want a Low, Medium or High risk category so that I can prioritize follow-up. | Must | 2 | S2 | ✅ Prototype |
| US06 | As an **Analyst**, I want to review model-evaluation metrics so that I can understand prediction quality. | Should | 3 | S2 | ✅ Prototype |
| US07 | As an **Analyst**, I want to see the main factors behind a churn prediction so that I can interpret the result. | Must | 5 | S3 | ✅ Prototype |
| US08 | As a **Retention Manager**, I want a suggested retention action so that I can decide on a suitable next step. | Should | 3 | S3 | ✅ Prototype |
| US09 | As a **Retention Manager**, I want to update a retention-action status so that follow-up can be tracked. | Should | 3 | S3 | ✅ Prototype |
| US10 | As a **Retention Manager**, I want a dashboard summary of churn risk so that I can understand the overall customer portfolio. | Should | 3 | S3 | ✅ Prototype |
| US11 | As a **Tester**, I want automated unit and integration tests so that defects are detected before release. | Must | 5 | S4 | ✅ 106 tests |
| US12 | As a **Developer**, I want to refactor identified code smells so that the codebase remains maintainable. | Should | 3 | S4 | 🟡 1 of 5 smells fixed |
| US13 | As a **Developer**, I want CI to run tests on pushes and pull requests so that regressions are caught early. | Must | 3 | S4 | ✅ CI green |
| | **Total** | | **46** | | |

## Acceptance criteria

| ID | Acceptance criteria (measurable) | Automated test |
|---|---|---|
| US01 | A valid file with required columns is accepted; missing columns or unreadable rows produce a clear error. | `test_validation.py` |
| US02 | Search by customer ID and attribute filters work; no matches display an empty state. | `test_api.py::test_search_*` |
| US03 | Selected attributes and activity/usage metrics display; unknown IDs return a clear not-found result. | `test_api.py::test_profile_*` |
| US04 | Valid inputs return a probability from 0 to 1; missing/invalid features are handled clearly; same model and input give reproducible output. | `test_prediction.py` |
| US05 | Documented thresholds classify scores consistently; boundary values map to exactly one category and appear with the probability. | `test_risk.py` |
| US06 | Holdout metrics (precision, recall, F1, ROC-AUC) are labeled clearly; training metrics are not shown as holdout results. | `test_api.py::test_model_metrics_*` |
| US07 | SHAP shows the top contributing factors for the selected customer; the explanation matches that customer and model output. | `test_explain.py` |
| US08 | A documented rule returns an action based on risk/factors, or a safe fallback; suggestions are marked for human review. | `test_recommend.py` |
| US09 | Pending → Contacted → Completed transitions are allowed as defined; status persists; invalid values are rejected. | `test_actions.py`, `test_api.py` |
| US10 | Total customers and risk counts reflect stored records; filters update results; empty data does not break the dashboard. | `test_api.py::test_dashboard_*` |
| US11 | Tests cover validation, risk, prediction, recommendation rules and key API flows; one documented command runs them. | `pytest` |
| US12 | At least one real smell is refactored; duplicated or oversized logic is improved; tests still pass. | Before/after in `08_refactoring_and_retro.md` |
| US13 | GitHub Actions runs tests and style checks; failures are visible and not silently ignored. | `.github/workflows/ci.yml` |

## INVEST check (sample)

| Letter | Meaning | Example from our backlog |
|---|---|---|
| **I**ndependent | Can be built on its own | US05 (risk category) only needs a probability value |
| **N**egotiable | Details can be discussed | US08 rules can change after faculty feedback |
| **V**aluable | Gives value to a user | US07 tells the analyst *why* a customer may leave |
| **E**stimable | The team can size it | Every story has story points |
| **S**mall | Fits in one sprint | Largest story is 5 SP; sprints hold 10–14 SP |
| **T**estable | Has measurable acceptance criteria | Each story maps to an automated test file |

## Backlog on a board tool

The syllabus asks for a board on **Trello / GitHub Projects**. Each row above becomes one card. Columns and WIP limits are in [06_kanban_and_crystal.md](06_kanban_and_crystal.md).

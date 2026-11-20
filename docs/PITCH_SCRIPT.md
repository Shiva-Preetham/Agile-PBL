# ChurnSense: 7-Minute Presentation Script

**Speakers:** Shiva Preetham Chelimila (Product Owner) and Artham Kumar (Scrum Master)
**Live app:** https://churnsense-one.vercel.app  **Repo:** https://github.com/Shiva-Preetham/Agile-PBL

## Before you walk in (5 minutes before)

- Open **https://churnsense-one.vercel.app** about 2 minutes early. The free server sleeps when idle and shows "Waking up the server…" for up to a minute; let it load once.
- Keep these tabs open, in order: **1)** the live app (Dashboard), **2)** the GitHub repo **commits** page, **3)** GitHub **Actions** page, **4)** the report PDF.
- Backup if Wi-Fi fails: run it locally (README → "Run it locally"), or show the screenshots in Chapter 3 of the report.
- **Don't click "Mark as Contacted" on the live site** unless you want that change to stay. It's permanent.

## Timing at a glance

| Time | Who | Part |
|---|---|---|
| 0:00–1:00 | Shiva | Opening + problem |
| 1:00–2:30 | Shiva | Agile process (backlog, sprints, Kanban) |
| 2:30–5:00 | Artham | Live demo |
| 5:00–6:15 | Artham | TDD, tests, CI/CD, deployment, refactoring |
| 6:15–7:00 | Shiva | Results + close |

---

## 1. Opening + problem (Shiva, 1 minute)

> "Good morning, ma'am/sir. We are Group 3: I'm Shiva Preetham, the Product Owner, and this is Artham Kumar, our Scrum Master. Our project is **ChurnSense: Explainable Churn Prediction**.
>
> Companies like telecom and internet providers lose customers every month; this is called **churn**. They have the data, but they usually get a churn score with no reason behind it, and no guidance on what to do.
>
> ChurnSense does three things: it **predicts** who is likely to leave, **explains why** in plain language, and suggests the **Next Best Action** to keep that customer, then tracks the follow-up."

## 2. Agile process (Shiva, 1.5 minutes)

*(Point to the report's Figure 2.1 or the README if needed.)*

> "We built it the Agile way, as the syllabus requires.
>
> - First we compared **Waterfall vs Agile** for the same project. Waterfall gives working software only at week 14; Scrum gives a working increment every sprint, so we could take your feedback early.
> - We wrote **15 user stories** in the 'As a… I want… so that…' format, with acceptance criteria, estimated them with **Planning Poker** in story points: **54 story points** in total.
> - We delivered them in **4 Scrum sprints**: customer data, then prediction, then explanations and actions, then quality and release. Our average **velocity was 13.5 story points** per sprint.
> - After the prototype review we **added two new stories**, Next Best Action and online hosting. That is Agile responding to change: the scope grew from 46 to 54 points.
> - We tracked work on a **Kanban board with a WIP limit of 2** in progress. Under Crystal, we are **Crystal Clear, D6**.
>
> Artham will now show you the working product."

## 3. Live demo (Artham, 2.5 minutes)

**Dashboard (30 s)**
> "This is live on the internet: frontend on **Vercel**, backend and **PostgreSQL** database on **Render**. It has 250 demo customers: 33 High risk, 47 Medium, 170 Low. Month-to-month contracts carry most of the risk."

**Customers → validation (30 s)**
*(Customers tab; type "100" in search, then pick "High" in the risk filter.)*
> "Analysts can search and filter. When a CSV is uploaded, every row is validated: if a row has text in a number field or an unknown contract type, the system shows the exact row and column and saves nothing." *(Mention it; show Figure 3.6 in the report if asked.)*

**Customer detail (1 min): the key moment**
*(Dashboard → click the top customer, CS-10005.)*
> "This customer has a **98% churn probability**. Why? The **SHAP** chart shows the biggest reason: **51 days since the last login**.
>
> Next Best Action: the system tries every retention action on a **copy** of the customer and asks the model again. A re-engagement campaign helps most: **98% to 83%**.
> The **retention plan** below shows that three actions together, re-engagement, a 12-month contract and a loyalty discount, bring the customer down to **39%, Low risk**.
> Every suggestion is marked **'needs human review'**: the system advises, a person decides."

**Model page (30 s)**
*(Model tab; change Contract type to "Two year" in the What-if form.)*
> "We test the model on 600 customers it never saw: **ROC-AUC 0.83**. And in the what-if form, changing only the contract to two years drops the risk from 96% to 76%."

## 4. Testing, CI/CD, refactoring (Artham, 1.25 minutes)

*(GitHub commits page, then the Actions page.)*
> "We followed **Test-Driven Development**. In our commit history you can see it for every feature: first a **RED** commit where the tests fail, then a **GREEN** commit where the code passes.
> We have **146 automated tests**. On every push, **GitHub Actions** runs style checks, all tests on SQLite **and** on a real PostgreSQL database, and builds the frontend. **Render only deploys when everything is green**, so broken code never reaches the live site.
> In Sprint 4 we found **five code smells**, such as duplicate code, a long method and magic numbers, and refactored all of them with techniques like **Extract Method** and **Move Function**. The tests passed before and after, so the behaviour didn't change."

## 5. Results + close (Shiva, 45 seconds)

> "To summarise: all **15 user stories, 54 story points**, are done; **146 tests** pass; the model reaches **0.83 ROC-AUC**; and the Next Best Action plans bring **79 of 80** at-risk customers down to Low risk according to the model. It is **deployed online** and documented in our 40-page report, with UML diagrams and the use of OOP concepts.
>
> Our honest limitations: the data is synthetic, and the what-if results are model estimates, not proof. Next we would use real data and test the actions with A/B tests.
>
> Thank you. We're happy to take your questions."

---

## Likely questions: who answers

| Question | Who | Short answer |
|---|---|---|
| Where is the data from? | Shiva | Synthetic, generated by our script with a fixed seed: no privacy issues, reproducible. A real dataset can be plugged in without code changes. |
| What is SHAP, simply? | Shiva | It splits a prediction into how much each field pushed the score up or down, and the parts always add up to the model's answer. We test that. |
| Why XGBoost? | Shiva | Strong on table data, fast on a normal CPU, and works with exact SHAP explanations. |
| Why 40% and 70% thresholds? | Shiva | Documented business rules, easy to change, tested exactly at the boundary values (0.40 → Medium, 0.70 → High). |
| Recall is only 0.54? | Shiva | At a 0.5 cut-off some churners are missed, but ranking quality (ROC-AUC 0.83) is good, so lowering the threshold catches more at the cost of more false alarms. |
| How is Next Best Action decided? | Shiva | Change a copy of the customer as the action would, re-score it, and pick the biggest drop; the plan repeats this until Low risk. |
| Does it prove the action works? | Shiva | No, it's a model estimate, labelled as such, with human review. A/B tests are the next step. |
| How did you do TDD? | Artham | Tests committed first and failing (RED), then code (GREEN); visible in the commits and CI history. |
| What does CI do? | Artham | On every push: flake8, 146 tests on SQLite and PostgreSQL, frontend build. Render deploys only if all pass. |
| Where is OOP used? | Artham | Classes like ChurnPredictor (encapsulation), inheritance in database models and custom errors, polymorphic action strategies. Report Section 2.2.3. |
| Which code smells? | Artham | Duplicate code, magic numbers, a long method, a duplicated test helper; fixed with Extract Method and Move Function, tests green before and after. |
| How is this Agile, not just coding? | Either | Backlog with story points, 4 sprints with increments, Kanban WIP limits, TDD commits, CI, refactoring, and we changed scope after review. |

## Tips

- Speak slowly; 7 minutes goes fast. If running late, **skip the Model page** in the demo.
- Shiva covers the **why and the process**; Artham covers the **product and the quality**. Hand over with one sentence ("Artham will now show you…").
- If the live site is slow, say: "The free server is waking up; this is expected on the free plan", and continue talking while it loads.

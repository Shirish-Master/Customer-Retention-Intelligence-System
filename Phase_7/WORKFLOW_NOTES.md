# Phase 7 — LAB_CL1 defect hunt: results and workflow note

## Task 3 and Task 9 — the two commits

> Commit your current code before making any changes — this is your only way
> back if the fix goes wrong

> Make two separate git commits — one before the fix, one after — and write a
> short note on what chat was useful for versus what needed the API

| Commit | Contents |
|---|---|
| `149e647` Phase 7 baseline | `.gitignore`, `record_risk_scores.py`, `risk_scores_before.*`. No behaviour changed. |
| *(second commit)* LAB_CL1 fix | `feature_columns.json` wiring in `LAB_ML2.py` / `predict.py`, the `main.py` forwarding fix, `audit_defect.py`, `risk_scores_after.*`. |

The baseline commit is the revert target. `git revert` on the second commit
restores the pre-fix scoring behaviour without losing the audit tooling.

---

## What the defect actually was

Two separate faults that only matter together:

1. **`Phase_6/predict.py`** hardcoded four values that belong to the training
   run — `internet_service = "Fiber optic"`, `auto_pay_flag = 0`,
   `has_streaming_bundle = 0`, and `MONTHLY_CHARGES_MEDIAN = 70.35`.
2. **`Phase_3/main.py`** never accepted or forwarded those attributes, so
   *every* API prediction used the hardcoded values regardless of who the
   customer was.

Why it mattered more than it looks: `internet_service_Fiber optic` is the
**third most important feature in the tree** (importance 0.165, behind only
`contract_type_Month-to-month` at 0.519 and `tenure` at 0.166). Fiber optic
customers churn at 41.9% against a 26.5% base rate, so hardcoding it biased
every API prediction *upward*.

This is an **inference-time** defect. The saved model was fine. Retraining
`LAB_ML2.py` produced byte-identical metrics (Decision Tree F1 0.6154,
accuracy 0.7906) — the model never needed rebuilding.

---

## Task 8 — Before / after risk scores

> Re-run your test predictions and your batch scoring job, and record the risk
> scores before and after the fix

Produced by running the same unchanged script either side of the fix:

```
python Phase_7/record_risk_scores.py before   # on the baseline commit
python Phase_7/record_risk_scores.py after    # on the fixed commit
```

### Test predictions — through the API path

| Persona | Internet | Autopay | Risk before | Risk after | Δ | Verdict before → after |
|---|---|---|---|---|---|---|
| P1 loyal / two-year / no internet | No | 1 | 0.0162 | 0.0162 | — | Unlikely → Unlikely |
| P2 mid-tenure / month-to-month / DSL | DSL | 1 | **0.5050** | **0.2895** | −0.2155 | **Likely → Unlikely** |
| P3 new / month-to-month / fiber | Fiber optic | 0 | 0.7214 | 0.7214 | — | Likely → Likely |
| P4 long tenure / one year / DSL / autopay | DSL | 1 | 0.0943 | 0.0943 | — | Unlikely → Unlikely |
| P5 new / month-to-month / no internet | No | 0 | **1.0000** | **0.0769** | −0.9231 | **Likely → Unlikely** |

The direction is exactly what the defect predicts:

- **Two false positives cleared.** P2 and P5 were being flagged for retention
  spend they did not need. P5 is the extreme case — scored at **1.00 certainty
  of churning** when its true score is **0.0769**, a 13× overstatement, purely
  because a customer with *no internet service at all* was scored as a fiber
  customer.
- **The genuine high-risk customer did not move.** P3 really is a new
  month-to-month fiber customer, so the placeholders happened to match reality
  and the score is unchanged at 0.7214. A fix that dragged P3 down would have
  been a fix that broke the model.
- **P1 and P4 unchanged** — both sit on One year / Two year contracts, and the
  contract split dominates the tree before internet service is ever reached.

Before the fix the API disagreed with ground truth on **2 of 5** personas.
After, **5 of 5** match (`api_matches_direct = True` for every row).

### Batch scoring job — unchanged, and that is the point

| Metric | Before | After |
|---|---|---|
| Rows scored | 7043 | 7043 |
| Mean risk score | 0.264654 | 0.264654 |
| Median risk score | 0.175 | 0.175 |
| Likely to churn | 1921 | 1921 |
| Likely-to-churn rate | 27.2753% | 27.2753% |

`batch_score.py` already passed all ten real attributes explicitly, so it was
never affected. Its being *identical* either side of the fix is the control
that proves the defect was confined to the API path — and it is the reason the
bug survived: the nightly batch numbers looked right the whole time, while the
dashboard was quietly inflating risk for every customer who was not on fiber.

`customer_risk_table` re-scored clean after the fix: 27.28% likely-to-churn
against a 26.54% training base rate, 80% overlap with the rule-based
`v_high_risk_customers` view.

### Tests

`Phase_6/test_predict.py` — 3 passed. The two four-field tests still pass
because `predict.py` now falls back to the *recorded* training defaults, which
happen to equal the old literals.

> Unrelated pre-existing failure: `Phase_1/test_customer_cleaner.py` cannot be
> collected from the project root because it opens `'..\customer_churn.csv'` by
> relative path. It only runs from inside `Phase_1/`. Not touched.

---

## A caveat worth recording

Swapping the literals for values read from `feature_columns.json` changed **no
score on its own**. The training-set modes turn out to equal the old hardcoded
literals exactly: `internet_service` mode *is* "Fiber optic" (3096 of 7043,
44%), `auto_pay_flag` mode is 0, `has_streaming_bundle` mode is 0, and the
median monthly charge is 70.35.

So the JSON contract is not what moved the numbers — **wiring `main.py` to
forward the real attributes is.** What the contract buys is that the values are
now provenanced and regenerated on every training run, so they cannot silently
drift away from the data, and the column order is asserted against
`model.feature_names_in_` at import instead of being trusted.

It is also worth being honest that a defaulted prediction is still a guess.
`predict.py` now logs a warning naming each feature it had to fall back on, so
a low-confidence score is visible rather than silent. The real follow-up is to
have the React form collect internet service and payment method.

---

## Task 9 — chat versus API

> write a short note on what chat was useful for versus what needed the API

**Chat earned its place at the start and the end.** The unled first-pass review
(Task 1) only works as a conversation — the whole value is in *not* specifying
what to look for, and then reading what comes back. Iterating the audit wording
(Task 2) is the same: three drafts, each one read and reacted to, until "where
does each value come from at inference time?" turned out to be the question
that forced a per-column answer instead of "looks fine". Drafting that in code
would have meant a round trip and a rerun per attempt. The plain-English
rewrite (Task 6) is a one-shot with a human judging the tone — there is nothing
to automate.

**The API earned its place in the middle, for one reason: assertions.** Task 5
requires *confirming* that the findings name every hardcoded feature and do not
recommend retraining. You cannot assert against prose. `tool_choice` forcing
`report_audit_findings` means the response is a typed object every time —
`findings[]`, `requires_retraining: bool`, `defect_class` from a fixed enum —
so `verify_findings()` can fail the run with an exit code. That turns the audit
from something a person reads into something CI can gate a merge on. Pasting
all four files into one request also keeps the comparison in a single context
rather than depending on what got scrolled into the chat.

The rough division: **chat for finding out what question to ask; the API for
asking that question the same way every time and acting on the answer.** The
useful artefact from the chat sessions was not any individual answer, it was
draft 3 of the prompt — which is what `audit_defect.py` now hardcodes.

---

## Part 2 — memory, templates, guardrails

| File | Task |
|---|---|
| `project_context.py` | The project memory, 11 named fact blocks, prepended to every system prompt |
| `claude_guardrails.py` | All four security checklist items; the only place that calls the Messages API |
| `prompt_loader.py` | `load_template(name, **kwargs)` — versioned, validated, secret-scanned |
| `prompts/*.v1.md` | The three templates |
| `security_review.py` | Human-only module; four independent checks before it will run |
| `memory_test.py` | Fact present → removed → restored |
| `secret_leak_check.py` | Six real leak attempts against a live `.env` value |

### Note — drafting prompts in chat versus running them via the API

Drafting a prompt and *operating* one turned out to be different jobs, and the
split was sharper here than in the defect hunt.

**Chat is where a prompt gets its content.** Every instruction that ended up
mattering came from watching a draft fail. The endpoint template is the clearest
case: the first version said "follow the conventions in Phase_3/main.py" and got
back SQL inlined into the route. Asking chat *which single instruction was
missing* produced the answer that "follow the conventions" is not an instruction
— the seven conventions had to be enumerated. No amount of reasoning about the
template in the abstract would have produced that; it needed a bad output in
front of both of us. Same with the memory: asking Claude to *ask me questions it
couldn't guess the answers to* surfaced the CamelCase quirk and the AVG-vs-median
inconsistency, neither of which I would have thought to write down.

**The API is where a prompt gets its guarantees.** Everything that makes these
templates safe to run repeatedly is code, not wording: that arguments are
validated before they become prompt text, that a `.env` value cannot reach the
request by any of six paths, that history is trimmed to ten turns and tokens
capped in one place, that only six named fields of a customer row are ever
forwarded. None of that is expressible in a chat window — in chat, *I* am the
guardrail, and I am not a reliable one at 6pm.

The thing that surprised me: **the memory is only worth having because it is
testable.** In chat, context accumulates invisibly and you cannot tell whether
an answer is grounded in what you said or in what the model already knew.
`memory_test.py` removes one fact and measures the answer getting worse, which
is the only way to know the block is doing work rather than decorating the
request. A memory you cannot degrade on purpose is a memory you cannot trust.

The corollary is that `security_review.py` deliberately refuses to be automated
even though it runs through the same API layer. Automating it would produce a
list of exploitable weaknesses in build logs on every push, and a green check
mark that nobody reads. Some things should stay hard to run.

---

## Running everything

```bash
# from the project root

python Phase_6/LAB_ML2.py                    # trains, writes models/feature_columns.json
python Phase_7/audit_defect.py --dry-run     # validate the request without an API call
python Phase_7/audit_defect.py               # the real audit (needs a live key in .env)
python Phase_7/record_risk_scores.py after   # personas + batch aggregate
python Phase_6/batch_score.py                # full job, writes customer_risk_table
python -m pytest Phase_6/test_predict.py -q

# part 2 - needs a live key in .env except where noted
python Phase_7/secret_leak_check.py          # no API call, no key needed
python Phase_7/memory_test.py                # fact present -> removed -> restored
python Phase_7/security_review.py --diff-from HEAD~1   # interactive only
```

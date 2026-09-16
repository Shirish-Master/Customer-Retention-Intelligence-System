# Phase 7 — the Claude.ai chat tasks

Three Phase 7 tasks are marked `[Claude.ai]`. They are done in the chat UI, not
in code, so the prompts live here rather than in a `.py` file. Paste each into
claude.ai and keep the reply alongside it.

---

## Task 1

> Do a first-pass review of predict.py — ask "does anything here look wrong or
> inconsistent?" without leading toward an answer  [Claude.ai]

The point of this task is that the question must **not** hint at the answer. Do
not mention hardcoding, placeholders, feature columns, or `internet_service`.
Attach or paste `Phase_6/predict.py` and ask exactly this:

```
Here is the prediction module from a customer churn service.

Does anything here look wrong or inconsistent?
```

That is the whole prompt. Anything more — "check the feature handling", "is the
preprocessing right?" — leaks the answer and makes the exercise worthless. If
the first-pass review finds the defect unprompted, that is a genuine signal. If
it does not, that is also a real result: record it, because it is the reason
Task 2 exists.

**Record here:** did the unled review find the hardcoded features? Yes / No, and
what it flagged instead.

---

## Task 2

> Draft and iterate the wording of a more targeted audit question, comparing
> train.py's feature columns against what predict.py actually builds  [Claude.ai]

Iterate the wording — keep every draft so the progression is visible.

**Draft 1 (too vague, produces a generic code review):**

```
Compare my training script and my prediction script. Are they consistent?
```

**Draft 2 (names the comparison, still lets the model wander into style notes):**

```
Here are my training script and my prediction script. Do the feature columns
in the prediction script match the ones the model was trained on?
```

**Draft 3 (final — anchors on provenance of each value, which is the actual
defect, without naming the defect):**

```
Here are two files from the same project: the script that trains a churn model,
and the script that loads that model to score a single customer.

For every feature column the model was trained on, tell me where the prediction
script gets that value from at inference time. Specifically: which values come
from the caller's real customer data, and which are produced some other way?

List them in a table with the column name and the source of the value.
```

Draft 3 works because "where does this value come from" forces the model to
account for each column individually. It cannot answer with "looks fine" — it
has to produce a row for `internet_service` and write down that the value is a
literal in the function signature.

Note the file naming in this repo: the checklist says `train.py`; here the
training script is `Phase_6/LAB_ML2.py` with feature prep in
`Phase_6/LAB_ML1.py`. Attach both.

**Record here:** which draft first surfaced the defect.

---

## Task 6

> Ask for a plain-English explanation of the findings suitable for a
> non-technical write-up  [Claude.ai]

Run this after `audit_defect.py` has produced `Phase_7/audit_findings.json`.
Paste that JSON in and ask:

```
Here are the findings from a technical audit of a customer churn prediction
system.

Rewrite this for a non-technical audience — a customer retention manager who
will read it in a status report. They need to understand what went wrong, who
was affected, and whether the numbers they have been acting on can be trusted.

Do not use the words model, feature, inference, or column. Two or three short
paragraphs. No bullet points.
```

The constraint list is what makes this prompt work. Without it you get the same
technical content with slightly shorter sentences.

**Record here:** paste the resulting write-up. It is the deliverable for this
task.

---

## Why these three stayed in chat

See `WORKFLOW_NOTES.md` for the full chat-versus-API note (Task 9). In short:
these three are open-ended and judgement-based, and the value is in reading the
reply and reacting to it. The audit in Task 4 is the opposite — it needs the
same rigid shape every time so it can be asserted against in CI, which is what
`tool_choice` buys and what the chat UI cannot give.

---
---

# Part 2 — memory, templates and the security checklist

Three more `[Claude.ai]` tasks. Same rule: draft in chat, commit the artefact.

---

## Task 1 (part 2)

> Draft the contents of your project's "memory" — the facts Claude should
> always know: your data quirks, your ML rules, your table names. Keep it under
> 200 lines  [Claude.ai]

Drafting this in chat is worth the round trip because the useful question is
"what did you get wrong when I *didn't* tell you this?" Prompt used:

```
I have a telco churn project: MySQL, FastAPI, a scikit-learn decision tree,
and a React dashboard. I want to write a "project memory" — a block of facts
prepended to the system prompt of every API call I make about this codebase.

Ask me up to ten questions about the project whose answers you could not
guess correctly from general knowledge of telco churn datasets. Do not write
the memory yet. I want the questions first.
```

Asking for the *questions* first is the trick. It surfaces exactly the facts
that are load-bearing — the ones where a plausible assumption is wrong. Three
came out of this that made it into the file: that `stg_customer_raw` keeps
CamelCase while everything else is snake_case, that `internet_service = "No"`
means no product rather than a missing value, and the `high_charge_flag`
AVG-versus-median inconsistency.

Then, with the answers pasted back:

```
Now write the memory block. Under 200 lines. Group it into named sections.
Facts only — no advice, no "consider doing X". Anything you would only know
by reading my code, not by knowing the domain.
```

**Artefact:** `project_context.py`.

---

## Task 4 (part 2)

> Draft three reusable prompt templates: one to profile your dataset, one to
> scaffold a new API endpoint, and one to review code changes for security
> issues  [Claude.ai]

Drafted one at a time. The pattern that worked was writing a bad first version
deliberately, running it, and asking what went wrong:

```
Here is a prompt template I use to scaffold new FastAPI endpoints, and here is
the output it produced. The output ignored my service-layer convention and put
the SQL directly in the route.

Rewrite the template so that cannot happen. Do not make it longer than it
needs to be — tell me which single instruction was missing.
```

That produced the numbered convention list in `scaffold_endpoint.v1.md`. The
answer was that "follow the conventions in main.py" is not an instruction, it
is a hope — the conventions had to be enumerated.

For the profiling template the lesson was the opposite: the first draft asked
for too much and got confident nonsense, so `profile_dataset.v1.md` ends with
an explicit instruction to name the missing aggregate rather than guess.

**Artefacts:** `prompts/profile_dataset.v1.md`,
`prompts/scaffold_endpoint.v1.md`, `prompts/security_review.v1.md`.

---

## Task 8 (part 2)

> Ask Claude.ai to red-team your checklist — "what am I missing, given this
> handles real customer data?"  [Claude.ai]

Paste `claude_guardrails.py` in and ask:

```
Here is the entire security layer for a system that sends code and database
aggregates to the Claude API. The underlying data is 7043 real telco customer
records: identifiers, tenure, billing amounts, payment method, per-service
subscription flags.

Red-team this. What am I missing, given this handles real customer data?

Be specific about what an attacker or a careless colleague actually does to
get past each control. Rank by what you would fix first. Do not restate what
the code already does correctly.
```

The "what does someone actually do to get past it" phrasing matters — without
it you get a checklist of generic best practices rather than the specific holes
in this code.

**Known gaps to expect it to find** — recording them here so the reply can be
judged rather than just accepted:

- `assert_no_secrets` compares against `.env` values by exact substring. A
  secret that is base64'd, URL-encoded, reversed, or split across two arguments
  goes straight through.
- `MIN_SECRET_LENGTH = 8` means a short secret is never scanned at all.
- The guard checks what is *sent*, not what comes *back*. Nothing scans the
  response before it is printed to a terminal or written to a file.
- `project_fields` restricts columns but nothing restricts *row count* — a
  caller can pass 7043 projected rows and still export the whole customer base.
- Prompts are not logged, so there is no record of what customer data was sent
  to a third party. That is a GDPR problem, not a security one, and it is
  invisible from inside the code.
- `dotenv_values` is re-read on every scan; an attacker who can write `.env`
  can shrink it to empty and disable the guard.

**Record here:** what the red-team found that is *not* in the list above. That
delta is the actual deliverable for this task.

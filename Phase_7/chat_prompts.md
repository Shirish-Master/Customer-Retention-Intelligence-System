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

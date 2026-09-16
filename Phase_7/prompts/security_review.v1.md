# security_review v1
# Placeholders: $change_description, $diff
# Loaded by: security_review.py ONLY — a human-invoked module.
# Do not import this template from automated code. See security_review.py.

Review the following change to a system that handles real customer records
(7043 telco subscribers: identifiers, tenure, billing amounts, payment method,
and per-service subscription flags).

Change description: $change_description

```diff
$diff
```

Review for security issues only. Ignore style, naming, performance and test
coverage unless they create a security problem.

Work through these, and say explicitly when a category has no findings:

1. **SQL injection.** Any query built by concatenation or f-string rather than
   `text()` with bound parameters. Check optional filters and any ORDER BY or
   LIMIT built from user input especially — those are the ones that get missed.
2. **Secret exposure.** Credentials, API keys or connection strings added to
   source, logs, error messages, or API responses. Note that this project has a
   hardcoded `mysql+pymysql://root:root@localhost/churn` URL in several files;
   flag any *new* occurrence or any path that could return it to a client.
3. **Customer data exposure.** Does the change widen what a response returns,
   or send customer rows somewhere new — a log, a third-party API, an error
   body? Personal identifiers leaving the database is the highest-severity
   category here.
4. **Authentication and authorisation.** Routes reachable without the X-API-Key
   check. Whether the change assumes an auth check that is not actually wired
   up.
5. **Input validation.** Unvalidated values reaching a query, a file path, a
   model, or a shell. Missing bounds on numeric inputs. Note whether Pydantic
   validators genuinely apply to the route, or only appear to.
6. **Error handling.** Stack traces, SQL fragments, or internal paths returned
   to the caller rather than a generic message.
7. **CORS and transport.** Widened `allow_origins`, credentials allowed against
   a wildcard origin.

For each finding, give: file and line, severity (high/medium/low), the concrete
attack or exposure it enables, and the minimal fix.

Rank findings by severity. If you find nothing, say so plainly rather than
producing filler. Do not rewrite the whole file — the goal is a reviewable list
a person acts on, not a refactor.

# profile_dataset v1
# Placeholders: $table_name, $row_count, $column_summary, $question
# Loaded by: prompt_loader.load_template("profile_dataset", ...)
# Send SCHEMA AND AGGREGATES ONLY. Never paste customer rows into this prompt.

Profile the table `$table_name` in the churn database.

It has $row_count rows. Here is the per-column summary — name, dtype, null
count, distinct count. These are aggregates; no individual customer records are
included and none should be requested.

$column_summary

Working from the project memory above and this summary, answer:

$question

In your answer:

1. Flag any column whose null count or distinct count contradicts what the
   project memory says should be true of it. Name the memory fact you are
   contradicting.
2. Call out columns that look like identifiers rather than features.
3. Call out any column that is constant or near-constant — it cannot carry
   signal and should not be fed to a model.
4. Note where a dtype looks wrong for the values described (a numeric quantity
   stored as text, a flag stored as something other than 0/1).

Do not propose model changes, retraining, or new features here — this task is
description only. If the summary is insufficient to answer confidently, say
which additional aggregate you would need, and do not guess.

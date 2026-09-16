# scaffold_endpoint v1
# Placeholders: $method, $route, $purpose, $response_fields, $source_tables
# Loaded by: prompt_loader.load_template("scaffold_endpoint", ...)

Scaffold a new FastAPI endpoint for this project.

- Method:          $method
- Route:           $route
- Purpose:         $purpose
- Response fields: $response_fields
- Source tables:   $source_tables

Follow the conventions already in Phase_3/main.py exactly:

1. A Pydantic response model, named in PascalCase, with explicit field types.
   Floats for money and rates, int for counts and flags, str for labels.
2. A service-layer function that takes an open session as its first argument
   and contains all the SQL. The route handler calls it and does nothing else.
   Business logic does not go in the route — see the LAB_API2 note in main.py.
3. `text()` with bound parameters for every query. Never build SQL by string
   concatenation or f-string, including for optional filters — extend the
   query string with a fixed fragment and bind the value.
4. `raise HTTPException(status_code=404, detail="...")` when a lookup returns
   nothing, with a message matching the style of the existing handlers.
5. Wrap the query in try/except and raise a 500 with detail
   "Database unavailable" on failure, logging the error first.
6. A `logger.info` at entry naming the method, path and key parameters, and one
   recording the response status.
7. Close the session in a `finally` block.

Use only the tables named above. If answering the stated purpose needs a table
that is not in that list, stop and say which one and why, rather than inventing
a schema — the project memory above lists the real tables and their join keys.

Return the code as a single block ready to paste at the end of main.py,
preceded by a one-line comment naming the lab step it belongs to. Do not
restate or modify any existing code in the file, and do not renumber the
existing lab step comments.

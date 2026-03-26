# Bartley-SC-App
Dev app for running races


Hub and spoke app - Centralized app for sailing club and personalized for individual sailors. 

QR Sign in

Personal stats

Nationwide comparisons

Instant results

Series Results

Stream results

Series list


## 🚀 Frontend improvements (UI/UX)

1. Session fallback
   - If `/api/session/entries` fails, show a user-friendly modal + "try again" / "start new race".


2. Table layout
   - Use CSS classes, not inline styles.
   - `text-align:center` (not `centre`).
   - sticky first columns (“Actions”) and header.
   Absolutely — great callout, and this is a high-impact UI improvement for better usability.
        Here’s exactly what sticky first columns (“Actions”) and header means:

        position: sticky on header:

        Keeps the column labels visible when scrolling vertically.
        With top: 0, the table header “sticks” at top of viewport.
        position: sticky on first column(s) like Actions:

        Keeps “Actions” buttons in view while scrolling horizontally.
        With left: 0 (or left: 0/60px if multiple sticky cols), it stays fixed.
        How this helps:

        For wide row/column sets with many lap columns, user can always press lap/finish without losing row context.
        Fast operator workflow with less scrolling and fewer mis-controls.
        Minimal CSS snippet
        For multiple sticky columns
        second column: left: 60px or width-of-first
        etc.
        Key points
        Header sticky: always see Actions/Sailor/Boat/... even after vertical scroll.
        First column sticky: always act on selected row even when horizontal scroll needed for many laps.
        Combined with row striping + clean horizontal grid improves readability dramatically on race-control screens.

3. Lap cells
   - “Finish” column explicitly.
   - Add per-lap delta (this lap vs best/goal).
   - Show boat status icons (⏳🚤✔️DNF).

<!-- 4. Timing
   - Running clock via `requestAnimationFrame` for smooth .
   - Option to pause/resume.
   - Add “split” into lap (split time separate from cumulative). -->

5. Data features
   - CSV/JSON export for results.
   - “Undo last lap” control.
   - Sort/paginate by columns.

6. Accessibility
   - ARIA labels on buttons/rows.
   - Keyboard nav for lap/finish.
   - high-contrast theme switch.

---

## 🗄️ Backend improvements

<!-- 1. Session model consistency
   - Normalize 1 key (`entries`) and/or use `pending_entries`.
   - Add API for `/session/attributes` once, to avoid mismatched keys. -->

2. Persistence & ID
   - `race_id` with DB record on race start.
   - `entry_id` per boat session to avoid `index` as primary key.

3. Validation
   - Enforce payload schema with `marshmallow` or `pydantic`.
   - Protect with race state (no lap after finish or before start).

4. DB design
   - `race` / `race_entry` / `lap` tables:
     - `race_entry` link for each boat in race.
     - `lap` row per `race_entry` + `lap_number`.
   - store `elapsed_sec` numeric and `corrected_sec` numeric not just text.

5. API
   - CRUD for entries and races.
   - endpoints:
     - POST `/api/races/start`
     - POST `/api/races/{id}/lap`
     - POST `/api/races/{id}/finish`
     - GET `/api/races/{id}/results`

6. Audit/metrics
   - Add soft logs + request traces.
   - Combat double-click logs with idempotency key.

---

## 🔒 Operations, reliability, testability

1. Unit tests for:
   - time calc, corrected time, ranking functions.
   - route responses in Flask.

2. Integration tests
   - Simulate full race lifecycle.
   - `pytest` + test DB fixture.

3. Error handling
   - Catch DB disconnect, return JSON errors.
   - Feature-flag “race mode”.

4. Deploy
   - Use Docker Compose + prod webserver (gunicorn/uvicorn).
   - `pass SECRET_KEY` from env, not hardcoded.

---

## 💡 Nice next “stretch” features

- “Tack by tack” intermediate targets / classes.
- Heat/series standing.
- Live socket updates (WebSocket) for multi-display.
- Mobile responsive layout; button size + dark mode.
- Auto-calc handicap corrected at known formula with season rating updates.

---

### Quick dev priority

1. Ensure `race_control` never depends on missing session data.
2. Replace inline in-table styles with CSS classes.
3. Back-end entry/session state canonicalization and DB normalization.
4. Unit tests for calculation + session race flow.

You're in a great place; focus on stability and data correctness first, then polishing the UI/flow for race operators in the wild.
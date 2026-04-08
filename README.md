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

Web
Setup series->Start race->Record Race Results

App
Enter Race->Recieve Results->View Series Results

test_admin / ChangeMe123! (minimal dataset)
bartley_admin / ChangeMe123!
rsyc_admin / ChangeMe123!
hamble_admin / ChangeMe123!
warsash_admin / ChangeMe123!
hillhead_admin / ChangeMe123!

## Test utility: reset a series for mobile/web testing

Use [\_reset_series_api_test.py](_reset_series_api_test.py) to clear old race data and create fresh upcoming races.

For one-click QA presets on Windows, run [reset_series_test.bat](reset_series_test.bat).
It provides a menu for default reset, series-only reset, 3-race seed, custom args, and help.

## Reconnect phone to backend (reusable)

If the phone is unplugged/replugged, run [reconnect_phone_backend.bat](reconnect_phone_backend.bat).

This will:
- find `adb` (Windows PATH/SDK or WSL fallback),
- reconnect `adb reverse tcp:5000 tcp:5000`,
- show connected devices and reverse mappings,
- call [app/app.py](app/app.py) health endpoint `GET /api/health`,
- probe mobile API and explain common HTTP 500 cause (database unavailable).

If probe output mentions `OperationalError` / `connection to server at "localhost"`, the phone tunnel is fine and PostgreSQL is down.

Main script: [reconnect_phone_backend.ps1](reconnect_phone_backend.ps1)

## Sync mobile app changes across Windows and Linux

If you edit the Android app from both the Windows repo copy and a WSL/Linux working copy, use the sync helper so both stay aligned.

- Push the repo mobile project into WSL:
  - `./sync_mobile_android.ps1 -Direction ToWsl`
- Pull WSL mobile changes back into the repo:
  - `./sync_mobile_android.ps1 -Direction FromWsl`

Defaults:
- distro: `Ubuntu`
- WSL project path: `/home/sjknight/mobile/sailor-android`

You can override both with `-WslDistro` and `-WslProjectPath`.

The sync excludes local-only files and build output such as `.gradle/`, `.idea/`, `build/`, `local.properties`, and `*.iml`.

## Advanced series scheduling (overlapping/non-linear)

New API endpoints support Lyme-style calendars with overlapping series and exceptions.

- Add recurring rule: `POST /api/series/manage/{series_id}/rules`
   - payload example:
      - `weekday`: `"saturday"` (or `0..6`)
      - `start_time`: `"11:00"`
      - `cadence_weeks`: `1`
      - `races_per_day`: `2`
      - `slot_gap_minutes`: `15`
      - `valid_from`: `"2026-04-01"`
      - `valid_to`: `"2026-09-30"` (optional)

- Add exception: `POST /api/series/manage/{series_id}/exceptions`
   - `exception_type`: `cancel` | `move` | `add`
   - `original_start_at` / `override_start_at` (ISO datetime as needed)

- Generate concrete races from rules/exceptions:
   - `POST /api/series/manage/{series_id}/generate`
   - payload: `{ "from_date": "2026-04-01", "to_date": "2026-10-31" }`

List configured data:
- `GET /api/series/manage/{series_id}/rules`
- `GET /api/series/manage/{series_id}/exceptions`

Examples:

- Default reset for `Series_API_Test` (club-wide cleanup):
   - `C:/Users/SJKnight/virtual_environments/sailing_app/Scripts/python.exe _reset_series_api_test.py`
- Reset a specific series only:
   - `C:/Users/SJKnight/virtual_environments/sailing_app/Scripts/python.exe _reset_series_api_test.py --series-name "Series_API_Test" --cleanup-scope series`
- Create 3 races starting 2 days ahead, 30 minutes apart:
   - `C:/Users/SJKnight/virtual_environments/sailing_app/Scripts/python.exe _reset_series_api_test.py --race-count 3 --days-ahead 2 --spacing-minutes 30`

Options:

- `--series-name` (default: `Series_API_Test`)
- `--cleanup-scope` = `club` or `series` (default: `club`)
- `--race-count` (default: `1`)
- `--days-ahead` (default: `1`)
- `--spacing-minutes` (default: `60`)
- `--db-url` (defaults to `DATABASE_URL` env var, else local postgres URL)

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

<!-- 4. DB design
   - `race` / `race_entry` / `lap` tables:
     - `race_entry` link for each boat in race.
     - `lap` row per `race_entry` + `lap_number`.
   - store `elapsed_sec` numeric and `corrected_sec` numeric not just text. -->

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



**Critical Gaps Vs Goals**
- **Admin hub maturity:** the web side still feels like race tooling plus setup pages, not yet a true club admin hub; app.py is a 3,500+ line monolith mixing HTML routes, mobile APIs, admin APIs, scheduling, and race logic.
- **Retrospective handwritten results:** I can see race creation, lap recording, and summaries, but not a dedicated backfill workflow with edit/review/audit support; this is the biggest functional gap for real club operations.
- **Permissions:** mobile race-control endpoints appear club-scoped, not role-scoped; a normal sailor with a club session can hit control endpoints in app.py. Your “only enabled when on duty” idea is exactly the right next model.
- **Security/ops:** hardcoded DB URI and Flask secret in app.py, SQL string building in connection.py, HTTP mobile base URL and verbose body logging in Network.kt.
- **Analytics platform gap:** there is not yet a normalized domain for personal handicap history, cross-club benchmarking, recommendation versioning, or coach-style athlete timelines.
- **Testing gap:** I don’t see a real automated test suite around race lifecycle, permissions, calculations, or regression scenarios.

**Product Recommendations**
- **P1 – mobile entitlement:** make race control invisible unless the backend says the sailor is currently granted duty access for that club/date/race.
- **P1 – analytics foundation:** create tables for `personal_handicap_snapshot`, `performance_event`, `club_adjustment_recommendation`, and `cross_club_benchmark`; start with trends like finish consistency, corrected-time delta to fleet median, class-normalized improvement, and series momentum.
- **P2 – local handicap recommendations:** let the system recommend changes, but require club admin approval with reason codes and before/after traceability.

**Specific Design Advice**
- For retrospective paper results, build a dedicated “Enter Results After Race” flow: create/select race → import/add entries → input finish times/positions/DNF → preview recalculated standings → approve/publish → keep immutable audit revisions.
- For your Strava-style vision, don’t make “personal handicap” just a single number; treat it as a time series with confidence, source, club scope, and recommendation rationale.
- For cross-club comparison, define normalization rules early: by class, handicap basis, fleet size, course length proxy, and weather/context where possible.
- For club trust, never auto-apply handicap changes; surface recommendation bands, evidence, and approval workflow.


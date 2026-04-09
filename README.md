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

## Change backlog

Desired changes and product backlog items from earlier review are now tracked centrally in [Changes.MD](Changes.MD).
- Go-live and real-user rollout steps are documented in [GO_LIVE_AND_SUPPORT_PLAN.md](GO_LIVE_AND_SUPPORT_PLAN.md).
- For your Strava-style vision, don’t make “personal handicap” just a single number; treat it as a time series with confidence, source, club scope, and recommendation rationale.
- For cross-club comparison, define normalization rules early: by class, handicap basis, fleet size, course length proxy, and weather/context where possible.
- For club trust, never auto-apply handicap changes; surface recommendation bands, evidence, and approval workflow.


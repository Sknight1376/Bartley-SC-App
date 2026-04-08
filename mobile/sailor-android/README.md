# Sailor Android Starter

Starter Android app for the QuickSail sailor spoke.

## Includes
- Kotlin + Jetpack Compose
- Retrofit + OkHttp client
- Session cookie support (in-memory cookie jar)
- API models and service methods matching backend mobile endpoints
- Basic screens/flow for:
  - Login/logout
  - View/edit sailor profile
  - View upcoming races
  - Join race
  - View own results

## Before running
1. Open `mobile/sailor-android` in Android Studio.
2. Let Gradle sync.
3. Set backend URL in:
   - `app/src/main/java/com/quicksail/sailor/api/Network.kt`
   - Default is emulator local: `http://10.0.2.2:5000/`
4. Ensure backend DB has sailor users seeded (e.g. `alice_test / ChangeMe123!`).

## Windows / Linux sync

If you work on the Android app from both the Windows repo copy and a WSL/Linux copy, keep them explicitly synced so edits do not drift.

- Repo copy: `mobile/sailor-android`
- Current WSL copy expected by the sync helper: `/home/sjknight/mobile/sailor-android`

From Windows PowerShell at the repo root:

- Push repo changes into WSL:
  - `./sync_mobile_android.ps1 -Direction ToWsl`
- Pull WSL changes back into the repo:
  - `./sync_mobile_android.ps1 -Direction FromWsl`

Optional overrides:

- Different distro:
  - `./sync_mobile_android.ps1 -Direction ToWsl -WslDistro Ubuntu-24.04`
- Different WSL path:
  - `./sync_mobile_android.ps1 -Direction FromWsl -WslProjectPath /home/<user>/mobile/sailor-android`

The sync excludes local machine files and build outputs such as `.gradle/`, `.idea/`, `build/`, `local.properties`, and `*.iml`.

## Notes
- Cookie storage is in-memory for now. Replace with persistent secure storage for production.
- UI is intentionally minimal starter scaffolding.






Good next step. A practical production-readiness checklist:

Security hardening
Enforce HTTPS only (no cleartext API traffic).
Store auth/session data securely (encrypted at rest).
Add certificate pinning if feasible.
Remove debug logs and any PII from logs/crash payloads.
Build/release setup
Create debug vs release configs for API base URL and flags.
Enable shrinking/obfuscation (minifyEnabled, R8, resource shrinking).
Verify signing config, keystore backup, and key rotation policy.
Turn on reproducible CI builds for tagged releases.
Reliability and UX
Add global network error handling, retries with backoff, and offline/timeout states.
Add loading/empty/error UI for each page.
Ensure pull-to-refresh and navigation state are consistent after process death.
Add analytics events for critical flows (login, joinRace, startRace, finishRace).
Testing
Unit tests for ViewModel logic and API mapping.
UI tests for core flows (auth, dashboard refresh, race control, results dialog).
Integration test against a staging backend and seeded database.
Regression checklist for race-day scenarios (multiple races/day, DNF, missing laps).
Performance
Profile startup and first-content render time.
Reduce overfetching; paginate/limit long lists.
Verify Compose recomposition hotspots and avoid unnecessary state churn.
Backend/API readiness
Version mobile APIs (e.g., /api/mobile/v1/...).
Add request/response schema validation and stricter error contracts.
Add rate limiting and auth/session expiration strategy.
Add observability: structured logs, traces, endpoint latency/error dashboards.
Operational readiness
Create staging and production environments with separate data.
Add crash reporting and alerting (with release version tags).
Define rollback strategy and hotfix process.
Prepare runbooks for race-day incidents.
Store release readiness
Privacy policy + data handling disclosures.
App icon, screenshots, feature graphics, release notes.
Internal testing track, then closed/open testing before production.
Compatibility matrix (min/max Android versions, device sanity list).






Good release question. For usability + ease of access, the highest-impact changes are:

<!-- 1. Navigation overhaul (primary)
- Replace the 2x2 action button grid with a fixed bottom navigation bar.
- Keep pages one tap away and avoid vertical scrolling just to navigate.
- Current nav is in SailorApp.kt. -->

<!-- 2. Authentication UX and safety
- Mask password fields and add show/hide toggle.
- Add `IME` actions (`Next`, `Done`) and auto-focus flow.
- Add “Forgot password” and account recovery path.
- Auth form lives in SailorApp.kt. -->

<!-- 3. Accessibility compliance
- Ensure all tap targets are at least 48dp.
- Add semantics/content descriptions for icons/buttons and dialog close actions.
- Verify TalkBack order, dynamic type scaling, and color contrast (especially status labels). -->
<!-- 
4. State clarity and feedback
- Add explicit success toasts/snackbars for `Join`, `Save Profile`, `Start Race`, `Finish Race`.
- Show per-section skeleton/loading states, not only generic spinner.
- Keep errors actionable (“No club assigned”, “No boats saved”, “Network timeout”). -->

<!-- 5. Dashboard usability
- Keep “Latest Races” sorted with clear date grouping.
- In “My Latest Result”, show date header and race count when multiple races exist that day.
- Make result cards tappable to view full details (instead of text-only summary). -->

<!-- 6. Session and continuity
- Persist login securely across app restarts.
- Restore last-opened tab/page and scroll position.
- This is especially important for race-day usage with intermittent connectivity. -->
<!-- 
7. Offline-friendly behavior
- Cache recent dashboard/race data and show “Last updated” timestamp.
- Queue critical race actions if brief network drop occurs, then sync automatically. -->

<!-- 8. First-run guidance
- Add a short onboarding checklist:
  - assign club
  - add boat
  - join first race
- Reduces confusion for new users significantly. -->

<!-- 9. Notifications
    - New races available
    - New results
    - Series End -->

If useful, I can turn this into a strict release backlog with P0/P1/P2 and then implement P0 items first.
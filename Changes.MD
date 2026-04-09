# Change Tracker

Use this file to track desired changes gathered from review and the repository README files. Completed items should be marked with `[x]`.

Priority levels:
- **P0** – Blocks real-world club usage or safety of data. Do first.
- **P1** – Significant functional or trust gap. Do next sprint.
- **P2** – Quality-of-life improvement or stretch feature. Do when capacity allows.

---

## ✅ Completed

### Web
- [x] Remove buttons for managing members and series; access is now through the club dashboard
- [x] Remove button for managing sailing portal, user admin is done in the mobile app
- [x] Add two panels on landing page — latest race results, and club admin summary stats
- [x] Add races captured by hand — manual entry of entries and times in the club dashboard

### Mobile
- [x] Add entries for boats that haven't used the app to sign in (race control manual add)

---

## P0 — Critical / blocks club operations

### Backend
- [x] Remove hardcoded secrets / DB configuration and tighten unsafe SQL / HTTP defaults
- [x] Restrict mobile race-control capabilities by role/duty entitlement rather than club membership alone
- [x] Store `race_id` when a race starts and introduce stable `entry_id` values per boat session
- [x] Enforce request payload schemas consistently and protect race actions with race-state validation
- [x] Catch DB disconnects consistently and return JSON errors where appropriate

### Web — Race Control UI
- [x] Add a user-friendly fallback modal when `/api/session/entries` fails, with `Try again` and `Start new race` actions

### Web — Club Dashboard
- [x] Build a dedicated retrospective results workflow: create/select race → add/import entries → input finish data → preview standings → approve/publish → immutable audit revisions

### Mobile
- [x] Add explicit success feedback and per-section loading / empty / error states
- [x] Add global network error handling, retries with backoff, and timeout/offline states
- [x] Store auth/session data securely at rest
- [x] Remove debug logs and PII from mobile logs/crash payloads
- [x] Create debug vs release configs for API base URL and feature flags

---

## P1 — Important functional or trust gaps

### Backend
- [ ] Expand CRUD coverage for races and entries, including reliable start / lap / finish / results endpoints
	- [ ] Define and document canonical API contracts for race and entry CRUD (request/response/error shapes)
	- [ ] Add create/update/delete endpoints for race entries with role-based authorization checks
	- [ ] Add update/cancel/reopen endpoints for races with state-transition guards
	- [ ] Add idempotency for start/lap/finish endpoints to prevent duplicate race actions
	- [ ] Add pagination/filtering/sorting for list endpoints (`races`, `entries`, `results`)
	- [ ] Add contract tests for full lifecycle: create race → add entries → start → lap(s) → finish → results
- [ ] Add soft logs, request traces, and idempotency protection for double-click race actions
	- [ ] Introduce per-request correlation IDs propagated across logs and responses
	- [ ] Add structured application logs with event type, actor, club, race, and latency fields
	- [ ] Persist race-action audit events (`start`, `lap`, `finish`, `publish`) with actor and timestamp
	- [ ] Implement idempotency-key middleware for mutating endpoints
	- [ ] Add replay-safe behavior and explicit duplicate-action responses
- [ ] Version mobile APIs and tighten error contracts, rate limiting, and session expiration strategy
	- [ ] Introduce `/api/mobile/v1/...` routes and maintain compatibility aliases for current routes
	- [ ] Standardize error envelope (`code`, `message`, `details`, `request_id`) across mobile endpoints
	- [ ] Add per-user and per-IP rate limits for auth and write-heavy endpoints
	- [ ] Implement explicit session expiry/refresh behavior and client-visible auth error codes
	- [ ] Add migration notes and deprecation timeline for non-versioned mobile routes
- [ ] Add structured observability for endpoint latency, traces, and error dashboards
	- [ ] Emit metrics for request count, duration, error rate, and DB/query timing by endpoint
	- [ ] Add distributed trace hooks for request lifecycle and database calls
	- [ ] Define SLO targets (p95 latency, availability, error budget) for critical paths
	- [ ] Build dashboards for API health, race-control actions, and DB reliability
	- [ ] Add alert thresholds for auth failures, 5xx spikes, and race-control endpoint degradation
- [ ] Add local handicap recommendations with admin approval, reason codes, and before/after audit traceability
	- [ ] Design recommendation model inputs (historical results, class baselines, recency weighting)
	- [ ] Implement recommendation generation service with deterministic versioned algorithm IDs
	- [ ] Add admin review workflow (`approve`, `reject`, `override`) with mandatory reason codes
	- [ ] Store before/after handicap values plus decision metadata in immutable audit records
	- [ ] Expose recommendation history endpoint for racer/club transparency

### Web — Race Control UI
- [ ] Replace inline table styles with CSS classes and fix alignment / sticky header / sticky action columns
	- [ ] Extract inline styles into dedicated stylesheet classes and remove inline style attributes
	- [ ] Implement sticky header and sticky first/last action columns with cross-browser checks
	- [ ] Fix numeric/time column alignment and responsive overflow behavior on smaller screens
	- [ ] Add visual regression snapshots for race-control table states
- [ ] Add an explicit `Finish` column, per-lap delta indicators, and boat status icons for race rows
	- [ ] Add computed `Finish` cell with clear finished/not-finished state
	- [ ] Show per-lap delta vs previous lap and highlight improving/slowing trends
	- [ ] Add status icons for `not started`, `racing`, `finished`, `dnf`, and `dns`
	- [ ] Add legend/tooltips for indicators and icons
- [ ] Add CSV/JSON export, undo last lap, and column sort/pagination controls on results tables
	- [ ] Add CSV and JSON export endpoints with current filters/sorts applied
	- [ ] Add UI controls for export with filename/date conventions
	- [ ] Implement server-backed undo-last-lap with audit trail and permission checks
	- [ ] Add client/server sorting and pagination for large race result sets

### Web — Club Dashboard
- [ ] Mature the web side into a fuller club admin hub rather than only race tooling and setup pages
	- [ ] Define IA/navigation for members, boats, duties, series, races, and audit views
	- [ ] Add member management page (search/filter, role assignment, activation/deactivation)
	- [ ] Add boat-class and handicap admin pages with validation and change history
	- [ ] Add duty planning/assignment UI with race-day coverage warnings
	- [ ] Add admin activity feed and quick actions on dashboard home
- [ ] Improve race-duty assignment workflow and mobile handoff clarity
	- [x] Add direct assignment controls in Race-Duty roster (race/member/role/status/notes)
	- [x] Add per-row remove action for duty assignments
	- [x] Add mobile-eligibility hints based on role/status compatibility
	- [x] Add unassigned coverage panel for upcoming races with quick-assign actions
	- [x] Remove bulk assignment option and related flows from duty roster UI
	- [x] Add roster filters (status/role/search/coverage)
	- [x] Add per-row mobile handoff copy action for admin-to-sailor workflow
	- [x] Add conflict override flow with richer scheduling rules (phase 2)
	- [x] Disable incompatible role/status combinations by default when mobile-enabled assignment is selected

- [ ] Add CSV export action directly on the Results Review Queue
	- [ ] Add an Export button per race row in the review queue table
	- [ ] Re-use the existing `/api/dashboard/exports/results.csv` endpoint with the race ID pre-filled
	- [ ] Trigger download inline without navigating away from the review queue

### Web — Landing Page UX/UI
- [ ] Fix race setup flow consistency and remove broken/missing field dependencies
	- [ ] Resolve `goRace` dependency on missing `raceNo` field and align required inputs with rendered form
	- [ ] Remove duplicate `goRace` click handlers and consolidate navigation logic
	- [ ] Add clear disabled/enabled state rules for primary CTA (`Go to Race`)
- [ ] Replace implicit side effects with explicit user actions
	- [ ] Remove auto-create club on input blur; require explicit create/confirm action
	- [ ] Add safe handling for duplicate/typo club names before persistence
- [ ] Improve validation, status, and error presentation
	- [ ] Replace browser `alert()` flows with inline validation and top-level status banner
	- [ ] Add per-field validation hints and actionable error text
	- [ ] Add empty-state guidance for entries table
- [x] Make landing page layout responsive and accessible
	- [x] Replace fixed-width container styles with responsive `max-width` layout rules
	- [x] Move inline step-banner styles to reusable CSS classes
	- [x] Improve label contrast, focus visibility, and keyboard navigation order
	- [x] Add ARIA live region for dynamic success/error status updates
- [x] Introduce a shared reusable top navigation/header across core web pages
	- [x] Create a reusable header partial with consistent nav links and active-page styling
	- [x] Move primary navigation into the top blue banner with a click-toggle pop-out menu (touch friendly)
	- [x] Apply shared header to landing, club entry, race control, and club dashboard pages
	- [x] Centralize logout behavior in shared navigation
	- [x] Remove obsolete prior nav styling/markup from the earlier inline nav implementation
- [x] Replace bottom landing navigation actions with next-race context panel and direct race-start action
	- [x] Show next race details (series, race number, start time, entries)
	- [x] Add `Start This Race` action to initialize session and navigate to sailor-entry flow
	- [x] Keep fallback link to choose a different race via club entry

### Mobile
- [ ] Replace the action-button grid with a fixed bottom navigation bar
	- [ ] Define navigation destinations and route/state model (`Dashboard`, `Races`, `Profile`, `Control`)
	- [ ] Implement bottom navigation with state restoration per tab
	- [ ] Migrate existing actions/pages into tab structure and remove legacy grid
	- [ ] Validate accessibility labels and selected-state semantics for nav items
- [ ] Improve authentication UX with masked passwords, show/hide toggle, IME actions, and recovery flow
	- [ ] Add password field visibility toggle and secure defaults (masked by default)
	- [ ] Add keyboard IME actions for submit/next and proper focus traversal
	- [ ] Improve validation and inline error messaging for auth forms
	- [ ] Add password reset/recovery flow endpoint integration and UI
- [ ] Improve dashboard usability with clearer latest-race grouping and tappable result cards
	- [ ] Group latest results by race/day with section headers
	- [ ] Convert result rows into tappable cards leading to detailed result view
	- [ ] Add empty/loading/error states for each dashboard block
	- [ ] Add “last updated” metadata and manual refresh affordance
- [ ] Persist login securely across restarts and restore last-opened tab / scroll state
	- [ ] Persist session cookie and non-sensitive continuity state in encrypted storage
	- [ ] Restore selected tab and per-tab scroll position on cold start
	- [ ] Add stale-session detection and graceful return to login
	- [ ] Add tests for restore behavior after process death/restart
- [ ] Enable shrinking/obfuscation and verify signing, keystore backup, key rotation, and reproducible CI builds
	- [ ] Enable R8/ProGuard for release and add keep rules for Retrofit/Gson models
	- [ ] Add signed release build config and secure keystore handling documentation
	- [ ] Define keystore backup and key-rotation operational procedure
	- [ ] Add CI release pipeline checks for deterministic/reproducible artifacts

### Web — Imports
- [ ] Improve the Imports (Paper / CSV) workflow UX and reliability
	- [ ] Clearer step-by-step guidance so it is obvious which actions to take and in what order
	- [ ] Better validation feedback on CSV preview (highlight missing/bad fields inline)
	- [ ] Confirm dialog before applying an import to avoid accidental overwrites
	- [ ] Show a diff/preview comparing current entries against the import before committing
	- [ ] Add ability to re-import / update an existing race without full re-entry

### Testing and operations
- [ ] Add unit tests for time calculations, corrected times, rankings, route responses, and mobile ViewModel/API mapping
	- [ ] Add backend unit tests for elapsed/corrected time and ranking edge cases (ties, DNF, DNS)
	- [ ] Add API response contract tests for key routes with success/error variants
	- [ ] Add mobile ViewModel tests for loading/success/error transitions
	- [ ] Add parser/mapper tests for mobile API model decoding
- [ ] Add integration tests that cover the full race lifecycle against a test or staging database
	- [ ] Create isolated test DB fixture/seeding strategy
	- [ ] Add end-to-end lifecycle tests across auth, race setup, entries, start/lap/finish, publish
	- [ ] Add failure-path tests (DB disconnect, invalid state transitions, duplicate actions)
	- [ ] Integrate integration suite into CI with artifacts/log capture
- [ ] Use Docker Compose with a production web server and environment-provided secrets for deployment
	- [ ] Add production compose profile with Gunicorn (or equivalent WSGI server)
	- [ ] Move all secrets/config to environment variables and secret stores
	- [ ] Add healthcheck/readiness probes and restart policies
	- [ ] Document deployment and rollback steps
- [ ] Add a feature flag / operational switch for race mode
	- [ ] Define feature-flag mechanism (env + DB overrides) and precedence rules
	- [ ] Add admin UI/API to toggle race mode with audit logging
	- [ ] Guard race-control endpoints/UI behind race-mode checks
	- [ ] Add tests for flag transitions during active races

---

## P2 — Quality of life, release readiness, and stretch features

### Backend
- [ ] Create a normalized analytics domain for personal handicap history, cross-club benchmarking, recommendation versioning, and athlete timelines
	- [ ] Design analytics schema and event model for handicap/race history
	- [ ] Add ETL/job flow to populate analytics tables from operational data
	- [ ] Implement recommendation-version lineage tracking for comparability over time
	- [ ] Add privacy controls and club-level data-sharing boundaries

### Web
- [ ] Add ARIA labels, keyboard navigation, and a high-contrast theme switch
	- [ ] Audit all interactive controls for ARIA roles/labels and focus order
	- [ ] Add keyboard shortcuts and full keyboard operability for race-control workflows
	- [ ] Add high-contrast theme tokens and toggle persistence
	- [ ] Validate against automated accessibility checks and manual screen-reader pass

### Mobile
- [ ] Ensure accessibility compliance with 48dp tap targets, semantics/content descriptions, TalkBack order, dynamic type support, and color contrast checks
	- [ ] Audit tap target sizes and spacing across all major screens
	- [ ] Add missing semantics/content descriptions for interactive elements
	- [ ] Validate TalkBack traversal order and heading structure
	- [ ] Test dynamic type/font scaling and prevent clipping/overlap
	- [ ] Run contrast checks for light/dark themes and error states
- [ ] Cache recent data for offline-friendly behaviour, show last-updated timestamps, and queue critical actions during brief outages
	- [ ] Define cache TTL/invalidation policy per data domain (dashboard/races/results)
	- [ ] Add per-section “last updated” timestamps in UI
	- [ ] Expand offline queue coverage and conflict resolution rules
	- [ ] Add sync-status indicator and manual retry controls
- [ ] Add a short first-run onboarding checklist for club assignment, boat setup, and first race join
	- [ ] Add first-launch detection and dismiss/persist behavior
	- [ ] Create checklist steps with completion tracking
	- [ ] Deep-link from checklist items to relevant screens/actions
	- [ ] Add reset option for onboarding in settings
- [ ] Add notifications for new races, new results, and series end updates
	- [ ] Define notification event taxonomy and trigger conditions
	- [ ] Implement push/local notification handlers with channel/category setup
	- [ ] Add opt-in settings by notification type
	- [ ] Add deeplink routing from notification taps
- [ ] Add certificate pinning if feasible
	- [ ] Evaluate backend cert rotation policy and pinning viability
	- [ ] Implement OkHttp certificate pinning for production hosts
	- [ ] Add fallback/kill-switch for emergency cert changes
	- [ ] Add instrumentation tests for pin validation behavior
- [ ] Add analytics events for critical flows such as login, join race, start race, and finish race
	- [ ] Define analytics schema/event naming and required properties
	- [ ] Instrument critical flows and key failure reasons
	- [ ] Add consent/privacy gating and data-retention rules
	- [ ] Validate analytics payload quality in QA builds
- [ ] Profile startup / first render and reduce overfetching or unnecessary recomposition churn
	- [ ] Capture baseline startup and first-render metrics on representative devices
	- [ ] Identify and remove redundant API calls during app bootstrap
	- [ ] Reduce unnecessary recompositions in major Compose screens
	- [ ] Re-measure and track performance delta after optimizations

### Testing and operations
- [ ] Create staging and production environments with separate data, rollback strategy, hotfix process, and race-day runbooks
	- [ ] Provision isolated staging/prod infra and data stores
	- [ ] Define release promotion and rollback criteria/process
	- [ ] Document hotfix workflow with owner/on-call responsibilities
	- [ ] Create race-day operational runbook and incident checklist
- [ ] Add crash reporting, alerting, release version tagging, and store-release readiness assets/disclosures
	- [ ] Integrate crash reporting SDK with environment tagging
	- [ ] Add alert routing for crash spikes and severe regressions
	- [ ] Standardize release tags/changelogs across backend/web/mobile
	- [ ] Prepare store listing assets, privacy disclosures, and release checklist
- [ ] Define a compatibility matrix for supported Android versions and representative devices
	- [ ] Select minimum supported API/device tiers and test device matrix
	- [ ] Add smoke/regression suite mapped to matrix tiers
	- [ ] Document known limitations/degradations by OS/device class
	- [ ] Review/update matrix quarterly

### Product and analytics ideas
- [ ] Add tack-by-tack intermediate targets / class analytics
	- [ ] Define tack-level metrics and data capture requirements
	- [ ] Add backend aggregation for class-level comparative analysis
	- [ ] Prototype visualization for tactical insights per race segment
- [ ] Expand heat / series standings and live multi-display socket updates
	- [ ] Design live update channel and websocket event contracts
	- [ ] Add backend pub/sub pipeline for standings and heat updates
	- [ ] Add spectator-display optimized UI with auto-refresh/failover
- [ ] Improve mobile-responsive layout, larger controls, and dark mode support across the product
	- [ ] Audit responsive breakpoints and control sizing across core pages
	- [ ] Add touch-optimized controls for race-day workflows
	- [ ] Implement consistent dark theme tokens and verify contrast
- [ ] Auto-calculate handicap corrections using the chosen formula with season rating updates
	- [ ] Finalize handicap formula parameters and governance process
	- [ ] Implement per-race and seasonal recalculation jobs
	- [ ] Add admin review/override with full audit trail
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
- [ ] Restrict mobile race-control capabilities by role/duty entitlement rather than club membership alone
- [ ] Store `race_id` when a race starts and introduce stable `entry_id` values per boat session
- [ ] Enforce request payload schemas consistently and protect race actions with race-state validation
- [ ] Catch DB disconnects consistently and return JSON errors where appropriate

### Web — Race Control UI
- [ ] Add a user-friendly fallback modal when `/api/session/entries` fails, with `Try again` and `Start new race` actions

### Web — Club Dashboard
- [ ] Build a dedicated retrospective results workflow: create/select race → add/import entries → input finish data → preview standings → approve/publish → immutable audit revisions

### Mobile
- [ ] Add explicit success feedback and per-section loading / empty / error states
- [ ] Add global network error handling, retries with backoff, and timeout/offline states
- [ ] Store auth/session data securely at rest
- [ ] Remove debug logs and PII from mobile logs/crash payloads
- [ ] Create debug vs release configs for API base URL and feature flags

---

## P1 — Important functional or trust gaps

### Backend
- [ ] Expand CRUD coverage for races and entries, including reliable start / lap / finish / results endpoints
- [ ] Add soft logs, request traces, and idempotency protection for double-click race actions
- [ ] Version mobile APIs and tighten error contracts, rate limiting, and session expiration strategy
- [ ] Add structured observability for endpoint latency, traces, and error dashboards
- [ ] Add local handicap recommendations with admin approval, reason codes, and before/after audit traceability

### Web — Race Control UI
- [ ] Replace inline table styles with CSS classes and fix alignment / sticky header / sticky action columns
- [ ] Add an explicit `Finish` column, per-lap delta indicators, and boat status icons for race rows
- [ ] Add CSV/JSON export, undo last lap, and column sort/pagination controls on results tables

### Web — Club Dashboard
- [ ] Mature the web side into a fuller club admin hub rather than only race tooling and setup pages

### Mobile
- [ ] Replace the action-button grid with a fixed bottom navigation bar
- [ ] Improve authentication UX with masked passwords, show/hide toggle, IME actions, and recovery flow
- [ ] Improve dashboard usability with clearer latest-race grouping and tappable result cards
- [ ] Persist login securely across restarts and restore last-opened tab / scroll state
- [ ] Enable shrinking/obfuscation and verify signing, keystore backup, key rotation, and reproducible CI builds

### Testing and operations
- [ ] Add unit tests for time calculations, corrected times, rankings, route responses, and mobile ViewModel/API mapping
- [ ] Add integration tests that cover the full race lifecycle against a test or staging database
- [ ] Use Docker Compose with a production web server and environment-provided secrets for deployment
- [ ] Add a feature flag / operational switch for race mode

---

## P2 — Quality of life, release readiness, and stretch features

### Backend
- [ ] Create a normalized analytics domain for personal handicap history, cross-club benchmarking, recommendation versioning, and athlete timelines

### Web
- [ ] Add ARIA labels, keyboard navigation, and a high-contrast theme switch

### Mobile
- [ ] Ensure accessibility compliance with 48dp tap targets, semantics/content descriptions, TalkBack order, dynamic type support, and color contrast checks
- [ ] Cache recent data for offline-friendly behaviour, show last-updated timestamps, and queue critical actions during brief outages
- [ ] Add a short first-run onboarding checklist for club assignment, boat setup, and first race join
- [ ] Add notifications for new races, new results, and series end updates
- [ ] Add certificate pinning if feasible
- [ ] Add analytics events for critical flows such as login, join race, start race, and finish race
- [ ] Profile startup / first render and reduce overfetching or unnecessary recomposition churn

### Testing and operations
- [ ] Create staging and production environments with separate data, rollback strategy, hotfix process, and race-day runbooks
- [ ] Add crash reporting, alerting, release version tagging, and store-release readiness assets/disclosures
- [ ] Define a compatibility matrix for supported Android versions and representative devices

### Product and analytics ideas
- [ ] Add tack-by-tack intermediate targets / class analytics
- [ ] Expand heat / series standings and live multi-display socket updates
- [ ] Improve mobile-responsive layout, larger controls, and dark mode support across the product
- [ ] Auto-calculate handicap corrections using the chosen formula with season rating updates
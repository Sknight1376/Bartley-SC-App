# Go-Live Codebase Audit

## Objective
Prepare a clean production repository by keeping only the code and assets required to run, support, and maintain the live product.

## Status update on 16 April 2026
Completed in the current repository:
- removed clearly non-production root helper files, caches, and editor artifacts
- tightened repository hygiene in [.gitignore](.gitignore)
- retained the verification suite so the release candidate can still be proved before the final repo cut

Fresh verification evidence:
- backend regression suite passed with 10 tests
- active Android compile completed successfully

Remaining final step:
- copy only the approved production set into the new clean go-live repository

---

## 1. Freeze the release baseline
- Stop feature work.
- Tag the current working version.
- Confirm the current regression suite passes.
- Record the exact deployment method and environment variables required.

## 2. Create a keep-review-remove inventory

### Keep
- Core backend application in [app/](app/)
- Deployment assets in [Dockerfile](Dockerfile), [docker-compose.prod.yml](docker-compose.prod.yml), and [init.d/init.sql](init.d/init.sql)
- Launch and support docs in [README.md](README.md), [DEPLOYMENT_QUICKSTART.md](DEPLOYMENT_QUICKSTART.md), and [GO_LIVE_AND_SUPPORT_PLAN.md](GO_LIVE_AND_SUPPORT_PLAN.md)
- Mobile app source in [mobile/sailor-android/](mobile/sailor-android/)

### Review
- Data seed/reference files such as [handicaps.csv](handicaps.csv)
- Any local-only compose or helper config still needed for support or onboarding

### Remove from the clean go-live repo
- One-off repair and inspection scripts such as [_clear_series_data.py](_clear_series_data.py), [check_schema.py](check_schema.py), [check_seriescontrol.py](check_seriescontrol.py), [fix_seriescontrol.py](fix_seriescontrol.py), and [migrate_p0_operational_schema.py](migrate_p0_operational_schema.py)
- Local helper scripts such as [build_mobile.ps1](build_mobile.ps1), [sync_mobile_android.ps1](sync_mobile_android.ps1), [reconnect_phone_backend.ps1](reconnect_phone_backend.ps1), and [reconnect_phone_backend.bat](reconnect_phone_backend.bat)
- Test harnesses and acceptance scripts such as [test_mobile_dashboard_linked_user.py](test_mobile_dashboard_linked_user.py), [test_phase1_acceptance.py](test_phase1_acceptance.py), [test_security_basics.py](test_security_basics.py), and [test_race.bat](test_race.bat)
- Test or sample data such as [minimal_test_data.sql](minimal_test_data.sql), [test_data.sql](test_data.sql), and [races/Races.csv](races/Races.csv)

---

## 3. Consolidate the codebase
- Choose one canonical repository location.
- Do not keep parallel working mirrors for release.
- Copy only the approved keep set into the new repo.
- Exclude caches, temporary files, editor settings, and build outputs.

## 4. Remove redundant code
- Delete dead scripts that are no longer part of the runtime or deployment path.
- Remove duplicate or superseded logic after checking references.
- Eliminate stale docs that describe old flows.
- Keep migrations only if they are still required for a fresh production setup.

## 5. Verify fit for purpose
- Run backend tests.
- Run the mobile compile.
- Manually verify the key live workflows:
  - login
  - member linking
  - dashboard
  - race control
  - results and series
  - admin and club flows

## 6. Production hardening check
- Ensure secrets are not committed.
- Confirm rate limiting, CSRF, password policy, and session handling are enabled.
- Remove development credentials and fallback values.
- Confirm logs are useful but do not leak sensitive data.

## 7. Repository hygiene
- Add or tighten ignore rules for caches, build outputs, local databases, and IDE folders.
- Keep the repo structure minimal and readable.
- Make the main run and deploy path obvious from the root documentation.

## 8. Create the clean go-live repo
Recommended contents:
- [app/](app/)
- [mobile/sailor-android/](mobile/sailor-android/)
- [Dockerfile](Dockerfile)
- [docker-compose.prod.yml](docker-compose.prod.yml)
- [init.d/init.sql](init.d/init.sql)
- [README.md](README.md)
- [DEPLOYMENT_QUICKSTART.md](DEPLOYMENT_QUICKSTART.md)
- [GO_LIVE_AND_SUPPORT_PLAN.md](GO_LIVE_AND_SUPPORT_PLAN.md)

## 9. Final sign-off gate
Only move to the new repo when all of the following are true:
- tests pass
- mobile build succeeds
- production env values are documented
- no obvious dead code remains
- no secrets are in source control
- deployment has been dry-run successfully

---

## Suggested execution order
1. Freeze and tag current state
2. Build keep-review-remove list
3. Remove dead scripts and test-only artifacts
4. Re-run tests and mobile build
5. Copy only approved files to a clean repo
6. Dry-run deployment
7. Go live from the clean repo

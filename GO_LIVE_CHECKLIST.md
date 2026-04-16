# Final Go-Live Checklist

This file is the single consolidated launch checklist for SailingHub, ClubHub, and SailorHub.

It replaces the earlier separate audit, deployment, and rollout notes.

---

## Overall readiness

Current position: **close to go-live** and suitable for a controlled pilot or soft launch.

Latest verified evidence:
- backend regression suite passed with 10 tests
- web app responded successfully on the local health path
- active Android compile completed successfully
- database review confirmed the current scale is fit for launch

---

## Red / Amber / Green status

| Area | Status | Notes |
|---|---|---|
| Core web and mobile functionality | Green | Main flows have been exercised and recent automated checks passed |
| Codebase cleanup and repository hygiene | Green | Dev clutter removed and ignore rules tightened |
| Database readiness | Green | Database reviewed, indexed, and currently small and healthy |
| Branding and public messaging | Green | SailingHub, ClubHub, and SailorHub naming aligned |
| Production hosting and deployment rehearsal | Amber | Final staging or production dry run still required |
| Secret rotation and production config | Amber | Must be completed before launch |
| Real-device and browser sign-off | Amber | Final end-to-end pass still needed |
| Monitoring, backups, rollback, support path | Amber | Should be verified before public rollout |
| Broad unsupervised public launch | Amber | Better after first controlled pilot |

---

## 1. Release baseline freeze

- [ ] Stop non-essential feature work
- [ ] Tag the launch candidate in source control
- [ ] Confirm the final production repository is the only canonical copy
- [ ] Record the exact deployment target and credentials ownership

## 2. Clean production repository

Keep only:
- [ ] [app/](app/)
- [ ] [mobile/sailor-android/](mobile/sailor-android/)
- [ ] [Dockerfile](Dockerfile)
- [ ] [docker-compose.prod.yml](docker-compose.prod.yml)
- [ ] [init.d/init.sql](init.d/init.sql)
- [ ] [.env.production.example](.env.production.example)
- [ ] [README.md](README.md)
- [ ] [Changes.MD](Changes.MD)

Remove or exclude from the clean repo:
- [ ] local-only scripts and one-off repair tools
- [ ] test data and sample CSV files not needed for production
- [ ] caches, editor settings, and build outputs
- [ ] duplicate mirrors or stale copies

## 3. Production configuration and secrets

- [ ] Copy [.env.production.example](.env.production.example) to a real production environment file outside source control
- [ ] Set a strong application secret
- [ ] Rotate database credentials and admin passwords
- [ ] Confirm session cookie security settings are correct
- [ ] Confirm no development fallback secrets remain in the live environment

## 4. Hosting and deployment rehearsal

Recommended first-live route:
- managed app hosting or container platform
- managed PostgreSQL in the same UK or EU region
- HTTPS only
- separate staging and production environments

### Dry-run checklist
- [ ] Provision or confirm staging
- [ ] Provision or confirm production
- [ ] Deploy the current release candidate to staging
- [ ] Run the app with the production-style config
- [ ] Confirm the health endpoint responds
- [ ] Confirm logs and restart behaviour are acceptable
- [ ] Rehearse rollback steps once

### Fast Docker route
1. Copy the example production env file
2. Set real secret values
3. Start the stack with the production compose file
4. Verify the app and health endpoint respond

## 5. Database launch checks

Already verified:
- database is currently small and fit for launch
- key indexes and query hardening have been added

Before launch, confirm:
- [ ] production backups are enabled
- [ ] restore test has been completed
- [ ] staging and production databases are separate
- [ ] database access is restricted appropriately
- [ ] monitoring is in place for future growth

## 6. Web and mobile sign-off

### ClubHub web app
- [ ] login works
- [ ] club dashboard loads
- [ ] race setup works
- [ ] race control works
- [ ] results and series views behave correctly
- [ ] admin and member management flows behave correctly

### SailorHub mobile app
- [ ] sign in works on a real device
- [ ] dashboard and profile load correctly
- [ ] upcoming races display correctly
- [ ] race control works for the intended users
- [ ] results display correctly
- [ ] offline and reconnect behaviour is acceptable

## 7. Android release readiness

- [ ] set the production API base URL for the release build
- [ ] increment version details
- [ ] use the real signing configuration
- [ ] produce a signed release build
- [ ] validate on at least one physical Android device
- [ ] publish to an internal or closed testing track first if using the Play Store

## 8. Monitoring, support, and rollback

- [ ] uptime monitoring enabled
- [ ] error logging reviewed
- [ ] support contact address confirmed
- [ ] launch-day owner and backup owner identified
- [ ] rollback steps documented and tested
- [ ] pre-launch database backup taken

## 9. Launch decision gate

Only go live when all of the following are true:
- [ ] tests are passing
- [ ] web deployment responds normally
- [ ] Android release build succeeds
- [ ] real-device checks are complete
- [ ] production secrets are set and rotated
- [ ] backups and rollback are ready
- [ ] hosting and monitoring are in place
- [ ] the clean production repository has been prepared

---

## Recommendation

The product is ready for a **controlled first launch** once the final operational items above are completed.

If these amber items are closed, the app is in a strong position for go-live.

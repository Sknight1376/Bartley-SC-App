# Go-Live and User Rollout Plan

This document outlines the steps to take Bartley-SC-App from current development state to a production launch for real club users (web + Android), then operate and support it safely.

---

## 1) Scope and launch goals

### Product surfaces in this launch
- Web app (club admin, race control, dashboard)
- Backend API (web + mobile)
- PostgreSQL database
- Android mobile app (sailor + race control flows)

### Launch goals
- Stable race-day operations (start/lap/finish/results)
- Secure handling of auth/session and secrets
- Reliable deployment + rollback process
- Real-time support path during race windows

### Exit criteria for launch readiness
- P0 checklist complete (already done)
- Critical P1 launch blockers identified and closed
- Staging sign-off completed
- Production runbook + on-call rota in place

---

## 2) Environment strategy (must-have)

Create and maintain separate environments:
- `dev` (local/dev testing)
- `staging` (production-like validation)
- `prod` (real users)

Each environment must have:
- Separate DB and credentials
- Separate base URLs
- Separate secrets
- Separate app signing/release channels where relevant

Do not share production data into staging/dev.

---

## 3) Production architecture baseline

## Backend and web
- Run Flask behind a production WSGI server (Gunicorn)
- Front with reverse proxy/TLS termination (Nginx or managed ingress)
- Use HTTPS only
- Configure request/worker timeouts for race-day load

## Database
- Managed PostgreSQL preferred (or hardened self-hosted instance)
- Enable automated backups + point-in-time recovery if available
- Restrict network access to app hosts only

## Hosting
- Use Docker image with immutable tags
- Use `docker compose` only if operationally managed; otherwise use managed container platform
- Add health checks and restart policies

### 3.1) Where should this be hosted? (decision guide)

If you are unsure, choose **managed hosting** first. It reduces operational risk on race day.

#### Option A — Managed PaaS + managed Postgres (**recommended for first live launch**)

Examples:
- Azure App Service + Azure Database for PostgreSQL
- Render Web Service + Managed PostgreSQL
- Fly.io/Railway + managed PostgreSQL

Pros:
- Fastest path to production
- Built-in TLS, scaling controls, logs, and health checks
- Lower ops burden for a small club team

Cons:
- Higher monthly cost than a single VM
- Some platform limits/customization constraints

Best when:
- Team is small
- Need reliability more than infra flexibility
- Limited DevOps capacity

#### Option B — Single cloud VM + Docker Compose + managed Postgres

Examples:
- DigitalOcean/Linode/Hetzner VM for app + Nginx
- Managed PostgreSQL from cloud provider

Pros:
- Lower app-hosting cost
- Full control of runtime and reverse proxy

Cons:
- You own patching, monitoring, hardening, and failover process
- Higher operational risk if owner is unavailable

Best when:
- Comfortable administering Linux servers
- Want lower cost but still keep DB managed

#### Option C — Fully self-hosted (on-prem/NAS/club server)

Pros:
- Maximum control

Cons:
- Highest operational and security risk
- Internet uptime/power/network are now your responsibility
- Hardest to support race-day reliability

Best when:
- Strong in-house IT + redundancy in place

### 3.2) Practical recommendation for Bartley-SC-App

For this project stage, use:
- **App/API/Web:** Managed PaaS container/web app
- **DB:** Managed PostgreSQL with automated backups
- **Storage/Artifacts:** Provider object storage for backups/export files
- **DNS/TLS:** Managed certificates + custom domain

This gives the best balance of reliability, speed, and supportability.

### 3.3) Region, data residency, and compliance

- Choose a UK or EU region for hosting and database.
- Keep prod and staging in same legal region family.
- Enable encryption at rest and in transit.
- Restrict DB to private network or allowlist app egress IP only.
- Keep an admin-access log for privileged actions.

### 3.4) Sizing baseline (starting point)

For an initial club rollout (tens to low hundreds of users):
- App instance: 1–2 vCPU, 1–2 GB RAM
- DB: 1–2 vCPU managed Postgres, 20–50 GB storage
- Enable autoscaling (or manual scale up) for race-day windows

Scale triggers to watch:
- API p95 latency > target
- DB CPU > 70% sustained
- Increased 5xx during race start/finish windows

### 3.5) Backup and disaster recovery minimums

- Automated daily DB backups (retain 14–30 days)
- Pre-release/manual snapshot before schema changes
- Restore drill at least monthly in staging
- Document RPO/RTO targets (example: RPO 15 min, RTO 60 min)

### 3.6) Monthly cost bands (rough planning, not quotes)

- Option A (managed app + managed DB): **~£70–£250/mo**
- Option B (VM app + managed DB): **~£40–£160/mo**
- Option C (self-hosted infra): variable cash cost, but highest support burden/risk

### 3.7) Target architecture blueprint (first live version)

1. DNS `app.yourclubdomain.org` → managed app endpoint
2. TLS certificate managed by platform
3. Flask (Gunicorn) container deployed from CI image tag
4. Managed PostgreSQL in same region + private access
5. Secret manager/env vars for `DATABASE_URL`, `SECRET_KEY`, API keys
6. Centralized logs + uptime checks + alerting
7. Staging environment mirrors production with smaller size

### 3.8) Hosting decision checklist

- [ ] Selected provider and region (UK/EU)
- [ ] Managed Postgres enabled with backups
- [ ] Prod/staging split with separate credentials
- [ ] Domain + TLS configured
- [ ] Monitoring and alerts configured
- [ ] Restore test completed successfully

### 3.9) Lowest-cost launch plan (desktop + laptop)

If budget is the main constraint, you can launch with near-zero hosting spend using your own machines.

#### Recommended cheap setup

- **Desktop (primary):** runs app + PostgreSQL + reverse proxy
- **Laptop (standby):** backup target + emergency failover host
- **DNS:** free dynamic DNS (or low-cost domain)
- **TLS/public access:** Cloudflare Tunnel (free tier) or equivalent

Estimated monthly cost:
- £0–£15/month (domain optional, electricity/internet not included)

#### Minimal production topology

On desktop (Docker Compose):
- `web` (Flask + Gunicorn)
- `db` (PostgreSQL)
- `proxy` (Caddy or Nginx)
- `cloudflared` (optional, for public HTTPS tunnel)

On laptop:
- Nightly backup pull (`pg_dump` files)
- Weekly restore verification
- Optional standby compose stack for manual failover

#### Hard reality / risks (important)

- Home broadband/power outages will take service down.
- Single-site hardware failure risk remains high.
- Race-day reliability is lower than managed hosting.
- You must do your own patching and backup verification.

This is acceptable for pilot/initial launch, but plan migration to managed hosting after validation.

#### Step-by-step low-cost rollout

1. **Use desktop as Linux host** (Ubuntu preferred) or stable Docker-capable OS.
2. **Create production `.env`** with strong secrets and DB credentials.
3. **Run Docker Compose stack** with restart policies (`unless-stopped`).
4. **Set up Cloudflare Tunnel** to expose only HTTPS app endpoint.
5. **Lock down firewall** (allow local admin IPs only; avoid direct DB exposure).
6. **Enable daily DB backup** to desktop + copy to laptop.
7. **Add health checks + uptime ping** (e.g., UptimeRobot free).
8. **Document failover procedure**: stop desktop, start stack on laptop, switch tunnel target.
9. **Run race-day rehearsal** including simulated desktop outage.

#### Backup policy for this setup

- Nightly full `pg_dump` (retain 14 days)
- Pre-race and pre-deploy manual backup snapshot
- Copy latest backups to laptop automatically
- Weekly restore test on laptop

#### Trigger to move off self-hosting

Migrate to managed app+DB when any of these occur:
- More than one outage in a month
- Regular concurrent race-day usage growth
- Need formal SLA/compliance posture
- On-call/support burden becomes unsustainable

---

## 4) Security hardening checklist

- Secrets only via environment/secret manager (no hardcoded keys)
- Rotate `SECRET_KEY`, DB password, and admin credentials before launch
- Enforce strong password policy for admin users
- Lock down CORS to approved origins
- Ensure secure cookie/session flags in production (`Secure`, `HttpOnly`, `SameSite`)
- Verify mobile release disables verbose HTTP body logging
- Enable dependency vulnerability scanning (Python + Android)
- Keep an access audit trail for admin actions

---

## 5) Data and migration plan

- Finalize production schema baseline
- Write/review migration scripts (schema and seed data)
- Prepare initial production data set:
  - clubs
  - boat classes
  - initial users/admins
  - initial series/race templates
- Dry-run migrations in staging
- Define rollback strategy for failed migration

---

## 6) Release pipeline (CI/CD)

## Backend/web pipeline
- Lint + unit tests
- Build Docker image
- Security scan image
- Deploy to staging automatically
- Run smoke tests against staging
- Manual approval gate
- Deploy to production
- Post-deploy smoke test

## Android pipeline
- Build `debug` for internal test
- Build signed `release` artifact
- Run unit/instrumentation tests
- Distribute to closed testing track
- Promote to production track after sign-off

Track each release with:
- version tag
- changelog
- rollback artifact

---

## 7) Mobile app distribution to real users

Preferred rollout path:
1. Internal testing (club admins + core testers)
2. Closed testing (selected sailors)
3. Staged production rollout (e.g., 10% → 50% → 100%)

Pre-release checklist:
- Correct production API base URL in release config
- Feature flags set for production
- App signing validated
- Privacy disclosures and store listing complete
- Support contact details in app/store listing

---

## 8) Observability, alerting, and SLOs

Implement before launch:
- Structured logs with request ID/correlation ID
- Metrics: request count, latency (p50/p95), error rate, DB availability
- Dashboard for critical endpoints:
  - auth/login
  - race control start/lap/finish
  - results/summary
- Alerts:
  - sustained 5xx errors
  - DB connectivity failures
  - auth failure spikes
  - elevated latency on race-control endpoints

Suggested initial SLOs:
- API availability: 99.9% during race windows
- p95 latency (critical endpoints): < 800ms
- Error rate: < 1% for authenticated traffic

---

## 9) Operational readiness and support model

Create runbooks for:
- Service down / 5xx spike
- DB unavailable / connection pool exhaustion
- Mobile cannot authenticate
- Race-control action fails during event
- Emergency rollback

Set support model:
- Named race-day on-call owner
- Escalation path (L1/L2)
- Incident channel and communication template
- Post-incident review template

Define support SLAs:
- Race-day critical incident acknowledgment: < 10 min
- Non-critical support response: same business day

---

## 10) UAT and launch rehearsal

Complete in staging with real club workflows:
- Admin login and permissions
- Series setup and race creation
- Entry management (including manual add)
- Start/lap/finish + results publish
- Mobile join race + results view
- Failure-path rehearsal (temporary DB outage/network interruption)

Run at least one full “mock race day” rehearsal end-to-end.

---

## 11) Production cutover plan

## T-7 to T-1 days
- Finalize release candidate
- Freeze non-critical changes
- Backup and migration rehearsal
- Confirm on-call rota and comms

## T-0 (launch day)
- Take pre-deploy backup
- Deploy backend/web
- Apply migrations
- Run smoke/UAT sanity checks
- Publish Android staged rollout
- Announce availability to pilot users

## T+1 to T+14
- Daily health review (errors, latency, support tickets)
- Expand rollout cohort if stable
- Patch fast on high-severity issues

---

## 12) Rollback strategy

- Keep previous backend image and DB rollback plan available
- Define objective rollback triggers (e.g., sustained critical failure > 15 min)
- One-command/one-procedure backend rollback
- Mobile rollback plan:
  - unpublish/halt rollout
  - force minimum supported version via backend if necessary

---

## 13) Documentation and training

Before launch, provide:
- Admin quick-start guide
- Race officer race-day checklist
- Sailor onboarding guide (install/login/join/results)
- Support contact and issue reporting steps

Run short training sessions:
- Club admin walkthrough
- Race control simulation

---

## 14) Immediate next actions for this repo

1. Create `staging` and `prod` environment variable templates (no secrets in repo).
2. Add production compose/server profile (Gunicorn + reverse proxy + health checks).
3. Implement request correlation IDs + structured logging.
4. Add deployment smoke-test script for `/api/health` + critical race-control endpoints.
5. Set up crash/error monitoring and dashboard alerts.
6. Prepare Android closed-testing release and pilot cohort list.
7. Schedule a full mock race-day rehearsal.

---

## 15) Launch go/no-go checklist

- [ ] Staging sign-off complete
- [ ] Security checklist complete
- [ ] Backups + restore tested
- [ ] Runbooks and on-call confirmed
- [ ] Monitoring and alerting live
- [ ] Rollback tested
- [ ] Pilot users identified and briefed
- [ ] Product owner go-live approval

When all boxes are checked, proceed with staged production rollout.

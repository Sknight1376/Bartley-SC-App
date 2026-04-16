# Deployment Quick Start

This is the fastest practical route to getting the app live.

## Recommended first-live setup

- Host the web app and API on a managed container or app platform
- Use managed PostgreSQL in the same UK or EU region
- Keep separate staging and production environments
- Use HTTPS only

## If launching with Docker first

1. Copy `.env.production.example` to `.env.production`
2. Replace all placeholder secrets with strong real values
3. Build and start the production stack:

   docker compose --env-file .env.production -f docker-compose.yml -f docker-compose.prod.yml up -d --build

4. Confirm the health endpoint responds:

   http://your-host:5000/api/health

## Pre go-live checklist

- rotate all admin passwords
- set a strong `SECRET_KEY`
- enable strict production secrets validation
- back up the database before launch
- confirm staging sign-off is complete
- confirm Android release points at the production API URL
- confirm monitoring and uptime checks are enabled

## Current launch-gate status

As of 2026-04-16, the codebase is in a good state for staging:
- backend automated checks passed with 8 tests green
- the local health endpoint responded healthy
- the Android release compile completed successfully

The main remaining go-live tasks are operational rather than code changes:
- provision staging and production hosting
- rotate secrets and admin passwords
- complete the final browser and real-device sign-off walkthroughs
- set the final Android release URL, signing config, and testing-track rollout

## Azure-first route to production

This is the recommended first live path for this app.

### Azure services to use
- Azure App Service for the web app and API
- Azure Database for PostgreSQL Flexible Server for the database
- Azure Key Vault for secrets if you want stronger secret handling later
- Azure Monitor and Application Insights for health and alerting

### Suggested first live shape
- Region: UK South or UK West
- App Service plan: Basic or Standard for first launch
- PostgreSQL Flexible Server: small managed instance with automated backups enabled
- Custom domain and managed TLS certificate

### Step-by-step rollout
1. Create a staging environment in Azure first.
2. Provision Azure Database for PostgreSQL Flexible Server in the same region as the app.
3. Create the Azure Web App and deploy the app container using the production settings from [.env.production.example](.env.production.example).
4. Set the live application settings for database URL, secret key, session security, and worker settings.
5. Run the health check and the Phase 1 smoke test against staging.
6. Point the Android release build at the production API host only after staging sign-off is complete.
7. Enable monitoring, uptime alerts, and backup checks before real user rollout.
8. Cut over the custom domain once the first staging rehearsal passes.

## Azure first staging deployment checklist

Use this as the exact first pass for a real staging deployment.

### 1. Create Azure resources
- create a resource group, for example `layline-staging-rg`
- create an Azure App Service plan in UK South or UK West
- create an Azure Web App for Containers
- create an Azure Database for PostgreSQL Flexible Server

### 2. Prepare staging secrets
Set these values in the Web App configuration:
- `DATABASE_URL`
- `SECRET_KEY`
- `REQUIRE_STRICT_SECRETS=true`
- `SESSION_COOKIE_SECURE=true`
- `SESSION_COOKIE_SAMESITE=Lax`
- `SESSION_LIFETIME_HOURS=12`
- `GUNICORN_WORKERS=2`
- `GUNICORN_THREADS=4`
- `GUNICORN_TIMEOUT=120`

### 3. Prepare the database
- allow the app to reach the PostgreSQL server
- create the staging database
- run the schema and seed/init scripts if needed
- confirm database backups are enabled

### 4. Deploy the app
- build the container image from the app folder
- push it to Azure Container Registry or another supported registry
- configure the Web App to use that image
- restart the app and confirm startup succeeds

### 5. Verify staging health
- open the staging URL
- check [app/app.py](app/app.py) health endpoint at `/api/health`
- log in with a staging admin account
- confirm the landing page, club dashboard, and mobile API routes respond

### 6. Run staging sign-off
- run the Phase 1 browser walkthrough
- run the notification confirmation script
- run the offline and reconnect device script
- record any findings in [Changes.MD](Changes.MD)

### 7. Promote to production only after sign-off
- create matching production resources
- rotate secrets again
- attach custom domain and TLS
- take a pre-launch DB backup
- cut over during a low-risk window

## Mobile app route to production

The Android app needs its own release path alongside the backend and web deployment.

### Recommended mobile release path
- keep `debug` pointing at local development only
- set the `LAYLINE_RELEASE_API_BASE_URL` Gradle property or environment variable to the real production API host before publishing
- keep release shrinking and obfuscation enabled
- generate a dedicated release signing key and store it securely
- produce a signed release build for internal testing first
- validate login, race entry, results, notifications, and offline restore on real devices
- publish initially through an internal or closed testing track before wider rollout

### Mobile production checklist

#### 1. Release configuration
- update the release `API_BASE_URL` in [mobile/sailor-android/app/build.gradle.kts](mobile/sailor-android/app/build.gradle.kts)
- increment `versionCode` and `versionName` for each release
- confirm release logging remains disabled

#### 2. Signing and build security
- create a dedicated upload keystore for the app
- store the keystore and passwords outside the repo
- document backup and recovery ownership for the signing key

#### 3. Real-device validation
- test on at least one phone that matches your likely club-user device profile
- verify sign in, club assignment, joining races, results display, notifications, and offline reconnect flow
- confirm the app points to staging before production cutover

#### 4. Distribution path
- first publish to an internal or closed testing track
- collect feedback from a small group of real sailors or race officers
- only then promote to a wider production release

#### 5. Store readiness
- confirm app icon, app name, screenshots, privacy wording, and support contact details
- prepare a short release note for each rollout
- ensure Play Store content matches the current Layline branding

### First Android release checklist

Use this for the first real test or store-ready app release.

1. Set the production or staging API URL in [mobile/sailor-android/app/build.gradle.kts](mobile/sailor-android/app/build.gradle.kts).
2. Update `versionCode` and `versionName` for the release.
3. Create or load the release signing key in Android Studio.
4. Build a signed release APK or AAB.
5. Install it on at least one physical Android device.
6. Run the mobile sign-in, dashboard, race entry, results, notification, and offline checks.
7. Fix any release-only issues found during that pass.
8. Publish to an internal or closed testing track first.
9. Review tester feedback and confirm there are no race-day blockers.
10. Promote the tested build to production only after final sign-off.

## Self-hosted option comparison

### When it makes sense
Use self-hosting only if cost is the main concern and you are comfortable owning patching, backups, failover, and race-day support.

### Typical self-hosted setup
- one desktop or mini PC running the app, database, and reverse proxy
- one laptop or spare machine as backup
- dynamic DNS or Cloudflare Tunnel for public HTTPS access
- manual backup and restore process

### Azure versus self-hosted

| Option | Cost | Reliability | Operational effort | Best use |
|---|---|---|---|---|
| Azure managed hosting | medium | high | low to medium | first real club launch |
| Self-hosted desktop or club server | low | medium to low | high | pilot or budget-constrained launch |

## Recommended hosting choice

For the first real launch, the safest route is:
- app and API on Azure App Service or equivalent managed PaaS
- managed PostgreSQL
- custom domain with managed TLS

This gives the lowest operational risk on race day.

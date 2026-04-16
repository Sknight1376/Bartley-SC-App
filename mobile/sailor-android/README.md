# Layline Sailor App

Android companion app for the Layline sailing platform.

## Current position

The app now broadly matches the Phase 1 MVP described in the main project roadmap and supports the core sailor journey:

- create and manage a sailor profile
- assign the sailor to a club
- add and manage boats
- view upcoming races
- enter races
- view latest results and personal latest races
- view web-style series standings in a mobile-friendly layout
- receive race, result, series, and duty notifications
- continue to work in degraded or offline mode using cached data and queued actions

## Tech stack

- Kotlin and Jetpack Compose
- Retrofit and OkHttp
- encrypted local preferences for session and app state
- persistent cookie-backed session continuity
- offline caching and queued action sync

## Phase 1 MVP status

### Included in the current app
- sailor profile and club assignment
- upcoming race entry flow
- latest results and personal race history
- mobile race-control support for eligible users
- Phase 1 notifications for results published, personal result summary, and upcoming race reminders
- offline support

### Remaining Phase 1 polish
- continued UI refinement for smaller screens
- deployment and build consistency across Windows and Linux mirrors
- final end-to-end device validation

## Development pathway

### Phase 1: Core sailor operations
Focus on race entry, results visibility, notifications, offline resilience, and operational race-day support.

### Phase 2: Extended sailor experience
Planned direction from the wider roadmap includes:
- sailor stats
- event entry

### Phase 3 and beyond: Community and broader engagement
Longer-term roadmap themes include:
- community stats
- social features

## Before running
1. Open the Android project in Android Studio.
2. Let Gradle sync complete.
3. Confirm the backend URL in the mobile network configuration.
4. Start the backend and ensure the test dataset or seeded sailor users exist.

## Windows and Linux sync

If you work from both the Windows repo copy and the WSL or Linux mirror, keep them explicitly in sync.

- Repo copy: mobile/sailor-android
- WSL mirror commonly used: /home/sjknight/mobile/sailor-android
- Repo mirror used for Linux compile checks: /home/sjknight/Bartley-SC-App/mobile/sailor-android

From PowerShell at the repo root:

- Push repo changes into WSL:
  - ./sync_mobile_android.ps1 -Direction ToWsl
- Pull WSL changes back into the repo:
  - ./sync_mobile_android.ps1 -Direction FromWsl

The sync excludes machine-local and build output files such as .gradle, .idea, build, local.properties, and iml files.

## Linux mirror build notes

For WSL or Linux compilation to work reliably:
- gradlew must be executable
- the mirror needs a valid local.properties
- sdk.dir should point at the local Android SDK, for example /home/sjknight/Android/Sdk

## Change backlog

Desired changes and release backlog items for the Android app are tracked centrally in [Changes.MD](../../Changes.MD).

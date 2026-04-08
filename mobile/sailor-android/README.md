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

## Change backlog

Desired changes and release backlog items for the Android app are now tracked centrally in [../../Changes.MD](../../Changes.MD).
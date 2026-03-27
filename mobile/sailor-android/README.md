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

## Notes
- Cookie storage is in-memory for now. Replace with persistent secure storage for production.
- UI is intentionally minimal starter scaffolding.

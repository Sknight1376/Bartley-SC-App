#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./deploy-device-linux.sh
#   SKIP_INSTALL=1 ./deploy-device-linux.sh
#   SKIP_REVERSE=1 ./deploy-device-linux.sh
#   ADB_PATH=/mnt/c/Users/<you>/AppData/Local/Android/Sdk/platform-tools/adb.exe ./deploy-device-linux.sh

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCAL_BUILD_DIR="${LOCAL_BUILD_DIR:-/tmp/sailor-android-build}"

echo "[0/4] Mirroring project to local writable build path: $LOCAL_BUILD_DIR"
mkdir -p "$LOCAL_BUILD_DIR"

if command -v rsync >/dev/null 2>&1; then
  rsync -a --delete \
    --exclude ".gradle" \
    --exclude "build" \
    --exclude ".idea" \
    "$PROJECT_DIR/" "$LOCAL_BUILD_DIR/"
else
  rm -rf "$LOCAL_BUILD_DIR"
  mkdir -p "$LOCAL_BUILD_DIR"
  cp -a "$PROJECT_DIR/." "$LOCAL_BUILD_DIR/"
  rm -rf "$LOCAL_BUILD_DIR/.gradle" "$LOCAL_BUILD_DIR/build" "$LOCAL_BUILD_DIR/.idea"
fi

cd "$LOCAL_BUILD_DIR"

PROJECT_CACHE_DIR="${PROJECT_CACHE_DIR:-$HOME/.gradle/project-cache/sailor-android}"
mkdir -p "$PROJECT_CACHE_DIR"

if [[ -d "$LOCAL_BUILD_DIR/.gradle" && ! -w "$LOCAL_BUILD_DIR/.gradle" ]]; then
  echo "WARN: $LOCAL_BUILD_DIR/.gradle is not writable. Using --project-cache-dir=$PROJECT_CACHE_DIR"
fi

echo "[1/4] Building debug APK in Linux environment..."
./gradlew :app:assembleDebug --stacktrace --project-cache-dir "$PROJECT_CACHE_DIR"

APK_PATH="$LOCAL_BUILD_DIR/app/build/outputs/apk/debug/app-debug.apk"
if [[ ! -f "$APK_PATH" ]]; then
  echo "ERROR: APK not found at $APK_PATH" >&2
  exit 1
fi

echo "[2/4] Build complete: $APK_PATH"

if [[ "${SKIP_INSTALL:-0}" == "1" && "${SKIP_REVERSE:-0}" == "1" ]]; then
  echo "Done (build only)."
  exit 0
fi

ADB_BIN="${ADB_PATH:-}"
if [[ -z "$ADB_BIN" ]]; then
  if command -v adb >/dev/null 2>&1; then
    ADB_BIN="$(command -v adb)"
  fi
fi

if [[ -z "$ADB_BIN" ]]; then
  for p in /mnt/c/Users/*/AppData/Local/Android/Sdk/platform-tools/adb.exe; do
    if [[ -x "$p" ]]; then
      ADB_BIN="$p"
      break
    fi
  done
fi

if [[ -z "$ADB_BIN" ]]; then
  echo "WARNING: adb not found. APK built successfully at: $APK_PATH"
  echo "Set ADB_PATH or install adb in WSL PATH to enable install/reverse."
  exit 0
fi

DEVICES_OUTPUT="$($ADB_BIN devices 2>/dev/null || true)"
READY_COUNT="$(echo "$DEVICES_OUTPUT" | grep -c $'\tdevice$' || true)"

if [[ "$READY_COUNT" -eq 0 ]]; then
  echo "WARNING: No ready device detected by adb."
  echo "$DEVICES_OUTPUT"
  echo "Tip: if device appears as unauthorized, unlock phone and accept USB debugging prompt."
  echo "APK built successfully at: $APK_PATH"
  exit 0
fi

TARGET_SERIAL="${ANDROID_SERIAL:-}"
if [[ -z "$TARGET_SERIAL" ]]; then
  TARGET_SERIAL="$(echo "$DEVICES_OUTPUT" | awk '/\tdevice$/{print $1; exit}')"
fi

ADB_ARGS=()
if [[ -n "$TARGET_SERIAL" ]]; then
  ADB_ARGS=(-s "$TARGET_SERIAL")
fi

if [[ "${SKIP_INSTALL:-0}" != "1" ]]; then
  echo "[3/4] Installing APK to connected device (${TARGET_SERIAL:-auto})..."
  "$ADB_BIN" "${ADB_ARGS[@]}" install -r "$APK_PATH"
fi

if [[ "${SKIP_REVERSE:-0}" != "1" ]]; then
  echo "[4/4] Setting port reverse tcp:5000 -> tcp:5000..."
  "$ADB_BIN" "${ADB_ARGS[@]}" reverse tcp:5000 tcp:5000
fi

echo "Done."

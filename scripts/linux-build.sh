#!/usr/bin/env bash
# FireDM Linux x64 build orchestrator. Mirrors scripts/windows-build.ps1 for
# the Linux release lane and is intended to run on Linux (GitHub Actions
# ubuntu-latest or a developer machine). PyInstaller cannot cross-compile,
# so this script refuses to run on non-Linux hosts.

set -euo pipefail

CHANNEL="dev"
ARCH="x64"
BUILD_CODE=""
BUILD_DATE=""
ALLOW_OVERWRITE=0
SKIP_TESTS=0
SKIP_LINT=0
SKIP_VALIDATION=0
PYTHON_EXE=""

usage() {
  cat <<'EOF'
Usage: scripts/linux-build.sh [options]

Options:
  --channel <dev|beta|stable>   Release channel. Default dev.
  --arch <x64>                  Linux architecture. Only x64 is implemented.
  --build-code YYYYMMDD_VN      Explicit build code (alias --build-id).
  --build-id   YYYYMMDD_VN      Explicit build code.
  --build-date YYYYMMDD         Override build date.
  --allow-overwrite             Allow rebuilding an existing build code.
  --skip-tests                  Skip pytest.
  --skip-lint                   Skip ruff.
  --skip-validation             Skip linux payload/portable validators.
  --python <path>               Python interpreter to use.
  -h | --help                   Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --channel) CHANNEL="$2"; shift 2 ;;
    --arch) ARCH="$2"; shift 2 ;;
    --build-code|--build-id) BUILD_CODE="$2"; shift 2 ;;
    --build-date) BUILD_DATE="$2"; shift 2 ;;
    --allow-overwrite) ALLOW_OVERWRITE=1; shift ;;
    --skip-tests) SKIP_TESTS=1; shift ;;
    --skip-lint) SKIP_LINT=1; shift ;;
    --skip-validation) SKIP_VALIDATION=1; shift ;;
    --python) PYTHON_EXE="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "scripts/linux-build.sh requires Linux (uname -s reports $(uname -s))." >&2
  echo "PyInstaller is not a cross-compiler. Use GitHub Actions ubuntu-latest" >&2
  echo "or a Linux host/WSL distribution." >&2
  exit 2
fi

if [[ "$ARCH" != "x64" ]]; then
  echo "Linux $ARCH lane is blocked; only x64 is implemented." >&2
  exit 2
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if [[ -z "$PYTHON_EXE" ]]; then
  if [[ -x ".venv/bin/python" ]]; then
    PYTHON_EXE=".venv/bin/python"
  else
    PYTHON_EXE="$(command -v python3.10 || command -v python3 || command -v python)"
  fi
fi

if [[ -z "$PYTHON_EXE" ]]; then
  echo "Python interpreter not found. Pass --python explicitly." >&2
  exit 2
fi

echo "Using Python: $PYTHON_EXE"
PYTHON_VERSION="$($PYTHON_EXE -c 'import sys; print(".".join(str(part) for part in sys.version_info[:2]))')"
echo "Python version: $PYTHON_VERSION"

BUILD_CODE_ARGS=()
if [[ -n "$BUILD_CODE" ]]; then
  BUILD_CODE_ARGS+=("--build-code" "$BUILD_CODE")
fi
if [[ -n "$BUILD_DATE" ]]; then
  BUILD_CODE_ARGS+=("--date" "$BUILD_DATE")
fi
if [[ "$ALLOW_OVERWRITE" -eq 1 ]]; then
  BUILD_CODE_ARGS+=("--allow-overwrite")
fi

RESOLVED_BUILD_CODE_JSON="$($PYTHON_EXE scripts/release/versioning.py select-build-code "${BUILD_CODE_ARGS[@]}" --json 2>/dev/null || true)"
if [[ -z "$RESOLVED_BUILD_CODE_JSON" ]]; then
  RESOLVED_BUILD_CODE_JSON="$($PYTHON_EXE scripts/release/versioning.py select-build-code "${BUILD_CODE_ARGS[@]}" --json)"
fi

RESOLVED_BUILD_CODE="$(printf '%s' "$RESOLVED_BUILD_CODE_JSON" | $PYTHON_EXE -c "import json, sys; print(json.load(sys.stdin)['build_code'])")"
echo "Build code: $RESOLVED_BUILD_CODE"

if [[ "$CHANNEL" == "stable" ]]; then
  export FIREDM_REQUIRE_SIGNING=1
fi

$PYTHON_EXE scripts/release/check_dependencies.py --arch "$ARCH" --channel "$CHANNEL" --skip-portable

$PYTHON_EXE -m compileall ./firedm ./scripts

if [[ "$SKIP_TESTS" -eq 0 ]]; then
  $PYTHON_EXE -m pytest -q
fi

if [[ "$SKIP_LINT" -eq 0 ]]; then
  $PYTHON_EXE -m ruff check \
    firedm/FireDM.py \
    firedm/app_paths.py \
    firedm/extractor_adapter.py \
    firedm/ffmpeg_service.py \
    firedm/tool_discovery.py \
    firedm/setting.py \
    firedm/update.py \
    tests
fi

LANE_ARGS=("scripts/release/build_linux.py" "--arch" "$ARCH" "--channel" "$CHANNEL" "--build-id" "$RESOLVED_BUILD_CODE")
if [[ "$ALLOW_OVERWRITE" -eq 1 ]]; then
  LANE_ARGS+=("--allow-overwrite")
fi
if [[ "$SKIP_VALIDATION" -eq 1 ]]; then
  LANE_ARGS+=("--skip-validation")
fi
$PYTHON_EXE "${LANE_ARGS[@]}"

echo "Linux release lane completed."
echo "Artifacts are under dist/payloads-linux, dist/portable-linux, dist/checksums, and dist/FireDM_release_manifest_${RESOLVED_BUILD_CODE}_linux.json."

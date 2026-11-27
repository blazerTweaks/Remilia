# Shared helpers for REMILIA build scripts. Sourced, not executed.
# shellcheck shell=bash

set -euo pipefail

REMILIA_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=../upstream/pins.env
source "$REMILIA_ROOT/upstream/pins.env"

# Must not start with a clang-cl option prefix: clang-cl parses a source path like
# /work/... as the MSVC option /wo and drops the file ("no input files").
# /builds/... is the prefix Mozilla's own CI uses for cross builds.
WORK="${WORK:-/builds/work}"
MOZBUILD="${MOZBUILD:-$HOME/.mozbuild}"
OUT="${OUT:-/out}"

DOWNLOADS="$WORK/downloads"
LW_DIR="$WORK/librewolf"                      # LibreWolf checkout (patch.sh expects ../assets etc.)
FF_PRISTINE="$LW_DIR/firefox-$FIREFOX_VERSION" # extracted Mozilla tarball, never modified
SRC="$LW_DIR/librewolf-$LIBREWOLF_VERSION-$LIBREWOLF_RELEASE"  # prepared tree that gets built
L10N_DIR="$WORK/l10n"
BSYS6_DIR="$WORK/bsys6"
LOGS="$WORK/logs"
MOZ_TARGET="x86_64-pc-windows-msvc"

# Staging trees (prepare.sh --staging, V1 checks) live here and nowhere else.
# Outside the LibreWolf checkout, so its `git clean` can never reach them.
STAGING_ROOT="$WORK/staging"
STAGING_MARKER=".remilia-staging"
# The preserved baseline and its inputs. Staging code refuses to delete any of
# them or anything that contains them.
PROTECTED_DIRS=("$WORK" "$DOWNLOADS" "$LW_DIR" "$FF_PRISTINE" "$SRC" "$L10N_DIR" "$BSYS6_DIR" "$LOGS")

log()  { printf '\033[1;31m==>\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31mERROR:\033[0m %s\n' "$*" >&2; exit 1; }
need() { for c in "$@"; do command -v "$c" >/dev/null || die "missing command: $c"; done; }

# assert_staging_dir <dir>: dies unless <dir> is a direct child of $STAGING_ROOT
# that is not, and does not contain, any protected directory.
assert_staging_dir() {
  local d=${1:-} real root p
  [ -n "$d" ] || die "refusing: empty staging path"
  real=$(realpath -m -- "$d")
  root=$(realpath -m -- "$STAGING_ROOT")
  case "$real" in
    "$root"/*/*|"$root"/) die "refusing: $real is not a direct child of $root" ;;
    "$root"/?*) ;;
    *) die "refusing: $real is not inside $root" ;;
  esac
  for p in "${PROTECTED_DIRS[@]}"; do
    p=$(realpath -m -- "$p")
    case "$p/" in "$real"/*) die "refusing: $real is or contains protected $p" ;; esac
  done
}

# staging_remove <dir>: validated removal of a staging tree created by staging_create.
staging_remove() {
  local d=${1:-}
  assert_staging_dir "$d"
  [ -e "$d" ] || [ -L "$d" ] || return 0
  [ ! -L "$d" ] || die "refusing: $d is a symlink"
  [ -f "$d/$STAGING_MARKER" ] || die "refusing to delete $d: it has no $STAGING_MARKER marker"
  log "removing staging tree $d"
  rm -rf --one-file-system -- "$d"
}

# staging_create <dir>: fresh, empty, marked staging directory.
staging_create() {
  local d=${1:-}
  staging_remove "$d"
  mkdir -p -- "$d"
  printf 'REMILIA staging tree created %s by %s. Never built or packaged; safe to delete.\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$0" >"$d/$STAGING_MARKER"
}

# git_at_commit <repo-url> <commit> <dir> [--blobless]
# Ensures <dir> is a git checkout whose HEAD is exactly <commit>.
git_at_commit() {
  local url=$1 commit=$2 dir=$3 mode=${4:-}
  if [ -d "$dir/.git" ] && [ "$(git -C "$dir" rev-parse HEAD 2>/dev/null)" = "$commit" ]; then
    return 0
  fi
  rm -rf "$dir"
  git init -q "$dir"
  git -C "$dir" remote add origin "$url"
  local filter=()
  [ "$mode" = "--blobless" ] && filter=(--filter=blob:none)
  # Prefer a shallow fetch of the exact commit; fall back to a full (blobless) fetch
  # for servers that refuse fetching unadvertised commits.
  if ! git -C "$dir" fetch -q --depth 1 "${filter[@]}" origin "$commit" 2>/dev/null; then
    log "server refused shallow fetch by commit; fetching history of $url"
    git -C "$dir" fetch -q --filter=blob:none origin
  fi
  if [ "$mode" = "--blobless" ]; then
    git -C "$dir" update-ref HEAD "$commit"
  else
    git -C "$dir" -c advice.detachedHead=false checkout -q "$commit"
  fi
  [ "$(git -C "$dir" rev-parse HEAD)" = "$commit" ] || die "$url: HEAD is not $commit"
}

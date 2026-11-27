#!/usr/bin/env bash
# Build the source tree: pristine Firefox -> LibreWolf layer -> REMILIA layers.
# Always starts from a fresh copy.
#
#   prepare.sh [--force]        prepare the baseline tree $SRC (the tree build.sh compiles)
#       --force                 delete an existing prepared tree (and its object directory)
#   prepare.sh --staging NAME   prepare a separate tree in $WORK/staging/NAME for V1 checks.
#                               Reads the baseline inputs, writes only under that directory:
#                               never touches $SRC, its object directory, the LibreWolf
#                               checkout or the logs in $WORK/logs.
#
# Environment (contract: remilia/README.md):
#   REMILIA_LAYERS        all (default) | none | comma list, e.g. security,privacy
#   REMILIA_LAYER_ROOT    category directory, default remilia/
#   REMILIA_EXCLUDE_FILE  LibreWolf patch exclusion list, default upstream/librewolf-exclude.txt
# Other layer roots or exclusion lists (test fixtures) are accepted only with --staging.
source "$(dirname "$0")/lib.sh"
need tar patch git python3 realpath

force=false
staging=""
while [ $# -gt 0 ]; do
  case "$1" in
    --force) force=true ;;
    --staging) [ $# -ge 2 ] || die "--staging needs a name"; staging=$2; shift ;;
    *) die "unknown argument: $1" ;;
  esac
  shift
done

LAYERS="${REMILIA_LAYERS:-all}"
LAYER_ROOT="${REMILIA_LAYER_ROOT:-$REMILIA_ROOT/remilia}"
EXCLUDE_FILE="${REMILIA_EXCLUDE_FILE:-$REMILIA_ROOT/upstream/librewolf-exclude.txt}"
SNAPSHOT="$REMILIA_ROOT/upstream/librewolf-base"
LAYERS_PY="$REMILIA_ROOT/scripts/remilia_layers.py"

[ -f "$DOWNLOADS/firefox-$FIREFOX_VERSION.sha256" ] || die "run fetch.sh first"
[ "$(git -C "$LW_DIR" rev-parse HEAD)" = "$LIBREWOLF_COMMIT" ] || die "LibreWolf checkout is not at the pinned commit; run fetch.sh"
sha256sum -c --quiet "$DOWNLOADS/firefox-$FIREFOX_VERSION.sha256" || die "Firefox tarball changed since it was verified"

if [ -n "$staging" ]; then
  # --- Staging tree: isolated from the baseline --------------------------
  $force && die "--force is not used with --staging (staging trees are always recreated)"
  [[ "$staging" =~ ^[a-z0-9][a-z0-9._-]{0,63}$ ]] || die "invalid staging name: $staging"
  [ -d "$FF_PRISTINE" ] || die "$FF_PRISTINE is missing; staging never extracts into the baseline area"
  BASE_LW_DIR=$LW_DIR
  STAGE="$STAGING_ROOT/$staging"
  staging_create "$STAGE"
  LW_DIR="$STAGE/librewolf"
  SRC="$LW_DIR/librewolf-$LIBREWOLF_VERSION-$LIBREWOLF_RELEASE"
  LOGS="$STAGE/logs"
  mkdir -p "$LW_DIR" "$LOGS"
  # A private copy of the pinned LibreWolf checkout: patch.sh edits files in it,
  # and the exclusion list edits its patches.txt. The real checkout is only read.
  log "staging: extracting LibreWolf $LIBREWOLF_COMMIT into $LW_DIR"
  git -C "$BASE_LW_DIR" archive "$LIBREWOLF_COMMIT" | tar -x -C "$LW_DIR"
  tree_kind="staging"
else
  # --- Baseline tree: only the repository's own categories ----------------
  [ "$(realpath -m "$LAYER_ROOT")" = "$(realpath -m "$REMILIA_ROOT/remilia")" ] ||
    die "REMILIA_LAYER_ROOT=$LAYER_ROOT is only allowed with --staging: fixtures never reach the tree that gets built"
  [ "$(realpath -m "$EXCLUDE_FILE")" = "$(realpath -m "$REMILIA_ROOT/upstream/librewolf-exclude.txt")" ] ||
    die "REMILIA_EXCLUDE_FILE=$EXCLUDE_FILE is only allowed with --staging"
  if [ -d "$SRC" ]; then
    $force || die "$SRC already exists (it contains the object directory). Re-run with --force to rebuild it from scratch."
    log "removing existing tree $SRC"
    rm -rf "$SRC"
  fi
  # LibreWolf's patch.sh edits files in its checkout (assets/mozconfig.new);
  # reset them so every preparation starts from the pinned commit.
  git -C "$LW_DIR" reset -q --hard "$LIBREWOLF_COMMIT"
  git -C "$LW_DIR" clean -q -fdx -e "firefox-$FIREFOX_VERSION/" -e "librewolf-*/"
  tree_kind="baseline"
fi

# --- Upstream category: LibreWolf patch exclusions -------------------------
# REMILIA_LAYERS=none means nothing REMILIA-owned, exclusions included.
# The provenance lines come from remilia_layers.py (exclusion_provenance_lines):
# a summary line, then one "LibreWolf patch excluded: <path>: <reason>" line each.
excluded="LibreWolf patches excluded: none (REMILIA_LAYERS=none)"
if [ "$LAYERS" != none ]; then
  cmp -s "$LW_DIR/assets/patches.txt" "$SNAPSHOT/patches.txt" ||
    die "LibreWolf assets/patches.txt differs from upstream/librewolf-base/patches.txt; review and refresh the snapshot (UPSTREAM.md)"
  excluded="LibreWolf patches excluded: none"
  if [ -f "$EXCLUDE_FILE" ]; then
    excluded=$(python3 "$LAYERS_PY" exclude --patches-txt "$LW_DIR/assets/patches.txt" --exclude-file "$EXCLUDE_FILE") ||
      die "LibreWolf patch exclusion list rejected"
    while IFS= read -r line; do
      case "$line" in "LibreWolf patch excluded: "*) log "excluded ${line#LibreWolf patch excluded: }" ;; esac
    done <<<"$excluded"
  fi
fi

# --- Layer 1: pristine Firefox --------------------------------------------
if [ ! -d "$FF_PRISTINE" ]; then
  log "extracting Firefox $FIREFOX_VERSION"
  tar -xf "$DOWNLOADS/firefox-$FIREFOX_VERSION.source.tar.xz" -C "$(dirname "$FF_PRISTINE")"
fi
log "copying pristine tree"
cp -a "$FF_PRISTINE" "$SRC"

# --- Layer 2: LibreWolf ---------------------------------------------------
log "staging pinned l10n"
mkdir -p "$SRC/lw"
cp -a "$L10N_DIR" "$SRC/lw/l10n"
rm -rf "$SRC/lw/l10n/.git" "$SRC/lw/l10n/.github" "$SRC/lw/l10n/LICENSE" "$SRC/lw/l10n/README"

log "applying LibreWolf $LIBREWOLF_TAG (scripts/patch.sh)"
mkdir -p "$LOGS"
(cd "$SRC" && SKIP_FETCHING_LOCALES=1 ../scripts/patch.sh "$LIBREWOLF_VERSION" "$LIBREWOLF_RELEASE") \
  >"$LOGS/patch.log" 2>&1 || { tail -30 "$LOGS/patch.log"; die "LibreWolf patch.sh failed (full log: $LOGS/patch.log)"; }
log "LibreWolf patches applied ($(grep -c '^Applying ' "$LOGS/patch.log") patches)"

# --- Build configuration for Windows cross-compilation --------------------
# Written before the REMILIA layers so that category mozconfig fragments come
# last (and are read last).
{
  echo
  echo "# --- added by REMILIA scripts/prepare.sh: Windows cross-compile ---"
  echo "ac_add_options --target=$MOZ_TARGET"
  echo "# bsys6 assets/windows.mozconfig @ $BSYS6_COMMIT"
  git -C "$BSYS6_DIR" show "$BSYS6_COMMIT:assets/windows.mozconfig"
} >>"$SRC/mozconfig"

# --- Layers 3 + 4: REMILIA categories (remilia/README.md) -----------------
if [ "$LAYERS" = none ]; then
  remilia_lines="REMILIA:   none (REMILIA_LAYERS=none): unmodified LibreWolf"
  log "REMILIA layers: none"
else
  log "REMILIA layers: $LAYERS from $LAYER_ROOT"
  python3 "$LAYERS_PY" apply --tree "$SRC" --layer-root "$LAYER_ROOT" --layers "$LAYERS" \
    --base "$SNAPSHOT" --report "$LOGS/remilia-layers.json" --provenance "$LOGS/remilia-layers.txt" >&2 ||
    die "REMILIA layers failed; the tree $SRC is incomplete and must be prepared again"
  remilia_lines="REMILIA:   layers applied (report: $LOGS/remilia-layers.json)
$(cat "$LOGS/remilia-layers.txt")"
fi

repo_rev=$(git -c safe.directory='*' -C "$REMILIA_ROOT" rev-parse HEAD 2>/dev/null || echo unknown)
if [ "$repo_rev" != unknown ] && [ -n "$(GIT_OPTIONAL_LOCKS=0 git -c safe.directory='*' -c core.autocrlf=true \
     -C "$REMILIA_ROOT" status --porcelain 2>/dev/null)" ]; then
  repo_rev="$repo_rev + uncommitted changes"
fi

cat >"$SRC/REMILIA-PROVENANCE.txt" <<EOF
Prepared $(date -u +%Y-%m-%dT%H:%M:%SZ) by REMILIA scripts/prepare.sh
Tree:      $tree_kind $SRC
Firefox:   $FIREFOX_VERSION  sha256 $(cut -d' ' -f1 "$DOWNLOADS/firefox-$FIREFOX_VERSION.sha256")
LibreWolf: $LIBREWOLF_TAG @ $LIBREWOLF_COMMIT
$excluded
l10n:      $L10N_COMMIT
bsys6:     $BSYS6_COMMIT
REMILIA repository: $repo_rev
$remilia_lines
EOF
log "prepared ($tree_kind): $SRC"

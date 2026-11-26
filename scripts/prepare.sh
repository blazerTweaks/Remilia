#!/usr/bin/env bash
# Build the source tree: pristine Firefox -> LibreWolf layer -> REMILIA layers.
# Always starts from a fresh copy. Usage: prepare.sh [--force]
#   --force  delete an existing prepared tree (and its object directory).
source "$(dirname "$0")/lib.sh"
need tar patch git

force=false
[ "${1:-}" = "--force" ] && force=true

[ -f "$DOWNLOADS/firefox-$FIREFOX_VERSION.sha256" ] || die "run fetch.sh first"
[ "$(git -C "$LW_DIR" rev-parse HEAD)" = "$LIBREWOLF_COMMIT" ] || die "LibreWolf checkout is not at the pinned commit; run fetch.sh"
sha256sum -c --quiet "$DOWNLOADS/firefox-$FIREFOX_VERSION.sha256" || die "Firefox tarball changed since it was verified"

if [ -d "$SRC" ]; then
  $force || die "$SRC already exists (it contains the object directory). Re-run with --force to rebuild it from scratch."
  log "removing existing tree $SRC"
  rm -rf "$SRC"
fi

# LibreWolf's patch.sh edits files in its checkout (assets/mozconfig.new);
# reset them so every preparation starts from the pinned commit.
git -C "$LW_DIR" reset -q --hard "$LIBREWOLF_COMMIT"
git -C "$LW_DIR" clean -q -fdx -e "firefox-$FIREFOX_VERSION/" -e "librewolf-*/"

# --- Layer 1: pristine Firefox --------------------------------------------
if [ ! -d "$FF_PRISTINE" ]; then
  log "extracting Firefox $FIREFOX_VERSION"
  tar -xf "$DOWNLOADS/firefox-$FIREFOX_VERSION.source.tar.xz" -C "$LW_DIR"
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

# --- Layers 3 + 4: REMILIA ------------------------------------------------
if [ -d "$REMILIA_ROOT/remilia" ]; then
  die "REMILIA layer exists but applying it is not implemented yet (Phase 3+)"
fi
log "REMILIA layers: none yet (Phase 2 builds unmodified LibreWolf)"

# --- Build configuration for Windows cross-compilation --------------------
{
  echo
  echo "# --- added by REMILIA scripts/prepare.sh: Windows cross-compile ---"
  echo "ac_add_options --target=$MOZ_TARGET"
  echo "# bsys6 assets/windows.mozconfig @ $BSYS6_COMMIT"
  git -C "$BSYS6_DIR" show "$BSYS6_COMMIT:assets/windows.mozconfig"
} >>"$SRC/mozconfig"

cat >"$SRC/REMILIA-PROVENANCE.txt" <<EOF
Prepared $(date -u +%Y-%m-%dT%H:%M:%SZ) by REMILIA scripts/prepare.sh
Firefox:   $FIREFOX_VERSION  sha256 $(cut -d' ' -f1 "$DOWNLOADS/firefox-$FIREFOX_VERSION.sha256")
LibreWolf: $LIBREWOLF_TAG @ $LIBREWOLF_COMMIT
l10n:      $L10N_COMMIT
bsys6:     $BSYS6_COMMIT
REMILIA:   no layers applied
EOF
log "prepared: $SRC"

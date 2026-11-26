#!/usr/bin/env bash
# Download and verify every upstream input listed in upstream/pins.env.
# Idempotent: verified inputs are kept and re-verified on each run.
source "$(dirname "$0")/lib.sh"
need curl gpg git sha256sum

mkdir -p "$DOWNLOADS"

# --- LibreWolf source at the pinned commit --------------------------------
log "LibreWolf $LIBREWOLF_TAG @ $LIBREWOLF_COMMIT"
git_at_commit "$LIBREWOLF_REPO" "$LIBREWOLF_COMMIT" "$LW_DIR"
tag_commit=$(git ls-remote "$LIBREWOLF_REPO" "refs/tags/$LIBREWOLF_TAG" | cut -f1)
if [ "$tag_commit" != "$LIBREWOLF_COMMIT" ]; then
  die "tag $LIBREWOLF_TAG now points to '${tag_commit:-nothing}', pins.env says $LIBREWOLF_COMMIT. Investigate before continuing."
fi
lw_version=$(make -s -C "$LW_DIR" version)
lw_release=$(make -s -C "$LW_DIR" release)
[ "$lw_version" = "$LIBREWOLF_VERSION" ] && [ "$lw_release" = "$LIBREWOLF_RELEASE" ] ||
  die "LibreWolf Makefile says $lw_version-$lw_release, pins.env says $LIBREWOLF_VERSION-$LIBREWOLF_RELEASE"
[ "$lw_version" = "$FIREFOX_VERSION" ] || die "LibreWolf $lw_version does not match FIREFOX_VERSION=$FIREFOX_VERSION"

# --- Firefox source tarball, GPG-verified against the pinned key ----------
tarball="$DOWNLOADS/firefox-$FIREFOX_VERSION.source.tar.xz"
for f in "$tarball" "$tarball.asc"; do
  if [ ! -s "$f" ]; then
    log "downloading $(basename "$f")"
    url="$FIREFOX_SOURCE_URL${f#"$tarball"}"
    curl -fsSL --proto '=https' --tlsv1.2 --retry 3 -o "$f.part" "$url"
    mv "$f.part" "$f"
  fi
done

log "verifying Firefox tarball signature"
gnupghome=$(mktemp -d)
trap 'rm -rf "$gnupghome"' EXIT
gpg --homedir "$gnupghome" --quiet --import "$LW_DIR/assets/MOZILLA_PUBKEY.asc" 2>/dev/null
status=$(gpg --homedir "$gnupghome" --status-fd 1 --verify "$tarball.asc" "$tarball" 2>/dev/null || true)
# VALIDSIG <signing-subkey-fpr> ... <primary-key-fpr> (last field)
primary=$(printf '%s\n' "$status" | awk '$2 == "VALIDSIG" {print $NF}')
[ -n "$primary" ] || die "Firefox tarball signature is NOT valid"
[ "$primary" = "$MOZILLA_KEY_FINGERPRINT" ] ||
  die "tarball signed by key $primary, expected Mozilla release key $MOZILLA_KEY_FINGERPRINT"
log "signature OK (primary key $primary)"
sha256sum "$tarball" | tee "$DOWNLOADS/firefox-$FIREFOX_VERSION.sha256"

# --- Firefox l10n at a pinned commit (LibreWolf's patch.sh would take HEAD) --
log "l10n @ $L10N_COMMIT"
git_at_commit "$L10N_REPO" "$L10N_COMMIT" "$L10N_DIR"

# --- bsys6 (only two files are read from it) ------------------------------
log "bsys6 @ $BSYS6_COMMIT"
git_at_commit "$BSYS6_REPO" "$BSYS6_COMMIT" "$BSYS6_DIR" --blobless

log "fetch complete"

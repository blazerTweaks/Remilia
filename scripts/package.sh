#!/usr/bin/env bash
# Package the build as a Windows zip (en-US) and copy it to $OUT with a checksum.
source "$(dirname "$0")/lib.sh"
objdir="$SRC/obj-$MOZ_TARGET"
[ -d "$objdir/dist/bin" ] || die "run build.sh first"
# Test fixtures (tests/layers/) must never be packaged. prepare.sh already
# refuses them outside staging trees; this re-checks the provenance record.
prov="$SRC/REMILIA-PROVENANCE.txt"
if grep -q '^Layer root:' "$prov" && ! grep -qx 'Layer root:  remilia' "$prov"; then
  die "$prov records a layer root other than remilia/; refusing to package"
fi

log "mach package"
(cd "$SRC" && ./mach package)
mkdir -p "$OUT"
shopt -s nullglob
zips=("$objdir"/dist/*.win64.zip)
[ ${#zips[@]} -gt 0 ] || die "no .win64.zip produced in $objdir/dist"
for z in "${zips[@]}"; do
  cp -v "$z" "$OUT/"
  (cd "$OUT" && sha256sum "$(basename "$z")" | tee "$(basename "$z").sha256")
done
cp "$SRC/REMILIA-PROVENANCE.txt" "$OUT/"
log "artifacts in $OUT"

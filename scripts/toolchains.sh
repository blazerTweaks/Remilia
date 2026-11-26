#!/usr/bin/env bash
# Download the Windows cross-compilation toolchains into $MOZBUILD.
# The artifact list and Visual Studio manifest are read from bsys6's
# assets/Dockerfile.windows at the pinned commit, so they track what LibreWolf
# uses for this Firefox version. Skips work when already done for these pins.
source "$(dirname "$0")/lib.sh"
[ -x "$SRC/mach" ] || die "run prepare.sh first"

dockerfile=$(git -C "$BSYS6_DIR" show "$BSYS6_COMMIT:assets/Dockerfile.windows")
artifacts=$(printf '%s\n' "$dockerfile" |
  sed -n '/artifact toolchain --from-build/,/&& \\$/p' | tr -d '\\' | tr ' ' '\n' |
  grep -vE '^$|mach$|^artifact$|^toolchain$|^--from-build$|^&&$' | sort -u)
vs_manifest=$(printf '%s\n' "$dockerfile" | grep -o 'build/vs/[^ ]*\.yaml' | head -1)
[ -n "$artifacts" ] && [ -n "$vs_manifest" ] || die "could not read toolchain list from bsys6 Dockerfile"

stamp="$MOZBUILD/.remilia-toolchains"
want=$(printf '%s\n%s\n%s\n' "$FIREFOX_VERSION" "$vs_manifest" "$artifacts" | sha256sum | cut -d' ' -f1)
if [ "$(cat "$stamp" 2>/dev/null)" = "$want" ]; then
  log "toolchains already present for these pins"
  exit 0
fi

log "fetching toolchain artifacts:" && printf '    %s\n' $artifacts >&2
tmp=$(mktemp -d -p "$MOZBUILD")
trap 'rm -rf "$tmp"' EXIT
# shellcheck disable=SC2086
(cd "$tmp" && "$SRC/mach" --no-interactive artifact toolchain --from-build $artifacts)
for d in "$tmp"/*/; do
  name=$(basename "$d")
  rm -rf "${MOZBUILD:?}/$name"
  mv "$d" "$MOZBUILD/$name"
done

log "fetching Visual Studio / Windows SDK files ($vs_manifest)"
rm -rf "$MOZBUILD/win-cross/vs"
(cd "$SRC" && ./mach --no-interactive python --virtualenv build \
  taskcluster/scripts/misc/get_vs.py "$vs_manifest" "$MOZBUILD/win-cross/vs")

rm -rf "$MOZBUILD/toolchains"   # download cache, as bsys6 does
echo "$want" >"$stamp"
log "toolchains ready"

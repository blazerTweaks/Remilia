#!/usr/bin/env bash
# Host entry point: run REMILIA build steps inside the pinned build container.
#
#   scripts/docker.sh image                 build the build-environment image
#   scripts/docker.sh fetch|prepare|toolchains|build|package [args]
#   scripts/docker.sh all                   fetch, prepare, toolchains, build, package
#   scripts/docker.sh shell                 interactive shell in the container
#
# Sources and object files live in Docker volumes (Linux filesystem: fast).
# The repository is mounted read-only; packaged artifacts land in ./dist.
set -euo pipefail
export MSYS_NO_PATHCONV=1   # Git Bash: do not rewrite /builds/work, /remilia, ... into Windows paths

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$root/upstream/pins.env"
[ -n "${DEBIAN_IMAGE:-}" ] || { echo "DEBIAN_IMAGE is not pinned in upstream/pins.env" >&2; exit 1; }

# Windows path for -v when running under Git Bash, POSIX path otherwise.
host_root=$( (cd "$root" && pwd -W) 2>/dev/null || echo "$root")
image_tag="remilia-build:windows-cross-$(cat "$root/build/windows-cross.Dockerfile" <(echo "$DEBIAN_IMAGE $RUST_VERSION") | sha256sum | cut -c1-12)"

build_image() {
  docker build -f "$host_root/build/windows-cross.Dockerfile" \
    --build-arg BASE_IMAGE="$DEBIAN_IMAGE" --build-arg RUST_VERSION="$RUST_VERSION" \
    -t "$image_tag" "$host_root/build"
}

run() {
  docker image inspect "$image_tag" >/dev/null 2>&1 || build_image
  mkdir -p "$root/dist"
  local tty=()
  [ -t 0 ] && [ -t 1 ] && tty=(-it)
  docker run --rm "${tty[@]}" \
    -v remilia-builds:/builds/work \
    -v remilia-mozbuild:/root/.mozbuild \
    -v "$host_root:/remilia:ro" \
    -v "$host_root/dist:/out" \
    "$image_tag" "$@"
}

cmd=${1:-}; shift || true
case "$cmd" in
  image) build_image ;;
  fetch|prepare|toolchains|build|package) run bash "/remilia/scripts/$cmd.sh" "$@" ;;
  all) for step in fetch prepare toolchains build package; do run bash "/remilia/scripts/$step.sh"; done ;;
  shell) run bash "$@" ;;
  *) sed -n '2,10p' "$0"; exit 2 ;;
esac

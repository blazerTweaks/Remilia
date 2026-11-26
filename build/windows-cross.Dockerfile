# REMILIA build environment: cross-compile Firefox/LibreWolf for Windows on Linux.
#
# Derived from LibreWolf bsys6 assets/Dockerfile.windows (MPL-2.0), commit
# af13a34f7e24ac63b9228b840964e37af042579a. Differences:
#   - no LibreWolf source tarball baked in; toolchains are fetched at build time
#     from the prepared REMILIA tree into the persistent /root/.mozbuild volume
#     (scripts/toolchains.sh), so the image does not depend on LibreWolf's forge;
#   - dropped release-only tools: ossign (third-party apt repo), s3cmd,
#     mono-complete + chocolatey (only for .nupkg packaging);
#   - added git (fetching sources inside the container).
#
# Both build args come from upstream/pins.env (passed by scripts/docker.sh);
# the base image is pinned by digest there.

ARG BASE_IMAGE
FROM ${BASE_IMAGE}

ARG RUST_VERSION
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates curl git gnupg patch make pigz xz-utils zstd zip unzip file jq \
        python3-pip msitools libc6-i386 nodejs gettext-base pkg-config mingw-w64-tools && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN test -n "$RUST_VERSION" && \
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | \
        sh -s -- -y --profile minimal --default-toolchain "$RUST_VERSION" --target x86_64-pc-windows-msvc

ENV PATH="/root/.cargo/bin:${PATH}" \
    MOZBUILD="/root/.mozbuild" \
    MOZBUILD_STATE_PATH="/root/.mozbuild"

WORKDIR /work

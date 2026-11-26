#!/usr/bin/env bash
# Compile the prepared tree. Output: $SRC/obj-x86_64-pc-windows-msvc
source "$(dirname "$0")/lib.sh"
[ -f "$SRC/REMILIA-PROVENANCE.txt" ] || die "run prepare.sh first"
[ -f "$MOZBUILD/.remilia-toolchains" ] || die "run toolchains.sh first"

mkdir -p "$LOGS"
logfile="$LOGS/build-$(date -u +%Y%m%dT%H%M%SZ).log"
log "mach build (log: $logfile)"
start=$(date +%s)
# Run from $SRC: bsys6 notes long paths can break the MASM assembler otherwise.
set +e
(cd "$SRC" && ./mach build) 2>&1 | tee "$logfile"
rc=${PIPESTATUS[0]}
set -e
elapsed=$(( $(date +%s) - start ))
printf 'exit=%s elapsed=%ss (%dh%02dm) nproc=%s\n' "$rc" "$elapsed" $((elapsed/3600)) $((elapsed%3600/60)) "$(nproc)" | tee -a "$logfile" >&2
[ "$rc" -eq 0 ] || die "build failed, see $logfile"
log "build succeeded in $((elapsed/60)) min"

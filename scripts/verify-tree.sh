#!/usr/bin/env bash
# V1 tree checks (ROADMAP.md "Validation strategy"). Prepares staging trees and
# compares them; never compiles, never writes outside $WORK/staging and $OUT.
#
# Run it through `scripts/docker.sh verify`, which mounts the remilia-builds
# volume read-only and only its staging/ subdirectory writable. The script
# refuses to run if the baseline tree is writable.
#
# Checks (results in $OUT/verify-tree/<timestamp>/):
#   - baseline read-only; staging path guards (self-test)
#   - unit tests of the category tool (GNU patch and Python of the container)
#   - REMILIA_LAYERS=none staging tree == preserved baseline tree (excluding
#     the object directory and the provenance file); every difference listed
#   - repository categories (remilia/) + exclusion list == none tree
#   - LibreWolf patch exclusion: excluding one patch changes exactly its files;
#     an unknown entry stops the preparation before the tree is copied
#   - fixtures (tests/layers/valid): each category alone and all together
#     change exactly the expected paths; overlap report; provenance hashes;
#     assembly is deterministic; every patch reverses with zero fuzz;
#     removing a patch from `series` == reverse-applying it
#   - invalid fixture sets fail against the real LibreWolf base
#   - object directory (size, mtime of every entry) and baseline tree
#     (content manifest) identical before and after
source "$(dirname "$0")/lib.sh"
need python3 patch git realpath

MANIFEST=(python3 "$REMILIA_ROOT/scripts/tree_manifest.py")
LAYERS_PY=(python3 "$REMILIA_ROOT/scripts/remilia_layers.py")
FIXTURES="$REMILIA_ROOT/tests/layers"
TREE_NAME="librewolf-$LIBREWOLF_VERSION-$LIBREWOLF_RELEASE"
OBJDIR="$SRC/obj-$MOZ_TARGET"
REPORT="$OUT/verify-tree/$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$REPORT"
exec > >(tee "$REPORT/verify.log") 2>&1
started=$(date +%s)

fails=0
record() {  # record PASS|FAIL|INFO <check> <detail>
  printf '%s\t%s\t%s\n' "$1" "$2" "${3:-}" >>"$REPORT/results.tsv"
  printf '\033[1m[%s]\033[0m %s %s\n' "$1" "$2" "${3:-}" >&2
  [ "$1" != FAIL ] || fails=$((fails + 1))
}
tree_of() { echo "$STAGING_ROOT/$1/librewolf/$TREE_NAME"; }
prep() {  # prep <name> [VAR=value ...]: prepare a staging tree, log in the report
  local name=$1; shift
  log "preparing staging tree '$name' ($*)"
  env "$@" bash "$REMILIA_ROOT/scripts/prepare.sh" --staging "$name" >"$REPORT/prepare-$name.log" 2>&1
}
keep() {  # keep <name>: copy provenance and layer report into the report
  local t; t=$(tree_of "$1")
  cp "$t/REMILIA-PROVENANCE.txt" "$REPORT/$1.provenance.txt"
  [ ! -f "$STAGING_ROOT/$1/logs/remilia-layers.json" ] || cp "$STAGING_ROOT/$1/logs/remilia-layers.json" "$REPORT/$1.layers.json"
}
manifest() { "${MANIFEST[@]}" build "$(tree_of "$1")" "$REPORT/$1.manifest" --exclude-top REMILIA-PROVENANCE.txt >/dev/null; }
compare() {  # compare <check> <a.manifest> <b.manifest> [expect-file]
  local check=$1 a=$2 b=$3 expect=${4:-} args=()
  [ -z "$expect" ] || args=(--expect "$expect")
  if "${MANIFEST[@]}" diff "$REPORT/$a" "$REPORT/$b" --json "$REPORT/$check.json" "${args[@]}" >"$REPORT/$check.txt"; then
    record PASS "$check" "$(head -1 "$REPORT/$check.txt")"
  else
    record FAIL "$check" "$(head -1 "$REPORT/$check.txt") (see $check.txt)"
  fi
}
cleanup() {
  local d
  for d in "$STAGING_ROOT"/*/; do
    if [ -f "$d/$STAGING_MARKER" ]; then staging_remove "${d%/}"; fi
  done
  return 0
}
trap cleanup EXIT

# --- 0. Preconditions ---------------------------------------------------------
[ -f "$SRC/REMILIA-PROVENANCE.txt" ] || die "baseline tree $SRC not found"
if touch "$SRC/.remilia-write-test" 2>/dev/null; then
  rm -f "$SRC/.remilia-write-test"
  die "the baseline tree is writable here; run this through scripts/docker.sh verify"
fi
record PASS baseline-read-only "$SRC cannot be written in this container"
[ -d "$STAGING_ROOT" ] && [ -w "$STAGING_ROOT" ] || die "$STAGING_ROOT is not writable"
[ -z "$(ls -A "$STAGING_ROOT")" ] || die "$STAGING_ROOT is not empty: $(ls -A "$STAGING_ROOT" | tr '\n' ' ')"
cp "$SRC/REMILIA-PROVENANCE.txt" "$REPORT/baseline.provenance.txt"

log "recording the protected state (object directory, baseline tree)"
"${MANIFEST[@]}" stat "$OBJDIR" "$REPORT/objdir-before.stat"
"${MANIFEST[@]}" build "$SRC" "$REPORT/baseline-before.manifest" \
  --exclude-top 'obj-*' --exclude-top REMILIA-PROVENANCE.txt
git -C "$LW_DIR" rev-parse HEAD >"$REPORT/librewolf-checkout-before.txt"
git -C "$LW_DIR" status --porcelain --untracked-files=no >>"$REPORT/librewolf-checkout-before.txt"

# --- 1. Staging guard self-test (scratch WORK in /tmp) -------------------------
if bash -c '
  set -euo pipefail
  export WORK=$(mktemp -d)
  source "$1/scripts/lib.sh"
  mkdir -p "$SRC" "$STAGING_ROOT/unmarked"
  ln -s "$LW_DIR" "$STAGING_ROOT/link"
  staging_create "$STAGING_ROOT/ok" && staging_remove "$STAGING_ROOT/ok" && [ ! -e "$STAGING_ROOT/ok" ]
  for bad in "" "$STAGING_ROOT" "$STAGING_ROOT/a/b" "$STAGING_ROOT/../librewolf" "$SRC" "$WORK" \
             "$STAGING_ROOT/unmarked" "$STAGING_ROOT/link"; do
    if (staging_remove "$bad") 2>/dev/null; then echo "NOT REFUSED: [$bad]"; exit 1; fi
  done
  [ -d "$SRC" ] && [ -d "$STAGING_ROOT/unmarked" ] && [ -L "$STAGING_ROOT/link" ] && [ -d "$LW_DIR" ]
  rm -rf "$WORK"' _ "$REMILIA_ROOT" >"$REPORT/guard-selftest.txt" 2>&1; then
  record PASS staging-guards "refuses root, nested, '..', baseline, WORK, unmarked and symlinked paths"
else
  record FAIL staging-guards "see guard-selftest.txt"
fi

# --- 2. Unit tests in the container ---------------------------------------------
if (cd "$FIXTURES" && python3 -B -m unittest discover -s . -p 'test_*.py') >"$REPORT/unit-tests.txt" 2>&1; then
  record PASS unit-tests "$(grep -E '^Ran ' "$REPORT/unit-tests.txt") ($(python3 --version), $(patch --version | head -1))"
else
  record FAIL unit-tests "see unit-tests.txt"
fi

# --- 3. REMILIA_LAYERS=none == baseline ---------------------------------------
if prep none REMILIA_LAYERS=none; then
  keep none; manifest none
  # Every difference is recorded. The check passes only if each one is an entry
  # that exists in the kept tree alone and was created after that tree was
  # prepared (by-products of the earlier build, such as __pycache__).
  "${MANIFEST[@]}" diff "$REPORT/baseline-before.manifest" "$REPORT/none.manifest" \
    --json "$REPORT/none-vs-baseline.json" >"$REPORT/none-vs-baseline.txt" || true
  if python3 "$REMILIA_ROOT/scripts/tree_manifest.py" classify "$REPORT/none-vs-baseline.json" "$SRC" \
       "$(sed -n 's/^Prepared \([^ ]*\) .*/\1/p' "$SRC/REMILIA-PROVENANCE.txt")" \
       >"$REPORT/none-vs-baseline-classified.txt"; then
    record PASS none-vs-baseline "$(head -1 "$REPORT/none-vs-baseline-classified.txt")"
  else
    record FAIL none-vs-baseline "$(head -1 "$REPORT/none-vs-baseline-classified.txt") (see none-vs-baseline-classified.txt)"
  fi
  mkdir -p "$REPORT/none-base"
  cp "$(tree_of none)/lw/librewolf.cfg" "$(tree_of none)/lw/policies.json" "$(tree_of none)/mozconfig" "$REPORT/none-base/"
  cp "$REMILIA_ROOT/upstream/librewolf-base/patches.txt" "$REPORT/none-base/"
  if "${LAYERS_PY[@]}" verify-base --tree "$(tree_of none)" --base "$REMILIA_ROOT/upstream/librewolf-base" \
       >"$REPORT/snapshot-check.txt" 2>&1; then
    record PASS snapshot-matches-tree "upstream/librewolf-base equals the prepared LibreWolf files"
  else
    record FAIL snapshot-matches-tree "see snapshot-check.txt"
  fi
  staging_remove "$STAGING_ROOT/none"
else
  record FAIL prepare-none "see prepare-none.log"
fi

# --- 4. Repository categories (remilia/) + exclusion list ---------------------
if prep repo; then
  keep repo; manifest repo
  compare repo-vs-none none.manifest repo.manifest
  staging_remove "$STAGING_ROOT/repo"
else
  record FAIL prepare-repo "see prepare-repo.log"
fi

# --- 5. LibreWolf patch exclusions ----------------------------------------------
"${LAYERS_PY[@]}" patch-targets "$LW_DIR/patches/msix.patch" >"$REPORT/exclude-msix.expected"
if prep exclude-msix REMILIA_EXCLUDE_FILE="$FIXTURES/exclude-msix.txt"; then
  keep exclude-msix; manifest exclude-msix
  compare exclude-msix-vs-none none.manifest exclude-msix.manifest "$REPORT/exclude-msix.expected"
  grep -q '^Applying patches/msix.patch' "$STAGING_ROOT/exclude-msix/logs/patch.log" &&
    record FAIL exclude-msix-log "msix.patch was still applied" ||
    record PASS exclude-msix-log "patch.log has $(grep -c '^Applying ' "$STAGING_ROOT/exclude-msix/logs/patch.log") of 68 patches"
  staging_remove "$STAGING_ROOT/exclude-msix"
else
  record FAIL prepare-exclude-msix "see prepare-exclude-msix.log"
fi
if prep exclude-unknown REMILIA_EXCLUDE_FILE="$FIXTURES/exclude-unknown.txt"; then
  record FAIL exclude-unknown "preparation succeeded with an unknown exclusion"
elif grep -q 'appears 0 times' "$REPORT/prepare-exclude-unknown.log" && [ ! -e "$(tree_of exclude-unknown)" ]; then
  record PASS exclude-unknown "refused before the Firefox tree was copied"
else
  record FAIL exclude-unknown "failed for another reason (see prepare-exclude-unknown.log)"
fi
staging_remove "$STAGING_ROOT/exclude-unknown"

# --- 6. Fixtures: each category alone, then all -------------------------------
VALID="$FIXTURES/valid"
for L in build-fixes security privacy branding all; do
  name="fx-$L"
  "${LAYERS_PY[@]}" expected --layer-root "$VALID" --layers "$L" >"$REPORT/$name.expected"
  if ! prep "$name" REMILIA_LAYER_ROOT="$VALID" REMILIA_LAYERS="$L"; then
    record FAIL "prepare-$name" "see prepare-$name.log"; continue
  fi
  keep "$name"; manifest "$name"
  compare "$name-vs-none" none.manifest "$name.manifest" "$REPORT/$name.expected"
  if [ "$L" != all ]; then staging_remove "$STAGING_ROOT/$name"; fi
done

T=$(tree_of fx-all)
if [ -d "$T" ]; then
  # Provenance and overlap report
  prov="$REPORT/fx-all.provenance.txt"
  if [ "$(grep -c '^Category .*: sha256 [0-9a-f]\{64\}' "$prov")" = 4 ] && grep -q '^Note: runtime-unverified' "$prov" &&
     grep -q "^LibreWolf: $LIBREWOLF_TAG @ $LIBREWOLF_COMMIT" "$prov" && grep -q "^Firefox:   $FIREFOX_VERSION" "$prov"; then
    record PASS provenance "versions, commits, 4 category hashes, runtime-unverified note recorded"
  else
    record FAIL provenance "see fx-all.provenance.txt"
  fi
  if python3 -c 'import json,sys; o=json.load(open(sys.argv[1]))["overlaps"]; sys.exit(0 if o.get("README.md")==["security","privacy"] else 1)' \
       "$REPORT/fx-all.layers.json"; then
    record PASS overlap-report "README.md reported as touched by security and privacy"
  else
    record FAIL overlap-report "see fx-all.layers.json"
  fi
  # Determinism: assemble twice (different REMILIA_LAYERS order) from the none tree's base files
  det=PASS
  for i in 1 2; do
    order=$([ $i = 1 ] && echo all || echo branding,privacy,security,build-fixes)
    "${LAYERS_PY[@]}" assemble --base "$REPORT/none-base" --layer-root "$VALID" --layers "$order" \
      --out "$REPORT/assemble-$i" >/dev/null 2>&1 || det=FAIL
  done
  cmp -s "$REPORT/assemble-1/librewolf.cfg" "$T/lw/librewolf.cfg" || det=FAIL
  cmp -s "$REPORT/assemble-1/policies.json" "$T/lw/policies.json" || det=FAIL
  cmp -s "$REPORT/assemble-1/mozconfig" "$T/mozconfig" || det=FAIL
  diff -r "$REPORT/assemble-1" "$REPORT/assemble-2" >/dev/null || det=FAIL
  record $det assembly-deterministic "two independent assemblies and the prepared tree are byte-identical"
  cp "$T/lw/librewolf.cfg" "$REPORT/fx-all.librewolf.cfg"
  cp "$T/lw/policies.json" "$REPORT/fx-all.policies.json"
  cp "$T/mozconfig" "$REPORT/fx-all.mozconfig"

  # Removal == reverse: reverse security/0001 in the all tree
  REMOVE=security/patches/0001-readme-top.patch
  if (cd "$T" && patch -R -p1 --fuzz=0 --batch --no-backup-if-mismatch --reject-file=- -i "$VALID/$REMOVE") \
       >"$REPORT/reverse-one.txt" 2>&1; then
    manifest fx-all; mv "$REPORT/fx-all.manifest" "$REPORT/fx-all-reversed-one.manifest"
    record PASS reverse-one "$REMOVE reversed with zero fuzz after the later privacy patch on the same file"
  else
    record FAIL reverse-one "see reverse-one.txt"
  fi
  # Reverse every remaining patch, last applied first
  rev_ok=PASS
  "${LAYERS_PY[@]}" patches --layer-root "$VALID" --layers all | grep -v " $VALID/$REMOVE\$" | tac >"$REPORT/reverse-all.order"
  while read -r cat p; do
    (cd "$T" && patch -R -p1 --fuzz=0 --batch --no-backup-if-mismatch --reject-file=- -i "$p") >>"$REPORT/reverse-all.txt" 2>&1 ||
      { rev_ok=FAIL; echo "FAILED: $cat $p" >>"$REPORT/reverse-all.txt"; }
  done <"$REPORT/reverse-all.order"
  record $rev_ok reverse-all "every fixture patch reverses with zero fuzz"
  "${LAYERS_PY[@]}" expected --layer-root "$VALID" --layers all --no-patches >"$REPORT/fx-all-reversed.expected"
  manifest fx-all; mv "$REPORT/fx-all.manifest" "$REPORT/fx-all-reversed.manifest"
  compare fx-all-reversed-vs-none none.manifest fx-all-reversed.manifest "$REPORT/fx-all-reversed.expected"
  staging_remove "$STAGING_ROOT/fx-all"

  # Same layer root without the patch: must equal the tree where it was reversed
  LR_STAGE="$STAGING_ROOT/layers-minus-one"
  staging_create "$LR_STAGE"
  LR="$LR_STAGE/layers"
  cp -r "$VALID" "$LR"
  rm "$LR/$REMOVE"
  sed -i '/^0001-readme-top.patch$/d' "$LR/security/series"
  diff -r "$VALID" "$LR" >"$REPORT/layers-minus-one.diff" || true
  if prep fx-minus-one REMILIA_LAYER_ROOT="$LR" REMILIA_LAYERS=all; then
    keep fx-minus-one; manifest fx-minus-one
    compare removal-equals-reverse fx-all-reversed-one.manifest fx-minus-one.manifest
    staging_remove "$STAGING_ROOT/fx-minus-one"
  else
    record FAIL prepare-fx-minus-one "see prepare-fx-minus-one.log"
  fi
  staging_remove "$LR_STAGE"
fi

# --- 7. Invalid fixture sets against the real LibreWolf base -------------------
for case in "$FIXTURES"/invalid/*/; do
  c=$(basename "$case"); expect=$(cat "$case/EXPECT")
  if "${LAYERS_PY[@]}" assemble --base "$REPORT/none-base" --layer-root "$case/layers" --layers all \
       --out "$REPORT/invalid-out" >"$REPORT/invalid-$c.txt" 2>&1; then
    record FAIL "invalid-$c" "was accepted"
  elif grep -qF -- "$expect" "$REPORT/invalid-$c.txt"; then
    record PASS "invalid-$c" "refused: $expect"
  else
    record FAIL "invalid-$c" "refused for another reason (see invalid-$c.txt)"
  fi
done
rm -rf "$REPORT/invalid-out"

# --- 8. Protected state unchanged -------------------------------------------------
"${MANIFEST[@]}" stat "$OBJDIR" "$REPORT/objdir-after.stat"
if cmp -s "$REPORT/objdir-before.stat" "$REPORT/objdir-after.stat"; then
  record PASS objdir-unchanged "$(head -1 "$REPORT/objdir-after.stat" | tr -d '#') (every path, size and mtime identical)"
else
  record FAIL objdir-unchanged "diff objdir-before.stat objdir-after.stat"
fi
"${MANIFEST[@]}" build "$SRC" "$REPORT/baseline-after.manifest" --exclude-top 'obj-*' --exclude-top REMILIA-PROVENANCE.txt
compare baseline-unchanged baseline-before.manifest baseline-after.manifest
cmp -s "$SRC/REMILIA-PROVENANCE.txt" "$REPORT/baseline.provenance.txt" &&
  record PASS baseline-provenance-unchanged "" || record FAIL baseline-provenance-unchanged ""
git -C "$LW_DIR" rev-parse HEAD >"$REPORT/librewolf-checkout-after.txt"
git -C "$LW_DIR" status --porcelain --untracked-files=no >>"$REPORT/librewolf-checkout-after.txt"
cmp -s "$REPORT/librewolf-checkout-before.txt" "$REPORT/librewolf-checkout-after.txt" &&
  record PASS librewolf-checkout-unchanged "$(head -1 "$REPORT/librewolf-checkout-after.txt")" ||
  record FAIL librewolf-checkout-unchanged ""

cleanup
left=$(ls -A "$STAGING_ROOT")
[ -z "$left" ] && record PASS staging-cleaned "$STAGING_ROOT is empty" || record FAIL staging-cleaned "left: $left"

elapsed=$(( $(date +%s) - started ))
pass=$(grep -c '^PASS' "$REPORT/results.tsv" || true)
printf 'V1 finished in %dm%02ds: %s passed, %s failed. Report: %s\n' $((elapsed/60)) $((elapsed%60)) "$pass" "$fails" "$REPORT" >&2
[ "$fails" -eq 0 ]

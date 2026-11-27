# Validation harness (Windows x64)

`validate_win64.py` collects evidence for the validation checklist in
ROADMAP.md ("Validation checklist"). It does not decide PASS/FAIL. A person reviews
`results.json`, the logs and the screenshots, then writes the verdicts to
`internal/evidence/<date>-<build>/`, a local folder ignored by Git; validation
records are never committed. The record states the build identity (provenance
file and package sha256), the machine, what was checked and how, the result,
and anything not checked with the reason. Failures are recorded, not hidden. A
check that cannot apply is marked not applicable with the reason, never passed.

The harness only observes the browser. It never patches or reconfigures the
build under test. The few test-only prefs it sets in its throwaway profiles are
recorded in `results.json` (`suite.test_prefs_set`).

## Tools (outside the repository, pinned)

| Tool | Version | Integrity |
|---|---|---|
| Python | 3.10+ | — |
| selenium | 4.54.0 (`pip install "selenium==4.*"`) | PyPI |
| pefile | 2024.8.26 | PyPI |
| geckodriver | 0.37.1, `geckodriver-v0.37.1-win64.zip` | sha256 `dfed9315abe8d2fbc1b6161a2ee8002452e79cf05ee92fdc653a4e26bc35edd8` (GitHub release digest) |
| git | any | — (used to confirm that `--out` is ignored by Git) |

geckodriver runs with `--allow-system-access` so that chrome-context scripts
can read Gecko's own diagnostics (Troubleshoot snapshot, AddonManager,
Downloads, profile service).

## Reference browser

Sandbox and process-model results are compared with **official Firefox** of the
same version, run on the same machine in `--snapshot-only` mode. For Firefox 161:
`Firefox Setup 161.0.exe` (win64, en-US) from `archive.mozilla.org`. Its
SHA-512 matches `SHA512SUMS`, which is GPG-signed by Mozilla's release key
`14F26682D0916CDD81E37B6D61B7B526D98F0353`, and its Authenticode signature is
valid (Mozilla Corporation). It is extracted with 7-Zip and **not installed**.

## Running

From the repository root:

```sh
python tests/validation/validate_win64.py --app-dir <unzipped>/librewolf --exe librewolf.exe \
  --geckodriver geckodriver.exe --zip <package>.win64.zip --out internal/evidence/<date>-<build>/

python tests/validation/validate_win64.py --app-dir <ff161>/core --exe firefox.exe \
  --geckodriver geckodriver.exe --out internal/evidence/<date>-<build>/ --snapshot-only
```

For the reference run, `<build>` names the official Firefox build.

Rules for `--out`, all checked before anything is written:

- `--out` is required. A relative path is resolved against the repository
  root (found through `upstream/pins.env`), never against the current
  directory, so the same command gives the same destination from any
  directory.
- The destination must be a directory inside `internal/evidence/`, with that
  exact case. Every other place is refused: elsewhere in the repository,
  absolute paths outside it, and symbolic links that lead out of it.
- Git is required: `git check-ignore` must confirm that the destination is
  ignored, so evidence cannot be committed by accident.
- A directory that is not empty is refused. Pass `--overwrite` to reuse it.

These rules have unit tests that run on the host without a browser:
`python -m unittest discover -s tests/validation`.

Browser windows open and close on the desktop while it runs. The `startup`
step launches the browser **without** automation and captures the screen.
The `profiles` step creates a named profile through `-CreateProfile` in the
application's real profile root (`%APPDATA%\<vendor>\<app>`) and deletes it at
the end.

## What each step collects

| Step | Evidence |
|---|---|
| `package` | zip sha256 and CRC test, double extraction compared file by file, essential files, every PE: machine type, PE32+, ASLR / high-entropy VA / DEP / CFG, imported DLLs not found in the package or System32, Authenticode status |
| `startup` | `--version`, process tree with Gecko process types, window title, desktop screenshot, exit code after a normal close, leftover processes, minidumps |
| `suite` | Troubleshoot snapshot (application, Fission, sandbox, graphics, policies), sandbox prefs, real-site loads with screenshots, JS/web-platform probes, media `canPlayType` and real playback progress, process list with several sites open, uBlock Origin presence + A/B blocking probe (enabled vs disabled) + dashboard, signed extension lifecycle, unsigned extension rejection, downloads (hash, Mark-of-the-Web, panel) |
| `profiles` | create, write, restart, read back (pref, bookmark, history, cookies), isolation from another profile, delete |

## Limits

- Automation runs with a WebDriver session (`navigator.webdriver` is true).
  The `startup` step exists to observe behaviour without it.
- Media playback is verified by decoding progress (currentTime, decoded frames),
  not by listening. Audio output reaching the speakers is not verified.
- Rendering correctness is judged from screenshots by a person.
- Real sites change. A failed load is recorded with the error and judged
  case by case.

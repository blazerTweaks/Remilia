#!/usr/bin/env python3
r"""REMILIA Phase 2 validation harness for a Windows x64 build (ROADMAP.md, Phase 2 step 3).

Collects *evidence* for each checklist item; it does not decide PASS/FAIL on its
own. A human reviews results.json, the logs and the screenshots, and writes the
verdicts into internal/evidence/ (local only, ignored by Git, never published).
This tool never modifies the browser under test.

Usage (Windows host, from any directory):
  python tests/validation/validate_win64.py --app-dir <unzipped browser dir> --exe librewolf.exe \
      --geckodriver <geckodriver.exe> --out internal/evidence/<date>-<build>/ [--zip <package.zip>] \
      [--only package,startup,suite,profiles] [--snapshot-only] [--overwrite]

--out must be a directory inside internal/evidence/ of this repository. A
relative --out is resolved against the repository root (found through
upstream/pins.env), never against the current directory. The destination must
be ignored by Git (git check-ignore) and must be empty unless --overwrite is
given. All of this is checked before anything is written.

Requirements: Python 3.10+, selenium 4.x, pefile, geckodriver, git (see README.md).
"""

import argparse
import csv
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
import zipfile
from pathlib import Path

RESULTS = {}

REPO_MARKER = ("upstream", "pins.env")
EVIDENCE_PARTS = ("internal", "evidence")


class OutputError(Exception):
    """The requested --out destination is not acceptable."""


def find_repo_root(script=__file__):
    """Repository root (two levels above tests/validation/), or None without upstream/pins.env."""
    root = Path(script).resolve().parents[2]
    return root if root.joinpath(*REPO_MARKER).is_file() else None


def git_check_ignore(repo_root, rel_posix):
    """Exit status of 'git check-ignore -q' (0: ignored, 1: not ignored), or -1 without git."""
    try:
        r = subprocess.run(["git", "-C", str(repo_root), "check-ignore", "-q", "--", rel_posix],
                           capture_output=True)
    except FileNotFoundError:
        return -1
    return r.returncode


def resolve_out(arg, repo_root, overwrite=False, check_ignore=git_check_ignore):
    """Resolve and validate --out before anything is written. Returns the absolute directory."""
    if repo_root is None:
        raise OutputError("repository root not found (no upstream/pins.env two levels above this "
                          "script); run the copy of this tool that is inside the REMILIA repository")
    raw = str(arg)
    p = Path(raw)
    if p.drive and not p.is_absolute():
        raise OutputError(f"--out {raw}: drive-relative paths are not accepted")
    if not p.is_absolute():
        p = Path(repo_root) / p
    norm = Path(os.path.normpath(p))
    root = Path(os.path.normpath(repo_root))
    try:
        rel = norm.relative_to(root)
    except ValueError:
        raise OutputError(f"--out {raw} is outside the repository; use internal/evidence/<date>-<build>/") from None
    if rel.parts[:2] != EVIDENCE_PARTS or len(rel.parts) < 3:
        raise OutputError(f"--out {raw} must be a directory inside internal/evidence/ "
                          f"(resolved to {rel.as_posix() or '.'})")
    real = norm.resolve()
    evidence = root.joinpath(*EVIDENCE_PARTS).resolve()
    if real == evidence or not real.is_relative_to(evidence):
        raise OutputError(f"--out {raw} resolves outside internal/evidence/ ({real})")
    status = check_ignore(root, rel.as_posix() + "/")
    if status == -1:
        raise OutputError("git not found: cannot confirm that --out is ignored by Git")
    if status != 0:
        raise OutputError(f"--out {rel.as_posix()} is not ignored by Git (git check-ignore exit {status}); "
                          "refusing to write evidence that could be committed")
    if real.exists():
        if not real.is_dir():
            raise OutputError(f"--out {raw} exists and is not a directory")
        if any(real.iterdir()) and not overwrite:
            raise OutputError(f"--out {raw} is not empty; pass --overwrite to reuse it")
    return real


def record(section, key, value):
    RESULTS.setdefault(section, {})[key] = value
    print(f"[{section}] {key}: {json.dumps(value, default=str)[:300]}", flush=True)


def guarded(section):
    """Run a test section; record any exception instead of aborting the run."""
    def deco(fn):
        def wrapper(*a, **kw):
            try:
                return fn(*a, **kw)
            except Exception as e:  # noqa: BLE001 - evidence collection must continue
                record(section, "EXCEPTION", f"{type(e).__name__}: {e}\n{traceback.format_exc()}")
        return wrapper
    return deco


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ps(command, timeout=120):
    r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
                       capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip(), r.stderr.strip(), r.returncode


def screen_capture(path):
    """Capture the whole primary screen (used where WebDriver is not involved)."""
    cmd = ("Add-Type -AssemblyName System.Windows.Forms,System.Drawing;"
           "$b=[System.Windows.Forms.Screen]::PrimaryScreen.Bounds;"
           "$bmp=New-Object System.Drawing.Bitmap $b.Width,$b.Height;"
           "$g=[System.Drawing.Graphics]::FromImage($bmp);"
           "$g.CopyFromScreen($b.Location,[System.Drawing.Point]::Empty,$b.Size);"
           f"$bmp.Save('{path}');")
    return ps(cmd)


def browser_processes(exe_name):
    """List running browser processes with their Gecko process type."""
    out, _, _ = ps(f"Get-CimInstance Win32_Process -Filter \"name='{exe_name}'\" | "
                   "Select-Object ProcessId,ParentProcessId,CommandLine | ConvertTo-Csv -NoTypeInformation")
    procs = []
    for row in csv.DictReader(io.StringIO(out)):
        cl = row.get("CommandLine") or ""
        kind = "parent"
        if "-contentproc" in cl:
            # Gecko passes the process type as the last argument of -contentproc command lines.
            kind = cl.strip().split()[-1].strip('"')
        procs.append({"pid": row["ProcessId"], "ppid": row["ParentProcessId"], "type": kind})
    return procs


# --------------------------------------------------------------------- package

@guarded("package")
def check_package(app_dir, zip_path):
    import pefile

    if zip_path:
        record("package", "zip", str(zip_path))
        record("package", "zip_sha256", sha256(zip_path))
        with zipfile.ZipFile(zip_path) as z:
            record("package", "zip_testzip_first_bad_member", z.testzip())  # None == all CRCs OK
            names = z.namelist()
            record("package", "zip_members", len(names))
            # Extract twice and compare every file hash: extraction is deterministic.
            hashes = []
            for _ in range(2):
                d = Path(tempfile.mkdtemp(prefix="remilia-zip-"))
                z.extractall(d)
                hashes.append({str(p.relative_to(d)): sha256(p) for p in d.rglob("*") if p.is_file()})
                shutil.rmtree(d, ignore_errors=True)
            record("package", "re_extraction_identical", hashes[0] == hashes[1])
            record("package", "re_extraction_files", len(hashes[0]))

    essential = ["librewolf.exe", "xul.dll", "nss3.dll", "mozglue.dll", "omni.ja",
                 "browser/omni.ja", "application.ini", "platform.ini", "dependentlibs.list",
                 "distribution/policies.json", "defaults/pref/local-settings.js", "librewolf.cfg"]
    record("package", "essential_files",
           {f: (app_dir / f).exists() for f in essential})

    sys32 = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32"
    pe_report, unresolved = {}, {}
    pe_files = sorted(p for p in app_dir.rglob("*") if p.suffix.lower() in (".exe", ".dll"))
    for p in pe_files:
        pe = pefile.PE(str(p), fast_load=True)
        pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"],
                                               pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_DELAY_IMPORT"]])
        dc = pe.OPTIONAL_HEADER.DllCharacteristics
        rel = str(p.relative_to(app_dir))
        pe_report[rel] = {
            "machine": hex(pe.FILE_HEADER.Machine),      # 0x8664 == x64
            "pe32plus": pe.OPTIONAL_HEADER.Magic == 0x20B,
            "aslr": bool(dc & 0x0040), "high_entropy_va": bool(dc & 0x0020),
            "dep_nx": bool(dc & 0x0100), "cfg": bool(dc & 0x4000),
        }
        imports = set()
        for attr in ("DIRECTORY_ENTRY_IMPORT", "DIRECTORY_ENTRY_DELAY_IMPORT"):
            for entry in getattr(pe, attr, []):
                imports.add(entry.dll.decode(errors="replace"))
        for dll in imports:
            low = dll.lower()
            if low.startswith(("api-ms-win-", "ext-ms-")):
                continue  # API sets, resolved by the OS loader
            if (p.parent / dll).exists() or (app_dir / dll).exists() or (sys32 / dll).exists():
                continue
            unresolved.setdefault(rel, []).append(dll)
        pe.close()
    record("package", "pe_files", len(pe_files))
    record("package", "pe_all_x64", all(v["machine"] == "0x8664" and v["pe32plus"] for v in pe_report.values()))
    for flag in ("aslr", "high_entropy_va", "dep_nx", "cfg"):
        record("package", f"pe_missing_{flag}", [k for k, v in pe_report.items() if not v[flag]])
    record("package", "unresolved_imports", unresolved)
    out, _, _ = ps(f"(Get-AuthenticodeSignature '{app_dir / 'librewolf.exe'}').Status")
    record("package", "authenticode_status", out)
    (OUT / "pe_report.json").write_text(json.dumps(pe_report, indent=1))


# --------------------------------------------------------------------- startup

@guarded("startup")
def check_startup(exe, exe_name):
    """Launch without any automation, the way a user would, and observe."""
    prof = Path(tempfile.mkdtemp(prefix="remilia-startup-"))
    out, _, _ = ps(f"& '{exe}' --version | Out-String")
    record("startup", "version_output", out)
    t0 = time.time()
    proc = subprocess.Popen([str(exe), "-no-remote", "-profile", str(prof), "https://www.wikipedia.org/"])
    time.sleep(25)
    record("startup", "alive_after_25s", proc.poll() is None)
    procs = browser_processes(exe_name)
    record("startup", "processes", procs)
    record("startup", "process_types", sorted({p["type"] for p in procs}))
    out, _, _ = ps(f"(Get-Process -Id {proc.pid}).MainWindowTitle")
    record("startup", "main_window_title", out)
    screen_capture(str(OUT / "startup_desktop.png"))
    ps(f"(Get-Process -Id {proc.pid}).CloseMainWindow() | Out-Null")
    try:
        rc = proc.wait(timeout=60)
    except subprocess.TimeoutExpired:
        rc = "did not exit within 60s"
        proc.kill()
    record("startup", "exit_code_after_close", rc)
    record("startup", "session_seconds", round(time.time() - t0, 1))
    time.sleep(3)
    record("startup", "leftover_processes", len(browser_processes(exe_name)))
    record("startup", "profile_created_files", len(list(prof.rglob("*"))))
    record("startup", "minidumps", [p.name for p in (prof / "minidumps").glob("*")] if (prof / "minidumps").exists() else [])
    shutil.rmtree(prof, ignore_errors=True)


# --------------------------------------------------------------- webdriver suite

def make_driver(exe, geckodriver, profile_dir, extra_prefs=None):
    from selenium import webdriver
    from selenium.webdriver.firefox.options import Options
    from selenium.webdriver.firefox.service import Service

    opts = Options()
    opts.binary_location = str(exe)
    opts.add_argument("-profile")
    opts.add_argument(str(profile_dir))
    # Keep the test profile as close to user defaults as possible: do not let the
    # Remote Agent apply its "recommended" automation prefs.
    opts.set_preference("remote.prefs.recommended", False)
    for k, v in (extra_prefs or {}).items():
        opts.set_preference(k, v)
    # --allow-system-access: chrome-context scripts are needed to read Gecko's own
    # diagnostics (Troubleshoot snapshot, AddonManager, Downloads, profile service).
    service = Service(executable_path=str(geckodriver), service_args=["--allow-system-access"],
                      log_output=str(OUT / f"geckodriver-{profile_dir.name}.log"))
    d = webdriver.Firefox(options=opts, service=service)
    d.set_page_load_timeout(60)
    d.set_script_timeout(180)
    return d


def chrome(d, script, *args):
    with d.context(d.CONTEXT_CHROME):
        return d.execute_script(script, *args)


SNAPSHOT_JS = """
const {Troubleshoot} = ChromeUtils.importESModule("resource://gre/modules/Troubleshoot.sys.mjs");
return Troubleshoot.snapshot().then(s => JSON.stringify(s));
"""

SANDBOX_PREFS_JS = """
const out = {};
for (const k of Services.prefs.getChildList("security.sandbox.")) {
  const t = Services.prefs.getPrefType(k);
  out[k] = t == Services.prefs.PREF_INT ? Services.prefs.getIntPref(k)
         : t == Services.prefs.PREF_BOOL ? Services.prefs.getBoolPref(k)
         : Services.prefs.getStringPref(k);
}
out["fission.autostart"] = Services.prefs.getBoolPref("fission.autostart", null);
return out;
"""


def snapshot(d, name):
    snap = json.loads(chrome(d, SNAPSHOT_JS))
    (OUT / f"snapshot-{name}.json").write_text(json.dumps(snap, indent=1))
    return snap


def shot(d, name, chrome_ctx=False):
    path = OUT / f"{name}.png"
    if chrome_ctx:
        with d.context(d.CONTEXT_CHROME):
            d.get_screenshot_as_file(str(path))
    else:
        d.get_screenshot_as_file(str(path))
    return path.name


SITES = [
    ("wikipedia", "https://www.wikipedia.org/"),
    ("news_g1", "https://g1.globo.com/"),
    ("news_bbc", "https://www.bbc.com/news"),
    ("video_youtube", "https://www.youtube.com/"),
    ("maps_osm", "https://www.openstreetmap.org/#map=12/-23.5505/-46.6333"),
    ("webmail_login_proton", "https://account.proton.me/login"),
    ("gov_br", "https://www.gov.br/"),
    ("bank_bb", "https://www.bb.com.br/"),
    ("github", "https://github.com/mozilla-firefox/firefox"),
]

PAGE_STATS_JS = """
return {
  readyState: document.readyState, title: document.title, url: location.href,
  textLength: (document.body && document.body.innerText || "").length,
  images: document.images.length,
  imagesComplete: Array.from(document.images).filter(i => i.complete && i.naturalWidth > 0).length,
  scripts: document.scripts.length,
};
"""

JS_PROBES = r"""
return (async () => {
  const r = {};
  const t = (k, f) => { try { r[k] = f(); } catch (e) { r[k] = 'ERR ' + e; } };
  t('optional_chaining', () => ({a: {b: 1}})?.a?.b === 1);
  t('array_findLast', () => [1, 2, 3].findLast(x => x < 3) === 2);
  t('structuredClone', () => structuredClone({a: 1}).a === 1);
  t('bigint', () => (2n ** 64n).toString() === '18446744073709551616');
  t('intl_ptBR', () => new Intl.NumberFormat('pt-BR').format(1234.5) === '1.234,5');
  t('webgl', () => !!document.createElement('canvas').getContext('webgl'));
  t('webgl2', () => !!document.createElement('canvas').getContext('webgl2'));
  t('serviceWorker_api', () => 'serviceWorker' in navigator);
  r.wasm_add = await WebAssembly.instantiate(new Uint8Array([0,97,115,109,1,0,0,0,1,7,1,96,2,127,127,1,127,
      3,2,1,0,7,7,1,3,97,100,100,0,0,10,9,1,7,0,32,0,32,1,106,11]))
    .then(m => m.instance.exports.add(2, 3) === 5).catch(e => 'ERR ' + e);
  r.worker = await new Promise(res => {
    try {
      const w = new Worker(URL.createObjectURL(new Blob(['onmessage=e=>postMessage(e.data*2)'])));
      w.onmessage = e => res(e.data === 42); w.onerror = e => res('ERR ' + e.message);
      w.postMessage(21); setTimeout(() => res('timeout'), 5000);
    } catch (e) { res('ERR ' + e); }
  });
  r.crypto_sha256 = await crypto.subtle.digest('SHA-256', new TextEncoder().encode('abc'))
    .then(b => Array.from(new Uint8Array(b)).map(x => x.toString(16).padStart(2, '0')).join('')
      === 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad').catch(e => 'ERR ' + e);
  r.indexeddb = await new Promise(res => {
    const q = indexedDB.open('remilia-validation', 1);
    q.onupgradeneeded = () => q.result.createObjectStore('s');
    q.onsuccess = () => { const tx = q.result.transaction('s', 'readwrite'); tx.objectStore('s').put(1, 'k');
      tx.oncomplete = () => res(true); tx.onerror = () => res('ERR tx'); };
    q.onerror = () => res('ERR ' + q.error);
  });
  r.fetch_same_origin = await fetch(location.href, {cache: 'no-store'}).then(x => x.ok).catch(e => 'ERR ' + e);
  return r;
})();
"""

MEDIA_SOURCES = {
    "video_h264_aac_mp4": ["https://mdn.github.io/shared-assets/videos/flower.mp4",
                           "https://www.w3schools.com/html/mov_bbb.mp4"],
    "video_vp8_or_vp9_webm": ["https://mdn.github.io/shared-assets/videos/flower.webm",
                              "https://upload.wikimedia.org/wikipedia/commons/2/22/Volcano_Lava_Sample.webm"],
    "audio_mp3": ["https://mdn.github.io/shared-assets/audio/t-rex-roar.mp3",
                  "https://www.w3schools.com/html/horse.mp3"],
    "audio_vorbis_ogg": ["https://www.w3schools.com/html/horse.ogg",
                         "https://upload.wikimedia.org/wikipedia/commons/c/c8/Example.ogg"],
}

MEDIA_JS = r"""
const [src, kind] = arguments;
return (async () => {
  const el = document.createElement(kind);
  el.muted = true; el.preload = 'auto'; el.src = src; document.body.prepend(el);
  const res = {src};
  try {
    await el.play();
    const t0 = el.currentTime;
    await new Promise(r => setTimeout(r, 4000));
    res.advanced_seconds = +(el.currentTime - t0).toFixed(2);
    res.paused = el.paused;
  } catch (e) { res.play_error = String(e); }
  res.error_code = el.error ? el.error.code : null;
  res.error_message = el.error ? el.error.message : null;
  res.readyState = el.readyState; res.duration = el.duration;
  if (kind === 'video') {
    res.videoWidth = el.videoWidth; res.videoHeight = el.videoHeight;
    const q = el.getVideoPlaybackQuality ? el.getVideoPlaybackQuality() : null;
    if (q) { res.totalVideoFrames = q.totalVideoFrames; res.droppedVideoFrames = q.droppedVideoFrames; }
  }
  el.pause(); el.remove();
  return res;
})();
"""

CANPLAY_JS = """
const v = document.createElement('video'), a = document.createElement('audio'), out = {};
for (const t of ['video/mp4; codecs="avc1.42E01E, mp4a.40.2"', 'video/webm; codecs="vp8, vorbis"',
                 'video/webm; codecs="vp9, opus"', 'video/mp4; codecs="av01.0.05M.08"',
                 'video/mp4; codecs="hev1.1.6.L93.B0"']) out[t] = v.canPlayType(t);
for (const t of ['audio/mpeg', 'audio/ogg; codecs="vorbis"', 'audio/ogg; codecs="opus"',
                 'audio/flac', 'audio/mp4; codecs="mp4a.40.2"']) out[t] = a.canPlayType(t);
out.eme_api = typeof navigator.requestMediaKeySystemAccess === 'function';
return out;
"""

ADDON_JS = """
const [id, action] = arguments;
const {AddonManager} = ChromeUtils.importESModule("resource://gre/modules/AddonManager.sys.mjs");
return (async () => {
  const a = await AddonManager.getAddonByID(id);
  if (!a) return null;
  if (action === 'disable') await a.disable();
  if (action === 'enable') await a.enable();
  if (action === 'uninstall') { await a.uninstall(); return {uninstalled: !(await AddonManager.getAddonByID(id))}; }
  const p = WebExtensionPolicy.getByID(id);
  return {id: a.id, name: a.name, version: a.version, isActive: a.isActive, userDisabled: a.userDisabled,
          signedState: a.signedState, installOrigins: a.installOrigins ?? null,
          temporarilyInstalled: a.temporarilyInstalled, hostname: p ? p.mozExtensionHostname : null};
})();
"""

INSTALL_FILE_JS = """
const [path] = arguments;
const {AddonManager} = ChromeUtils.importESModule("resource://gre/modules/AddonManager.sys.mjs");
return (async () => {
  const file = Cc["@mozilla.org/file/local;1"].createInstance(Ci.nsIFile);
  file.initWithPath(path);
  const install = await AddonManager.getInstallForFile(file);
  const res = {state: install.state, error: install.error};
  try { const addon = await install.install(); res.installed = addon ? addon.id : null; }
  catch (e) { res.install_exception = String(e); }
  res.final_state = install.state; res.final_error = install.error;
  return res;
})();
"""

BLOCK_PROBE_JS = """
const urls = arguments[0];
return (async () => {
  const out = {};
  for (const u of urls) {
    try { await fetch(u, {mode: 'no-cors', cache: 'no-store', credentials: 'omit'}); out[u] = 'loaded'; }
    catch (e) { out[u] = 'blocked (' + e.name + ')'; }
  }
  return out;
})();
"""

AD_PROBES = [
    "https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js",
    "https://securepubads.g.doubleclick.net/tag/js/gpt.js",
    "https://www.google-analytics.com/analytics.js",
    "https://connect.facebook.net/en_US/fbevents.js",
    "https://static.ads-twitter.com/uwt.js",
    "https://cdn.taboola.com/libtrc/loader.js",
    "https://upload.wikimedia.org/wikipedia/commons/6/63/Wikipedia-logo.png",  # control: must load
]

DOWNLOADS_JS = """
const {Downloads} = ChromeUtils.importESModule("resource://gre/modules/Downloads.sys.mjs");
return (async () => {
  const list = await (await Downloads.getList(Downloads.ALL)).getAll();
  return list.map(d => ({source: d.source.url, target: d.target.path, succeeded: d.succeeded,
    stopped: d.stopped, error: d.error ? String(d.error.message || d.error) : null,
    hasBlockedData: d.hasBlockedData, currentBytes: d.currentBytes, totalBytes: d.totalBytes}));
})();
"""

UBO_ID = "uBlock0@raymondhill.net"


@guarded("suite")
def run_suite(exe, geckodriver, exe_name, snapshot_only):
    prof = Path(tempfile.mkdtemp(prefix="remilia-suite-"))
    dl_dir = OUT / "downloads"
    dl_dir.mkdir(exist_ok=True)
    prefs = {} if snapshot_only else {
        # Test configuration (recorded): save downloads without a dialog into the evidence dir.
        "browser.download.dir": str(dl_dir), "browser.download.folderList": 2,
        "browser.download.useDownloadDir": True,
        "browser.download.always_ask_before_handling_new_types": False,
    }
    record("suite", "test_prefs_set", prefs)
    d = make_driver(exe, geckodriver, prof, prefs)
    try:
        d.get("https://www.wikipedia.org/")
        snap = snapshot(d, "suite")
        app = snap.get("application", {})
        record("suite", "app_name_version", f"{app.get('name')} {app.get('version')} build {app.get('buildID')}")
        for k in ("remoteAutoStart", "fissionAutoStart", "fissionDecisionStatus", "numTotalWindows",
                  "numFissionWindows", "numRemoteWindows", "launcherProcessState"):
            record("suite", f"app.{k}", app.get(k))
        record("suite", "sandbox", snap.get("sandbox"))
        record("suite", "sandbox_prefs", chrome(d, SANDBOX_PREFS_JS))
        g = snap.get("graphics", {})
        record("suite", "graphics.summary", {k: g.get(k) for k in (
            "windowLayerManagerType", "windowLayerManagerRemote", "numTotalWindows", "numAcceleratedWindows",
            "adapterDescription", "adapterDriverVersion", "webgl1Renderer", "webgl2Renderer", "direct2DEnabled",
            "directWriteEnabled", "usesTiling", "targetFrameRate")})
        feats = (g.get("featureLog") or {}).get("features") or []
        record("suite", "graphics.features", {f.get("name"): f.get("status") for f in feats})
        record("suite", "policies_active", sorted((snap.get("policies") or {}).get("activePolicies", {}).keys())
               if isinstance(snap.get("policies"), dict) else snap.get("policies"))
        if snapshot_only:
            return

        # ---- real sites
        pages = {}
        for name, url in SITES:
            t0 = time.time()
            try:
                d.get(url)
                time.sleep(4)
                stats = d.execute_script(PAGE_STATS_JS)
                stats["load_seconds"] = round(time.time() - t0, 1)
                stats["screenshot"] = shot(d, f"site_{name}")
            except Exception as e:  # noqa: BLE001
                stats = {"error": f"{type(e).__name__}: {str(e)[:200]}"}
            pages[name] = stats
            record("sites", name, stats)

        # ---- JavaScript / web platform probes (on a real https origin)
        d.get("https://www.wikipedia.org/")
        record("javascript", "probes", d.execute_script(JS_PROBES))

        # ---- audio / video
        record("media", "canPlayType", d.execute_script(CANPLAY_JS))
        for label, candidates in MEDIA_SOURCES.items():
            kind = "video" if label.startswith("video") else "audio"
            attempts = []
            for src in candidates:
                r = d.execute_script(MEDIA_JS, src, kind)
                attempts.append(r)
                if r.get("advanced_seconds", 0) > 1:
                    break
            record("media", label, attempts)

        # ---- multiprocess: several sites in tabs, then ask Gecko and Windows
        for url in ("https://www.wikipedia.org/", "https://github.com/", "https://www.openstreetmap.org/"):
            d.switch_to.new_window("tab")
            d.get(url)
        time.sleep(3)
        procinfo = chrome(d, """return ChromeUtils.requestProcInfo().then(i => i.children.map(
            c => ({type: c.type, origin: c.origin || null, pid: c.pid})));""")
        record("multiprocess", "gecko_children", procinfo)
        record("multiprocess", "windows_processes", browser_processes(exe_name))
        for h in d.window_handles[1:]:
            d.switch_to.window(h)
            d.close()
        d.switch_to.window(d.window_handles[0])

        # ---- uBlock Origin (installed by LibreWolf policy on first run, from AMO)
        ubo, waited = None, 0
        while waited < 180:
            ubo = chrome(d, ADDON_JS, UBO_ID, "info")
            if ubo and ubo.get("isActive"):
                break
            time.sleep(5)
            waited += 5
        record("ublock", "addon", ubo)
        record("ublock", "seconds_waited_for_policy_install", waited)
        if ubo and ubo.get("isActive"):
            time.sleep(20)  # let uBO load its filter lists after install
            d.get("https://www.wikipedia.org/")
            record("ublock", "probe_enabled", d.execute_script(BLOCK_PROBE_JS, AD_PROBES))
            d.get("https://d3ward.github.io/toolz/adblock")
            time.sleep(15)
            record("ublock", "d3ward_enabled_text", d.execute_script(
                "return (document.body.innerText.match(/[^\\n]*\\d+\\s*%[^\\n]*/g)||[]).slice(0,5)"))
            record("ublock", "d3ward_enabled_shot", shot(d, "ublock_d3ward_enabled"))
            d.get(f"moz-extension://{ubo['hostname']}/dashboard.html")
            time.sleep(3)
            record("ublock", "dashboard_shot", shot(d, "ublock_dashboard"))
            record("ublock", "dashboard_title", d.title)
            chrome(d, ADDON_JS, UBO_ID, "disable")
            time.sleep(3)
            d.get("https://www.wikipedia.org/")
            record("ublock", "probe_disabled_etp_only", d.execute_script(BLOCK_PROBE_JS, AD_PROBES))
            d.get("https://d3ward.github.io/toolz/adblock")
            time.sleep(15)
            record("ublock", "d3ward_disabled_text", d.execute_script(
                "return (document.body.innerText.match(/[^\\n]*\\d+\\s*%[^\\n]*/g)||[]).slice(0,5)"))
            record("ublock", "d3ward_disabled_shot", shot(d, "ublock_d3ward_disabled"))
            chrome(d, ADDON_JS, UBO_ID, "enable")
            record("ublock", "re_enabled", chrome(d, ADDON_JS, UBO_ID, "info"))

        # ---- Firefox extensions: signed install / disable / enable / uninstall, unsigned rejected
        ext_dir = OUT / "extensions"
        ext_dir.mkdir(exist_ok=True)
        signed = ext_dir / "multi-account-containers.xpi"
        if not signed.exists():
            import urllib.request
            urllib.request.urlretrieve(
                "https://addons.mozilla.org/firefox/downloads/latest/multi-account-containers/latest.xpi", signed)
        record("extensions", "signed_xpi_sha256", sha256(signed))
        record("extensions", "install_signed", chrome(d, INSTALL_FILE_JS, str(signed)))
        ext_id = "@testpilot-containers"
        record("extensions", "after_install", chrome(d, ADDON_JS, ext_id, "info"))
        chrome(d, ADDON_JS, ext_id, "disable")
        record("extensions", "after_disable", chrome(d, ADDON_JS, ext_id, "info"))
        chrome(d, ADDON_JS, ext_id, "enable")
        record("extensions", "after_enable", chrome(d, ADDON_JS, ext_id, "info"))
        record("extensions", "uninstall", chrome(d, ADDON_JS, ext_id, "uninstall"))
        unsigned = ext_dir / "unsigned-test.xpi"
        with zipfile.ZipFile(unsigned, "w") as z:
            z.writestr("manifest.json", json.dumps({
                "manifest_version": 2, "name": "REMILIA unsigned test", "version": "1.0",
                "browser_specific_settings": {"gecko": {"id": "unsigned-test@remilia.invalid"}}}))
        record("extensions", "install_unsigned_expect_rejected", chrome(d, INSTALL_FILE_JS, str(unsigned)))
        record("extensions", "xpinstall.signatures.required",
               chrome(d, "return Services.prefs.getBoolPref('xpinstall.signatures.required', null)"))

        # ---- downloads
        d.get("https://www.wikipedia.org/")
        targets = {
            "zip_known_hash": ("https://github.com/mozilla/geckodriver/releases/download/v0.37.1/geckodriver-v0.37.1-win64.zip",
                               "dfed9315abe8d2fbc1b6161a2ee8002452e79cf05ee92fdc653a4e26bc35edd8"),
            "exe": ("https://the.earth.li/~sgtatham/putty/latest/w64/putty.exe", None),
        }
        for label, (url, _) in targets.items():
            d.execute_script("const a=document.createElement('a');a.href=arguments[0];document.body.append(a);a.click();", url)
            time.sleep(2)
        deadline = time.time() + 120
        while time.time() < deadline:
            dls = chrome(d, DOWNLOADS_JS)
            if len(dls) >= len(targets) and all(x["stopped"] for x in dls):
                break
            time.sleep(3)
        record("downloads", "list", dls)
        record("downloads", "panel_shot", shot(d, "downloads_panel_chrome", chrome_ctx=True))
        for x in dls:
            tgt = Path(x["target"])
            info = {"exists": tgt.exists()}
            if tgt.exists():
                info["sha256"] = sha256(tgt)
                info["size"] = tgt.stat().st_size
                zone, _, rc = ps(f"Get-Content -LiteralPath '{tgt}' -Stream Zone.Identifier -ErrorAction Stop | Out-String")
                info["zone_identifier"] = zone if rc == 0 else None
            for label, (url, want) in targets.items():
                if x["source"] == url and want:
                    info["sha256_matches_published"] = info.get("sha256") == want
            record("downloads", tgt.name, info)
        d.get("about:downloads")
        time.sleep(2)
        record("downloads", "about_downloads_shot", shot(d, "about_downloads"))
    finally:
        d.quit()
        shutil.rmtree(prof, ignore_errors=True)


# --------------------------------------------------------------------- profiles

PROFILE_SVC_JS = """
const ps = Cc["@mozilla.org/toolkit/profile-service;1"].getService(Ci.nsIToolkitProfileService);
return {profiles: Array.from(ps.profiles).map(p => ({name: p.name, path: p.rootDir.path})),
        userAppData: Services.dirsvc.get("UAppData", Ci.nsIFile).path};
"""

SESSION1_JS = """
const {PlacesUtils} = ChromeUtils.importESModule("resource://gre/modules/PlacesUtils.sys.mjs");
return (async () => {
  Services.prefs.setStringPref("remilia.validation.marker", "persist-me");
  await PlacesUtils.bookmarks.insert({parentGuid: PlacesUtils.bookmarks.unfiledGuid,
    url: "https://example.org/remilia-bookmark", title: "remilia-validation"});
  return true;
})();
"""

SESSION2_JS = """
const {PlacesUtils} = ChromeUtils.importESModule("resource://gre/modules/PlacesUtils.sys.mjs");
return (async () => ({
  pref: Services.prefs.getStringPref("remilia.validation.marker", null),
  bookmark: !!(await PlacesUtils.bookmarks.fetch({url: "https://example.org/remilia-bookmark"})),
  history_visit: await PlacesUtils.history.hasVisits("https://example.org/"),
  cookies_example_org: Services.cookies.getCookiesFromHost("example.org", {}).length,
}))();
"""


@guarded("profiles")
def check_profiles(exe, geckodriver):
    name = "remilia-validation-A"
    r = subprocess.run([str(exe), "-no-remote", "-CreateProfile", name], capture_output=True, text=True, timeout=60)
    record("profiles", "create_profile_rc", r.returncode)
    probe = Path(tempfile.mkdtemp(prefix="remilia-probe-"))
    d = make_driver(exe, geckodriver, probe)
    try:
        info = chrome(d, PROFILE_SVC_JS)
    finally:
        d.quit()
    record("profiles", "registered_profiles", info)
    created = [p for p in info["profiles"] if p["name"] == name]
    if not created:
        record("profiles", "error", "profile not registered after -CreateProfile")
        return
    path = Path(created[0]["path"])

    d = make_driver(exe, geckodriver, path)          # session 1: write data
    try:
        d.get("https://example.org/")
        d.execute_script("document.cookie='remilia=1; max-age=86400; path=/; secure; samesite=lax'")
        record("profiles", "session1_cookie_set", chrome(d,
               "return Services.cookies.getCookiesFromHost('example.org', {}).length"))
        record("profiles", "session1_write", chrome(d, SESSION1_JS))
    finally:
        d.quit()                                     # normal shutdown -> sanitize-on-shutdown runs
    d = make_driver(exe, geckodriver, path)          # session 2: same profile, after restart
    try:
        record("profiles", "session2_read_after_restart", chrome(d, SESSION2_JS))
    finally:
        d.quit()
    d = make_driver(exe, geckodriver, probe)         # isolation + deletion from another profile
    try:
        record("profiles", "other_profile_sees_marker",
               chrome(d, "return Services.prefs.getStringPref('remilia.validation.marker', null)"))
        record("profiles", "delete", chrome(d, """
            const name = arguments[0];
            const ps = Cc["@mozilla.org/toolkit/profile-service;1"].getService(Ci.nsIToolkitProfileService);
            return (async () => {
              for (const p of ps.profiles) if (p.name == name) p.remove(true);
              await ps.asyncFlush();
              return Array.from(ps.profiles).map(p => p.name);
            })();""", name))
    finally:
        d.quit()
        shutil.rmtree(probe, ignore_errors=True)
    record("profiles", "profile_dir_removed", not path.exists())


def main():
    global OUT
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--app-dir", required=True, type=Path)
    ap.add_argument("--exe", required=True)
    ap.add_argument("--geckodriver", required=True, type=Path)
    ap.add_argument("--out", required=True,
                    help="evidence directory inside internal/evidence/ (relative to the repository root)")
    ap.add_argument("--overwrite", action="store_true", help="allow a non-empty --out directory")
    ap.add_argument("--zip", type=Path)
    ap.add_argument("--only", default="package,startup,suite,profiles")
    ap.add_argument("--snapshot-only", action="store_true",
                    help="only collect the Troubleshoot snapshot (used for the official Firefox reference)")
    a = ap.parse_args()
    try:
        OUT = resolve_out(a.out, find_repo_root(), a.overwrite)  # before anything is written
    except OutputError as e:
        ap.error(str(e))
    OUT.mkdir(parents=True, exist_ok=True)
    exe = a.app_dir / a.exe
    steps = a.only.split(",")
    record("meta", "started_utc", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    record("meta", "exe", str(exe))
    if "package" in steps and not a.snapshot_only:
        check_package(a.app_dir, a.zip)
    if "startup" in steps and not a.snapshot_only:
        check_startup(exe, a.exe)
    if "suite" in steps:
        run_suite(exe, a.geckodriver, a.exe, a.snapshot_only)
    if "profiles" in steps and not a.snapshot_only:
        check_profiles(exe, a.geckodriver)
    record("meta", "finished_utc", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    (OUT / "results.json").write_text(json.dumps(RESULTS, indent=1, default=str))


if __name__ == "__main__":
    sys.exit(main())

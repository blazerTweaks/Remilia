<!-- i18n:nav -->
[English](../../ARCHITECTURE.md) | [Português (Brasil)](../pt-BR/ARCHITECTURE.md) | **日本語** | [Español](../es/ARCHITECTURE.md)
<!-- /i18n:nav -->

<!-- i18n:meta -->
> - **Translation status:** Current
> - **Language:** ja
> - **Original language:** English
> - **Source:** [ARCHITECTURE.md](../../ARCHITECTURE.md)
> - **Source revision:** sha256:7871350590894ef0f326a9e435b9da5c25f9ca493007087c61f04062da58faf9
<!-- /i18n:meta -->

# REMILIA Browser — アーキテクチャ

プロジェクトのコードネーム：**SCARLET**
ステータス：フェーズ 2（ブラウザの基盤）— ビルドパイプラインを構築中。REMILIA の変更はまだ適用していない。
最終レビュー：2026-11-25

このドキュメントは、*REMILIA が何をもとに構築され、各レイヤーがどのように
組み合わさり、なぜそうするのか* を記録するものです。

---

## 1. 概要

REMILIA は **Firefox（Gecko）のダウンストリームビルド** であり、
**LibreWolf のパッチセットとプライバシー設定** の上に、REMILIA のパッチ、設定、
ブランディングからなる、別途管理される薄いレイヤーを重ねたものです。

REMILIA は独自のブラウザエンジンを **持たず**、WebView をラップしたものでもなく、
Electron アプリでもありません。すべてのページは Gecko によってレンダリングされ、
すべてのリクエストは Necko（Firefox のネットワークスタック）を通り、すべての
コンテンツプロセスは Firefox の Windows サンドボックス内で動作します。

```
┌───────────────────────────────────────────────────────────────┐
│ Layer 4  REMILIA branding & assets                            │
│          icons, wordmark, about pages, installer art, theme   │
├───────────────────────────────────────────────────────────────┤
│ Layer 3  REMILIA build-fixes, security, privacy               │
│          one directory per category: patches, prefs,          │
│          policies, mozconfig; applied/reverted separately     │
├───────────────────────────────────────────────────────────────┤
│ Layer 2  LibreWolf (pinned commit of librewolf/source)        │
│          68 patches, librewolf.cfg, policies, uBO assets      │
├───────────────────────────────────────────────────────────────┤
│ Layer 1  Upstream Firefox release source tarball              │
│          GPG-verified against Mozilla's release key           │
└───────────────────────────────────────────────────────────────┘
```

各レイヤーは **スクリプトによって、手を加えていないツリーに順番に** 適用されます。
レイヤー 1 と 2 の内容を、このリポジトリ内で手作業で編集することはありません。
これにより、アップストリームのセキュリティリリースを低コストで取り込めます
（[UPSTREAM.md](UPSTREAM.md) を参照）。

---

## 2. ベースの選定

### 2.1 検討した選択肢

| 選択肢 | 判定 | 理由 |
|---|---|---|
| エンジンを自作する | 却下 | 現実的ではなく、プロジェクトのルールで明示的に禁止されている。 |
| Chromium / CEF / Electron | 却下 | プロジェクトの目標は Gecko ブラウザである。Chromium ベースにすると Firefox 拡張機能との互換性、包括的 Cookie 保護、RFP を失い、これらの目標に対して文書化された利点もない。 |
| Firefox を直接フォークする（mozilla-firefox/firefox） | 主要な選択肢としては却下 | LibreWolf がすでに維持しているもの（テレメトリの除去、68 個のパッチ、各種設定）をすべてやり直す必要がある。*アップストリームのアップストリーム* として位置づける。 |
| **`librewolf/source` を git フォークして LibreWolf をフォークする** | 却下 | 4 週間ごとのリリースのたびにマージコンフリクトが発生する。REMILIA の変更が LibreWolf の履歴に混ざり、出自が不明確になる。 |
| **固定した LibreWolf のコミットの上にレイヤーを重ねる** | **採用** | LibreWolf 自身のビルドがすでに「検証済みの Firefox tarball + 順序付きパッチリスト + コピーされるファイル」という形で動いている。REMILIA はこれと同じパターンを一段上で繰り返す。4 レイヤーが明確に分離され、差分は小さく、リベースも容易。 |
| Release ではなく Firefox ESR を使う | 現時点では却下 | LibreWolf は Release に追従している。ESR に従うと LibreWolf によるメンテナンスを手放すことになる。REMILIA のメンテナーの体制で 4 週間サイクルを維持できない場合は再検討する（§8 を参照）。 |

決定記録：ADR-0001。

### 2.2 LibreWolf の実際の構成（2026-11-25 に確認）

出典：`https://codeberg.org/librewolf/source`、`main` のコミット
`ed92167b4c56`（Makefile の `VERSION = 161.0`、`RELEASE = 1`）。リリースタグ
`161.0-1` はコミット `e2baf3254fc7` です。REMILIA は `main` ではなくタグを固定します。

- **ビルドの入力：** `archive.mozilla.org` の `firefox-<ver>.source.tar.xz`。
  `assets/MOZILLA_PUBKEY.asc` に対して `gpg --verify` で検証します。
- 続いて **`scripts/patch.sh`** が、展開したツリー内で次の処理を行います：
  - `assets/mozconfig.new` → `mozconfig` をコピー。
  - ブランディング（`themes/browser/branding/librewolf`）、検索設定、
    `about:librewolf` ページ、そして **LibreWolf の MAR アップデート署名用公開鍵** を
    `toolkit/mozapps/update/updater/release_{primary,secondary}.der` にコピー。
  - `settings/librewolf.cfg`、`settings/distribution/policies.json`、
    `settings/defaults/pref/local-settings.js` を `lw/` にコピー。
  - `assets/patches.txt` のパッチを順番にすべて適用（`patch -p1`）。
  - OpenAI の ML バックエンドを削除し、すべての Glean ping をデータ送信設定に
    従わせ、`appstrings.properties` 内の「Firefox」を書き換え。
  - Firefox の l10n を取得し、LibreWolf の文字列を上書き。
- **設定：** `librewolf.cfg`（約 1000 行、AutoConfig、`lockPref`/`pref`/
  `defaultPref`）を、AutoConfig サンドボックスを有効にした状態で
  `general.config.filename` 経由で読み込み、`policies.json`（エンタープライズポリシー）を使用。
- **uBlock Origin：** ファイルとしては *同梱されていません*。`policies.json` →
  `ExtensionSettings["uBlock0@raymondhill.net"]` に
  `installation_mode: normal_installed` と AMO の `install_url` を指定し、初回起動時に
  addons.mozilla.org から uBO をダウンロードします。Gecko へのパッチ
  （`custom-ubo-assets-bootstrap-location.patch`）が uBO の管理ストレージに
  `adminSettings.assetsBootstrapLocation` を注入し、uBO のデフォルトのリスト選択が
  LibreWolf の `uBOAssets.json` に基づくようにしています。
- **Windows ビルド** は `bsys6` によって、**Docker 上の Debian でのクロスコンパイル**
  で作成されます（clang、Rust の MSVC ターゲット、Mozilla の `get_vs.py` で取得する
  Windows SDK、`widl` 用の Wine、`fxc2`、NSIS）。LibreWolf の README には、
  Windows での *ネイティブ* ビルドは「あまり十分にテストされていない」と記載されています。
- **アップデート：** bsys6 は署名付きの `.mar` ファイルと `update.xml` を生成します。
  LibreWolf のツリーは `MOZ_APPUPDATE_HOST` を `update.librewolf.net` に向けています。

---

## 3. リポジトリ構成（目標）

```
REMILIA/
├── upstream/               # category "upstream": pins.env (Firefox, LibreWolf,
│                           #   l10n, bsys6, base image, Rust); LibreWolf exclusions
├── remilia/                # REMILIA changes, one directory per category
│   ├── build-fixes/        # compile-only fixes, no behaviour change (layer 3)
│   ├── security/           # sandbox, certificates, signing, updates (layer 3)
│   ├── privacy/            # tracking, fingerprinting, cookies, DNS, telemetry,
│   │                       #   uBlock Origin (layer 3)
│   └── branding/           # logos, icons, colours, theme, names, UI (layer 4)
│       # each category holds only what it needs:
│       #   patches/ + series, prefs.cfg, policies.json, mozconfig, files/
├── build/                  # build-environment image (windows-cross.Dockerfile)
├── scripts/                # fetch, prepare, toolchains, build, package, docker
├── i18n/                   # documentation translations
├── tests/                  # validation checklists and recorded results
└── *.md                    # this documentation set
```

`remilia/` と `tests/` はまだ存在しません。実際の内容が初めて入るとき（それぞれ
フェーズ 3a とフェーズ 2 の検証時）に作成し、空の雛形は作りません。カテゴリーの
ルールは §10 にあります。

---

## 4. ビルドパイプライン

```
fetch   → firefox-161.0.source.tar.xz (+ .asc)      gpg --verify (Mozilla key)
        → librewolf/source @ <pinned commit>         git, commit hash checked
prepare → LibreWolf patch.sh on a pristine copy       = layer 2 applied
        → REMILIA patch series + file overlays        = layers 3 + 4 applied
build   → ./mach build   (mozconfig: LW base + REMILIA overrides)
package → ./mach package → zip → NSIS installer, .mar update files
```

### 4.1 Windows のビルドホスト

2 つの方法があり、どちらも正当な方法です。[BUILD.md](BUILD.md) を参照してください：

1. **リリース用／再現可能な方法 — Docker を使った Linux 上でのクロスコンパイル。**
   LibreWolf が公開している Windows バイナリと同じ方法であり、LibreWolf のパッチが
   実際にテストされているのはこの方法です。このマシンでは Docker Desktop
   （WSL2 バックエンド）経由で実行できます。
2. **開発用の方法 — MozillaBuild を使った Windows ネイティブビルド。** Mozilla が
   文書化し、サポートしている方法です。デバッグ（WinDbg、`mach build faster`、
   フロントエンドの差分ビルド）に適しています。LibreWolf のシェルスクリプトには、
   MozillaBuild に同梱されている GNU ツールが必要です。

フェーズ 2 で両方を検証し、どちらをリリースの正式な方法とするかを記録します。
想定：リリースは Docker でのクロスコンパイル、反復開発はネイティブビルド。

---

## 5. プライバシーのアーキテクチャ

プライバシーは **Firefox のネイティブな仕組み** を設定することで実現し、
再実装は決して行いません：

| 対象 | 仕組み（ネイティブ） |
|---|---|
| クロスサイトトラッキング | ETP **厳格**（`browser.contentblocking.category=strict`）：包括的 Cookie 保護（dFPI）、厳格なトラッカーリスト、SmartBlock の shim、クエリパラメーターの除去 |
| フィンガープリンティング | `privacy.resistFingerprinting`（RFP）— Tor Browser や Mullvad Browser と同じ仕組み |
| テレメトリ | **コンパイル時** に無効化（`MOZ_TELEMETRY_REPORTING` を空に設定、クラッシュレポーターはビルドしない、Glean の ping はデータ送信設定に従う）し、さらにポリシーでも無効化 |
| コンテンツブロック | uBlock Origin（無変更、AMO 署名済み） |
| DNS | Firefox の TRR（DoH）— デフォルトでは無効、プロバイダーを選択可能 |
| 通信路 | HTTPS-Only モード有効、CRLite を強制、0-RTT 無効 |

REMILIA が意図的に LibreWolf と **異なる** 点を含む、設定項目ごとの評価の全体は
[PRIVACY.md](PRIVACY.md) にあります。セキュリティに関わる相違点は
[SECURITY.md](SECURITY.md) にあります。

---

## 6. 広告ブロックのアーキテクチャ

- **エンジン：** uBlock Origin。無変更の、AMO 署名済みビルドです。REMILIA は uBO の
  コードをフォークしたり再パッケージしたりしないため、フィルタリングエンジン、
  サイトごとの実際のリクエスト数を表示するポップアップ、ダッシュボードはすべて
  uBO 自身のものです。
- **配布：** 署名済みの `.xpi`（固定バージョン + SHA-256）をアプリケーションの
  `distribution/extensions/` に配置し、**初回起動時にオフラインでも** 存在するように
  します。*さらに* `policies.json` の `ExtensionSettings` にも記載し、Firefox が
  AMO の通常の署名付きアップデートチャネルで更新し続けるようにします。
  署名の検証は引き続き必須です。
- **デフォルトのリスト：** uBO がサポートしている
  `adminSettings.assetsBootstrapLocation` → REMILIA の `assets.json` によって設定します。
  これは *初回インストール時のデフォルト* を定めるだけであり、ユーザーは完全な
  制御権を持ち続けます。`toOverwrite.filterLists` は **使いません**：uBO の
  `restoreAdminSettings()` は起動のたびにこれを再適用するため（`src/js/storage.js` で
  確認済み）、ユーザーの選択を黙って元に戻してしまいます。
- **ブラジル：** uBO の標準カタログには、現在ブラジル専用のリストがありません。
  pt-BR をカバーする地域リストは `spa-1`（AdGuard Spanish/Portuguese）です。
  uBO は `navigator.language` に基づいて地域リストを自動的に有効化しますが、
  RFP はこの値を `en-US` に偽装するため、REMILIA はアセットマニフェストで
  `spa-1` を明示的に有効化する必要があります。その他のブラジルのコミュニティリストは
  フェーズ 5 で評価します。
- **ポップアップ：** フェーズ 5 で、(a) uBO 自身のポップアップをツールバーの
  「保護」パネルとして使うか、(b) uBO が公開するデータだけを読み取る REMILIA の
  パネルを使うかを決定します。ルール：ブロッカーが生成していない統計値は表示しない。
  Firefox 自身の ETP パネルはすでにサイトごとの実際のトラッカー数を表示しており、
  そのまま残します。

決定記録：ADR-0003。

---

## 7. アップデート

REMILIA は **Mozilla 自身のアップデーター**（MAR ファイル + `update.xml`）を使用します。
これは LibreWolf が現在使っているのと同じ仕組みですが、**REMILIA 独自の
アイデンティティ** を用います：

- REMILIA の MAR 署名用鍵ペア。公開鍵で `release_primary.der` /
  `release_secondary.der` 内の LibreWolf の鍵を置き換えます。**LibreWolf のツリーを
  無変更でビルドすると、REMILIA が LibreWolf の署名したアップデートを受け入れ、
  `update.librewolf.net` に問い合わせることになります。これは公開ビルドの前に
  必ず上書きしなければなりません。**
- `MOZ_APPUPDATE_HOST` → REMILIA が管理するホスト（ドメインは未定。ROADMAP の
  ブロッカーを参照）。
- アップデートがプロファイルディレクトリに触れることはありません。ユーザーデータの
  移行は、Firefox 自身のプロファイル移行コードによってのみ行われます。

フィルターリストは uBO を通じて更新され、uBO 自体は AMO を通じて更新されます。

---

## 8. メンテナンスモデル

Firefox は **4 週間** ごとにメジャーリリースを行い、さらに予定外のセキュリティ
ポイントリリース（「chemspill」）があります。LibreWolf は通常、数日以内に追従します。
ユーザーに届くまでの REMILIA の遅延 = LibreWolf の遅延 + REMILIA のリベース +
ビルド + 公開。

現実的な要件：

- **リリースごと：** ピンの更新、パッチシリーズの再適用、リジェクトの修正、
  フルビルド（6 コアの Ryzen 5 3600 で最適化ビルドに約 1.5〜3 時間。フェーズ 2 で
  計測予定）、スモークテスト、署名、公開。
- **目標：** セキュリティリリースを LibreWolf のリリースから **72 時間** 以内に公開する。
  これを確実に達成できない場合は、ユーザーにはっきりと伝えなければなりません。
  古いままのプライバシーブラウザはセキュリティ上のリスクです。
- **パッチの予算：** REMILIA のソースパッチは少なく、小さく保つ。C++/JS の差分よりも、
  pref、ポリシー、ファイルの上書きを優先する。すべてのパッチには、目的、レイヤー、
  アップストリームに提出可能かどうかを記したヘッダーを付ける。

詳細：[UPSTREAM.md](UPSTREAM.md)。

---

## 9. 明示的な対象外事項

- 独自のレンダリング、ネットワーク、暗号、サンドボックスのコードは書かない。
- REMILIA のユーザーを小さく識別しやすい集団にしてしまうような、独自の
  フィンガープリンティング「ランダム化」は行わない。
- フロントエンドフレームワークやバンドラーは使わない（React も Vite も使わない）。
  ブラウザ UI の変更は、Firefox 自身の XHTML/CSS/JS/Fluent によるフロントエンドで行う。
- 匿名性をうたわない。

---

## 10. 変更のカテゴリー

REMILIA のすべての変更は、ちょうど 1 つのカテゴリーに属します。各カテゴリーは
分離されており、それぞれ独立してレビュー、デバッグ、取り消し、アップストリームとの
再同期ができます（ADR-0004）。

| カテゴリー | 対象 | 場所 |
|---|---|---|
| アップストリーム | 無変更の Firefox と LibreWolf、ピン、REMILIA が除外する LibreWolf のパッチ | `upstream/` |
| ビルド修正 | コンパイルのためだけに必要な変更。動作は変えない | `remilia/build-fixes/` |
| セキュリティ | サンドボックス、証明書、HTTPS の検証、署名、プロセス保護、アップデート | `remilia/security/` |
| プライバシー | トラッキング防止、フィンガープリンティング、Cookie、DNS、テレメトリ、コンテンツブロック（uBlock Origin） | `remilia/privacy/` |
| ブランディング | ロゴ、アイコン、色、テーマ、名称、UI のビジュアルアイデンティティ | `remilia/branding/` |

ルール：

- パッチ、pref のブロック、ポリシーファイル、mozconfig の断片は、それぞれ 1 つの
  カテゴリーに属する。2 つのカテゴリーにまたがる変更は 2 つに分割する。
- 分類は効果に基づく。見た目だけを変える UI はブランディング、動作を変える UI は
  その動作のカテゴリーに属する（DoH の設定項目はプライバシー）。
- Firefox が読み込むのは、AutoConfig ファイル、`distribution/policies.json`、
  `mozconfig` のそれぞれ 1 つだけである。`prepare.sh` は各カテゴリーの断片から
  これらを組み立て、カテゴリーごとにヘッダーを付け、2 つのカテゴリーが同じ pref や
  ポリシーを設定している場合は失敗する。
- 適用順は固定：build-fixes → security → privacy → branding。任意の組み合わせを
  適用できるため、各カテゴリーを単独でビルド・検証でき、不具合をカテゴリー単位まで
  二分探索で絞り込める。
- すべてのパッチのヘッダーには、カテゴリー、目的、影響するファイルと pref、
  アップストリームに提出可能かどうか、取り消した場合に何が変わるかを記載する。

`prepare.sh` での組み立てと組み合わせの選択はフェーズ 3a の作業です。現時点の
`prepare.sh` は REMILIA のレイヤーを一切適用しません。

---

## 11. 検証ゲート

コンパイルの成功が証明するのは、ビルド基盤が機能していることだけです。それで
ブラウザが使えるようになるわけではありません。どのビルドも、
[ROADMAP.md](ROADMAP.md) の検証チェックリスト（フェーズ 2、ステップ 3）に合格し、
その結果が `tests/results/` に記録されるまでは、動作するものとは見なしません
（ADR-0005）。
後から追加する各カテゴリーでは、そのカテゴリー単独の場合と、すべてのカテゴリーを
適用した場合の 2 回、チェックリストを実施します。

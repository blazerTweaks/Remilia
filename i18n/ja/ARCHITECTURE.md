<!-- i18n:nav -->
[English](../../ARCHITECTURE.md) | [Português (Brasil)](../pt-BR/ARCHITECTURE.md) | **日本語** | [Español](../es/ARCHITECTURE.md)
<!-- /i18n:nav -->

<!-- i18n:meta -->
> - **Translation status:** Current
> - **Language:** ja
> - **Original language:** English
> - **Source:** [ARCHITECTURE.md](../../ARCHITECTURE.md)
> - **Source revision:** sha256:749aef02a89ed2ddfeeb6202e0487524bf84dc23a38b321e9f117c767f87d7fd
<!-- /i18n:meta -->

# Remilia Browser — アーキテクチャ

プロジェクトのコードネーム：**SCARLET**
ステータス：ビルド基盤は作成済みで一部を実証済み。最初のフルビルドは Remilia の
カテゴリーが統合されるまで延期。最初のフルビルドを、無変更の LibreWolf ではなく
Remilia のビルドにするためである。カテゴリーの仕組みは存在する
（フェーズ 3a、`static-verified`）が、Remilia の変更はまだ適用していない。
最終レビュー：2026-11-26

このドキュメントは、*Remilia が何をもとに構築され、各レイヤーがどのように
組み合わさり、なぜそうするのか* を記録するものです。

---

## 1. 概要

Remilia は **Firefox（Gecko）のダウンストリームビルド** であり、
**LibreWolf のパッチセットとプライバシー設定** の上に、Remilia のパッチ、設定、
ブランディングからなる、別途管理される薄いレイヤーを重ねたものです。

Remilia は独自のブラウザエンジンを **持たず**、WebView をラップしたものでもなく、
Electron アプリでもありません。すべてのページは Gecko によってレンダリングされ、
すべてのリクエストは Necko（Firefox のネットワークスタック）を通り、すべての
コンテンツプロセスは Firefox の Windows サンドボックス内で動作します。

```
┌───────────────────────────────────────────────────────────────┐
│ Layer 4  Remilia branding & assets                            │
│          icons, wordmark, about pages, installer art, theme   │
├───────────────────────────────────────────────────────────────┤
│ Layer 3  Remilia build-fixes, security, privacy               │
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
| **`librewolf/source` を git フォークして LibreWolf をフォークする** | 却下 | 4 週間ごとのリリースのたびにマージコンフリクトが発生する。Remilia の変更が LibreWolf の履歴に混ざり、出自が不明確になる。 |
| **固定した LibreWolf のコミットの上にレイヤーを重ねる** | **採用** | LibreWolf 自身のビルドがすでに「検証済みの Firefox tarball + 順序付きパッチリスト + コピーされるファイル」という形で動いている。Remilia はこれと同じパターンを一段上で繰り返す。4 レイヤーが明確に分離され、差分は小さく、リベースも容易。 |
| Release ではなく Firefox ESR を使う | 現時点では却下 | LibreWolf は Release に追従している。ESR に従うと LibreWolf によるメンテナンスを手放すことになる。Remilia のメンテナーの体制で 4 週間サイクルを維持できない場合は再検討する（§8 を参照）。 |

### 2.2 LibreWolf の実際の構成（2026-11-25 に確認）

出典：`https://codeberg.org/librewolf/source`、`main` のコミット
`ed92167b4c56`（Makefile の `VERSION = 161.0`、`RELEASE = 1`）。リリースタグ
`161.0-1` はコミット `e2baf3254fc7` です。Remilia は `main` ではなくタグを固定します。

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
Remilia/
├── upstream/               # category "upstream": pins.env (Firefox, LibreWolf,
│                           #   l10n, bsys6, base image, Rust); librewolf-exclude.txt;
│                           #   librewolf-base/ (snapshot of LibreWolf's config files)
├── remilia/                # Remilia changes, one directory per category
│   ├── README.md           # the category contract checked by the tools
│   ├── build-fixes/        # compile-only fixes, no behaviour change (layer 3)
│   ├── security/           # sandbox, certificates, signing, updates (layer 3)
│   ├── privacy/            # tracking, fingerprinting, cookies, DNS, telemetry,
│   │                       #   uBlock Origin (layer 3)
│   └── branding/           # logos, icons, colours, theme, names, UI (layer 4)
│       # each category holds only what it needs:
│       #   patches/ + series, prefs.cfg, policies.json, mozconfig, files/,
│       #   replaces.txt, deviations.tsv
├── build/                  # build-environment image (windows-cross.Dockerfile)
├── scripts/                # fetch, prepare, toolchains, build, package, docker,
│   │                       #   remilia_layers.py (categories), verify-tree.sh (V1)
│   └── windows/            # host-side tools (build resource guard)
├── i18n/                   # documentation translations
├── tests/                  # validation harness, category test fixtures
│                           #   (tests/layers/)
├── LICENSE                 # MPL-2.0, for Remilia's own files
└── *.md                    # this documentation set
```

現時点の `remilia/` には契約（`README.md`）しかありません。各カテゴリーの
ディレクトリは、実際の内容が初めて入るとき（フェーズ 3b 以降）に作成し、空の
雛形は作りません。カテゴリーのルールは §10 にあります。

---

## 4. ビルドパイプライン

```
fetch   → firefox-161.0.source.tar.xz (+ .asc)      gpg --verify (Mozilla key)
        → librewolf/source @ <pinned commit>         git, commit hash checked
prepare → LibreWolf patch.sh on a pristine copy       = layer 2 applied
        → Remilia patch series + file overlays        = layers 3 + 4 applied
build   → ./mach build   (mozconfig: LW base + Remilia overrides)
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

フェーズ 5 で両方を検証し、どちらをリリースの正式な方法とするかを記録します。
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

Remilia が意図的に LibreWolf と **異なる** 点を含む、設定項目ごとの評価の全体は
[PRIVACY.md](PRIVACY.md) にあります。セキュリティに関わる相違点は
[SECURITY.md](SECURITY.md) にあります。

---

## 6. 広告ブロックのアーキテクチャ

- **エンジン：** uBlock Origin。無変更の、AMO 署名済みビルドです。Remilia は uBO の
  コードをフォークしたり再パッケージしたりしないため、フィルタリングエンジン、
  サイトごとの実際のリクエスト数を表示するポップアップ、ダッシュボードはすべて
  uBO 自身のものです。
- **配布：** 署名済みの `.xpi`（固定バージョン + SHA-256）をアプリケーションの
  `distribution/extensions/` に配置し、**初回起動時にオフラインでも** 存在するように
  します。*さらに* `policies.json` の `ExtensionSettings` にも記載し、Firefox が
  AMO の通常の署名付きアップデートチャネルで更新し続けるようにします。
  署名の検証は引き続き必須です。
- **デフォルトのリスト：** uBO がサポートしている
  `adminSettings.assetsBootstrapLocation` → Remilia の `assets.json` によって設定します。
  これは *初回インストール時のデフォルト* を定めるだけであり、ユーザーは完全な
  制御権を持ち続けます。`toOverwrite.filterLists` は **使いません**：uBO の
  `restoreAdminSettings()` は起動のたびにこれを再適用するため（`src/js/storage.js` で
  確認済み）、ユーザーの選択を黙って元に戻してしまいます。
- **ブラジル：** uBO の標準カタログには、現在ブラジル専用のリストがありません。
  pt-BR をカバーする地域リストは `spa-1`（AdGuard Spanish/Portuguese）です。
  uBO は `navigator.language` に基づいて地域リストを自動的に有効化しますが、
  RFP はこの値を `en-US` に偽装するため、Remilia はアセットマニフェストで
  `spa-1` を明示的に有効化する必要があります。その他のブラジルのコミュニティリストは
  フェーズ 5 で評価します。
- **ポップアップ：** フェーズ 5 で、(a) uBO 自身のポップアップをツールバーの
  「保護」パネルとして使うか、(b) uBO が公開するデータだけを読み取る Remilia の
  パネルを使うかを決定します。ルール：ブロッカーが生成していない統計値は表示しない。
  Firefox 自身の ETP パネルはすでにサイトごとの実際のトラッカー数を表示しており、
  そのまま残します。

---

## 7. アップデート

Remilia は **Mozilla 自身のアップデーター**（MAR ファイル + `update.xml`）を使用します。
これは LibreWolf が現在使っているのと同じ仕組みですが、**Remilia 独自の
アイデンティティ** を用います：

- Remilia の MAR 署名用鍵ペア。公開鍵で `release_primary.der` /
  `release_secondary.der` 内の LibreWolf の鍵を置き換えます。**LibreWolf のツリーを
  無変更でビルドすると、Remilia が LibreWolf の署名したアップデートを受け入れ、
  `update.librewolf.net` に問い合わせることになります。これは公開ビルドの前に
  必ず上書きしなければなりません。**
- `MOZ_APPUPDATE_HOST` → Remilia が管理するホスト（ドメインは未定。ROADMAP の
  ブロッカーを参照）。
- アップデートがプロファイルディレクトリに触れることはありません。ユーザーデータの
  移行は、Firefox 自身のプロファイル移行コードによってのみ行われます。

フィルターリストは uBO を通じて更新され、uBO 自体は AMO を通じて更新されます。

---

## 8. メンテナンスモデル

Firefox は **4 週間** ごとにメジャーリリースを行い、さらに予定外のセキュリティ
ポイントリリース（「chemspill」）があります。LibreWolf は通常、数日以内に追従します。
ユーザーに届くまでの Remilia の遅延 = LibreWolf の遅延 + Remilia のリベース +
ビルド + 公開。

現実的な要件：

- **リリースごと：** ピンの更新、パッチシリーズの再適用、リジェクトの修正、
  フルビルド（6 コアの Ryzen 5 3600 で最適化ビルドに約 1.5〜3 時間。フェーズ 5 で
  計測予定）、スモークテスト、署名、公開。
- **目標：** セキュリティリリースを LibreWolf のリリースから **72 時間** 以内に公開する。
  これを確実に達成できない場合は、ユーザーにはっきりと伝えなければなりません。
  古いままのプライバシーブラウザはセキュリティ上のリスクです。
- **パッチの予算：** Remilia のソースパッチは少なく、小さく保つ。C++/JS の差分よりも、
  pref、ポリシー、ファイルの上書きを優先する。すべてのパッチには、目的、レイヤー、
  アップストリームに提出可能かどうかを記したヘッダーを付ける。

詳細：[UPSTREAM.md](UPSTREAM.md)。

---

## 9. 明示的な対象外事項

- 独自のレンダリング、ネットワーク、暗号、サンドボックスのコードは書かない。
- Remilia のユーザーを小さく識別しやすい集団にしてしまうような、独自の
  フィンガープリンティング「ランダム化」は行わない。
- フロントエンドフレームワークやバンドラーは使わない（React も Vite も使わない）。
  ブラウザ UI の変更は、Firefox 自身の XHTML/CSS/JS/Fluent によるフロントエンドで行う。
- 匿名性をうたわない。

---

## 10. 変更のカテゴリー

Remilia のすべての変更は、ちょうど 1 つのカテゴリーに属します。各カテゴリーは
分離されており、それぞれ独立してレビュー、デバッグ、取り消し、アップストリームとの
再同期ができます。

| カテゴリー | 対象 | 場所 |
|---|---|---|
| アップストリーム | 無変更の Firefox と LibreWolf、ピン、Remilia が除外する LibreWolf のパッチ | `upstream/` |
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
- LibreWolf の値を上書きする値には、書面の理由を指す登録済みの逸脱
  （`deviations.tsv`）が必要で、LibreWolf が使った関数（`pref`、`defaultPref`、
  `lockPref`）を維持しなければならない。LibreWolf がロックしている pref の
  再定義は、実行中のブラウザで効果を確認するまで `runtime-unverified` と
  記録する。
- 適用順は固定：build-fixes → security → privacy → branding。任意の組み合わせを
  適用できるため、各カテゴリーを単独でビルド・検証でき、不具合をカテゴリー単位まで
  二分探索で絞り込める。
- すべてのパッチのヘッダーには、カテゴリー、目的、影響するファイルと pref、
  アップストリームに提出可能かどうか、取り消した場合に何が変わるかを記載する。

実装（フェーズ 3a）：`REMILIA_LAYERS` に対応した `prepare.sh` と、チェックと
組み立てを行う `scripts/remilia_layers.py`。契約は `remilia/README.md` です。
逸脱は `upstream/librewolf-base/` にある LibreWolf の設定ファイルのスナップショット
と照合するため、静的チェックは Docker なしで実行できます。

---

## 11. 検証ゲート

コンパイルの成功が証明するのは、ビルド基盤が機能していることだけです。それで
ブラウザが使えるようになるわけではありません。どのビルドも、
[ROADMAP.md](ROADMAP.md#検証チェックリスト) の検証チェックリストに合格し、
その結果が `tests/validation/README.md` に記載された形式で記録されるまでは、
動作するものとは見なしません。検証記録はメンテナーがローカルに保管し、この
リポジトリでは公開しません。

最初のフルビルドは、ブランディング、セキュリティ、プライバシーが統合されるまで
延期します。それまでは、変更をコンパイルせずに確認します：変更のたびに
静的チェック（V0）を行い、各フェーズを完了する前にカテゴリーごとのツリーを新しく
準備して確認します（V1）。V1 はビルド用ボリューム内の `staging/` に別の
ステージングツリーを準備します。V1 の実行中、保持しているツリーとその
オブジェクトディレクトリを含むボリュームの残りの部分は読み取り専用でマウント
されます。V0 と V1 にだけ合格した作業は `static-verified` であり、
`done` にはしません。フルビルド（V2）とチェックリスト（V3）は ROADMAP の
フェーズ 5 で行います。各カテゴリーにも単独のフルビルドを行うかどうかはフェーズ 5
で決めます。`REMILIA_LAYERS`（§10）によってそれが可能になります。

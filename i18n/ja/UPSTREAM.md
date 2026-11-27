<!-- i18n:nav -->
[English](../../UPSTREAM.md) | [Português (Brasil)](../pt-BR/UPSTREAM.md) | **日本語** | [Español](../es/UPSTREAM.md)
<!-- /i18n:nav -->

<!-- i18n:meta -->
> - **Translation status:** Current
> - **Language:** ja
> - **Original language:** English
> - **Source:** [UPSTREAM.md](../../UPSTREAM.md)
> - **Source revision:** sha256:928a4476b63ce5794056918ae2ad2afdbffbb1132346c2eb913cabf00f5beb2d
<!-- /i18n:meta -->

# アップストリームとの同期

REMILIA は 2 つのプロジェクトのダウンストリームです。これらに追従し続けることは、
最も重要な継続的メンテナンス作業です。セキュリティ修正のほぼすべてが
アップストリームからもたらされるためです。

## レイヤー

| レイヤー | 取得元 | 固定場所 | REMILIA が編集するか |
|---|---|---|---|
| 1. Firefox | `archive.mozilla.org/pub/firefox/releases/<ver>/source/`（GPG 署名付き tarball）。正規リポジトリ：`github.com/mozilla-firefox/firefox` | `upstream/pins.env` → `FIREFOX_VERSION` | 直接は編集しない。レイヤー 3 のパッチを通じてのみ |
| 2. LibreWolf | `codeberg.org/librewolf/source`（パッチ、設定、ビルドスクリプト） | `upstream/pins.env` → `LIBREWOLF_COMMIT` | 編集しない。REMILIA がその上から上書きする |
| 3. REMILIA のビルド修正、セキュリティ、プライバシー | `remilia/build-fixes/`、`remilia/security/`、`remilia/privacy/`（それぞれ 1 カテゴリー。ARCHITECTURE.md §10） | — | する |
| 4. REMILIA のブランディング | `remilia/branding/` | — | する |

## 追跡すべきリリースサイクル

- Firefox：4 週間ごとのメジャーリリース。セキュリティ問題に対するドット
  リリースがあり、予定外のこともある（「chemspill」）。アドバイザリ：
  mozilla.org/security/advisories/。
- LibreWolf：`<firefox-version>-<lw-release>` 形式のタグ（例：`161.0-1`）。
  通常は Firefox から数日以内。
- uBlock Origin：独立している。AMO を通じて更新され、REMILIA のリリースとは
  連動しない。

## アップデート手順

1. 新しい Firefox バージョンに対応する、新しい LibreWolf のタグが公開される。
2. `upstream/pins.env` を更新する：`FIREFOX_VERSION`、`LIBREWOLF_COMMIT`、`LIBREWOLF_TAG`。
3. `./scripts/fetch.sh` を実行する。Mozilla の GPG 署名とコミットハッシュが検証される。
4. `./scripts/prepare.sh`。`upstream/librewolf-base/` が新しい LibreWolf の
   ファイルと異なる間は、REMILIA のカテゴリーの適用を拒否します。REMILIA の
   パッチが当たらない場合：
   - 新しいツリーに合わせて更新する。
   - パッチが変更するコードの意味が変わった場合は、パッチの目的ヘッダーを見直し、
     作り直す。無理に当てない。
5. `scripts/remilia_layers.py snapshot` で LibreWolf ベースのスナップショットを
   更新し、その差分（`librewolf.cfg`、`policies.json`、`mozconfig`、
   `patches.txt`）を確認する。変更された pref はすべて PRIVACY.md と SECURITY.md
   に照らして確認する。REMILIA の上書きがアップストリームと衝突したり重複したり
   している可能性があるためです。その後
   `python scripts/remilia_layers.py check` を実行する。
6. ツリーチェック（`./scripts/docker.sh verify`）の後、ビルドし、検証
   チェックリストを実施し、パッケージ化、署名、公開を行う。
7. リリースノートには、含まれている MFSA アドバイザリを列挙する。

## REMILIA パッチのルール

- 1 つのパッチには 1 つの関心事と 1 つのカテゴリー（ARCHITECTURE.md §10）。
  ヘッダーには、カテゴリー、目的、影響する pref・ファイル、LibreWolf や Mozilla に
  提出できるかどうか、取り消した場合に何が変わるかを記載する。正確な形式は
  `remilia/README.md` にある。
- 優先順位：カテゴリーの `prefs.cfg` の pref → その `policies.json` の
  ポリシー → ファイルのオーバーレイ（コピー）→ ソースパッチ。ソースパッチは
  最後の手段とする。
- LibreWolf のパッチは変更しない。不要なものがあれば
  `upstream/librewolf-exclude.txt` で除外する。1 行に 1 パッチで、LibreWolf の
  `patches.txt` に書かれたとおりのパス、続けて理由を書く。理由は必須で、
  `REMILIA-PROVENANCE.txt` にコピーされるため公開される：10〜200 文字で、カンマ、
  制御文字、内部文書への参照を含まないこと。`scripts/remilia_layers.py` は、パス、
  そのパスが `patches.txt` にちょうど 1 回現れること、理由を確認する。理由の代わりに
  決定の識別子を書いた旧形式の行は拒否される。LibreWolf 161.0-1 では
  リストは空です。
- REMILIA 固有でない修正は、まずアップストリームに提案する。

## LibreWolf ツリーのリブランディング：変更箇所

フェーズ 3a で作成した、準備済み LibreWolf 161.0-1 ツリーの棚卸しです。
"librewolf" を含む行が 4018 行見つかりました。1 行ずつの完全なリストは公開して
いません。そのうち
3605 行は、`lw/l10n/`（504 ファイル）にある LibreWolf 独自の UI 文字列の
オーバーレイです。

棚卸しの対象：準備済みツリー（オブジェクトディレクトリを除く）のテキスト
ファイルのうち、大文字小文字を問わず "librewolf" を含むすべての行。対象外：

- バイナリファイルの行単位の一覧（アイコンとビットマップはディレクトリ単位で記載）
- その語を含まないアイデンティティ（残っている "Firefox" の文字列や Mozilla の URL など）
- `librewolf.cfg` 以外で設定される pref の既定値（`browser/app/profile/firefox.js`、
  `modules/libpref/init/all.js`、`modules/libpref/init/StaticPrefList.yaml`、
  `browser/branding/librewolf/pref/firefox-branding.js` など）。カテゴリーの
  チェックもこれらの値の上書きを検出しない（`remilia/README.md` の
  "What the checks cover"）。これはフェーズ 3b、4a、4b の持ち越し作業である。

フェーズ 3b では、ユーザーに見えるアイデンティティ（名前、アイコン、UI、実行
ファイル、プロファイル）を REMILIA に変更します。内部名はそのまま残します：
`lw/` ディレクトリ、`librewolf.cfg` というファイル名、`librewolf.*` の pref
名前空間です。これらを変更すると、セキュリティとプライバシーがブランディングに
依存してしまいます。

| 変更箇所 | 場所 | カテゴリー | フェーズ |
|---|---|---|---|
| アプリケーション名、ブランディングディレクトリ、リモーティング名 | `mozconfig` 21、23、30 行目；`browser/branding/librewolf/configure.sh` 8–11 行目；`toolkit/moz.configure` 23、37 行目のベンダー名とアプリ名の既定値 | ブランディング（`mozconfig` の逸脱） | 3b |
| ディストリビューション ID `net.librewolf` | `mozconfig` 22 行目 | ブランディング | 3b、B1 が必要 |
| ブランディングディレクトリ：アイコン（`.ico`、`.png`、`.icns`、`.bmp`）、ワードマーク、`brand.ftl`、`brand.dtd`、`brand.properties`、`branding.nsi` | `browser/branding/librewolf/`（42 項目。`patch.sh` が LibreWolf の `themes/` からコピー） | ブランディング：REMILIA の新しいブランディングディレクトリを作り、LibreWolf のものは編集しない | 3b |
| 実行ファイルのマニフェスト | `browser/app/librewolf.exe.manifest` 6、9 行目 | ブランディング | 3b |
| プロファイルとデータのディレクトリ名 | `toolkit/xre/nsXREDirProvider.cpp` 337、430、432、1010、1307、1317 行目（`profile-directory.patch`、`mozilla-dirs.patch`）；バックアップフォルダー `browser/components/backup/BackupService.sys.mjs` 661 行目 | ブランディング | 3b |
| プロファイルから読み込むユーザー上書きファイル `librewolf.overrides.cfg` | `extensions/pref/autoconfig/src/prefcalls.js` 25–54 行目 | 未決：内部の AutoConfig の仕組みの中にある、ユーザーに見えるファイル名 | 3b で決定 |
| 「について」ダイアログと `about:librewolf` ページ | `browser/base/content/aboutDialog.xhtml` 38、44、45 行目；`toolkit/content/librewolf.html`；`toolkit/locales/en-US/toolkit/about/aboutLibreWolf.ftl`；`docshell/build/components.conf` 18 行目 | ブランディング（表示テキスト）。`about:` のアドレスは 3b の未決事項 | 3b |
| 設定画面 | `browser/components/preferences/librewolf.js`、`librewolf.inc.xhtml`；`browser/locales/en-US/browser/preferences/preferences.ftl`（46 行） | 名前とアイコンはブランディング。各項目の動作はそれぞれのカテゴリーに属する | 3b |
| 埋め込みの文字列 | `appstrings.properties`（`patch.sh` が書き換え、12 行）；`dom/locales/en-US/chrome/appstrings.properties`；`lw/l10n/` のオーバーレイ（表示名を含む 1545 行） | ブランディング | 3b |
| 開発ツールのロゴ | `devtools/client/aboutdebugging/src/actions/runtimes.js` 74 行目（`lw-logo-devtools.patch`） | ブランディング | 3b |
| サポートとリリースノートのリンク | `lw/librewolf.cfg` 582–586 行目と 648 行目（`app.update.url.*`、`app.releaseNotesURL*`、`app.support.baseURL`）；`lw/policies.json` 93–94 行目（`SupportMenu`）と 60 行目（言語パックのメッセージ） | ブランディング（pref とポリシーの逸脱） | 3b、B1 が必要 |
| 更新ホストと MAR 鍵 | `build/moz.build` 95 行目（`MOZ_APPUPDATE_HOST`）；`patch.sh` がコピーする `release_primary.der`、`release_secondary.der` | ブランディングではなくセキュリティ（ブラウザが受け入れる更新を決めるため） | 4a、B1・B2 が必要 |
| uBlock Origin のアセットリストの場所 | `lw/librewolf.cfg` 996–999 行目（`librewolf.uBO.assetsBootstrapLocation`） | プライバシー | 4b |
| LibreWolf のサーバーでのバージョン確認（既定で無効） | `browser/base/content/aboutDialog.js` 42–72 行目 | プライバシー（ネットワーク通信）。無効のまま | 4b |
| 検索エンジン | `services/settings/dumps/main/search-config-v2.json`（`patch.sh` がコピー） | プライバシー（D1） | 4b |
| Windows インストーラーの名前 | `browser/branding/librewolf/branding.nsi` 11–13 行目 | ブランディング | 8 |
| 残す内部名 | `librewolf.*` の pref（`modules/libpref/init/StaticPrefList.yaml` 12433–12446 行目と、コード中の約 40 箇所）；`lw/` と `librewolf.cfg`（`browser/installer/package-manifest.in` 279 行目、`lw/local-settings.js`） | なし：意図的に残す | — |

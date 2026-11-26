<!-- i18n:nav -->
[English](../../UPSTREAM.md) | [Português (Brasil)](../pt-BR/UPSTREAM.md) | **日本語** | [Español](../es/UPSTREAM.md)
<!-- /i18n:nav -->

<!-- i18n:meta -->
> - **Translation status:** Current
> - **Language:** ja
> - **Original language:** English
> - **Source:** [UPSTREAM.md](../../UPSTREAM.md)
> - **Source revision:** sha256:71c41dc82b06b164ca0c1f15cf5c5277437d0719e2cc5866c7e3c4ecfebdbf49
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

## アップデート手順 *(スクリプトはフェーズ 2 で用意)*

1. 新しい Firefox バージョンに対応する、新しい LibreWolf のタグが公開される。
2. `upstream/pins.env` を更新する：`FIREFOX_VERSION`、`LIBREWOLF_COMMIT`、`LIBREWOLF_TAG`。
3. `./scripts/fetch.sh` を実行する。Mozilla の GPG 署名とコミットハッシュが検証される。
4. `./scripts/prepare.sh` を実行する。REMILIA のパッチが適用できない場合は：
   - 新しいツリーに対してパッチを更新する。
   - パッチが触れているコードの意味が変わっている場合は、パッチの目的を記した
     ヘッダーを見直し、改めて作り直す。無理に適用しない。
5. 旧・新の LibreWolf のコミット間で `librewolf.cfg` と `policies.json` の差分を取る。
   変更されたすべての pref を PRIVACY.md と SECURITY.md に照らして確認する。
   REMILIA の上書きが、アップストリームと衝突したり重複したりしている可能性が
   あるためである。
6. ビルドし、スモークテストのチェックリスト（`tests/`）を実行し、パッケージ化、署名、
   公開する。
7. リリースノートには、含まれる MFSA アドバイザリを記載する。

## REMILIA のパッチに関するルール

- 1 つのパッチには 1 つの関心事と 1 つのカテゴリーのみ（ARCHITECTURE.md §10）。
  ヘッダーに、カテゴリー、目的、影響する pref／ファイル、LibreWolf や Mozilla へ
  提出可能かどうか、取り消した場合に何が変わるかを記載する。
- 優先順位：カテゴリーの `prefs.cfg` の pref → そのカテゴリーの `policies.json` の
  ポリシー → ファイルの上書き（コピー）→ ソースパッチ。ソースパッチは最後の手段とする。
- LibreWolf のパッチは変更しない。不要なパッチがある場合は、ADR を添えて
  `upstream/` の除外リスト（フェーズ 3a）で除外する。
- REMILIA 固有ではない修正は、まずアップストリームに提案する。

## LibreWolf のツリーのリブランディング：既知の変更箇所

LibreWolf は自身のアイデンティティをいくつかの箇所にハードコードしており、REMILIA は
それらを上書きする必要があります。一覧はフェーズ 3 で完成させます：

- `mozconfig`：`--with-app-name`、`--with-distribution-id`、`--with-branding`、
  `MOZ_APP_REMOTINGNAME`。
- `lw/` ディレクトリと `librewolf.cfg` のファイル名（`lw-dir.patch`、`local-settings.js`）。
- プロファイルディレクトリの名前（`profile-directory.patch`、`mozilla-dirs.patch`）。
- `about:librewolf` ページと設定パネル（`about-librewolf.patch`、`pref-pane/`）。
- `librewolf.*` の pref 名前空間（例：`librewolf.uBO.assetsBootstrapLocation`）。
- アップデーター：`MOZ_APPUPDATE_HOST`、`release_primary.der`、`release_secondary.der`。
- 文字列：`appstrings.properties` の書き換えと l10n の上書き。
- `policies.json` の `SupportMenu`、`app.update.url.*`、`app.releaseNotesURL*`。

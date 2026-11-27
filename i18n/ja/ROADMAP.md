<!-- i18n:nav -->
[English](../../ROADMAP.md) | [Português (Brasil)](../pt-BR/ROADMAP.md) | **日本語** | [Español](../es/ROADMAP.md)
<!-- /i18n:nav -->

<!-- i18n:meta -->
> - **Translation status:** Current
> - **Language:** ja
> - **Original language:** English
> - **Source:** [ROADMAP.md](../../ROADMAP.md)
> - **Source revision:** sha256:7c173f95a3c52e9e5b8ad4d6ce1df15a5d1630ef3d47b0b79adf5ac36d4fdf33
<!-- /i18n:meta -->

# ロードマップと進捗状況

このファイルは、完了したタスク、未完了のタスク、ブロッカー、決定事項を記録する、
プロジェクトの公式な記録です。ステータスの値：`done`（完了）、`in progress`（進行中）、
`todo`（未着手）、`blocked`（ブロック中）、`deferred`（作業を保持したまま意図的に延期）、
`static-verified`（実装済みで静的チェックとツリーチェックに合格したが、まだコンパイルも
実行中のブラウザでのテストもしていない。`done` と同等ではない）。

最終更新：2026-11-26

## 現在のフェーズ：3a は静的検証により完了（2026-11-26）。フェーズ 3b — ブランディングはメンテナーの明示的な承認待ち。

## 作業ルール

1. **変更カテゴリーの分離。** アップストリーム、ビルド修正、セキュリティ、
   プライバシー、ブランディングはそれぞれ別のファイルとパッチで管理し、1 つの
   パッチやコミットに混在させない。それぞれ追跡可能で、個別に取り消せるようにする
   （ARCHITECTURE.md §10）。
2. **ビルドの成功は、動作するブラウザを意味しない。** コンパイルの成功が証明するのは
   ビルド基盤だけである。検証チェックリストに合格し、その結果を記録するまでは、
   何も「動作する」とは呼ばない（ARCHITECTURE.md §11）。
3. **最初のフルビルドは延期であり、放棄ではない。** Remilia を先に開発し、
   ブランディング、セキュリティ、プライバシーがプロジェクトを代表できる程度に
   統合された時点でコンパイルする。それまでは、各フェーズは静的チェックと
   ツリーチェックで完了とし、その作業は `done` ではなく `static-verified` とする。
4. **フェーズの自動移行はしない。** 次のフェーズに進むかどうかは、記録された証拠を
   確認したうえでメンテナーが決める。

## 進め方

1. ビルド基盤：取得、検証、LibreWolf のパッチ、ツールチェーン、Docker、ビルドと
   パッケージングのスクリプト（フェーズ 2。ビルドそのものは延期）。
2. Remilia 独自の変更のための構造と設定（フェーズ 3a）。
3. ブランディング（フェーズ 3b）。
4. セキュリティ（フェーズ 4a）。
5. プライバシー（uBlock Origin の統合を含む）（フェーズ 4b）。
6. 統合した状態での最初のフルビルド、パッケージング、Windows での機能検証
   （フェーズ 5）。
7. ユーザー体験、セキュリティテスト、配布（フェーズ 6〜8）。

## 検証の方針

すべての変更にコンパイルが必要なわけではない。以下の各レベルは必要なときに実施し、
下位のレベルは常に上位のレベルより先に実施する。

| レベル | 時期 | 内容 | 必要なもの |
|---|---|---|---|
| V0 静的 | 変更のたび | フラグメントの構文、パッチのヘッダーと `series` ファイル、カテゴリーの境界、カテゴリー間での pref やポリシーの重複、`python i18n/i18n.py check`、単体テスト（`python -m unittest discover -s tests/layers`、`python -m unittest discover -s tests/validation`） | ホスト上の Python。Docker もコンパイルも不要 |
| V1 ツリー | 各フェーズを完了する前 | 別のステージングツリーへの新規準備：すべてのパッチが fuzz 0 で適用でき、きれいに元に戻せる。各カテゴリー単独とすべてのカテゴリーの組み合わせ。複数のカテゴリーが触れるファイルの一覧。カテゴリーなしのツリーが LibreWolf のベースと同一 | Docker。コンパイルは不要。既存のオブジェクトディレクトリには一切触れない |
| V2 フルビルド | フェーズ 5、ブランディング、セキュリティ、プライバシーが統合されたとき | `build.sh`、`package.sh`、sha256、出自情報ファイル | Docker、数時間のコンパイル |
| V3 機能 | 最初の V2 パッケージの後 | Windows での[検証チェックリスト](#検証チェックリスト)、結果は `internal/evidence/<date>-<build>/` に保存（ローカル、非公開） | メンテナーの Windows マシン |

ルール：

- コンパイルしないと検証できない変更は、ビルドを始める前に理由を説明し、承認を得る。
- V0 と V1 が証明するのは、変更が適用でき、一貫性があり、分離できることである。
  実行時に何かが動作することは証明しない。それは V2 と V3 の役割である。
- V2／V3 でしか確認できないもの：`mozconfig` のオプション、ソースパッチが
  コンパイルできること、実行ファイル内のアイコンとリソース、pref とポリシーの
  実行時の効果、サンドボックス、uBlock Origin の同梱。

## ブロッカーと未決定事項

| ID | 項目 | 必要な時期 | 担当 |
|---|---|---|---|
| B1 | アップデートサーバー、ディストリビューション ID（`--with-distribution-id`）、サポートリンクのための **プロジェクトのドメイン** | フェーズ 3b（ブランディング）、フェーズ 8（アップデート） | メンテナー |
| B2 | **MAR アップデート署名用の鍵ペア** を生成し、オフラインで保管する | フェーズ 4a。公開ビルドより前 | メンテナー |
| B3 | **Safe Browsing の API キー**：取得するか、文書化された代替策（SECURITY.md §S3）を受け入れる | フェーズ 4a | メンテナー |
| B4 | **Windows のコード署名（Authenticode）証明書。** これがないとインストーラーに SmartScreen の警告が表示される | フェーズ 8 | メンテナー |
| B5 | ~~Remilia 独自ファイルのライセンス~~ 2026-11-26 解決：MPL-2.0（`LICENSE`）。継承したファイルはそれぞれのライセンスを維持 | フェーズ 3a | メンテナー |
| B6 | ビルド方法 B のために **MozillaBuild** をインストールする（対話型インストーラーと UAC が必要） | フェーズ 5（任意） | メンテナー |
| D1 | デフォルトの検索エンジン | フェーズ 4b | 未定 |
| D2 | 終了時の履歴消去のデフォルト（プライバシー対ログイン状態の維持） | フェーズ 4b | 未定 |
| D3 | DoH のデフォルト（無効か、初回起動時の選択か） | フェーズ 4b | 未定 |
| D4 | ツールバーの保護パネル：uBO のポップアップか、uBO のデータを使う Remilia のパネルか | フェーズ 6 | 未定 |

## フェーズ 1 — 調査 `done`

- [x] Firefox のソースの調査：正規リポジトリは現在 `github.com/mozilla-firefox/firefox`（Git）。リリースの tarball は GPG で署名されている。
- [x] LibreWolf の調査：`codeberg.org/librewolf/source`（パッチ、設定、ビルド）と `bsys6`（パッケージング、Windows 向けクロスコンパイル）。
- [x] Windows での Firefox のビルド要件（MozillaBuild、`mach bootstrap`、40 GB 以上、パスにスペースを含めない）。
- [x] LibreWolf が Windows バイナリをビルドする方法（Debian 上の Docker でのクロスコンパイル）。
- [x] 拡張機能の統合：LibreWolf が uBO をインストールする方法。uBO の管理ストレージの挙動を uBO のソースで確認。
- [x] `librewolf.cfg` v8.6 のプライバシー設定のレビュー（プライバシー、ネットワーク、フィンガープリンティング、セキュリティ、拡張機能、アップデーターの各セクション）。
- [x] ライセンス：MPL-2.0（Firefox、LibreWolf）、GPL-3.0（uBO）、Firefox の商標、東方の二次創作に関する考慮事項。
- [x] メンテナンスモデル（4 週間サイクル、chemspill）。
- [x] ドキュメント一式：README、ARCHITECTURE、PRIVACY、SECURITY、BUILD、UPSTREAM、ROADMAP、CONTRIBUTING。
- [x] アップストリームのピンを記録（`upstream/pins.env`）。
- [x] ドキュメントの翻訳（pt-BR、ja、es）と同期チェッカー（`i18n/i18n.py`）。
- [ ] 未完了：`librewolf.cfg` の UI／テレメトリ／地域の各セクションの精読と、LibreWolf の全 68 パッチの 1 行ずつのレビュー。フェーズ 4a／4b に持ち越し。

## フェーズ 2 — ビルド基盤 `deferred`

目標：LibreWolf 161.0-1 のベースから Windows x64 の実行ファイルを生成できるビルド
基盤。無変更の LibreWolf を単独でビルドすることは、もはや目標ではない。
基盤は維持し、残りのステップはフェーズ 5 に移す。

- [x] ビルド環境のイメージ `build/windows-cross.Dockerfile`（bsys6 をもとに作成、ベースイメージはダイジェストで固定）。
- [x] `scripts/fetch.sh`：Firefox の tarball を固定した Mozilla の鍵で GPG 検証。LibreWolf、l10n、bsys6 は固定したコミット。改ざんした tarball が拒否されることを確認（テスト済み）。
- [x] `scripts/prepare.sh`：クリーンなコピー → LibreWolf の `patch.sh`（68 パッチ、fuzz／リジェクト 0）→ Windows 向けクロスコンパイル用の mozconfig。
- [x] l10n を Mozilla の `firefox-l10n` のコミットに固定（LibreWolf のミラーは HTTP 502 を返した。同じコミットなので内容も同じ）。
- [x] `scripts/toolchains.sh`：clang、sysroot、Wine、NSIS、Windows SDK を `remilia-mozbuild` ボリュームに取得（完了マーカーあり、2026-11-26）。
- [x] ビルドを実行して見つかったビルド上の修正：作業ディレクトリを `/builds/work` に移動（clang-cl が `/work/...` を自身の `/wo` オプションとして解釈したため）。メモリ不足になった WSL2 の VM に `memory=18GB`、`swap=24GB` を設定。並列ジョブは 6。
- [x] 検証ハーネス `tests/validation/validate_win64.py` を作成。Remilia のビルドに対してはまだ実行していない。
- [x] ビルドのリソース監視を `scripts/windows/guard-build.ps1` としてリポジトリに移動（guard v2 のロジックは変更なし。しきい値とパスはパラメーター化）。2026-11-26 に試験実行。この場所からのビルドではまだ使っていない。
- [ ] `deferred` 無変更の LibreWolf に対する `scripts/build.sh`：3 回の試行をログに記録。最後の試行は 2026-11-26 に、1145 個の統合 C++ ファイルのうち 260 個の時点で意図的に停止した。オブジェクトディレクトリ（6.9 GB）とすべてのログは `remilia-builds` ボリュームに保持している。
- [ ] `deferred` `scripts/package.sh`、BUILD.md への計測したビルド時間とリソース使用量の記載、正式なビルド方法の選択（BUILD.md に記載する）：フェーズ 5 に移動。
- [ ] LibreWolf の `main`（ed92167b）とタグ `161.0-1`（e2baf325）の差分を取り、リリース後の変更を把握する。

ボリューム `remilia-work`、`remilia-builds`、`remilia-mozbuild`、ダウンロード、ログ、
ツールチェーンは保持する。何も削除しない。

## フェーズ 3a — 構造と設定 `static-verified`

このフェーズではブラウザの動作を変更しない。後続のフェーズが中身を入れる仕組みを
作る。そのルールは `remilia/README.md` と ARCHITECTURE.md §10 に記載している。
以下の項目はすべて V0 と V1 に合格した（結果はメンテナーが記録し、公開しない）。いずれも `done` ではない：組み立てた
ファイルは、まだ実行中のブラウザに読み込まれていない（フェーズ 5）。

メンテナーが結果と最終監査を確認した後、2026-11-26 に静的検証（V0 + V1）により
完了した。フェーズ 5 で実行時の証拠が得られるまで、各項目は `static-verified` の
ままとする。

- [x] `static-verified` ライセンス：Remilia 独自ファイルは MPL-2.0（`LICENSE`、B5）。
- [x] `static-verified` カテゴリーの契約 `remilia/README.md`：構成、パッチのヘッダー、`prefs.cfg`、`policies.json`、`mozconfig`、`files/` + `replaces.txt`、`deviations.tsv`。
- [x] `static-verified` `scripts/remilia_layers.py`：V0 チェックと、`librewolf.cfg`、`policies.json`、`mozconfig` の決定的な組み立て（カテゴリーごとにヘッダー）。カテゴリー間の重複と、宣言されていない LibreWolf の上書きは失敗する。上書きは LibreWolf の関数を維持しなければならない。`lockPref` の再定義は `runtime-unverified` と記録する。
- [x] `static-verified` LibreWolf ベースのスナップショット `upstream/librewolf-base/`（準備したツリーと照合）。
- [x] `static-verified` `prepare.sh`：`REMILIA_LAYERS`、fuzz 0 でのパッチ適用、オーバーレイ、組み立て、バージョン・コミット・カテゴリー・ハッシュを含む来歴。保持しているツリーから隔離された `--staging` ツリー。
- [x] `static-verified` 除外リスト `upstream/librewolf-exclude.txt`（161.0-1 では空）。
- [x] `static-verified` V1 スクリプト `scripts/verify-tree.sh`（`docker.sh verify`）。ビルド用ボリュームは `staging/` を除き読み取り専用。
- [x] `static-verified` テスト用フィクスチャ `tests/layers/`（有効なセット、12 の無効なセット、49 の単体テスト）。パッケージには含めない。
- [x] `static-verified` フェーズ 3b のための LibreWolf のアイデンティティの棚卸し（概要は UPSTREAM.md）。
- [x] ゲート（V1）：`REMILIA_LAYERS=none` のツリーは、保持している LibreWolf 161.0-1 のツリーと同一。例外は、保持しているツリーにだけ存在し、その準備後に作られた 1110 項目（ビルドの副産物）で、差分はすべて結果に記載した。
- [x] フェーズ 3a の結果と最終監査のメンテナーによるレビュー（2026-11-26 承認）。

後続のフェーズに持ち越す既知の制限：上書きの検出は `librewolf.cfg`、
`policies.json`、`mozconfig` に対してだけ行う。それ以外の場所（既定の pref
ファイル、静的 pref、ブランディングの pref ファイル、コード）で設定される pref の
既定値は検出されない。アイデンティティの棚卸しも "librewolf" を含むテキスト行
だけが対象である（`remilia/README.md` の "What the checks cover"）。

## フェーズ 3b — ブランディング `todo`

カテゴリー：ブランディングのみ。このフェーズではプライバシーやセキュリティの変更を行わない。
未着手：メンテナーの明示的な承認待ち。

- [ ] Remilia という名前：アプリ名、リモーティング名、実行ファイルのアイデンティティ、プロファイルディレクトリ（UPSTREAM.md の変更箇所を参照）。内部の `lw/` ディレクトリ、`librewolf.cfg` という名前、`librewolf.*` の pref 名前空間は残す。セキュリティとプライバシーがブランディングに依存しないようにするため（`remilia/README.md`）。
- [ ] ロゴのコンセプト：スカーレットのひし形を左右対称のコウモリの翼が囲むデザイン。SVG のマスターを作成し、16/32/64/128/256 px で確認する。
- [ ] バリエーション：フルカラー、モノクロ、明るい背景用、暗い背景用、透過。
- [ ] Windows 用の `.ico` の生成、インストーラー用のビットマップ。
- [ ] `--with-branding` を置き換えるブランディングディレクトリ。
- [ ] ブリーフのカラーパレットを使ったブラウザテーマ（Firefox の CSS、フレームワークなし）。
- [ ] スタートページ（ローカルのみ、リモートコンテンツなし、すべての要素を任意で表示）。
- [ ] 3a からの持ち越し：`browser/branding/librewolf/pref/firefox-branding.js` の既定値と、棚卸しで見えないアイデンティティ（残っている "Firefox" の文字列、バイナリのアセット）を一覧にし、ブランディングの各 pref をそれと照合する。
- [ ] ゲート（V0 + V1）：ブランディング単独と、他のカテゴリーとの組み合わせ。結果を記録する。実行時のチェックはフェーズ 5 で行う。

## フェーズ 4a — セキュリティ `todo`

カテゴリー：セキュリティのみ。

- [ ] 拡張機能の署名を必須にする（SECURITY.md S1）。
- [ ] Remilia のアップデーターのアイデンティティ：MAR 鍵、アップデートホスト（S2。B1、B2 が必要）。
- [ ] 証明書：継承した設定のレビュー（SECURITY.md）。
- [ ] サンドボックス：継承したレベルを維持する。公式 Firefox との違いはフェーズ 5 で確認する。
- [ ] セーフブラウジングの決定（S3、B3）と、拡張機能の制限ドメイン（S4）。
- [ ] セキュリティに関係する LibreWolf のパッチと `librewolf.cfg` の各セクションの 1 行ずつのレビュー。
- [ ] `runtime-unverified` の pref とポリシー（`lockPref` の再定義など）を、公式の LibreWolf 161.0-1 バイナリで実行時に確認する。4a と 4b の両方が対象（`remilia/README.md`）。
- [ ] 3a からの持ち越し：`librewolf.cfg` 以外で設定されるセキュリティ関連の pref の既定値（既定の pref ファイルと静的 pref。LibreWolf が変更した値を含む）はチェックで検出されない。これを確認し、ツールで扱うべきかを決める。
- [ ] ゲート（V0 + V1）：セキュリティ単独と、それまでのすべてのカテゴリーとの組み合わせ。結果を記録する。

## フェーズ 4b — プライバシー `todo`

カテゴリー：プライバシーのみ。

- [ ] 文書化された相違点だけを含むプライバシーの pref。それ以外はすべて LibreWolf から継承する：トラッキング防止、フィンガープリンティング、テレメトリ、Cookie とストレージ、DNS over HTTPS、WebRTC。
- [ ] D1〜D3 を解決する。
- [ ] 設定 UI：わかりやすい説明を付け、RFP の副作用と切り替えを提示する。
- [ ] uBlock Origin：AMO 署名済みの xpi を固定し（SHA-256）、`distribution/extensions/` に同梱する。
- [ ] Remilia の `assets.json`（uBO の標準 + `spa-1`、LibreWolf による追加分、評価中のブラジルのリスト）を `assetsBootstrapLocation` で提供する。
- [ ] 3a からの持ち越し：`librewolf.cfg` 以外で設定されるプライバシー関連の pref の既定値はチェックで検出されない。プライバシーの pref を設定する前にこれを確認し、ツールで扱うべきかを決める。
- [ ] ゲート（V0 + V1）：プライバシー単独と、すべてのカテゴリーとの組み合わせ。結果を記録する。

## フェーズ 5 — 統合した状態での最初のビルドと検証 `todo`

Remilia の最初のフルビルド：フェーズ 2 の基盤を、統合したカテゴリーに適用する。

- [ ] V2：ビルド、パッケージング、sha256、出自情報。ビルド時間、ディスク使用量、RAM 使用量を BUILD.md に記録する。
- [ ] リリースの正式なビルド方法を決め、BUILD.md に記載する。任意：デバッグ用に方法 B（ネイティブの MozillaBuild、B6 の後）。
- [ ] V3：[検証チェックリスト](#検証チェックリスト)。結果は `internal/evidence/<date>-<build>/` に保存（形式は `tests/validation/README.md`）。
- [ ] 新規プロファイルのパケットキャプチャ：すべての外向き接続を PRIVACY.md に一覧化する。
- [ ] uBlock Origin：初回起動時のオフライン動作、AMO によるアップデート、定評のある広告ブロックのテストページ。結果を正直に記録する。
- [ ] フェーズ 3a〜4b の項目は、記録された証拠がある場合にのみ `static-verified` から `done` に変わる。

フェーズ 5 は、メンテナーが記録された結果を確認してはじめて完了とする。

## フェーズ 6 — ユーザー体験 `todo`
ツールバー、タブ、アドレスバー、ダウンロード、ブックマーク、設定、そして決定事項 D4
（パネルは uBO の実データのみに基づいて作る）。これらの大部分は Firefox の既存機能で
あり、Remilia の作業はテーマ（ブランディング）と設定（プライバシー／セキュリティ）で、
それぞれカテゴリーごとに管理します。

## フェーズ 7 — セキュリティとテスト `todo`
BrowserLeaks、EFF Cover Your Tracks、DNS と WebRTC の漏洩テスト、互換性テスト
スイート、パフォーマンスのプロファイリング。結果は日付とバージョンを付けて
`internal/evidence/<date>-<build>/` に記録します（ローカル、非公開）。

## フェーズ 8 — 配布 `todo`
NSIS インストーラーとポータブル版の zip（どちらも LibreWolf の bsys6 に存在）、MAR
アップデートのパイプライン、アップデートサーバー、リリース用ドキュメント。B1、B2、
B4 に依存します。

## 検証チェックリスト

Windows 10 x64（メンテナーのマシン）で新しいプロファイルを使って実施する。
各チェックは、合格、不合格、または理由付きで対象外として記録する。証拠は
`tests/validation/validate_win64.py` が収集し、判定は人が記入する。

| チェック | 方法 |
|---|---|
| 起動 | 展開したパッケージから起動し、プロファイルが作成され、クラッシュせず、`about:support` が開く |
| 実際のサイトの閲覧 | 決められた実サイトの一覧（ニュース、動画、地図、ウェブメールのログインページ、政府のサイト、ブラジルの銀行の公開ページ）が読み込まれ、正しく表示される |
| JavaScript とウェブ互換性 | JS を多用するサイトが動作し、標準的なウェブプラットフォームのテストページが動く |
| 音声と動画 | HTML5 の音声・動画の再生（オープンなコーデックと H.264）。DRM／EME の状態を記録（LibreWolf のポリシーで無効） |
| グラフィックアクセラレーション | `about:support` → グラフィック：コンポジター、WebRender、GPU アクセラレーションの状態 |
| Firefox 拡張機能 | addons.mozilla.org から署名済みの拡張機能をインストールし、有効化、無効化、削除する |
| uBlock Origin | 初回起動時に存在し、広告ブロックのテストページでブロックし、ダッシュボードが開く |
| マルチプロセス | `about:support` のマルチプロセスウィンドウと Fission。`about:processes` に個別のコンテンツプロセスが表示される |
| サンドボックス | `about:support` のサンドボックスレベルが、同じマシン上の公式 Firefox 161 と同じ |
| プロファイル管理 | `about:profiles`：プロファイルの作成、切り替え、削除。設定どおり再起動後もデータが保持される |
| ダウンロード | ファイルをダウンロードする。進捗、保存場所、履歴、危険なファイルの警告 |
| アップデート | ビルドに `--disable-updater`（LibreWolf のベース mozconfig）がある間は対象外。フェーズ 4a のアップデーターのアイデンティティができた時点で対象になる |
| パッケージの完全性 | sha256 を記録。パッケージを再展開して同一であること。`.exe`／`.dll` に対する `winchecksec`（ASLR、DEP、CFG） |

## 有効な決定

| 決定 | 説明している文書 | ステータス |
|---|---|---|
| Firefox Release の上の、固定した LibreWolf リリースにレイヤーを重ねる | ARCHITECTURE.md §2 | 承認済み |
| `librewolf.cfg` を継承し、逸脱は文書化された理由がある場合のみ | PRIVACY.md、SECURITY.md、`remilia/README.md` | 承認済み |
| 署名済みの uBO の xpi を同梱し、デフォルトは `toOverwrite` ではなく `assetsBootstrapLocation` で設定する | ARCHITECTURE.md §6 | 承認済み |
| 変更カテゴリーの分離：アップストリーム、ビルド修正、セキュリティ、プライバシー、ブランディング | ARCHITECTURE.md §10 | 承認済み |
| ビルドの成功は動作するブラウザを意味しない。何かを「動作する」と呼ぶ前に検証のゲートを設ける | ARCHITECTURE.md §11、検証チェックリスト（このファイル） | 承認済み |
| ブランディング、セキュリティ、プライバシーが統合されるまで最初のフルビルドを延期する。検証レベル V0〜V3 | ARCHITECTURE.md §11、検証の方針（このファイル） | 承認済み |
| フェーズ 3a の決定：MPL-2.0、AutoConfig の組み立てルール、隔離されたステージング、内部名 `librewolf.*` の維持、フィクスチャ、リソース監視 | `remilia/README.md`、CONTRIBUTING.md（ライセンス）、BUILD.md（リソース監視） | 承認済み |

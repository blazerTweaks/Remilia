<!-- i18n:nav -->
[English](../../SECURITY.md) | [Português (Brasil)](../pt-BR/SECURITY.md) | **日本語** | [Español](../es/SECURITY.md)
<!-- /i18n:nav -->

<!-- i18n:meta -->
> - **Translation status:** Current
> - **Language:** ja
> - **Original language:** English
> - **Source:** [SECURITY.md](../../SECURITY.md)
> - **Source revision:** sha256:a93382773a101575a8d0edac736d9c03534c00051f0870bfca987ba98d37c1a1
<!-- /i18n:meta -->

# REMILIA Browser — セキュリティ

ステータス：**設計のみ。** REMILIA のビルドはまだ存在しません。

プライバシーとセキュリティは別の概念です。プライバシーのための設定が Firefox の
セキュリティアーキテクチャを弱めることは決してあってはなりません。このファイルでは、
REMILIA が行う、または継承する、セキュリティに関わるすべての変更を、その根拠と
ともに列挙します。

## 脆弱性の報告

専用の窓口ができるまでは、メンテナーに非公開で報告してください。脆弱性について
公開の issue を立てないでください。エンジンの脆弱性はアップストリーム（Mozilla の
Bugzilla、セキュリティグループ）に報告すべきものです。修正を含むアップストリームの
リリースが公開された時点で、REMILIA もその修正を配布します。

## 変更せずに維持するもの

- Gecko のマルチプロセスアーキテクチャと **Fission**（サイト分離）。
- **Windows のコンテンツプロセスサンドボックス**（`--enable-sandbox`、LibreWolf の
  Windows 用 mozconfig から継承）。メモリ節約のためにレベルを下げることはしません。
- NSS による証明書の検証。**決して無効化しません。** 独自の TLS や暗号の実装は
  行いません。
- 混在コンテンツのブロック、HSTS、HPKP の静的ピンニング。
- 拡張機能の署名検証（後述。これは LibreWolf との意図的な相違点です）。
- ビルドのハードニング：`--enable-hardening`、`--enable-stl-hardening`、
  `-ftrivial-auto-var-init=zero`、`-fwrapv`（継承）。

## LibreWolf から継承するハードニング — 維持

| 設定 | 効果 |
|---|---|
| `security.pki.crlite_mode = 2` | CRLite による失効確認をローカルで強制する。 |
| `security.OCSP.enabled = 0` | OCSP リクエストを行わない（プライバシーのため）。CRLite に依存する。 |
| `security.cert_pinning.enforcement_level = 2` | 厳格なピンニング。アンチウイルスによる TLS の傍受と衝突する場合がある。トラブルシューティングに記載する。 |
| `security.ssl.require_safe_negotiation = true` | RFC 5746 に対応していないサーバーを拒否する。不具合はまれ。 |
| `security.tls.enable_0rtt_data = false` | TLS 1.3 の 0-RTT を使わない（リプレイのリスク）。 |
| `security.enterprise_roots.enabled = false` | Windows の証明書ストアのルート証明書を自動的には信頼しない。 |
| `network.IDN_show_punycode = true` | ホモグラフ攻撃への対策。 |
| `pdfjs.enableScripting = false` | PDF ビューアーで JS を実行しない。 |

## REMILIA と LibreWolf の相違点（セキュリティ上の理由によるもの）

| # | LibreWolf | REMILIA（計画） | 理由 |
|---|---|---|---|
| S1 | `MOZ_REQUIRE_SIGNING=`（空）：pref により署名のない拡張機能を有効にできる | Mozilla のデフォルトを維持：署名は **必須** で、pref では無効にできない | 改ざんされた拡張機能や署名のない拡張機能のインストールを防ぐ。開発者は引き続き `about:debugging` から一時的なアドオンを読み込める。 |
| S2 | LibreWolf の MAR アップデート署名用公開鍵を同梱。アップデートホストは `update.librewolf.net` | REMILIA 独自の MAR 鍵とアップデートホスト | REMILIA のバイナリは、REMILIA が署名したアップデートだけを受け入れなければならない。公開ビルドの前に必須。 |
| S3 | セーフブラウジングを完全に無効化 | **評価 — 下記を参照** | プロジェクトの要件はセーフブラウジングによる保護を求めている。 |
| S4 | `extensions.webextensions.restrictedDomains = ""`（拡張機能が addons.mozilla.org などで動作できる） | **評価：** Firefox のデフォルトに戻す | 制限ドメインのリストは、侵害された拡張機能がアドオンストアのページを操作することを防ぐ。 |

### S3 — セーフブラウジング：未解決の課題

Firefox のセーフブラウジングは Google のハッシュプレフィックスのリストを
ダウンロードして URL をローカルで照合し、部分一致があった場合にのみハッシュ
プレフィックスを送信します。これには **ビルドに組み込まれた Google Safe Browsing の
API キー** が必要です。Mozilla のキーはフォークでは使用できません。Google は
Safe Browsing API の利用を非商用に限定しており、商用利用には有料の Web Risk API が
必要です。

フェーズ 4 で決定する選択肢：

1. REMILIA 用の Safe Browsing API キー（非商用プロジェクトとして）を取得し、
   フィッシング／マルウェアのリスト照合を有効にする。ダウンロードの *リモート*
   レピュテーション確認（`browser.safebrowsing.downloads.remote.*`）はファイルの
   メタデータを Google に送信するため、**無効** のままにする。
2. キーを取得できない場合：セーフブラウジングは無効のままとし、uBO のマルウェア／
   フィッシング対策リスト（`urlhaus-1`、`curben-phishing`、デフォルトで有効）と、
   任意で使えるマルウェアブロック機能付きの DoH リゾルバーに頼る。これはセーフ
   ブラウジングより弱いことを正直に説明しなければならない。

ローカルでのダウンロード保護（危険なファイル形式の警告、Mark-of-the-Web）は
セーフブラウジングとは独立しており、引き続き有効です。

## サプライチェーン

- Firefox のソース：`archive.mozilla.org` の、GPG で検証した tarball。
- LibreWolf のソース：`upstream/pins.env` に固定したコミットハッシュ。
- uBlock Origin：AMO 署名済みの `.xpi`。バージョンと SHA-256 を固定。
- ビルドツールチェーン：`mach` で取得（Mozilla の Taskcluster アーティファクト）、
  またはバージョンを固定したコンテナイメージ。
- リリース署名用の鍵（MAR、Authenticode）は、このリポジトリに決してコミットしません。

## セキュリティアップデートの方針

Firefox のセキュリティリリースが最優先です。目標：対応する LibreWolf のリリースから
72 時間以内に REMILIA のビルドを公開する。各リリースノートには、含まれる Mozilla
Security Advisories（MFSA）を記載します。

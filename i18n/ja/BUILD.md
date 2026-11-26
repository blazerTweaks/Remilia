<!-- i18n:nav -->
[English](../../BUILD.md) | [Português (Brasil)](../pt-BR/BUILD.md) | **日本語** | [Español](../es/BUILD.md)
<!-- /i18n:nav -->

<!-- i18n:meta -->
> - **Translation status:** Current
> - **Language:** ja
> - **Original language:** English
> - **Source:** [BUILD.md](../../BUILD.md)
> - **Source revision:** sha256:5532a997ca4ac008ffcc43b6011129078eac39ce1b873fea15db8e6ee4c0a3ff
<!-- /i18n:meta -->

# REMILIA のビルド

ステータス：**まだビルドできません。** fetch／patch／build のスクリプトはフェーズ 2
の作業です。このドキュメントでは、確認済みの要件と予定している手順を説明します。
*(Phase 2)* と記載された手順は、まだ実行されていません。

## 要件

Mozilla の Windows 向けビルドガイド（`docs/setup/windows_build.md`、mozilla-firefox/firefox `main`）より：

- Windows 10/11 x64。
- 8 GB 以上の RAM（最低 4 GB）。最適化ビルドには 16〜32 GB を強く推奨。
- ソースツリー + オブジェクトディレクトリごとに **40 GB 以上の空きディスク容量**。
- ソースや MozillaBuild のパスにスペースを含めないこと。
- 推奨：**Dev Drive**（ビルドが 5〜10% 高速化。Windows 11 のみ）。
- ソースディレクトリと `%USERPROFILE%\.mozbuild` を Windows Defender の除外対象に追加する（bootstrap が追加を提案してくれる）。

リファレンスマシン（メンテナー）：Ryzen 5 3600（6C/12T）、32 GB RAM、
Windows 10 Pro 19045、Docker Desktop（WSL2）、Visual Studio インストール済み。
ビルド時間はフェーズ 2 の後にここに記録します。現時点では数値を示していません。

## 方法 A — Docker でのクロスコンパイル（リリース用として予定）

LibreWolf が公開している Windows バイナリのビルド方法（`bsys6`、
`assets/Dockerfile.windows`）と同じです：clang、`x86_64-pc-windows-msvc`
ターゲット付きの Rust、Mozilla の `taskcluster/scripts/misc/get_vs.py` で取得する
Windows SDK、Wine（`widl`）、`fxc2`、NSIS を含む Debian イメージを使います。

*(Phase 2)*

```sh
# inside WSL2 or any x86_64 Linux with Docker
./scripts/fetch.sh            # Firefox tarball + GPG verify, LibreWolf @ pinned commit
./scripts/prepare.sh          # apply LibreWolf, then REMILIA layers
./scripts/build.sh windows    # runs mach in the build container
```

注意：
- 作業ディレクトリは Linux のファイルシステム（Docker ボリュームまたは WSL の ext4）に
  置き、`/mnt/c` や `/mnt/d` の下には **置かない** でください。ファイルシステムを
  またぐ I/O は非常に低速です。
- Docker Desktop の WSL2 VM には、デフォルトでホストの RAM の 50% が割り当てられます。
  リンク時にメモリが不足する場合は、`%USERPROFILE%\.wslconfig`（`memory=24GB`）で
  増やしてください。

## 方法 B — MozillaBuild による Windows ネイティブビルド（開発用）

*(Phase 2)*

1. MozillaBuild（最新版）を `C:\mozilla-build` にインストールする。
2. `C:\mozilla-build\start-shell.bat` を開く。
3. 準備済みの REMILIA のツリーで：`./mach --no-interactive bootstrap --application-choice=browser`
   （clang、Rust、Windows SDK をダウンロードする。Defender の除外設定のために UAC が一度表示される）。
4. `./mach build`、続いて `./mach run`。

反復開発のヒント：`./mach build faster` を使うと、フロントエンドのみ
（JS/CSS/XHTML/Fluent）の変更を数秒で再ビルドできます。UI やブランディングの作業に
使ってください。

## ビルドの検証 *(Phase 2)*

- `./mach run` は一時プロファイルで起動します。
- `about:support` にはバージョンと、`Multiprocess Windows`、`Fission`、
  `Sandbox` の各レベルが表示されます。いずれも、同じマシン上の同じバージョンの
  公式 Firefox ビルドが示すレベルと一致しなければなりません。
- `about:policies` に REMILIA のポリシーが有効として表示されます。
- `about:config` → `general.config.filename` に REMILIA の cfg が表示されます。

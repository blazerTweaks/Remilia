<!-- i18n:nav -->
[English](../../BUILD.md) | [Português (Brasil)](../pt-BR/BUILD.md) | **日本語** | [Español](../es/BUILD.md)
<!-- /i18n:nav -->

<!-- i18n:meta -->
> - **Translation status:** Current
> - **Language:** ja
> - **Original language:** English
> - **Source:** [BUILD.md](../../BUILD.md)
> - **Source revision:** sha256:717bcf7ecd7362413cfc986362c160ad2db3db152e186aa189a38d505409553e
<!-- /i18n:meta -->

# Remilia のビルド

ステータス：**ビルド基盤は作成済みで一部を実証済み。最初のフルビルドは延期。**
fetch、prepare、toolchains の各ステップは正常に完了しています。コンパイルの
ステップは、無変更の LibreWolf 161.0-1 の統合 C++ ファイル 1145 個のうち 260 個まで
進んだところで意図的に停止しました。最初のフルビルドは、ブランディング、セキュリティ、
プライバシーが統合された時点で Remilia に対して行います（ROADMAP のフェーズ 5）。
*(Phase 5)* と記載された手順は、まだ完了していません。

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
ビルド時間は最初のフルビルド（フェーズ 5）の後にここに記録します。現時点では
数値を示していません。

## 方法 A — Docker でのクロスコンパイル（リリース用として予定）

LibreWolf が公開している Windows バイナリのビルド方法（`bsys6`、
`assets/Dockerfile.windows`）と同じです：clang、`x86_64-pc-windows-msvc`
ターゲット付きの Rust、Mozilla の `taskcluster/scripts/misc/get_vs.py` で取得する
Windows SDK、Wine（`widl`）、`fxc2`、NSIS を含む Debian イメージを使います。

*(`build` と `package` は Phase 5)*

```sh
# from the repository root, in Git Bash or any shell with Docker
./scripts/docker.sh image       # build-environment image
./scripts/docker.sh fetch       # Firefox tarball + GPG verify, LibreWolf @ pinned commit
./scripts/docker.sh prepare     # apply LibreWolf, then Remilia layers
./scripts/docker.sh toolchains  # clang, Rust, Windows SDK, Wine, NSIS
./scripts/docker.sh build       # mach build
./scripts/docker.sh package     # .win64.zip + sha256 + provenance in dist/
```

注意：
- 作業ディレクトリは Linux のファイルシステム（Docker ボリュームまたは WSL の ext4）に
  置き、`/mnt/c` や `/mnt/d` の下には **置かない** でください。ファイルシステムを
  またぐ I/O は非常に低速です。
- Docker Desktop の WSL2 VM には、デフォルトでホストの RAM の 50% が割り当てられます。
  リファレンスマシンではデフォルトのままだと VM のメモリが不足しました。
  `%USERPROFILE%\.wslconfig` に `memory=18GB` と `swap=24GB` を設定し、並列ジョブ 6 で
  ビルドできています。
- `prepare.sh` は、準備済みのツリーを上書きしません。オブジェクトディレクトリが
  その中にあるためです。`--force` を付けると両方とも削除されます。`remilia-builds`
  ボリュームに保持しているツリーには決して使わないでください。
- `REMILIA_LAYERS` で `prepare.sh` が適用する Remilia のカテゴリーを選びます。
  `all`（既定）、`none`（無変更の LibreWolf）、または `security,privacy` のような
  リストです。`remilia/README.md` を参照してください。
- `prepare.sh --staging <name>` は `/builds/work/staging/<name>` に別のツリーを
  準備し、保持しているツリーには一切触れません。別のレイヤールートや除外リスト
  （テスト用フィクスチャ）を受け付けるのはステージングツリーだけです。

## コンパイルしないツリーチェック（V1）

```sh
./scripts/docker.sh verify
```

ステージングツリーを準備し、保持しているツリーと比較します。カテゴリーなし、
フィクスチャの各カテゴリー単独と全カテゴリー、パッチの逆適用、LibreWolf パッチの
除外を確認します。コンパイルは行いません。`remilia-builds` ボリュームは
`staging/` ディレクトリを除いて読み取り専用でマウントされるため、保持している
ツリー、そのオブジェクトディレクトリ、ログは変更できません。各ステージング
ツリーは存在する間だけ約 6 GB を使い、その後削除されます。レポートは
`dist/verify-tree/<timestamp>/` に出力されます。

## リソース監視（Windows ホスト）

`scripts/windows/guard-build.ps1` はビルド中の Windows と WSL2 のメモリを計測し、
メモリが尽きたときに SIGINT でビルドを止めます（WSL や Docker を停止することは
ありません）。ビルドコンテナより先に起動してください。ビルドコンテナは
`--name remilia-build-run` で起動する必要があります（または `-Container` を
指定します）。

```powershell
.\scripts\windows\guard-build.ps1 -Csv "$env:TEMP\guard.csv" -Events "$env:TEMP\guard-events.log"
```

しきい値はパラメーター、または `-ConfigFile` で渡す `.psd1` ファイルのキーで
指定します。既定値はフェーズ 2 のビルドで使った値です。

## 方法 B — MozillaBuild による Windows ネイティブビルド（開発用）

*(Phase 5、任意)*

1. MozillaBuild（最新版）を `C:\mozilla-build` にインストールする。
2. `C:\mozilla-build\start-shell.bat` を開く。
3. 準備済みの Remilia のツリーで：`./mach --no-interactive bootstrap --application-choice=browser`
   （clang、Rust、Windows SDK をダウンロードする。Defender の除外設定のために UAC が一度表示される）。
4. `./mach build`、続いて `./mach run`。

反復開発のヒント：`./mach build faster` を使うと、フロントエンドのみ
（JS/CSS/XHTML/Fluent）の変更を数秒で再ビルドできます。UI やブランディングの作業に
使ってください。

## ビルドの検証 *(Phase 5)*

- `./mach run` は一時プロファイルで起動します。
- `about:support` にはバージョンと、`Multiprocess Windows`、`Fission`、
  `Sandbox` の各レベルが表示されます。いずれも、同じマシン上の同じバージョンの
  公式 Firefox ビルドが示すレベルと一致しなければなりません。
- `about:policies` に Remilia のポリシーが有効として表示されます。
- `about:config` → `general.config.filename` に Remilia の cfg が表示されます。

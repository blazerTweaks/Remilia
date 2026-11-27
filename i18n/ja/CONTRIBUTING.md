<!-- i18n:nav -->
[English](../../CONTRIBUTING.md) | [Português (Brasil)](../pt-BR/CONTRIBUTING.md) | **日本語** | [Español](../es/CONTRIBUTING.md)
<!-- /i18n:nav -->

<!-- i18n:meta -->
> - **Translation status:** Current
> - **Language:** ja
> - **Original language:** English
> - **Source:** [CONTRIBUTING.md](../../CONTRIBUTING.md)
> - **Source revision:** sha256:54c611a0a73f59196c60663e6a67fb6e8c3faff4b56ea530995b10477c23308b
<!-- /i18n:meta -->

# Remilia へのコントリビューション

## 基本ルール

1. **見せかけの機能を作らない。** 機能の代わりにモックアップを置いたり、
   作り物の統計値を表示したりしないこと。実装されていないものは、ドキュメントに
   そう明記する。
2. **利便性やベンチマークのためにセキュリティを弱めない。** 証明書の検証、
   サンドボックス、Fission、拡張機能の署名は交渉の余地がない。
3. **プライバシーやセキュリティに関わる変更はすべて文書化する。** 同じ変更の中で、
   理由とともに PRIVACY.md または SECURITY.md に記載すること。
4. **アップストリーム優先。** pref、次にポリシー、次にファイルの上書き、最後に
   ソースパッチの順に検討する。UPSTREAM.md を参照。
5. **新しい依存関係やフレームワークは追加しない。** 具体的な理由を変更の中で説明し、
   メンテナーが受け入れた場合を除く。ブラウザの UI には Firefox 自身のフロントエンド技術を使う。
6. **テスト結果やベンチマークを捏造しない。** 何を、どのビルドで、いつ実行し、
   何が失敗したかを記録する。

## 変更の進め方

- コミットは小さく、1 つのコミットに 1 つの関心事と 1 つのカテゴリー（アップストリーム、
  ビルド修正、セキュリティ、プライバシー、ブランディング。ARCHITECTURE.md §10）。
  メッセージには *なぜ* を書く。
- Remilia の新しいパッチ、pref、ポリシー：所属する 1 つのカテゴリーのディレクトリ
  `remilia/<category>/` に置く。パッチはそのカテゴリーの `patches/` と `series` に
  入れ、ヘッダー（カテゴリー、目的、影響するファイルと pref、アップストリームに提出
  可能か、取り消した場合の影響）を付ける。2 つのカテゴリーにまたがる変更は 2 つに
  分割する。正確な形式は `remilia/README.md` にある。
- LibreWolf の値を上書きする値は、そのカテゴリーの `deviations.tsv` にエントリーを
  追加し、理由を PRIVACY.md または SECURITY.md に記す（ブランディングは
  UPSTREAM.md の変更箇所一覧）。
- アーキテクチャに関わる選択は、実装の前にコンテキスト、決定、影響を添えて
  メンテナーに提案する。採用されたら、その効果を ARCHITECTURE.md に記述する。
- タスクのステータスが変わったら ROADMAP.md を更新する。

## 検証

変更のたびに：静的チェック（ROADMAP.md の「検証の方針」の V0）。フェーズを
完了する前に：ツリーチェック（V1）。

```sh
python scripts/remilia_layers.py check        # V0: categories, duplicates, deviations
python -m unittest discover -s tests/layers   # V0: tests of the category tool
python -m unittest discover -s tests/validation  # V0: tests of the validation harness
python i18n/i18n.py check                     # V0: documentation translations
./scripts/docker.sh verify                    # V1: staging trees, no compilation
```

変更のたびにフルビルドを行う必要はない。
最初のフルビルドは、ブランディング、セキュリティ、プライバシーが統合された時点で
行う。コンパイルしないと検証できない変更は、ビルドを始める前に理由を
説明する。

ビルドの成功は、ブラウザが動作することを意味しない。どのビルドも、動作するものと
呼ぶ前に[検証チェックリスト](ROADMAP.md#検証チェックリスト)を実施し、結果を
`internal/evidence/<date>-<build>/`（Git が無視するローカルのフォルダー。検証記録は
コミットしない）に記録する。V0 と V1 にだけ合格した作業は
`static-verified` であり、`done` ではない。

## ライセンス

Remilia 独自のオリジナルファイルは MPL-2.0 です（[LICENSE](../../LICENSE)）。
Firefox や LibreWolf のファイルに関わるコントリビューションも MPL-2.0 となります。
Firefox、LibreWolf その他の第三者コンポーネントから継承したファイルは、それぞれの
ライセンスと表示を保持します。それらを変更しないでください。

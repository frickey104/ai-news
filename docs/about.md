---
title: ソース一覧
description: AI ニュースまとめの情報収集元
---

# ソース一覧

このサイトは以下のソースから毎週自動収集しています。

## 📰 ニュースメディア（RSS）

| メディア | 言語 | 特徴 |
|---------|------|------|
| **TechCrunch** | 英語 | AI・スタートアップの速報 |
| **VentureBeat** | 英語 | AI事業・エンタープライズ動向 |
| **The Verge** | 英語 | テクノロジーカルチャー・製品レビュー |

## 💬 コミュニティ

| コミュニティ | 特徴 |
|------------|------|
| **Reddit r/MachineLearning** | AI研究者・エンジニアの議論。論文・技術トピック中心 |
| **Reddit r/LocalLLaMA** | オープンソースLLMの活用事例・ベンチマーク比較 |
| **HackerNews** | シリコンバレー発のAI話題。週間トップをAIキーワードでフィルタ |

## 🎥 YouTube

| チャンネル | 特徴 |
|----------|------|
| **Matt Wolfe** | 週次のAIツール・ニュースまとめ。網羅性が高い |
| **AI Explained** | AIモデルの技術解説。深い分析が特徴 |
| **Two Minute Papers** | 最新AI論文を2分で解説。研究トレンドを把握しやすい |

---

## 更新の仕組み

```
毎週日曜日 AM9:00（JST）
 └── GitHub Actions が自動起動
      ├── RSS フィード取得
      ├── Reddit / HackerNews API 取得
      └── YouTube チャンネル RSS 取得
 └── Markdown ファイル自動生成
 └── VitePress でビルド
 └── GitHub Pages にデプロイ
```

情報源の追加や改善の要望は [GitHub Issues](https://github.com/Shin-sibainu/cc-company/issues) まで。

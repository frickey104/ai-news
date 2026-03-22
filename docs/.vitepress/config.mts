import { defineConfig } from "vitepress";

export default defineConfig({
  title: "AI ニュースまとめ",
  base: "/cc-company/",
  description: "生成AI・テクノロジーの最新情報を毎週自動収集してお届け",
  lang: "ja",
  cleanUrls: true,

  head: [
    ["meta", { name: "theme-color", content: "#0f172a" }],
    ["meta", { property: "og:type", content: "website" }],
    ["meta", { name: "viewport", content: "width=device-width, initial-scale=1.0" }],
  ],

  themeConfig: {
    nav: [
      { text: "最新号", link: "/" },
      { text: "アーカイブ", link: "/weekly/" },
      { text: "ソース一覧", link: "/about" },
    ],

    sidebar: false,

    socialLinks: [
      { icon: "github", link: "https://github.com/Shin-sibainu/cc-company" },
    ],

    footer: {
      copyright: "© 2026 AI ニュースまとめ &nbsp;|&nbsp; 毎週日曜自動更新",
    },

    search: {
      provider: "local",
    },

    outline: false,
  },
});

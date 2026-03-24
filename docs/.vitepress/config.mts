import { defineConfig } from "vitepress";

export default defineConfig({
  title: "AI NEWS",
  base: "/ai-news/",
  description: "生成AIの最新情報を毎日自動収集してお届け",
  lang: "ja",
  cleanUrls: true,
  appearance: "dark",

  head: [
    ["meta", { name: "theme-color", content: "#0f172a" }],
    ["meta", { property: "og:type", content: "website" }],
    ["meta", { name: "viewport", content: "width=device-width, initial-scale=1.0" }],
  ],

  themeConfig: {
    nav: [
      { text: "TODAY", link: "/" },
      { text: "ARCHIVE", link: "/daily/" },
      { text: "SOURCES", link: "/about" },
    ],

    sidebar: false,

    socialLinks: [
      { icon: "github", link: "https://github.com/Shin-sibainu/cc-company" },
    ],

    footer: {
      copyright: "© 2026 AI NEWS &nbsp;|&nbsp; Updated daily at 6:00 AM JST",
    },

    search: {
      provider: "local",
    },

    outline: false,
  },
});

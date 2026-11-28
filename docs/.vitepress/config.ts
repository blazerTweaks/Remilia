import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vitepress'
import { repoLinks, sourceOf } from './repo-links'

const REPO_URL = 'https://github.com/ivuia/Remilia'
const BRANCH = 'main'
// GitHub Pages project site: https://ivuia.github.io/Remilia/
const BASE = '/Remilia/'

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..')

export default defineConfig({
  base: BASE,
  lang: 'en-US',
  title: 'Remilia',
  description:
    'Documentation for Remilia, a privacy-focused desktop browser built on Firefox (Gecko) and LibreWolf. In development: there is no release yet.',

  appearance: 'force-dark',
  cleanUrls: true,
  // docs/README.md is for maintainers of this site; docs/research/ is
  // maintainer-only material kept out of Git (.gitignore) and must never be
  // built, even locally.
  srcExclude: ['README.md', 'research/**'],

  head: [
    // `head` is not rewritten with `base`, so the prefix is written out here.
    ['link', { rel: 'icon', type: 'image/svg+xml', href: `${BASE}brand/remilia-hat.svg` }],
    ['meta', { name: 'theme-color', content: '#111014' }],
  ],

  transformPageData(pageData) {
    const source = sourceOf(pageData.relativePath)
    if (source) pageData.frontmatter.editSource = source
  },

  markdown: {
    config(md) {
      md.use(repoLinks, { repoRoot, repoUrl: REPO_URL, branch: BRANCH })
    },
  },

  themeConfig: {
    // Wordmark 3 (flat scarlet): the cleanest at small sizes on a dark background.
    logo: { src: '/brand/remilia-wordmark-3.svg', alt: 'Remilia' },
    siteTitle: false,

    nav: [
      { text: 'Guide', link: '/guide/overview', activeMatch: '^/(guide|browser)/' },
      { text: 'Privacy', link: '/privacy/', activeMatch: '^/privacy/' },
      { text: 'Security', link: '/security/', activeMatch: '^/security/' },
      { text: 'Development', link: '/development/building', activeMatch: '^/development/' },
      { text: 'Roadmap', link: '/project/roadmap', activeMatch: '^/project/' },
    ],

    sidebar: [
      {
        text: 'Introduction',
        items: [{ text: 'Overview', link: '/guide/overview' }],
      },
      {
        text: 'Browser',
        items: [
          { text: 'Architecture', link: '/browser/architecture' },
          { text: 'Firefox & LibreWolf upstream', link: '/browser/upstream' },
        ],
      },
      {
        text: 'Privacy & security',
        items: [
          { text: 'Privacy', link: '/privacy/' },
          { text: 'Security', link: '/security/' },
        ],
      },
      {
        text: 'Development',
        items: [
          { text: 'Building', link: '/development/building' },
          { text: 'Change categories', link: '/development/change-categories' },
          { text: 'Validation harness', link: '/development/validation' },
          { text: 'Contributing', link: '/development/contributing' },
        ],
      },
      {
        text: 'Project',
        items: [
          { text: 'Roadmap & status', link: '/project/roadmap' },
          { text: 'License', link: '/project/license' },
        ],
      },
    ],

    outline: { level: [2, 3], label: 'On this page' },
    externalLinkIcon: true,
    search: { provider: 'local' },

    // Pages that publish a repository document send edits to that document
    // (`editSource`, set in transformPageData below). This function runs in
    // the browser, so it cannot use anything defined outside its own body.
    editLink: {
      pattern: ({ filePath, frontmatter }) =>
        'https://github.com/ivuia/Remilia/edit/main/' +
        (frontmatter.editSource ?? 'docs/' + filePath),
      text: 'Edit this page on GitHub',
    },

    socialLinks: [{ icon: 'github', link: REPO_URL, ariaLabel: 'Remilia on GitHub' }],

    footer: {
      message: 'Remilia is in development. There is no Remilia release yet.',
      copyright:
        'Remilia’s own files are licensed under MPL-2.0. Touhou Project and Remilia Scarlet are creations of ZUN / Team Shanghai Alice; Remilia is an independent fan-inspired project.',
    },
  },
})

# Remilia documentation website

The public documentation site, built with [VitePress](https://vitepress.dev/)
1.6.4 and published to GitHub Pages at <https://ivuia.github.io/Remilia/>.

This file is for maintainers of the site and is not published (`srcExclude`
in `.vitepress/config.ts`).

## Running locally

Requires Node.js 20 or later. From this directory (`docs/`):

```sh
npm install            # or `npm ci` to install exactly what the lockfile pins
npm run docs:dev       # development server with hot reload
npm run docs:build     # production build into .vitepress/dist/
npm run docs:preview   # serve the production build at http://localhost:4173/Remilia/
```

The site is built for the `/Remilia/` base path, so local URLs include it.

**Windows, Git Bash:** `cd /d/...` gives Node a lower-case drive letter, which
makes `vitepress build` fail with `ERR_MODULE_NOT_FOUND` /
`Cannot read properties of undefined (reading 'imports')`. Run the build from
PowerShell, or `cd D:/...` with an upper-case drive letter.

## Where the content comes from

The site does not copy the project's documentation. Pages publish the
repository documents with VitePress includes:

| Page | Source |
|---|---|
| `guide/overview.md` | `README.md` |
| `browser/architecture.md` | `ARCHITECTURE.md` |
| `browser/upstream.md` | `UPSTREAM.md` |
| `privacy/index.md` | `PRIVACY.md` |
| `security/index.md` | `SECURITY.md` |
| `development/building.md` | `BUILD.md` |
| `development/change-categories.md` | `remilia/README.md` |
| `development/validation.md` | `tests/validation/README.md` |
| `development/contributing.md` | `CONTRIBUTING.md` |
| `project/roadmap.md` | `ROADMAP.md` |

To change one of these pages, edit the source document, not the page. The
"Edit this page on GitHub" link already points to the source.

Only `index.md` (home) and `project/license.md` are written for the site.

`.vitepress/repo-links.ts` adapts the included documents:

- links between published documents become links to their site pages;
- other relative links become GitHub links, and the build fails if the
  target file does not exist;
- the build fails if an include cannot be resolved (VitePress 1.x would
  otherwise leave it out silently);
- the `i18n:nav` language bar is removed; translations are not published.

To publish another repository document: add it to `publishedDocs` in
`repo-links.ts`, create its page with an include, add it to the sidebar in
`config.ts`, and add its path to `on.push.paths` in
`.github/workflows/docs.yml`. Check first that it is meant for the public:
nothing under `internal/` or `docs/research/` is ever published.

Pages written for the site use absolute links (`/privacy/`), which the plugin
never rewrites.

## Visual identity

- Palette and typography are set in `.vitepress/theme/custom.css` as CSS
  variables over the VitePress default theme. The site is always dark.
- Fonts are self-hosted, all under the SIL Open Font License: Cormorant
  Garamond (headings) and JetBrains Mono (code) from `@fontsource-variable`,
  and Inter (text), bundled with VitePress.
- `public/brand/` holds unmodified copies of the brand vectors: the wordmark
  (header and home), the mascot (home) and the bat symbol `remilia-hat.svg`
  (favicon and home divider). Replace them with new exports from the source
  files; do not edit them here.

## Publishing (GitHub Pages)

`.github/workflows/docs.yml` builds the site with `npm ci` from the lockfile
and deploys `docs/.vitepress/dist` on every push to `main` that touches the
site or a published document. It can also be run by hand from the Actions tab
(**Run workflow**).

One-time setup, in the repository on GitHub:

1. **Settings → Pages → Build and deployment → Source:** select
   **GitHub Actions**.
2. Push to `main`, or run the **Documentation site** workflow by hand.
3. The site appears at <https://ivuia.github.io/Remilia/>. The deployment URL
   is also shown on the workflow run and under **Environments →
   github-pages**.

The workflow needs no secrets. The build job can only read the repository;
only the deploy job can write to Pages.

## Known issue

`npm audit` reports an esbuild advisory (GHSA-67mh-4wv8-2f99) through Vite.
It affects only the development server (`docs:dev`), not the published site.
The only fix is VitePress 2, which is still in alpha.

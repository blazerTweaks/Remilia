// Lets site pages publish repository documents (README.md, PRIVACY.md, ...)
// with `<!--@include: ...-->` instead of copying them.
//
// VitePress 1.x inlines an included file as plain text, so its relative links
// end up resolved against the *including* page, and a missing include is left
// in the page silently. This plugin fixes both:
//
// - links between published documents become links to their site pages;
// - any other relative link becomes a GitHub link to the file in the
//   repository, and the build fails if that file does not exist;
// - the build fails if an `@include` was not resolved;
// - GitHub-only blocks of the source documents are removed: the
//   `<!-- i18n:nav -->` language bar (translations are not published) and the
//   `<!-- readme:logo -->` block (the site has the wordmark in its header).
//
// Relative links are read as relative to the repository root, which is where
// every published document with links lives. Site pages themselves must use
// absolute links (`/privacy/`), which this plugin never touches.

import fs from 'node:fs'
import path from 'node:path'
import type { MarkdownRenderer } from 'vitepress'

/** Repository documents published on the site: repository path → page in docs/. */
export const publishedDocs: Readonly<Record<string, string>> = {
  'README.md': 'guide/overview.md',
  'ARCHITECTURE.md': 'browser/architecture.md',
  'UPSTREAM.md': 'browser/upstream.md',
  'PRIVACY.md': 'privacy/index.md',
  'SECURITY.md': 'security/index.md',
  'BUILD.md': 'development/building.md',
  'remilia/README.md': 'development/change-categories.md',
  'tests/validation/README.md': 'development/validation.md',
  'CONTRIBUTING.md': 'development/contributing.md',
  'ROADMAP.md': 'project/roadmap.md',
}

/** Repository files that are not published verbatim but have their own page. */
const describedFiles: Readonly<Record<string, string>> = {
  'LICENSE': 'project/license.md',
}

/** The repository document a site page publishes, if any (page path relative to docs/). */
export function sourceOf(page: string): string | undefined {
  return Object.keys(publishedDocs).find((source) => publishedDocs[source] === page)
}

export interface RepoLinksOptions {
  /** Absolute path of the repository root. */
  repoRoot: string
  /** https://github.com/<owner>/<repo> */
  repoUrl: string
  /** Branch that GitHub links point to. */
  branch: string
}

/**
 * Blocks of the source documents that only make sense on GitHub: the language
 * bar (translations are not published) and the README logo (the site shows
 * the wordmark in its own header).
 */
const GITHUB_ONLY_BLOCKS: ReadonlyArray<readonly [open: string, close: string]> = [
  ['<!-- i18n:nav -->', '<!-- /i18n:nav -->'],
  ['<!-- readme:logo -->', '<!-- /readme:logo -->'],
]
const HAS_SCHEME = /^[a-z][a-z\d+.-]*:/i
const NOT_REPO_RELATIVE = /^(\/|#|\.\.?\/)/

function toRoute(page: string): string {
  return '/' + page.replace(/(^|\/)index\.md$/, '$1').replace(/\.md$/, '')
}

export function repoLinks(md: MarkdownRenderer, options: RepoLinksOptions): void {
  const routes = new Map(
    Object.entries({ ...publishedDocs, ...describedFiles }).map(([source, page]) => [
      source,
      toRoute(page),
    ]),
  )

  function rewrite(href: string, where: string): string {
    if (HAS_SCHEME.test(href) || NOT_REPO_RELATIVE.test(href)) return href

    const hashAt = href.indexOf('#')
    const file = hashAt < 0 ? href : href.slice(0, hashAt)
    const hash = hashAt < 0 ? '' : href.slice(hashAt)
    const target = path.posix.normalize(decodeURI(file))

    const route = routes.get(target)
    if (route) return route + hash

    const absolute = path.join(options.repoRoot, target)
    if (target.startsWith('..') || !fs.existsSync(absolute)) {
      throw new Error(
        `${where}: link "${href}" points to "${target}", which is not a file in the repository`,
      )
    }
    const kind = fs.statSync(absolute).isDirectory() ? 'tree' : 'blob'
    return `${options.repoUrl}/${kind}/${options.branch}/${target}${hash}`
  }

  md.core.ruler.push('remilia_repo_links', (state) => {
    const where = (state.env as { relativePath?: string })?.relativePath ?? 'a page'
    const tokens = state.tokens

    // The closing marker may share an HTML block with the markup before it, so
    // it is matched with `includes`.
    for (let i = 0; i < tokens.length; i++) {
      if (tokens[i].type !== 'html_block') continue
      const block = GITHUB_ONLY_BLOCKS.find(([open]) => tokens[i].content.trim() === open)
      if (!block) continue
      const [open, close] = block
      const end = tokens.findIndex(
        (t, j) => j > i && t.type === 'html_block' && t.content.includes(close),
      )
      if (end < 0) throw new Error(`${where}: "${open}" has no matching "${close}"`)
      tokens.splice(i, end - i + 1)
      i--
    }

    for (const token of tokens) {
      for (const t of [token, ...(token.children ?? [])]) {
        if (t.type.startsWith('html_') && t.content.includes('@include:')) {
          throw new Error(`${where}: unresolved include: ${t.content.trim()}`)
        }
        if (t.type !== 'link_open') continue
        const href = t.attrGet('href')
        if (href) t.attrSet('href', rewrite(href, where))
      }
    }
  })
}

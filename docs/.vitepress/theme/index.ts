import DefaultTheme from 'vitepress/theme'
import type { Theme } from 'vitepress'

// Self-hosted fonts (SIL Open Font License), bundled into the build output.
// Inter, the body font, already ships with the VitePress default theme.
import '@fontsource-variable/cormorant-garamond'
import '@fontsource-variable/jetbrains-mono'

import './custom.css'

export default {
  extends: DefaultTheme,
} satisfies Theme

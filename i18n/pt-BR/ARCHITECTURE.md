<!-- i18n:nav -->
[English](../../ARCHITECTURE.md) | **Português (Brasil)** | [日本語](../ja/ARCHITECTURE.md) | [Español](../es/ARCHITECTURE.md)
<!-- /i18n:nav -->

<!-- i18n:meta -->
> - **Translation status:** Current
> - **Language:** pt-BR
> - **Original language:** English
> - **Source:** [ARCHITECTURE.md](../../ARCHITECTURE.md)
> - **Source revision:** sha256:7871350590894ef0f326a9e435b9da5c25f9ca493007087c61f04062da58faf9
<!-- /i18n:meta -->

# REMILIA Browser — Arquitetura

Codinome do projeto: **SCARLET**
Status: Fase 2 (base do navegador) — pipeline de build em andamento; nenhuma mudança do REMILIA aplicada ainda.
Última revisão: 2026-11-25

Este documento registra *a partir do que o REMILIA é construído, como as
camadas se encaixam e por quê*.

---

## 1. Resumo

O REMILIA é uma **build derivada (downstream) do Firefox (Gecko)**, construída
sobre **o conjunto de patches e a configuração de privacidade do LibreWolf**,
com uma camada fina, mantida separadamente, de patches, configurações e
branding do REMILIA.

O REMILIA **não** contém um motor de navegador próprio, não encapsula uma
WebView e não é um aplicativo Electron. Toda página é renderizada pelo Gecko,
toda requisição passa pelo Necko (a pilha de rede do Firefox) e todo processo de
conteúdo roda dentro da sandbox do Firefox para Windows.

```
┌───────────────────────────────────────────────────────────────┐
│ Layer 4  REMILIA branding & assets                            │
│          icons, wordmark, about pages, installer art, theme   │
├───────────────────────────────────────────────────────────────┤
│ Layer 3  REMILIA build-fixes, security, privacy               │
│          one directory per category: patches, prefs,          │
│          policies, mozconfig; applied/reverted separately     │
├───────────────────────────────────────────────────────────────┤
│ Layer 2  LibreWolf (pinned commit of librewolf/source)        │
│          68 patches, librewolf.cfg, policies, uBO assets      │
├───────────────────────────────────────────────────────────────┤
│ Layer 1  Upstream Firefox release source tarball              │
│          GPG-verified against Mozilla's release key           │
└───────────────────────────────────────────────────────────────┘
```

Cada camada é aplicada **em ordem, por script, sobre uma árvore limpa**. Nada
nas camadas 1 ou 2 é editado à mão dentro deste repositório. É isso que torna
barato absorver as versões de segurança do upstream (veja
[UPSTREAM.md](UPSTREAM.md)).

---

## 2. Escolha da base

### 2.1 Opções consideradas

| Opção | Veredito | Motivo |
|---|---|---|
| Escrever um motor | Rejeitada | Inviável; explicitamente proibido pelas regras do projeto. |
| Chromium / CEF / Electron | Rejeitada | O objetivo do projeto é um navegador Gecko; uma base Chromium perderia a compatibilidade com extensões do Firefox, a Proteção Total de Cookies e o RFP, e não oferece nenhum benefício documentado para esses objetivos. |
| Fork direto do Firefox (mozilla-firefox/firefox) | Rejeitada como base principal | Exigiria refazer tudo o que o LibreWolf já mantém (remoção de telemetria, 68 patches, configurações). Mantido como o *upstream do upstream*. |
| **Fork do LibreWolf via git fork de `librewolf/source`** | Rejeitada | Conflitos de merge a cada versão de 4 semanas; as mudanças do REMILIA ficariam intercaladas com o histórico do LibreWolf, tornando a procedência confusa. |
| **Camada sobre um commit fixado do LibreWolf** | **Escolhida** | A própria build do LibreWolf já funciona como "tarball verificado do Firefox + lista ordenada de patches + arquivos copiados". O REMILIA repete o mesmo padrão um nível acima. Separação clara em 4 camadas, diffs pequenos, rebase fácil. |
| Firefox ESR em vez do Release | Rejeitada por enquanto | O LibreWolf acompanha o Release; seguir o ESR significaria abrir mão da manutenção do LibreWolf. Reavaliar se a capacidade dos mantenedores do REMILIA não sustentar o ciclo de 4 semanas (veja §8). |

Registro de decisão: ADR-0001.

### 2.2 O que o LibreWolf realmente é (verificado em 2026-11-25)

Fonte: `https://codeberg.org/librewolf/source`, `main` no commit
`ed92167b4c56` (Makefile `VERSION = 161.0`, `RELEASE = 1`). A tag de release
`161.0-1` é o commit `e2baf3254fc7`; o REMILIA fixa a tag, não a `main`.

- **Entrada da build:** `firefox-<ver>.source.tar.xz` de `archive.mozilla.org`,
  verificado com `gpg --verify` contra `assets/MOZILLA_PUBKEY.asc`.
- **`scripts/patch.sh`**, em seguida, dentro da árvore extraída:
  - copia `assets/mozconfig.new` → `mozconfig`;
  - copia o branding (`themes/browser/branding/librewolf`), a configuração de
    busca, a página `about:librewolf` e **as chaves públicas de assinatura de
    atualizações MAR do LibreWolf** para
    `toolkit/mozapps/update/updater/release_{primary,secondary}.der`;
  - copia `settings/librewolf.cfg`, `settings/distribution/policies.json`,
    `settings/defaults/pref/local-settings.js` para `lw/`;
  - aplica cada patch de `assets/patches.txt` em ordem (`patch -p1`);
  - remove o backend de ML da OpenAI, força todos os pings do Glean a seguirem a
    preferência de envio de dados e reescreve "Firefox" em
    `appstrings.properties`;
  - baixa a l10n do Firefox e sobrepõe as strings do LibreWolf.
- **Configurações:** `librewolf.cfg` (~1000 linhas, AutoConfig, `lockPref`/`pref`/
  `defaultPref`) carregado via `general.config.filename` com a sandbox do
  AutoConfig ativada; `policies.json` (políticas corporativas).
- **uBlock Origin:** *não* é incluído como arquivo. `policies.json` →
  `ExtensionSettings["uBlock0@raymondhill.net"]` com
  `installation_mode: normal_installed` e uma `install_url` da AMO; o uBO é
  baixado de addons.mozilla.org na primeira execução. Um patch no Gecko
  (`custom-ubo-assets-bootstrap-location.patch`) injeta
  `adminSettings.assetsBootstrapLocation` no armazenamento gerenciado do uBO
  para que a seleção padrão de listas do uBO venha do `uBOAssets.json` do
  LibreWolf.
- **As builds para Windows** são produzidas pelo `bsys6` por **compilação
  cruzada no Debian, em Docker** (clang, alvos MSVC do Rust, o Windows SDK
  baixado pelo `get_vs.py` da Mozilla, Wine para `widl`, `fxc2`, NSIS). O README
  do LibreWolf afirma que builds *nativas* no Windows "não são muito bem
  testadas".
- **Atualizações:** o bsys6 gera arquivos `.mar` assinados e um `update.xml`; a
  árvore do LibreWolf aponta `MOZ_APPUPDATE_HOST` para `update.librewolf.net`.

---

## 3. Estrutura do repositório (alvo)

```
REMILIA/
├── upstream/               # category "upstream": pins.env (Firefox, LibreWolf,
│                           #   l10n, bsys6, base image, Rust); LibreWolf exclusions
├── remilia/                # REMILIA changes, one directory per category
│   ├── build-fixes/        # compile-only fixes, no behaviour change (layer 3)
│   ├── security/           # sandbox, certificates, signing, updates (layer 3)
│   ├── privacy/            # tracking, fingerprinting, cookies, DNS, telemetry,
│   │                       #   uBlock Origin (layer 3)
│   └── branding/           # logos, icons, colours, theme, names, UI (layer 4)
│       # each category holds only what it needs:
│       #   patches/ + series, prefs.cfg, policies.json, mozconfig, files/
├── build/                  # build-environment image (windows-cross.Dockerfile)
├── scripts/                # fetch, prepare, toolchains, build, package, docker
├── i18n/                   # documentation translations
├── tests/                  # validation checklists and recorded results
└── *.md                    # this documentation set
```

`remilia/` e `tests/` ainda não existem. Eles são criados quando recebem
conteúdo real pela primeira vez (Fase 3a e validação da Fase 2,
respectivamente) — nada de estrutura vazia. As regras das categorias estão na
§10.

---

## 4. Pipeline de build

```
fetch   → firefox-161.0.source.tar.xz (+ .asc)      gpg --verify (Mozilla key)
        → librewolf/source @ <pinned commit>         git, commit hash checked
prepare → LibreWolf patch.sh on a pristine copy       = layer 2 applied
        → REMILIA patch series + file overlays        = layers 3 + 4 applied
build   → ./mach build   (mozconfig: LW base + REMILIA overrides)
package → ./mach package → zip → NSIS installer, .mar update files
```

### 4.1 Host de build para Windows

Dois caminhos, ambos legítimos; veja [BUILD.md](BUILD.md):

1. **Caminho de release / reprodutível — compilação cruzada em Linux com
   Docker.** É o mesmo método que o LibreWolf usa para os binários Windows que
   publica, portanto é o caminho contra o qual os patches do LibreWolf são de
   fato testados. Roda nesta máquina via Docker Desktop (backend WSL2).
2. **Caminho de desenvolvimento — Windows nativo com MozillaBuild.** O método
   documentado e suportado pela Mozilla. Melhor para depuração (WinDbg,
   `mach build faster`, alterações incrementais no front-end). Os scripts de
   shell do LibreWolf precisam das ferramentas GNU que o MozillaBuild inclui.

A Fase 2 vai validar os dois e registrar qual deles é o oficial para releases.
Expectativa: compilação cruzada com Docker para releases, nativa para iteração.

---

## 5. Arquitetura de privacidade

A privacidade é implementada com **os mecanismos nativos do Firefox**,
configurados, nunca reimplementados:

| Aspecto | Mecanismo (nativo) |
|---|---|
| Rastreamento entre sites | ETP **Rigoroso** (`browser.contentblocking.category=strict`): Proteção Total de Cookies (dFPI), listas rigorosas de rastreadores, shims do SmartBlock, remoção de parâmetros de consulta |
| Fingerprinting | `privacy.resistFingerprinting` (RFP) — o mesmo mecanismo usado pelo Tor Browser e pelo Mullvad Browser |
| Telemetria | Desativada **em tempo de compilação** (`MOZ_TELEMETRY_REPORTING` vazio, relator de falhas não compilado, pings do Glean seguem a preferência de envio de dados) e por política |
| Bloqueio de conteúdo | uBlock Origin (sem modificações, assinado pela AMO) |
| DNS | TRR do Firefox (DoH) — desativado por padrão, provedores selecionáveis |
| Transporte | Modo Somente HTTPS ativado, CRLite obrigatório, 0-RTT desativado |

A avaliação completa de cada configuração, incluindo os pontos em que o REMILIA
**diverge** deliberadamente do LibreWolf, está em [PRIVACY.md](PRIVACY.md). As
diferenças relevantes para a segurança estão em [SECURITY.md](SECURITY.md).

---

## 6. Arquitetura de bloqueio de anúncios

- **Motor:** uBlock Origin, sem modificações, a build assinada pela AMO. O
  REMILIA nunca faz fork nem reempacota o código do uBO, então o motor de
  filtragem, o popup com contagens reais de requisições por site e o painel de
  controle são todos do próprio uBO.
- **Distribuição:** o `.xpi` assinado (versão fixada + SHA-256) é colocado em
  `distribution/extensions/` do aplicativo, de modo que esteja presente
  **offline na primeira execução**, *e* listado em `policies.json`
  `ExtensionSettings`, para que o Firefox o mantenha atualizado pelo canal
  normal de atualizações assinadas da AMO. A verificação de assinatura continua
  obrigatória.
- **Listas padrão:** definidas por meio do mecanismo suportado pelo uBO,
  `adminSettings.assetsBootstrapLocation` → um `assets.json` do REMILIA.
  Isso define apenas os *padrões da primeira instalação*; o usuário mantém
  controle total. **Não** `toOverwrite.filterLists`: o `restoreAdminSettings()`
  do uBO reaplica isso a cada inicialização (verificado em `src/js/storage.js`),
  o que desfaria silenciosamente as escolhas do usuário.
- **Brasil:** o catálogo padrão do uBO não tem atualmente nenhuma lista
  dedicada ao Brasil; a lista regional que cobre pt-BR é `spa-1` (AdGuard
  Spanish/Portuguese). O uBO ativa listas regionais automaticamente a partir de
  `navigator.language`, mas o RFP falsifica esse valor como `en-US`, então o
  REMILIA precisa ativar `spa-1` explicitamente no seu manifesto de assets.
  Listas comunitárias brasileiras adicionais serão avaliadas na Fase 5.
- **Popup:** a Fase 5 decide entre (a) usar o próprio popup do uBO como painel
  de "proteção" da barra de ferramentas, ou (b) um painel do REMILIA que lê
  apenas os dados expostos pelo uBO. Regra: nenhuma estatística é exibida se não
  tiver sido produzida pelo bloqueador. O painel de ETP do próprio Firefox já
  informa contagens reais de rastreadores por site e permanece.

Registro de decisão: ADR-0003.

---

## 7. Atualizações

O REMILIA usa **o próprio atualizador da Mozilla** (arquivos MAR +
`update.xml`), o mesmo mecanismo que o LibreWolf usa hoje, com **identidade
própria do REMILIA**:

- Par de chaves de assinatura MAR do REMILIA; as chaves públicas substituem as
  do LibreWolf em `release_primary.der` / `release_secondary.der`. **Compilar a
  árvore do LibreWolf sem modificações faria o REMILIA aceitar atualizações
  assinadas pelo LibreWolf e consultar `update.librewolf.net` — isso precisa ser
  substituído antes de qualquer build pública.**
- `MOZ_APPUPDATE_HOST` → um host controlado pelo REMILIA (domínio ainda não
  escolhido — veja os bloqueios no ROADMAP).
- As atualizações nunca mexem no diretório do perfil; os dados do usuário são
  migrados apenas pelo código de migração de perfil do próprio Firefox.

As listas de filtros são atualizadas pelo uBO; o próprio uBO é atualizado pela
AMO.

---

## 8. Modelo de manutenção

O Firefox lança uma versão principal a cada **4 semanas**, além de versões
pontuais de segurança não programadas ("chemspill"). O LibreWolf normalmente
acompanha em poucos dias. A latência do REMILIA até os usuários = latência do
LibreWolf + rebase do REMILIA + build + publicação.

Requisitos realistas:

- **Por versão:** atualizar os pins, reaplicar a série de patches, corrigir
  rejeições, build completa (≈1,5–3 h em um Ryzen 5 3600 de 6 núcleos para uma
  build otimizada, a ser medido na Fase 2), testes de fumaça, assinatura,
  publicação.
- **Meta:** versões de segurança publicadas em até **72 horas** após as do
  LibreWolf. Se isso não puder ser cumprido de forma confiável, os usuários
  devem ser avisados claramente; um navegador de privacidade desatualizado é um
  risco de segurança.
- **Orçamento de patches:** manter os patches de código-fonte do REMILIA poucos
  e pequenos. Preferir prefs, políticas e sobreposição de arquivos a diffs em
  C++/JS. Todo patch tem um cabeçalho informando propósito, camada e se pode ser
  enviado ao upstream.

Detalhes: [UPSTREAM.md](UPSTREAM.md).

---

## 9. Não objetivos explícitos

- Nenhum código próprio de renderização, rede, criptografia ou sandbox.
- Nenhuma "randomização" própria de fingerprinting que tornaria os usuários do
  REMILIA uma população pequena e distinguível.
- Nenhum framework de frontend ou bundler (nada de React, nada de Vite). As
  mudanças na interface do navegador são feitas no próprio front-end do Firefox
  em XHTML/CSS/JS/Fluent.
- Nenhuma alegação de anonimato.

---

## 10. Categorias de mudança

Toda mudança do REMILIA pertence a exatamente uma categoria. As categorias são
isoladas para que cada uma possa ser revisada, depurada, revertida e
ressincronizada com o upstream de forma independente
(ADR-0004).

| Categoria | Abrange | Local |
|---|---|---|
| Upstream | Firefox e LibreWolf, sem modificações; pins; patches do LibreWolf que o REMILIA exclui | `upstream/` |
| Correções de build | Mudanças necessárias apenas para compilar; nenhuma mudança de comportamento | `remilia/build-fixes/` |
| Segurança | Sandbox, certificados, validação HTTPS, assinaturas, proteção de processos, atualizações | `remilia/security/` |
| Privacidade | Proteção contra rastreamento, fingerprinting, cookies, DNS, telemetria, bloqueio de conteúdo (uBlock Origin) | `remilia/privacy/` |
| Branding | Logos, ícones, cores, tema, nomes, identidade visual da interface | `remilia/branding/` |

Regras:

- Um patch, bloco de prefs, arquivo de políticas ou fragmento de mozconfig
  pertence a uma única categoria. Uma mudança que afeta duas categorias é
  dividida em duas.
- A classificação segue o efeito. Interface que só muda a aparência é branding;
  interface que muda o comportamento pertence à categoria desse comportamento
  (um controle de configuração de DoH é privacidade).
- O Firefox lê um único arquivo AutoConfig, um único
  `distribution/policies.json` e um único `mozconfig`. O `prepare.sh` os monta a
  partir dos fragmentos de cada categoria, com um cabeçalho por categoria, e
  falha se duas categorias definirem a mesma pref ou política.
- Ordem fixa de aplicação: build-fixes → security → privacy → branding.
  Qualquer subconjunto pode ser aplicado, de modo que cada categoria pode ser
  compilada e validada sozinha, e uma regressão pode ser isolada por bisseção
  até uma categoria.
- O cabeçalho de todo patch registra: categoria, propósito, arquivos e prefs
  afetados, se pode ser enviado ao upstream e o que muda ao revertê-lo.

A montagem e a seleção de subconjuntos no `prepare.sh` são trabalho da Fase 3a;
hoje o `prepare.sh` não aplica nenhuma camada do REMILIA.

---

## 11. Portões de validação

Uma compilação bem-sucedida prova que a infraestrutura de build funciona. Ela
não torna o navegador utilizável. Nenhuma build é descrita como funcional até
passar pelo checklist de validação do [ROADMAP.md](ROADMAP.md) (Fase 2, etapa
3), com os resultados registrados em `tests/results/`
(ADR-0005). Cada
categoria introduzida depois repete o checklist duas vezes: com essa categoria
sozinha e com todas as categorias aplicadas.

<!-- i18n:nav -->
[English](../../UPSTREAM.md) | **Português (Brasil)** | [日本語](../ja/UPSTREAM.md) | [Español](../es/UPSTREAM.md)
<!-- /i18n:nav -->

<!-- i18n:meta -->
> - **Translation status:** Current
> - **Language:** pt-BR
> - **Original language:** English
> - **Source:** [UPSTREAM.md](../../UPSTREAM.md)
> - **Source revision:** sha256:78b60c4f52a5aa358b5bae55549602fb82f0f7cdead29794fe77201d14c5e91b
<!-- /i18n:meta -->

# Sincronização com o upstream

O Remilia é derivado de dois projetos. Manter-se atualizado em relação a eles é
a tarefa contínua de manutenção mais importante, porque quase todas as
correções de segurança chegam pelo upstream.

## Camadas

| Camada | Origem | Fixada em | O Remilia a edita? |
|---|---|---|---|
| 1. Firefox | `archive.mozilla.org/pub/firefox/releases/<ver>/source/` (tarball assinado com GPG). Repositório canônico: `github.com/mozilla-firefox/firefox` | `upstream/pins.env` → `FIREFOX_VERSION` | Nunca diretamente; apenas por patches da camada 3 |
| 2. LibreWolf | `codeberg.org/librewolf/source` (patches, configurações, scripts de build) | `upstream/pins.env` → `LIBREWOLF_COMMIT` | Nunca; o Remilia sobrepõe por cima |
| 3. Correções de build, segurança e privacidade do Remilia | `remilia/build-fixes/`, `remilia/security/`, `remilia/privacy/` (uma categoria cada, ARCHITECTURE.md §10) | — | Sim |
| 4. Branding do Remilia | `remilia/branding/` | — | Sim |

## Ciclos de lançamento a acompanhar

- Firefox: versão principal a cada 4 semanas; versões pontuais para problemas de
  segurança, às vezes não programadas ("chemspills"). Avisos:
  mozilla.org/security/advisories/.
- LibreWolf: tags `<firefox-version>-<lw-release>` (por exemplo, `161.0-1`),
  geralmente poucos dias depois do Firefox.
- uBlock Origin: independente; atualizado pela AMO, sem vínculo com as versões
  do Remilia.

## Procedimento de atualização

1. Aparece uma nova tag do LibreWolf para uma nova versão do Firefox.
2. Atualize `upstream/pins.env`: `FIREFOX_VERSION`, `LIBREWOLF_COMMIT`, `LIBREWOLF_TAG`.
3. `./scripts/fetch.sh`, que verifica a assinatura GPG da Mozilla e o hash do commit.
4. `./scripts/prepare.sh`. Ele se recusa a aplicar as categorias do Remilia
   enquanto `upstream/librewolf-base/` for diferente dos novos arquivos do
   LibreWolf. Se um patch do Remilia não se aplicar:
   - atualize-o contra a nova árvore;
   - se o código que ele altera mudou de significado, revise o cabeçalho de
     propósito do patch e refaça-o. Não force a aplicação.
5. Atualize o snapshot da base do LibreWolf com
   `scripts/remilia_layers.py snapshot` e revise o diff: `librewolf.cfg`,
   `policies.json`, `mozconfig` e `patches.txt`. Revise cada pref alterada à luz
   de PRIVACY.md e SECURITY.md, porque as sobreposições do Remilia agora podem
   conflitar com o upstream ou duplicá-lo. Depois rode
   `python scripts/remilia_layers.py check`.
6. Verificações de árvore (`./scripts/docker.sh verify`); depois compile,
   execute o checklist de validação, empacote, assine, publique.
7. As notas de versão listam os avisos MFSA incluídos.

## Regras para patches do Remilia

- Uma preocupação e uma categoria por patch (ARCHITECTURE.md §10). Um
  cabeçalho informa: categoria, propósito, prefs/arquivos afetados, se poderia
  ser enviado ao LibreWolf ou à Mozilla e o que muda ao revertê-lo. O formato
  exato está em `remilia/README.md`.
- Prefira, nesta ordem: pref no `prefs.cfg` da categoria → política no
  `policies.json` dela → sobreposição de arquivo (cópia) → patch de
  código-fonte. Patches de código são o último recurso.
- Não modifique patches do LibreWolf. Se um deles for indesejado, exclua-o por
  meio de `upstream/librewolf-exclude.txt`, uma linha por patch: o caminho como
  está no `patches.txt` do LibreWolf, seguido do motivo. O motivo é obrigatório
  e público, porque é copiado para o `REMILIA-PROVENANCE.txt`: de 10 a 200
  caracteres, sem vírgulas, sem caracteres de controle e sem referências a
  documentos internos. O `scripts/remilia_layers.py` verifica o caminho, se ele
  aparece exatamente uma vez no `patches.txt`, e o motivo; uma linha no formato
  antigo, com um identificador de decisão no lugar do motivo, é recusada. A
  lista está vazia para o LibreWolf 161.0-1.
- Correções que não são específicas do Remilia são propostas primeiro ao
  upstream.

## Rebranding de uma árvore do LibreWolf: pontos de contato

Inventário da árvore preparada do LibreWolf 161.0-1, feito na Fase 3a. Ele
encontrou 4018 linhas que contêm "librewolf"; a lista completa, linha a linha,
não é publicada. 3605 delas são as próprias sobreposições de strings de interface do LibreWolf
em `lw/l10n/` (504 arquivos).

O que o inventário cobre: cada linha de arquivo de texto da árvore preparada
(sem o diretório de objetos) que contém "librewolf", em qualquer caixa. O que
ele não cobre:

- arquivos binários linha a linha (ícones e bitmaps são listados por diretório);
- identidade que não contém essa palavra, como strings "Firefox" restantes ou
  URLs da Mozilla;
- padrões de prefs definidos fora do `librewolf.cfg`, como `browser/app/profile/firefox.js`,
  `modules/libpref/init/all.js`, `modules/libpref/init/StaticPrefList.yaml`
  e `browser/branding/librewolf/pref/firefox-branding.js`. As verificações das
  categorias também não detectam sobrescritas desses valores (`remilia/README.md`,
  "What the checks cover"). Isso é trabalho pendente para as Fases 3b, 4a e 4b.

A Fase 3b muda para Remilia a identidade que o usuário vê: nome, ícones,
interface, executáveis e perfil. Os nomes internos ficam: o diretório `lw/`, o
nome de arquivo `librewolf.cfg` e o namespace de prefs `librewolf.*`.
Renomeá-los faria a segurança e a privacidade dependerem do branding.

| Ponto de contato | Onde | Categoria | Fase |
|---|---|---|---|
| Nome do aplicativo, diretório de branding, nome de remoting | `mozconfig` linhas 21, 23, 30; `browser/branding/librewolf/configure.sh` linhas 8–11; padrões de vendor e nome do aplicativo em `toolkit/moz.configure` linhas 23, 37 | Branding (desvios de `mozconfig`) | 3b |
| ID de distribuição `net.librewolf` | `mozconfig` linha 22 | Branding | 3b, depende de B1 |
| Diretório de branding: ícones (`.ico`, `.png`, `.icns`, `.bmp`), wordmark, `brand.ftl`, `brand.dtd`, `brand.properties`, `branding.nsi` | `browser/branding/librewolf/` (42 entradas, copiadas pelo `patch.sh` de `themes/` do LibreWolf) | Branding: um novo diretório de branding do Remilia; o do LibreWolf não é editado | 3b |
| Manifesto do executável | `browser/app/librewolf.exe.manifest` linhas 6, 9 | Branding | 3b |
| Nomes dos diretórios de perfil e de dados | `toolkit/xre/nsXREDirProvider.cpp` linhas 337, 430, 432, 1010, 1307, 1317 (`profile-directory.patch`, `mozilla-dirs.patch`); pasta de backup `browser/components/backup/BackupService.sys.mjs` linha 661 | Branding | 3b |
| Arquivo de sobreposições do usuário `librewolf.overrides.cfg` (no Windows, lido de `%USERPROFILE%\.librewolf\`) | `extensions/pref/autoconfig/src/prefcalls.js` linhas 25–54 | Segurança: o Remilia o lê de `%USERPROFILE%\.remilia\`, com o mesmo nome de arquivo (SECURITY.md, S5) | 3b, feito (`static-verified`) |
| Janela "Sobre" e página `about:librewolf` | `browser/base/content/aboutDialog.xhtml` linhas 38, 44, 45; `toolkit/content/librewolf.html`; `toolkit/locales/en-US/toolkit/about/aboutLibreWolf.ftl`; `docshell/build/components.conf` linha 18 | Branding (texto visível); o endereço `about:` é uma decisão em aberto da 3b | 3b |
| Painel de configurações | `browser/components/preferences/librewolf.js`, `librewolf.inc.xhtml`; `browser/locales/en-US/browser/preferences/preferences.ftl` (46 linhas) | Branding para nomes e ícones; o comportamento de cada controle fica na sua própria categoria | 3b |
| Strings fixas | `appstrings.properties` (reescrito pelo `patch.sh`, 12 linhas); `dom/locales/en-US/chrome/appstrings.properties`; sobreposições em `lw/l10n/` (1545 linhas com o nome visível) | Branding | 3b |
| Logo das ferramentas de desenvolvedor | `devtools/client/aboutdebugging/src/actions/runtimes.js` linha 74 (`lw-logo-devtools.patch`) | Branding | 3b |
| Links de suporte e de notas de versão | `lw/librewolf.cfg` linhas 582–586 e 648 (`app.update.url.*`, `app.releaseNotesURL*`, `app.support.baseURL`); `lw/policies.json` linhas 93–94 (`SupportMenu`) e 60 (mensagem sobre pacotes de idioma) | Branding (desvios de pref e de política) | 3b, depende de B1 |
| Host de atualização e chaves MAR | `build/moz.build` linha 95 (`MOZ_APPUPDATE_HOST`); `release_primary.der`, `release_secondary.der` copiados pelo `patch.sh` | Segurança, não branding: decidem quais atualizações o navegador aceita | 4a, depende de B1, B2 |
| Local da lista de assets do uBlock Origin | `lw/librewolf.cfg` linhas 996–999 (`librewolf.uBO.assetsBootstrapLocation`) | Privacidade | 4b |
| Verificação de versão no servidor do LibreWolf (desligada por padrão) | `browser/base/content/aboutDialog.js` linhas 42–72 | Privacidade (requisição de rede); continua desligada | 4b |
| Mecanismos de busca | `services/settings/dumps/main/search-config-v2.json` (copiado pelo `patch.sh`) | Privacidade (D1) | 4b |
| Nomes no instalador do Windows | `browser/branding/librewolf/branding.nsi` linhas 11–13 | Branding | 8 |
| Nomes internos mantidos | Prefs `librewolf.*` (`modules/libpref/init/StaticPrefList.yaml` linhas 12433–12446 e cerca de 40 pontos no código); `lw/` e `librewolf.cfg` (`browser/installer/package-manifest.in` linha 279, `lw/local-settings.js`) | Nenhuma: mantidos de propósito | — |

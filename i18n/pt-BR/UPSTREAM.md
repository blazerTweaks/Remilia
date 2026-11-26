<!-- i18n:nav -->
[English](../../UPSTREAM.md) | **Português (Brasil)** | [日本語](../ja/UPSTREAM.md) | [Español](../es/UPSTREAM.md)
<!-- /i18n:nav -->

<!-- i18n:meta -->
> - **Translation status:** Current
> - **Language:** pt-BR
> - **Original language:** English
> - **Source:** [UPSTREAM.md](../../UPSTREAM.md)
> - **Source revision:** sha256:71c41dc82b06b164ca0c1f15cf5c5277437d0719e2cc5866c7e3c4ecfebdbf49
<!-- /i18n:meta -->

# Sincronização com o upstream

O REMILIA é derivado de dois projetos. Manter-se atualizado em relação a eles é
a tarefa contínua de manutenção mais importante, porque quase todas as
correções de segurança chegam pelo upstream.

## Camadas

| Camada | Origem | Fixada em | O REMILIA a edita? |
|---|---|---|---|
| 1. Firefox | `archive.mozilla.org/pub/firefox/releases/<ver>/source/` (tarball assinado com GPG). Repositório canônico: `github.com/mozilla-firefox/firefox` | `upstream/pins.env` → `FIREFOX_VERSION` | Nunca diretamente; apenas por patches da camada 3 |
| 2. LibreWolf | `codeberg.org/librewolf/source` (patches, configurações, scripts de build) | `upstream/pins.env` → `LIBREWOLF_COMMIT` | Nunca; o REMILIA sobrepõe por cima |
| 3. Correções de build, segurança e privacidade do REMILIA | `remilia/build-fixes/`, `remilia/security/`, `remilia/privacy/` (uma categoria cada, ARCHITECTURE.md §10) | — | Sim |
| 4. Branding do REMILIA | `remilia/branding/` | — | Sim |

## Ciclos de lançamento a acompanhar

- Firefox: versão principal a cada 4 semanas; versões pontuais para problemas de
  segurança, às vezes não programadas ("chemspills"). Avisos:
  mozilla.org/security/advisories/.
- LibreWolf: tags `<firefox-version>-<lw-release>` (por exemplo, `161.0-1`),
  geralmente poucos dias depois do Firefox.
- uBlock Origin: independente; atualizado pela AMO, sem vínculo com as versões
  do REMILIA.

## Procedimento de atualização *(os scripts chegam na Fase 2)*

1. Aparece uma nova tag do LibreWolf para uma nova versão do Firefox.
2. Atualize `upstream/pins.env`: `FIREFOX_VERSION`, `LIBREWOLF_COMMIT`, `LIBREWOLF_TAG`.
3. `./scripts/fetch.sh`, que verifica a assinatura GPG da Mozilla e o hash do commit.
4. `./scripts/prepare.sh`. Se um patch do REMILIA não se aplicar:
   - atualize-o contra a nova árvore;
   - se o código que ele altera mudou de significado, revise o cabeçalho de
     propósito do patch e refaça-o. Não force a aplicação.
5. Compare `librewolf.cfg` e `policies.json` entre o commit antigo e o novo do
   LibreWolf. Revise cada pref alterada à luz de PRIVACY.md e SECURITY.md,
   porque as sobreposições do REMILIA agora podem conflitar com o upstream ou
   duplicá-lo.
6. Compile, execute a checklist de testes de fumaça (`tests/`), empacote,
   assine, publique.
7. As notas de versão listam os avisos MFSA incluídos.

## Regras para patches do REMILIA

- Uma preocupação e uma categoria por patch (ARCHITECTURE.md §10). Um
  cabeçalho informa: categoria, propósito, prefs/arquivos afetados, se poderia
  ser enviado ao LibreWolf ou à Mozilla e o que muda ao revertê-lo.
- Prefira, nesta ordem: pref no `prefs.cfg` da categoria → política no
  `policies.json` dela → sobreposição de arquivo (cópia) → patch de
  código-fonte. Patches de código são o último recurso.
- Não modifique patches do LibreWolf. Se um deles for indesejado, exclua-o pela
  lista de exclusões em `upstream/` (Fase 3a), com um ADR.
- Correções que não são específicas do REMILIA são propostas primeiro ao
  upstream.

## Rebranding de uma árvore do LibreWolf: pontos de contato conhecidos

O LibreWolf fixa sua identidade no código em vários lugares que o REMILIA
precisa sobrepor. Inventário a ser concluído na Fase 3:

- `mozconfig`: `--with-app-name`, `--with-distribution-id`, `--with-branding`,
  `MOZ_APP_REMOTINGNAME`.
- Diretório `lw/` e nome de arquivo `librewolf.cfg` (`lw-dir.patch`, `local-settings.js`).
- Nome do diretório de perfil (`profile-directory.patch`, `mozilla-dirs.patch`).
- Página `about:librewolf` e painel de preferências (`about-librewolf.patch`, `pref-pane/`).
- Namespace de prefs `librewolf.*` (por exemplo, `librewolf.uBO.assetsBootstrapLocation`).
- Atualizador: `MOZ_APPUPDATE_HOST`, `release_primary.der`, `release_secondary.der`.
- Strings: reescrita de `appstrings.properties` e sobreposições de l10n.
- `policies.json` `SupportMenu`, `app.update.url.*`, `app.releaseNotesURL*`.

<!-- i18n:nav -->
[English](../../UPSTREAM.md) | [Português (Brasil)](../pt-BR/UPSTREAM.md) | [日本語](../ja/UPSTREAM.md) | **Español**
<!-- /i18n:nav -->

<!-- i18n:meta -->
> - **Translation status:** Current
> - **Language:** es
> - **Original language:** English
> - **Source:** [UPSTREAM.md](../../UPSTREAM.md)
> - **Source revision:** sha256:71c41dc82b06b164ca0c1f15cf5c5277437d0719e2cc5866c7e3c4ecfebdbf49
<!-- /i18n:meta -->

# Sincronización con el upstream

REMILIA deriva de dos proyectos. Mantenerse al día con ellos es la tarea de
mantenimiento continua más importante, porque casi todas las correcciones de
seguridad llegan desde el upstream.

## Capas

| Capa | Origen | Fijada en | ¿La edita REMILIA? |
|---|---|---|---|
| 1. Firefox | `archive.mozilla.org/pub/firefox/releases/<ver>/source/` (tarball firmado con GPG). Repositorio canónico: `github.com/mozilla-firefox/firefox` | `upstream/pins.env` → `FIREFOX_VERSION` | Nunca directamente; solo mediante parches de la capa 3 |
| 2. LibreWolf | `codeberg.org/librewolf/source` (parches, ajustes, scripts de compilación) | `upstream/pins.env` → `LIBREWOLF_COMMIT` | Nunca; REMILIA superpone sus cambios encima |
| 3. Correcciones de compilación, seguridad y privacidad de REMILIA | `remilia/build-fixes/`, `remilia/security/`, `remilia/privacy/` (una categoría cada uno, ARCHITECTURE.md §10) | — | Sí |
| 4. Imagen de marca de REMILIA | `remilia/branding/` | — | Sí |

## Ciclos de publicación que hay que seguir

- Firefox: versión principal cada 4 semanas; versiones puntuales para problemas
  de seguridad, a veces no programadas ("chemspills"). Avisos:
  mozilla.org/security/advisories/.
- LibreWolf: etiquetas `<firefox-version>-<lw-release>` (por ejemplo, `161.0-1`),
  normalmente pocos días después de Firefox.
- uBlock Origin: independiente; se actualiza a través de AMO, sin relación con
  las versiones de REMILIA.

## Procedimiento de actualización *(los scripts llegan en la Fase 2)*

1. Aparece una nueva etiqueta de LibreWolf para una nueva versión de Firefox.
2. Actualiza `upstream/pins.env`: `FIREFOX_VERSION`, `LIBREWOLF_COMMIT`, `LIBREWOLF_TAG`.
3. `./scripts/fetch.sh`, que verifica la firma GPG de Mozilla y el hash del commit.
4. `./scripts/prepare.sh`. Si un parche de REMILIA no se aplica:
   - actualízalo contra el nuevo árbol;
   - si el código que modifica ha cambiado de significado, revisa la cabecera de
     propósito del parche y vuelve a elaborarlo. No lo fuerces.
5. Compara `librewolf.cfg` y `policies.json` entre el commit antiguo y el nuevo
   de LibreWolf. Revisa cada pref modificada a la luz de PRIVACY.md y
   SECURITY.md, porque las superposiciones de REMILIA podrían ahora entrar en
   conflicto con el upstream o duplicarlo.
6. Compila, ejecuta la lista de comprobación de pruebas de humo (`tests/`),
   empaqueta, firma y publica.
7. Las notas de versión enumeran los avisos MFSA incluidos.

## Reglas para los parches de REMILIA

- Un asunto y una categoría por parche (ARCHITECTURE.md §10). Una cabecera
  indica: categoría, propósito, prefs/archivos afectados, si podría enviarse a
  LibreWolf o a Mozilla y qué cambia al revertirlo.
- Preferir, por este orden: pref en el `prefs.cfg` de la categoría → política en
  su `policies.json` → superposición de archivos (copia) → parche de código
  fuente. Los parches de código fuente son el último recurso.
- No modifiques parches de LibreWolf. Si uno no se desea, exclúyelo mediante la
  lista de exclusiones de `upstream/` (Fase 3a), con un ADR.
- Las correcciones que no son específicas de REMILIA se proponen primero al
  upstream.

## Cambiar la imagen de marca de un árbol de LibreWolf: puntos de contacto conocidos

LibreWolf fija su identidad en el código en varios lugares que REMILIA debe
sobrescribir. Inventario a completar en la Fase 3:

- `mozconfig`: `--with-app-name`, `--with-distribution-id`, `--with-branding`,
  `MOZ_APP_REMOTINGNAME`.
- Directorio `lw/` y nombre de archivo `librewolf.cfg` (`lw-dir.patch`, `local-settings.js`).
- Nombre del directorio del perfil (`profile-directory.patch`, `mozilla-dirs.patch`).
- Página `about:librewolf` y panel de preferencias (`about-librewolf.patch`, `pref-pane/`).
- Espacio de nombres de prefs `librewolf.*` (por ejemplo, `librewolf.uBO.assetsBootstrapLocation`).
- Actualizador: `MOZ_APPUPDATE_HOST`, `release_primary.der`, `release_secondary.der`.
- Cadenas: reescritura de `appstrings.properties` y superposiciones de l10n.
- `policies.json` `SupportMenu`, `app.update.url.*`, `app.releaseNotesURL*`.

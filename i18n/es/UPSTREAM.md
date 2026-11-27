<!-- i18n:nav -->
[English](../../UPSTREAM.md) | [Português (Brasil)](../pt-BR/UPSTREAM.md) | [日本語](../ja/UPSTREAM.md) | **Español**
<!-- /i18n:nav -->

<!-- i18n:meta -->
> - **Translation status:** Current
> - **Language:** es
> - **Original language:** English
> - **Source:** [UPSTREAM.md](../../UPSTREAM.md)
> - **Source revision:** sha256:78b60c4f52a5aa358b5bae55549602fb82f0f7cdead29794fe77201d14c5e91b
<!-- /i18n:meta -->

# Sincronización con el upstream

Remilia deriva de dos proyectos. Mantenerse al día con ellos es la tarea de
mantenimiento continua más importante, porque casi todas las correcciones de
seguridad llegan desde el upstream.

## Capas

| Capa | Origen | Fijada en | ¿La edita Remilia? |
|---|---|---|---|
| 1. Firefox | `archive.mozilla.org/pub/firefox/releases/<ver>/source/` (tarball firmado con GPG). Repositorio canónico: `github.com/mozilla-firefox/firefox` | `upstream/pins.env` → `FIREFOX_VERSION` | Nunca directamente; solo mediante parches de la capa 3 |
| 2. LibreWolf | `codeberg.org/librewolf/source` (parches, ajustes, scripts de compilación) | `upstream/pins.env` → `LIBREWOLF_COMMIT` | Nunca; Remilia superpone sus cambios encima |
| 3. Correcciones de compilación, seguridad y privacidad de Remilia | `remilia/build-fixes/`, `remilia/security/`, `remilia/privacy/` (una categoría cada uno, ARCHITECTURE.md §10) | — | Sí |
| 4. Imagen de marca de Remilia | `remilia/branding/` | — | Sí |

## Ciclos de publicación que hay que seguir

- Firefox: versión principal cada 4 semanas; versiones puntuales para problemas
  de seguridad, a veces no programadas ("chemspills"). Avisos:
  mozilla.org/security/advisories/.
- LibreWolf: etiquetas `<firefox-version>-<lw-release>` (por ejemplo, `161.0-1`),
  normalmente pocos días después de Firefox.
- uBlock Origin: independiente; se actualiza a través de AMO, sin relación con
  las versiones de Remilia.

## Procedimiento de actualización

1. Aparece una nueva etiqueta de LibreWolf para una nueva versión de Firefox.
2. Actualiza `upstream/pins.env`: `FIREFOX_VERSION`, `LIBREWOLF_COMMIT`, `LIBREWOLF_TAG`.
3. `./scripts/fetch.sh`, que verifica la firma GPG de Mozilla y el hash del commit.
4. `./scripts/prepare.sh`. Se niega a aplicar las categorías de Remilia
   mientras `upstream/librewolf-base/` difiera de los nuevos archivos de
   LibreWolf. Si un parche de Remilia no se aplica:
   - actualízalo contra el nuevo árbol;
   - si el código que modifica cambió de significado, revisa la cabecera de
     propósito del parche y rehazlo. No lo fuerces.
5. Actualiza la instantánea de la base de LibreWolf con
   `scripts/remilia_layers.py snapshot` y revisa su diff: `librewolf.cfg`,
   `policies.json`, `mozconfig` y `patches.txt`. Revisa cada pref cambiada
   frente a PRIVACY.md y SECURITY.md, porque las sobrescrituras de Remilia
   pueden ahora entrar en conflicto con el upstream o duplicarlo. Después
   ejecuta `python scripts/remilia_layers.py check`.
6. Comprobaciones de árbol (`./scripts/docker.sh verify`); después compila,
   ejecuta la lista de comprobación de validación, empaqueta, firma y publica.
7. Las notas de la versión enumeran los avisos MFSA incluidos.

## Reglas para los parches de Remilia

- Un asunto y una categoría por parche (ARCHITECTURE.md §10). Una cabecera
  indica: categoría, propósito, prefs/archivos afectados, si podría enviarse a
  LibreWolf o a Mozilla y qué cambia al revertirlo. El formato exacto está en
  `remilia/README.md`.
- Prefiere, en este orden: pref en el `prefs.cfg` de la categoría → política en
  su `policies.json` → superposición de archivo (copia) → parche de código
  fuente. Los parches de código son el último recurso.
- No modifiques los parches de LibreWolf. Si uno no se quiere, exclúyelo
  mediante `upstream/librewolf-exclude.txt`, una línea por parche: la ruta tal
  como aparece en el `patches.txt` de LibreWolf y, después, el motivo. El motivo
  es obligatorio y público, porque se copia en `REMILIA-PROVENANCE.txt`: de 10 a
  200 caracteres, sin comas, sin caracteres de control y sin referencias a
  documentos internos. `scripts/remilia_layers.py` comprueba la ruta, que
  aparezca exactamente una vez en `patches.txt`, y el motivo; una línea en el
  formato antiguo, con un identificador de decisión en lugar del motivo, se
  rechaza. La lista está vacía para LibreWolf 161.0-1.
- Las correcciones que no son específicas de Remilia se proponen primero al
  upstream.

## Cambio de marca de un árbol de LibreWolf: puntos de contacto

Inventario del árbol preparado de LibreWolf 161.0-1, hecho en la Fase 3a.
Encontró 4018 líneas que contienen "librewolf"; la lista completa, línea por
línea, no se publica. 3605 de ellas son
las propias superposiciones de cadenas de interfaz de LibreWolf en `lw/l10n/`
(504 archivos).

Qué cubre el inventario: cada línea de un archivo de texto del árbol preparado
(sin el directorio de objetos) que contiene "librewolf", en mayúsculas o
minúsculas. Qué no cubre:

- archivos binarios línea a línea (los iconos y mapas de bits se listan por
  directorio);
- identidad que no contiene esa palabra, como cadenas "Firefox" restantes o
  URL de Mozilla;
- valores por defecto de prefs definidos fuera de `librewolf.cfg`, como
  `browser/app/profile/firefox.js`, `modules/libpref/init/all.js`,
  `modules/libpref/init/StaticPrefList.yaml` y
  `browser/branding/librewolf/pref/firefox-branding.js`. Las comprobaciones de
  las categorías tampoco detectan sobrescrituras de esos valores
  (`remilia/README.md`, "What the checks cover"). Es trabajo pendiente para
  las Fases 3b, 4a y 4b.

La Fase 3b cambia a Remilia la identidad que ve el usuario: nombre, iconos,
interfaz, ejecutables y perfil. Los nombres internos se quedan: el directorio
`lw/`, el nombre de archivo `librewolf.cfg` y el espacio de nombres de prefs
`librewolf.*`. Renombrarlos haría que la seguridad y la privacidad dependieran
de la imagen de marca.

| Punto de contacto | Dónde | Categoría | Fase |
|---|---|---|---|
| Nombre de la aplicación, directorio de marca, nombre de remoting | `mozconfig` líneas 21, 23, 30; `browser/branding/librewolf/configure.sh` líneas 8–11; valores por defecto de vendor y nombre de aplicación en `toolkit/moz.configure` líneas 23, 37 | Imagen de marca (desviaciones de `mozconfig`) | 3b |
| ID de distribución `net.librewolf` | `mozconfig` línea 22 | Imagen de marca | 3b, depende de B1 |
| Directorio de marca: iconos (`.ico`, `.png`, `.icns`, `.bmp`), logotipo, `brand.ftl`, `brand.dtd`, `brand.properties`, `branding.nsi` | `browser/branding/librewolf/` (42 entradas, copiadas por `patch.sh` desde `themes/` de LibreWolf) | Imagen de marca: un nuevo directorio de marca de Remilia; el de LibreWolf no se edita | 3b |
| Manifiesto del ejecutable | `browser/app/librewolf.exe.manifest` líneas 6, 9 | Imagen de marca | 3b |
| Nombres de los directorios de perfil y de datos | `toolkit/xre/nsXREDirProvider.cpp` líneas 337, 430, 432, 1010, 1307, 1317 (`profile-directory.patch`, `mozilla-dirs.patch`); carpeta de copia de seguridad `browser/components/backup/BackupService.sys.mjs` línea 661 | Imagen de marca | 3b |
| Archivo de sobrescrituras del usuario `librewolf.overrides.cfg` (en Windows, leído de `%USERPROFILE%\.librewolf\`) | `extensions/pref/autoconfig/src/prefcalls.js` líneas 25–54 | Seguridad: Remilia lo lee de `%USERPROFILE%\.remilia\`, con el mismo nombre de archivo (SECURITY.md, S5) | 3b, hecho (`static-verified`) |
| Ventana "Acerca de" y página `about:librewolf` | `browser/base/content/aboutDialog.xhtml` líneas 38, 44, 45; `toolkit/content/librewolf.html`; `toolkit/locales/en-US/toolkit/about/aboutLibreWolf.ftl`; `docshell/build/components.conf` línea 18 | Imagen de marca (texto visible); la dirección `about:` es una decisión abierta de 3b | 3b |
| Panel de ajustes | `browser/components/preferences/librewolf.js`, `librewolf.inc.xhtml`; `browser/locales/en-US/browser/preferences/preferences.ftl` (46 líneas) | Imagen de marca para nombres e iconos; el comportamiento de cada control queda en su propia categoría | 3b |
| Cadenas fijas | `appstrings.properties` (reescrito por `patch.sh`, 12 líneas); `dom/locales/en-US/chrome/appstrings.properties`; superposiciones de `lw/l10n/` (1545 líneas con el nombre visible) | Imagen de marca | 3b |
| Logotipo de las herramientas de desarrollo | `devtools/client/aboutdebugging/src/actions/runtimes.js` línea 74 (`lw-logo-devtools.patch`) | Imagen de marca | 3b |
| Enlaces de soporte y de notas de la versión | `lw/librewolf.cfg` líneas 582–586 y 648 (`app.update.url.*`, `app.releaseNotesURL*`, `app.support.baseURL`); `lw/policies.json` líneas 93–94 (`SupportMenu`) y 60 (mensaje sobre paquetes de idioma) | Imagen de marca (desviaciones de pref y de política) | 3b, depende de B1 |
| Host de actualizaciones y claves MAR | `build/moz.build` línea 95 (`MOZ_APPUPDATE_HOST`); `release_primary.der`, `release_secondary.der` copiados por `patch.sh` | Seguridad, no imagen de marca: deciden qué actualizaciones acepta el navegador | 4a, depende de B1, B2 |
| Ubicación de la lista de recursos de uBlock Origin | `lw/librewolf.cfg` líneas 996–999 (`librewolf.uBO.assetsBootstrapLocation`) | Privacidad | 4b |
| Comprobación de versión en el servidor de LibreWolf (desactivada por defecto) | `browser/base/content/aboutDialog.js` líneas 42–72 | Privacidad (petición de red); sigue desactivada | 4b |
| Motores de búsqueda | `services/settings/dumps/main/search-config-v2.json` (copiado por `patch.sh`) | Privacidad (D1) | 4b |
| Nombres en el instalador de Windows | `browser/branding/librewolf/branding.nsi` líneas 11–13 | Imagen de marca | 8 |
| Nombres internos que se mantienen | Prefs `librewolf.*` (`modules/libpref/init/StaticPrefList.yaml` líneas 12433–12446 y unos 40 puntos del código); `lw/` y `librewolf.cfg` (`browser/installer/package-manifest.in` línea 279, `lw/local-settings.js`) | Ninguna: se mantienen a propósito | — |

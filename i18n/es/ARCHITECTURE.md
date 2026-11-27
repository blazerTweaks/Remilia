<!-- i18n:nav -->
[English](../../ARCHITECTURE.md) | [Português (Brasil)](../pt-BR/ARCHITECTURE.md) | [日本語](../ja/ARCHITECTURE.md) | **Español**
<!-- /i18n:nav -->

<!-- i18n:meta -->
> - **Translation status:** Current
> - **Language:** es
> - **Original language:** English
> - **Source:** [ARCHITECTURE.md](../../ARCHITECTURE.md)
> - **Source revision:** sha256:0a67ffd6d7c69a8fda3bf872c3e6b6e505e5db82ad402287610c01a001c2bb3e
<!-- /i18n:meta -->

# REMILIA Browser — Arquitectura

Nombre en clave del proyecto: **SCARLET**
Estado: infraestructura de compilación escrita y demostrada en parte; primera
compilación completa aplazada hasta que las categorías de REMILIA estén
integradas, para que la primera compilación completa sea de REMILIA y no de
LibreWolf sin modificar. El mecanismo de categorías existe (Fase 3a,
`static-verified`), pero todavía no se ha aplicado ningún cambio de REMILIA.
Última revisión: 2026-11-26

Este documento registra *a partir de qué se construye REMILIA, cómo encajan las
capas y por qué*.

---

## 1. Resumen

REMILIA es una **compilación derivada (downstream) de Firefox (Gecko)**,
construida sobre **el conjunto de parches y la configuración de privacidad de
LibreWolf**, con una capa fina, mantenida por separado, de parches, ajustes e
imagen de marca de REMILIA.

REMILIA **no** contiene un motor de navegador propio, no envuelve una WebView y
no es una aplicación Electron. Cada página la renderiza Gecko, cada petición pasa
por Necko (la pila de red de Firefox) y cada proceso de contenido se ejecuta
dentro del sandbox de Firefox para Windows.

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

Cada capa se aplica **en orden, mediante scripts, sobre un árbol limpio**. Nada
de las capas 1 o 2 se edita a mano dentro de este repositorio. Eso es lo que hace
que incorporar las versiones de seguridad del upstream sea barato (ver
[UPSTREAM.md](UPSTREAM.md)).

---

## 2. Elección de la base

### 2.1 Opciones consideradas

| Opción | Veredicto | Motivo |
|---|---|---|
| Escribir un motor | Rechazada | Inviable; prohibido explícitamente por las reglas del proyecto. |
| Chromium / CEF / Electron | Rechazada | El objetivo del proyecto es un navegador Gecko; una base Chromium perdería la compatibilidad con extensiones de Firefox, la Protección total de cookies y el RFP, y no ofrece ningún beneficio documentado para estos objetivos. |
| Bifurcar Firefox directamente (mozilla-firefox/firefox) | Rechazada como base principal | Obligaría a rehacer todo lo que LibreWolf ya mantiene (eliminación de telemetría, 68 parches, ajustes). Se conserva como el *upstream del upstream*. |
| **Bifurcar LibreWolf mediante un fork en git de `librewolf/source`** | Rechazada | Conflictos de fusión en cada versión de 4 semanas; los cambios de REMILIA quedarían intercalados con el historial de LibreWolf y la procedencia sería poco clara. |
| **Capa sobre un commit fijado de LibreWolf** | **Elegida** | La propia compilación de LibreWolf ya funciona como "tarball verificado de Firefox + lista ordenada de parches + archivos copiados". REMILIA repite el mismo patrón un nivel más arriba. Separación clara en 4 capas, diffs pequeños, rebase sencillo. |
| Firefox ESR en lugar de Release | Rechazada por ahora | LibreWolf sigue Release; seguir ESR supondría renunciar al mantenimiento de LibreWolf. Se reconsiderará si la capacidad de los mantenedores de REMILIA no permite sostener el ciclo de 4 semanas (ver §8). |

### 2.2 Qué es realmente LibreWolf (verificado el 2026-11-25)

Fuente: `https://codeberg.org/librewolf/source`, `main` en el commit
`ed92167b4c56` (Makefile `VERSION = 161.0`, `RELEASE = 1`). La etiqueta de
versión `161.0-1` corresponde al commit `e2baf3254fc7`; REMILIA fija la
etiqueta, no `main`.

- **Entrada de la compilación:** `firefox-<ver>.source.tar.xz` de
  `archive.mozilla.org`, verificado con `gpg --verify` contra
  `assets/MOZILLA_PUBKEY.asc`.
- **`scripts/patch.sh`** después, dentro del árbol extraído:
  - copia `assets/mozconfig.new` → `mozconfig`;
  - copia la imagen de marca (`themes/browser/branding/librewolf`), la
    configuración de búsqueda, la página `about:librewolf` y **las claves
    públicas de firma de actualizaciones MAR de LibreWolf** en
    `toolkit/mozapps/update/updater/release_{primary,secondary}.der`;
  - copia `settings/librewolf.cfg`, `settings/distribution/policies.json`,
    `settings/defaults/pref/local-settings.js` en `lw/`;
  - aplica en orden cada parche de `assets/patches.txt` (`patch -p1`);
  - elimina el backend de ML de OpenAI, obliga a todos los pings de Glean a
    seguir la preferencia de envío de datos y reescribe "Firefox" en
    `appstrings.properties`;
  - descarga la l10n de Firefox y superpone las cadenas de LibreWolf.
- **Ajustes:** `librewolf.cfg` (~1000 líneas, AutoConfig, `lockPref`/`pref`/
  `defaultPref`) cargado mediante `general.config.filename` con el sandbox de
  AutoConfig activado; `policies.json` (políticas empresariales).
- **uBlock Origin:** *no* se incluye como archivo. `policies.json` →
  `ExtensionSettings["uBlock0@raymondhill.net"]` con
  `installation_mode: normal_installed` y una `install_url` de AMO; uBO se
  descarga de addons.mozilla.org en el primer arranque. Un parche de Gecko
  (`custom-ubo-assets-bootstrap-location.patch`) inyecta
  `adminSettings.assetsBootstrapLocation` en el almacenamiento administrado de
  uBO para que la selección predeterminada de listas de uBO provenga del
  `uBOAssets.json` de LibreWolf.
- **Las compilaciones para Windows** las genera `bsys6` mediante
  **compilación cruzada en Debian dentro de Docker** (clang, destinos MSVC de
  Rust, el Windows SDK descargado por el `get_vs.py` de Mozilla, Wine para
  `widl`, `fxc2`, NSIS). El README de LibreWolf indica que las compilaciones
  *nativas* en Windows "no están muy bien probadas".
- **Actualizaciones:** bsys6 genera archivos `.mar` firmados y un `update.xml`;
  el árbol de LibreWolf apunta `MOZ_APPUPDATE_HOST` a `update.librewolf.net`.

---

## 3. Estructura del repositorio (objetivo)

```
REMILIA/
├── upstream/               # category "upstream": pins.env (Firefox, LibreWolf,
│                           #   l10n, bsys6, base image, Rust); librewolf-exclude.txt;
│                           #   librewolf-base/ (snapshot of LibreWolf's config files)
├── remilia/                # REMILIA changes, one directory per category
│   ├── README.md           # the category contract checked by the tools
│   ├── build-fixes/        # compile-only fixes, no behaviour change (layer 3)
│   ├── security/           # sandbox, certificates, signing, updates (layer 3)
│   ├── privacy/            # tracking, fingerprinting, cookies, DNS, telemetry,
│   │                       #   uBlock Origin (layer 3)
│   └── branding/           # logos, icons, colours, theme, names, UI (layer 4)
│       # each category holds only what it needs:
│       #   patches/ + series, prefs.cfg, policies.json, mozconfig, files/,
│       #   replaces.txt, deviations.tsv
├── build/                  # build-environment image (windows-cross.Dockerfile)
├── scripts/                # fetch, prepare, toolchains, build, package, docker,
│   │                       #   remilia_layers.py (categories), verify-tree.sh (V1)
│   └── windows/            # host-side tools (build resource guard)
├── i18n/                   # documentation translations
├── tests/                  # validation harness, category test fixtures
│                           #   (tests/layers/)
├── LICENSE                 # MPL-2.0, for REMILIA's own files
└── *.md                    # this documentation set
```

Por ahora, `remilia/` solo contiene su contrato (`README.md`). El directorio
de cada categoría se crea cuando recibe contenido real por primera vez (de la
Fase 3b en adelante), sin estructura vacía. Las reglas de las categorías están
en la §10.

---

## 4. Pipeline de compilación

```
fetch   → firefox-161.0.source.tar.xz (+ .asc)      gpg --verify (Mozilla key)
        → librewolf/source @ <pinned commit>         git, commit hash checked
prepare → LibreWolf patch.sh on a pristine copy       = layer 2 applied
        → REMILIA patch series + file overlays        = layers 3 + 4 applied
build   → ./mach build   (mozconfig: LW base + REMILIA overrides)
package → ./mach package → zip → NSIS installer, .mar update files
```

### 4.1 Equipo de compilación para Windows

Dos vías, ambas legítimas; ver [BUILD.md](BUILD.md):

1. **Vía de publicación / reproducible — compilación cruzada en Linux con
   Docker.** Es el mismo método que usa LibreWolf para los binarios de Windows
   que publica, así que es la vía con la que realmente se prueban los parches de
   LibreWolf. Funciona en esta máquina mediante Docker Desktop (backend WSL2).
2. **Vía de desarrollo — Windows nativo con MozillaBuild.** El método
   documentado y soportado por Mozilla. Mejor para depurar (WinDbg,
   `mach build faster`, cambios incrementales en el front-end). Los scripts de
   shell de LibreWolf necesitan las herramientas GNU que incluye MozillaBuild.

La Fase 5 validará ambas y registrará cuál es la oficial para las
publicaciones. Previsión: compilación cruzada con Docker para las
publicaciones, nativa para iterar.

---

## 5. Arquitectura de privacidad

La privacidad se implementa con **los mecanismos nativos de Firefox**,
configurados, nunca reimplementados:

| Aspecto | Mecanismo (nativo) |
|---|---|
| Rastreo entre sitios | ETP **Estricto** (`browser.contentblocking.category=strict`): Protección total de cookies (dFPI), listas estrictas de rastreadores, shims de SmartBlock, eliminación de parámetros de consulta |
| Huella digital (fingerprinting) | `privacy.resistFingerprinting` (RFP) — el mismo mecanismo que usan Tor Browser y Mullvad Browser |
| Telemetría | Desactivada **en tiempo de compilación** (`MOZ_TELEMETRY_REPORTING` vacío, informador de fallos no compilado, los pings de Glean siguen la preferencia de envío de datos) y por política |
| Bloqueo de contenido | uBlock Origin (sin modificar, firmado por AMO) |
| DNS | TRR de Firefox (DoH) — desactivado por defecto, proveedores seleccionables |
| Transporte | Modo solo HTTPS activado, CRLite obligatorio, 0-RTT desactivado |

La evaluación completa ajuste por ajuste, incluidos los puntos en los que
REMILIA **difiere** deliberadamente de LibreWolf, está en
[PRIVACY.md](PRIVACY.md). Las diferencias relevantes para la seguridad están en
[SECURITY.md](SECURITY.md).

---

## 6. Arquitectura de bloqueo de anuncios

- **Motor:** uBlock Origin, sin modificar, la compilación firmada por AMO.
  REMILIA nunca bifurca ni reempaqueta el código de uBO, así que el motor de
  filtrado, la ventana emergente con recuentos reales de peticiones por sitio y
  el panel de control son todos del propio uBO.
- **Distribución:** el `.xpi` firmado (versión fijada + SHA-256) se coloca en
  `distribution/extensions/` de la aplicación para que esté disponible **sin
  conexión en el primer arranque**, *y* se declara en `policies.json`
  `ExtensionSettings` para que Firefox lo mantenga actualizado mediante el canal
  habitual de actualizaciones firmadas de AMO. La verificación de firmas sigue
  siendo obligatoria.
- **Listas predeterminadas:** se definen mediante el mecanismo que uBO admite,
  `adminSettings.assetsBootstrapLocation` → un `assets.json` de REMILIA.
  Esto solo define los *valores predeterminados de la primera instalación*; el
  usuario conserva el control total. **No** `toOverwrite.filterLists`: el
  `restoreAdminSettings()` de uBO lo vuelve a aplicar en cada arranque
  (verificado en `src/js/storage.js`), lo que desharía silenciosamente las
  elecciones del usuario.
- **Brasil:** el catálogo estándar de uBO no tiene actualmente ninguna lista
  dedicada a Brasil; la lista regional que cubre pt-BR es `spa-1` (AdGuard
  Spanish/Portuguese). uBO activa automáticamente las listas regionales a partir
  de `navigator.language`, pero el RFP falsea ese valor como `en-US`, así que
  REMILIA debe activar `spa-1` explícitamente en su manifiesto de recursos. En la
  Fase 5 se evaluarán listas comunitarias brasileñas adicionales.
- **Ventana emergente:** la Fase 5 decide entre (a) usar la propia ventana
  emergente de uBO como panel de "protección" de la barra de herramientas, o
  (b) un panel de REMILIA que lea solo los datos que expone uBO. Regla: no se
  muestra ninguna estadística que no haya generado el bloqueador. El propio panel
  de ETP de Firefox ya muestra recuentos reales de rastreadores por sitio y se
  mantiene.

---

## 7. Actualizaciones

REMILIA usa **el propio actualizador de Mozilla** (archivos MAR +
`update.xml`), el mismo mecanismo que usa ahora LibreWolf, con **la identidad
propia de REMILIA**:

- Par de claves de firma MAR de REMILIA; las claves públicas sustituyen a las de
  LibreWolf en `release_primary.der` / `release_secondary.der`. **Compilar el
  árbol de LibreWolf sin modificar haría que REMILIA aceptara actualizaciones
  firmadas por LibreWolf y consultara `update.librewolf.net`; esto debe
  sustituirse antes de cualquier compilación pública.**
- `MOZ_APPUPDATE_HOST` → un servidor controlado por REMILIA (dominio aún no
  elegido; ver los bloqueos en el ROADMAP).
- Las actualizaciones nunca tocan el directorio del perfil; los datos del
  usuario solo los migra el propio código de migración de perfiles de Firefox.

Las listas de filtros se actualizan a través de uBO; uBO se actualiza a través de
AMO.

---

## 8. Modelo de mantenimiento

Firefox publica una versión principal cada **4 semanas**, además de versiones
puntuales de seguridad no programadas ("chemspill"). LibreWolf suele seguirlas
en pocos días. La latencia de REMILIA hasta los usuarios = latencia de
LibreWolf + rebase de REMILIA + compilación + publicación.

Requisitos realistas:

- **Por versión:** actualizar los pins, volver a aplicar la serie de parches,
  corregir los rechazos, compilación completa (≈1,5–3 h en un Ryzen 5 3600 de 6
  núcleos para una compilación optimizada, a medir en la Fase 5), pruebas de
  humo, firma, publicación.
- **Objetivo:** versiones de seguridad publicadas en un plazo de **72 horas**
  tras las de LibreWolf. Si no se puede cumplir de forma fiable, hay que
  decírselo claramente a los usuarios; un navegador de privacidad
  desactualizado es un riesgo de seguridad.
- **Presupuesto de parches:** mantener los parches de código fuente de REMILIA
  pocos y pequeños. Preferir prefs, políticas y superposición de archivos a
  diffs de C++/JS. Cada parche lleva una cabecera que indica propósito, capa y si
  se puede enviar al upstream.

Detalles: [UPSTREAM.md](UPSTREAM.md).

---

## 9. Lo que explícitamente no se persigue

- Ningún código propio de renderizado, red, criptografía ni sandbox.
- Ninguna "aleatorización" propia de la huella digital que convertiría a los
  usuarios de REMILIA en una población pequeña y distinguible.
- Ningún framework de frontend ni bundler (nada de React, nada de Vite). Los
  cambios en la interfaz del navegador se hacen en el propio front-end de
  Firefox en XHTML/CSS/JS/Fluent.
- Ninguna afirmación de anonimato.

---

## 10. Categorías de cambios

Cada cambio de REMILIA pertenece exactamente a una categoría. Las categorías
están aisladas para que cada una pueda revisarse, depurarse, revertirse y
resincronizarse con el upstream por separado.

| Categoría | Abarca | Ubicación |
|---|---|---|
| Upstream | Firefox y LibreWolf, sin modificar; pins; parches de LibreWolf que REMILIA excluye | `upstream/` |
| Correcciones de compilación | Cambios necesarios solo para compilar; ningún cambio de comportamiento | `remilia/build-fixes/` |
| Seguridad | Sandbox, certificados, validación HTTPS, firmas, protección de procesos, actualizaciones | `remilia/security/` |
| Privacidad | Protección contra el rastreo, huella digital, cookies, DNS, telemetría, bloqueo de contenido (uBlock Origin) | `remilia/privacy/` |
| Imagen de marca | Logotipos, iconos, colores, tema, nombres, identidad visual de la interfaz | `remilia/branding/` |

Reglas:

- Un parche, bloque de prefs, archivo de políticas o fragmento de mozconfig
  pertenece a una sola categoría. Un cambio que afecta a dos categorías se
  divide en dos.
- La clasificación sigue al efecto. La interfaz que solo cambia la apariencia es
  imagen de marca; la que cambia el comportamiento pertenece a la categoría de
  ese comportamiento (un control de ajustes de DoH es privacidad).
- Firefox lee un único archivo AutoConfig, un único
  `distribution/policies.json` y un único `mozconfig`. `prepare.sh` los compone a
  partir de los fragmentos de cada categoría, con una cabecera por categoría, y
  falla si dos categorías definen la misma pref o política.
- Un valor que sobrescribe a LibreWolf necesita una desviación registrada
  (`deviations.tsv`) que apunte a su motivo escrito, y debe mantener la función
  que usó LibreWolf (`pref`, `defaultPref`, `lockPref`). Redefinir una pref que
  LibreWolf bloquea se marca como `runtime-unverified` hasta que un navegador en
  ejecución confirme su efecto.
- Orden de aplicación fijo: build-fixes → security → privacy → branding. Se
  puede aplicar cualquier subconjunto, de modo que cada categoría se puede
  compilar y validar sola, y una regresión se puede acotar por bisección hasta
  una categoría.
- La cabecera de cada parche registra: categoría, propósito, archivos y prefs
  afectados, si se puede enviar al upstream y qué cambia al revertirlo.

Implementación (Fase 3a): `prepare.sh` con `REMILIA_LAYERS`, y
`scripts/remilia_layers.py` para las comprobaciones y la composición. El
contrato es `remilia/README.md`. Las desviaciones se comprueban contra una
instantánea de los archivos de configuración de LibreWolf en
`upstream/librewolf-base/`, para que las comprobaciones estáticas se ejecuten
sin Docker.

---

## 11. Puntos de control de validación

Una compilación correcta demuestra que la infraestructura de compilación
funciona. No convierte el resultado en un navegador utilizable. Ninguna
compilación se describe como funcional hasta que supera la lista de comprobación
de validación de [ROADMAP.md](ROADMAP.md#lista-de-comprobación-de-validación),
con los resultados registrados según se describe en
`tests/validation/README.md`. Los registros de validación los guarda el
mantenedor localmente y no se publican en este repositorio.

La primera compilación completa se aplaza hasta que la imagen de marca, la
seguridad y la privacidad estén integradas. Hasta entonces, los
cambios se comprueban sin compilar: comprobaciones estáticas en cada cambio
(V0) y una preparación nueva del árbol, por categoría, antes de cerrar cada
fase (V1). V1 prepara árboles de staging separados en `staging/`, dentro del
volumen de compilación. El resto del volumen, con el árbol conservado y su
directorio de objetos, se monta en solo lectura mientras se ejecuta V1. El
trabajo que solo ha superado V0 y V1 queda `static-verified`,
nunca `done`. La compilación completa (V2) y la lista de comprobación (V3)
llegan en la Fase 5 del ROADMAP. Si cada categoría tendrá además una
compilación completa propia es una decisión de la Fase 5; `REMILIA_LAYERS`
(§10) lo hace posible.

<!-- i18n:nav -->
[English](../../ROADMAP.md) | [Português (Brasil)](../pt-BR/ROADMAP.md) | [日本語](../ja/ROADMAP.md) | **Español**
<!-- /i18n:nav -->

<!-- i18n:meta -->
> - **Translation status:** Current
> - **Language:** es
> - **Original language:** English
> - **Source:** [ROADMAP.md](../../ROADMAP.md)
> - **Source revision:** sha256:7c173f95a3c52e9e5b8ad4d6ce1df15a5d1630ef3d47b0b79adf5ac36d4fdf33
<!-- /i18n:meta -->

# Hoja de ruta y estado

Este archivo es el registro del proyecto de tareas completadas, tareas
pendientes, bloqueos y decisiones. Valores de estado: `done` (completado),
`in progress` (en curso), `todo` (pendiente), `blocked` (bloqueado),
`deferred` (aplazado a propósito, con el trabajo conservado) y
`static-verified` (implementado y superadas las comprobaciones estáticas y de
árbol, pero aún no compilado ni probado en un navegador en ejecución; nunca
equivale a `done`).

Última actualización: 2026-11-26

## Fase actual: 3a cerrada por verificación estática (2026-11-26). La Fase 3b — Imagen de marca espera la autorización explícita del mantenedor.

## Reglas de trabajo

1. **Categorías de cambios aisladas.** Upstream, correcciones de compilación,
   seguridad, privacidad e imagen de marca se mantienen en archivos y parches
   separados, nunca mezclados en un mismo parche o commit, cada uno rastreable y
   reversible por separado (ARCHITECTURE.md §10).
2. **Una compilación no es un navegador que funciona.** Una compilación correcta
   solo demuestra la infraestructura de compilación. Nada se califica de
   funcional antes de que la lista de comprobación de validación se supere y
   sus resultados queden registrados (ARCHITECTURE.md §11).
3. **La primera compilación completa se aplaza, no se abandona.** Remilia se
   desarrolla primero y se compila cuando la imagen de marca, la seguridad y la
   privacidad estén lo bastante integradas para representar el proyecto.
   Hasta entonces, las fases se cierran con comprobaciones
   estáticas y de árbol, y su trabajo queda `static-verified`, no `done`.
4. **Ningún cambio de fase automático.** Pasar a la siguiente fase es una
   decisión del mantenedor, tomada tras revisar las pruebas registradas.

## Secuencia

1. Infraestructura de compilación: descarga, verificación, parches de
   LibreWolf, toolchains, Docker, scripts de compilación y empaquetado
   (Fase 2; la compilación en sí se aplaza).
2. Estructura y configuración para los cambios propios de Remilia (Fase 3a).
3. Imagen de marca (Fase 3b).
4. Seguridad (Fase 4a).
5. Privacidad, incluida la integración de uBlock Origin (Fase 4b).
6. Primera compilación completa integrada, empaquetado y validación funcional
   en Windows (Fase 5).
7. Experiencia de usuario, pruebas de seguridad, distribución (Fases 6–8).

## Estrategia de validación

No todo cambio necesita una compilación. Cada nivel se ejecuta cuando es
pertinente, y los niveles inferiores siempre se ejecutan antes que los
superiores.

| Nivel | Cuándo | Qué | Requiere |
|---|---|---|---|
| V0 Estático | Cada cambio | Sintaxis de los fragmentos; cabeceras de parches y archivos `series`; límites entre categorías; prefs o políticas duplicadas entre categorías; `python i18n/i18n.py check`; pruebas unitarias (`python -m unittest discover -s tests/layers`, `python -m unittest discover -s tests/validation`) | Python en el anfitrión. Sin Docker, sin compilación |
| V1 Árbol | Antes de cerrar cada fase | Preparación nueva en un árbol de staging separado: cada parche se aplica con fuzz cero y se revierte limpiamente; cada categoría sola y todas juntas; informe de archivos tocados por varias categorías; un árbol sin categorías es idéntico a la base de LibreWolf | Docker, sin compilación. Nunca toca el directorio de objetos existente |
| V2 Compilación completa | Fase 5, cuando la imagen de marca, la seguridad y la privacidad estén integradas | `build.sh`, `package.sh`, sha256, archivo de procedencia | Docker, horas de compilación |
| V3 Funcional | Tras el primer paquete V2 | La [lista de comprobación de validación](#lista-de-comprobación-de-validación) en Windows, resultados en `internal/evidence/<date>-<build>/` (local, no publicado) | La máquina Windows del mantenedor |

Reglas:

- Si un cambio solo puede validarse compilándolo, se explica el motivo y se
  aprueba antes de iniciar la compilación.
- V0 y V1 demuestran que los cambios se aplican, son coherentes y se pueden
  separar. No demuestran que nada funcione en tiempo de ejecución. Eso
  corresponde a V2 y V3.
- Lo que solo V2/V3 pueden confirmar: opciones de `mozconfig`, que los parches
  de código compilan, iconos y recursos dentro de los ejecutables, el efecto en
  tiempo de ejecución de prefs y políticas, el sandbox, la inclusión de
  uBlock Origin.

## Bloqueos y decisiones abiertas

| ID | Elemento | Necesario para | Responsable |
|---|---|---|---|
| B1 | **Dominio del proyecto** para el servidor de actualizaciones, el ID de distribución (`--with-distribution-id`) y los enlaces de soporte | Fase 3b (imagen de marca), Fase 8 (actualizaciones) | Mantenedor |
| B2 | **Par de claves de firma de actualizaciones MAR** generado y guardado sin conexión | Fase 4a; antes de cualquier compilación pública | Mantenedor |
| B3 | **Clave de API de Safe Browsing**: obtener una o aceptar la alternativa documentada (SECURITY.md §S3) | Fase 4a | Mantenedor |
| B4 | **Certificado de firma de código de Windows (Authenticode).** Sin él, SmartScreen muestra avisos en el instalador | Fase 8 | Mantenedor |
| B5 | ~~Licencia de los archivos propios de Remilia~~ Resuelto el 2026-11-26: MPL-2.0 (`LICENSE`); los archivos heredados conservan sus licencias | Fase 3a | Mantenedor |
| B6 | Instalar **MozillaBuild** (requiere un instalador interactivo y UAC) para la vía de compilación B | Fase 5 (opcional) | Mantenedor |
| D1 | Motor de búsqueda predeterminado | Fase 4b | Abierta |
| D2 | Valor predeterminado de limpieza al cerrar (privacidad frente a mantener la sesión iniciada) | Fase 4b | Abierta |
| D3 | Valor predeterminado de DoH (desactivado frente a elección en el primer arranque) | Fase 4b | Abierta |
| D4 | Panel de protección de la barra de herramientas: ventana emergente de uBO frente a un panel de Remilia sobre los datos de uBO | Fase 6 | Abierta |

## Fase 1 — Investigación `done`

- [x] Estudio del código fuente de Firefox: el repositorio canónico es ahora `github.com/mozilla-firefox/firefox` (Git); los tarballs de publicación están firmados con GPG.
- [x] Estudio de LibreWolf: `codeberg.org/librewolf/source` (parches, ajustes, compilación) y `bsys6` (empaquetado, compilación cruzada para Windows).
- [x] Requisitos de compilación de Firefox en Windows (MozillaBuild, `mach bootstrap`, 40 GB+, sin espacios en las rutas).
- [x] Cómo compila LibreWolf los binarios de Windows (compilación cruzada con Docker en Debian).
- [x] Integración de extensiones: cómo instala LibreWolf uBO; semántica del almacenamiento gestionado de uBO verificada en el código fuente de uBO.
- [x] Revisión de la configuración de privacidad de `librewolf.cfg` v8.6 (secciones de privacidad, red, fingerprinting, seguridad, extensiones y actualizador).
- [x] Licencias: MPL-2.0 (Firefox, LibreWolf), GPL-3.0 (uBO), marca registrada de Firefox, consideraciones sobre obras de fans de Touhou.
- [x] Modelo de mantenimiento (ciclo de 4 semanas, chemspills).
- [x] Conjunto de documentación: README, ARCHITECTURE, PRIVACY, SECURITY, BUILD, UPSTREAM, ROADMAP, CONTRIBUTING.
- [x] Pins del upstream registrados (`upstream/pins.env`).
- [x] Traducciones de la documentación (pt-BR, ja, es) con un verificador de sincronización (`i18n/i18n.py`).
- [ ] No completado: lectura completa de las secciones de UI/telemetría/región de `librewolf.cfg` y revisión línea por línea de los 68 parches de LibreWolf. Trasladado a las Fases 4a/4b.

## Fase 2 — Infraestructura de compilación `deferred`

Objetivo: una infraestructura de compilación capaz de producir un ejecutable de
Windows x64 a partir de la base LibreWolf 161.0-1. Una compilación aislada de
LibreWolf sin modificar ya no es un objetivo. La infraestructura se
conserva y sus pasos restantes pasan a la Fase 5.

- [x] Imagen del entorno de compilación `build/windows-cross.Dockerfile` (derivada de bsys6, imagen base fijada por digest).
- [x] `scripts/fetch.sh`: tarball de Firefox verificado con GPG contra la clave fijada de Mozilla; LibreWolf, l10n y bsys6 en commits fijados; tarball manipulado rechazado (probado).
- [x] `scripts/prepare.sh`: copia limpia → `patch.sh` de LibreWolf (68 parches, 0 fuzz/rechazos) → mozconfig de compilación cruzada para Windows.
- [x] l10n fijada en un commit del `firefox-l10n` de Mozilla (el espejo de LibreWolf devolvió HTTP 502; mismo commit, mismo contenido).
- [x] `scripts/toolchains.sh`: clang, sysroots, Wine, NSIS y Windows SDK en el volumen `remilia-mozbuild` (marca de finalización presente, 2026-11-26).
- [x] Correcciones de compilación halladas al ejecutar la compilación: directorio de trabajo movido a `/builds/work` (clang-cl leía `/work/...` como su opción `/wo`); a la VM de WSL2 se le dio `memory=18GB`, `swap=24GB` tras quedarse sin memoria; 6 trabajos en paralelo.
- [x] Arnés de validación `tests/validation/validate_win64.py` escrito. Aún no se ha ejecutado contra una compilación de Remilia.
- [x] Vigilante de recursos de compilación trasladado al repositorio como `scripts/windows/guard-build.ps1` (lógica del guard v2 sin cambios; umbrales y rutas ahora son parámetros). Ejecución de prueba el 2026-11-26; todavía no se ha usado en una compilación desde esta ubicación.
- [ ] `deferred` `scripts/build.sh` sobre LibreWolf sin modificar: tres intentos registrados; el último se detuvo a propósito el 2026-11-26 en 260 de 1145 archivos C++ unificados. El directorio de objetos (6,9 GB) y todos los registros se conservan en el volumen `remilia-builds`.
- [ ] `deferred` `scripts/package.sh`, tiempo de compilación y recursos medidos en BUILD.md, elección de la vía de compilación oficial (a documentar en BUILD.md): trasladados a la Fase 5.
- [ ] Comparar la `main` de LibreWolf (ed92167b) con la etiqueta `161.0-1` (e2baf325) para entender los cambios posteriores a la publicación.

Los volúmenes `remilia-work`, `remilia-builds` y `remilia-mozbuild`, las
descargas, los registros y los toolchains se conservan. No se limpia nada.

## Fase 3a — Estructura y configuración `static-verified`

Esta fase no cambia el comportamiento del navegador. Construye el mecanismo
que llenarán las fases siguientes. Sus reglas se describen en
`remilia/README.md` y en ARCHITECTURE.md §10. Todos los elementos de abajo
superaron V0 y V1; el mantenedor registra los resultados y no se publican.
Ninguno está `done`: ningún navegador en ejecución ha leído todavía los
archivos compuestos (Fase 5).

Cerrada el 2026-11-26 por verificación estática (V0 + V1), después de que el
mantenedor revisara los resultados y la auditoría final. Los elementos siguen
`static-verified` hasta que la Fase 5 aporte pruebas en ejecución.

- [x] `static-verified` Licencia: MPL-2.0 para los archivos propios de Remilia (`LICENSE`, B5).
- [x] `static-verified` Contrato de las categorías `remilia/README.md`: estructura, cabeceras de parche, `prefs.cfg`, `policies.json`, `mozconfig`, `files/` + `replaces.txt`, `deviations.tsv`.
- [x] `static-verified` `scripts/remilia_layers.py`: comprobaciones V0 y composición determinista de `librewolf.cfg`, `policies.json` y `mozconfig`, con una cabecera por categoría. Los duplicados entre categorías y las sobrescrituras no declaradas de LibreWolf fallan; una sobrescritura debe mantener la función de LibreWolf; redefinir un `lockPref` se marca como `runtime-unverified`.
- [x] `static-verified` Instantánea de la base de LibreWolf `upstream/librewolf-base/`, comprobada contra el árbol preparado.
- [x] `static-verified` `prepare.sh`: `REMILIA_LAYERS`, parches con fuzz cero, superposiciones, composición, procedencia con versiones, commits, categorías y hashes; árboles `--staging` aislados del árbol conservado.
- [x] `static-verified` Lista de exclusiones `upstream/librewolf-exclude.txt` (vacía para 161.0-1).
- [x] `static-verified` Script V1 `scripts/verify-tree.sh` (`docker.sh verify`), con el volumen de compilación en solo lectura salvo `staging/`.
- [x] `static-verified` Fixtures de prueba `tests/layers/` (conjunto válido, 12 conjuntos inválidos, 49 pruebas unitarias); nunca se empaquetan.
- [x] `static-verified` Inventario de la identidad de LibreWolf para la Fase 3b (resumen en UPSTREAM.md).
- [x] Punto de control (V1): el árbol `REMILIA_LAYERS=none` es idéntico al árbol conservado de LibreWolf 161.0-1, salvo 1110 entradas que solo existen en el árbol conservado y se crearon después de su preparación (subproductos de la compilación); todas las diferencias figuran en los resultados.
- [x] Revisión de los resultados de la Fase 3a y de la auditoría final por el mantenedor (aprobada el 2026-11-26).

Limitación conocida que pasa a las fases siguientes: las sobrescrituras solo se
detectan frente a `librewolf.cfg`, `policies.json` y `mozconfig`. Los valores
por defecto de prefs definidos en otros lugares (archivos de prefs por defecto,
prefs estáticas, el archivo de prefs de la marca, código) no se detectan, y el
inventario de identidad solo cubre líneas de texto que contienen "librewolf"
(`remilia/README.md`, "What the checks cover").

## Fase 3b — Imagen de marca `todo`

Categoría: solo imagen de marca. En esta fase no hay cambios de privacidad ni de seguridad.
No iniciada: espera la autorización explícita del mantenedor.

- [ ] Nombre Remilia: nombre de la aplicación, remoting name, identidad de los ejecutables, directorio del perfil (ver los puntos de contacto en UPSTREAM.md). El directorio interno `lw/`, el nombre `librewolf.cfg` y el espacio de nombres de prefs `librewolf.*` se mantienen, para que la seguridad y la privacidad nunca dependan de la imagen de marca (`remilia/README.md`).
- [ ] Concepto del logotipo: un par simétrico de alas de murciélago alrededor de un rombo escarlata. SVG maestro, probado a 16/32/64/128/256 px.
- [ ] Variantes: a todo color, monocromo, para fondo claro, para fondo oscuro, transparente.
- [ ] Generación de `.ico` para Windows; mapas de bits del instalador.
- [ ] Directorio de imagen de marca que sustituye a `--with-branding`.
- [ ] Tema del navegador con la paleta del briefing (CSS de Firefox, sin framework).
- [ ] Página de inicio (local, sin contenido remoto, todos los elementos opcionales).
- [ ] Pendiente de 3a: enumerar los valores por defecto de `browser/branding/librewolf/pref/firefox-branding.js` y las cadenas de identidad que el inventario no ve (cadenas "Firefox" restantes, recursos binarios); comprobar cada pref de marca contra ellos.
- [ ] Punto de control (V0 + V1): imagen de marca sola y con las demás categorías; resultados registrados. Las comprobaciones en tiempo de ejecución esperan a la Fase 5.

## Fase 4a — Seguridad `todo`

Categoría: solo seguridad.

- [ ] Firma de extensiones obligatoria (SECURITY.md S1).
- [ ] Identidad del actualizador de Remilia: claves MAR, servidor de actualizaciones (S2; requiere B1, B2).
- [ ] Certificados: revisión de los ajustes heredados (SECURITY.md).
- [ ] Sandbox: se mantienen los niveles heredados; las diferencias con Firefox oficial se comprueban en la Fase 5.
- [ ] Decisión sobre Safe Browsing (S3, B3) y dominios restringidos para extensiones (S4).
- [ ] Revisión línea por línea de los parches de LibreWolf y de las secciones de `librewolf.cfg` relevantes para la seguridad.
- [ ] Comprobación en ejecución de las prefs y políticas `runtime-unverified` (como redefiniciones de `lockPref`) en un binario oficial de LibreWolf 161.0-1, para 4a y 4b (`remilia/README.md`).
- [ ] Pendiente de 3a: las comprobaciones no detectan los valores por defecto de prefs relevantes para la seguridad definidos fuera de `librewolf.cfg` (archivos de prefs por defecto y prefs estáticas, incluidos los valores que cambia LibreWolf); revisarlos y decidir si la herramienta debe cubrirlos.
- [ ] Punto de control (V0 + V1): seguridad sola y con todas las categorías hasta ese momento; resultados registrados.

## Fase 4b — Privacidad `todo`

Categoría: solo privacidad.

- [ ] Prefs de privacidad con solo las diferencias documentadas; todo lo demás heredado de LibreWolf: protección contra el rastreo, fingerprinting, telemetría, cookies y almacenamiento, DNS over HTTPS, WebRTC.
- [ ] Resolver D1–D3.
- [ ] Interfaz de ajustes: explicaciones claras, mostrando los efectos secundarios y las opciones de RFP.
- [ ] uBlock Origin: fijar el xpi firmado por AMO (SHA-256) e incluirlo en `distribution/extensions/`.
- [ ] `assets.json` de Remilia (estándar de uBO más `spa-1`, los añadidos de LibreWolf, listas brasileñas en evaluación), entregado mediante `assetsBootstrapLocation`.
- [ ] Pendiente de 3a: las comprobaciones no detectan los valores por defecto de prefs relevantes para la privacidad definidos fuera de `librewolf.cfg`; revisarlos antes de definir prefs de privacidad y decidir si la herramienta debe cubrirlos.
- [ ] Punto de control (V0 + V1): privacidad sola y con todas las categorías; resultados registrados.

## Fase 5 — Primera compilación integrada y validación `todo`

La primera compilación completa de Remilia: la infraestructura de la Fase 2
aplicada a las categorías integradas.

- [ ] V2: compilación, empaquetado, sha256, procedencia. Registrar en BUILD.md el tiempo de compilación y el uso de disco y RAM.
- [ ] Elegir la vía de compilación oficial para las publicaciones y documentarla en BUILD.md. Opcional: vía B (MozillaBuild nativo, tras B6) para depuración.
- [ ] V3: [lista de comprobación de validación](#lista-de-comprobación-de-validación), resultados en `internal/evidence/<date>-<build>/` (formato en `tests/validation/README.md`).
- [ ] Captura de paquetes de un perfil nuevo: enumerar cada conexión saliente en PRIVACY.md.
- [ ] uBlock Origin: comportamiento sin conexión en el primer arranque, actualizaciones de AMO, páginas de prueba de bloqueo de anuncios reconocidas; resultados registrados con honestidad.
- [ ] Los elementos de las Fases 3a–4b pasan de `static-verified` a `done` solo con pruebas registradas.

La Fase 5 solo se cierra cuando el mantenedor ha revisado los resultados registrados.

## Fase 6 — Experiencia de usuario `todo`
Barra de herramientas, pestañas, barra de direcciones, descargas, marcadores,
ajustes y la decisión D4 (construir un panel solo sobre datos reales de uBO).
En gran medida son funciones ya existentes de Firefox; el trabajo de Remilia es
tema (imagen de marca) y configuración (privacidad/seguridad), clasificados por
categoría.

## Fase 7 — Seguridad y pruebas `todo`
BrowserLeaks, EFF Cover Your Tracks, pruebas de fugas de DNS y WebRTC, batería de
compatibilidad, perfilado de rendimiento. Los resultados se registran
con fechas y versiones en `internal/evidence/<date>-<build>/` (local, no publicado).

## Fase 8 — Distribución `todo`
Instalador NSIS y zip portátil (ambos existen ya en el bsys6 de LibreWolf),
pipeline de actualizaciones MAR, servidor de actualizaciones, documentación de
publicación. Depende de B1, B2 y B4.

## Lista de comprobación de validación

Ejecutar en Windows 10 x64 (la máquina del mantenedor) con un perfil nuevo. Cada
comprobación se registra como superada, fallida o no aplicable, con el motivo.
Las pruebas las recoge `tests/validation/validate_win64.py`; una persona
escribe los veredictos.

| Comprobación | Cómo |
|---|---|
| Arranque | Arranca desde el paquete descomprimido; crea un perfil; sin fallos; `about:support` se abre |
| Navegación por sitios reales | Una lista fija de sitios reales (noticias, vídeo, mapas, página de inicio de sesión de un webmail, un sitio gubernamental, la página pública de un banco brasileño) carga y se muestra correctamente |
| JavaScript y compatibilidad web | Los sitios con mucho JS funcionan; se ejecuta una página de pruebas estándar de la plataforma web |
| Audio y vídeo | Reproducción de audio y vídeo HTML5 (códecs abiertos y H.264); anotar el estado de DRM/EME (desactivado por la política de LibreWolf) |
| Aceleración gráfica | `about:support` → Gráficos: compositor, WebRender, estado de la aceleración por GPU |
| Extensiones de Firefox | Instalar una extensión firmada de addons.mozilla.org; activar, desactivar, eliminar |
| uBlock Origin | Presente en el primer arranque; bloquea en una página de prueba de bloqueo de anuncios; el panel se abre |
| Multiproceso | Ventanas multiproceso y Fission en `about:support`; `about:processes` muestra procesos de contenido separados |
| Sandbox | Los niveles de sandbox de `about:support` son iguales a los de Firefox 161 oficial en la misma máquina |
| Gestión de perfiles | `about:profiles`: crear, cambiar y eliminar un perfil; los datos persisten tras reiniciar según la configuración |
| Descargas | Descargar un archivo; progreso, ubicación, historial, aviso de archivo peligroso |
| Actualizaciones | No aplicable mientras la compilación tenga `--disable-updater` (mozconfig base de LibreWolf); se aplica cuando exista la identidad del actualizador de la Fase 4a |
| Integridad del paquete | sha256 registrado; el paquete se vuelve a extraer de forma idéntica; `winchecksec` sobre los `.exe`/`.dll` (ASLR, DEP, CFG) |

## Decisiones en vigor

| Decisión | Dónde se explica | Estado |
|---|---|---|
| Capa sobre una versión fijada de LibreWolf, sobre Firefox Release | ARCHITECTURE.md §2 | Aceptada |
| Heredar `librewolf.cfg`; diferencias solo con motivos por escrito | PRIVACY.md, SECURITY.md, `remilia/README.md` | Aceptada |
| Incluir el xpi firmado de uBO; valores predeterminados mediante `assetsBootstrapLocation`, no `toOverwrite` | ARCHITECTURE.md §6 | Aceptada |
| Categorías de cambios aisladas: upstream, correcciones de compilación, seguridad, privacidad, imagen de marca | ARCHITECTURE.md §10 | Aceptada |
| Una compilación correcta no es un navegador que funciona; punto de control de validación antes de calificar nada de funcional | ARCHITECTURE.md §11; Lista de comprobación de validación (este archivo) | Aceptada |
| Aplazar la primera compilación completa hasta que la imagen de marca, la seguridad y la privacidad estén integradas; niveles de validación V0–V3 | ARCHITECTURE.md §11; Estrategia de validación (este archivo) | Aceptada |
| Decisiones de la Fase 3a: MPL-2.0, reglas de composición de AutoConfig, staging aislado, nombres internos `librewolf.*` mantenidos, fixtures, vigilante de recursos | `remilia/README.md`; CONTRIBUTING.md (licencia); BUILD.md (vigilante de recursos) | Aceptada |

<!-- i18n:nav -->
[English](../../ROADMAP.md) | [Português (Brasil)](../pt-BR/ROADMAP.md) | [日本語](../ja/ROADMAP.md) | **Español**
<!-- /i18n:nav -->

<!-- i18n:meta -->
> - **Translation status:** Current
> - **Language:** es
> - **Original language:** English
> - **Source:** [ROADMAP.md](../../ROADMAP.md)
> - **Source revision:** sha256:7b20e98014332469c687cfb4b31a476e4c2ba61f158587bc6601e5e00c17c184
<!-- /i18n:meta -->

# Hoja de ruta y estado

Este archivo es el registro del proyecto de tareas completadas, tareas
pendientes, bloqueos y decisiones. Valores de estado: `done` (completado),
`in progress` (en curso), `todo` (pendiente), `blocked` (bloqueado).

Última actualización: 2026-11-25

## Fase actual: 2 — Base del navegador, paso 1 (toolchain).

## Reglas de trabajo

1. **Categorías de cambios aisladas.** Upstream, correcciones de compilación,
   seguridad, privacidad e imagen de marca se mantienen en archivos y parches
   separados, nunca mezclados en un mismo parche o commit, cada uno rastreable y
   reversible por separado (ARCHITECTURE.md §10, ADR 0004).
2. **Una compilación no es un navegador que funciona.** Una compilación correcta
   solo demuestra la infraestructura de compilación. Nada se califica de
   funcional, y ninguna fase se cierra, antes de que la lista de comprobación de
   validación se supere y sus resultados queden registrados (ARCHITECTURE.md
   §11, ADR 0005).

## Secuencia

1. Terminar el toolchain.
2. Compilar el LibreWolf original, sin cambios de REMILIA.
3. Validar el ejecutable producido.
4. Registrar los resultados de las pruebas.
5. Establecer la estructura de parches y configuraciones propias de REMILIA.
6. Empezar los cambios de imagen de marca.
7. Implementar las configuraciones de seguridad y privacidad, en etapas separadas.
8. Validar cada conjunto de cambios por separado.

Los pasos 1–4 son la Fase 2, el paso 5 es la Fase 3a, el paso 6 es la Fase 3b,
el paso 7 corresponde a las Fases 4a, 4b y 5, y el paso 8 es el punto de control
que cierra cada una de esas fases.

## Bloqueos y decisiones abiertas

| ID | Elemento | Necesario para | Responsable |
|---|---|---|---|
| B1 | **Dominio del proyecto** para el servidor de actualizaciones, el ID de distribución (`--with-distribution-id`) y los enlaces de soporte | Fase 3b (imagen de marca), Fase 8 (actualizaciones) | Mantenedor |
| B2 | **Par de claves de firma de actualizaciones MAR** generado y guardado sin conexión | Fase 4a; antes de cualquier compilación pública | Mantenedor |
| B3 | **Clave de API de Safe Browsing**: obtener una o aceptar la alternativa documentada (SECURITY.md §S3) | Fase 4a | Mantenedor |
| B4 | **Certificado de firma de código de Windows (Authenticode).** Sin él, SmartScreen muestra avisos en el instalador | Fase 8 | Mantenedor |
| B5 | **Licencia de los archivos propios de REMILIA.** Recomendación: MPL-2.0, que los parches sobre archivos MPL exigen de todos modos | Fase 3a | Mantenedor |
| B6 | Instalar **MozillaBuild** (requiere un instalador interactivo y UAC) para la vía de compilación B | Fase 2 (opcional) | Mantenedor |
| D1 | Motor de búsqueda predeterminado | Fase 4b | Abierta |
| D2 | Valor predeterminado de limpieza al cerrar (privacidad frente a mantener la sesión iniciada) | Fase 4b | Abierta |
| D3 | Valor predeterminado de DoH (desactivado frente a elección en el primer arranque) | Fase 4b | Abierta |
| D4 | Panel de protección de la barra de herramientas: ventana emergente de uBO frente a un panel de REMILIA sobre los datos de uBO | Fase 5 | Abierta |

## Fase 1 — Investigación `done`

- [x] Estudio del código fuente de Firefox: el repositorio canónico es ahora `github.com/mozilla-firefox/firefox` (Git); los tarballs de publicación están firmados con GPG.
- [x] Estudio de LibreWolf: `codeberg.org/librewolf/source` (parches, ajustes, compilación) y `bsys6` (empaquetado, compilación cruzada para Windows).
- [x] Requisitos de compilación de Firefox en Windows (MozillaBuild, `mach bootstrap`, 40 GB+, sin espacios en las rutas).
- [x] Cómo compila LibreWolf los binarios para Windows (compilación cruzada con Docker en Debian).
- [x] Integración de extensiones: cómo instala LibreWolf uBO; semántica del almacenamiento administrado de uBO verificada en el código fuente de uBO.
- [x] Revisión de la configuración de privacidad de `librewolf.cfg` v8.6 (secciones de privacidad, red, huella digital, seguridad, extensiones y actualizador).
- [x] Licencias: MPL-2.0 (Firefox, LibreWolf), GPL-3.0 (uBO), marca registrada de Firefox, consideraciones sobre obras de fans de Touhou.
- [x] Modelo de mantenimiento (ciclo de 4 semanas, chemspills).
- [x] Conjunto de documentación: README, ARCHITECTURE, PRIVACY, SECURITY, BUILD, UPSTREAM, ROADMAP, CONTRIBUTING, ADR.
- [x] Pins del upstream registrados (`upstream/pins.env`).
- [x] Traducciones de la documentación (pt-BR, ja, es) con un verificador de sincronización (`i18n/i18n.py`).
- [ ] Sin hacer: lectura completa de las secciones de UI/telemetría/región de `librewolf.cfg` y revisión línea por línea de los 68 parches de LibreWolf. Pasa a las Fases 4a/4b.

## Fase 2 — Base del navegador `in progress`

Objetivo: demostrar que la infraestructura de compilación produce un ejecutable
de Windows válido a partir de **LibreWolf 161.0-1 sin modificar**, y verificar
ese ejecutable. En esta fase no se aplica ningún cambio de REMILIA.

### Paso 1 — Toolchain `in progress`

- [x] Imagen del entorno de compilación `build/windows-cross.Dockerfile` (derivada de bsys6, imagen base fijada por digest).
- [x] `scripts/fetch.sh`: tarball de Firefox verificado con GPG contra la clave fijada de Mozilla; LibreWolf, l10n y bsys6 en commits fijados; tarball manipulado rechazado (probado).
- [x] `scripts/prepare.sh`: copia limpia → `patch.sh` de LibreWolf (68 parches, 0 fuzz/rechazos) → mozconfig de compilación cruzada para Windows.
- [x] l10n fijada en un commit del `firefox-l10n` de Mozilla (el espejo de LibreWolf devolvió HTTP 502; mismo commit, mismo contenido).
- [ ] `scripts/toolchains.sh`: clang, sysroots, Wine, NSIS y Windows SDK en el volumen `remilia-mozbuild`.

### Paso 2 — Compilar LibreWolf sin modificar `todo`

- [ ] `scripts/build.sh` para Windows x64 (vía A, compilación cruzada con Docker). Registrar tiempo, uso de disco y de RAM.
- [ ] `scripts/package.sh`: `.win64.zip` en-US + sha256 + archivo de procedencia en `dist/`.

### Paso 3 — Validar el ejecutable `todo`

Ejecutar en Windows 10 x64 (la máquina del mantenedor) con un perfil nuevo. Cada
comprobación se registra como superada, fallida o no aplicable, con el motivo.

| Comprobación | Cómo |
|---|---|
| Arranque | Arranca desde el paquete descomprimido; crea un perfil; sin fallos; `about:support` se abre |
| Navegación por sitios reales | Una lista fija de sitios reales (noticias, vídeo, mapas, página de inicio de sesión de un webmail, un sitio gubernamental, la página pública de un banco brasileño) carga y se muestra correctamente |
| JavaScript y compatibilidad web | Los sitios con mucho JS funcionan; se ejecuta una página de pruebas estándar de la plataforma web |
| Audio y vídeo | Reproducción de audio y vídeo HTML5 (códecs abiertos y H.264); anotar el estado de DRM/EME (desactivado por la política de LibreWolf) |
| Aceleración gráfica | `about:support` → Gráficos: compositor, WebRender, estado de la aceleración por GPU |
| Extensiones de Firefox | Instalar una extensión firmada de addons.mozilla.org; activar, desactivar, eliminar |
| uBlock Origin | Instalado por la política de LibreWolf en el primer arranque; bloquea en una página de prueba de bloqueo de anuncios; el panel se abre |
| Multiproceso | Ventanas multiproceso y Fission en `about:support`; `about:processes` muestra procesos de contenido separados |
| Sandbox | Los niveles de sandbox de `about:support` son iguales a los de Firefox 161 oficial en la misma máquina |
| Gestión de perfiles | `about:profiles`: crear, cambiar y eliminar un perfil; los datos persisten tras reiniciar según la configuración |
| Descargas | Descargar un archivo; progreso, ubicación, historial, aviso de archivo peligroso |
| Actualizaciones | No aplicable a esta compilación: el mozconfig base de LibreWolf tiene `--disable-updater`. Se cubre en la Fase 4a |
| Integridad del paquete | sha256 registrado; el paquete se vuelve a extraer de forma idéntica; `winchecksec` sobre los `.exe`/`.dll` (ASLR, DEP, CFG) |

### Paso 4 — Registrar los resultados `todo`

- [ ] Escribir `tests/results/<date>-librewolf-161.0-1-win64.md` (formato del ADR 0005).
- [ ] Actualizar BUILD.md con el tiempo de compilación y el uso de recursos medidos, y con los comandos reales.
- [ ] Elegir la vía oficial de compilación para las publicaciones (ADR).
- [ ] Opcional: vía B (MozillaBuild nativo, tras B6) para depurar.
- [ ] Comparar `main` de LibreWolf (ed92167b) con la etiqueta `161.0-1` (e2baf325) para entender los cambios posteriores a la publicación.

La Fase 2 solo se cierra cuando el mantenedor ha revisado los resultados registrados.

## Fase 3a — Estructura de cambios de REMILIA `todo`

- [ ] Crear `remilia/build-fixes/`, `remilia/security/`, `remilia/privacy/`, `remilia/branding/` a medida que llegue el contenido (ADR 0004).
- [ ] `prepare.sh`: aplicar las categorías en orden fijo; componer el archivo AutoConfig, `policies.json` y `mozconfig` con cabeceras por categoría; fallar ante prefs/políticas duplicadas; seleccionar subconjuntos con `REMILIA_LAYERS`.
- [ ] Lista de exclusiones de parches de LibreWolf en `upstream/`, cada una con un ADR.
- [ ] Comprobación: un árbol preparado sin ninguna categoría es idéntico al árbol de la Fase 2.

## Fase 3b — Imagen de marca `todo`

Categoría: solo imagen de marca. En esta fase no hay cambios de privacidad ni de seguridad.

- [ ] Concepto del logotipo: un par simétrico de alas de murciélago alrededor de un rombo escarlata. SVG maestro, probado a 16/32/64/128/256 px.
- [ ] Variantes: a todo color, monocromo, para fondo claro, para fondo oscuro, transparente.
- [ ] Generación de `.ico` para Windows; mapas de bits del instalador.
- [ ] Directorio de imagen de marca que sustituye a `--with-branding`; nombre de la aplicación, remoting name, directorio del perfil, nombre del archivo cfg (ver los puntos de contacto en UPSTREAM.md).
- [ ] Tema del navegador con la paleta del briefing (CSS de Firefox, sin framework).
- [ ] Página de inicio (local, sin contenido remoto, todos los elementos opcionales).
- [ ] Punto de control: lista de comprobación de validación solo con la imagen de marca; resultados registrados.

## Fase 4a — Seguridad `todo`

Categoría: solo seguridad.

- [ ] Firma de extensiones obligatoria (SECURITY.md S1).
- [ ] Identidad del actualizador de REMILIA: claves MAR, servidor de actualizaciones (S2; requiere B1, B2).
- [ ] Decisión sobre Safe Browsing (S3, B3) y dominios restringidos para extensiones (S4).
- [ ] Punto de control: lista de comprobación de validación solo con seguridad y después con todas las categorías hasta ese momento; resultados registrados.

## Fase 4b — Privacidad `todo`

Categoría: solo privacidad.

- [ ] Prefs de privacidad con solo las diferencias documentadas; todo lo demás heredado de LibreWolf.
- [ ] Resolver D1–D3.
- [ ] Captura de paquetes de un perfil nuevo: enumerar cada conexión saliente en PRIVACY.md.
- [ ] Interfaz de ajustes: explicaciones claras, mostrando los efectos secundarios y las opciones de RFP.
- [ ] Punto de control: lista de comprobación de validación solo con privacidad y después con todas las categorías; resultados registrados.

## Fase 5 — Bloqueo de anuncios `todo`

Categoría: privacidad.

- [ ] Fijar uBO (xpi firmado por AMO, SHA-256) e incluirlo en `distribution/extensions/`.
- [ ] `assets.json` de REMILIA (estándar de uBO más `spa-1`, los añadidos de LibreWolf, listas brasileñas en evaluación); entregarlo mediante `assetsBootstrapLocation`.
- [ ] Validar el comportamiento sin conexión en el primer arranque y las actualizaciones de AMO.
- [ ] Resolver D4; construir el panel solo sobre datos reales de uBO.
- [ ] Probar en páginas de prueba de bloqueo de anuncios reconocidas; registrar los resultados con honestidad.
- [ ] Punto de control: lista de comprobación de validación; resultados registrados.

## Fase 6 — Experiencia de usuario `todo`
Barra de herramientas, pestañas, barra de direcciones, descargas, marcadores,
ajustes. En gran medida son funciones ya existentes de Firefox; el trabajo de
REMILIA es tema (imagen de marca) y configuración (privacidad/seguridad),
clasificados por categoría.

## Fase 7 — Seguridad y pruebas `todo`
BrowserLeaks, EFF Cover Your Tracks, pruebas de fugas de DNS y WebRTC, batería de
compatibilidad, perfilado de rendimiento. Los resultados van a `tests/results/`
con fechas y versiones.

## Fase 8 — Distribución `todo`
Instalador NSIS y zip portátil (ambos existen ya en el bsys6 de LibreWolf),
pipeline de actualizaciones MAR, servidor de actualizaciones, documentación de
publicación. Depende de B1, B2 y B4.

## Registro de decisiones

| ADR | Decisión | Estado |
|---|---|---|
| 0001 | Capa sobre una versión fijada de LibreWolf, sobre Firefox Release | Aceptada |
| 0002 | Heredar `librewolf.cfg`; diferencias solo con motivos por escrito | Aceptada |
| 0003 | Incluir el xpi firmado de uBO; valores predeterminados mediante `assetsBootstrapLocation`, no `toOverwrite` | Aceptada |
| 0004 | Categorías de cambios aisladas: upstream, correcciones de compilación, seguridad, privacidad, imagen de marca | Aceptada |
| 0005 | Una compilación correcta no es un navegador que funciona; punto de control de validación por fase | Aceptada |

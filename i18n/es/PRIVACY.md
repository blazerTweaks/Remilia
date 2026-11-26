<!-- i18n:nav -->
[English](../../PRIVACY.md) | [Português (Brasil)](../pt-BR/PRIVACY.md) | [日本語](../ja/PRIVACY.md) | **Español**
<!-- /i18n:nav -->

<!-- i18n:meta -->
> - **Translation status:** Current
> - **Language:** es
> - **Original language:** English
> - **Source:** [PRIVACY.md](../../PRIVACY.md)
> - **Source revision:** sha256:3d383430b03fb0ac9e685314d8c6a73cc750d90952a99898e79c50b0e2627a8b
<!-- /i18n:meta -->

# REMILIA Browser — Privacidad

Estado: **solo diseño.** Nada de este documento se ha compilado ni probado
todavía. Cada elemento tiene un estado: `planned` (planificado), `implemented`
(implementado), `verified` (probado, con resultados en `tests/`). Hoy todos los
elementos están en `planned`.

## Principios

1. **Mecanismos nativos en lugar de código propio.** Firefox ya incluye
   Protección total de cookies, ETP, RFP, Modo solo HTTPS y DoH. REMILIA los
   configura.
2. **Heredar de LibreWolf por defecto.** Cualquier diferencia respecto a
   `librewolf.cfg` necesita una justificación escrita, porque cada diferencia es
   trabajo de mantenimiento y puede hacer que los usuarios de REMILIA sean más
   distinguibles dentro de la población, más grande, de LibreWolf.
3. **Romper sitios debe aportar privacidad.** Un ajuste que rompe sitios sin una
   mejora significativa de la privacidad no se activa por defecto.
4. **Sin exageraciones.** REMILIA reduce la superficie de rastreo y de huella
   digital. No hace anónimo a nadie. DoH no oculta qué sitios visitas al
   proveedor de DoH, ni a los operadores de los sitios, ni a quien observe el SNI
   de TLS, salvo que se use ECH.

## Contra qué protege REMILIA y contra qué no

| Protege (reduce) | **No** protege contra |
|---|---|
| Rastreo entre sitios mediante cookies y almacenamiento | Que tu proveedor de internet o la red vean las IP de destino |
| Dominios conocidos de rastreadores y anuncios | Que el sitio que visitas te identifique después de iniciar sesión |
| Muchos vectores pasivos de huella digital | Un adversario decidido y dirigido |
| Parámetros de rastreo en las consultas de los enlaces | El malware en tu ordenador |
| El espionaje de DNS en la red local (cuando DoH está activado) | Que el proveedor de DoH vea tus consultas DNS |
| La telemetría y la recopilación de datos en segundo plano por parte del navegador | Cualquier cosa que envíes voluntariamente a los sitios web |

## Configuración base (del `librewolf.cfg` v8.6 de LibreWolf, Firefox 161)

Leyenda — **Mantener**: heredar de LibreWolf. **Cambiar**: REMILIA difiere.
**Evaluar**: decidir en la Fase 4, con pruebas.

### Rastreo y cookies

| Ajuste | LibreWolf | REMILIA | Notas |
|---|---|---|---|
| `browser.contentblocking.category` | `strict` | Mantener | ETP Estricto: Protección total de cookies, listas estrictas, shims de SmartBlock, eliminación de parámetros de consulta. |
| Lista de eliminación de parámetros de consulta | lista de Brave | Mantener | Elimina `fbclid`, `gclid`, etc. |
| `privacy.sanitize.sanitizeOnShutdown` | `true` (cookies/caché borradas al salir) | **Evaluar** | Privacidad sólida, pero cierra la sesión del usuario en cada reinicio. Propuesta: mantenerlo activado y dar visibilidad a las excepciones por sitio en los ajustes y en la bienvenida. |
| Caché en disco | desactivada | Mantener | Caché solo en memoria. Cuesta algo de rendimiento en visitas repetidas. |
| `browser.formfill.enable` | `false` | Mantener | |
| Protección contra el rastreo por redirección (bounce tracking) | valor predeterminado de Firefox | **Evaluar** | Confirmar su estado en el ETP Estricto de Fx 161. |
| Global Privacy Control | activado | Mantener | |

### Huella digital (fingerprinting)

| Ajuste | LibreWolf | REMILIA | Notas |
|---|---|---|---|
| `privacy.resistFingerprinting` | `true` | Mantener | Compartido con Tor/Mullvad/LibreWolf, de modo que los usuarios se confunden en un grupo más grande. Efectos secundarios: se informa la zona horaria UTC, se informa la configuración regional `en-US`, se informa a los sitios un tema claro, tamaño de ventana redondeado. Todos se exponen como opciones claras en los ajustes. |
| Letterboxing | desactivado | Mantener | |
| WebGL | activado (protegido por RFP) | Mantener | Desactivar WebGL rompe los mapas y el 3D, y esa elección en sí puede usarse para la huella digital. |
| WebGPU | desactivado | Mantener | |
| Aleatorización propia | — | **Nunca** | Convertiría a los usuarios de REMILIA en una población pequeña y diferenciada. |

No se afirma: protección completa contra la huella digital. La enumeración de
fuentes, el tamaño de pantalla y los detalles del hardware se reducen con RFP, no
se eliminan.

### Telemetría y conexiones en segundo plano

| Elemento | REMILIA |
|---|---|
| Telemetría | Desactivada en tiempo de compilación (`MOZ_TELEMETRY_REPORTING` vacío) **y** por política. |
| Estudios / experimentos de Normandy / Nimbus | Desactivados (`DisableFirefoxStudies`, `DisableRemoteImprovements`). |
| Pocket / mosaicos patrocinados / sugerencias patrocinadas / Firefox Suggest | Desactivados. |
| Informador de fallos | **No se compila** (los servidores de fallos de Mozilla no aceptan compilaciones de bifurcaciones). No se transmite ningún dato de fallos. Una futura opción, voluntaria, de volcados de fallos solo locales es un elemento del roadmap, no una función. |
| Default browser agent | No se compila. |
| Funciones de IA (chatbot en la barra lateral, grupos de pestañas inteligentes, etc.) | Bloqueadas por política; backend de OpenAI eliminado del código fuente (heredado). |

Contactos de red que siguen siendo esperables, que se enumerarán con exactitud en
la Fase 4 mediante una captura de paquetes: Remote Settings (revocación de
certificados/CRLite, listas de bloqueo de seguridad), actualizaciones de
extensiones de AMO, actualizaciones de las listas de filtros de uBO, comprobación
de actualizaciones de REMILIA. Ninguno de ellos envía el historial de navegación.

### DNS y red

| Ajuste | LibreWolf | REMILIA | Notas |
|---|---|---|---|
| DoH (`network.trr.mode`) | `5` (desactivado) | **Evaluar** | Desactivado significa que se usa el resolvedor del sistema operativo. Activado (modo 2/3) traslada la confianza al proveedor. Propuesta: desactivado por defecto, ofreciendo la elección en el primer arranque. |
| Lista de proveedores de DoH | Quad9 ×2, LibreDNS ×2, Wikimedia, DNS4All | Mantener + evaluar añadir un proveedor adecuado para Brasil | No se impone ningún proveedor. |
| Precarga de DNS / precarga de enlaces / conexiones especulativas | desactivadas | Mantener | |
| `network.proxy.socks_remote_dns` | `true` | Mantener | Las consultas DNS pasan por el proxy SOCKS5 cuando hay uno configurado. |
| WebRTC | activado; mDNS oculta la IP local; solo a través del proxy cuando hay uno | Mantener | Desactivar WebRTC rompe las llamadas y puede usarse para la huella digital. Habrá una opción en los ajustes para desactivarlo. |
| Recorte del referer entre orígenes | `XOriginTrimmingPolicy=2` | Mantener | |
| Modo solo HTTPS | activado (política) | Mantener | |
| `beacon.enabled` | `false` | Mantener | |

## Búsqueda

- No se impone ningún proveedor de búsqueda predeterminado. Candidatos
  ofrecidos: DuckDuckGo, Brave Search, Startpage, Mojeek (heredado), Google, Bing.
  La opción predeterminada está por decidir (ADR pendiente).
- Las sugerencias de búsqueda están **desactivadas** por defecto. Si se activan,
  lo que se teclea se envía al proveedor elegido; el ajuste lo dice con palabras
  claras.
- La barra de direcciones no envía consultas a ningún sitio hasta que el usuario
  las confirma.

## Datos que REMILIA nunca recopila

REMILIA (el proyecto) no opera analíticas, cuentas ni servicios de
sincronización. La comprobación de actualizaciones envía la petición que exige el
formato del actualizador de Mozilla (versión, destino de compilación, canal). Esa
petición se documentará en [SECURITY.md](SECURITY.md) cuando exista el servidor de
actualizaciones.

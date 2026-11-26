<!-- i18n:nav -->
[English](../../SECURITY.md) | [Português (Brasil)](../pt-BR/SECURITY.md) | [日本語](../ja/SECURITY.md) | **Español**
<!-- /i18n:nav -->

<!-- i18n:meta -->
> - **Translation status:** Current
> - **Language:** es
> - **Original language:** English
> - **Source:** [SECURITY.md](../../SECURITY.md)
> - **Source revision:** sha256:a93382773a101575a8d0edac736d9c03534c00051f0870bfca987ba98d37c1a1
<!-- /i18n:meta -->

# REMILIA Browser — Seguridad

Estado: **solo diseño.** Todavía no existe ninguna compilación de REMILIA.

La privacidad y la seguridad son cosas distintas. Un ajuste de privacidad nunca
debe debilitar la arquitectura de seguridad de Firefox. Este archivo enumera
cada modificación relevante para la seguridad que REMILIA hace o hereda, con su
justificación.

## Cómo informar de vulnerabilidades

Hasta que exista un canal específico, informa de forma privada al mantenedor. No
abras issues públicas para vulnerabilidades. Las vulnerabilidades del motor
corresponden al upstream (Bugzilla de Mozilla, grupo de seguridad); REMILIA
distribuirá la corrección cuando se publique la versión del upstream que la
contenga.

## Se conserva sin cambios

- Arquitectura multiproceso de Gecko y **Fission** (aislamiento de sitios).
- **Sandbox de procesos de contenido de Windows** (`--enable-sandbox`, heredado
  del mozconfig de Windows de LibreWolf). Nunca se rebaja para ahorrar memoria.
- Validación de certificados mediante NSS. **Nunca se desactiva.** Ninguna
  implementación propia de TLS ni de criptografía.
- Bloqueo de contenido mixto, HSTS, pinning estático HPKP.
- Verificación de firmas de extensiones (ver más abajo: es una diferencia
  deliberada respecto a LibreWolf).
- Endurecimiento de la compilación: `--enable-hardening`, `--enable-stl-hardening`,
  `-ftrivial-auto-var-init=zero`, `-fwrapv` (heredados).

## Endurecimiento heredado de LibreWolf — se mantiene

| Ajuste | Efecto |
|---|---|
| `security.pki.crlite_mode = 2` | Revocación mediante CRLite aplicada localmente. |
| `security.OCSP.enabled = 0` | Sin peticiones OCSP (privacidad); depende de CRLite. |
| `security.cert_pinning.enforcement_level = 2` | Pinning estricto. Puede entrar en conflicto con la interceptación de TLS de los antivirus; documentado en la solución de problemas. |
| `security.ssl.require_safe_negotiation = true` | Rechaza servidores sin RFC 5746. Roturas poco frecuentes. |
| `security.tls.enable_0rtt_data = false` | Sin 0-RTT de TLS 1.3 (riesgo de repetición). |
| `security.enterprise_roots.enabled = false` | No se confía automáticamente en las raíces del almacén de certificados de Windows. |
| `network.IDN_show_punycode = true` | Protección contra homógrafos. |
| `pdfjs.enableScripting = false` | Sin JS en el visor de PDF. |

## Diferencias de REMILIA respecto a LibreWolf (motivadas por la seguridad)

| # | LibreWolf | REMILIA (previsto) | Motivo |
|---|---|---|---|
| S1 | `MOZ_REQUIRE_SIGNING=` (vacío): las extensiones sin firmar se pueden activar con una pref | Mantener el valor predeterminado de Mozilla: firma **obligatoria**, no anulable mediante pref | Impide instalar extensiones manipuladas o sin firmar. Los desarrolladores pueden seguir cargando complementos temporales desde `about:debugging`. |
| S2 | Incluye las claves públicas de firma MAR de LibreWolf; servidor de actualizaciones `update.librewolf.net` | Claves MAR y servidor de actualizaciones propios de REMILIA | Un binario de REMILIA solo debe aceptar actualizaciones firmadas por REMILIA. Obligatorio antes de cualquier compilación pública. |
| S3 | Safe Browsing totalmente desactivado | **Evaluar — ver más abajo** | Los requisitos del proyecto piden protección de Safe Browsing. |
| S4 | `extensions.webextensions.restrictedDomains = ""` (las extensiones pueden ejecutarse en addons.mozilla.org, etc.) | **Evaluar:** restaurar el valor predeterminado de Firefox | La lista de dominios restringidos impide que una extensión comprometida manipule las páginas de la tienda de complementos. |

### S3 — Safe Browsing: problema abierto

El Safe Browsing de Firefox descarga listas de prefijos de hash de Google y
comprueba las URL localmente, enviando solo prefijos de hash cuando hay una
coincidencia parcial. Requiere una **clave de API de Google Safe Browsing
compilada dentro del binario**. La clave de Mozilla no la pueden usar las
bifurcaciones. Google restringe la API de Safe Browsing al uso no comercial, y el
uso comercial requiere la Web Risk API, que es de pago.

Opciones, a decidir en la Fase 4:

1. Obtener una clave de API de Safe Browsing para REMILIA (proyecto no comercial)
   y activar las comprobaciones de las listas de phishing/malware. Las
   comprobaciones *remotas* de reputación de descargas
   (`browser.safebrowsing.downloads.remote.*`) envían metadatos de los archivos
   a Google y siguen **desactivadas**.
2. Si no se puede obtener una clave: mantener Safe Browsing desactivado y
   depender de las listas de malware/phishing de uBO (`urlhaus-1`,
   `curben-phishing`, activadas por defecto), además de un resolvedor DoH
   opcional con bloqueo de malware. Debe describirse con honestidad como más
   débil que Safe Browsing.

Las protecciones locales de descargas (avisos de tipos de archivo peligrosos,
Mark-of-the-Web) son independientes de Safe Browsing y siguen activadas.

## Cadena de suministro

- Código fuente de Firefox: tarball verificado con GPG, de `archive.mozilla.org`.
- Código fuente de LibreWolf: hash de commit fijado en `upstream/pins.env`.
- uBlock Origin: `.xpi` firmado por AMO, con versión y SHA-256 fijados.
- Toolchains de compilación: obtenidas por `mach` (artefactos de Taskcluster de
  Mozilla) o mediante imágenes de contenedor fijadas.
- Las claves de firma de las publicaciones (MAR, Authenticode) nunca se suben a
  este repositorio.

## Política de actualizaciones de seguridad

Las versiones de seguridad de Firefox son la máxima prioridad. Objetivo: una
compilación de REMILIA publicada en un plazo de 72 horas tras la versión
correspondiente de LibreWolf. Cada nota de versión enumera los Mozilla Security
Advisories (MFSA) que incluye.

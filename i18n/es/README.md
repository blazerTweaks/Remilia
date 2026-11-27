<!-- i18n:nav -->
[English](../../README.md) | [Português (Brasil)](../pt-BR/README.md) | [日本語](../ja/README.md) | **Español**
<!-- /i18n:nav -->

<!-- i18n:meta -->
> - **Translation status:** Current
> - **Language:** es
> - **Original language:** English
> - **Source:** [README.md](../../README.md)
> - **Source revision:** sha256:7d3436fb918ba4e9b83dc34ed449cb27a527d7757e695ceeb03668a563859353
<!-- /i18n:meta -->

# REMILIA Browser

**Project SCARLET** — un navegador de escritorio centrado en la privacidad,
construido sobre Firefox (Gecko) y LibreWolf, con una identidad propia inspirada
en Remilia Scarlet.

> **Estado: en desarrollo.** La investigación está terminada y la
> infraestructura de compilación existe, pero todavía no hay ninguna compilación
> de REMILIA: la primera compilación completa está prevista para cuando la
> imagen de marca, la seguridad y la privacidad estén integradas. Nada de lo que
> aparece a continuación es una función publicada. El progreso se registra en
> [ROADMAP.md](ROADMAP.md).

## Qué es REMILIA

- Un **navegador real**: renderizado con Gecko, la pila de red de Firefox,
  multiproceso y aislamiento de sitios, el sandbox de Windows y compatibilidad
  con extensiones de Firefox, todo sin modificar.
- **La base de privacidad de LibreWolf**: telemetría eliminada en tiempo de
  compilación, Protección contra rastreo mejorada en modo Estricto, Protección
  total de cookies, resistFingerprinting y Modo solo HTTPS.
- **uBlock Origin integrado**: la extensión real, firmada por AMO,
  preinstalada, con listas predeterminadas razonables, incluida cobertura
  regional para Brasil.
- **Identidad propia**: una imagen de marca original, gótica y con acentos
  escarlata. La referencia es sutil, y la interfaz se ve profesional incluso
  para quien nunca ha oído hablar de Touhou.

## Qué no es REMILIA

No es un envoltorio de WebView, no es Electron, no es un motor nuevo y no es una
herramienta de anonimato. Consulta [PRIVACY.md](PRIVACY.md) para saber contra qué
protege y contra qué no.

## Documentación

| Documento | Contenido |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Elección de la base, modelo de capas, pipeline de compilación, diseño del bloqueo de anuncios y de las actualizaciones |
| [PRIVACY.md](PRIVACY.md) | Evaluación de privacidad ajuste por ajuste, diferencias respecto a LibreWolf |
| [SECURITY.md](SECURITY.md) | Modelo de seguridad, diferencias, cadena de suministro, problemas abiertos |
| [BUILD.md](BUILD.md) | Requisitos y procedimiento de compilación (Windows x64) |
| [UPSTREAM.md](UPSTREAM.md) | Seguimiento de las versiones de Firefox y LibreWolf |
| [ROADMAP.md](ROADMAP.md) | Fases, estado de las tareas, bloqueos |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Cómo trabajar en el proyecto |

## Créditos y licencias

REMILIA está construido sobre Mozilla Firefox (MPL-2.0) y LibreWolf (MPL-2.0), e
incluye uBlock Origin (GPL-3.0, distribuido sin modificar). "Firefox" es una
marca registrada de Mozilla y no se usa en el nombre ni en la imagen de marca de
REMILIA.

Los archivos originales propios de REMILIA están bajo la Mozilla Public License
2.0 ([LICENSE](../../LICENSE)). Los archivos heredados de Firefox, LibreWolf y
otros componentes de terceros conservan sus propias licencias y avisos, que
REMILIA no modifica.

Touhou Project y Remilia Scarlet son creaciones de ZUN / Team Shanghai Alice.
REMILIA es un proyecto independiente inspirado por fans. No usa ninguna
ilustración oficial, y todos sus recursos visuales son originales.

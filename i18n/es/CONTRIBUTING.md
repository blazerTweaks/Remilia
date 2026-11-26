<!-- i18n:nav -->
[English](../../CONTRIBUTING.md) | [Português (Brasil)](../pt-BR/CONTRIBUTING.md) | [日本語](../ja/CONTRIBUTING.md) | **Español**
<!-- /i18n:nav -->

<!-- i18n:meta -->
> - **Translation status:** Current
> - **Language:** es
> - **Original language:** English
> - **Source:** [CONTRIBUTING.md](../../CONTRIBUTING.md)
> - **Source revision:** sha256:2264196e465502b70acd3022adfb1275a9317dc9a2ceca7b8788f556fea90b67
<!-- /i18n:meta -->

# Contribuir a REMILIA

## Reglas básicas

1. **Nada de funcionalidades falsas.** Nada de maquetas en lugar de funciones ni
   de estadísticas de relleno. Si algo no está implementado, la documentación lo
   dice.
2. **Nunca debilites la seguridad por comodidad ni por los benchmarks.** La
   validación de certificados, el sandbox, Fission y la firma de extensiones no
   son negociables.
3. **Todo cambio de privacidad o seguridad se documenta** en PRIVACY.md o
   SECURITY.md, con el motivo, en el mismo cambio.
4. **Primero el upstream.** Prefiere prefs, después políticas, después
   superposición de archivos y, por último, parches de código fuente. Ver
   UPSTREAM.md.
5. **Ninguna dependencia ni framework nuevo** sin un motivo concreto registrado
   en un ADR. La interfaz del navegador usa las propias tecnologías de front-end
   de Firefox.
6. **Nunca inventes resultados de pruebas ni benchmarks.** Registra qué se
   ejecutó, en qué compilación y en qué fecha, y qué falló.

## Hacer un cambio

- Commits pequeños, con un asunto y una categoría cada uno (upstream,
  correcciones de compilación, seguridad, privacidad, imagen de marca;
  ARCHITECTURE.md §10). El mensaje explica el *porqué*.
- Nuevo parche, pref o política de REMILIA: colócalo en el directorio de su
  única categoría, `remilia/<category>/`. Un parche va en `patches/` y `series`
  de esa categoría, con una cabecera (categoría, propósito, archivos y prefs
  afectados, si se puede enviar al upstream, efecto de revertirlo). Un cambio que
  abarca dos categorías se divide en dos.
- Las decisiones a nivel de arquitectura llevan un registro de decisión de
  arquitectura (ADR): Contexto, Decisión, Consecuencias, Estado.
- Actualiza ROADMAP.md cuando cambie el estado de una tarea.

## Verificación

Tras cualquier cambio que afecte a la compilación: una compilación completa y,
después, la lista de comprobación de pruebas de humo de BUILD.md ("Verificar una
compilación"). Tras un cambio en una pref de privacidad: vuelve a ejecutar las
pruebas correspondientes en `tests/` y actualiza los resultados.

Una compilación correcta no es un navegador que funciona. Antes de calificar
cualquier compilación como funcional, ejecuta la lista de comprobación de
validación (ROADMAP.md, Fase 2, paso 3) y registra los resultados en
`tests/results/` (ADR 0005).

## Licencias

Las contribuciones que afectan a archivos de Firefox o LibreWolf son MPL-2.0. La
licencia de los archivos originales de REMILIA está pendiente (ROADMAP B5).

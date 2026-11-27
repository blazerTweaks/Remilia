<!-- i18n:nav -->
[English](../../CONTRIBUTING.md) | [Português (Brasil)](../pt-BR/CONTRIBUTING.md) | [日本語](../ja/CONTRIBUTING.md) | **Español**
<!-- /i18n:nav -->

<!-- i18n:meta -->
> - **Translation status:** Current
> - **Language:** es
> - **Original language:** English
> - **Source:** [CONTRIBUTING.md](../../CONTRIBUTING.md)
> - **Source revision:** sha256:54c611a0a73f59196c60663e6a67fb6e8c3faff4b56ea530995b10477c23308b
<!-- /i18n:meta -->

# Contribuir a Remilia

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
5. **Ninguna dependencia ni framework nuevo** sin un motivo concreto, explicado
   en el propio cambio y aceptado por el mantenedor. La interfaz del navegador usa las propias tecnologías de front-end
   de Firefox.
6. **Nunca inventes resultados de pruebas ni benchmarks.** Registra qué se
   ejecutó, en qué compilación y en qué fecha, y qué falló.

## Hacer un cambio

- Commits pequeños, con un asunto y una categoría cada uno (upstream,
  correcciones de compilación, seguridad, privacidad, imagen de marca;
  ARCHITECTURE.md §10). El mensaje explica el *porqué*.
- Nuevo parche, pref o política de Remilia: colócalo en el directorio de su
  única categoría, `remilia/<category>/`. Un parche va en `patches/` y `series`
  de esa categoría, con una cabecera (categoría, propósito, archivos y prefs
  afectados, si se puede enviar al upstream, efecto de revertirlo). Un cambio que
  abarca dos categorías se divide en dos. Los formatos exactos están en
  `remilia/README.md`.
- Un valor que sobrescribe a LibreWolf lleva una entrada en el `deviations.tsv`
  de la categoría y su motivo en PRIVACY.md o SECURITY.md (branding: la
  tabla de puntos de contacto de UPSTREAM.md).
- Las decisiones a nivel de arquitectura se presentan al mantenedor antes de
  implementarlas, con contexto, decisión y consecuencias. Una vez adoptadas,
  su efecto se describe en ARCHITECTURE.md.
- Actualiza ROADMAP.md cuando cambie el estado de una tarea.

## Verificación

En cada cambio: las comprobaciones estáticas (V0 en ROADMAP.md, "Estrategia
de validación"). Antes de cerrar una fase: las comprobaciones de árbol (V1).

```sh
python scripts/remilia_layers.py check        # V0: categories, duplicates, deviations
python -m unittest discover -s tests/layers   # V0: tests of the category tool
python -m unittest discover -s tests/validation  # V0: tests of the validation harness
python i18n/i18n.py check                     # V0: documentation translations
./scripts/docker.sh verify                    # V1: staging trees, no compilation
```

No hace falta una compilación completa tras cada cambio; la primera llega cuando
la imagen de marca, la seguridad y la privacidad estén integradas.
Si un cambio solo puede validarse compilándolo, explica el motivo antes de
iniciar la compilación.

Una compilación correcta no es un navegador que funciona. Antes de calificar
cualquier compilación como funcional, ejecuta la
[lista de comprobación de validación](ROADMAP.md#lista-de-comprobación-de-validación)
y registra los resultados en `internal/evidence/<date>-<build>/` (una carpeta
local que Git ignora; los registros de validación nunca se incluyen en un
commit). El trabajo que solo
ha superado V0 y V1 queda `static-verified`, no `done`.

## Licencias

Los archivos originales propios de Remilia son MPL-2.0 ([LICENSE](../../LICENSE)).
Las contribuciones que afectan a archivos de Firefox o LibreWolf también son
MPL-2.0. Los archivos heredados de Firefox, LibreWolf y otros componentes de
terceros conservan sus propias licencias y avisos; no los modifiques.

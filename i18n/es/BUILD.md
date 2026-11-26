<!-- i18n:nav -->
[English](../../BUILD.md) | [Português (Brasil)](../pt-BR/BUILD.md) | [日本語](../ja/BUILD.md) | **Español**
<!-- /i18n:nav -->

<!-- i18n:meta -->
> - **Translation status:** Current
> - **Language:** es
> - **Original language:** English
> - **Source:** [BUILD.md](../../BUILD.md)
> - **Source revision:** sha256:5532a997ca4ac008ffcc43b6011129078eac39ce1b873fea15db8e6ee4c0a3ff
<!-- /i18n:meta -->

# Compilar REMILIA

Estado: **todavía no se puede compilar.** Los scripts de fetch/patch/build son
trabajo de la Fase 2. Este documento describe los requisitos verificados y el
procedimiento previsto. Los pasos marcados con *(Phase 2)* aún no se han
ejecutado.

## Requisitos

De la guía de compilación para Windows de Mozilla (`docs/setup/windows_build.md`, mozilla-firefox/firefox `main`):

- Windows 10/11 x64.
- 8 GB+ de RAM (mínimo 4 GB). Se recomiendan encarecidamente 16–32 GB para compilaciones optimizadas.
- **≥ 40 GB libres en disco** por cada árbol de código fuente + directorio de objetos.
- Sin espacios en la ruta del código fuente ni en la de MozillaBuild.
- Recomendado: una **Dev Drive** (compilaciones un 5–10% más rápidas; solo Windows 11).
- Añade el directorio del código fuente y `%USERPROFILE%\.mozbuild` a las exclusiones de Windows Defender (el bootstrap se ofrece a hacerlo).

Máquina de referencia (mantenedor): Ryzen 5 3600 (6C/12T), 32 GB de RAM,
Windows 10 Pro 19045, Docker Desktop (WSL2), Visual Studio instalado. Los tiempos
de compilación se registrarán aquí tras la Fase 2; todavía no se indica ninguno.

## Vía A — compilación cruzada con Docker (vía de publicación prevista)

Reproduce la forma en que LibreWolf compila los binarios de Windows que publica
(`bsys6`, `assets/Dockerfile.windows`): una imagen de Debian con clang, Rust con
el destino `x86_64-pc-windows-msvc`, el Windows SDK descargado por el
`taskcluster/scripts/misc/get_vs.py` de Mozilla, Wine (`widl`), `fxc2` y NSIS.

*(Phase 2)*

```sh
# inside WSL2 or any x86_64 Linux with Docker
./scripts/fetch.sh            # Firefox tarball + GPG verify, LibreWolf @ pinned commit
./scripts/prepare.sh          # apply LibreWolf, then REMILIA layers
./scripts/build.sh windows    # runs mach in the build container
```

Notas:
- Mantén el directorio de trabajo en el sistema de archivos de Linux (volumen de
  Docker o ext4 de WSL), **no** bajo `/mnt/c` ni `/mnt/d`. La E/S entre sistemas
  de archivos es muy lenta.
- La VM WSL2 de Docker Desktop recibe por defecto el 50% de la RAM del equipo.
  Auméntala en `%USERPROFILE%\.wslconfig` (`memory=24GB`) si el enlazado se queda
  sin memoria.

## Vía B — Windows nativo con MozillaBuild (vía de desarrollo)

*(Phase 2)*

1. Instala MozillaBuild (la última versión) en `C:\mozilla-build`.
2. Abre `C:\mozilla-build\start-shell.bat`.
3. En el árbol preparado de REMILIA: `./mach --no-interactive bootstrap --application-choice=browser`
   (descarga clang, Rust y el Windows SDK; solicita UAC una vez para las exclusiones de Defender).
4. `./mach build` y después `./mach run`.

Consejos para iterar: `./mach build faster` recompila en segundos los cambios
que solo afectan al front-end (JS/CSS/XHTML/Fluent); úsalo para el trabajo de
interfaz e imagen de marca.

## Verificar una compilación *(Phase 2)*

- `./mach run` arranca con un perfil temporal.
- `about:support` muestra la versión y los niveles de `Multiprocess Windows`,
  `Fission` y `Sandbox`; cada uno debe coincidir con el nivel que indica una
  compilación oficial de Firefox de la misma versión en la misma máquina.
- `about:policies` muestra las políticas de REMILIA como activas.
- `about:config` → `general.config.filename` muestra el cfg de REMILIA.

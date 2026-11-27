<!-- i18n:nav -->
[English](../../BUILD.md) | [Português (Brasil)](../pt-BR/BUILD.md) | [日本語](../ja/BUILD.md) | **Español**
<!-- /i18n:nav -->

<!-- i18n:meta -->
> - **Translation status:** Current
> - **Language:** es
> - **Original language:** English
> - **Source:** [BUILD.md](../../BUILD.md)
> - **Source revision:** sha256:adf617eee0385e53aee38f2f12b67f9a1d5dec7f1161d376d756d87546b218ce
<!-- /i18n:meta -->

# Compilar REMILIA

Estado: **infraestructura de compilación escrita y demostrada en parte;
primera compilación completa aplazada.** Los pasos de fetch, prepare y
toolchains se han ejecutado correctamente. El paso de compilación llegó a 260 de
1145 archivos C++ unificados de LibreWolf 161.0-1 sin modificar y después se
detuvo a propósito: la primera compilación completa será de REMILIA, cuando la
imagen de marca, la seguridad y la privacidad estén integradas (Fase 5 del
ROADMAP). Los pasos marcados con *(Phase 5)* aún no se han
completado.

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
de compilación se registrarán aquí tras la primera compilación completa
(Fase 5); todavía no se indica ninguno.

## Vía A — compilación cruzada con Docker (vía de publicación prevista)

Reproduce la forma en que LibreWolf compila los binarios de Windows que publica
(`bsys6`, `assets/Dockerfile.windows`): una imagen de Debian con clang, Rust con
el destino `x86_64-pc-windows-msvc`, el Windows SDK descargado por el
`taskcluster/scripts/misc/get_vs.py` de Mozilla, Wine (`widl`), `fxc2` y NSIS.

*(Phase 5 para `build` y `package`)*

```sh
# from the repository root, in Git Bash or any shell with Docker
./scripts/docker.sh image       # build-environment image
./scripts/docker.sh fetch       # Firefox tarball + GPG verify, LibreWolf @ pinned commit
./scripts/docker.sh prepare     # apply LibreWolf, then REMILIA layers
./scripts/docker.sh toolchains  # clang, Rust, Windows SDK, Wine, NSIS
./scripts/docker.sh build       # mach build
./scripts/docker.sh package     # .win64.zip + sha256 + provenance in dist/
```

Notas:
- Mantén el directorio de trabajo en el sistema de archivos de Linux (volumen de
  Docker o ext4 de WSL), **no** bajo `/mnt/c` ni `/mnt/d`. La E/S entre sistemas
  de archivos es muy lenta.
- La VM WSL2 de Docker Desktop recibe por defecto el 50% de la RAM del equipo.
  En la máquina de referencia la VM se quedó sin memoria con los valores
  predeterminados; compila con `memory=18GB` y `swap=24GB` en
  `%USERPROFILE%\.wslconfig` y 6 trabajos en paralelo.
- `prepare.sh` se niega a sobrescribir un árbol ya preparado, porque el
  directorio de objetos está dentro. `--force` borra ambos. No lo uses nunca
  sobre el árbol conservado en el volumen `remilia-builds`.
- `REMILIA_LAYERS` elige las categorías de REMILIA que aplica `prepare.sh`:
  `all` (por defecto), `none` (LibreWolf sin modificar) o una lista como
  `security,privacy`. Consulta `remilia/README.md`.
- `prepare.sh --staging <name>` prepara un árbol separado en
  `/builds/work/staging/<name>` y nunca toca el árbol conservado. Solo los
  árboles de staging aceptan otra raíz de capas u otra lista de exclusiones
  (los fixtures de prueba).

## Comprobaciones de árbol sin compilar (V1)

```sh
./scripts/docker.sh verify
```

Prepara árboles de staging y los compara con el árbol conservado: sin
categorías, cada categoría de fixture por separado y todas juntas, reversión
de parches, una exclusión de parche de LibreWolf. Nunca compila. El volumen
`remilia-builds` se monta en solo lectura, salvo su directorio `staging/`, de
modo que el árbol conservado, su directorio de objetos y los registros no
pueden modificarse. Cada árbol de staging ocupa unos 6 GB mientras existe y se
borra después. El informe va a `dist/verify-tree/<timestamp>/`.

## Vigilante de recursos (anfitrión Windows)

`scripts/windows/guard-build.ps1` mide la memoria de Windows y de WSL2 durante
una compilación y la detiene con SIGINT cuando se agota la memoria (nunca
apagando WSL ni Docker). Arráncalo antes que el contenedor de compilación, que
debe iniciarse con `--name remilia-build-run` (o pasa `-Container`):

```powershell
.\scripts\windows\guard-build.ps1 -Csv "$env:TEMP\guard.csv" -Events "$env:TEMP\guard-events.log"
```

Los umbrales son parámetros, o claves de un archivo `.psd1` pasado con
`-ConfigFile`. Los valores por defecto son los usados en las compilaciones de
la Fase 2.

## Vía B — Windows nativo con MozillaBuild (vía de desarrollo)

*(Phase 5, opcional)*

1. Instala MozillaBuild (la última versión) en `C:\mozilla-build`.
2. Abre `C:\mozilla-build\start-shell.bat`.
3. En el árbol preparado de REMILIA: `./mach --no-interactive bootstrap --application-choice=browser`
   (descarga clang, Rust y el Windows SDK; solicita UAC una vez para las exclusiones de Defender).
4. `./mach build` y después `./mach run`.

Consejos para iterar: `./mach build faster` recompila en segundos los cambios
que solo afectan al front-end (JS/CSS/XHTML/Fluent); úsalo para el trabajo de
interfaz e imagen de marca.

## Verificar una compilación *(Phase 5)*

- `./mach run` arranca con un perfil temporal.
- `about:support` muestra la versión y los niveles de `Multiprocess Windows`,
  `Fission` y `Sandbox`; cada uno debe coincidir con el nivel que indica una
  compilación oficial de Firefox de la misma versión en la misma máquina.
- `about:policies` muestra las políticas de REMILIA como activas.
- `about:config` → `general.config.filename` muestra el cfg de REMILIA.

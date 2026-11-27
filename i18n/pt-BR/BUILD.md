<!-- i18n:nav -->
[English](../../BUILD.md) | **Português (Brasil)** | [日本語](../ja/BUILD.md) | [Español](../es/BUILD.md)
<!-- /i18n:nav -->

<!-- i18n:meta -->
> - **Translation status:** Current
> - **Language:** pt-BR
> - **Original language:** English
> - **Source:** [BUILD.md](../../BUILD.md)
> - **Source revision:** sha256:adf617eee0385e53aee38f2f12b67f9a1d5dec7f1161d376d756d87546b218ce
<!-- /i18n:meta -->

# Compilando o REMILIA

Status: **infraestrutura de build escrita e parcialmente comprovada; primeira
build completa adiada.** As etapas de fetch, prepare e toolchains foram
executadas com sucesso. A etapa de compilação rodou até 260 de 1145 arquivos
C++ unificados do LibreWolf 161.0-1 sem modificações e então foi interrompida
de propósito: a primeira build completa será do REMILIA, quando branding,
segurança e privacidade estiverem integrados (Fase 5 do ROADMAP). As
etapas marcadas com *(Phase 5)* ainda não foram concluídas.

## Requisitos

Do guia de build para Windows da Mozilla (`docs/setup/windows_build.md`, mozilla-firefox/firefox `main`):

- Windows 10/11 x64.
- 8 GB+ de RAM (mínimo de 4 GB). 16–32 GB são fortemente recomendados para builds otimizadas.
- **≥ 40 GB livres em disco** por árvore de código-fonte + diretório de objetos.
- Sem espaços no caminho do código-fonte nem no do MozillaBuild.
- Recomendado: um **Dev Drive** (builds 5–10% mais rápidas; apenas Windows 11).
- Adicione o diretório do código-fonte e `%USERPROFILE%\.mozbuild` às exclusões do Windows Defender (o bootstrap oferece fazer isso).

Máquina de referência (mantenedor): Ryzen 5 3600 (6C/12T), 32 GB de RAM,
Windows 10 Pro 19045, Docker Desktop (WSL2), Visual Studio instalado. Os tempos
de build serão registrados aqui após a primeira build completa (Fase 5) —
nenhum é informado ainda.

## Caminho A — compilação cruzada com Docker (caminho de release planejado)

Espelha o modo como o LibreWolf compila os binários Windows que publica
(`bsys6`, `assets/Dockerfile.windows`): uma imagem Debian com clang, Rust com o
alvo `x86_64-pc-windows-msvc`, o Windows SDK baixado pelo
`taskcluster/scripts/misc/get_vs.py` da Mozilla, Wine (`widl`), `fxc2` e NSIS.

*(Phase 5 para `build` e `package`)*

```sh
# from the repository root, in Git Bash or any shell with Docker
./scripts/docker.sh image       # build-environment image
./scripts/docker.sh fetch       # Firefox tarball + GPG verify, LibreWolf @ pinned commit
./scripts/docker.sh prepare     # apply LibreWolf, then REMILIA layers
./scripts/docker.sh toolchains  # clang, Rust, Windows SDK, Wine, NSIS
./scripts/docker.sh build       # mach build
./scripts/docker.sh package     # .win64.zip + sha256 + provenance in dist/
```

Observações:
- Mantenha o diretório de trabalho no sistema de arquivos do Linux (volume
  Docker ou ext4 do WSL), **não** em `/mnt/c` ou `/mnt/d`. E/S entre sistemas de
  arquivos é muito lenta.
- A VM WSL2 do Docker Desktop recebe 50% da RAM do host por padrão. Na máquina
  de referência a VM ficou sem memória com os padrões; ela compila com
  `memory=18GB` e `swap=24GB` em `%USERPROFILE%\.wslconfig` e 6 jobs paralelos.
- O `prepare.sh` se recusa a sobrescrever uma árvore já preparada, porque o
  diretório de objetos fica dentro dela. `--force` apaga os dois. Nunca o use na
  árvore preservada no volume `remilia-builds`.
- `REMILIA_LAYERS` escolhe as categorias do REMILIA que o `prepare.sh` aplica:
  `all` (padrão), `none` (LibreWolf sem modificações) ou uma lista como
  `security,privacy`. Veja `remilia/README.md`.
- `prepare.sh --staging <name>` prepara uma árvore separada em
  `/builds/work/staging/<name>` e nunca toca a árvore preservada. Só árvores de
  staging aceitam outra raiz de camadas ou outra lista de exclusões (as
  fixtures de teste).

## Verificações de árvore sem compilar (V1)

```sh
./scripts/docker.sh verify
```

Prepara árvores de staging e as compara com a árvore preservada: sem
categorias, cada categoria de fixture sozinha e todas juntas, reversão de
patches, uma exclusão de patch do LibreWolf. Nunca compila. O volume
`remilia-builds` é montado somente leitura, exceto o diretório `staging/`;
assim, a árvore preservada, o seu diretório de objetos e os logs não podem ser
modificados. Cada árvore de staging ocupa cerca de 6 GB enquanto existe e é
apagada em seguida. O relatório vai para `dist/verify-tree/<timestamp>/`.

## Monitor de recursos (host Windows)

O `scripts/windows/guard-build.ps1` mede a memória do Windows e do WSL2
durante uma build e a interrompe com SIGINT quando a memória se esgota (nunca
desligando o WSL ou o Docker). Inicie-o antes do contêiner de build, que deve
ser iniciado com `--name remilia-build-run` (ou passe `-Container`):

```powershell
.\scripts\windows\guard-build.ps1 -Csv "$env:TEMP\guard.csv" -Events "$env:TEMP\guard-events.log"
```

Os limites são parâmetros, ou chaves de um arquivo `.psd1` passado com
`-ConfigFile`. Os valores padrão são os usados nas builds da Fase 2.

## Caminho B — Windows nativo com MozillaBuild (caminho de desenvolvimento)

*(Phase 5, opcional)*

1. Instale o MozillaBuild (versão mais recente) em `C:\mozilla-build`.
2. Abra `C:\mozilla-build\start-shell.bat`.
3. Na árvore preparada do REMILIA: `./mach --no-interactive bootstrap --application-choice=browser`
   (baixa clang, Rust e Windows SDK; pede o UAC uma vez para as exclusões do Defender).
4. `./mach build`, depois `./mach run`.

Dicas de iteração: `./mach build faster` recompila em segundos mudanças apenas
de front-end (JS/CSS/XHTML/Fluent); use-o para trabalho de interface e branding.

## Verificando uma build *(Phase 5)*

- `./mach run` inicia com um perfil temporário.
- `about:support` mostra a versão e os níveis de `Multiprocess Windows`, `Fission` e
  `Sandbox`; cada um deve ser igual ao nível informado por uma build oficial do
  Firefox da mesma versão, na mesma máquina.
- `about:policies` mostra as políticas do REMILIA como ativas.
- `about:config` → `general.config.filename` mostra o cfg do REMILIA.

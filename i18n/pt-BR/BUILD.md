<!-- i18n:nav -->
[English](../../BUILD.md) | **Português (Brasil)** | [日本語](../ja/BUILD.md) | [Español](../es/BUILD.md)
<!-- /i18n:nav -->

<!-- i18n:meta -->
> - **Translation status:** Current
> - **Language:** pt-BR
> - **Original language:** English
> - **Source:** [BUILD.md](../../BUILD.md)
> - **Source revision:** sha256:5532a997ca4ac008ffcc43b6011129078eac39ce1b873fea15db8e6ee4c0a3ff
<!-- /i18n:meta -->

# Compilando o REMILIA

Status: **ainda não é compilável.** Os scripts de fetch/patch/build são
trabalho da Fase 2. Este documento descreve os requisitos verificados e o
procedimento planejado. As etapas marcadas com *(Phase 2)* ainda não foram
executadas.

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
de build serão registrados aqui após a Fase 2 — nenhum é informado ainda.

## Caminho A — compilação cruzada com Docker (caminho de release planejado)

Espelha o modo como o LibreWolf compila os binários Windows que publica
(`bsys6`, `assets/Dockerfile.windows`): uma imagem Debian com clang, Rust com o
alvo `x86_64-pc-windows-msvc`, o Windows SDK baixado pelo
`taskcluster/scripts/misc/get_vs.py` da Mozilla, Wine (`widl`), `fxc2` e NSIS.

*(Phase 2)*

```sh
# inside WSL2 or any x86_64 Linux with Docker
./scripts/fetch.sh            # Firefox tarball + GPG verify, LibreWolf @ pinned commit
./scripts/prepare.sh          # apply LibreWolf, then REMILIA layers
./scripts/build.sh windows    # runs mach in the build container
```

Observações:
- Mantenha o diretório de trabalho no sistema de arquivos do Linux (volume
  Docker ou ext4 do WSL), **não** em `/mnt/c` ou `/mnt/d`. E/S entre sistemas de
  arquivos é muito lenta.
- A VM WSL2 do Docker Desktop recebe 50% da RAM do host por padrão. Aumente em
  `%USERPROFILE%\.wslconfig` (`memory=24GB`) se a etapa de link ficar sem memória.

## Caminho B — Windows nativo com MozillaBuild (caminho de desenvolvimento)

*(Phase 2)*

1. Instale o MozillaBuild (versão mais recente) em `C:\mozilla-build`.
2. Abra `C:\mozilla-build\start-shell.bat`.
3. Na árvore preparada do REMILIA: `./mach --no-interactive bootstrap --application-choice=browser`
   (baixa clang, Rust e Windows SDK; pede o UAC uma vez para as exclusões do Defender).
4. `./mach build`, depois `./mach run`.

Dicas de iteração: `./mach build faster` recompila em segundos mudanças apenas
de front-end (JS/CSS/XHTML/Fluent); use-o para trabalho de interface e branding.

## Verificando uma build *(Phase 2)*

- `./mach run` inicia com um perfil temporário.
- `about:support` mostra a versão e os níveis de `Multiprocess Windows`, `Fission` e
  `Sandbox`; cada um deve ser igual ao nível informado por uma build oficial do
  Firefox da mesma versão, na mesma máquina.
- `about:policies` mostra as políticas do REMILIA como ativas.
- `about:config` → `general.config.filename` mostra o cfg do REMILIA.

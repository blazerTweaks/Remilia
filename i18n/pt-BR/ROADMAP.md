<!-- i18n:nav -->
[English](../../ROADMAP.md) | **Português (Brasil)** | [日本語](../ja/ROADMAP.md) | [Español](../es/ROADMAP.md)
<!-- /i18n:nav -->

<!-- i18n:meta -->
> - **Translation status:** Current
> - **Language:** pt-BR
> - **Original language:** English
> - **Source:** [ROADMAP.md](../../ROADMAP.md)
> - **Source revision:** sha256:7c173f95a3c52e9e5b8ad4d6ce1df15a5d1630ef3d47b0b79adf5ac36d4fdf33
<!-- /i18n:meta -->

# Roadmap e status

Este arquivo é o registro do projeto de tarefas concluídas, tarefas pendentes,
bloqueios e decisões. Valores de status: `done` (concluído), `in progress` (em
andamento), `todo` (a fazer), `blocked` (bloqueado), `deferred` (adiado de
propósito, com o trabalho preservado) e `static-verified` (implementado e
aprovado nas verificações estáticas e de árvore, mas ainda não compilado nem
testado em um navegador em execução; nunca equivale a `done`).

Última atualização: 2026-11-26

## Fase atual: 3a encerrada por verificação estática (2026-11-26). A Fase 3b — Branding aguarda autorização explícita do mantenedor.

## Regras de trabalho

1. **Categorias de mudança isoladas.** Upstream, correções de build, segurança,
   privacidade e branding ficam em arquivos e patches separados, nunca
   misturados em um mesmo patch ou commit, cada um rastreável e reversível
   individualmente (ARCHITECTURE.md §10).
2. **Uma build não é um navegador funcionando.** Uma compilação bem-sucedida só
   comprova a infraestrutura de build. Nada é chamado de funcional antes que o
   checklist de validação passe e seus resultados sejam registrados
   (ARCHITECTURE.md §11).
3. **A primeira build completa foi adiada, não abandonada.** O Remilia é
   desenvolvido primeiro e compilado quando branding, segurança e privacidade
   estiverem integrados o suficiente para representar o projeto.
   Até lá, as fases são encerradas com verificações estáticas e de árvore, e
   seu trabalho fica `static-verified`, não `done`.
4. **Nenhuma mudança automática de fase.** Avançar para a próxima fase é uma
   decisão do mantenedor, tomada depois de revisar as evidências registradas.

## Sequência

1. Infraestrutura de build: download, verificação, patches do LibreWolf,
   toolchains, Docker, scripts de build e de empacotamento (Fase 2; a build em
   si foi adiada).
2. Estrutura e configurações para as mudanças próprias do Remilia (Fase 3a).
3. Branding (Fase 3b).
4. Segurança (Fase 4a).
5. Privacidade, incluindo a integração do uBlock Origin (Fase 4b).
6. Primeira build completa integrada, empacotamento e validação funcional no
   Windows (Fase 5).
7. Experiência do usuário, testes de segurança, distribuição (Fases 6–8).

## Estratégia de validação

Nem toda mudança precisa de compilação. Cada nível abaixo é executado quando é
relevante, e os níveis inferiores sempre rodam antes dos superiores.

| Nível | Quando | O quê | Requer |
|---|---|---|---|
| V0 Estático | A cada mudança | Sintaxe dos fragmentos; cabeçalhos de patch e arquivos `series`; limites entre categorias; prefs ou políticas duplicadas entre categorias; `python i18n/i18n.py check`; testes unitários (`python -m unittest discover -s tests/layers`, `python -m unittest discover -s tests/validation`) | Python no host. Sem Docker, sem compilação |
| V1 Árvore | Antes de encerrar cada fase | Preparação nova em uma árvore de staging separada: todo patch se aplica com fuzz zero e é revertido sem erros; cada categoria sozinha e todas juntas; relatório de arquivos tocados por mais de uma categoria; uma árvore sem categorias é idêntica à base do LibreWolf | Docker, sem compilação. Nunca toca o diretório de objetos existente |
| V2 Build completa | Fase 5, quando branding, segurança e privacidade estiverem integrados | `build.sh`, `package.sh`, sha256, arquivo de procedência | Docker, horas de compilação |
| V3 Funcional | Depois do primeiro pacote V2 | O [checklist de validação](#checklist-de-validação) no Windows, resultados em `internal/evidence/<date>-<build>/` (local, não publicado) | A máquina Windows do mantenedor |

Regras:

- Se uma mudança só puder ser validada compilando, o motivo é informado e
  aprovado antes de a build começar.
- V0 e V1 comprovam que as mudanças se aplicam, são consistentes e podem ser
  separadas. Não comprovam que algo funciona em tempo de execução. Esse é o
  papel de V2 e V3.
- O que só V2/V3 podem confirmar: opções do `mozconfig`, que os patches de
  código compilam, ícones e recursos dentro dos executáveis, o efeito em tempo
  de execução de prefs e políticas, o sandbox, a inclusão do uBlock Origin.

## Bloqueios e decisões em aberto

| ID | Item | Necessário até | Responsável |
|---|---|---|---|
| B1 | **Domínio do projeto** para o servidor de atualizações, ID de distribuição (`--with-distribution-id`), links de suporte | Fase 3b (branding), Fase 8 (atualizações) | Mantenedor |
| B2 | **Par de chaves de assinatura de atualizações MAR** gerado e guardado offline | Fase 4a; antes de qualquer build pública | Mantenedor |
| B3 | **Chave de API do Safe Browsing**: obter uma ou aceitar a alternativa documentada (SECURITY.md §S3) | Fase 4a | Mantenedor |
| B4 | **Certificado de assinatura de código do Windows (Authenticode).** Sem ele, o SmartScreen exibe avisos no instalador | Fase 8 | Mantenedor |
| B5 | ~~Licença dos arquivos próprios do Remilia~~ Resolvido em 2026-11-26: MPL-2.0 (`LICENSE`); os arquivos herdados mantêm suas licenças | Fase 3a | Mantenedor |
| B6 | Instalar o **MozillaBuild** (requer um instalador interativo e UAC) para o caminho de build B | Fase 5 (opcional) | Mantenedor |
| D1 | Mecanismo de busca padrão | Fase 4b | Em aberto |
| D2 | Padrão de limpeza ao fechar (privacidade vs. permanecer conectado) | Fase 4b | Em aberto |
| D3 | Padrão de DoH (desativado vs. escolha na primeira execução) | Fase 4b | Em aberto |
| D4 | Painel de proteção da barra de ferramentas: popup do uBO vs. um painel do Remilia sobre os dados do uBO | Fase 6 | Em aberto |

## Fase 1 — Pesquisa `done`

- [x] Levantamento do código-fonte do Firefox: o repositório canônico agora é `github.com/mozilla-firefox/firefox` (Git); os tarballs de release são assinados com GPG.
- [x] Levantamento do LibreWolf: `codeberg.org/librewolf/source` (patches, configurações, build) e `bsys6` (empacotamento, compilação cruzada para Windows).
- [x] Requisitos de build do Firefox no Windows (MozillaBuild, `mach bootstrap`, 40 GB+, sem espaços nos caminhos).
- [x] Como o LibreWolf compila os binários para Windows (compilação cruzada com Docker no Debian).
- [x] Integração de extensões: como o LibreWolf instala o uBO; semântica do armazenamento gerenciado do uBO verificada no código-fonte do uBO.
- [x] Revisão da configuração de privacidade do `librewolf.cfg` v8.6 (seções de privacidade, rede, fingerprinting, segurança, extensões e atualizador).
- [x] Licenciamento: MPL-2.0 (Firefox, LibreWolf), GPL-3.0 (uBO), marca registrada do Firefox, considerações sobre obras de fãs de Touhou.
- [x] Modelo de manutenção (ciclo de 4 semanas, chemspills).
- [x] Conjunto de documentação: README, ARCHITECTURE, PRIVACY, SECURITY, BUILD, UPSTREAM, ROADMAP, CONTRIBUTING.
- [x] Pins do upstream registrados (`upstream/pins.env`).
- [x] Traduções da documentação (pt-BR, ja, es) com um verificador de sincronização (`i18n/i18n.py`).
- [ ] Não concluído: leitura completa das seções de UI/telemetria/região do `librewolf.cfg` e revisão linha a linha de todos os 68 patches do LibreWolf. Transferido para as Fases 4a/4b.

## Fase 2 — Infraestrutura de build `deferred`

Objetivo: infraestrutura de build capaz de produzir um executável Windows x64 a
partir da base LibreWolf 161.0-1. Uma build isolada do LibreWolf sem
modificações deixou de ser um objetivo. A infraestrutura é mantida e
as etapas restantes passam para a Fase 5.

- [x] Imagem do ambiente de build `build/windows-cross.Dockerfile` (derivada do bsys6, imagem base fixada por digest).
- [x] `scripts/fetch.sh`: tarball do Firefox verificado por GPG contra a chave fixada da Mozilla; LibreWolf, l10n e bsys6 em commits fixados; tarball adulterado rejeitado (testado).
- [x] `scripts/prepare.sh`: cópia limpa → `patch.sh` do LibreWolf (68 patches, 0 fuzz/rejeições) → mozconfig de compilação cruzada para Windows.
- [x] l10n fixada em um commit do `firefox-l10n` da Mozilla (o espelho do LibreWolf retornou HTTP 502; mesmo commit, mesmo conteúdo).
- [x] `scripts/toolchains.sh`: clang, sysroots, Wine, NSIS e Windows SDK no volume `remilia-mozbuild` (marcador de conclusão presente, 2026-11-26).
- [x] Correções de build encontradas ao executar a build: diretório de trabalho movido para `/builds/work` (o clang-cl lia `/work/...` como sua opção `/wo`); VM do WSL2 configurada com `memory=18GB`, `swap=24GB` depois de ficar sem memória; 6 jobs paralelos.
- [x] Harness de validação `tests/validation/validate_win64.py` escrito. Ainda não executado contra uma build do Remilia.
- [x] Monitor de recursos da build movido para o repositório como `scripts/windows/guard-build.ps1` (lógica do guard v2 inalterada; limites e caminhos viraram parâmetros). Execução de teste em 2026-11-26; ainda não usado em uma build a partir deste local.
- [ ] `deferred` `scripts/build.sh` no LibreWolf sem modificações: três tentativas registradas em log; a última foi interrompida de propósito em 2026-11-26, em 260 de 1145 arquivos C++ unificados. O diretório de objetos (6,9 GB) e todos os logs estão preservados no volume `remilia-builds`.
- [ ] `deferred` `scripts/package.sh`, tempo de build e recursos medidos no BUILD.md, escolha do caminho oficial de build (a documentar no BUILD.md): transferidos para a Fase 5.
- [ ] Comparar a `main` do LibreWolf (ed92167b) com a tag `161.0-1` (e2baf325) para entender as mudanças pós-release.

Os volumes `remilia-work`, `remilia-builds` e `remilia-mozbuild`, os downloads,
os logs e os toolchains são mantidos. Nada é limpo.

## Fase 3a — Estrutura e configurações `static-verified`

Nenhuma mudança de comportamento do navegador nesta fase. Ela constrói o
mecanismo que as próximas fases preenchem. Suas regras estão descritas em
`remilia/README.md` e no ARCHITECTURE.md §10. Todos os itens abaixo passaram
no V0 e no V1; os resultados são registrados pelo mantenedor e não são
publicados.
Nenhum deles está `done`: os arquivos montados ainda não foram lidos por um
navegador em execução (Fase 5).

Encerrada em 2026-11-26 por verificação estática (V0 + V1), depois que o
mantenedor revisou os resultados e a auditoria final. Os itens continuam
`static-verified` até que a Fase 5 traga evidências em execução.

- [x] `static-verified` Licença: MPL-2.0 para os arquivos próprios do Remilia (`LICENSE`, B5).
- [x] `static-verified` Contrato das categorias `remilia/README.md`: estrutura, cabeçalhos de patch, `prefs.cfg`, `policies.json`, `mozconfig`, `files/` + `replaces.txt`, `deviations.tsv`.
- [x] `static-verified` `scripts/remilia_layers.py`: verificações V0 e montagem determinística de `librewolf.cfg`, `policies.json` e `mozconfig`, com um cabeçalho por categoria. Duplicatas entre categorias e sobrescritas não declaradas do LibreWolf falham; uma sobrescrita deve manter a função do LibreWolf; a redefinição de um `lockPref` é marcada como `runtime-unverified`.
- [x] `static-verified` Snapshot da base do LibreWolf `upstream/librewolf-base/`, verificado contra a árvore preparada.
- [x] `static-verified` `prepare.sh`: `REMILIA_LAYERS`, patches com fuzz zero, sobreposições, montagem, procedência com versões, commits, categorias e hashes; árvores `--staging` isoladas da árvore preservada.
- [x] `static-verified` Lista de exclusões `upstream/librewolf-exclude.txt` (vazia para a 161.0-1).
- [x] `static-verified` Script V1 `scripts/verify-tree.sh` (`docker.sh verify`), com o volume de build somente leitura, exceto `staging/`.
- [x] `static-verified` Fixtures de teste `tests/layers/` (conjunto válido, 12 conjuntos inválidos, 49 testes unitários); nunca empacotadas.
- [x] `static-verified` Inventário da identidade do LibreWolf para a Fase 3b (resumo no UPSTREAM.md).
- [x] Portão (V1): a árvore `REMILIA_LAYERS=none` é idêntica à árvore preservada do LibreWolf 161.0-1, exceto por 1110 entradas que existem apenas na árvore preservada e foram criadas depois da sua preparação (subprodutos da build); todas as diferenças estão listadas nos resultados.
- [x] Revisão dos resultados da Fase 3a e da auditoria final pelo mantenedor (aprovada em 2026-11-26).

Limitação conhecida, levada para as fases seguintes: as sobrescritas só são
detectadas em relação a `librewolf.cfg`, `policies.json` e `mozconfig`. Os
padrões de prefs definidos em outros lugares (arquivos de prefs padrão, prefs
estáticas, o arquivo de prefs do branding, código) não são detectados, e o
inventário de identidade só cobre linhas de texto que contêm "librewolf"
(`remilia/README.md`, "What the checks cover").

## Fase 3b — Branding `todo`

Categoria: apenas branding. Nenhuma mudança de privacidade ou segurança nesta fase.
Não iniciada: aguarda autorização explícita do mantenedor.

- [ ] Nome Remilia: nome do aplicativo, remoting name, identidade dos executáveis, diretório de perfil (veja os pontos de contato em UPSTREAM.md). O diretório interno `lw/`, o nome `librewolf.cfg` e o namespace de prefs `librewolf.*` ficam, para que segurança e privacidade nunca dependam do branding (`remilia/README.md`).
- [ ] Conceito do logo: par simétrico de asas de morcego em volta de um losango escarlate. SVG mestre, testado em 16/32/64/128/256 px.
- [ ] Variantes: colorida, monocromática, para fundo claro, para fundo escuro, transparente.
- [ ] Geração de `.ico` para Windows; bitmaps do instalador.
- [ ] Diretório de branding substituindo `--with-branding`.
- [ ] Tema do navegador com a paleta do briefing (CSS do Firefox, sem framework).
- [ ] Página inicial (local, sem conteúdo remoto, todos os elementos opcionais).
- [ ] Pendente da 3a: listar os padrões em `browser/branding/librewolf/pref/firefox-branding.js` e as strings de identidade que o inventário não enxerga (strings "Firefox" restantes, assets binários); conferir cada pref de branding contra eles.
- [ ] Portão (V0 + V1): branding sozinho e com as outras categorias; resultados registrados. As verificações em tempo de execução aguardam a Fase 5.

## Fase 4a — Segurança `todo`

Categoria: apenas segurança.

- [ ] Assinatura de extensões obrigatória (SECURITY.md S1).
- [ ] Identidade do atualizador do Remilia: chaves MAR, host de atualização (S2; requer B1, B2).
- [ ] Certificados: revisão das configurações herdadas (SECURITY.md).
- [ ] Sandbox: níveis herdados mantidos; diferenças em relação ao Firefox oficial verificadas na Fase 5.
- [ ] Decisão sobre o Safe Browsing (S3, B3) e domínios restritos para extensões (S4).
- [ ] Revisão linha a linha dos patches do LibreWolf e das seções do `librewolf.cfg` relevantes para segurança.
- [ ] Verificação em execução das prefs e políticas `runtime-unverified` (como redefinições de `lockPref`) em um binário oficial do LibreWolf 161.0-1, para a 4a e a 4b (`remilia/README.md`).
- [ ] Pendente da 3a: os padrões de prefs relevantes para segurança definidos fora do `librewolf.cfg` (arquivos de prefs padrão e prefs estáticas, incluindo os valores alterados pelo LibreWolf) não são detectados pelas verificações; revisá-los e decidir se a ferramenta deve cobri-los.
- [ ] Portão (V0 + V1): segurança sozinha e com todas as categorias até aqui; resultados registrados.

## Fase 4b — Privacidade `todo`

Categoria: apenas privacidade.

- [ ] Prefs de privacidade contendo apenas as divergências documentadas; todo o resto herdado do LibreWolf: proteção contra rastreamento, fingerprinting, telemetria, cookies e armazenamento, DNS over HTTPS, WebRTC.
- [ ] Resolver D1–D3.
- [ ] Interface de configurações: explicações claras, expondo os efeitos colaterais e as opções do RFP.
- [ ] uBlock Origin: fixar o xpi assinado pela AMO (SHA-256) e incluí-lo em `distribution/extensions/`.
- [ ] `assets.json` do Remilia (padrão do uBO mais `spa-1`, os acréscimos do LibreWolf, listas brasileiras em avaliação), entregue via `assetsBootstrapLocation`.
- [ ] Pendente da 3a: os padrões de prefs relevantes para privacidade definidos fora do `librewolf.cfg` não são detectados pelas verificações; revisá-los antes de definir prefs de privacidade e decidir se a ferramenta deve cobri-los.
- [ ] Portão (V0 + V1): privacidade sozinha e com todas as categorias; resultados registrados.

## Fase 5 — Primeira build integrada e validação `todo`

A primeira build completa do Remilia: a infraestrutura da Fase 2 aplicada às
categorias integradas.

- [ ] V2: build, empacotamento, sha256, procedência. Registrar no BUILD.md o tempo de build e o uso de disco e de RAM.
- [ ] Escolher o caminho oficial de build para releases e documentá-lo no BUILD.md. Opcional: caminho B (MozillaBuild nativo, após B6) para depuração.
- [ ] V3: [checklist de validação](#checklist-de-validação), resultados em `internal/evidence/<date>-<build>/` (formato em `tests/validation/README.md`).
- [ ] Captura de pacotes de um perfil novo: listar toda conexão de saída em PRIVACY.md.
- [ ] uBlock Origin: comportamento offline na primeira execução, atualizações pela AMO, páginas de teste de bloqueio de anúncios consagradas; resultados registrados com honestidade.
- [ ] Os itens das Fases 3a–4b passam de `static-verified` para `done` somente com evidências registradas.

A Fase 5 só é encerrada depois que o mantenedor revisar os resultados registrados.

## Fase 6 — Experiência do usuário `todo`
Barra de ferramentas, abas, barra de endereços, downloads, favoritos,
configurações e a decisão D4 (construir um painel apenas sobre dados reais do
uBO). Em grande parte são recursos já existentes no Firefox; o trabalho do
Remilia é tema (branding) e configuração (privacidade/segurança), registrados
por categoria.

## Fase 7 — Segurança e testes `todo`
BrowserLeaks, EFF Cover Your Tracks, testes de vazamento de DNS e WebRTC,
suíte de compatibilidade, profiling de desempenho. Os resultados são registrados
com datas e versões em `internal/evidence/<date>-<build>/` (local, não publicado).

## Fase 8 — Distribuição `todo`
Instalador NSIS e zip portátil (ambos já existem no bsys6 do LibreWolf),
pipeline de atualizações MAR, servidor de atualizações, documentação de
release. Depende de B1, B2 e B4.

## Checklist de validação

Executar no Windows 10 x64 (a máquina do mantenedor) com um perfil novo. Cada
verificação é registrada como aprovada, reprovada ou não aplicável, com o
motivo. As evidências são coletadas por `tests/validation/validate_win64.py`;
uma pessoa escreve os veredictos.

| Verificação | Como |
|---|---|
| Inicialização | Inicia a partir do pacote descompactado; cria um perfil; sem falhas; `about:support` abre |
| Navegação em sites reais | Uma lista fixa de sites reais (notícias, vídeo, mapas, página de login de webmail, um site do governo, a página pública de um banco brasileiro) carrega e renderiza |
| JavaScript e compatibilidade web | Sites com muito JS funcionam; uma página de testes padrão da plataforma web roda |
| Áudio e vídeo | Reprodução de áudio e vídeo HTML5 (codecs abertos e H.264); anotar o estado de DRM/EME (desativado pela política do LibreWolf) |
| Aceleração gráfica | `about:support` → Gráficos: compositor, WebRender, status da aceleração por GPU |
| Extensões do Firefox | Instalar uma extensão assinada de addons.mozilla.org; ativar, desativar, remover |
| uBlock Origin | Presente na primeira execução; bloqueia em uma página de teste de bloqueio de anúncios; o painel abre |
| Multiprocesso | Janelas multiprocesso e Fission em `about:support`; `about:processes` mostra processos de conteúdo separados |
| Sandbox | Níveis de sandbox em `about:support` iguais aos do Firefox 161 oficial na mesma máquina |
| Gerenciamento de perfis | `about:profiles`: criar, alternar e excluir um perfil; os dados persistem após reiniciar, conforme configurado |
| Downloads | Baixar um arquivo; progresso, local, histórico, aviso de arquivo perigoso |
| Atualizações | Não aplicável enquanto a build tiver `--disable-updater` (mozconfig base do LibreWolf); passa a valer quando a identidade do atualizador da Fase 4a existir |
| Integridade do pacote | sha256 registrado; o pacote é extraído novamente de forma idêntica; `winchecksec` nos `.exe`/`.dll` (ASLR, DEP, CFG) |

## Decisões em vigor

| Decisão | Onde está explicada | Status |
|---|---|---|
| Camada sobre uma release fixada do LibreWolf, sobre o Firefox Release | ARCHITECTURE.md §2 | Aceita |
| Herdar o `librewolf.cfg`; divergências somente com motivos por escrito | PRIVACY.md, SECURITY.md, `remilia/README.md` | Aceita |
| Incluir o xpi assinado do uBO; padrões via `assetsBootstrapLocation`, não `toOverwrite` | ARCHITECTURE.md §6 | Aceita |
| Categorias de mudança isoladas: upstream, correções de build, segurança, privacidade, branding | ARCHITECTURE.md §10 | Aceita |
| Uma build bem-sucedida não é um navegador funcionando; portão de validação antes de qualquer coisa ser chamada de funcional | ARCHITECTURE.md §11; Checklist de validação (este arquivo) | Aceita |
| Adiar a primeira build completa até que branding, segurança e privacidade estejam integrados; níveis de validação V0–V3 | ARCHITECTURE.md §11; Estratégia de validação (este arquivo) | Aceita |
| Decisões da Fase 3a: MPL-2.0, regras de montagem do AutoConfig, staging isolado, nomes internos `librewolf.*` mantidos, fixtures, monitor de recursos | `remilia/README.md`; CONTRIBUTING.md (licença); BUILD.md (monitor de recursos) | Aceita |

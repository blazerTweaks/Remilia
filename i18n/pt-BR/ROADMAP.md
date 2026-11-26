<!-- i18n:nav -->
[English](../../ROADMAP.md) | **Português (Brasil)** | [日本語](../ja/ROADMAP.md) | [Español](../es/ROADMAP.md)
<!-- /i18n:nav -->

<!-- i18n:meta -->
> - **Translation status:** Current
> - **Language:** pt-BR
> - **Original language:** English
> - **Source:** [ROADMAP.md](../../ROADMAP.md)
> - **Source revision:** sha256:7b20e98014332469c687cfb4b31a476e4c2ba61f158587bc6601e5e00c17c184
<!-- /i18n:meta -->

# Roadmap e status

Este arquivo é o registro do projeto de tarefas concluídas, tarefas pendentes,
bloqueios e decisões. Valores de status: `done` (concluído), `in progress` (em
andamento), `todo` (a fazer), `blocked` (bloqueado).

Última atualização: 2026-11-25

## Fase atual: 2 — Base do navegador, etapa 1 (toolchain).

## Regras de trabalho

1. **Categorias de mudança isoladas.** Upstream, correções de build, segurança,
   privacidade e branding ficam em arquivos e patches separados, nunca
   misturados em um mesmo patch ou commit, cada um rastreável e reversível
   individualmente (ARCHITECTURE.md §10, ADR 0004).
2. **Uma build não é um navegador funcionando.** Uma compilação bem-sucedida só
   comprova a infraestrutura de build. Nada é chamado de funcional, e nenhuma
   fase é encerrada, antes que o checklist de validação passe e seus resultados
   sejam registrados (ARCHITECTURE.md §11, ADR 0005).

## Sequência

1. Finalizar o toolchain.
2. Compilar o LibreWolf original, sem modificações do REMILIA.
3. Validar o executável produzido.
4. Registrar os resultados dos testes.
5. Estabelecer a estrutura de patches e configurações próprias do REMILIA.
6. Começar as modificações de branding.
7. Implementar as configurações de segurança e privacidade, em etapas separadas.
8. Validar cada conjunto de modificações individualmente.

As etapas 1–4 são a Fase 2, a etapa 5 é a Fase 3a, a etapa 6 é a Fase 3b, a
etapa 7 corresponde às Fases 4a, 4b e 5, e a etapa 8 é o portão que encerra
cada uma dessas fases.

## Bloqueios e decisões em aberto

| ID | Item | Necessário até | Responsável |
|---|---|---|---|
| B1 | **Domínio do projeto** para o servidor de atualizações, ID de distribuição (`--with-distribution-id`), links de suporte | Fase 3b (branding), Fase 8 (atualizações) | Mantenedor |
| B2 | **Par de chaves de assinatura de atualizações MAR** gerado e guardado offline | Fase 4a; antes de qualquer build pública | Mantenedor |
| B3 | **Chave de API do Safe Browsing**: obter uma ou aceitar a alternativa documentada (SECURITY.md §S3) | Fase 4a | Mantenedor |
| B4 | **Certificado de assinatura de código do Windows (Authenticode).** Sem ele, o SmartScreen exibe avisos no instalador | Fase 8 | Mantenedor |
| B5 | **Licença dos arquivos próprios do REMILIA.** Recomendação: MPL-2.0, que os patches em arquivos MPL já exigem de qualquer forma | Fase 3a | Mantenedor |
| B6 | Instalar o **MozillaBuild** (requer um instalador interativo e UAC) para o caminho de build B | Fase 2 (opcional) | Mantenedor |
| D1 | Mecanismo de busca padrão | Fase 4b | Em aberto |
| D2 | Padrão de limpeza ao fechar (privacidade vs. permanecer conectado) | Fase 4b | Em aberto |
| D3 | Padrão de DoH (desativado vs. escolha na primeira execução) | Fase 4b | Em aberto |
| D4 | Painel de proteção da barra de ferramentas: popup do uBO vs. um painel do REMILIA sobre os dados do uBO | Fase 5 | Em aberto |

## Fase 1 — Pesquisa `done`

- [x] Levantamento do código-fonte do Firefox: o repositório canônico agora é `github.com/mozilla-firefox/firefox` (Git); os tarballs de release são assinados com GPG.
- [x] Levantamento do LibreWolf: `codeberg.org/librewolf/source` (patches, configurações, build) e `bsys6` (empacotamento, compilação cruzada para Windows).
- [x] Requisitos de build do Firefox no Windows (MozillaBuild, `mach bootstrap`, 40 GB+, sem espaços nos caminhos).
- [x] Como o LibreWolf compila os binários para Windows (compilação cruzada com Docker no Debian).
- [x] Integração de extensões: como o LibreWolf instala o uBO; semântica do armazenamento gerenciado do uBO verificada no código-fonte do uBO.
- [x] Revisão da configuração de privacidade do `librewolf.cfg` v8.6 (seções de privacidade, rede, fingerprinting, segurança, extensões e atualizador).
- [x] Licenciamento: MPL-2.0 (Firefox, LibreWolf), GPL-3.0 (uBO), marca registrada do Firefox, considerações sobre obras de fãs de Touhou.
- [x] Modelo de manutenção (ciclo de 4 semanas, chemspills).
- [x] Conjunto de documentação: README, ARCHITECTURE, PRIVACY, SECURITY, BUILD, UPSTREAM, ROADMAP, CONTRIBUTING, ADRs.
- [x] Pins do upstream registrados (`upstream/pins.env`).
- [x] Traduções da documentação (pt-BR, ja, es) com um verificador de sincronização (`i18n/i18n.py`).
- [ ] Não concluído: leitura completa das seções de UI/telemetria/região do `librewolf.cfg` e revisão linha a linha de todos os 68 patches do LibreWolf. Transferido para as Fases 4a/4b.

## Fase 2 — Base do navegador `in progress`

Objetivo: comprovar que a infraestrutura de build produz um executável Windows
válido a partir do **LibreWolf 161.0-1 sem modificações** e verificar esse
executável. Nenhuma mudança do REMILIA é aplicada nesta fase.

### Etapa 1 — Toolchain `in progress`

- [x] Imagem do ambiente de build `build/windows-cross.Dockerfile` (derivada do bsys6, imagem base fixada por digest).
- [x] `scripts/fetch.sh`: tarball do Firefox verificado por GPG contra a chave fixada da Mozilla; LibreWolf, l10n e bsys6 em commits fixados; tarball adulterado rejeitado (testado).
- [x] `scripts/prepare.sh`: cópia limpa → `patch.sh` do LibreWolf (68 patches, 0 fuzz/rejeições) → mozconfig de compilação cruzada para Windows.
- [x] l10n fixada em um commit do `firefox-l10n` da Mozilla (o espelho do LibreWolf retornou HTTP 502; mesmo commit, mesmo conteúdo).
- [ ] `scripts/toolchains.sh`: clang, sysroots, Wine, NSIS e Windows SDK no volume `remilia-mozbuild`.

### Etapa 2 — Compilar o LibreWolf sem modificações `todo`

- [ ] `scripts/build.sh` para Windows x64 (caminho A, compilação cruzada com Docker). Registrar tempo, uso de disco e de RAM.
- [ ] `scripts/package.sh`: `.win64.zip` en-US + sha256 + arquivo de procedência em `dist/`.

### Etapa 3 — Validar o executável `todo`

Executar no Windows 10 x64 (a máquina do mantenedor) com um perfil novo. Cada
verificação é registrada como aprovada, reprovada ou não aplicável, com o motivo.

| Verificação | Como |
|---|---|
| Inicialização | Inicia a partir do pacote descompactado; cria um perfil; sem falhas; `about:support` abre |
| Navegação em sites reais | Uma lista fixa de sites reais (notícias, vídeo, mapas, página de login de webmail, um site do governo, a página pública de um banco brasileiro) carrega e renderiza |
| JavaScript e compatibilidade web | Sites com muito JS funcionam; uma página de testes padrão da plataforma web roda |
| Áudio e vídeo | Reprodução de áudio e vídeo HTML5 (codecs abertos e H.264); anotar o estado de DRM/EME (desativado pela política do LibreWolf) |
| Aceleração gráfica | `about:support` → Gráficos: compositor, WebRender, status da aceleração por GPU |
| Extensões do Firefox | Instalar uma extensão assinada de addons.mozilla.org; ativar, desativar, remover |
| uBlock Origin | Instalado pela política do LibreWolf na primeira execução; bloqueia em uma página de teste de bloqueio de anúncios; o painel abre |
| Multiprocesso | Janelas multiprocesso e Fission em `about:support`; `about:processes` mostra processos de conteúdo separados |
| Sandbox | Níveis de sandbox em `about:support` iguais aos do Firefox 161 oficial na mesma máquina |
| Gerenciamento de perfis | `about:profiles`: criar, alternar e excluir um perfil; os dados persistem após reiniciar, conforme configurado |
| Downloads | Baixar um arquivo; progresso, local, histórico, aviso de arquivo perigoso |
| Atualizações | Não aplicável a esta build: o mozconfig base do LibreWolf tem `--disable-updater`. Coberto na Fase 4a |
| Integridade do pacote | sha256 registrado; o pacote é extraído novamente de forma idêntica; `winchecksec` nos `.exe`/`.dll` (ASLR, DEP, CFG) |

### Etapa 4 — Registrar os resultados `todo`

- [ ] Escrever `tests/results/<date>-librewolf-161.0-1-win64.md` (formato do ADR 0005).
- [ ] Atualizar o BUILD.md com o tempo de build e o uso de recursos medidos, e com os comandos reais.
- [ ] Escolher o caminho oficial de build para releases (ADR).
- [ ] Opcional: caminho B (MozillaBuild nativo, após B6) para depuração.
- [ ] Comparar a `main` do LibreWolf (ed92167b) com a tag `161.0-1` (e2baf325) para entender as mudanças pós-release.

A Fase 2 só é encerrada depois que o mantenedor revisar os resultados registrados.

## Fase 3a — Estrutura de mudanças do REMILIA `todo`

- [ ] Criar `remilia/build-fixes/`, `remilia/security/`, `remilia/privacy/`, `remilia/branding/` à medida que o conteúdo chegar (ADR 0004).
- [ ] `prepare.sh`: aplicar as categorias em ordem fixa; montar o arquivo AutoConfig, o `policies.json` e o `mozconfig` com cabeçalhos por categoria; falhar em prefs/políticas duplicadas; selecionar subconjuntos com `REMILIA_LAYERS`.
- [ ] Lista de exclusões de patches do LibreWolf em `upstream/`, cada uma com um ADR.
- [ ] Verificação: uma árvore preparada sem nenhuma categoria é idêntica à árvore da Fase 2.

## Fase 3b — Branding `todo`

Categoria: apenas branding. Nenhuma mudança de privacidade ou segurança nesta fase.

- [ ] Conceito do logo: par simétrico de asas de morcego em volta de um losango escarlate. SVG mestre, testado em 16/32/64/128/256 px.
- [ ] Variantes: colorida, monocromática, para fundo claro, para fundo escuro, transparente.
- [ ] Geração de `.ico` para Windows; bitmaps do instalador.
- [ ] Diretório de branding substituindo `--with-branding`; nome do aplicativo, remoting name, diretório de perfil, nome do arquivo cfg (veja os pontos de contato em UPSTREAM.md).
- [ ] Tema do navegador com a paleta do briefing (CSS do Firefox, sem framework).
- [ ] Página inicial (local, sem conteúdo remoto, todos os elementos opcionais).
- [ ] Portão: checklist de validação apenas com branding; resultados registrados.

## Fase 4a — Segurança `todo`

Categoria: apenas segurança.

- [ ] Assinatura de extensões obrigatória (SECURITY.md S1).
- [ ] Identidade do atualizador do REMILIA: chaves MAR, host de atualização (S2; requer B1, B2).
- [ ] Decisão sobre o Safe Browsing (S3, B3) e domínios restritos para extensões (S4).
- [ ] Portão: checklist de validação apenas com segurança e depois com todas as categorias até aqui; resultados registrados.

## Fase 4b — Privacidade `todo`

Categoria: apenas privacidade.

- [ ] Prefs de privacidade contendo apenas as divergências documentadas; todo o resto herdado do LibreWolf.
- [ ] Resolver D1–D3.
- [ ] Captura de pacotes de um perfil novo: listar toda conexão de saída em PRIVACY.md.
- [ ] Interface de configurações: explicações claras, expondo os efeitos colaterais e as opções do RFP.
- [ ] Portão: checklist de validação apenas com privacidade e depois com todas as categorias; resultados registrados.

## Fase 5 — Bloqueio de anúncios `todo`

Categoria: privacidade.

- [ ] Fixar o uBO (xpi assinado pela AMO, SHA-256) e incluí-lo em `distribution/extensions/`.
- [ ] `assets.json` do REMILIA (padrão do uBO mais `spa-1`, os acréscimos do LibreWolf, listas brasileiras em avaliação); entregá-lo via `assetsBootstrapLocation`.
- [ ] Validar o comportamento offline na primeira execução e as atualizações pela AMO.
- [ ] Resolver D4; construir o painel apenas sobre dados reais do uBO.
- [ ] Testar em páginas de teste de bloqueio de anúncios consagradas; registrar os resultados com honestidade.
- [ ] Portão: checklist de validação; resultados registrados.

## Fase 6 — Experiência do usuário `todo`
Barra de ferramentas, abas, barra de endereços, downloads, favoritos,
configurações. Em grande parte são recursos já existentes no Firefox; o trabalho
do REMILIA é tema (branding) e configuração (privacidade/segurança), registrados
por categoria.

## Fase 7 — Segurança e testes `todo`
BrowserLeaks, EFF Cover Your Tracks, testes de vazamento de DNS e WebRTC,
suíte de compatibilidade, profiling de desempenho. Os resultados vão para
`tests/results/` com datas e versões.

## Fase 8 — Distribuição `todo`
Instalador NSIS e zip portátil (ambos já existem no bsys6 do LibreWolf),
pipeline de atualizações MAR, servidor de atualizações, documentação de
release. Depende de B1, B2 e B4.

## Registro de decisões

| ADR | Decisão | Status |
|---|---|---|
| 0001 | Camada sobre uma release fixada do LibreWolf, sobre o Firefox Release | Aceita |
| 0002 | Herdar o `librewolf.cfg`; divergências somente com motivos por escrito | Aceita |
| 0003 | Incluir o xpi assinado do uBO; padrões via `assetsBootstrapLocation`, não `toOverwrite` | Aceita |
| 0004 | Categorias de mudança isoladas: upstream, correções de build, segurança, privacidade, branding | Aceita |
| 0005 | Uma build bem-sucedida não é um navegador funcionando; portão de validação por fase | Aceita |

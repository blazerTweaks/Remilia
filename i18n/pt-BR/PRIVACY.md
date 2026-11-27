<!-- i18n:nav -->
[English](../../PRIVACY.md) | **Português (Brasil)** | [日本語](../ja/PRIVACY.md) | [Español](../es/PRIVACY.md)
<!-- /i18n:nav -->

<!-- i18n:meta -->
> - **Translation status:** Current
> - **Language:** pt-BR
> - **Original language:** English
> - **Source:** [PRIVACY.md](../../PRIVACY.md)
> - **Source revision:** sha256:5a9a65b92947c44c41f46f5ae265e99cac41daa6cbc2144cd03106131502a46c
<!-- /i18n:meta -->

# Remilia Browser — Privacidade

Status: **apenas design.** Nada neste documento foi compilado ou testado ainda.
Cada item tem um status: `planned` (planejado), `implemented` (implementado),
`verified` (testado, com resultados em `tests/`). Hoje, todos os itens estão
como `planned`.

## Princípios

1. **Mecanismos nativos em vez de código próprio.** O Firefox já inclui
   Proteção Total de Cookies, ETP, RFP, Modo Somente HTTPS e DoH. O Remilia
   apenas os configura.
2. **Herdar do LibreWolf por padrão.** Qualquer divergência em relação ao
   `librewolf.cfg` precisa de uma justificativa escrita, porque toda divergência
   é trabalho de manutenção e pode tornar os usuários do Remilia mais
   distinguíveis dentro da população maior do LibreWolf.
3. **Quebra de sites precisa trazer ganho de privacidade.** Uma configuração
   que quebra sites sem ganho significativo de privacidade não é ativada por
   padrão.
4. **Sem exageros.** O Remilia reduz a superfície de rastreamento e de
   fingerprinting. Ele não torna ninguém anônimo. O DoH não esconde quais sites
   você visita do provedor de DoH, nem dos operadores dos sites, nem de quem
   observa o SNI do TLS, a menos que o ECH seja usado.

## Contra o que o Remilia protege — e contra o que não protege

| Protege (reduz) | **Não** protege contra |
|---|---|
| Rastreamento entre sites por cookies e armazenamento | Seu provedor de internet / a rede vendo os IPs de destino |
| Domínios conhecidos de rastreadores e anúncios | O site que você visita identificar você depois do login |
| Muitos vetores passivos de fingerprinting | Um adversário determinado e direcionado |
| Parâmetros de rastreamento na URL de links | Malware no seu computador |
| Espionagem de DNS na rede local (quando o DoH está ativado) | O provedor de DoH vendo suas consultas DNS |
| Telemetria e coleta de dados em segundo plano pelo navegador | Qualquer coisa que você envie voluntariamente a sites |

## Configuração de base (do `librewolf.cfg` v8.6 do LibreWolf, Firefox 161)

Legenda — **Manter**: herdar do LibreWolf. **Alterar**: o Remilia diverge.
**Avaliar**: decidir na Fase 4, com testes.

### Rastreamento e cookies

| Configuração | LibreWolf | Remilia | Observações |
|---|---|---|---|
| `browser.contentblocking.category` | `strict` | Manter | ETP Rigoroso: Proteção Total de Cookies, listas rigorosas, shims do SmartBlock, remoção de parâmetros de consulta. |
| Lista de remoção de parâmetros de consulta | lista do Brave | Manter | Remove `fbclid`, `gclid` etc. |
| `privacy.sanitize.sanitizeOnShutdown` | `true` (cookies/cache apagados ao sair) | **Avaliar** | Privacidade forte, mas desconecta o usuário de todos os sites a cada reinício. Proposta: manter ativado e dar destaque às exceções por site nas configurações e no onboarding. |
| Cache em disco | desativado | Manter | Cache somente em memória. Custa um pouco de desempenho em visitas repetidas. |
| `browser.formfill.enable` | `false` | Manter | |
| Proteção contra rastreamento por redirecionamento (bounce tracking) | padrão do Firefox | **Avaliar** | Confirmar o estado no ETP Rigoroso do Fx 161. |
| Global Privacy Control | ativado | Manter | |

### Fingerprinting

| Configuração | LibreWolf | Remilia | Observações |
|---|---|---|---|
| `privacy.resistFingerprinting` | `true` | Manter | Compartilhado com Tor/Mullvad/LibreWolf, de modo que os usuários se misturam a um grupo maior. Efeitos colaterais: fuso horário informado como UTC, idioma informado como `en-US`, tema claro informado aos sites, tamanho de janela arredondado. Todos expostos como opções claras nas configurações. |
| Letterboxing | desativado | Manter | |
| WebGL | ativado (protegido pelo RFP) | Manter | Desativar o WebGL quebra mapas e 3D, e essa escolha em si pode ser usada para fingerprinting. |
| WebGPU | desativado | Manter | |
| Randomização própria | — | **Nunca** | Tornaria os usuários do Remilia uma população pequena e distinta. |

Não alegamos: proteção completa contra fingerprinting. A enumeração de fontes,
o tamanho da tela e os detalhes de hardware são reduzidos pelo RFP, não
eliminados.

### Telemetria e conexões em segundo plano

| Item | Remilia |
|---|---|
| Telemetria | Desativada em tempo de compilação (`MOZ_TELEMETRY_REPORTING` vazio) **e** por política. |
| Estudos / experimentos Normandy / Nimbus | Desativados (`DisableFirefoxStudies`, `DisableRemoteImprovements`). |
| Pocket / atalhos patrocinados / sugestões patrocinadas / Firefox Suggest | Desativados. |
| Relator de falhas | **Não compilado** (os servidores de falhas da Mozilla não aceitam builds de forks). Nenhum dado de falha é transmitido. Uma futura opção, opt-in, de dump de falhas apenas local é um item do roadmap, não um recurso. |
| Default browser agent | Não compilado. |
| Recursos de IA (chatbot na barra lateral, grupos de abas inteligentes etc.) | Bloqueados por política; backend da OpenAI removido do código-fonte (herdado). |

Contatos de rede ainda esperados, a serem listados com exatidão na Fase 4 com
uma captura de pacotes: Remote Settings (revogação de certificados/CRLite,
listas de bloqueio de segurança), atualizações de extensões da AMO,
atualizações das listas de filtros do uBO, verificação de atualizações do
Remilia. Nenhum deles envia o histórico de navegação.

### DNS e rede

| Configuração | LibreWolf | Remilia | Observações |
|---|---|---|---|
| DoH (`network.trr.mode`) | `5` (desativado) | **Avaliar** | Desativado significa que o resolvedor do sistema operacional é usado. Ativado (modo 2/3) transfere a confiança para o provedor. Proposta: desativado por padrão, com uma escolha oferecida na primeira execução. |
| Lista de provedores de DoH | Quad9 ×2, LibreDNS ×2, Wikimedia, DNS4All | Manter + avaliar a inclusão de um provedor adequado para o Brasil | Nenhum provedor é imposto. |
| Pré-busca de DNS / pré-busca de links / conexões especulativas | desativados | Manter | |
| `network.proxy.socks_remote_dns` | `true` | Manter | O DNS passa pelo proxy SOCKS5 quando um estiver configurado. |
| WebRTC | ativado; o mDNS oculta o IP local; somente via proxy quando há proxy | Manter | Desativar o WebRTC quebra chamadas e pode ser usado para fingerprinting. Haverá uma opção nas configurações para desativá-lo. |
| Corte do referer entre origens | `XOriginTrimmingPolicy=2` | Manter | |
| Modo Somente HTTPS | ativado (política) | Manter | |
| `beacon.enabled` | `false` | Manter | |

## Busca

- Nenhum provedor de busca padrão é imposto. Candidatos oferecidos:
  DuckDuckGo, Brave Search, Startpage, Mojeek (herdado), Google, Bing. A escolha
  padrão ainda será decidida (ROADMAP, decisão em aberto D1).
- As sugestões de busca vêm **desativadas** por padrão. Quando ativadas, o que
  é digitado é enviado ao provedor escolhido; a configuração diz isso em
  linguagem clara.
- A barra de endereços não envia consultas a lugar nenhum até que o usuário as
  confirme.

## Dados que o Remilia nunca coleta

O Remilia (o projeto) não opera nenhuma analítica, nenhuma conta, nenhum
serviço de sincronização. A verificação de atualizações envia a requisição que
o formato do atualizador da Mozilla exige (versão, alvo da build, canal). Essa
requisição será documentada em [SECURITY.md](SECURITY.md) quando o servidor de
atualizações existir.

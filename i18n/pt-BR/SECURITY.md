<!-- i18n:nav -->
[English](../../SECURITY.md) | **Português (Brasil)** | [日本語](../ja/SECURITY.md) | [Español](../es/SECURITY.md)
<!-- /i18n:nav -->

<!-- i18n:meta -->
> - **Translation status:** Current
> - **Language:** pt-BR
> - **Original language:** English
> - **Source:** [SECURITY.md](../../SECURITY.md)
> - **Source revision:** sha256:ab8ffc730db55bc9fd30040ac1cde236b667f95b8bba14b8d107b4f169263334
<!-- /i18n:meta -->

# Remilia Browser — Segurança

Status: **apenas design.** Ainda não existe nenhuma build do Remilia.

Privacidade e segurança são coisas diferentes. Uma configuração de privacidade
nunca deve enfraquecer a arquitetura de segurança do Firefox. Este arquivo
lista toda modificação relevante para a segurança que o Remilia faz ou herda,
com sua justificativa.

## Como relatar vulnerabilidades

Até que exista um canal dedicado, relate de forma privada ao mantenedor. Não
abra issues públicas para vulnerabilidades. Vulnerabilidades do motor pertencem
ao upstream (Bugzilla da Mozilla, grupo de segurança); o Remilia distribuirá a
correção quando a versão do upstream que a contém for lançada.

## Preservado sem alterações

- Arquitetura multiprocesso do Gecko e **Fission** (isolamento de sites).
- **Sandbox de processos de conteúdo do Windows** (`--enable-sandbox`, herdado
  do mozconfig de Windows do LibreWolf). Nunca reduzida para economizar
  memória.
- Validação de certificados via NSS. **Nunca desativada.** Nenhuma
  implementação própria de TLS ou criptografia.
- Bloqueio de conteúdo misto, HSTS, pinning estático HPKP.
- Verificação de assinatura de extensões (veja abaixo — esta é uma diferença
  deliberada em relação ao LibreWolf).
- Hardening de build: `--enable-hardening`, `--enable-stl-hardening`,
  `-ftrivial-auto-var-init=zero`, `-fwrapv` (herdados).

## Hardening herdado do LibreWolf — mantido

| Configuração | Efeito |
|---|---|
| `security.pki.crlite_mode = 2` | Revogação por CRLite aplicada localmente. |
| `security.OCSP.enabled = 0` | Nenhuma requisição OCSP (privacidade); depende do CRLite. |
| `security.cert_pinning.enforcement_level = 2` | Pinning rigoroso. Pode conflitar com a interceptação de TLS de antivírus — documentado na seção de solução de problemas. |
| `security.ssl.require_safe_negotiation = true` | Rejeita servidores sem RFC 5746. Quebra rara. |
| `security.tls.enable_0rtt_data = false` | Sem 0-RTT do TLS 1.3 (risco de replay). |
| `security.enterprise_roots.enabled = false` | Raízes do repositório de certificados do Windows não são confiadas automaticamente. |
| `network.IDN_show_punycode = true` | Proteção contra homógrafos. |
| `pdfjs.enableScripting = false` | Sem JS no visualizador de PDF. |

## Divergências do Remilia em relação ao LibreWolf (motivadas por segurança)

| # | LibreWolf | Remilia (planejado) | Motivo |
|---|---|---|---|
| S1 | `MOZ_REQUIRE_SIGNING=` (vazio): extensões não assinadas podem ser ativadas por uma pref | Manter o padrão da Mozilla: assinatura **obrigatória**, sem possibilidade de anulação por pref | Impede a instalação de extensões adulteradas ou não assinadas. Desenvolvedores ainda podem carregar complementos temporários pelo `about:debugging`. |
| S2 | Inclui as chaves públicas de assinatura MAR do LibreWolf; host de atualização `update.librewolf.net` | Chaves MAR e host de atualização próprios do Remilia | Um binário do Remilia deve aceitar apenas atualizações assinadas pelo Remilia. Obrigatório antes de qualquer build pública. |
| S3 | Safe Browsing totalmente desativado | **Avaliar — veja abaixo** | Os requisitos do projeto pedem proteção de Safe Browsing. |
| S4 | `extensions.webextensions.restrictedDomains = ""` (extensões podem rodar em addons.mozilla.org etc.) | **Avaliar:** restaurar o padrão do Firefox | A lista de domínios restritos impede que uma extensão comprometida manipule as páginas da loja de complementos. |
| S5 | No Windows, o AutoConfig também carrega `%USERPROFILE%\.librewolf\librewolf.overrides.cfg`, então sobreposições escritas para um LibreWolf instalado também valem | Lê apenas `%USERPROFILE%\.remilia\librewolf.overrides.cfg` (implementado, `static-verified`) | O arquivo de outro programa não deve alterar as prefs do Remilia, inclusive as de segurança e privacidade. |

### S3 — Safe Browsing: problema em aberto

O Safe Browsing do Firefox baixa listas de prefixos de hash do Google e
verifica as URLs localmente, enviando apenas prefixos de hash quando há uma
correspondência parcial. Ele exige uma **chave de API do Google Safe Browsing
compilada na build**. A chave da Mozilla não pode ser usada por forks. O Google
restringe a API Safe Browsing ao uso não comercial, e o uso comercial exige a
Web Risk API, que é paga.

Opções, a serem decididas na Fase 4:

1. Obter uma chave de API Safe Browsing para o Remilia (projeto não comercial) e
   ativar as verificações das listas de phishing/malware. As verificações
   *remotas* de reputação de downloads
   (`browser.safebrowsing.downloads.remote.*`) enviam metadados dos arquivos ao
   Google e continuam **desativadas**.
2. Se não for possível obter uma chave: manter o Safe Browsing desativado e
   contar com as listas de malware/phishing do uBO (`urlhaus-1`,
   `curben-phishing`, ativadas por padrão), além de um resolvedor DoH opcional
   com bloqueio de malware. Isso deve ser descrito honestamente como mais fraco
   que o Safe Browsing.

As proteções locais de download (avisos de tipos de arquivo perigosos,
Mark-of-the-Web) independem do Safe Browsing e continuam ativadas.

## Cadeia de suprimentos

- Código-fonte do Firefox: tarball verificado por GPG, de `archive.mozilla.org`.
- Código-fonte do LibreWolf: hash de commit fixado em `upstream/pins.env`.
- uBlock Origin: `.xpi` assinado pela AMO, com versão e SHA-256 fixados.
- Toolchains de build: obtidas pelo `mach` (artefatos do Taskcluster da Mozilla)
  ou por imagens de contêiner fixadas.
- As chaves de assinatura de release (MAR, Authenticode) nunca são commitadas
  neste repositório.

## Política de atualizações de segurança

As versões de segurança do Firefox são a prioridade máxima. Meta: uma build do
Remilia publicada em até 72 horas após a versão correspondente do LibreWolf.
Cada nota de versão lista os Mozilla Security Advisories (MFSA) incluídos.

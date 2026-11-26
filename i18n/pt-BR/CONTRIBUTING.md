<!-- i18n:nav -->
[English](../../CONTRIBUTING.md) | **Português (Brasil)** | [日本語](../ja/CONTRIBUTING.md) | [Español](../es/CONTRIBUTING.md)
<!-- /i18n:nav -->

<!-- i18n:meta -->
> - **Translation status:** Current
> - **Language:** pt-BR
> - **Original language:** English
> - **Source:** [CONTRIBUTING.md](../../CONTRIBUTING.md)
> - **Source revision:** sha256:2264196e465502b70acd3022adfb1275a9317dc9a2ceca7b8788f556fea90b67
<!-- /i18n:meta -->

# Contribuindo com o REMILIA

## Regras básicas

1. **Nada de funcionalidade falsa.** Nada de mockups no lugar de recursos, nem
   de estatísticas de mentira. Se algo não está implementado, a documentação diz
   isso.
2. **Nunca enfraqueça a segurança por conveniência ou por benchmarks.**
   Validação de certificados, sandbox, Fission e assinatura de extensões não são
   negociáveis.
3. **Toda mudança de privacidade ou segurança é documentada** em PRIVACY.md ou
   SECURITY.md, com o motivo, na mesma alteração.
4. **Upstream primeiro.** Prefira prefs, depois políticas, depois sobreposição
   de arquivos, depois patches de código-fonte. Veja UPSTREAM.md.
5. **Nenhuma nova dependência ou framework** sem um motivo concreto registrado
   em um ADR. A interface do navegador usa as tecnologias de front-end do
   próprio Firefox.
6. **Nunca invente resultados de testes ou benchmarks.** Registre o que foi
   executado, em qual build e em que data, e o que falhou.

## Fazendo uma alteração

- Commits pequenos, com uma preocupação e uma categoria cada (upstream,
  correções de build, segurança, privacidade, branding; ARCHITECTURE.md §10). A
  mensagem explica o *porquê*.
- Novo patch, pref ou política do REMILIA: coloque-o no diretório da sua única
  categoria, `remilia/<category>/`. Um patch vai para `patches/` e `series`
  dessa categoria, com um cabeçalho (categoria, propósito, arquivos e prefs
  afetados, se pode ir para o upstream, efeito de revertê-lo). Uma mudança que
  abrange duas categorias é dividida em duas.
- Escolhas de nível de arquitetura ganham um registro de decisão de arquitetura
  (ADR): Contexto, Decisão, Consequências, Status.
- Atualize o ROADMAP.md quando o status de uma tarefa mudar.

## Verificando

Depois de qualquer mudança que afete a build: uma build completa e, em seguida,
a checklist de testes de fumaça do BUILD.md ("Verificando uma build"). Depois de
uma mudança em pref de privacidade: execute novamente os testes relevantes em
`tests/` e atualize os resultados.

Uma build bem-sucedida não é um navegador funcionando. Antes de chamar qualquer
build de funcional, execute o checklist de validação (ROADMAP.md, Fase 2, etapa
3) e registre os resultados em `tests/results/` (ADR 0005).

## Licenciamento

Contribuições que alteram arquivos do Firefox ou do LibreWolf são MPL-2.0. A
licença dos arquivos originais do REMILIA está pendente (ROADMAP B5).

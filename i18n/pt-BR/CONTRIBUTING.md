<!-- i18n:nav -->
[English](../../CONTRIBUTING.md) | **Português (Brasil)** | [日本語](../ja/CONTRIBUTING.md) | [Español](../es/CONTRIBUTING.md)
<!-- /i18n:nav -->

<!-- i18n:meta -->
> - **Translation status:** Current
> - **Language:** pt-BR
> - **Original language:** English
> - **Source:** [CONTRIBUTING.md](../../CONTRIBUTING.md)
> - **Source revision:** sha256:d2159a306b0c86d12c64fd3d5e3d306ebc924a3b7f6fa3b887e39d72b6f7e428
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
5. **Nenhuma nova dependência ou framework** sem um motivo concreto, explicado
   na própria mudança e aceito pelo mantenedor. A interface do navegador usa as tecnologias de front-end do
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
  abrange duas categorias é dividida em duas. Os formatos exatos estão em
  `remilia/README.md`.
- Um valor que sobrescreve o LibreWolf ganha uma entrada no `deviations.tsv`
  da categoria e o seu motivo no PRIVACY.md ou no SECURITY.md.
- Escolhas de nível de arquitetura são apresentadas ao mantenedor antes da
  implementação, com contexto, decisão e consequências. Depois de adotadas, o
  efeito delas é descrito no ARCHITECTURE.md.
- Atualize o ROADMAP.md quando o status de uma tarefa mudar.

## Verificando

A cada mudança: as verificações estáticas (V0 no ROADMAP.md, "Estratégia de
validação"). Antes de uma fase ser encerrada: as verificações de árvore (V1).

```sh
python scripts/remilia_layers.py check        # V0: categories, duplicates, deviations
python -m unittest discover -s tests/layers   # V0: tests of the category tool
python -m unittest discover -s tests/validation  # V0: tests of the validation harness
python i18n/i18n.py check                     # V0: documentation translations
./scripts/docker.sh verify                    # V1: staging trees, no compilation
```

Não é preciso uma build completa depois de cada mudança; a primeira vem quando
branding, segurança e privacidade estiverem integrados. Se uma
mudança só puder ser validada compilando, explique o motivo antes de iniciar a
build.

Uma build bem-sucedida não é um navegador funcionando. Antes de chamar qualquer
build de funcional, execute o
[checklist de validação](ROADMAP.md#checklist-de-validação) e registre os
resultados em `internal/evidence/<date>-<build>/` (uma pasta local ignorada
pelo Git; os registros de validação nunca entram em commits). Um trabalho
aprovado apenas em V0 e
V1 fica `static-verified`, não `done`.

## Licenciamento

Os arquivos originais do próprio REMILIA são MPL-2.0 ([LICENSE](../../LICENSE)).
Contribuições que alteram arquivos do Firefox ou do LibreWolf também são
MPL-2.0. Os arquivos herdados do Firefox, do LibreWolf e de outros componentes
de terceiros mantêm suas próprias licenças e avisos; não os altere.

# docgit

*Controle de versão estilo Git para Google Docs, com commits com mensagem e branches. CLI em Python, open-source sob licença MIT.*

**Status:** especificação v1.2. Todas as decisões estão no texto e não há questões em aberto.

## 1. Problema

O histórico do Google Docs salva a cada mudança pequena, não permite checkpoints com mensagem e não tem branches. Quem mantém várias versões de um mesmo documento, como um currículo para vagas de back-end, de full-stack e uma versão geral, acaba duplicando arquivos e perdendo o controle de qual é a versão final.

## 2. Objetivos e não-objetivos

**Objetivos da v0.1**

- Salvar checkpoints (commits) com mensagem, quando o usuário quiser.
- Criar e alternar entre branches de um mesmo documento.
- Trabalhar no Google Docs como área de trabalho. Os comandos são executados pelo terminal, com o `docgit`.
- Manter o link do Google Doc estável: existe um único doc por repositório, e o conteúdo muda conforme a branch ativa.
- Rodar localmente, sem servidor, com os dados na máquina do usuário.
- Núcleo testável, sem dependência do Google, para reaproveitar em outros adaptadores no futuro.

**Não-objetivos da v0.1**

- Merge entre branches, diff entre commits, tags e stash.
- Interface gráfica ou web, e hospedagem.
- Colaboração entre pessoas, remotes (push/pull) e resolução de conflitos.
- Fidelidade de 100% da formatação em todos os casos.

## 3. Escopo da v0.1

| Funcionalidade | Incluída |
| --- | --- |
| Inicializar um repositório ligado a um Google Doc | Sim |
| Autenticar no Google (`auth`) | Sim |
| Commit com mensagem | Sim |
| Status (alterações não commitadas) | Sim |
| Histórico da branch (`log`) | Sim |
| Criar e listar branches | Sim |
| Trocar de branch | Sim |
| Restaurar um commit antigo, criando um novo commit (`restore`) | Sim |
| Exportar um snapshot como .docx ou PDF | Opcional |
| Merge, diff, tags, stash | Não |

## 4. Onde ficam os dados

**Decisão:** o Google Docs é o espaço de trabalho. Os commits são snapshots .docx guardados localmente.

Alternativas descartadas:

- **Cópias do documento no Drive:** enchem o Drive do usuário com arquivos do app e misturam dados do app com os do usuário.
- **Só arquivos locais em Markdown ou .docx, sem Google:** perde a integração, que é requisito.

Consequência: todo commit é uma exportação do Google, e todo checkout é uma substituição do conteúdo do doc. A fidelidade dessa ida e volta é o maior risco técnico e precisa ser validada no spike (seção 14).

## 5. Estrutura local: a pasta `.docgit/`

**Decisão:** a pasta `.docgit/` é criada no diretório onde `docgit init` é executado, como o `.git` do Git. Não existe diretório global de dados.

```
.docgit/
  config.json          # id do Google Doc, nome do repositório, versão do formato
  HEAD                 # nome da branch ativa, ex.: main
  refs/heads/<branch>  # hash do último commit da branch
  commits/<hash>.json  # metadados do commit
  blobs/<hash>.docx    # snapshots, endereçados pelo hash do conteúdo normalizado
```

Regras:

- Commits são imutáveis. Uma branch é apenas um ponteiro para um commit.
- Criar branch é criar um arquivo em `refs/heads/`, sem copiar conteúdo.
- Blobs são deduplicados pelo hash.
- A branch inicial é `main`, e o `init` cria o commit inicial com o conteúdo atual do doc.
- Um repositório corresponde a um documento. Vários documentos exigem vários diretórios.
- A pasta `.docgit/` pode ser versionada em um repositório privado, como backup.

## 6. Modelo de commit

```json
{
  "hash": "sha256 do JSON canônico, sem o próprio campo hash",
  "parent": "hash do commit anterior, ou null no primeiro",
  "blob": "hash do conteúdo normalizado",
  "message": "Ajusta resumo para vaga de back-end",
  "author": "nome <email>",
  "timestamp": "2026-11-12T14:30:00Z"
}
```

## 7. Comandos da CLI

| Comando | O que faz |
| --- | --- |
| `docgit auth` | Faz login no Google pelo navegador (OAuth) |
| `docgit init <url-ou-id-do-doc>` | Cria `.docgit/` no diretório atual, liga ao doc e cria o commit inicial na `main` |
| `docgit status` | Mostra a branch ativa e se o doc tem alterações não commitadas |
| `docgit commit -m "mensagem"` | Exporta o doc e cria um commit na branch ativa |
| `docgit log` | Lista os commits da branch ativa |
| `docgit branch` | Lista as branches e marca a ativa |
| `docgit branch <nome> [commit]` | Cria uma branch a partir do commit atual ou do informado |
| `docgit checkout <branch>` | Troca de branch e substitui o conteúdo do doc pelo último commit dela |
| `docgit checkout --force <branch>` | Igual ao anterior, mas descarta as alterações não commitadas do doc |
| `docgit restore <commit>` | Substitui o conteúdo do doc pelo de um commit antigo e cria um novo commit na branch ativa |

## 8. Fluxos

**Commit:** exporta o doc como .docx pela Drive API, normaliza (seção 9) e calcula o hash. Se for igual ao do último commit da branch, informa "nada para commitar" e para. Caso contrário, grava o blob, grava o commit e avança o ponteiro da branch.

**Status:** compara o `modifiedTime` do doc com o registrado no último commit ou checkout. Só exporta e compara o hash se o documento tiver mudado.

**Checkout:** verifica alterações não commitadas no doc. Se houver, a CLI recusa a operação e orienta o usuário a fazer uma de duas coisas: rodar `docgit commit` antes, ou usar `--force`, que descarta as alterações não commitadas. Sem `--force`, nada é perdido. Com `--force`, as alterações feitas no Google Docs desde o último commit são perdidas, e a CLI deve avisar isso na saída. Depois, lê o blob do último commit da branch de destino, substitui o conteúdo do doc (seção 10) e atualiza o HEAD.

**Restore:** igual ao checkout, mas o conteúdo vem de um commit antigo, e o resultado vira um novo commit na branch ativa. Segue a mesma regra de alterações não commitadas.

## 9. Normalização do .docx

Exportar o mesmo documento duas vezes pode gerar arquivos com bytes diferentes, por causa de metadados. Sem tratamento, o status acusaria alterações o tempo todo.

A normalização abre o zip (`zipfile`), remove ou fixa campos voláteis (como `docProps/core.xml`), ordena as entradas e recompacta de forma determinística antes de calcular o hash. Se não bastar, o plano B é calcular o hash apenas de `word/document.xml` e dos estilos. Isso será validado no spike.

## 10. Integração com o Google

**Autenticação**

- OAuth para aplicativo instalado (loopback com PKCE), via `google-auth-oauthlib`.
- Cada usuário usa as próprias credenciais do Google Cloud: o arquivo `credentials.json`, do tipo "App para computador". Isso evita a verificação do app pelo Google.
- Escopo: `https://www.googleapis.com/auth/drive`. O escopo `drive.file` foi descartado, porque não dá acesso a um documento existente em uma CLI. Passar a URL não basta: a API responde 404.
- O impacto de privacidade é que o app enxerga todos os arquivos do Drive do usuário. O README deve explicar isso.
- Credenciais em `~/.config/docgit/credentials.json` e token em `~/.config/docgit/token.json`, com permissão restrita ao usuário. Nenhum dos dois vai para o repositório.
- Em modo de teste, o refresh token expira em 7 dias. Para uso pessoal, o app pode ser publicado ("In production") sem verificação, com aviso de app não verificado no login. O README documenta as duas opções.

**APIs**

- Google Drive API (obrigatória): `files.export` para exportar em .docx, `files.update` no mesmo `fileId` para substituir o conteúdo mantendo link e permissões, e `files.get` para `modifiedTime` e `headRevisionId`.
- Google Docs API (ativada, reservada): usada apenas no plano B, se `files.update` não preservar o documento. Nesse caso, o conteúdo é inserido via `batchUpdate`, com perda de fidelidade.

## 11. Arquitetura

**Stack:** Python 3.11+, `typer` para a CLI, `google-api-python-client` e `google-auth-oauthlib`, `zipfile` da biblioteca padrão, `pytest` para testes, `ruff` para lint e formatação, `pyproject.toml` para empacotamento.

**Estrutura**

```
src/docgit/
  core/     # commits, branches, HEAD, hash, armazenamento; sem dependência do Google
  gdocs/    # adaptador: implementa DocumentProvider com a Drive API
  cli/      # comandos e saída no terminal
tests/
```

**Contrato entre núcleo e adaptador**

```python
class DocumentProvider(Protocol):
    def export_docx(self) -> bytes: ...
    def replace_content(self, docx: bytes) -> None: ...
    def modified_time(self) -> str: ...
```

O núcleo conhece só essa interface. Os testes usam um provider falso em memória, sem rede.

**Distribuição:** publicação no PyPI como `docgit`, com instalação via `pipx install docgit`.

## 12. Decisões de projeto

- **Nome:** `docgit`. Disponível no PyPI e no GitHub, verificado.
- **Licença:** MIT.
- **Checkout com alterações não commitadas:** a CLI recusa a operação e pede commit ou `--force`. O `--force` descarta as alterações, e a CLI avisa antes (seção 8).

Não há questões em aberto nesta versão. Mudanças futuras de escopo entram como nova revisão desta spec.

## 13. Testes

- **Unitários (núcleo):** criação de commits, ponteiros de branch, deduplicação de blobs, hash determinístico, recusa de checkout com alterações pendentes, `--force` descartando alterações, e restore.
- **Integração (CLI com provider falso):** fluxo completo de init, commit, branch, checkout e log.
- **Manual:** roteiro com um Google Doc real, documentado no repositório. Testes contra o Google ficam fora do CI, porque exigem credenciais.

## 14. Spike (antes da CLI)

Script descartável, validado com um currículo de teste num Google Doc. O spike só avança se os quatro critérios passarem:

1. Autenticação com o escopo `drive` e token salvo.
2. `files.export` em .docx preserva fontes, margens, links, listas e colunas de um currículo real.
3. `files.update` mantém o `fileId`, o link e a formatação. Se não mantiver, usa-se o plano B.
4. Exportações consecutivas sem edição geram o mesmo hash após normalização.

## 15. Plano de execução

**Fase 0, preparação (usuário):** Google Cloud configurado (concluído), `credentials.json` em `~/.config/docgit/`, currículo de teste em Google Doc.

**Fase 1, esqueleto (agente):** estrutura em `src/docgit/`, `pyproject.toml`, `ruff`, `pytest`, `.gitignore`, `LICENSE` (MIT) e README mínimo. Critério: `pip install -e .` funciona e `docgit --help` lista os comandos.

**Fase 2, núcleo sem Google (agente):** hash, blobs, commits, refs e HEAD. `init`, `commit`, `log`, `branch` e `checkout` contra o provider em memória. Critério: testes unitários da seção 13 passando.

**Fase 3, spike com o Google (conjunto):** adaptador `gdocs` executado contra o currículo de teste. Critério: os quatro itens da seção 14.

**Fase 4, integração (agente):** ligar `gdocs` à CLI, com `auth`, `init`, `commit` e `checkout` de ponta a ponta. Critério: roteiro manual da seção 13 executado.

**Fase 5, portfólio:** README com GIF do terminal, `docs/decisoes.md`, badge de CI e publicação no PyPI.

## 16. Entregáveis para o portfólio

- README com o problema, o GIF do fluxo e as decisões de arquitetura.
- `docs/decisoes.md` com as decisões e limitações conhecidas, como a escolha de snapshots .docx em vez de cópias no Drive.
- Arquivo `LICENSE` com a licença MIT.
- Badge de CI e cobertura do núcleo.
- Publicação no PyPI.

## 17. Roadmap após a v0.1

- **v0.2:** diff entre commits (algoritmo de Myers) e status detalhado.
- **v0.3:** merge de três vias para texto, com detecção de conflito.
- **v0.4:** tags, stash e interface web local.
- **Depois:** versão web hospedada com modo demo, e adaptador para arquivos locais.

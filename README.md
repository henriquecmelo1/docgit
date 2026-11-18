# docgit

Controle de versão estilo Git para Google Docs, com commits com mensagem,
branches e snapshots locais em `.docx`.

## Visão geral

O Google Docs tem histórico de versões, mas ele é linear, automático e difícil
de organizar: não dá para dizer "esta é a versão que enviei para a vaga X" ou
manter variações paralelas do mesmo documento com clareza. O docgit adiciona
essa camada que falta.

**O Google Docs continua sendo o lugar de edição.** O docgit não é um editor
nem tenta substituir a interface do Google Docs. Ele cuida apenas do
versionamento:

- você escreve, formata e revisa o documento na interface que já conhece;
- quando chega a um ponto que vale guardar, você registra um commit pelo
  terminal com `docgit commit`;
- quando quer explorar uma variação, cria uma branch e troca entre elas com
  `docgit checkout`.

Em outras palavras: **edição no Google Docs, versionamento no docgit.**

Um caso de uso típico é manter um currículo com uma branch para cada tipo de
vaga, sem duplicar arquivos no Drive e sem perder o histórico do que foi
enviado para cada lugar.

## Motivação

Eu tinha várias versões do meu currículo para enviar a vagas diferentes, e cada uma vivia em um Google Doc separado. O resultado era uma pasta cheia de cópias parecidas ("Currículo - Back-end", "Currículo - Back-end v2", "Currículo - Full Stack (final)"), difícil de organizar e fácil de confundir. Com o docgit, tudo fica em um único Google Doc: para mudar de versão, basta trocar de branch. O mesmo arquivo passa a conter quantas variações do currículo eu precisar, cada uma com seu histórico.

O Google Docs já tem um histórico de versões, mas ele é linear, fica escondido
em menus e é atualizado a cada pequena mudança, o que dificulta encontrar um
ponto específico e não permite manter variações paralelas do mesmo documento. No
docgit, o checkpoint só é criado quando o usuário decide, e cada commit tem uma
mensagem que diz o que ele representa. Os comandos seguem o Git de propósito:
como quase todo programador já tem muita experiência com a ferramenta,
`commit`, `branch` e `checkout` são intuitivos e não há nada novo para
aprender.

## O que o docgit faz

- liga um diretório local a um único Google Doc;
- cria checkpoints locais chamados commits;
- mantém branches no modelo de ponteiros para commits;
- exporta o documento atual como `.docx`;
- substitui o conteúdo do Google Doc ao trocar de branch;
- mantém os snapshots localmente em `.docgit/`, sem criar cópias no Drive.

## Limitações da v0.1

- `status` ainda não está implementado;
- `restore` ainda não está implementado;
- não há merge, diff, tags, stash, remotes ou push/pull;
- comentários e threads do Google Docs não fazem parte do contrato garantido
  dos snapshots;
- a fidelidade visual pode variar entre exportações e deve ser validada para
  documentos complexos.

## Como rodar

### 1. Pré-requisitos

- Python 3.11 ou superior;
- Git instalado e configurado;
- conta Google que possa acessar o documento;
- um projeto no Google Cloud;
- Google Drive API habilitada;
- OAuth configurado como app de computador.

### 2. Criar e preparar o projeto no Google Cloud

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/).
2. Crie um projeto novo ou selecione um projeto existente.
3. Vá em **APIs e serviços > Biblioteca**.
4. Procure por **Google Drive API** e clique em **Ativar**.
5. Vá em **APIs e serviços > Tela de consentimento OAuth**.
6. Escolha o tipo de usuário:
   - **Externo** para contas pessoais Gmail;
   - **Interno** somente quando o projeto pertence a uma organização Google
     Workspace que também autoriza o usuário.
7. Preencha o nome do aplicativo, endereço de suporte e domínio de
   desenvolvimento, se solicitados.
8. Ao configurar os escopos, adicione:
   `https://www.googleapis.com/auth/drive`

O escopo `drive.file` não é suficiente: ele não garante acesso a um documento
existente que não foi criado pelo aplicativo.

### 3. Criar as credenciais de OAuth

1. Vá em **APIs e serviços > Credenciais**.
2. Clique em **Criar credenciais > ID do cliente OAuth**.
3. Selecione **App para computador**.
4. Baixe o arquivo JSON.
5. Renomeie-o para `credentials.json`.
6. Coloque-o em:
   - Windows: `C:\Users\<usuario>\.config\docgit\credentials.json`
   - macOS/Linux: `~/.config/docgit/credentials.json`

No Windows, o caminho `~/.config/docgit/credentials.json` aponta para a pasta
do usuário após a expansão pelo Python.

Nunca coloque `credentials.json` ou `token.json` no repositório. Eles contêm
dados de autenticação e são cobertos pelo `.gitignore` do projeto.

O aplicativo verá os arquivos disponíveis ao usuário no Google Drive. Esse
impacto de privacidade deve ser explicado antes da autorização.

Se o app estiver em modo de teste, adicione o endereço usado para login em
**Audience > Test users**. Dependendo da configuração do Google, o refresh token
pode expirar depois de alguns dias. Para uso pessoal recorrente, você pode
publicar o app como em produção, sujeito à tela de aviso do Google.

### 4. Instalar o projeto

Na raiz do repositório:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

Em macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

Para instalar também as ferramentas de desenvolvimento:

```powershell
python -m pip install -e ".[dev]"
```

### 5. Configurar o autor dos commits

Os commits usam a configuração local do Git:

```powershell
git config --local user.name "Seu Nome"
git config --local user.email "seu-email@example.com"
```

### 6. Autorizar o Google

```powershell
docgit auth
```

Esse comando abre o navegador, pede autorização no escopo `drive` e cria
`~/.config/docgit/token.json`.

### 7. Inicializar um documento

Use o ID do Google Doc ou a URL completa:

```powershell
docgit init "https://docs.google.com/document/d/SEU_ID/edit"
```

Para usar somente o ID:

```powershell
docgit init "SEU_ID"
```

O comando cria `.docgit/` no diretório atual e o primeiro commit na branch
`main`.

## Uso básico

O fluxo é sempre o mesmo: edite o documento no Google Docs como de costume e,
quando quiser guardar um ponto, registre-o com o docgit.

```powershell
docgit log
docgit commit -m "Ajusta resumo para vaga de back-end"
docgit branch
docgit branch feature
docgit checkout feature
docgit checkout main
docgit checkout --force feature
```

Criar uma branch a partir de um commit antigo:

```powershell
docgit log
docgit branch antigo 07ee3cb
docgit checkout antigo
```

O prefixo do commit deve ser não ambíguo.

`checkout` recusa alterações não commitadas. O usuário pode primeiro fazer um
commit ou usar `--force`, sabendo que as alterações pendentes serão perdidas.

Liste os comandos disponíveis com:

```powershell
docgit --help
```

## Próximos passos

Funcionalidades planejadas para as próximas versões:

- **`status`**: mostrar se o documento no Google Docs tem alterações ainda não
  commitadas em relação ao último commit da branch atual;
- **`restore`**: recuperar o conteúdo de um commit anterior de volta para o
  Google Doc, sem mexer no histórico;
- **`checkout` para um commit**: permitir inspecionar o documento exatamente
  como estava em um commit específico, sem precisar criar uma branch antes;
- **`reset`**: desfazer commits movendo o ponteiro da branch atual para um
  commit anterior, como no Git. A ideia é avaliar modos equivalentes aos do
  Git (por exemplo, mover apenas o ponteiro ou também substituir o conteúdo do
  documento), deixando explícito o que é descartado;
- **`diff`**: comparar duas versões do documento;
- **`merge`**: combinar branches;
- **tags**: nomear commits importantes (por exemplo, a versão enviada a uma
  empresa);
- **`stash`**: guardar alterações pendentes temporariamente;
- **remotes e push/pull**: compartilhar o histórico entre máquinas;
- melhorar a fidelidade dos snapshots em documentos complexos e avaliar o
  tratamento de comentários e threads.

## Desenvolvimento

Execute testes e verificadores:

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .
```

Os testes contra o Google real não fazem parte do CI e exigem credenciais locais.
Os testes automatizados usam um `DocumentProvider` falso em memória.

## Como este projeto foi desenvolvido

O docgit foi construído com **Spec-Driven Development (SDD)**, usando
**agentes de código e Skills** como parte central do processo, mas com um
princípio inegociável: **human in the loop**. A IA acelera a implementação;
as decisões e a aprovação de cada etapa continuam sendo humanas.

### Spec-Driven Development

Em vez de começar pelo código, o projeto começa pela especificação:

- a especificação em [`docs/spec.md`](docs/spec.md) é a fonte da verdade;
- os planos dividem o trabalho em fases pequenas e verificáveis;
- os checkpoints registram a cobertura entre requisitos, plano e tarefas, de
  modo que nenhum requisito fique sem implementação e nenhuma tarefa fique sem
  requisito;
- decisões de arquitetura ficam registradas em
  [`docs/decisoes.md`](docs/decisoes.md).

### Agentes e Skills

A implementação foi feita por agentes de código trabalhando em lotes pequenos e
bem delimitados, orientados pela especificação. Para que esse trabalho seja
consistente e repetível, o projeto usa Skills: instruções reutilizáveis que
padronizam etapas do fluxo, como:

- planejamento: transformar a spec em fases e tarefas verificáveis;
- implementação: executar um lote de tarefas respeitando a arquitetura e as
  camadas do projeto;
- commits: gerar commits pequenos, coesos e com mensagens padronizadas.

Os testes fazem o papel de rede de segurança: eles são escritos 
antes ou junto da implementação do núcleo e dão aos agentes um 
critério objetivo de correção.

### Human in the loop

Nenhuma etapa é delegada por inteiro à IA: o humano decide e os agentes
executam. O ciclo de trabalho é:

1. **Humano**: define a especificação, o escopo e os requisitos;
2. **Agente**: propõe o plano e as tarefas a partir da spec;
3. **Humano**: revisa, avalia e aprova o plano antes de qualquer código;
4. **Agente**: implementa um lote pequeno, com testes;
5. **Humano**: revisa o código, confere se o resultado atende ao que foi 
   pedido, com apoio dos testes e das verificações automáticas, e decide 
   se aceita, pede ajustes ou descarta;
6. **Humano**: autoriza o commit e registra as decisões relevantes em
   `docs/decisoes.md`.

Lotes pequenos mantêm esse ciclo leve: cada entrega é pequena o bastante para
ser verificada rapidamente, e as decisões que importam (o que entra, o que fica
de fora e como as peças se encaixam) continuam sendo humanas.

### Arquitetura

As camadas respeitam a separação do projeto:

```text
src/docgit/core/  regras locais e interface DocumentProvider
src/docgit/gdocs/ adaptador OAuth e Google Drive
src/docgit/cli/   parsing, injeção da fábrica e saída do terminal
tests/            testes unitários e integração com provider falso
```

## Estrutura local

```text
.docgit/
  config.json
  HEAD
  refs/heads/
  commits/
  blobs/
```

A pasta `.docgit/` não deve ser enviada com dados pessoais de documentos
privados. Ela pode ser mantida em backup privado.

## Licença

MIT. Veja [LICENSE](LICENSE).
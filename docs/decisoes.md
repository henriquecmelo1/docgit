# Decisões de arquitetura

Este documento registra as decisões relevantes da versão 0.1 do docgit.

## Google Docs como área de trabalho

Decisão:

O Google Doc é a área de trabalho. Os commits são snapshots `.docx` guardados
localmente em `.docgit/blobs/`.

Consequências:

- existe apenas um documento por repositório;
- cada checkout substitui o conteúdo do mesmo `fileId`;
- não são criadas cópias no Google Drive;
- o usuário mantém o link e as permissões do documento original.

Alternativas descartadas:

- criar uma cópia no Drive para cada branch, o que duplicaria arquivos;
- usar Markdown como única representação, pois perderia o formato do documento.

## Provider como única fronteira do Google

Decisão:

O núcleo depende de `DocumentProvider`, não da API do Google.

O contrato contém:

- `export_docx`;
- `replace_content`;
- `modified_time`.

Consequências:

- `core/` pode ser testado sem rede;
- o adaptador Google pode ser substituído por um provider falso;
- novas fontes de documentos podem implementar o mesmo contrato.

## OAuth com escopo drive

Decisão:

Usar OAuth para aplicativo instalado e escopo
`https://www.googleapis.com/auth/drive`.

Razões:

- `drive.file` não dá acesso garantido a documentos existentes no Drive;
- a CLI precisa localizar e substituir o conteúdo de um documento escolhido;
- cada usuário fornece suas próprias credenciais de aplicativo.

Consequências:

- o app pode enxergar todos os arquivos disponíveis ao usuário;
- credenciais e token ficam em `~/.config/docgit/`;
- o usuário autoriza o app no navegador;
- testes manuais não fazem parte do CI.

## Hash do conteúdo normalizado

Decisão:

Exportações são normalizadas antes de calcular o hash do blob.

A normalização remove ou fixa metadados voláteis, ordena as entradas do ZIP e
recompacta o `.docx` com metadados determinísticos.

Consequências:

- exportações consecutivas sem alteração tendem a produzir o mesmo hash;
- documentos complexos ainda exigem validação manual;
- blobs iguais são deduplicados.

## Atualização no mesmo fileId

Decisão:

O adapter usa `files.update` no `fileId` original.

Consequências:

- o link do documento não muda;
- permissões existentes não são substituídas por cópias;
- a fidelidade depende do resultado real do Google Drive;
- o plano B é usar Google Docs `batchUpdate`, reservado para casos em que
  `files.update` não preserve o documento.

## Commits são snapshots imutáveis

Decisão:

Commits e blobs não são alterados depois de gravados.

Branches são referências mutáveis para o último commit da branch.

Consequências:

- um commit pode ser usado como origem para uma branch;
- um checkout atual não sobrescreve o histórico;
- blobs iguais são compartilhados por deduplicação.

## Proteção de alterações pendentes

Decisão:

O checkout recusa alterações não commitadas sem `--force`.

`--force` descarta explicitamente alterações pendentes e deve mostrar um aviso.

Razões:

- impedir perda silenciosa de trabalho no Google Doc;
- manter o comportamento semelhante ao Git;
- deixar a decisão de descarte explícita para o usuário.

## Idioma da CLI

Decisão:

Comandos e opções permanecem em inglês, enquanto mensagens exibidas ao usuário
estão em português.

## Comentários do Google Docs

Estado atual:

Comentários e threads não são garantidos pelos snapshots `.docx` ou pela
operação `files.update`.

Consequências:

- um checkout pode preservar ou não comentários dependendo do comportamento
  da API e do Google Docs;
- comentários não devem ser tratados como parte da semântica de commit até haver
  testes e uma decisão revisada da spec.

## Funcionalidades futuras

Fora da v0.1:

- `status`;
- `restore`;
- merge;
- diff;
- tags;
- stash;
- remotes;
- push/pull;
- interface web.

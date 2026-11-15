# Lia Agent Hub — Guia de instalação e uso

Este guia é para **quem vai usar** o Hub, não para quem vai mexer no código.
Para desenvolvimento, veja [DESENVOLVIMENTO.md](DESENVOLVIMENTO.md).

---

## O que o Hub é — e o que ele não é

O **Lia Agent Hub** é um acervo local de capacidades para agentes: skills,
servidores MCP, prompts, workflows, templates, referências.

**O Hub não executa nada.** Ele importa, inspeciona, valida estruturalmente,
descreve, versiona, empacota e exporta. Quem executa uma skill é o host do
agente — outra peça, outra decisão.

Isso não é limitação temporária: é o desenho. Um acervo que executa o que
cataloga precisa das defesas de um runtime, e o Hub não tem essas defesas.

### Quatro coisas que o Hub nunca faz

| Nunca | O que ele faz no lugar |
|---|---|
| Executar o que importa | Guarda e descreve; execução é do host |
| Guardar senhas ou tokens | Registra só o *nome* de variáveis de ambiente |
| Conectar sozinho à internet | Nada sai da sua máquina; sem telemetria |
| Chamar hash de assinatura | Diz "integridade", e avisa que não prova autoria |

---

## Onde ficam seus arquivos

```
%USERPROFILE%\Lia\
├─ AgentHub\
│  ├─ Biblioteca\      ← capacidades ativas (o que aparece na tela)
│  ├─ Quarentena\      ← importado, aguardando sua decisão
│  ├─ Exportados\      ← pacotes .lia-capability que você gerou
│  └─ Colecoes\        ← reservado para coleções
└─ Comum\
   └─ Capacidades\
      ├─ index.json          ← índice portátil, legível por qualquer coisa
      └─ index.schema.json   ← a definição do formato
```

**Seus arquivos são a verdade.** O Hub lê o disco; não há banco de dados que
possa divergir e não há nada "dentro do programa". Se você copiar a pasta
`Lia\AgentHub` para outro computador, sua biblioteca vai junto.

Configuração e logs ficam em `%APPDATA%\Lia\AgentHub` e
`%LOCALAPPDATA%\Lia\AgentHub\logs`.

---

## Instalar

### Opção 1 — executável (recomendada para uso)

1. Baixe `LiaAgentHub.exe`.
2. Coloque onde quiser (por exemplo, `C:\Programas\Lia`).
3. Dê dois cliques.

Na primeira execução o Windows pode mostrar *"O Windows protegeu o computador"*.
Isso acontece porque o executável **não é assinado digitalmente**. Para seguir:
**Mais informações → Executar mesmo assim**.

> **Sobre a ausência de assinatura.** Assinar exige um certificado de código
> pago. O projeto não tem um. Isso significa que você não consegue verificar
> criptograficamente quem compilou o arquivo. Se isso for um requisito seu,
> compile você mesmo a partir do código-fonte — as instruções estão em
> [DESENVOLVIMENTO.md](DESENVOLVIMENTO.md).

### Opção 2 — a partir do código

Requer Python 3.11 ou superior.

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -e .
lia-agenthub
```

---

## A janela

O Hub abre numa janela própria usando o **WebView2** (o mesmo motor do Edge,
já presente no Windows 11).

**Se o WebView2 não estiver instalado**, o Hub abre no seu navegador padrão.
A interface é idêntica — só não tem janela separada. O Hub **não baixa nem
instala** o runtime por você. Se quiser a janela nativa, procure
"Evergreen WebView2 Runtime" no site da Microsoft.

### As cinco áreas

| Área | Para quê |
|---|---|
| **Biblioteca** | Procurar, filtrar e abrir o que você já tem |
| **Quarentena** | O que você importou e ainda não decidiu |
| **Importar** | Trazer algo novo |
| **Índice e pacotes** | Gerar o índice, conferir um pacote recebido |
| **Diagnóstico** | Onde estão os arquivos, o que o Hub sabe de si |

### Como ler os indicadores

O Hub mostra **o que ele sabe**, e não esconde o que não sabe.

- **Risco** — heurística por regras explícitas: presença de scripts, domínios
  de saída declarados, variáveis de ambiente, licença desconhecida.
  Não é veredito sobre segurança. O painel lista o que **não** foi avaliado.
- **Confiança** — começa em *não revisado* e só muda quando **você** decide.
  O Hub registra quem decidiu e quando, no histórico.
- **Licença** — *desconhecida* não é *livre*. Ausência de licença não dá
  permissão a ninguém.

---

## Importar

Cole o caminho de um arquivo, pasta, `.zip` ou `.lia-capability`.
Use **Simular** para ver o relatório sem gravar nada.

O recurso **sempre** entra na **Quarentena** primeiro. Lá você lê o relatório
e decide: **Promover** (vai para a biblioteca) ou **Descartar**.

O original nunca é movido, alterado ou apagado.

### O que é recusado na importação

- Caminhos com `..`, absolutos, ou com letra de unidade (proteção contra
  escrever fora da pasta do Hub).
- Nomes que o Windows não aceita (`CON`, `aux`, nomes terminando em ponto).
- Arquivos compactados: symlinks, aninhados, com senha, com CRC inválido,
  que passam de 256 MB descomprimidos, ou com taxa de compressão absurda.
- `SKILL.md` estruturalmente inválido: frontmatter ausente, `name` fora do
  formato, corpo vazio.
- Caracteres invisíveis de controle bidirecional **dentro de bloco de código**.
  Em prosa eles são preservados e **marcados para revisão** — não bloqueiam.

Nada disso apaga seu arquivo original. A recusa é do Hub, não do seu disco.

---

## Copiar, exportar e compatilhar

**Exportar** gera um pacote `.lia-capability`: um ZIP com manifesto, conteúdo,
procedência, avisos de licença e hashes.

O destino define o que é permitido:

| Destino | Regra |
|---|---|
| `private` | Sempre permitido |
| `shared` | Permitido com aviso: você está decidindo compartilhar |
| `public` | **Recusado** sem base de redistribuição registrada |

A recusa de `public` é intencional. O Hub não sabe se você tem direito de
redistribuir; ele exige que essa decisão seja registrada por você, não
inferida por ele.

Recursos não revisados saem com `-NAO-REVISADO` no nome do arquivo. Quem
receber vê o mesmo que você vê.

**Ninguém deve depender do Hub para ler o índice.** `index.json` é JSON puro,
sem caminho absoluto, sem segredo, sem dependência de rede.

---

## Reimportar para conferir

Recebeu um `.lia-capability` e quer saber se está intacto?

**Índice e pacotes → Verificar pacote.** O Hub recalcula os hashes e compara
com o manifesto.

- Se conferir: o conteúdo não mudou desde que o pacote foi montado.
- Se não conferir: alguém alterou o arquivo, ou ele corrompeu no transporte.

**O que isso não prova:** quem montou o pacote. Hash é integridade, não
identidade. Um pacote adulterado com manifesto refeito passa na verificação.
Não existe assinatura digital no Hub.

---

## Backup

Com o Hub **fechado**, copie a pasta inteira:

```bat
robocopy "%USERPROFILE%\Lia" "D:\backup-lia" /E
```

Isso é suficiente. Não há estado escondido fora dessa pasta.

## Restaurar

1. Feche o Hub.
2. Copie a pasta de backup de volta para `%USERPROFILE%\Lia`.
3. Abra o Hub. Ele lê o disco; não precisa de "importar backup".

## Se algo quebrar

| Sintoma | O que fazer |
|---|---|
| Janela não abre | O Hub deve cair para o navegador. Se não, rode com `--browser` |
| "WebView2 não encontrado" | É aviso, não erro. Funciona no navegador |
| Capacidade sumiu | Veja **Diagnóstico**: o item pode ter metadado corrompido |
| Índice inconsistente | Gere o índice de novo em **Índice e pacotes** |
| Tela de erro ao abrir | O Hub grava `lia-agenthub-erro.html` e abre sozinho |

Os logs ficam em `%LOCALAPPDATA%\Lia\AgentHub\logs\agenthub.log`
(rotaciona em 1 MB, mantém 3 arquivos). **Nada é enviado automaticamente** —
se quiser pedir ajuda, anexe o arquivo você mesmo.

## Atualizar

1. Feche o Hub.
2. Substitua o `.exe` pela versão nova.
3. Abra.

Sua biblioteca não é tocada. Se uma versão futura mudar o formato dos
metadados, o Hub avisa em vez de converter em silêncio.

---

## Perguntas diretas com respostas diretas

**O Hub envia algo para a internet?**
Não. Não há telemetria, conta, sincronização nem verificação de atualização.

**O Hub pode executar o que eu importar?**
Não. Não há caminho de código para isso no MVP.

**Um recurso marcado "risco baixo" é seguro?**
Não. É um recurso com menos fatores observáveis. O painel lista o que não foi
avaliado — inclusive "conteúdo malicioso em prosa", que nenhuma heurística
resolve com confiança.

**O que acontece se eu importar a mesma coisa duas vezes?**
O Hub reconhece pelo hash do conteúdo, avisa que já está na biblioteca e não
duplica nada.

**Posso usar isso no Linux?**
O código roda, a interface abre no navegador. O `.exe` é Windows.

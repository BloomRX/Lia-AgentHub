# Third-Party Notices — Lia Agent Hub

**Estado:** registro inicial, criado na Fase 0.1 (2026-11-15).
**Escopo:** todo conteúdo deste repositório, em todas as branches.

---

## 1. Situação atual: nenhum código de terceiros incorporado

A Fase 0 e a Fase 0.1 foram **exclusivamente documentais**. A auditoria destas duas sessões
verificou:

| Verificação | Resultado |
|---|---|
| Código-fonte de terceiros copiado ou adaptado para este repositório | **Nenhum** |
| Dependências de runtime declaradas | **Nenhuma** — não há manifesto de pacote |
| Dependências de build declaradas | **Nenhuma** |
| Ferramenta de terceiros instalada | **Nenhuma** |
| Conteúdo binário versionado | **Apenas** `docs/KIT-PROJETO-NOVO.zip`, que é material **do próprio projeto Lia**, não de terceiro |
| Trechos de código de outros projetos reproduzidos em prosa | **Nenhum** — as auditorias descrevem e citam caminhos, não copiam implementação |

**Verificação reproduzível:**

```bash
git ls-files | grep -vE '\.md$|\.zip$'
# saída esperada: .gitignore e THIRD_PARTY_NOTICES.md — nenhum arquivo de código
```

A única citação extensa de terceiros está em `docs/research/INTEGRATION-CANDIDATES.md`, que é
**análise**, não incorporação. Nomes de projeto, URLs e números de versão são fatos, não obras
derivadas.

---

## 2. O que **precisará** ser registrado aqui quando houver código

Esta seção existe para que ninguém descubra a obrigação depois de publicar. Cada item vem da
pesquisa da Fase 0 e da verificação de metadados da Fase 0.1.

### 2.1 Empacotamento — atenção jurídica

| Componente | Licença | Por que importa |
|---|---|---|
| **PyInstaller** | **GPLv2-or-later, com exceção especial** que permite empacotar software proprietário | **A exceção é o que torna o `.exe` possível.** Sem ela, o bundle seria obra derivada de GPL. A exceção precisa ser citada **no momento em que PyInstaller for usado**, com a redação da licença preservada. Não é opcional |
| **PyInstaller hooks-contrib** | GPL (mesma família) | Empacotado como dependência de build |

### 2.2 Interface (se `D-17` escolher `pywebview`)

| Componente | Licença | Observação |
|---|---|---|
| **pywebview** | BSD 3-Clause | Exige preservar copyright e disclaimer |
| **pythonnet** | Não declarada no metadado do PyPI | **Precisa de verificação manual do arquivo `LICENSE` do projeto** antes de adotar |
| **bottle** | MIT | Servidor WSGI embutido no pywebview |
| **proxy_tools**, **typing_extensions** | MIT / PSF | Dependências transitivas |

### 2.3 WebView2 (se usado)

| Componente | Licença | Observação |
|---|---|---|
| **Microsoft Edge WebView2 Runtime** | Distribuível com o app, conforme termos da Microsoft | **Não** é empacotado no modo Evergreen — o app usa o do sistema. Se o modo *Fixed Version* for adotado, os termos mudam e precisam ser revistos |

### 2.4 Importado do ecossistema Lia (se algum dia houver código compartilhado)

| Origem | Licença declarada | Observação |
|---|---|---|
| **Lia Studio** (`BloomRX/Lia-Studio`) | MIT no arquivo `LICENSE` da branch de desenvolvimento; marca **fora** da MIT | O endpoint de licença do GitHub retorna 404 porque o arquivo não está na branch padrão. **Verificar antes de reutilizar** |
| **Lia Forge** (`BloomRX/Lia-Forge`) | Idem | Idem |
| **Lia Project** (`BloomRX/Lia-Project`) | Sem `LICENSE` na árvore auditada | **Não reutilizar sem decisão humana** |
| Skills adaptadas de fontes MIT | Citadas individualmente nos `SKILL.md` do Studio | A obrigação de atribuição está **no repositório do Studio**, não aqui |

### 2.5 Candidatos externos — **nenhum adotado**

| Candidato | Licença | Estado neste repositório |
|---|---|---|
| `bitbonsai/mcpvault` | MIT | **Não adotado** — apenas referência de estudo |
| `Graphify-Labs/graphify` | Apache-2.0 + `NOTICE` | **Não adotado** — Apache exige preservar `NOTICE` se adotado |
| `akitaonrails/ai-memory` | MIT | **Não adotado** |
| `astral-sh/uv` | Apache-2.0 OR MIT | **Não adotado** — nem como dependência de build |
| Agent Skills (especificação) | Apache-2.0 (código) / CC-BY-4.0 (docs) | **Referência normativa**, não incorporação |
| Obsidian | **Não verificado** | **Não adotado**; licenciamento marcado `RESEARCH (não verificada)` |

---

## 3. Regras para quem adicionar código depois

1. **Toda dependência nova entra neste arquivo no mesmo commit que a adiciona.** Não depois.
2. **Versão fixa** para toda dependência de build e de runtime — sem `latest`, sem faixa aberta.
3. **Licença verificada no arquivo real do projeto**, não no metadado do registro de pacotes.
   O caso `pythonnet` (§2.2) mostra por que: o PyPI não declara licença para ele.
4. **`NOTICE` preservado** quando a licença exigir (Apache-2.0 é o caso mais comum).
5. **O núcleo (L3) não pode ganhar dependência.** Se um adaptador precisa de um pacote, ele fica
   na camada do adaptador e é registrado aqui — o domínio continua stdlib.
6. **Nenhuma licença é escolhida para este repositório por este arquivo.** A licença do Lia
   Agent Hub é a decisão `D-16`, aberta, reservada ao usuário.

---

## 4. Nota sobre a ausência de `LICENSE`

Este repositório **não tem** `LICENSE`. Isso é **deliberado** nesta fase: a escolha de licença
é a decisão `D-16` do registro de decisões, e escolher MIT, Apache-2.0 ou qualquer outra
unilateralmente violaria o mandato da Fase 0.

**Consequência a declarar:** sem `LICENSE`, o direito de reutilização deste material não está
concedido por padrão. Isso é irrelevante enquanto o conteúdo é documentação interna do projeto,
e é **bloqueante** antes de qualquer publicação que convide terceiros a usar o código.

Ver `docs/DECISION-REGISTER.md` → `D-16`.

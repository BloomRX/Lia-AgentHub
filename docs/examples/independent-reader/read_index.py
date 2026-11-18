#!/usr/bin/env python3
"""Leitor de referência do índice `Comum/Capacidades/index.json` — IDX-3.

OBJETIVO: provar, por execução, que o contrato de distribuição do Lia Agent
Hub é consumível **sem o Hub instalado**.

Este arquivo é deliberadamente independente:
  - não importa `lia_agenthub`;
  - usa apenas a biblioteca padrão do Python;
  - não conhece o formato interno de `capability.json`;
  - não escreve nada no disco.

Se este script precisar mudar para continuar funcionando, o contrato do índice
mudou de forma incompatível — e isso é exatamente o que ele existe para
detectar.

Uso:
    python read_index.py <caminho-do-index.json> [--json] [--check]

    --json    imprime o índice inteiro em JSON, sem formatação de tabela
    --check   valida o índice contra as regras publicadas e retorna
              código 1 se algo estiver inconsistente; não imprime tabela

Códigos de saída:
    0  sucesso (ou --check sem problemas)
    1  índice inconsistente (só em --check)
    2  arquivo ilegível, ausente ou malformado
"""
from __future__ import annotations

import json
import sys
from typing import NoReturn

#: Campos que o contrato promete em cada capacidade publicada.
#: A ausência de qualquer um destes é uma quebra de contrato, não um detalhe.
REQUIRED_TOP_LEVEL = ("schemaVersion", "generatedAt", "capabilities")
REQUIRED_PER_CAPABILITY = ("id", "name", "version", "type", "trust",
                           "license", "licenseKnown", "redistributable", "treeHash")

#: Versões de schema que este leitor entende. Uma versão nova exige leitor novo.
SUPPORTED_SCHEMA_VERSIONS = (1,)

#: Presentes no índice por honestidade: o consumidor precisa poder ver que o
#: índice NÃO é assinado e o que ele NÃO avalia.
INFORMATIONAL_TOP_LEVEL = ("signed", "signatureNote", "scope", "scopeNote")


def _falhar(mensagem: str) -> "NoReturn":
    """Sai com código 2 (erro de entrada, não de contrato).

    Não usar `sys.exit(texto)`: com uma string como argumento, o Python imprime
    a mensagem e sai com código **1** — que aqui significa "índice
    inconsistente". As duas coisas precisam ser distinguíveis por quem chama.
    """
    print(mensagem, file=sys.stderr)
    raise SystemExit(2)


def load(path: str) -> dict:
    """Lê e faz o parse do índice. Sai com código 2 em qualquer falha de leitura."""
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        _falhar(f"erro: arquivo não encontrado: {path}")
    except PermissionError:
        _falhar(f"erro: sem permissão de leitura: {path}")
    except UnicodeDecodeError:
        _falhar(f"erro: arquivo não é UTF-8 válido: {path}")
    except json.JSONDecodeError as e:
        _falhar(f"erro: JSON malformado em {path}:{e.lineno}: {e.msg}")
    except OSError as e:
        _falhar(f"erro: não foi possível ler {path}: {e}")


def problems(index: dict) -> list[str]:
    """Inconsistências do índice, em texto legível. Vazia = consistente."""
    out: list[str] = []

    if not isinstance(index, dict):
        return ["a raiz do índice não é um objeto JSON"]

    for chave in REQUIRED_TOP_LEVEL:
        if chave not in index:
            out.append(f"campo obrigatório ausente no topo: `{chave}`")

    versao = index.get("schemaVersion")
    if versao is not None and versao not in SUPPORTED_SCHEMA_VERSIONS:
        out.append(
            f"schemaVersion {versao!r} não é suportado por este leitor "
            f"(suporta: {list(SUPPORTED_SCHEMA_VERSIONS)}). "
            "Atualize o leitor; não ignore a versão.")

    caps = index.get("capabilities")
    if not isinstance(caps, list):
        out.append("`capabilities` não é uma lista")
        return out

    vistos: set[str] = set()
    for i, cap in enumerate(caps):
        onde = f"capabilities[{i}]"
        if not isinstance(cap, dict):
            out.append(f"{onde}: não é um objeto")
            continue
        for chave in REQUIRED_PER_CAPABILITY:
            if chave not in cap:
                out.append(f"{onde}: campo obrigatório ausente: `{chave}`")
        cid = cap.get("id")
        if isinstance(cid, str):
            if cid in vistos:
                out.append(f"{onde}: id duplicado: `{cid}`")
            vistos.add(cid)
        # Honestidade do contrato: "desconhecido" é null, nunca inventado.
        if cap.get("license") is None and cap.get("licenseKnown") is True:
            out.append(
                f"{onde}: `license` é null mas `licenseKnown` é true — "
                "o índice estaria afirmando conhecer uma licença que não registra")
        if cap.get("redistributable") is True and cap.get("license") is None:
            out.append(
                f"{onde}: `redistributable` é true sem licença registrada — "
                "redistribuição exige base, e a base não está no contrato")
    return out


def _cell(value) -> str:
    """Formata um valor sem converter `null` em texto enganoso."""
    if value is None:
        return "—"
    if value is True:
        return "sim"
    if value is False:
        return "não"
    if value == "":
        return "(vazio)"
    return str(value)


def print_table(index: dict) -> None:
    caps = index.get("capabilities") or []
    print(f"Índice gerado em : {_cell(index.get('generatedAt'))}")
    print(f"Schema           : {_cell(index.get('schemaVersion'))}")
    print(f"Assinado         : {_cell(index.get('signed'))}")
    nota = index.get("signatureNote")
    if nota:
        print(f"Nota de assinatura: {nota}")
    escopo = index.get("scope")
    if escopo:
        print(f"Escopo           : {escopo}")
        if index.get("scopeNote"):
            print(f"  {index['scopeNote']}")
    print(f"Capacidades      : {len(caps)}")
    if not caps:
        return

    cabecalho = ("ID", "NOME", "VER", "TIPO", "CONFIANÇA", "LICENÇA", "REDIST.")
    linhas = [cabecalho]
    for cap in caps:
        licenca = _cell(cap.get("license"))
        if not cap.get("licenseKnown"):
            licenca = "desconhecida" if cap.get("license") is None else licenca
        linhas.append((
            _cell(cap.get("id")),
            _cell(cap.get("name")),
            _cell(cap.get("version")),
            _cell(cap.get("type")),
            _cell(cap.get("trust")),
            licenca,
            _cell(cap.get("redistributable")),
        ))

    larguras = [max(len(str(l[i])) for l in linhas) for i in range(len(cabecalho))]
    for n, linha in enumerate(linhas):
        texto = "  ".join(str(c).ljust(larguras[i]) for i, c in enumerate(linha))
        print(texto.rstrip())
        if n == 0:
            print("  ".join("-" * w for w in larguras))

    # Requisitos: o que o host precisa para usar cada item.
    com_requisito = [c for c in caps if c.get("egress") or c.get("containsScripts")]
    if com_requisito:
        print("\nRequisitos declarados:")
        for cap in com_requisito:
            partes = []
            if cap.get("egress"):
                partes.append("egress: " + ", ".join(cap["egress"]))
            if cap.get("containsScripts"):
                partes.append("contém scripts (não executados pelo Hub)")
            print(f"  {cap.get('name')}: {'; '.join(partes)}")

    # O leitor repete o aviso em vez de assumir que o consumidor leu o índice.
    negados = caps[0].get("notEvaluated") if caps else None
    if negados:
        print("\nO índice NÃO avalia:")
        for item in negados:
            print(f"  - {item}")


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if not a.startswith("--")]
    flags = {a for a in argv[1:] if a.startswith("--")}

    if not args or "-h" in flags or "--help" in flags:
        print(__doc__)
        return 0 if args or flags else 2

    index = load(args[0])

    if "--json" in flags:
        print(json.dumps(index, ensure_ascii=False, indent=2))
        return 0

    if "--check" in flags:
        falhas = problems(index)
        if falhas:
            print(f"{len(falhas)} problema(s) no índice:")
            for f in falhas:
                print(f"  - {f}")
            return 1
        print(f"índice consistente: {len(index.get('capabilities') or [])} capacidade(s)")
        return 0

    print_table(index)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

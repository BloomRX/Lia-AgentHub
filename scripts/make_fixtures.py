#!/usr/bin/env python3
"""Gera fixtures SINTÉTICAS para os testes manuais no Windows.

Nada aqui é código real de terceiro. Cada pasta exercita um caminho do produto:
importação válida, licença ausente, scripts presentes, referência quebrada,
caractere invisível, ZIP aninhado, CRC adulterado, pacote do Hub.

Uso:
    python scripts/make_fixtures.py            # cria em ./fixtures
    python scripts/make_fixtures.py C:\\temp\\fx

O script NUNCA executa o que gera.
"""
from __future__ import annotations

import io
import json
import struct
import sys
import zipfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _escreve(p: Path, texto: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(texto, encoding="utf-8")


def skill_valida(base: Path) -> Path:
    """Agent Skill bem formada, com licença MIT detectável."""
    d = base / "01-skill-valida"
    _escreve(d / "SKILL.md",
             "---\n"
             "name: skill-valida\n"
             "description: Fixture sintetica que descreve um recurso valido.\n"
             "version: 1.0.0\n"
             "metadata: tags:teste,fixture, domain:exemplo, author:Fixture\n"
             "---\n\n"
             "# Skill válida\n\n"
             "Este corpo é sintético. Ele existe para exercitar a importação.\n\n"
             "Consulte `apoio.md` para detalhes.\n")
    _escreve(d / "apoio.md", "# Apoio\n\nArquivo referenciado pelo SKILL.md.\n")
    _escreve(d / "LICENSE", "MIT License\n\nCopyright (c) 2026 Fixture Sintética\n")
    return d


def skill_sem_licenca(base: Path) -> Path:
    """Válida, mas sem licença: o caso mais mal interpretado."""
    d = base / "02-skill-sem-licenca"
    _escreve(d / "SKILL.md",
             "---\n"
             "name: skill-sem-licenca\n"
             "description: Sem arquivo de licenca. Ausencia NAO significa livre.\n"
             "version: 0.1.0\n"
             "---\n\nCorpo sintético.\n")
    return d


def skill_com_scripts(base: Path) -> Path:
    """Contém script. O Hub deve importar e NUNCA executar."""
    d = base / "03-skill-com-scripts"
    _escreve(d / "SKILL.md",
             "---\n"
             "name: skill-com-scripts\n"
             "description: Possui um script que nao pode ser executado pelo Hub.\n"
             "version: 2.0.0\n"
             "---\n\nUse `scripts/prova.py`.\n\n"
             "Se o Hub executar este script, ele cria PWNED.txt na pasta atual.\n")
    _escreve(d / "scripts" / "prova.py",
             "# MARCADOR DE EXECUCAO: se este arquivo rodar, deixa rastro.\n"
             "import pathlib\n"
             "pathlib.Path('PWNED.txt').write_text('executado', encoding='utf-8')\n"
             "print('NAO DEVERIA APARECER')\n")
    return d


def skill_frontmatter_invalido(base: Path) -> Path:
    """Deve ser recusada na importação."""
    d = base / "04-skill-invalida"
    _escreve(d / "SKILL.md",
             "---\n"
             "name: Tem Espaco E Maiuscula\n"
             "description: Nome fora do formato da especificacao.\n"
             "---\n\nCorpo.\n")
    return d


def skill_referencia_quebrada(base: Path) -> Path:
    """Válida, mas cita arquivo que não existe — aviso, não bloqueio."""
    d = base / "05-skill-referencia-quebrada"
    _escreve(d / "SKILL.md",
             "---\n"
             "name: referencia-quebrada\n"
             "description: Cita arquivo ausente; deve gerar aviso.\n"
             "version: 1.0.0\n"
             "---\n\nLeia `nao-existe.md`.\n")
    return d


def skill_bidi_prosa(base: Path) -> Path:
    """Bidi em PROSA: deve importar com marcação de revisão, não bloquear."""
    d = base / "06-skill-bidi-prosa"
    _escreve(d / "SKILL.md",
             "---\n"
             "name: bidi-prosa\n"
             "description: Tem marcador bidirecional em prosa.\n"
             "version: 1.0.0\n"
             "---\n\n"
             "Texto normal e aqui \u202eum trecho invertido\u202c de proposito.\n")
    return d


def skill_bidi_codigo(base: Path) -> Path:
    """Bidi dentro de bloco de código: DEVE ser bloqueado."""
    d = base / "07-skill-bidi-codigo"
    _escreve(d / "SKILL.md",
             "---\n"
             "name: bidi-codigo\n"
             "description: Marcador bidirecional dentro de bloco de codigo.\n"
             "version: 1.0.0\n"
             "---\n\n```\ntexto \u202eoculto\u202c aqui\n```\n")
    return d


def zip_traversal(base: Path) -> Path:
    """ZIP que tenta escrever fora da área."""
    alvo = base / "08-zip-traversal.zip"
    base.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(alvo, "w") as zf:
        zf.writestr("../../INVADIU.txt", "não deveria existir")
        zf.writestr("SKILL.md", "---\nname: traversal\ndescription: d\n---\n")
    return alvo


def zip_aninhado(base: Path) -> Path:
    """ZIP dentro de ZIP: deve ser recusado."""
    interno = io.BytesIO()
    with zipfile.ZipFile(interno, "w") as zf:
        zf.writestr("SKILL.md", "x")
    alvo = base / "09-zip-aninhado.zip"
    with zipfile.ZipFile(alvo, "w") as zf:
        zf.writestr("pacote.zip", interno.getvalue())
        zf.writestr("SKILL.md", "---\nname: aninhado\ndescription: d\n---\n")
    return alvo


def zip_crc(base: Path) -> Path:
    """ZIP com CRC declarado errado: deve ser recusado."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as zf:
        zf.writestr("SKILL.md", b"conteudo adulterado")
    raw = bytearray(buf.getvalue())
    raw[14:18] = struct.pack("<I", 0xDEADBEEF)
    ci = raw.find(b"PK\x01\x02")
    if ci > 0:
        raw[ci + 16:ci + 20] = struct.pack("<I", 0xDEADBEEF)
    alvo = base / "10-zip-crc-invalido.zip"
    alvo.write_bytes(bytes(raw))
    return alvo


def zip_arquivo_grande(base: Path) -> Path:
    """ZIP com arquivo acima do limite de 64 MB — recusado."""
    alvo = base / "11-zip-arquivo-grande.zip"
    with zipfile.ZipFile(alvo, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("grande.bin", b"x" * (65 * 1024 * 1024))
    return alvo


def pacote_hub(base: Path) -> Path | None:
    """Gera um `.lia-capability` REAL usando o próprio Hub."""
    sys.path.insert(0, str(ROOT / "src"))
    try:
        from lia_agenthub.adapters.paths_resolver import resolve_locations
        from lia_agenthub.app import AgentHub
    except ImportError:
        return None

    import tempfile
    destino = base / "12-pacote-valido.lia-capability"
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / "home"
        hub = AgentHub(resolve_locations(home))
        r = hub.import_path(str(skill_valida(Path(tmp) / "src")))
        if not r.ok:
            return None
        hub.promote(r.capability_id)
        e = hub.export(r.capability_id, target="private",
                       destination=str(Path(tmp) / "out"))
        if not e["ok"]:
            return None
        destino.write_bytes(Path(e["path"]).read_bytes())
    return destino


def pacote_adulterado(base: Path, origem: Path | None) -> Path | None:
    """Copia o pacote válido e troca um byte do payload — deve falhar a verificação."""
    if not origem or not origem.is_file():
        return None
    entrada = zipfile.ZipFile(origem)
    conteudo = {n: entrada.read(n) for n in entrada.namelist()}
    entrada.close()

    chave = next((k for k in conteudo if k.startswith("payload/")), None)
    if not chave:
        return None
    conteudo[chave] = conteudo[chave] + b"\n<!-- adulterado -->\n"

    alvo = base / "13-pacote-adulterado.lia-capability"
    with zipfile.ZipFile(alvo, "w") as zf:
        for n, d in conteudo.items():
            zf.writestr(n, d)
    return alvo


def arquivo_solto(base: Path) -> Path:
    d = base / "14-documento-solto"
    d.mkdir(parents=True, exist_ok=True)
    alvo = d / "notas.md"
    _escreve(alvo, "# Notas\n\nDocumento solto, sem SKILL.md.\n")
    return alvo


def main() -> int:
    base = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "fixtures"
    base.mkdir(parents=True, exist_ok=True)

    print(f"Gerando fixtures em {base}")
    criados: list[str] = []

    for fn in (skill_valida, skill_sem_licenca, skill_com_scripts,
               skill_frontmatter_invalido, skill_referencia_quebrada,
               skill_bidi_prosa, skill_bidi_codigo, zip_traversal,
               zip_aninhado, zip_crc, zip_arquivo_grande, arquivo_solto):
        try:
            p = fn(base)
            criados.append(str(Path(p).relative_to(base)))
        except Exception as e:  # noqa: BLE001
            print(f"  ! {fn.__name__} falhou: {e}")

    pac = pacote_hub(base)
    if pac:
        criados.append(str(pac.relative_to(base)))
        ad = pacote_adulterado(base, pac)
        if ad:
            criados.append(str(ad.relative_to(base)))

    manifesto = {
        "aviso": "TODAS as fixtures são sintéticas. Nenhuma deve ser executada.",
        "geradoPor": "scripts/make_fixtures.py",
        "itens": criados,
    }
    _escreve(base / "MANIFESTO.json", json.dumps(manifesto, ensure_ascii=False, indent=2))

    for c in criados:
        print(f"  + {c}")
    print(f"\n{len(criados)} fixtures criadas. Nada foi executado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

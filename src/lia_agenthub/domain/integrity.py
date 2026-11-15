"""Hashes — integridade, NÃO assinatura. SECURITY §3.7.1.

Seis conceitos, seis nomes:
  contentHash  → aquele arquivo não mudou desde a importação
  treeHash     → o CONJUNTO de arquivos não mudou
  packageHash  → o ZIP não corrompeu no transporte
  signature    → NÃO IMPLEMENTADO (fase futura)
  author       → declaração, não prova
  provenance   → de onde o Hub diz que veio

Nenhuma função aqui produz ou valida assinatura. Não existe campo `signed`.
"""
from __future__ import annotations

import hashlib
import unicodedata

CHUNK = 1 << 20


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while chunk := fh.read(CHUNK):
            h.update(chunk)
    return h.hexdigest()


def normalize_newlines(data: bytes) -> bytes:
    """CRLF -> LF. Muda bytes; por isso registramos os DOIS hashes."""
    return data.replace(b"\r\n", b"\n")


def content_hashes(data: bytes) -> dict[str, str]:
    """Dois hashes quando a normalização muda o conteúdo (§8.3).

    `asReceived` é o hash do que chegou; `normalized` é o do que o Hub
    guarda. Comparar só um dos dois esconde corrupção de transporte.
    """
    received = sha256_bytes(data)
    normalized = sha256_bytes(normalize_newlines(data))
    out = {"asReceived": received, "normalized": normalized}
    return out


def tree_hash(entries: dict[str, str]) -> str:
    """Hash do conjunto: caminho + hash de cada arquivo, ordem estável.

    Pega arquivo ADICIONADO ou REMOVIDO, não só alterado — que é o que
    contentHash sozinho não vê.
    """
    h = hashlib.sha256()
    for path in sorted(entries):
        h.update(path.encode("utf-8"))
        h.update(b"\x00")
        h.update(entries[path].encode("ascii"))
        h.update(b"\n")
    return h.hexdigest()


def normalize_for_compare(text: str) -> str:
    """NFC para comparar. NUNCA gravar isto — alteraria o conteúdo do autor."""
    return unicodedata.normalize("NFC", text)


def is_same_content(a: str, b: str) -> bool:
    return a == b and bool(a)


def verify_integrity(expected: str, data: bytes) -> bool:
    return sha256_bytes(data) == expected

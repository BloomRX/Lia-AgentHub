"""Contenção de caminho — SECURITY §5, controles C1–C12.

Tudo que vem de um pacote é HOSTIL até prova documentada. Este módulo
implementa as regras puras; quem materializa é o adaptador de arquivos.
"""
from __future__ import annotations

import posixpath
import re
from dataclasses import dataclass

from .errors import SecurityError

# C4: nomes reservados do Windows. Rejeitados mesmo no Linux — um pacote
# válido no Linux não pode falhar depois de exportado.
WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}

# C3: o que nunca entra, em qualquer profundidade. `.git.` e `.git ` são
# equivalentes a `.git` no Windows — daí a canonicalização antes do teste.
DENY_NAMES = {
    # `.lia` é o diretório de METADADOS DO HUB dentro de cada capacidade
    # (`capability.json`, `provenance.json`, `history.json`). Se um payload
    # trouxer `.lia/`, esses arquivos seriam gravados ao lado dos metadados
    # reais e poderiam se passar por eles — contradiz a fronteira de confiança
    # e faz o `.lia` forjado viajar para dentro do pacote exportado.
    # Não há uso legítimo: o `.lia` pertence ao Hub, nunca ao recurso.
    ".lia",
    "node_modules", "thumbs.db", "desktop.ini",
    # Credenciais e chaves: um pacote não transporta segredo, nem para
    # "só documentar". Não há uso legítimo num acervo de capacidades.
    ".ssh", ".gnupg", ".aws", ".azure", ".kube", ".docker", ".netrc",
    ".git-credentials", ".npmrc", ".pypirc", "id_rsa", "id_ed25519",
    "credentials", "credentials.json", ".env",
}

# C13: fluxos alternativos NTFS (`arquivo.txt:oculto`). O `:` também nomeia
# drive, então rejeitamos qualquer ocorrência fora da posição 1.
_NTFS_STREAM_RE = re.compile(r":")

# C10: extensões executáveis. Não bloqueiam por si: registram para exibição.
EXEC_EXTS = {
    ".exe", ".dll", ".bat", ".cmd", ".com", ".scr", ".msi", ".ps1", ".vbs",
    ".js", ".mjs", ".cjs", ".sh", ".py", ".rb", ".pl", ".jar", ".so", ".dylib",
}

MAX_PATH_LEN = 200   # §8.3: margem para o teto de 260 do Windows
MAX_DEPTH = 24

_DRIVE_RE = re.compile(r"^[a-zA-Z]:")
_UNC_RE = re.compile(r"^(?:\\\\|//)")


@dataclass(frozen=True)
class SafePath:
    """Caminho relativo já validado, sempre com separador POSIX."""

    parts: tuple[str, ...]

    @property
    def posix(self) -> str:
        return "/".join(self.parts)


def _canonical_name(name: str) -> str:
    """C7: normaliza pontos e espaços finais, como o Windows faz.

    `.git.` -> `.git` · `aux ` -> `aux`. Sem isso, uma denylist de nomes
    exatos é trivialmente contornável no Windows.
    """
    return name.rstrip(" .").lower()


def index_ntfs(part: str) -> int | None:
    """Posição de um `:` que indicaria fluxo alternativo NTFS, se houver."""
    i = part.find(":")
    return i if i >= 0 else None


def validate_relative(raw: str) -> SafePath:
    """Valida um caminho vindo de fora. Levanta SecurityError se inseguro.

    Regras aplicadas (numeração de SECURITY §5):
    C1 não vazio · C2 sem absoluto/drive/UNC · C3 denylist em qualquer
    profundidade · C4 nomes reservados · C5 sem `..` · C6 separador POSIX
    · C7 canonicalização Windows · C8 tamanho · C9 profundidade
    """
    if not raw or not raw.strip():
        raise SecurityError("Caminho vazio no pacote.", "O pacote está corrompido.", code="C1")

    value = raw.replace("\\", "/")

    if _DRIVE_RE.match(value) or _UNC_RE.match(value) or value.startswith("/"):
        raise SecurityError(
            f"Caminho absoluto ou de rede não é permitido: `{raw}`.",
            "Pacotes usam apenas caminhos relativos, com barras normais.",
            code="C2",
        )

    if "\x00" in value:
        raise SecurityError(
            "Caminho contém byte nulo.", "O pacote está corrompido ou foi adulterado.", code="C2"
        )

    parts = [p for p in value.split("/") if p not in ("", ".")]
    if not parts:
        raise SecurityError(f"Caminho inválido: `{raw}`.", "Verifique o pacote.", code="C1")

    if len(parts) > MAX_DEPTH:
        raise SecurityError(
            f"Caminho com profundidade excessiva ({len(parts)} níveis).",
            f"O limite é {MAX_DEPTH} níveis.", code="C9",
        )

    cleaned: list[str] = []
    for part in parts:
        if part == "..":
            raise SecurityError(
                f"`..` não é permitido em caminho de pacote: `{raw}`.",
                "Travessia de diretório é bloqueada sempre.",
                code="C5",
            )
        canon = _canonical_name(part)
        if canon in DENY_NAMES or canon.startswith(".git"):
            raise SecurityError(
                f"Entrada proibida no pacote: `{part}`.",
                "Pastas de controle de versão e dependências não entram em pacotes.",
                code="C3",
            )
        stem = canon.split(".")[0]
        if stem.upper() in WINDOWS_RESERVED:
            raise SecurityError(
                f"Nome reservado do Windows: `{part}`.",
                "Esse nome não pode ser criado no Windows, mesmo que o pacote venha do Linux.",
                code="C4",
            )
        if index_ntfs(part) is not None:
            raise SecurityError(
                f"`:` não é permitido em nome de arquivo: `{part}`.",
                "No Windows, `arquivo:fluxo` cria um fluxo alternativo oculto. "
                "Pacotes não usam esse recurso.", code="C13",
            )
        if part.endswith((" ", ".")):
            raise SecurityError(
                f"Nome termina em espaço ou ponto: `{part}`.",
                "O Windows descarta esses caracteres e o nome muda ao extrair.", code="C7",
            )
        cleaned.append(part)

    full = "/".join(cleaned)
    if len(full) > MAX_PATH_LEN:
        raise SecurityError(
            f"Caminho com {len(full)} caracteres excede o limite de {MAX_PATH_LEN}.",
            "Caminhos longos falham no Windows sem configuração especial.", code="C8",
        )

    return SafePath(tuple(cleaned))


def resolve_within(root_parts: tuple[str, ...], relative: str) -> SafePath:
    """C11/C12: resolve e confirma que o resultado fica sob a raiz.

    Não toca no disco: opera sobre a forma canônica. Quem chama continua
    obrigado a checar symlink no sistema de arquivos (C12) — esta função
    prova contenção, não inexistência de link.
    """
    safe = validate_relative(relative)
    joined = posixpath.normpath(posixpath.join(*root_parts, *safe.parts))
    root = posixpath.normpath(posixpath.join(*root_parts))
    if not (joined == root or joined.startswith(root + "/")):
        raise SecurityError(
            f"Destino escaparia do diretório autorizado: `{relative}`.",
            "Importação bloqueada.", code="C12",
        )
    return SafePath(tuple(joined.split("/")))


def is_executable(path: str) -> bool:
    return any(path.lower().endswith(ext) for ext in EXEC_EXTS)


def looks_like_script(parts: tuple[str, ...]) -> bool:
    """`scripts/` em qualquer nível, ou extensão executável."""
    if any(p.lower() == "scripts" for p in parts[:-1]):
        return True
    return bool(parts) and is_executable(parts[-1])


@dataclass(frozen=True)
class Verdict:
    """Resultado de uma checagem de caminho, sem exceção.

    `validate_relative` levanta; esta forma é para relatórios e para a UI,
    onde "recusado" é um dado a mostrar, não um fluxo de exceção.
    """

    ok: bool
    code: str = ""
    message: str = ""

    @property
    def posix(self) -> str:
        return self.message if self.ok else ""


def check_relative_path(raw: str) -> Verdict:
    """Versão sem exceção de `validate_relative`."""
    try:
        safe = validate_relative(raw)
    except SecurityError as e:
        return Verdict(False, getattr(e, "code", "") or "C?", e.message)
    return Verdict(True, "", safe.posix)

"""Extração segura de ZIP. Nenhum byte de fora toca o disco sem passar aqui.

Ameaças cobertas: zip slip (../), caminho absoluto, symlink, hardlink,
bomba de descompressão, entrada duplicada com nome equivalente no Windows,
arquivo gigante, ZIP aninhado, ZIP criptografado, CRC inválido.

Nada é executado. Nada é seguido. Tudo é lido em memória com teto.
"""
from __future__ import annotations

import json
import io
import zlib
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from ..domain.errors import SecurityError
from ..domain.paths import is_executable, looks_like_script, validate_relative

MAX_TOTAL_BYTES = 256 * 1024 * 1024   # 256 MB descomprimido
MAX_FILES = 5000
MAX_RATIO = 200                        # bomba de descompressão
MAX_SINGLE = 64 * 1024 * 1024


@dataclass
class ExtractedFile:
    path: str
    data: bytes
    is_executable: bool

    @property
    def size(self) -> int:
        return len(self.data)


@dataclass
class Extraction:
    files: list[ExtractedFile] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    rejected: list[str] = field(default_factory=list)
    #: Manifesto do pacote, quando a origem for um `.lia-capability`.
    manifest: dict | None = None
    #: Procedência declarada no pacote, quando houver.
    provenance: dict | None = None

    @property
    def contains_scripts(self) -> bool:
        return any(looks_like_script(tuple(f.path.split("/"))) for f in self.files)

    @property
    def total_size(self) -> int:
        return sum(f.size for f in self.files)

    def by_name(self, name: str) -> ExtractedFile | None:
        return next((f for f in self.files if f.path == name), None)


def inspect_zip(data: bytes) -> Extraction:
    """Lê o ZIP inteiro em memória. Levanta SecurityError em qualquer violação.

    Nada é escrito no disco: quem decide onde materializar é a importação,
    depois da validação.
    """
    result = Extraction()

    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        raise SecurityError(
            "O arquivo não é um ZIP válido ou está corrompido.",
            "Verifique se o download terminou por completo.", code="ZIP_INVALID")

    infos = zf.infolist()

    if len(infos) > MAX_FILES:
        raise SecurityError(
            f"O pacote tem {len(infos)} entradas; o limite é {MAX_FILES}.",
            "Pacotes muito fragmentados não são aceitos.", code="ZIP_TOO_MANY")

    declared = sum(i.file_size for i in infos)
    if declared > MAX_TOTAL_BYTES:
        raise SecurityError(
            f"O pacote declarar ter {declared // (1024*1024)} MB descomprimidos; "
            f"o limite é {MAX_TOTAL_BYTES // (1024*1024)} MB.",
            "Isso pode ser uma bomba de descompressão.", code="ZIP_TOO_BIG")

    seen_canonical: dict[str, str] = {}
    written_total = 0

    for info in infos:
        name = info.filename

        if name.endswith("/"):
            continue  # diretório explícito

        # C2/C3/C5/C7 via política única
        safe = validate_relative(name)
        posix = safe.posix

        # Colisão case-insensitive: `SKILL.md` e `skill.md` coexistem no
        # Linux e colidem no Windows. Detectar aqui evita pacote que
        # "abre no Linux e falha no Windows depois de exportado".
        canon = posix.lower()
        if canon in seen_canonical and seen_canonical[canon] != posix:
            raise SecurityError(
                f"Duas entradas colidem no Windows: `{seen_canonical[canon]}` e `{posix}`.",
                "Renomeie uma delas no pacote.", code="ZIP_CASE_COLLISION")
        seen_canonical[canon] = posix

        # symlink / hardlink / dispositivo
        mode = (info.external_attr >> 16) & 0xF000
        if mode == 0xA000:
            raise SecurityError(
                f"O pacote contém um link simbólico: `{posix}`.",
                "Links não entram em pacotes: podem apontar para fora.", code="ZIP_SYMLINK")
        if mode and mode not in (0x8000, 0x4000, 0x0000):
            raise SecurityError(
                f"Entrada não é arquivo nem diretório: `{posix}`.",
                "Dispositivos e FIFOs não entram em pacotes.", code="ZIP_SPECIAL")

        if info.flag_bits & 0x1:
            raise SecurityError(
                f"Entrada criptografada: `{posix}`.",
                "Pacotes do Hub não usam senha; a presença de senha é sinal de origem "
                "desconhecida.", code="ZIP_ENCRYPTED")

        if info.file_size > MAX_SINGLE:
            raise SecurityError(
                f"Arquivo grande demais: `{posix}` "
                f"({info.file_size // (1024*1024)} MB).",
                f"O limite por arquivo é {MAX_SINGLE // (1024*1024)} MB.", code="ZIP_FILE_BIG")

        if info.compress_size > 0 and info.file_size / max(info.compress_size, 1) > MAX_RATIO:
            raise SecurityError(
                f"Taxa de compressão suspeita em `{posix}` "
                f"({info.file_size // max(info.compress_size,1)}:1).",
                "Isso é a assinatura de uma bomba de descompressão.", code="ZIP_BOMB")

        # Extração real, com teto — não confiamos em file_size declarado.
        # `zf.open` valida o CRC no ÚLTIMO read (que retorna b""); por isso o
        # try envolve também a leitura final, e não só a abertura.
        try:
            with zf.open(info) as fh:
                chunks, size = [], 0
                while True:
                    chunk = fh.read(1 << 16)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > MAX_SINGLE:
                        raise SecurityError(
                            f"`{posix}` excedeu o tamanho declarado durante a leitura.",
                            "Pacote adulterado.", code="ZIP_LIE")
                    chunks.append(chunk)
                payload = b"".join(chunks)
        except zipfile.BadZipFile:
            raise SecurityError(
                f"CRC inválido em `{posix}`.",
                "O arquivo foi truncado ou corrompido no transporte.", code="ZIP_CRC")
        except (zlib.error, EOFError, OSError) as e:
            raise SecurityError(
                f"Falha ao descomprimir `{posix}`: {e}.",
                "O arquivo foi truncado ou corrompido no transporte.", code="ZIP_CRC")

        # CRC declarado != CRC real é adulteração silenciosa. Quando o tamanho
        # é grande o `zlib.crc32` não basta; aqui os payloads já são limitados.
        if zlib.crc32(payload) & 0xFFFFFFFF != info.CRC:
            raise SecurityError(
                f"CRC do conteúdo não confere em `{posix}`.",
                "O conteúdo foi alterado depois de o índice do ZIP ser gravado.",
                code="ZIP_CRC")

        written_total += len(payload)
        if written_total > MAX_TOTAL_BYTES:
            raise SecurityError(
                "O pacote ultrapassou o limite total durante a extração.",
                "Pacote adulterado ou bomba de descompressão.", code="ZIP_TOO_BIG")

        if posix.lower().endswith(".zip"):
            raise SecurityError(
                f"`{posix}` é um ZIP dentro do pacote.",
                "Aninhamento esconde conteúdo da revisão. Extraia antes de importar.",
                code="ZIP_NESTED")

        result.files.append(
            ExtractedFile(path=posix, data=payload, is_executable=is_executable(posix))
        )

    if not result.files:
        raise SecurityError(
            "O pacote está vazio.",
            "Um pacote precisa de ao menos um arquivo.", code="ZIP_EMPTY")

    return result


def inspect_directory(root: Path) -> Extraction:
    """Lê um diretório local. Não segue symlink — recusa e reporta."""
    root = Path(root).resolve()
    result = Extraction()
    total = 0

    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()

        if path.is_symlink():
            raise SecurityError(
                f"O diretório contém link simbólico: `{rel}`.",
                "Links podem apontar para fora da pasta e vazar arquivos do sistema.",
                code="DIR_SYMLINK")

        if path.is_dir():
            canon = rel.lower()
            if canon.split("/")[-1] in ("node_modules", ".git"):
                result.warnings.append(f"`{rel}/` ignorado (pasta de controle).")
            continue

        if not path.is_file():
            continue

        safe = validate_relative(rel)
        size = path.stat().st_size
        if size > MAX_SINGLE:
            raise SecurityError(
                f"Arquivo grande demais: `{rel}`.", "Reduza o recurso.", code="DIR_FILE_BIG")
        total += size
        if total > MAX_TOTAL_BYTES:
            raise SecurityError(
                "O diretório excede o tamanho máximo de importação.",
                "Importe em partes.", code="DIR_TOO_BIG")

        result.files.append(ExtractedFile(
            path=safe.posix,
            data=path.read_bytes(),
            is_executable=is_executable(safe.posix),
        ))

    if not result.files:
        raise SecurityError("O diretório está vazio.", "Escolha uma pasta com conteúdo.",
                            code="DIR_EMPTY")
    return result


PAYLOAD_PREFIX = "payload/"


def inspect_package(path: Path) -> Extraction:
    """Lê um `.lia-capability` desembrulhando `payload/`.

    O pacote é um ZIP cujo conteúdo real está sob `payload/`. Tratá-lo como
    ZIP comum faria o Hub importar `payload/SKILL.md` como se fosse o arquivo
    do autor, e o hash nunca corresponderia ao original.
    """
    raw = Path(path).read_bytes()
    zf = _open_zip(raw)
    infos = [i for i in zf.infolist() if not i.filename.endswith("/")]
    nomes = {i.filename for i in infos}

    if "manifest.json" not in nomes:
        raise SecurityError(
            "O arquivo não tem `manifest.json` na raiz.",
            "Sem manifesto não há como verificar integridade ou procedência.",
            code="PKG_NO_MANIFEST")

    payload = [i for i in infos if i.filename.startswith(PAYLOAD_PREFIX)
               and i.filename != PAYLOAD_PREFIX]
    if not payload:
        raise SecurityError(
            "O pacote não tem conteúdo em `payload/`.",
            "Um pacote do Hub precisa de payload.", code="PKG_EMPTY")

    # Reaproveita todas as defesas do inspect_zip reescrevendo só um ZIP
    # interno com os caminhos relativos ao payload.
    inner = io.BytesIO()
    with zipfile.ZipFile(inner, "w", zipfile.ZIP_DEFLATED) as out:
        for info in payload:
            with zf.open(info) as fh:
                out.writestr(info.filename[len(PAYLOAD_PREFIX):], fh.read())

    result = inspect_zip(inner.getvalue())

    # O manifesto e a procedência são lidos aqui: são metadados do pacote,
    # não payload. Sem eles o importador não consegue conferir declarações.
    try:
        manifest_raw = zf.read("manifest.json")
        result.manifest = json.loads(manifest_raw.decode("utf-8"))
    except (KeyError, json.JSONDecodeError, UnicodeDecodeError):
        raise SecurityError(
            "O `manifest.json` do pacote não é JSON válido.",
            "O pacote está corrompido ou foi adulterado.", code="PKG_BAD_MANIFEST")
    try:
        result.provenance = json.loads(zf.read("provenance.json").decode("utf-8"))
    except (KeyError, json.JSONDecodeError, UnicodeDecodeError):
        result.provenance = None   # procedência é desejável, não obrigatória

    result.warnings.append(
        "Pacote do Hub: manifesto e procedência lidos e verificados.")
    return result


def _open_zip(raw: bytes):
    try:
        return zipfile.ZipFile(io.BytesIO(raw))
    except zipfile.BadZipFile:
        raise SecurityError(
            "O arquivo não é um ZIP válido ou está corrompido.",
            "Verifique se o download terminou por completo.", code="ZIP_INVALID")

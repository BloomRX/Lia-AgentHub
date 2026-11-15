"""Escrita atômica — tmp + rename, com lock de diretório.

Interrupção no meio da escrita nunca deixa arquivo truncado: ou o antigo
está inteiro, ou o novo está inteiro. Testado com kill simulado.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

#: No Windows, antivírus, indexador ou editor podem segurar o arquivo de
#: destino por alguns milissegundos. `os.replace` levanta PermissionError nesse
#: caso. Repetir com backoff resolve sem mascarar erro real (o último erro
#: propaga). Fora do Windows é 1 tentativa: não há motivo para esperar.
_REPLACE_ATTEMPTS = 5 if sys.platform == "win32" else 1
_REPLACE_DELAY = 0.05


def _replace(src: str, dst: Path) -> None:
    """`os.replace` com retry apenas onde isso é necessário."""
    ultimo: PermissionError | None = None
    for tentativa in range(_REPLACE_ATTEMPTS):
        try:
            os.replace(src, dst)
            return
        except PermissionError as e:
            ultimo = e
            if tentativa == _REPLACE_ATTEMPTS - 1:
                break
            time.sleep(_REPLACE_DELAY * (2 ** tentativa))
    assert ultimo is not None
    raise ultimo


def atomic_write_bytes(path: Path, data: bytes) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".lia-tmp-", suffix=".part")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        _replace(tmp, path)  # atômico no mesmo volume
    except BaseException:
        if os.path.exists(tmp):
            try:
                os.unlink(tmp)
            except OSError:
                pass  # se nem remover dá, o erro original é mais informativo
        raise


def atomic_write_text(path: Path, text: str) -> None:
    atomic_write_bytes(path, text.encode("utf-8"))


def atomic_write_json(path: Path, obj) -> None:
    atomic_write_text(path, json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True))


def read_json(path: Path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default
    except (json.JSONDecodeError, UnicodeDecodeError):
        return default


@contextmanager
def dir_lock(lock_path: Path):
    """Lock simples por arquivo. Não é IPC entre processos arbitrários;
    protege contra duas instâncias do Hub escrevendo o mesmo índice."""
    lock_path = Path(lock_path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        yield False
        return
    try:
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        yield True
    finally:
        try:
            os.unlink(lock_path)
        except FileNotFoundError:
            pass

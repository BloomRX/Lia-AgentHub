"""Ponto de entrada do executável empacotado.

Por que este arquivo existe
---------------------------
O PyInstaller executa o script de entrada como `__main__`, SEM contexto de
pacote. Um `from . import X` dentro de `lia_agenthub/__main__.py` falha com
`ImportError: attempted relative import with no known parent package`.

Este launcher importa o pacote pelo nome absoluto, o que funciona tanto no
modo fonte quanto no modo congelado (onefile/onefolder).
"""
from __future__ import annotations

import sys


def main() -> int:
    from lia_agenthub.__main__ import main as real_main

    return real_main()


if __name__ == "__main__":
    sys.exit(main())

"""O spec do PyInstaller precisa estar coerente com o código — sem build.

O build real exige Windows (ou ao menos uma libpython compartilhada) e um
ambiente de empacotamento. Este ambiente não tem nenhum dos dois, então o
build NÃO é executado aqui. O que dá para verificar sem empacotar:

  - o spec é Python válido e aponta para arquivos que existem;
  - a UI estática entra no bundle;
  - módulos importados dinamicamente estão em hiddenimports;
  - exclusões não removem nada de que o app precise.

Isso não substitui o build. Substitui a ausência TOTAL de verificação.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
SPEC = RAIZ / "packaging/lia_agenthub.spec"
LAUNCHER = RAIZ / "packaging/launcher.py"


class TestSpecValido:
    def test_spec_e_python_valido(self):
        ast.parse(SPEC.read_text(encoding="utf-8"))

    def test_aponta_para_launcher_existente(self):
        assert LAUNCHER.is_file()
        assert "launcher.py" in SPEC.read_text(encoding="utf-8")

    def test_ui_estatica_existe_e_e_empacotada(self):
        static = RAIZ / "src/lia_agenthub/resources/static"
        assert (static / "index.html").is_file()
        assert (static / "app.js").is_file()
        assert (static / "app.css").is_file()
        assert "resources/static" in SPEC.read_text(encoding="utf-8")

    def test_cli_esta_nos_hiddenimports(self):
        """`cli` é importado dentro de função; se sumir do spec, a CLI
        funciona no código-fonte e falha só no executável."""
        assert "lia_agenthub.cli" in SPEC.read_text(encoding="utf-8")

    def test_spec_nao_crava_caminho_absoluto(self):
        """O spec é executado da raiz do repo e resolve caminhos por SPECPATH.

        Caminho absoluto cravado quebraria em qualquer outra máquina — e o
        build só falharia no Windows de quem tentasse empacotar.
        """
        texto = SPEC.read_text(encoding="utf-8")
        assert "SPECPATH" in texto
        for linha in texto.splitlines():
            s = linha.strip()
            if s.startswith(("C:\\", "C:/", "/home/", "/Users/", "/tmp/")):
                pytest.fail(f"caminho absoluto cravado no spec: {s}")


class TestExclusoesSeguras:
    def test_nao_exclui_o_que_o_app_usa(self):
        texto = SPEC.read_text(encoding="utf-8")
        inicio = texto.index("excludes=[")
        bloco = texto[inicio:inicio + 800]
        for usado in ("argparse", "json", "http", "zipfile"):
            assert f'"{usado}"' not in bloco, f"exclui módulo usado: {usado}"

    def test_exclui_backends_nao_usados(self):
        """Excluir Qt evita .exe gigante; se voltar, o tamanho salta."""
        texto = SPEC.read_text(encoding="utf-8")
        for backend in ("PyQt5", "PySide6", "gi"):
            assert backend in texto, backend

    def test_upx_desligado(self):
        """UPX dispara falso positivo de antivírus — decisão registrada."""
        assert "upx=False" in SPEC.read_text(encoding="utf-8")

    def test_console_desligado(self):
        assert "console=False" in SPEC.read_text(encoding="utf-8")


class TestBuildNaoFoiExecutado:
    """Registro honesto: o teste não finge ter empacotado."""

    def test_documenta_que_build_exige_ambiente(self):
        texto = Path(__file__).read_text(encoding="utf-8")
        assert "NÃO é executado aqui" in texto or "não é executado aqui" in texto


class TestLauncher:
    def test_launcher_importa_o_pacote_de_forma_absoluta(self):
        """Import relativo em script de entrada quebra no PyInstaller."""
        fonte = LAUNCHER.read_text(encoding="utf-8")
        for linha in fonte.splitlines():
            s = linha.strip()
            if s.startswith("from .") or s.startswith("import ."):
                pytest.fail(f"import relativo no launcher: {s}")

    def test_launcher_chama_main(self):
        assert "main(" in LAUNCHER.read_text(encoding="utf-8")

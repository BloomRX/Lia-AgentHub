"""Arquivos malformados, bombas de descompactação e colisões."""
import io
import zipfile
import zlib

import pytest

from lia_agenthub.adapters.safe_extract import inspect_zip
from lia_agenthub.domain.errors import SecurityError


def zbytes(entries: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in entries.items():
            zf.writestr(name, data)
    return buf.getvalue()


def test_zip_normal_passa():
    ex = inspect_zip(zbytes({"SKILL.md": b"---\nname: x\ndescription: y\n---\n"}))
    assert [f.path for f in ex.files] == ["SKILL.md"]


def test_zip_que_nao_e_zip_e_recusado():
    with pytest.raises(SecurityError):
        inspect_zip(b"isto nao e um zip")


def test_zip_vazio_e_recusado():
    with pytest.raises(SecurityError):
        inspect_zip(zbytes({}))


def test_colisao_de_maiusculas_e_recusada():
    """Em Windows e macOS, A.md e a.md são o mesmo arquivo."""
    with pytest.raises(SecurityError) as e:
        inspect_zip(zbytes({"A.md": b"1", "a.md": b"2"}))
    assert "ZIP_CASE_COLLISION" in str(e.value.code)


def test_zip_aninhado_e_recusado():
    interno = zbytes({"SKILL.md": b"x"})
    with pytest.raises(SecurityError) as e:
        inspect_zip(zbytes({"pacote.zip": interno}))
    assert e.value.code == "ZIP_NESTED"


def test_dot_git_dentro_do_zip_e_recusado():
    with pytest.raises(SecurityError):
        inspect_zip(zbytes({".git/config": b"[core]"}))


def test_ponto_git_disfarcado_e_recusado():
    with pytest.raises(SecurityError):
        inspect_zip(zbytes({".git./config": b"x"}))


def test_zip_criptografado_e_recusado():
    """Ligamos o bit de criptografia na central directory, onde o zipfile lê."""
    raw = bytearray(zbytes({"SKILL.md": b"---\nname: x\n---\n"}))
    idx = raw.find(b"PK\x01\x02")
    assert idx >= 0, "central directory não encontrada"
    raw[idx + 8] |= 0x01
    with pytest.raises(SecurityError) as e:
        inspect_zip(bytes(raw))
    assert e.value.code == "ZIP_ENCRYPTED"


def test_arquivo_individual_grande_demais_e_recusado():
    grande = b"x" * (65 * 1024 * 1024)
    with pytest.raises(SecurityError):
        inspect_zip(zbytes({"SKILL.md": grande}))


def test_zip_bomba_de_descompactacao_e_recusado():
    """Alta taxa de compressão com saída enorme."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("SKILL.md", b"0" * (80 * 1024 * 1024))
    assert len(buf.getvalue()) < 1_000_000, "o teste depende de comprimir bem"
    with pytest.raises(SecurityError):
        inspect_zip(buf.getvalue())


def test_muitos_arquivos_e_recusado():
    entradas = {f"f{i}.txt": b"x" for i in range(5200)}
    with pytest.raises(SecurityError):
        inspect_zip(zbytes(entradas))


def test_crc_corrompido_e_recusado():
    """CRC declarado no ZIP não corresponde ao conteúdo: adulteração."""
    import struct

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as zf:
        zf.writestr("SKILL.md", b"conteudo sintetico")
    raw = bytearray(buf.getvalue())
    raw[14:18] = struct.pack("<I", 0xDEADBEEF)        # CRC no cabeçalho local
    ci = raw.find(b"PK\x01\x02")
    assert ci > 0
    raw[ci + 16:ci + 20] = struct.pack("<I", 0xDEADBEEF)   # e na central
    with pytest.raises(SecurityError) as e:
        inspect_zip(bytes(raw))
    assert e.value.code == "ZIP_CRC"


def test_conteudo_adulterado_sem_trocar_crc_e_recusado():
    """O ataque real: troca o conteúdo e deixa o CRC antigo."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as zf:
        zf.writestr("SKILL.md", b"conteudo sintetico")
    raw = bytearray(buf.getvalue())
    pos = raw.find(b"conteudo sintetico")
    assert pos > 0
    raw[pos] = ord("X")
    with pytest.raises(SecurityError) as e:
        inspect_zip(bytes(raw))
    assert e.value.code == "ZIP_CRC"


def test_crc_declarado_correto_passa():
    """Controle positivo: sem adulteração, o mesmo caminho de código aceita."""
    ex = inspect_zip(zbytes({"SKILL.md": b"conteudo sintetico"}))
    assert ex.files[0].data == b"conteudo sintetico"


def test_diretorio_com_arquivo_grande_demais_e_recusado(tmp_path):
    from lia_agenthub.adapters.safe_extract import inspect_directory
    d = tmp_path / "grande"
    d.mkdir()
    (d / "grande.bin").write_bytes(b"x" * (65 * 1024 * 1024))
    with pytest.raises(SecurityError):
        inspect_directory(d)


def test_zip_sem_entradas_uteis_e_recusado():
    """Um ZIP só com diretórios não tem payload."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("pasta/", b"")
    with pytest.raises(SecurityError):
        inspect_zip(buf.getvalue())


def test_arquivo_solto_e_aceito_como_pacote_de_um(tmp_path, hub):
    f = tmp_path / "leiame.md"
    f.write_text("# Nota\n\nConteúdo sintético.\n", encoding="utf-8")
    report = hub.import_path(str(f))
    assert report.ok
    assert [x["path"] for x in report.files] == ["leiame.md"]

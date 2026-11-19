import json
import zipfile

from lia_agenthub.adapters.packager import verify_package

from lia_agenthub.__main__ import main


def test_oficina_versoes_e_edicao_concorrente(tmp_path, capsys):
    source = tmp_path / "SKILL.md"
    source.write_bytes(b"---\r\nname: teste\r\ndescription: Skill sintetica\r\n---\r\n\r\nPrimeira.\r\n")

    def run(*args, status=0):
        assert main(["--home", str(tmp_path / "hub"), "skill", *args]) == status
        output = capsys.readouterr()
        return json.loads(output.out) if status == 0 else output.err

    draft = run("create", str(source))
    skill_id = draft["id"]
    assert run("preview", skill_id)["validation"]["ok"]
    first = run("publish", skill_id, "1")
    assert first["text"].encode() == source.read_bytes()
    assert run("publish", skill_id, "1") == first
    source.write_bytes(source.read_bytes().replace(b"Primeira", b"Segunda"))
    assert run("edit", skill_id, "1", str(source))["generation"] == 2
    assert "Gera" in run("edit", skill_id, "1", str(source), status=1)
    assert run("diff", skill_id, "1")["body"]
    second = run("publish", skill_id, "2")
    assert second["digest"] != first["digest"]
    assert run("restore", skill_id, "2", "1")["generation"] == 3
    assert run("publish", skill_id, "3")["digest"] == first["digest"]
    assert [r["revision"] for r in run("history", skill_id)] == [3, 2, 1]
    assert run("read_revision", skill_id, "1") == first
    package = run("pack", skill_id, "1")
    assert package["ok"]
    assert verify_package(package["path"])["ok"]
    with zipfile.ZipFile(package["path"]) as bundle:
        assert bundle.read("payload/SKILL.md") == first["text"].encode("utf-8")


def test_oficina_recusa_publicar_rascunho_invalido(tmp_path, capsys):
    source = tmp_path / "SKILL.md"
    source.write_text("sem frontmatter", encoding="utf-8")
    command = ["--home", str(tmp_path / "hub"), "skill"]
    assert main([*command, "create", str(source)]) == 0
    skill_id = json.loads(capsys.readouterr().out)["id"]
    assert main([*command, "publish", skill_id, "1"]) == 1
    assert main([*command, "history", skill_id]) == 0
    assert json.loads(capsys.readouterr().out) == []

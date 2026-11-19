import json
import zipfile
from pathlib import Path

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
    listed, = run("list")
    assert listed == {"id": skill_id, "generation": 1, "name": "teste",
                      "latestRevision": None, "origin": None}
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
    assert run("list")[0]["latestRevision"] == 3
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


def test_materializa_revisao_local_sem_banco_da_oficina(tmp_path, capsys):
    package_home = tmp_path / "hub"
    source = tmp_path / "SKILL.md"
    source.write_text(
        "---\nname: piloto\ndescription: Skill sintetica\n---\n\nConteudo.\n",
        encoding="utf-8",
    )

    def run(home, *args, status=0):
        assert main(["--home", str(home), "skill", *map(str, args)]) == status
        output = capsys.readouterr()
        return json.loads(output.out) if status == 0 else output.err

    drafted = run(package_home, "create", source)
    run(package_home, "publish", drafted["id"], 1)
    packed = run(package_home, "pack", drafted["id"], 1, "--profile", "lia-studio")
    lock = tmp_path / "skill-lock.json"
    lock.write_text(json.dumps(packed["lock"]), encoding="utf-8")
    host_home = tmp_path / "host-home"
    destination = tmp_path / "materialized"
    materialized = run(host_home, "materialize", lock, packed["path"], destination)
    assert materialized["treeSha256"] == packed["lock"]["treeSha256"]
    assert (destination / "SKILL.md").read_bytes() == source.read_bytes()
    assert not host_home.exists()
    assert "destino já existe" in run(
        host_home, "materialize", lock, packed["path"], destination, status=1,
    )
    invalid_package = tmp_path / "invalid.lia-capability"
    invalid_package.write_bytes(Path(packed["path"]).read_bytes() + b"changed")
    rejected_destination = tmp_path / "rejected"
    assert "SHA-256" in run(
        host_home, "materialize", lock, invalid_package, rejected_destination, status=1,
    )
    assert not rejected_destination.exists()

    source.write_bytes(source.read_bytes().replace(b"Conteudo", b"Atualizado"))
    run(package_home, "edit", drafted["id"], 1, source)
    run(package_home, "publish", drafted["id"], 2)
    updated = run(package_home, "pack", drafted["id"], 2, "--profile", "lia-studio")
    updated_lock = tmp_path / "updated.json"
    updated_lock.write_text(json.dumps(updated["lock"]), encoding="utf-8")
    next_destination = tmp_path / "updated"
    run(host_home, "materialize", updated_lock, updated["path"], next_destination)
    assert (next_destination / "SKILL.md").read_bytes() == source.read_bytes()
    rollback = tmp_path / "rollback"
    run(host_home, "materialize", lock, packed["path"], rollback)
    assert (rollback / "SKILL.md").read_bytes() == (destination / "SKILL.md").read_bytes()


def test_anexos_sao_versionados_e_restaurados(tmp_path, capsys):
    skill = tmp_path / "fonte"
    skill.mkdir()
    (skill / "SKILL.md").write_text(
        "---\nname: anexos\ndescription: Skill com anexos\n---\n\n[Guia](guia.md)\n",
        encoding="utf-8",
    )
    guide = skill / "guia.md"
    guide.write_bytes(b"original")

    def run(*args, status=0):
        assert main(["--home", str(tmp_path / "hub"), "skill", *map(str, args)]) == status
        output = capsys.readouterr()
        return json.loads(output.out) if status == 0 else output.err

    skill_id = run("create", skill)["id"]
    assert run("preview", skill_id)["files"] == ["guia.md"]
    run("publish", skill_id, 1)
    guide.write_bytes(b"alterado")
    run("edit", skill_id, 1, skill)
    assert run("diff", skill_id, 1)["files"] == {"guia.md": "changed"}
    run("publish", skill_id, 2)
    run("restore", skill_id, 2, 1)
    run("publish", skill_id, 3)
    packed = run("pack", skill_id, 3, "--profile", "lia-studio")
    lock = tmp_path / "lock.json"
    lock.write_text(json.dumps(packed["lock"]), encoding="utf-8")
    destination = tmp_path / "consumo"
    run("materialize", lock, packed["path"], destination)
    assert (destination / "guia.md").read_bytes() == b"original"

    internal = skill / ".lia"
    internal.mkdir()
    (internal / "capability.json").write_text("{}", encoding="utf-8")
    assert "Entrada proibida" in run("edit", skill_id, 3, skill, status=1)
    assert run("preview", skill_id)["generation"] == 3


def test_procedencia_git_fica_vinculada_ao_snapshot_e_ao_pacote(tmp_path, capsys):
    from lia_agenthub.domain.integrity import sha256_file, tree_hash

    source = tmp_path / "SKILL.md"
    source.write_text(
        "---\nname: origem\ndescription: Skill de origem sintetica\n---\n\nCorpo.\n",
        encoding="utf-8",
    )
    origin = {
        "repository": "https://example.invalid/lia/studio",
        "commit": "a" * 40,
        "path": ".agents/skills/origem/SKILL.md",
        "author": None,
        "maintainer": "Studio",
        "licensePath": "LICENSE",
        "licenseSha256": "b" * 64,
        "treeSha256": "c" * 64,
    }
    evidence = tmp_path / "origin.json"
    command = ["--home", str(tmp_path / "hub"), "skill"]

    def run(*args, status=0):
        assert main([*command, *map(str, args)]) == status
        output = capsys.readouterr()
        return json.loads(output.out) if status == 0 else output.err

    evidence.write_text(json.dumps(origin), encoding="utf-8")
    assert "hash de origem" in run("create", source, "--origin", evidence, status=1)
    origin["treeSha256"] = tree_hash({"SKILL.md": sha256_file(source)})
    evidence.write_text(json.dumps(origin), encoding="utf-8")
    skill_id = run("create", source, "--origin", evidence)["id"]
    assert run("publish", skill_id, 1)["origin"] == {"kind": "git-snapshot", **origin}
    package = run("pack", skill_id, 1)
    with zipfile.ZipFile(package["path"]) as bundle:
        provenance = json.loads(bundle.read("provenance.json"))
        manifest = json.loads(bundle.read("manifest.json"))
    assert provenance["source"]["workshopOrigin"] == {"kind": "git-snapshot", **origin}
    assert not manifest["license"]["redistributable"]


def test_fork_preserva_atribuicao_e_anexos_sem_conceder_redistribuicao(tmp_path, capsys):
    from lia_agenthub.domain.integrity import sha256_file, tree_hash

    source = tmp_path / "source"
    source.mkdir()
    text = source / "SKILL.md"
    guide = source / "guia.md"
    text.write_text(
        "---\nname: origem\ndescription: Skill de origem sintetica\n---\n\n[Guia](guia.md)\n",
        encoding="utf-8",
    )
    guide.write_bytes(b"Anexo")
    tree = tree_hash({path.name: sha256_file(path) for path in (text, guide)})
    origin = tmp_path / "origin.json"
    origin.write_text(json.dumps({
        "repository": "https://example.invalid/lia/studio",
        "commit": "a" * 40,
        "path": ".agents/skills/origem/SKILL.md",
        "author": "Equipe de origem",
        "maintainer": "Studio",
        "licensePath": "LICENSE",
        "licenseSha256": "b" * 64,
        "treeSha256": tree,
    }), encoding="utf-8")
    command = ["--home", str(tmp_path / "hub"), "skill"]

    def run(*args, status=0):
        assert main([*command, *map(str, args)]) == status
        output = capsys.readouterr()
        return json.loads(output.out) if status == 0 else output.err

    upstream = run("create", source, "--origin", origin)["id"]
    run("publish", upstream, 1)
    evidence = tmp_path / "autorizacao.txt"
    evidence.touch()
    assert "evidência" in run("fork", upstream, 1, "--copy-evidence", evidence, status=1)
    assert len(run("list")) == 1
    evidence.write_text("Autorizacao de copia para este teste sintetico.", encoding="utf-8")
    fork = run("fork", upstream, 1, "--copy-evidence", evidence)["id"]
    assert fork != upstream
    assert run("preview", fork)["files"] == ["guia.md"]
    lineage = run("publish", fork, 1)["origin"]
    assert lineage["parentOrigin"]["author"] == "Equipe de origem"
    assert lineage["parentSkillId"] == f"urn:lia:cap:{upstream}"
    assert lineage["parentRevision"] == 1
    assert lineage["parentTreeSha256"] == tree
    assert lineage["copyBasisSha256"] == sha256_file(evidence)
    package = run("pack", fork, 1)
    with zipfile.ZipFile(package["path"]) as bundle:
        assert json.loads(bundle.read("provenance.json"))["source"]["workshopOrigin"] == lineage
        assert not json.loads(bundle.read("manifest.json"))["license"]["redistributable"]
        assert bundle.read("payload/guia.md") == b"Anexo"

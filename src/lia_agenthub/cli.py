"""CLI de desenvolvimento — `validate`, `pack`, `export`, `diagnostico`, `index`,
`inventory`.

Existe porque nem todo fluxo do produto precisa de janela. O `.exe` abre a
interface; a CLI serve a quem está automatizando ou depurando. As duas usam o
mesmo `AgentHub`, então não há dois comportamentos para manter.

**O que a CLI NÃO faz:** conectar MCP, executar Skill, instalar coisa alguma.
É a mesma fronteira da interface, verificada pelos mesmos testes.

Códigos de saída (contrato estável, usado por scripts):
    0  sucesso
    1  o recurso tem erro bloqueante / a operação foi recusada
    2  uso incorreto, caminho inexistente ou falha de leitura
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .app import AgentHub


def _json(obj) -> None:
    # Redirecionamentos no Windows podem usar uma página de código legada.
    print(json.dumps(obj, ensure_ascii=True, indent=2))


def _erro(msg: str, codigo: int = 2) -> int:
    print(f"erro: {msg}", file=sys.stderr)
    return codigo


def _hub(args) -> AgentHub:
    from .adapters.paths_resolver import resolve_locations
    return AgentHub(resolve_locations(Path(args.home) if args.home else None))


# --------------------------------------------------------------------------
def cmd_diagnostico(args) -> int:
    from .adapters.paths_resolver import resolve_locations
    locs = resolve_locations(Path(args.home) if args.home else None)
    print("Caminhos resolvidos (fonte da verdade: arquivos em disco)")
    for chave, valor in locs.as_dict().items():
        p = Path(str(valor))
        marca = "OK " if p.exists() else "-- "
        print(f"  {marca}{chave:12} {valor}")
    if args.json:
        _json(locs.as_dict())
    return 0


def cmd_validate(args) -> int:
    """Valida um caminho ANTES de importar, ou um id já na biblioteca."""
    alvo = args.alvo
    hub = _hub(args)
    caminho = Path(alvo)

    if not caminho.exists():
        # Pode ser um id da biblioteca.
        try:
            detalhe = hub.detail(alvo)
        except Exception:
            return _erro(f"não é caminho existente nem id na biblioteca: {alvo}")
        rel = hub.validate(alvo)
        return _imprimir_validacao(rel, nome=detalhe.get("name", alvo))

    if caminho.is_dir():
        skill = caminho / "SKILL.md"
        if not skill.is_file():
            return _erro(f"diretório sem SKILL.md: {caminho}")
        texto = skill.read_text(encoding="utf-8", errors="replace")
        from .domain.skills import check_references, folder_name_do_recurso, validate_skill
        arquivos = {str(p.relative_to(caminho)).replace("\\", "/")
                    for p in caminho.rglob("*") if p.is_file()}
        pasta = folder_name_do_recurso(str(caminho), list(arquivos))
        issues = validate_skill(texto, folder_name=pasta)
        issues.extend(check_references(texto, arquivos, folder_name=pasta))
        rel = _relatorio(issues)
        return _imprimir_validacao(rel, nome=caminho.name)

    if caminho.suffix.lower() in (".zip", ".lia-capability"):
        return _erro("validação de pacote usa `lia-agenthub verify-package <arquivo>`")

    return _erro(f"não sei validar: {caminho}")


def _relatorio(issues) -> dict:
    return {
        "issues": [i.as_dict() for i in issues],
        "summary": {s: sum(1 for i in issues if i.severity.value == s)
                    for s in ("error", "warning", "info", "review")},
        "note": "Validação estrutural. Não avalia se o conteúdo é seguro.",
    }


def _imprimir_validacao(rel: dict, *, nome: str) -> int:
    s = rel["summary"]
    print(f"Validação de `{nome}`")
    print(f"  erros: {s.get('error', 0)}  avisos: {s.get('warning', 0)}  "
          f"info: {s.get('info', 0)}  revisão: {s.get('review', 0)}")
    for i in rel["issues"]:
        print(f"  [{i['severity']:7}] {i['code']}: {i['message']}")
    if rel.get("note"):
        print(f"\n{rel['note']}")
    return 1 if s.get("error", 0) else 0


def cmd_pack(args) -> int:
    """Empacota em `.lia-capability` (é o `export` com destino explícito)."""
    hub = _hub(args)
    destino = args.dest or None
    r = hub.export(args.id, target=args.target, destination=destino)
    if not r.get("ok"):
        print(f"recusado: {r.get('refusedReason', r.get('reason', 'motivo não informado'))}",
              file=sys.stderr)
        if r.get("hint"):
            print(f"dica: {r['hint']}", file=sys.stderr)
        return 1
    print(f"pacote: {r['path']}")
    for chave in ("contentHash", "treeHash"):
        if r.get(chave):
            print(f"  {chave}: {r[chave]}")
    for aviso in r.get("warnings") or []:
        print(f"  aviso: {aviso}")
    return 0


def cmd_export(args) -> int:
    return cmd_pack(args)


def cmd_index(args) -> int:
    hub = _hub(args)
    if args.publish:
        r = hub.publish_index()
        if not r.get("ok"):
            print(f"publicação recusada: {r.get('reason', '')}", file=sys.stderr)
            return 1
        print(f"índice: {r['path']} ({r['count']} capacidade(s))")
        return 0
    idx = hub.read_index()
    if args.json:
        _json(idx)
        return 0
    caps = (idx or {}).get("capabilities") or []
    print(f"{len(caps)} capacidade(s) no índice")
    for c in caps:
        lic = c.get("license") or "desconhecida"
        print(f"  {c.get('id'):32} {c.get('trust'):16} {lic}")
    return 0


def cmd_verify_package(args) -> int:
    hub = _hub(args)
    r = hub.verify_package(args.arquivo)
    if args.json:
        _json(r)
    else:
        estado = "íntegro" if r.get("ok") else "ALTERADO ou inválido"
        print(f"{args.arquivo}: {estado}")
        # `verify_package` explica a recusa em `problems`, não em `reason`.
        # Ler a chave errada fazia a CLI dizer apenas "ALTERADO" sem por quê.
        for problema in r.get("problems") or []:
            print(f"  - {problema}")
        if r.get("treeHashOk") is not None:
            print(f"  treeHash confere: {'sim' if r['treeHashOk'] else 'não'}")
        print("  Isto prova integridade, não autoria.")
    return 0 if r.get("ok") else 1


def cmd_inventory(args) -> int:
    """Recebe inventário v1. `--preview` é o padrão; gravar exige `--commit`.

    O padrão ser dry-run não é detalhe de ergonomia: sem `--commit` nada é
    gravado, então um comando errado não deixa recibo nem índice.
    """
    from .adapters.inventory_intake import IntakeError

    acao = args.inventory_cmd
    hub = _hub(args)

    if acao == "state":
        estado = hub.inventory_state()
        if args.json:
            _json(estado)
        elif not estado.get("ok"):
            print(f"erro: {estado.get('error')}", file=sys.stderr)
        else:
            print(f"{estado['count']} identidade(s) conhecida(s) — teto: inventoried")
            for r in estado["records"]:
                print(f"  {r['id']:46} {r['kind'] or '-':14} "
                      f"{r['issuerProject'] or '-':16} {r['lastRevision']}")
        return 0 if estado.get("ok") else 1

    if acao == "receipts":
        recibos = hub.inventory_receipts()
        if args.json:
            _json({"ok": True, "receipts": recibos})
        else:
            print(f"{len(recibos)} recibo(s)")
            for r in recibos:
                print(f"  {r.get('receiptId','')}  {r.get('state',''):12} "
                      f"{r.get('issuerProject',''):14} {r.get('revision','')}")
        return 0

    if acao == "receipt":
        try:
            recibo = hub.inventory_receipt(args.recibo_id)
        except IntakeError as e:
            return _erro(str(e))
        if args.json:
            _json(recibo)
        else:
            print(f"Recibo {recibo.get('receiptId')} — estado {recibo.get('state')}")
            print(f"  emissor   {recibo.get('issuerProject')}")
            print(f"  inventário {recibo.get('inventoryId')} rev {recibo.get('revision')}")
            print(f"  arquivo   {recibo.get('fileName')} sha256 {recibo.get('fileDigest')}")
            print(f"  recebido  {recibo.get('receivedAt')}")
            print(f"  registros {recibo.get('recordCount')} "
                  f"(admitidos {recibo.get('admitted')}, "
                  f"em quarentena {recibo.get('quarantined')})")
            for a in recibo.get("findings") or []:
                print(f"    [{a.get('severity')}] {a.get('code')}: {a.get('message')}")
            print(f"  {recibo.get('note','')}")
        return 0

    # preview / receive
    try:
        plano = (hub.inventory_receive(args.arquivo) if args.commit
                 else hub.inventory_preview(args.arquivo))
    except IntakeError as e:
        return _erro(str(e))

    if args.json:
        _json(plano)
    else:
        if plano["committed"]:
            marca = "RECEBIDO"
        elif args.commit:
            # Pediu para gravar e não gravou: dizer "pré-visualização" aqui
            # esconderia que o recebimento foi recusado.
            marca = "RECUSADO (nada gravado)"
        else:
            marca = "PRÉ-VISUALIZAÇÃO (nada gravado)"
        print(f"{marca} — estado: {plano['state']}")
        env = plano.get("envelope")
        if env:
            print(f"  emissor   {env['issuer'].get('project')}")
            print(f"  inventário {env['inventoryId']} rev {env['revision']}")
            print(f"  gerado em {env['generatedAt']} | completo: {env['complete']}")
            print(f"  arquivo   sha256 {env['fileDigest']}")
        if plano.get("classifications"):
            print("  classificação:")
            for classe, qtd in sorted(plano["classifications"].items()):
                print(f"    {classe:20} {qtd}")
        for a in plano.get("findings") or []:
            local = f" ({a['where']})" if a.get("where") else ""
            print(f"  [{a['severity']}] {a['code']}: {a['message']}{local}")
            if a.get("hint"):
                print(f"      -> {a['hint']}")
        if plano.get("feedProblem"):
            print(f"  conflito de feed: {plano['feedProblem']}")
        if plano.get("receiptPath"):
            print(f"  recibo    {plano['receiptPath']}")
        if plano.get("quarantinePath"):
            print(f"  retenção  {plano['quarantinePath']}")
            print("            registros não admitidos ficam retidos para revisão; "
                  "o estado do documento é o acima")
        print("  Fronteira: nada foi executado, instalado ou conectado. "
              "Teto de estado: inventoried.")

    if not plano["ok"]:
        return 1
    return 0


# --------------------------------------------------------------------------
def cmd_skill(args) -> int:
    from .adapters.paths_resolver import resolve_locations
    import stat

    from .adapters.safe_extract import MAX_FILES, MAX_SINGLE, inspect_directory, stat_import_path
    from .domain.unicode_policy import has_bom
    from .adapters.skill_workshop import SkillWorkshop
    from .domain.errors import SecurityError

    locations = resolve_locations(Path(args.home) if args.home else None)
    workshop = SkillWorkshop(locations.home / "Oficina" / "skills.sqlite3")
    parameters = {}
    for name in ("skill_id", "generation", "revision", "reason"):
        if hasattr(args, name):
            parameters[name] = getattr(args, name)
    try:
        if hasattr(args, "arquivo"):
            source = Path(args.arquivo)
            metadata = stat_import_path(source)
            if stat.S_ISDIR(metadata.st_mode):
                entries = inspect_directory(source).files
                if len(entries) > MAX_FILES:
                    return _erro("A pasta excede o limite de arquivos.", 1)
                files = {entry.path: entry.data for entry in entries}
                if "SKILL.md" not in files:
                    return _erro("A pasta precisa de um SKILL.md na raiz.", 1)
                seen_paths = {}
                for path, data in files.items():
                    parts = path.split("/")
                    if has_bom(data):
                        return _erro(f"Arquivo começa com BOM: {path}", 1)
                    for length in range(1, len(parts) + 1):
                        prefix = "/".join(parts[:length])
                        if seen_paths.setdefault(prefix.casefold(), prefix) != prefix:
                            return _erro(f"Colisão de caminhos na pasta: {path}", 1)
                parameters["text"] = files.pop("SKILL.md").decode("utf-8")
                parameters["files"] = files
            else:
                if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > MAX_SINGLE:
                    return _erro("SKILL.md inválido ou grande demais.", 1)
                with source.open("rb") as stream:
                    data = stream.read(MAX_SINGLE + 1)
                if len(data) > MAX_SINGLE or has_bom(data):
                    return _erro("SKILL.md excede o limite ou começa com BOM.", 1)
                parameters["text"] = data.decode("utf-8")
        if getattr(args, "origin", None):
            origin_path = Path(args.origin)
            metadata = stat_import_path(origin_path)
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > 65536:
                return _erro("O manifesto de origem precisa ser um JSON de até 64 KiB.", 1)
            parameters["origin"] = json.loads(origin_path.read_bytes())
        if args.skill_cmd == "fork":
            from .domain.integrity import sha256_bytes

            evidence = Path(args.copy_evidence)
            metadata = stat_import_path(evidence)
            if not stat.S_ISREG(metadata.st_mode) or not 0 < metadata.st_size <= 65536:
                return _erro("A evidência de cópia precisa ser um arquivo de até 64 KiB.", 1)
            with evidence.open("rb") as stream:
                content = stream.read(65537)
            if not content.strip() or len(content) > 65536:
                return _erro("A evidência de cópia está vazia ou excede 64 KiB.", 1)
            parameters["copy_basis_sha256"] = sha256_bytes(content)
        if args.skill_cmd == "pack":
            from tempfile import TemporaryDirectory
            from .adapters.safe_extract import Extraction, ExtractedFile
            from .domain.paths import looks_like_script
            from .adapters.skill_consumer import dependency_pin, read_lock

            if len(args.requires) > 100:
                return _erro("O manifesto aceita no máximo 100 dependências.", 1)
            if args.requires and not args.profile:
                return _erro("--requires precisa de --profile para gerar o manifesto.", 1)
            pins = [read_lock(Path(path)) for path in args.requires]
            if any(pin["profile"] != args.profile for pin in pins):
                return _erro("O manifesto de dependência precisa usar o mesmo perfil.", 1)
            if len({pin["skillId"] for pin in pins}) != len(pins):
                return _erro("Manifesto de dependência repetido.", 1)
            record = workshop.read_revision(**parameters)
            if any(pin["skillId"] == f"urn:lia:cap:{record['id']}" for pin in pins):
                return _erro("A Skill não pode depender dela mesma.", 1)
            destination = Path(args.dest).resolve() if args.dest else locations.exports
            with TemporaryDirectory(prefix="lia-skill-") as temporary:
                hub = AgentHub(resolve_locations(Path(temporary)))
                files = workshop.payload(**parameters)
                archive = Extraction(files=[
                    ExtractedFile(path, data, looks_like_script(tuple(path.split("/"))))
                    for path, data in files.items()
                ])
                upstream = f"urn:lia:cap:{record['id']}:{record['revision']}"
                origin = record["origin"]
                source_extra = {"workshopOrigin": origin} if origin is not None else None
                report = hub.importer.from_extraction(archive, upstream=upstream,
                                                       source_extra=source_extra)
                if not report.ok:
                    return _erro(report.blocked_reason, 1)
                hub.promote(report.capability_id)
                result = hub.export(report.capability_id, destination=str(destination))
                if not result["ok"]:
                    return _erro(result["refusedReason"], 1)
                if args.profile:
                    verified = hub.verify_package(result["path"])
                    result["lock"] = {
                        "lockVersion": 1,
                        "skillId": f"urn:lia:cap:{record['id']}",
                        "revision": record["revision"],
                        "capabilityId": report.capability_id,
                        "version": verified["manifest"]["version"],
                        "packageSha256": result["packageHash"],
                        "treeSha256": verified["computedTreeHash"],
                        "profile": args.profile,
                        "dependencies": [dependency_pin(pin) for pin in pins],
                    }
            _json(result)
            return 0
        operation = getattr(workshop, args.skill_cmd)
        result = operation(**parameters)
    except (ValueError, SecurityError) as error:
        return _erro(str(error), 1)
    _json(result)
    return 0


def cmd_materialize_skill(args) -> int:
    import zipfile

    from .adapters.skill_consumer import materialize
    from .domain.errors import SecurityError

    try:
        sources = tuple((Path(pin), Path(directory)) for pin, directory in args.dependency)
        revocations = Path(args.revocations) if args.revocations else None
        result = materialize(Path(args.lock), Path(args.package), Path(args.dest),
                             dependencies=sources, revocations=revocations)
    except (ValueError, KeyError, TypeError, SecurityError, zipfile.BadZipFile) as error:
        return _erro(str(error), 1)
    _json(result)
    return 0


def _skill_parser(sub) -> None:
    skill = sub.add_parser("skill", help="edita e versiona Skills na oficina local")
    actions = skill.add_subparsers(dest="skill_cmd", required=True)
    for action in ("create", "edit", "preview", "publish", "history", "diff", "restore", "read_revision", "pack"):
        command = actions.add_parser(action)
        if action != "create":
            command.add_argument("skill_id")
        if action in ("edit", "publish", "restore"):
            command.add_argument("generation", type=int)
        if action in ("diff", "restore", "read_revision", "pack"):
            command.add_argument("revision", type=int)
        if action in ("create", "edit"):
            command.add_argument("arquivo", help="SKILL.md em UTF-8 ou pasta de Skill com anexos")
        if action == "create":
            command.add_argument("--origin", help="manifesto JSON de procedência do snapshot Git")
        if action == "pack":
            command.add_argument("--dest", help="diretório de destino do backup privado")
            command.add_argument("--profile", help="perfil do host para gerar manifesto de consumo")
            command.add_argument("--requires", action="append", default=[],
                                 help="fixa uma dependência pelo manifesto de consumo local")
        command.set_defaults(func=cmd_skill)

    fork = actions.add_parser("fork", help="deriva um rascunho de uma revisão publicada")
    fork.add_argument("skill_id")
    fork.add_argument("revision", type=int)
    fork.add_argument("--copy-evidence", required=True, help="documento local de autorização de cópia")
    fork.set_defaults(func=cmd_skill)

    listing = actions.add_parser("list", help="lista rascunhos e revisões da oficina")
    listing.set_defaults(func=cmd_skill, skill_cmd="list_skills")

    revoke = actions.add_parser("revoke", help="retira uma revisão de circulação")
    revoke.add_argument("skill_id")
    revoke.add_argument("revision", type=int)
    revoke.add_argument("--reason", required=True)
    revoke.set_defaults(func=cmd_skill)

    revocations = actions.add_parser("revocations", help="exporta a lista local de revogações")
    revocations.set_defaults(func=cmd_skill)

    materialize = actions.add_parser("materialize", help="materializa uma revisão local fixada")
    materialize.add_argument("lock", help="manifesto de consumo JSON")
    materialize.add_argument("package", help="pacote .lia-capability local")
    materialize.add_argument("dest", help="novo diretório de destino")
    materialize.add_argument("--dependency", action="append", nargs=2, default=[],
                             metavar=("LOCK", "DIRETORIO"), help="dependência local já materializada")
    materialize.add_argument("--revocations", help="lista local de revisões revogadas")
    materialize.set_defaults(func=cmd_materialize_skill)


def build_parser(prog: str = "lia-agenthub") -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog=prog,
        description="CLI de desenvolvimento do Lia Agent Hub. "
                    "Nada é executado e nada é baixado.")
    ap.add_argument("--home", help="raiz de dados alternativa")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("diagnostico", help="imprime caminhos resolvidos")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_diagnostico)

    p = sub.add_parser("validate", help="valida um caminho ou um id da biblioteca")
    p.add_argument("alvo")
    p.set_defaults(func=cmd_validate)

    for nome, funcao, ajuda in (
            ("pack", cmd_pack, "empacota em .lia-capability"),
            ("export", cmd_export, "igual a pack; nome usado pela interface")):
        p = sub.add_parser(nome, help=ajuda)
        p.add_argument("id")
        p.add_argument("--target", default="private",
                       choices=("private", "shared", "public"))
        p.add_argument("--dest", help="diretório de destino")
        p.set_defaults(func=funcao)

    p = sub.add_parser("index", help="lê ou publica o índice")
    p.add_argument("--publish", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_index)

    p = sub.add_parser("inventory", help="recebe inventário de capacidades v1")
    p.add_argument("inventory_cmd", choices=("preview", "receive", "state",
                                             "receipts", "receipt"))
    p.add_argument("arquivo", nargs="?", help="arquivo .json do inventário")
    p.add_argument("recibo_id", nargs="?", help="id do recibo, para `receipt`")
    p.add_argument("--commit", action="store_true",
                   help="grava o recebimento; sem esta flag é só pré-visualização")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_inventory)

    _skill_parser(sub)

    p = sub.add_parser("verify-package", help="verifica integridade de um pacote")
    p.add_argument("arquivo")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_verify_package)

    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except FileNotFoundError as e:
        return _erro(f"arquivo não encontrado: {e}")
    except PermissionError as e:
        return _erro(f"sem permissão: {e}")
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())

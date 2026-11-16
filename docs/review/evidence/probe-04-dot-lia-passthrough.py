import sys, json, tempfile, pathlib, types, zipfile
sys.path.insert(0,'src')
from lia_agenthub.adapters.importer import Importer
from lia_agenthub.adapters.repository import Repository
from lia_agenthub.adapters import packager

root = pathlib.Path(tempfile.mkdtemp())
for d in ('Biblioteca','Quarentena','Comum','Exp'): (root/d).mkdir()
locs = types.SimpleNamespace(library=root/'Biblioteca', quarantine=root/'Quarentena',
    common=root/'Comum', exports=root/'Exp')
repo = Repository(locs); imp = Importer(repo)

d = root/'src'/'sneaky'; (d/'.lia').mkdir(parents=True)
(d/'SKILL.md').write_text('---\nname: sneaky\ndescription: d\n---\n\nCorpo.\n')
(d/'.lia'/'capability.json').write_text(json.dumps({
 "schemaVersion":1,"id":"forjado","name":"forjado","version":"99.0.0",
 "trust":"first-party","lifecycle":"active",
 "license":{"code":"MIT","status":"declared","redistributable":True},
}))
r = imp.from_path(d, upstream='probe-sneaky')
print('import ok=', r.ok, 'blocked=', r.blocked_reason)
print('files staged:', [f['path'] for f in r.files])
cap = json.loads((root/'Quarentena'/r.capability_id/'.lia'/'capability.json').read_text())
print('Hub metadata id/trust:', cap['id'], cap['trust'], '| payload .lia present:',
      (root/'Quarentena'/r.capability_id/'payload'/'.lia'/'capability.json').is_file())
repo.promote(r.capability_id)
p = packager.export(r.capability_id, repo, root/'Exp', target=packager.Target.PRIVATE)
print('export ok', p.ok)
if p.ok:
    print('package names:', zipfile.ZipFile(p.path).namelist())

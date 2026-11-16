import sys, json, tempfile, pathlib, types
sys.path.insert(0,'src')
from lia_agenthub.adapters.importer import Importer
from lia_agenthub.adapters.repository import Repository
from lia_agenthub.adapters import packager

root = pathlib.Path(tempfile.mkdtemp())
for d in ('Biblioteca','Quarentena','Comum','Exp'): (root/d).mkdir()
locs = types.SimpleNamespace(library=root/'Biblioteca', quarantine=root/'Quarentena',
    common=root/'Comum', exports=root/'Exp')
repo = Repository(locs); imp = Importer(repo)
d = root/'src'/'origem-real'; d.mkdir(parents=True)
(d/'SKILL.md').write_text('---\nname: origem-real\ndescription: d\n---\n\nCorpo.\n')
r = imp.from_path(d, upstream='BloomRX/Lia-Studio@203b60f:.agents/skills/origem-real')
repo.promote(r.capability_id)
before = json.loads((root/'Biblioteca'/r.capability_id/'.lia'/'provenance.json').read_text())
print('provenance BEFORE:', json.dumps(before, indent=1)[:400])
p = packager.export(r.capability_id, repo, root/'Exp', target=packager.Target.PRIVATE)
print('\nexport ->', p.ok, pathlib.Path(p.path).name)
# reimport the package into a fresh library
root2 = root/'r2'
for x in ('Biblioteca','Quarentena','Comum','Exp'): (root2/x).mkdir(parents=True)
locs2 = types.SimpleNamespace(library=root2/'Biblioteca', quarantine=root2/'Quarentena',
    common=root2/'Comum', exports=root2/'Exp')
repo2 = Repository(locs2); imp2 = Importer(repo2)
r2 = imp2.from_path(p.path)
print('reimport ok', r2.ok, r2.blocked_reason)
after = json.loads((root2/'Quarentena'/r2.capability_id/'.lia'/'provenance.json').read_text())
print('\nprovenance AFTER :', json.dumps(after, indent=1)[:400])
cap2 = json.loads((root2/'Quarentena'/r2.capability_id/'.lia'/'capability.json').read_text())
print('\ncapability.source AFTER:', json.dumps(cap2['source'], indent=1))
print('\nsame treeHash?', before['hashes']['treeHash'] == after['hashes']['treeHash'])

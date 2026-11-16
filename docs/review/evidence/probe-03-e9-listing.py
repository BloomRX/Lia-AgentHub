import sys, json, tempfile, pathlib, types
sys.path.insert(0,'src')
from lia_agenthub.adapters.repository import Repository
from lia_agenthub.app import AgentHub, SearchQuery

root = pathlib.Path(tempfile.mkdtemp())
for d in ('Biblioteca','Quarentena','Comum','Exp','Config'): (root/d).mkdir()
locs = types.SimpleNamespace(library=root/'Biblioteca', quarantine=root/'Quarentena',
    common=root/'Comum', exports=root/'Exp', config=root/'Config',
    ensure=lambda: None)
hub = AgentHub.__new__(AgentHub)
hub.locations = locs
hub.repo = Repository(locs)
from lia_agenthub.adapters.importer import Importer
hub.importer = Importer(hub.repo)

def mk(name, body='Corpo.'):
    d = root/'src'/name; d.mkdir(parents=True)
    (d/'SKILL.md').write_text(f"---\nname: {name}\ndescription: d\n---\n\n{body}\n")
    return d
d1 = mk('ativa'); d2 = mk('na-quarentena')
r1 = hub.importer.from_path(d1); hub.repo.promote(r1.capability_id)
r2 = hub.importer.from_path(d2)

print('promoted:', r1.capability_id, '| quarantined:', r2.capability_id)
print('items(lifecycle=None) ->', [i['id'] for i in hub.items(SearchQuery(lifecycle=None))])
print('items(lifecycle="all")->', [i['id'] for i in hub.items(SearchQuery(lifecycle="all"))])
print('items(quarantined)   ->', [i['id'] for i in hub.items(SearchQuery(lifecycle='quarantined'))])
print('items(default)       ->', [i['id'] for i in hub.items()])

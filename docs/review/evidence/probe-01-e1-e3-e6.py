import sys, json, tempfile, pathlib, types
sys.path.insert(0,'src')
from lia_agenthub.adapters.importer import Importer
from lia_agenthub.adapters.repository import Repository

root = pathlib.Path(tempfile.mkdtemp())
for d in ('Biblioteca','Quarentena'): (root/d).mkdir()
locs = types.SimpleNamespace(library=root/'Biblioteca', quarantine=root/'Quarentena',
    common=root/'Comum', exports=root/'Exp')
repo = Repository(locs); imp = Importer(repo)

skill = """---
name: demo-skill
description: Uma descrição completa que existe no frontmatter.
license: MIT
compatibility: Exige Windows.
metadata:
  author: BloomRX
  version: "19"
  tags: a, b
---

# Demo
Corpo.
"""
folder = root/'src'/'demo-skill'
(folder/'references').mkdir(parents=True)
(folder/'SKILL.md').write_text(skill)
(folder/'references'/'x.md').write_text('# x')
# LICENSE at payload root vs repo root
(folder/'LICENSE').write_text('MIT License\n\nCopyright (c) 2026')
r = imp.from_path(folder, upstream='probe')
print('blocked:', r.blocked_reason)
print('warnings:'); [print('  -',w) for w in r.warnings]
print('issues:'); [print('  -',i) for i in r.issues]
cap = json.loads((root/'Quarentena'/r.capability_id/'.lia'/'capability.json').read_text())
for k in ('description','version','domain','tags','author','license','type','containsScripts'):
    print(f'{k:16}', json.dumps(cap[k], ensure_ascii=False))

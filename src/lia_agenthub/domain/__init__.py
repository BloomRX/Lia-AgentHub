"""Camada L3 — domínio puro.

Regra dura (ver PRODUCT-BOUNDARIES-AND-ARCHITECTURE.md §5): esta camada não
faz I/O, não acessa rede e não importa nada fora da allowlist de stdlib.
O teste tests/unit/test_domain_purity.py falha se a regra for violada.
"""

"""Modelo de risco — D-18: regras transparentes, sem confiança automática.

O resultado NUNCA promove confiança. Ele informa ao humano o que foi
encontrado. SECURITY §6: scanner verde produz evidência, não aprovação.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .model import Capability, ResourceType


class Risk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


@dataclass
class RiskFactor:
    code: str
    description: str
    weight: int

    def as_dict(self) -> dict:
        return {"code": self.code, "description": self.description, "weight": self.weight}


@dataclass
class RiskAssessment:
    level: Risk
    factors: list[RiskFactor] = field(default_factory=list)
    #: O que este modelo NÃO avaliou. Sempre não-vazio, por honestidade.
    not_evaluated: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "level": self.level.value,
            "score": sum(f.weight for f in self.factors),
            "factors": [f.as_dict() for f in self.factors],
            "notEvaluated": list(self.not_evaluated),
            "disclaimer": (
                "Avaliação heurística por regras explícitas. Não executa o código "
                "e não verifica se o conteúdo é malicioso. Não é aprovação."
            ),
        }


ALWAYS_NOT_EVALUATED = [
    "Se o texto contém instruções maliciosas em prosa (não detectável com confiança)",
    "Se o código em scripts/ é seguro (análise estática não é prova)",
    "Homóglifos entre escritas diferentes (exigiria confusables.txt)",
    "Comportamento real em execução",
]


def assess(cap: Capability) -> RiskAssessment:
    factors: list[RiskFactor] = []
    not_eval = list(ALWAYS_NOT_EVALUATED)

    if cap.contains_scripts:
        factors.append(RiskFactor(
            "SCRIPTS", "O recurso contém scripts ou executáveis.", 3))
    if cap.secrets_env_vars:
        factors.append(RiskFactor(
            "SECRETS_DECLARED",
            "Declara variáveis de ambiente — o host pode pedir credenciais.", 2))
    if cap.egress:
        factors.append(RiskFactor(
            "EGRESS",
            f"Declara envio de dados para {len(cap.egress)} destino(s) externo(s).", 3))
    if not cap.license.is_known:
        factors.append(RiskFactor(
            "UNKNOWN_LICENSE",
            "Licença não declarada. Ausência de licença NÃO significa licença livre.", 2))
    if cap.type is ResourceType.UNKNOWN:
        factors.append(RiskFactor(
            "UNKNOWN_TYPE", "Tipo de recurso não reconhecido.", 2))
    if cap.trust.value == "unreviewed":
        factors.append(RiskFactor(
            "UNREVIEWED", "Nenhum humano revisou este recurso ainda.", 1))
    if cap.declared_permissions:
        factors.append(RiskFactor(
            "PERMISSIONS",
            f"Declara {len(cap.declared_permissions)} permissão(ões).", 2))

    if cap.requirements is None:
        not_eval.append("Requisitos de sistema (não medidos)")

    score = sum(f.weight for f in factors)
    if not cap.license.is_known and cap.trust.value == "unreviewed" and score >= 6:
        level = Risk.HIGH
    elif score >= 4:
        level = Risk.HIGH
    elif score >= 2:
        level = Risk.MEDIUM
    elif score == 0:
        level = Risk.LOW
    else:
        level = Risk.MEDIUM

    return RiskAssessment(level=level, factors=factors, not_evaluated=not_eval)

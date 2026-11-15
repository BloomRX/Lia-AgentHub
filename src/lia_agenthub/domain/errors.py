"""Erros do domínio. Mensagens em pt-BR, porque quem lê é o usuário."""
from __future__ import annotations


class LiaError(Exception):
    """Base. `hint` é a ação que o usuário pode tomar."""

    def __init__(self, message: str, hint: str = "", *, code: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint
        self.code = code or self.__class__.__name__

    def as_dict(self) -> dict:
        return {"code": self.code, "message": self.message, "hint": self.hint}


class ValidationError(LiaError):
    """Estrutura inválida. Bloqueia."""


class SecurityError(LiaError):
    """Violação de contenção. Bloqueia sempre."""


class ImportRejected(LiaError):
    """Importação bloqueada. Ver categorias A/B/C/D em SECURITY §3.2."""

    def __init__(self, message: str, hint: str = "", *, code: str = "", findings=None):
        super().__init__(message, hint, code=code)
        self.findings = findings or []


class ConflictError(LiaError):
    """Já existe recurso com essa identidade. Nunca sobrescreve em silêncio."""


class NotFound(LiaError):
    """Recurso não existe."""


class IntegrityError(LiaError):
    """Hash não confere. Não é assinatura — ver SECURITY §3.7.1."""

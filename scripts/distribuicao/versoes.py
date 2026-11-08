"""Validação de versões e nomes portáveis no Windows."""
import re


def validar_nome(valor: str) -> str:
    """Aceita nomes livres seguros para um componente de diretório Windows."""
    if (not valor or valor != valor.strip() or valor.endswith((".", " "))
            or len(valor) > 100 or re.search(r'[<>:"/\\|?*\x00-\x1f]', valor)):
        raise ValueError("Versão vazia ou nome inválido para pasta Windows.")
    reservado = valor.split(".")[0].upper()
    if reservado in {"CON", "PRN", "AUX", "NUL", *[f"COM{i}" for i in range(10)],
                     *[f"LPT{i}" for i in range(10)]}:
        raise ValueError("Nome reservado no Windows.")
    return valor


def validar_producao(valor: str) -> str:
    """Exige três componentes numéricos em produção."""
    validar_nome(valor)
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", valor):
        raise ValueError("Produção exige X.Y.Z, por exemplo 0.0.3.")
    return valor

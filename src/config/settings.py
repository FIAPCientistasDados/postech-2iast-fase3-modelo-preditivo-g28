import os
from pathlib import Path

from src.config.secrets import get_secret


IS_DATABRICKS = bool(
    os.getenv("DATABRICKS_RUNTIME_VERSION")
)


def localizar_raiz_projeto() -> Path:
    diretorio_atual = Path.cwd().resolve()

    for candidato in [
        diretorio_atual,
        *diretorio_atual.parents,
    ]:
        if (candidato / "src").is_dir():
            return candidato

    if not IS_DATABRICKS:
        arquivo_atual = Path(__file__).resolve()

        for candidato in [
            arquivo_atual.parent,
            *arquivo_atual.parents,
        ]:
            if (candidato / "src").is_dir():
                return candidato

    raise FileNotFoundError(
        "Não foi possível localizar a raiz do projeto. "
        "A pasta 'src' não foi encontrada."
    )


def exigir_configuracao(
    secret_name: str,
    env_name: str,
) -> str:
    valor = get_secret(
        secret_name=secret_name,
        env_name=env_name,
        required=True,
    )

    valor_normalizado = (
        str(valor).strip()
        if valor is not None
        else ""
    )

    if not valor_normalizado:
        raise RuntimeError(
            f"Configuração obrigatória não encontrada: "
            f"{env_name}"
        )

    return valor_normalizado


ROOT = localizar_raiz_projeto()

DADOS_PATH = ROOT / "dados"
BRONZE_PATH = DADOS_PATH / "bronze"
SILVER_PATH = DADOS_PATH / "silver"
GOLD_PATH = DADOS_PATH / "gold"

for diretorio in [
    DADOS_PATH,
    BRONZE_PATH,
    SILVER_PATH,
    GOLD_PATH,
]:
    diretorio.mkdir(
        parents=True,
        exist_ok=True,
    )


AZURE_STORAGE_ACCOUNT = exigir_configuracao(
    secret_name="AZURE-STORAGE-ACCOUNT",
    env_name="AZURE_STORAGE_ACCOUNT",
)

AZURE_STORAGE_KEY = exigir_configuracao(
    secret_name="AZURE-STORAGE-KEY",
    env_name="AZURE_STORAGE_KEY",
)

BRONZE_CONTAINER = exigir_configuracao(
    secret_name="AZURE-CONTAINER-BRONZE",
    env_name="AZURE_CONTAINER_BRONZE",
)


__all__ = [
    "IS_DATABRICKS",
    "ROOT",
    "DADOS_PATH",
    "BRONZE_PATH",
    "SILVER_PATH",
    "GOLD_PATH",
    "AZURE_STORAGE_ACCOUNT",
    "AZURE_STORAGE_KEY",
    "BRONZE_CONTAINER",
]

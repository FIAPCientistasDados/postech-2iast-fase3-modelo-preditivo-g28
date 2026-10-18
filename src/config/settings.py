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

    arquivo_atual = Path(__file__).resolve()

    for candidato in [
        arquivo_atual.parent,
        *arquivo_atual.parents,
    ]:
        if (candidato / "src").is_dir():
            return candidato

    raise FileNotFoundError(
        "Não foi possível localizar a raiz do projeto."
    )


def carregar_configuracao(
    secret_name: str,
    env_name: str,
) -> str:
    valor = get_secret(
        secret_name=secret_name,
        env_name=env_name,
        required=True,
    )

    if valor is None:
        raise RuntimeError(
            f"Configuração não encontrada: {env_name}"
        )

    valor = str(valor).strip()

    if not valor:
        raise RuntimeError(
            f"Configuração vazia: {env_name}"
        )

    return valor


ROOT = localizar_raiz_projeto()

DADOS_PATH = ROOT / "dados"
BRONZE_PATH = DADOS_PATH / "bronze"
SILVER_PATH = DADOS_PATH / "silver"
GOLD_PATH = DADOS_PATH / "gold"

for caminho in [
    DADOS_PATH,
    BRONZE_PATH,
    SILVER_PATH,
    GOLD_PATH,
]:
    caminho.mkdir(
        parents=True,
        exist_ok=True,
    )


AZURE_STORAGE_ACCOUNT = carregar_configuracao(
    secret_name="AZURE-STORAGE-ACCOUNT",
    env_name="AZURE_STORAGE_ACCOUNT",
)

AZURE_STORAGE_KEY = carregar_configuracao(
    secret_name="AZURE-STORAGE-KEY",
    env_name="AZURE_STORAGE_KEY",
)

BRONZE_CONTAINER = carregar_configuracao(
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

import os
from typing import Any, Optional


KEYVAULT_SCOPE = "kvfiaptechprod"


def obter_dbutils() -> Optional[Any]:
    databricks_utils = globals().get("dbutils")

    if databricks_utils is not None:
        return databricks_utils

    try:
        from pyspark.dbutils import DBUtils
        from pyspark.sql import SparkSession

        spark = SparkSession.getActiveSession()

        if spark is not None:
            return DBUtils(spark)

    except (
        ImportError,
        ModuleNotFoundError,
        RuntimeError,
    ):
        return None

    return None


def normalizar_valor(
    value: Any,
) -> Optional[str]:
    if value is None:
        return None

    value = str(value).strip()

    return value or None


def get_secret(
    secret_name: str,
    env_name: Optional[str] = None,
    required: bool = False,
    scope: str = KEYVAULT_SCOPE,
) -> Optional[str]:
    secret_name = normalizar_valor(
        secret_name
    )

    env_name = normalizar_valor(
        env_name
    )

    scope = normalizar_valor(
        scope
    )

    if not secret_name:
        raise ValueError(
            "secret_name não pode ser vazio."
        )

    if not scope:
        raise ValueError(
            "scope não pode ser vazio."
        )

    databricks_utils = obter_dbutils()
    databricks_error = None

    if databricks_utils is not None:
        try:
            value = (
                databricks_utils
                .secrets
                .get(
                    scope=scope,
                    key=secret_name,
                )
            )

            value = normalizar_valor(
                value
            )

            if value:
                return value

        except Exception as exc:
            databricks_error = exc

    if env_name:
        value = normalizar_valor(
            os.getenv(env_name)
        )

        if value:
            return value

    if required:
        mensagem = (
            f"Segredo '{secret_name}' não encontrado "
            f"no Secret Scope '{scope}'"
        )

        if env_name:
            mensagem += (
                f" nem na variável de ambiente "
                f"'{env_name}'"
            )

        mensagem += "."

        if databricks_error is not None:
            raise RuntimeError(
                mensagem
            ) from databricks_error

        raise RuntimeError(
            mensagem
        )

    return None
    
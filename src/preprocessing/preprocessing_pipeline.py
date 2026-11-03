"""Pipeline de preprocessamento integrado ao modelo.

Arquivo sugerido: src/preprocessing/preprocessing_pipeline.py
"""
from __future__ import annotations

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler


def _log1p_seguro(x):
    return np.log1p(np.clip(x, 0, None))


def _one_hot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(
            handle_unknown="ignore",
            sparse_output=False,
            dtype=np.float32,
        )
    except TypeError:
        return OneHotEncoder(
            handle_unknown="ignore",
            sparse=False,
            dtype=np.float32,
        )


def build_preprocessor(
    grupos: dict[str, list[str]],
    escalonar: bool = True,
) -> ColumnTransformer:
    """Cria ramos para historico, log, numericas e categoricas."""
    def escala():
        return StandardScaler() if escalonar else "passthrough"

    ramos = []
    if grupos.get("historico"):
        ramos.append((
            "historico",
            Pipeline([
                ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
                ("scaler", escala()),
            ]),
            grupos["historico"],
        ))
    if grupos.get("log"):
        ramos.append((
            "log",
            Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("log1p", FunctionTransformer(_log1p_seguro, feature_names_out="one-to-one")),
                ("scaler", escala()),
            ]),
            grupos["log"],
        ))
    if grupos.get("numericas"):
        ramos.append((
            "num",
            Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", escala()),
            ]),
            grupos["numericas"],
        ))
    if grupos.get("categoricas"):
        ramos.append((
            "cat",
            Pipeline([
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("onehot", _one_hot_encoder()),
            ]),
            grupos["categoricas"],
        ))
    if not ramos:
        raise ValueError("Nenhum grupo de features foi informado.")
    return ColumnTransformer(
        ramos,
        remainder="drop",
        verbose_feature_names_out=False,
    )


def build_pipeline(
    grupos: dict[str, list[str]],
    modelo,
    escalonar: bool = True,
) -> Pipeline:
    return Pipeline([
        ("prep", build_preprocessor(grupos, escalonar)),
        ("modelo", modelo),
    ])


def nomes_das_features(pipeline: Pipeline) -> list[str]:
    prep = pipeline.named_steps["prep"]
    nomes = list(prep.get_feature_names_out())
    return [str(n).replace("missingindicator_", "ausente_") for n in nomes]

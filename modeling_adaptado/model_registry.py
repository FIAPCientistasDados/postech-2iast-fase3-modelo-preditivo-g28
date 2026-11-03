"""Catalogo de estimadores e espacos de hiperparametros.

Arquivo sugerido: src/modeling/model_registry.py

O LightGBM e opcional. Se a biblioteca nao estiver instalada, os modelos
``logistic_regression``, ``ridge`` e ``random_forest`` continuam disponiveis.
"""
from __future__ import annotations

from scipy.stats import loguniform, randint, uniform
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, Ridge

SEED = 42

try:
    from lightgbm import LGBMClassifier, LGBMRegressor
    LIGHTGBM_DISPONIVEL = True
except ImportError:
    LGBMClassifier = None
    LGBMRegressor = None
    LIGHTGBM_DISPONIVEL = False


def classificadores(n_jobs: int = 1) -> dict[str, tuple[object, dict]]:
    modelos: dict[str, tuple[object, dict]] = {
        "logistic_regression": (
            LogisticRegression(max_iter=3000, random_state=SEED),
            {"modelo__C": loguniform(1e-3, 10)},
        ),
        "random_forest": (
            RandomForestClassifier(
                n_estimators=400,
                class_weight="balanced",
                n_jobs=n_jobs,
                random_state=SEED,
            ),
            {
                "modelo__max_depth": randint(4, 20),
                "modelo__min_samples_leaf": randint(5, 100),
                "modelo__max_features": uniform(0.2, 0.6),
            },
        ),
    }
    if LIGHTGBM_DISPONIVEL:
        modelos["lightgbm"] = (
            LGBMClassifier(
                n_estimators=600,
                learning_rate=0.03,
                random_state=SEED,
                n_jobs=n_jobs,
                verbose=-1,
            ),
            {
                "modelo__num_leaves": randint(15, 96),
                "modelo__max_depth": randint(3, 12),
                "modelo__min_child_samples": randint(20, 300),
                "modelo__subsample": uniform(0.6, 0.4),
                "modelo__subsample_freq": [1],
                "modelo__colsample_bytree": uniform(0.5, 0.5),
                "modelo__reg_lambda": loguniform(1e-2, 10),
            },
        )
    return modelos


def regressores(n_jobs: int = 1) -> dict[str, tuple[object, dict]]:
    modelos: dict[str, tuple[object, dict]] = {
        "ridge": (
            Ridge(),
            {"modelo__alpha": loguniform(1e-2, 100)},
        ),
        "random_forest": (
            RandomForestRegressor(
                n_estimators=400,
                n_jobs=n_jobs,
                random_state=SEED,
            ),
            {
                "modelo__max_depth": randint(4, 20),
                "modelo__min_samples_leaf": randint(5, 100),
                "modelo__max_features": uniform(0.2, 0.6),
            },
        ),
    }
    if LIGHTGBM_DISPONIVEL:
        modelos["lightgbm"] = (
            LGBMRegressor(
                n_estimators=600,
                learning_rate=0.03,
                random_state=SEED,
                n_jobs=n_jobs,
                verbose=-1,
            ),
            {
                "modelo__num_leaves": randint(15, 96),
                "modelo__max_depth": randint(3, 12),
                "modelo__min_child_samples": randint(20, 300),
                "modelo__subsample": uniform(0.6, 0.4),
                "modelo__subsample_freq": [1],
                "modelo__colsample_bytree": uniform(0.5, 0.5),
                "modelo__reg_lambda": loguniform(1e-2, 10),
            },
        )
    return modelos


# Aliases para compatibilidade com notebooks antigos.
criar_modelos = classificadores
criar_regressores = regressores

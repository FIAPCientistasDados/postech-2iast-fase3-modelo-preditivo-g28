"""Registro de modelos e espaços de hiperparâmetros.

Destino sugerido:
    src/modeling/model_registry.py

Todos os modelos usam paralelismo limitado por padrão para evitar esgotamento
de memória no WSL. O LightGBM é opcional.
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
    """Modelos de classificação e distribuições para RandomizedSearchCV."""
    modelos: dict[str, tuple[object, dict]] = {
        "logistic_regression": (
            LogisticRegression(
                max_iter=2000,
                class_weight="balanced",
                random_state=SEED,
            ),
            {
                "modelo__C": loguniform(1e-3, 10.0),
            },
        ),
        "random_forest": (
            RandomForestClassifier(
                n_estimators=100,
                class_weight="balanced",
                n_jobs=n_jobs,
                random_state=SEED,
            ),
            {
                "modelo__max_depth": randint(4, 16),
                "modelo__min_samples_leaf": randint(5, 60),
                "modelo__max_features": uniform(0.2, 0.6),
            },
        ),
    }

    if LIGHTGBM_DISPONIVEL:
        modelos["lightgbm"] = (
            LGBMClassifier(
                n_estimators=300,
                learning_rate=0.03,
                random_state=SEED,
                n_jobs=n_jobs,
                verbose=-1,
            ),
            {
                "modelo__num_leaves": randint(15, 64),
                "modelo__max_depth": randint(3, 10),
                "modelo__min_child_samples": randint(20, 200),
                "modelo__subsample": uniform(0.6, 0.4),
                "modelo__subsample_freq": [1],
                "modelo__colsample_bytree": uniform(0.5, 0.5),
                "modelo__reg_lambda": loguniform(1e-2, 10.0),
            },
        )

    return modelos


def regressores(n_jobs: int = 1) -> dict[str, tuple[object, dict]]:
    """Modelos de regressão e distribuições para RandomizedSearchCV."""
    modelos: dict[str, tuple[object, dict]] = {
        "ridge": (
            Ridge(),
            {
                "modelo__alpha": loguniform(1e-2, 100.0),
            },
        ),
        "random_forest": (
            RandomForestRegressor(
                n_estimators=100,
                n_jobs=n_jobs,
                random_state=SEED,
            ),
            {
                "modelo__max_depth": randint(4, 16),
                "modelo__min_samples_leaf": randint(5, 60),
                "modelo__max_features": uniform(0.2, 0.6),
            },
        ),
    }

    if LIGHTGBM_DISPONIVEL:
        modelos["lightgbm"] = (
            LGBMRegressor(
                n_estimators=300,
                learning_rate=0.03,
                random_state=SEED,
                n_jobs=n_jobs,
                verbose=-1,
            ),
            {
                "modelo__num_leaves": randint(15, 64),
                "modelo__max_depth": randint(3, 10),
                "modelo__min_child_samples": randint(20, 200),
                "modelo__subsample": uniform(0.6, 0.4),
                "modelo__subsample_freq": [1],
                "modelo__colsample_bytree": uniform(0.5, 0.5),
                "modelo__reg_lambda": loguniform(1e-2, 10.0),
            },
        )

    return modelos


# Compatibilidade com códigos anteriores.
criar_modelos = classificadores
criar_regressores = regressores

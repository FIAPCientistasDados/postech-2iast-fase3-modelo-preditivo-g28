"""Executa o projeto inteiro na ordem correta.

Uso, na raiz do projeto:
    python run_pipeline.py
    python run_pipeline.py --skip-gold
    python run_pipeline.py --skip-train
    python run_pipeline.py --modelo-aluno random_forest --modelo-municipio random_forest

Etapas:
1. Executa notebooks/gold_raw.ipynb.
2. Executa o notebook de bases analiticas.
3. Treina os modelos.
4. Executa notebook opcional de explicabilidade, se existir.
5. Valida os arquivos produzidos.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
DATA_DIR = PROJECT_ROOT / "data"
GOLD_DIR = DATA_DIR / "gold"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"


GOLD_NOTEBOOK_CANDIDATES = (
    "gold_raw.ipynb",
    "01_gold_raw.ipynb",
    "gold_corrigido.ipynb",
)

ANALYTICAL_NOTEBOOK_CANDIDATES = (
    "base_analitica.ipynb",
    "04_gold_base_analitica.ipynb",
    "02_bases_analiticas.ipynb",
)

EXPLAINABILITY_NOTEBOOK_CANDIDATES = (
    "06_model_explainability.ipynb",
    "model_explainability.ipynb",
    "explicabilidade_modelos.ipynb",
)


def encontrar_notebook(candidatos: tuple[str, ...], obrigatorio: bool) -> Path | None:
    for nome in candidatos:
        caminho = NOTEBOOKS_DIR / nome
        if caminho.exists():
            return caminho
    if obrigatorio:
        raise FileNotFoundError(
            "Nenhum notebook encontrado entre: "
            + ", ".join(str(NOTEBOOKS_DIR / n) for n in candidatos)
        )
    return None


def executar_comando(comando: list[str], etapa: str, timeout: int | None = None) -> None:
    print(f"\n{'=' * 80}")
    print(f"[etapa] {etapa}")
    print("[comando]", " ".join(comando))
    inicio = time.perf_counter()
    subprocess.run(
        comando,
        cwd=PROJECT_ROOT,
        check=True,
        timeout=timeout,
    )
    duracao = time.perf_counter() - inicio
    print(f"[ok] {etapa} concluida em {duracao / 60:.1f} minuto(s).")


def executar_notebook(caminho: Path, timeout_celula: int = 1800) -> None:
    if shutil.which("jupyter") is None:
        raise RuntimeError(
            "O comando 'jupyter' nao foi encontrado. Instale com: "
            "python -m pip install jupyter nbconvert ipykernel"
        )
    executar_comando(
        [
            sys.executable,
            "-m",
            "jupyter",
            "nbconvert",
            "--to",
            "notebook",
            "--execute",
            "--inplace",
            f"--ExecutePreprocessor.timeout={timeout_celula}",
            f"--ExecutePreprocessor.cwd={PROJECT_ROOT}",
            str(caminho),
        ],
        etapa=f"Executar notebook {caminho.name}",
    )


def validar_arquivos(arquivos: list[Path], etapa: str) -> None:
    ausentes = [str(p.relative_to(PROJECT_ROOT)) for p in arquivos if not p.exists()]
    if ausentes:
        raise FileNotFoundError(f"{etapa}: arquivos esperados nao foram gerados: {ausentes}")
    print(f"[validacao] {etapa}: {len(arquivos)} arquivo(s) encontrado(s).")
    for caminho in arquivos:
        tamanho_mb = caminho.stat().st_size / 1024**2
        print(f"  - {caminho.relative_to(PROJECT_ROOT)} ({tamanho_mb:.2f} MB)")


def executar_pipeline(args: argparse.Namespace) -> None:
    print(f"[projeto] {PROJECT_ROOT}")
    print(f"[python] {sys.executable}")

    if not args.skip_gold:
        notebook_gold = encontrar_notebook(GOLD_NOTEBOOK_CANDIDATES, obrigatorio=True)
        executar_notebook(notebook_gold, timeout_celula=args.notebook_timeout)
        validar_arquivos(
            [
                GOLD_DIR / "fato_aluno.parquet",
                GOLD_DIR / "contexto_municipio.parquet",
                GOLD_DIR / "ideb_municipio.parquet",
                GOLD_DIR / "indicador_municipio.parquet",
                GOLD_DIR / "metas_municipio.parquet",
            ],
            "camada Gold",
        )
    else:
        print("[skip] Camada Gold ignorada.")

    if not args.skip_processed:
        notebook_abt = encontrar_notebook(ANALYTICAL_NOTEBOOK_CANDIDATES, obrigatorio=True)
        executar_notebook(notebook_abt, timeout_celula=args.notebook_timeout)
        validar_arquivos(
            [
                PROCESSED_DIR / "base_analitica_aluno.parquet",
                PROCESSED_DIR / "base_analitica_municipio.parquet",
            ],
            "bases analiticas",
        )
    else:
        print("[skip] Bases analiticas ignoradas.")

    if not args.skip_train:
        comando_treino = [
            sys.executable,
            "-m",
            "src.modeling.train_models",
            "--alvo",
            args.alvo,
            "--modelo-aluno",
            args.modelo_aluno,
            "--modelo-municipio",
            args.modelo_municipio,
            "--n-iter",
            str(args.n_iter),
            "--amostra",
            str(args.amostra),
        ]
        executar_comando(comando_treino, "Treinar modelos")

        esperados = []
        if args.alvo in ("aluno", "todos"):
            esperados.extend([
                MODELS_DIR / "modelo_aluno.joblib",
                MODELS_DIR / "modelo_aluno.json",
                MODELS_DIR / "modelo_aluno_oof.parquet",
            ])
        if args.alvo in ("municipio", "todos"):
            esperados.extend([
                MODELS_DIR / "modelo_municipio.joblib",
                MODELS_DIR / "modelo_municipio.json",
                MODELS_DIR / "modelo_municipio_oof.parquet",
            ])
        validar_arquivos(esperados, "modelos e validacao")
    else:
        print("[skip] Treinamento ignorado.")

    if not args.skip_explainability:
        notebook_explicacao = encontrar_notebook(
            EXPLAINABILITY_NOTEBOOK_CANDIDATES,
            obrigatorio=False,
        )
        if notebook_explicacao is None:
            print(
                "[aviso] Notebook de explicabilidade nao encontrado. "
                "A etapa foi ignorada."
            )
        else:
            executar_notebook(
                notebook_explicacao,
                timeout_celula=args.notebook_timeout,
            )
            print(f"[validacao] Relatorios disponiveis em: {REPORTS_DIR}")
    else:
        print("[skip] Explicabilidade ignorada.")

    print(f"\n{'=' * 80}")
    print("[sucesso] Pipeline concluido.")
    print(f"Gold: {GOLD_DIR}")
    print(f"Processed: {PROCESSED_DIR}")
    print(f"Models: {MODELS_DIR}")
    print(f"Reports: {REPORTS_DIR}")


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Executa Gold, bases analiticas, treinamento e explicabilidade."
    )
    parser.add_argument("--alvo", choices=["aluno", "municipio", "todos"], default="todos")
    parser.add_argument("--modelo-aluno", default="random_forest")
    parser.add_argument("--modelo-municipio", default="random_forest")
    parser.add_argument("--n-iter", type=int, default=20)
    parser.add_argument("--amostra", type=int, default=300_000)
    parser.add_argument("--notebook-timeout", type=int, default=1800)
    parser.add_argument("--skip-gold", action="store_true")
    parser.add_argument("--skip-processed", action="store_true")
    parser.add_argument("--skip-train", action="store_true")
    parser.add_argument("--skip-explainability", action="store_true")
    return parser


if __name__ == "__main__":
    executar_pipeline(criar_parser().parse_args())

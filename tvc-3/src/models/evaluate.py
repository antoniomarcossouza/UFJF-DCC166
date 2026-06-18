"""Métricas e artefatos de avaliação."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import mlflow
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.preprocessing import LabelEncoder, label_binarize

from utils.paths import REPORTS_DIR, ensure_dirs


def _get_proba(model: Any, x: np.ndarray) -> np.ndarray | None:
    if hasattr(model, "predict_proba"):
        return model.predict_proba(x)
    if hasattr(model, "decision_function"):
        scores = model.decision_function(x)
        if scores.ndim == 1:
            scores = np.vstack([-scores, scores]).T
        exp = np.exp(scores - scores.max(axis=1, keepdims=True))
        return exp / exp.sum(axis=1, keepdims=True)
    return None


def evaluate_classifier(
    model: Any, x: np.ndarray, y_true: np.ndarray
) -> dict[str, float]:
    """Calcula métricas obrigatórias."""
    y_pred = model.predict(x)
    metrics: dict[str, float] = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(
            precision_score(y_true, y_pred, average="macro", zero_division=0)
        ),
        "recall": float(
            recall_score(y_true, y_pred, average="macro", zero_division=0)
        ),
        "f1": float(
            f1_score(y_true, y_pred, average="macro", zero_division=0)
        ),
        "roc_auc": 0.0,
        "pr_auc": 0.0,
    }
    proba = _get_proba(model, x)
    if proba is None:
        return metrics

    classes = np.unique(y_true)
    if len(classes) == 2:
        pos_idx = 1 if proba.shape[1] > 1 else 0
        y_score = proba[:, pos_idx]
        y_bin = LabelEncoder().fit_transform(y_true)
        metrics["roc_auc"] = float(roc_auc_score(y_bin, y_score))
        metrics["pr_auc"] = float(average_precision_score(y_bin, y_score))
    else:
        y_bin = label_binarize(y_true, classes=classes)
        metrics["roc_auc"] = float(
            roc_auc_score(y_bin, proba, multi_class="ovr", average="macro")
        )
        metrics["pr_auc"] = float(
            average_precision_score(y_bin, proba, average="macro")
        )
    return metrics


def _save_confusion_matrix(
    y_true: np.ndarray, y_pred: np.ndarray, path: Path
) -> None:
    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xlabel("Predito")
    ax.set_ylabel("Real")
    ax.set_title("Matriz de Confusão")
    fig.colorbar(im, ax=ax)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _save_roc_curve(
    y_true: np.ndarray, y_score: np.ndarray, path: Path
) -> None:
    fpr, tpr, _ = roc_curve(y_true, y_score)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(fpr, tpr)
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray")
    ax.set_xlabel("FPR")
    ax.set_ylabel("TPR")
    ax.set_title("ROC Curve")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _save_pr_curve(
    y_true: np.ndarray, y_score: np.ndarray, path: Path
) -> None:
    precision, recall, _ = precision_recall_curve(y_true, y_score)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(recall, precision)
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_title("Precision-Recall Curve")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def log_evaluation_artifacts(
    model: Any,
    x: np.ndarray,
    y_true: np.ndarray,
    prefix: str,
) -> None:
    """Salva matrizes e curvas como artefatos MLflow e em reports/."""
    ensure_dirs()
    y_pred = model.predict(x)
    reports_prefix = REPORTS_DIR / prefix
    reports_prefix.mkdir(parents=True, exist_ok=True)

    cm_path = reports_prefix / "confusion_matrix.png"
    _save_confusion_matrix(y_true, y_pred, cm_path)
    mlflow.log_artifact(str(cm_path))

    proba = _get_proba(model, x)
    if proba is not None and len(np.unique(y_true)) == 2:
        y_bin = LabelEncoder().fit_transform(y_true)
        y_score = proba[:, 1] if proba.shape[1] > 1 else proba[:, 0]
        roc_path = reports_prefix / "roc_curve.png"
        pr_path = reports_prefix / "pr_curve.png"
        _save_roc_curve(y_bin, y_score, roc_path)
        _save_pr_curve(y_bin, y_score, pr_path)
        mlflow.log_artifact(str(roc_path))
        mlflow.log_artifact(str(pr_path))

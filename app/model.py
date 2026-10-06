"""ML part: TF-IDF (words + character n-grams) and one logistic-regression head per label (type, dependency, urgency, subtype)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.pipeline import FeatureUnion

from .text import strip_accents

HEADS = ("type", "dependency", "urgency", "subtype")


@dataclass
class LabeledText:
    """One training example. A head with `None` is simply not trained from this example."""

    text: str
    type: str | None = None
    dependency: str | None = None
    urgency: str | None = None
    subtype: str | None = None
    weight: float = 1.0


def _prep(text: str) -> str:
    return strip_accents(text).lower()


@dataclass
class TextModel:
    seed: int = 42
    vectorizer: FeatureUnion | None = None
    heads: dict[str, LogisticRegression] = field(default_factory=dict)
    trained_on: dict[str, int] = field(default_factory=dict)
    metrics: dict[str, dict[str, float]] = field(default_factory=dict)
    trained_at: float = 0.0

    # ------------------------------------------------------------ training
    def _new_vectorizer(self) -> FeatureUnion:
        return FeatureUnion([
            ("word", TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=2, sublinear_tf=True, max_features=80_000)),
            ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=3, sublinear_tf=True, max_features=120_000)),
        ])

    def _fit_heads(self, vec: FeatureUnion, items: list[LabeledText], X) -> dict[str, LogisticRegression]:  # noqa: ANN001
        heads: dict[str, LogisticRegression] = {}
        for head in HEADS:
            idx = [i for i, it in enumerate(items) if getattr(it, head) is not None]
            labels = [getattr(items[i], head) for i in idx]
            if len(set(labels)) < 2:
                continue
            clf = LogisticRegression(C=6.0, max_iter=500, class_weight="balanced", random_state=self.seed)
            clf.fit(X[idx], labels, sample_weight=np.array([items[i].weight for i in idx]))
            heads[head] = clf
        return heads

    def fit(self, items: list[LabeledText], evaluate: bool = True) -> "TextModel":
        if len(items) < 30:
            raise ValueError("Se necesitan al menos 30 ejemplos para entrenar el modelo.")
        rng = np.random.default_rng(self.seed)
        if evaluate and len(items) >= 200:
            order = rng.permutation(len(items))
            cut = int(len(items) * 0.85)
            train = [items[i] for i in order[:cut]]
            val = [items[i] for i in order[cut:]]
            vec = self._new_vectorizer()
            X = vec.fit_transform([_prep(it.text) for it in train])
            heads = self._fit_heads(vec, train, X)
            Xv = vec.transform([_prep(it.text) for it in val])
            self.metrics = {}
            for head, clf in heads.items():
                idx = [i for i, it in enumerate(val) if getattr(it, head) is not None]
                if not idx:
                    continue
                y = [getattr(val[i], head) for i in idx]
                pred = clf.predict(Xv[idx])
                self.metrics[head] = {"accuracy": round(float(accuracy_score(y, pred)), 4), "macro_f1": round(float(f1_score(y, pred, average="macro")), 4), "n_validation": len(idx)}
        vec = self._new_vectorizer()
        X = vec.fit_transform([_prep(it.text) for it in items])
        self.vectorizer = vec
        self.heads = self._fit_heads(vec, items, X)
        self.trained_on = {h: sum(1 for it in items if getattr(it, h) is not None) for h in HEADS}
        self.trained_at = time.time()
        return self

    # ------------------------------------------------------------ inference
    def predict_proba(self, texts: list[str]) -> dict[str, list[dict[str, float]]]:
        """head -> list (one per text) of {class: probability}."""
        if self.vectorizer is None:
            raise RuntimeError("El modelo no está entrenado.")
        X = self.vectorizer.transform([_prep(t) for t in texts])
        out: dict[str, list[dict[str, float]]] = {}
        for head, clf in self.heads.items():
            proba = clf.predict_proba(X)
            classes = [str(c) for c in clf.classes_]
            out[head] = [dict(zip(classes, map(float, row))) for row in proba]
        return out

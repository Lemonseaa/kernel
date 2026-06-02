"""Readability evaluator."""

from __future__ import annotations

import re

from opc_os.evaluation.evaluator import Evaluator
from opc_os.evaluation.result import EvaluationResult


class ReadabilityEvaluator(Evaluator):
    """Score Chinese readability using sentence, paragraph, and format signals."""

    @property
    def name(self) -> str:
        """Return evaluator name."""

        return "readability"

    def evaluate(self, content: str, platform: str = "public") -> EvaluationResult:
        """Evaluate readability."""

        text = content.strip()
        sentences = [item for item in re.split(r"[。！？!?]\s*", text) if item.strip()]
        paragraphs = [item for item in re.split(r"\n\s*\n", text) if item.strip()]
        avg_sentence_len = sum(len(item.strip()) for item in sentences) / max(len(sentences), 1)
        paragraph_sentence_counts = [
            len([sentence for sentence in re.split(r"[。！？!?]\s*", paragraph) if sentence.strip()])
            for paragraph in paragraphs
        ]
        avg_paragraph_sentences = sum(paragraph_sentence_counts) / max(len(paragraph_sentence_counts), 1)

        sentence_score = self._band_score(avg_sentence_len, low=15, high=35, soft_low=8, soft_high=55)
        paragraph_score = self._band_score(avg_paragraph_sentences, low=1, high=5, soft_low=1, soft_high=8)
        format_score = self._format_score(text, paragraphs)
        score = self._clamp(sentence_score * 0.35 + paragraph_score * 0.3 + format_score * 0.35)
        suggestions: list[str] = []
        if sentence_score < 70:
            suggestions.append("调整句子长度，避免过短或过长。")
        if paragraph_score < 70:
            suggestions.append("控制段落长度，让每段围绕一个清晰观点。")
        if format_score < 70:
            suggestions.append("补充标题、分段和更完整的正文。")
        return EvaluationResult(
            name=self.name,
            score=round(score, 2),
            passed=score >= 60,
            details={
                "avg_sentence_length": round(avg_sentence_len, 2),
                "avg_paragraph_sentences": round(avg_paragraph_sentences, 2),
                "format_score": round(format_score, 2),
            },
            suggestions=suggestions,
        )

    def _format_score(self, text: str, paragraphs: list[str]) -> float:
        """Score basic formatting completeness."""

        score = 0.0
        if text:
            score += 25.0
        if "\n" in text or len(paragraphs) >= 2:
            score += 30.0
        if len(text) >= 80:
            score += 30.0
        if len(text.splitlines()[0]) <= 40:
            score += 15.0
        return self._clamp(score)

    def _band_score(self, value: float, low: float, high: float, soft_low: float, soft_high: float) -> float:
        """Score highest inside a target band, falling off outside it."""

        if low <= value <= high:
            return 100.0
        if value < low:
            if value <= soft_low:
                return 50.0
            return 50.0 + (value - soft_low) / (low - soft_low) * 50.0
        if value >= soft_high:
            return 50.0
        return 100.0 - (value - high) / (soft_high - high) * 50.0

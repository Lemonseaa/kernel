"""SEO evaluator."""

from __future__ import annotations

import re

from checkpoint_ai.evaluation.evaluator import Evaluator
from checkpoint_ai.evaluation.result import EvaluationResult


class SEOEvaluator(Evaluator):
    """Score lightweight SEO quality."""

    @property
    def name(self) -> str:
        """Return evaluator name."""

        return "seo"

    def evaluate(self, content: str, platform: str = "public") -> EvaluationResult:
        """Evaluate keyword reuse, structure, and length."""

        lines = [line.strip() for line in content.strip().splitlines() if line.strip()]
        title = lines[0] if lines else ""
        body = "\n".join(lines[1:]) if len(lines) > 1 else content
        title_tokens = [token for token in re.findall(r"[\u4e00-\u9fffA-Za-z0-9]{2,}", title) if len(token) >= 2]
        keyword_hits = sum(1 for token in title_tokens if token in body)
        keyword_score = 100.0 if not title_tokens else keyword_hits / len(title_tokens) * 100.0
        structure_score = 100.0 if re.search(r"(一|二|三|首先|其次|最后|第[一二三四五六七八九十]+)", content) else 55.0
        length_score = min(100.0, len(content) / 500 * 100.0)
        score = self._clamp(keyword_score * 0.3 + structure_score * 0.3 + length_score * 0.4)
        suggestions: list[str] = []
        if keyword_score < 70:
            suggestions.append("在正文中自然复用标题关键词。")
        if structure_score < 70:
            suggestions.append("增加层级结构，例如首先、其次、最后。")
        if length_score < 70:
            suggestions.append("扩展正文长度，补充案例、步骤或细节。")
        return EvaluationResult(
            name=self.name,
            score=round(score, 2),
            passed=score >= 60,
            details={
                "keyword_score": round(keyword_score, 2),
                "structure_score": round(structure_score, 2),
                "length_score": round(length_score, 2),
            },
            suggestions=suggestions,
        )

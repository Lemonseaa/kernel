"""Platform adaptation evaluator."""

from __future__ import annotations

import re

from kernel.evaluation.evaluator import Evaluator
from kernel.evaluation.result import EvaluationResult


class PlatformEvaluator(Evaluator):
    """Score basic platform fit."""

    @property
    def name(self) -> str:
        """Return evaluator name."""

        return "platform"

    def evaluate(self, content: str, platform: str = "public") -> EvaluationResult:
        """Evaluate platform-specific format signals."""

        normalized = platform.lower()
        lines = [line.strip() for line in content.strip().splitlines() if line.strip()]
        title = lines[0] if lines else ""
        body = "\n".join(lines[1:]) if len(lines) > 1 else content
        if normalized in {"xiaohongshu", "xhs"}:
            return self._xiaohongshu(title, body, content)
        if normalized == "wechat":
            return self._wechat(title, body, content)
        if normalized == "blog":
            return self._blog(title, body, content)
        return self._public(content)

    def _xiaohongshu(self, title: str, body: str, content: str) -> EvaluationResult:
        """Evaluate Xiaohongshu format."""

        title_score = 100.0 if 8 <= len(title) <= 20 else 55.0
        body_score = 100.0 if 120 <= len(body) <= 1200 else min(80.0, len(body) / 120 * 80.0)
        tag_score = 100.0 if re.search(r"#[\w\u4e00-\u9fff]+", content) else 40.0
        score = self._clamp(title_score * 0.3 + body_score * 0.45 + tag_score * 0.25)
        suggestions = []
        if title_score < 70:
            suggestions.append("小红书标题建议控制在8-20字。")
        if body_score < 70:
            suggestions.append("小红书正文需要更完整，建议至少120字。")
        if tag_score < 70:
            suggestions.append("补充小红书标签，例如 #AI #内容运营。")
        return EvaluationResult(self.name, round(score, 2), score >= 60, suggestions=suggestions)

    def _wechat(self, title: str, body: str, content: str) -> EvaluationResult:
        """Evaluate WeChat format."""

        title_score = 100.0 if 10 <= len(title) <= 35 else 60.0
        body_score = min(100.0, len(body) / 1000 * 100.0)
        summary_score = 100.0 if re.search(r"(摘要|导语|本文)", content) else 55.0
        score = self._clamp(title_score * 0.25 + body_score * 0.5 + summary_score * 0.25)
        suggestions = []
        if body_score < 70:
            suggestions.append("公众号正文建议扩展到1000字以上。")
        if summary_score < 70:
            suggestions.append("增加摘要或导语，帮助读者快速判断价值。")
        return EvaluationResult(self.name, round(score, 2), score >= 60, suggestions=suggestions)

    def _blog(self, title: str, body: str, content: str) -> EvaluationResult:
        """Evaluate blog format."""

        title_score = 100.0 if title else 40.0
        body_score = min(100.0, len(body) / 800 * 100.0)
        meta_score = 100.0 if re.search(r"(meta|description|标签|keywords|#)", content, re.I) else 45.0
        score = self._clamp(title_score * 0.25 + body_score * 0.45 + meta_score * 0.3)
        suggestions = []
        if meta_score < 70:
            suggestions.append("补充meta描述或标签，方便搜索和归档。")
        return EvaluationResult(self.name, round(score, 2), score >= 60, suggestions=suggestions)

    def _public(self, content: str) -> EvaluationResult:
        """Evaluate generic content format."""

        score = 100.0 if len(content.strip()) >= 80 else 45.0
        suggestions = [] if score >= 70 else ["补充正文内容，让观点更完整。"]
        return EvaluationResult(self.name, round(score, 2), score >= 60, suggestions=suggestions)

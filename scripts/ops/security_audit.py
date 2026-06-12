"""Run a lightweight security audit for production readiness."""

from __future__ import annotations

from pathlib import Path

SECRET_MARKERS = ("sk-", "ghp_", "xoxb-", "AKIA")


def main() -> int:
    """Check committed files for obvious secret leaks."""

    root = Path(__file__).resolve().parents[1]
    critical_findings: list[str] = []
    for path in [root / ".env.example", root / "docker-compose.yml", root / "README.md"]:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for marker in SECRET_MARKERS:
            if marker in text:
                critical_findings.append(f"{path.name}: contains marker {marker}")
    for finding in critical_findings:
        print(f"critical: {finding}")
    print(f"security_audit critical_findings={len(critical_findings)}")
    return 1 if critical_findings else 0


if __name__ == "__main__":
    raise SystemExit(main())

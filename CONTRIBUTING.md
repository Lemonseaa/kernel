# Contributing to CheckpointAI

Thank you for your interest in contributing to CheckpointAI!

## Development Setup

```bash
# Clone the repository
git clone https://github.com/Lemonseaa/checkpoint_ai.git
cd checkpoint_ai

# Install in development mode
pip install -e ".[all]"

# Run tests
python -m unittest discover -s tests -v

# Lint
ruff check checkpoint_ai/

# Type check
mypy checkpoint_ai/
```

## Code Style

- Follow PEP 8
- Line length: 100 characters
- Use type hints where possible
- Run `ruff check checkpoint_ai/` before committing

## Testing

- All new features should include tests
- Run `python -m unittest discover -s tests -v` before submitting PR
- Aim for passing all existing tests

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Add tests
5. Run linting and tests
6. Commit your changes (`git commit -m "Add feature: description"`)
7. Push to your fork
8. Open a Pull Request

## Commit Message Format

```
type: Short description

Longer description if needed.

Fixes #issue-number
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Maintenance tasks

## Reporting Issues

Please use the issue templates when reporting:
- [Bug Report](.github/ISSUE_TEMPLATE/bug_report.md) for bugs
- [Feature Request](.github/ISSUE_TEMPLATE/feature_request.md) for features

## Questions?

Feel free to open an issue for questions about the project.

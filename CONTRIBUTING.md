# Contributing Guide

Thanks for your interest in contributing to this project. This guide explains how to contribute effectively and maintain consistency.

---

## 1. Getting Started

Clone the repository and set up the environment:

```bash
git clone <repo-url>
cd <project-folder>
pip install -r requirements.txt
```

Run the project:

```bash
python main.py
```

---

## 2. Branching Strategy

* `main` → stable, production-ready code
* `dev` → active development
* Feature branches → `feature/<feature-name>`
* Bug fixes → `fix/<issue-name>`

Example:

```bash
git checkout -b feature/data-ingestion
```

---

## 3. Commit Guidelines

Use clear and structured commit messages:

* `feat:` → new feature
* `fix:` → bug fix
* `docs:` → documentation
* `refactor:` → code improvements

Examples:

```bash
feat: add Power BI metadata extraction
fix: resolve API timeout issue
docs: update README with setup steps
```

Avoid vague commits like:

```bash
"update", "done", "fix stuff"
```

---

## 4. Pull Request Process

1. Create a pull request to `dev`
2. Add a clear description:

   * What was changed
   * Why it was changed
3. Ensure code runs without errors
4. Review your own code before submitting

---

## 5. Code Standards

* Follow consistent naming conventions
* Keep functions modular and readable
* Add comments for complex logic
* Avoid hardcoding values

For Python:

* Follow PEP8 guidelines
* Use meaningful variable names

---

## 6. Data Handling Guidelines

* Do not commit sensitive data
* Use sample/mock data for testing
* Clearly document data sources

---

## 7. Reporting Issues

Use GitHub Issues to report bugs or request features.

Include:

* Steps to reproduce
* Expected vs actual behavior
* Screenshots/logs (if applicable)

---

## 8. Contribution Scope

You can contribute in:

* Feature development
* Bug fixes
* Documentation improvements
* Performance optimization

---

## Final Notes

Keep contributions focused and minimal.
Large changes should be discussed before implementation.

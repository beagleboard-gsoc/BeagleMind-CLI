# Contributing to BeagleMind-CLI

Thank you for your interest in contributing! BeagleMind-CLI is an intelligent documentation assistant using RAG to help developers work with BeagleBoard documentation and codebases.

## Quick Start

**Prerequisites:** Python 3.8+, Git

**Setup:**
```bash
git clone https://github.com/YOUR_USERNAME/BeagleMind-CLI.git
cd BeagleMind-CLI
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
pytest tests/  # Run tests
```

## Contributing

**Report Issues:** Use GitHub issues with OS/Python version, steps to reproduce, and error messages

**Code Contributions:**
1. Fork and create a feature branch: `git checkout -b feature/name`
2. Follow code style (PEP 8, type hints, docstrings)
3. Add tests and update docs
4. Commit: `git commit -m "feat: description"` (use conventional commits)
5. Create a pull request

## Roadmap & Enhancement Ideas

### Phase 1: Advanced Features (Q1 - Q2 2026)
**Multi-modal & CLI Enhancements**
- [ ] Image understanding / generation (circuit diagrams, schematics)
- [ ] Stabilize tool calls for the existing set of providers
- [ ] Provider diversity

**Hardware Integration**
- [ ] Auto-detect connected BeagleBoard devices
- [ ] Live debugging and log analysis (optional)

### Additional Enhancement Ideas
**High Priority:** Config management (YAML/TOML), enhanced error handling with fallbacks, performance optimization (caching, parallel processing)

**Medium Priority:** Offline mode

## Code Guidelines

- Use conventional commits: `feat|fix|docs|style|refactor|test|chore: description`
- Add tests for new features (optional)
- Run `black .` and `flake8 src/` before committing
- Please test your work locally before submitting a PR (make sure it works).

## Community & Support

**Get Help:** GitHub Issues/Discussions, BeagleBoard Forum, Discord, fayez.zouari@insat.ucar.tn

**Code of Conduct:** Be respectful, inclusive, and constructive.

---

**Thank you for contributing!** 🚀

# Contributing to GuardianX

Thanks for your interest in improving GuardianX!

**Feature note:** GuardianX is currently at **feature freeze** and in Release
Candidate polish. Please do not add new major modules. Focus contributions on
correctness, stability, security, documentation, and test coverage.

## Getting started

1. Fork and clone the repository.
2. Read [`docs/DEVELOPMENT.md`](./DEVELOPMENT.md) to set up the backend and
   frontend locally.
3. Create a branch: `git checkout -b fix/describe-the-change`.

## What to work on

- **Bug fixes** with a failing regression test.
- **Stability** improvements: better error handling, logging, performance.
- **Security** hardening and security fixes.
- **Tests** and **documentation** improvements.

## Guidelines

- Keep your changes scoped to a single concern.
- Follow the existing code style in the file you touch.
- Backend changes: add or update tests under `backend/tests/` and run the suite.
- Frontend changes: add/update component tests and run `npm run lint` and
  `npm run build`.
- Update relevant documentation when behaviour changes (`docs/`).
- Never commit secrets, `.env` files, or generated artifacts.

## Pull request checklist

- [ ] Backend tests pass: `python -m pytest backend/tests -q`
- [ ] Frontend builds: `npm run build`
- [ ] Frontend lint passes: `npm run lint`
- [ ] Frontend tests pass: `npm test`
- [ ] Documentation updated where applicable

## Commit style

Write clear, conventional commit messages, e.g.:

```
feat(auth): add email verification and password reset
fix(scans): handle empty nmap arguments for custom profiles
test: cover refresh-token rotation edge cases
```

## Questions

Open an issue for problems or feature requests that fall within the RC polish
scope.
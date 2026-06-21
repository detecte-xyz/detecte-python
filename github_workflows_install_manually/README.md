# Install workflows manually
The OAuth token used to push this repo lacks `workflow` scope. To enable PyPI auto-publish:

1. `mkdir -p .github/workflows`
2. Move `release.yml` and `test.yml` here into `.github/workflows/`
3. Delete this folder
4. Commit + push from GitHub UI or a token with workflow scope.

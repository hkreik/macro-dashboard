# Contributing to Macro-Equity Dashboard

## Development Setup

### 1. Clone and install

```bash
git clone https://github.com/hkreik/macro-dashboard.git
cd macro-dashboard
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
pre-commit install
```

### 2. Set up GPG commit signing (recommended)

Signed commits verify your identity and are displayed with a "Verified" badge on GitHub.

**Generate a GPG key:**
```bash
gpg --full-generate-key
# Choose: RSA, 4096 bits, no expiry
# Use your GitHub email address
```

**Get your key ID:**
```bash
gpg --list-secret-keys --keyid-format=long
# Copy the long key ID (e.g. 3AA5C34371567BD2)
```

**Export and add to GitHub:**
```bash
gpg --armor --export 3AA5C34371567BD2
# Copy the output and add it to GitHub → Settings → SSH and GPG keys
```

**Configure git to sign all commits:**
```bash
git config --global user.signingkey 3AA5C34371567BD2
git config --global commit.gpgsign true
git config --global tag.gpgsign true
```

**Verify signing works:**
```bash
git commit --allow-empty -m "test: verify GPG signing"
git log --show-signature -1
```

### 3. Set up SSH commit signing (alternative to GPG)

If you prefer SSH keys over GPG:

```bash
# Use your existing SSH key or generate one
ssh-keygen -t ed25519 -C "your@email.com"

# Add the public key to GitHub as a "Signing Key" (separate from auth key)
cat ~/.ssh/id_ed25519.pub
# GitHub → Settings → SSH and GPG keys → New SSH key → Key type: Signing Key

# Configure git
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub
git config --global commit.gpgsign true
```

## Workflow

1. Create a feature branch: `git checkout -b feat/your-feature`
2. Make changes and commit (pre-commit hooks run automatically)
3. Push and open a PR against `master`
4. CI must pass (lint + tests + coverage ≥ 70%)
5. Get 1 approving review
6. Merge

## Code Style

- Formatter: `ruff format .`
- Linter: `ruff check .`
- Config: `ruff.toml` in the repo root
- Line length: 100 characters

## Running Tests

```bash
pytest                              # all tests
pytest tests/test_data.py -v        # specific file
pytest --cov=. --cov-report=html    # with HTML coverage report
open htmlcov/index.html             # view coverage
```

## Adding a Secret (FRED_API_KEY)

The CI pipeline reads `FRED_API_KEY` from GitHub Actions secrets.
To add it: GitHub repo → Settings → Secrets and variables → Actions → New repository secret.

# Security Policy

This document covers the security posture of **Risk Battle Game A**
(repository: EWSimpson1791/SafeVault1791).

---

## Supported Versions

| Version / Branch | Security fixes applied |
|---|---|
| master | Yes - all patches land here |
| Feature branches | No - merge to master first |

---

## Authentication and Brute-Force Controls

The auth/auth_manager.py module enforces the following controls on every
login attempt. These must not be weakened in any future commit without a
documented security review.

| Control | Value | Purpose |
|---|---|---|
| Password hashing | PBKDF2-HMAC-SHA256, 260,000 iterations | Defeats offline brute-force and rainbow tables |
| Salt | 32-byte random per user | Defeats pre-computation attacks |
| Comparison | hmac.compare_digest | Defeats timing-based username enumeration |
| Unknown-user dummy hash | Enabled | Response time is uniform, account existence is not leaked |
| Max consecutive failures | 5 | Triggers account lockout |
| Lockout duration | 15 minutes (900 seconds) | Enforced cooldown window |
| Lockout persistence | data/lockout_state.json | Survives process restarts, cannot be bypassed by restarting |
| Failure log | data/auth_failures.log | UTC timestamp and reason code on every failure |
| Admin reset | AuthManager.reset_lockout(username) | Privileged clear of lockout state |

### Lockout reason codes

| Code | Meaning |
|---|---|
| WRONG_PASSWORD | Account exists; password did not match |
| UNKNOWN_USER | No account found for the supplied username |
| LOCKED_OUT | Account is within the active lockout window |

---

## Protected Runtime Files

The following files are generated at runtime and are explicitly excluded
from version control via .gitignore. They must never be committed.

| File | Why it must stay out of git |
|---|---|
| data/users.json | Contains PBKDF2 hashes and per-user salts |
| data/users.json.py | Legacy credential store - may contain plaintext |
| data/lockout_state.json | Live lockout state - committing resets it on deploy |
| data/auth_failures.log | Failure log - contains usernames and timestamps |

If any of these files appear in git status output, do not stage them.
If they were committed in a prior session, remove them from history using
git filter-repo before any visibility change.

---

## Repository Visibility

This repository is and must remain private.

Reasons:
- auth/dcrypt.py exposes decryption logic - public access enables targeted
  cryptanalysis of the algorithm
- auth/user_store.py documents the credential storage schema
- The combination of schema and algorithm and any leaked hash gives an
  attacker a complete attack surface

This repository must not be made public without a full independent
security audit of the auth/ package.

---

## CI Security Gate

Every push or pull request touching auth/ or tests/test_auth_manager.py
triggers .github/workflows/auth_security.yml, which runs the full 19-test
auth security suite on Python 3.12.

A failing security gate must block the merge. Do not merge to master
while the Auth Security Gate workflow is red.

---

## Reporting a Vulnerability

This is a private repository. To report a security issue:

1. Do not open a public GitHub issue.
2. Contact the repository owner directly via GitHub (@EWSimpson1791)
   using a private message.
3. Include: affected file(s), reproduction steps, and potential impact.
4. Allow up to 72 hours for an initial response.

---

## Security Test Coverage

| Test file | Controls covered | Status |
|---|---|---|
| tests/test_auth_manager.py | All 6 auth controls - 19 tests | 19/19 passing |

Run locally at any time:

    python -m pytest tests/test_auth_manager.py -v

---

*Last reviewed: 2026-05-10*
*Reviewer: EWSimpson1791*
*Repository: https://github.com/EWSimpson1791/SafeVault1791*

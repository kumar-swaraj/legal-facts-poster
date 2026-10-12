# Security Policy

## Supported Versions

The following versions of `legal-facts-poster` currently receive security updates:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1.0 | :x:                |

## Security Architecture & Best Practices

`legal-facts-poster` adopts defense-in-depth principles:
- **Session Credentials Protection**: Stored session state (`session.json`) and local credentials (`~/.config/legal-facts-poster/.env`) are strictly locked with POSIX `0600` permissions (owner read/write only).
- **Container Hardening**: Docker images drop root privileges and execute under the unprivileged `pwuser` account.
- **Graceful Signal Handling**: Listens for `SIGTERM` and `SIGINT` to safely conclude browser tasks and avoid credential or file corruption.
- **Air-Gapped & Offline Control**: Automatic browser binary downloads can be forbidden by setting `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=true`.

## Reporting a Vulnerability

We take the security of `legal-facts-poster` and users' credentials seriously.

If you believe you have discovered a vulnerability (such as secret leakage, session storage insecurity, or dependency exposure):

1. **Do not open a public issue.**
2. Report the vulnerability privately via **[GitHub Private Vulnerability Reporting](https://github.com/kumar-swaraj/legal-facts-poster/security/advisories/new)** or by email to the repository owner at `123369109+kumar-swaraj@users.noreply.github.com`.
3. Provide a clear description of the vulnerability, reproduction steps, and potential impact.

You will receive an acknowledgment within 48 hours, followed by updates on the assessment and release timeline for a security patch.

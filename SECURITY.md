# Safe publication and security
This public research repository must contain only material approved for publication.

## Before publishing
- Keep API keys, tokens, passwords, cookies, private SSH keys, recovery codes, browser storage and HAR captures out of Git.
- Use environment variables or a secret manager for credentials. Commit only sanitized example configuration.
- Export AI session outputs into fresh static Markdown or text files. Remove session/share URLs, authorization headers, signed links and personal data. Inspect notebook outputs, screenshots and document metadata separately.
- Review staged changes AND commit messages. Do not add Claude-Session trailers or interactive conversation links.
- Run `node --test scripts/security-check.test.mjs` and `node scripts/security-check.mjs --since c09812e3e37062903feaac63e48b325dc277197d`.
- The guard checks selected patterns in tracked text and new commit snapshots/messages. It does not inspect binary contents, validate credentials, cover every secret type, prevent a push, or enforce branch protection. Enable GitHub secret scanning and push protection too.
- The baseline excludes four historical commits from routine message scanning because their session links require separate remediation. `node scripts/security-check.mjs --all` includes them. A passing routine check is not a clean historical audit.

## If something is exposed
Revoke or rotate credentials at the provider first; terminate affected sessions and review access logs. Deleting the current file does not remove history or downloaded copies. Coordinate any history rewrite, then inspect forks, clones, pull requests, releases, workflow logs and hosted artifacts.

## Reporting
Do not publish credentials or exploitable details in a public issue. If GitHub private vulnerability reporting is enabled, use the repository Security tab. Otherwise contact the owner through an established private channel, using redacted evidence only.

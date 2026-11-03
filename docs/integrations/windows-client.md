# Windows client handoff

- Intent: provide a native Windows client and let OpenSSH choose an existing identity, including agent-backed identities.
- Branch/worktree: `feat/windows-client`, `../ssh-workspace-windows`.
- Base: local `main` / `origin/main` at `7a082e5`; target: `main` via review. Fetch failed with SSH public-key authentication denied, so upstream freshness is unknown.
- Contract: Windows installer builds an executable with PyInstaller, installs it per-user, and adds its directory to PATH. Generated PowerShell scripts invoke that executable; `--key` is optional and no identity is copied or bridged. Linux server behavior is unchanged.
- Evidence: Python unittest suite and generated PowerShell invocation on Linux; PowerShell installer parsing. See final test output for results.
- Blocker: actual Windows build, native OpenSSH connection, and interactive TUI have not been exercised. Run the Windows CI workflow and an interactive SSH connection on a Windows client before release. Windows and WSL agents require separate configuration or a trusted bridge.
- Activation: changes exist only on this feature branch; no installed client or remote service was changed.
- Next: review against an authenticated, freshly fetched main; run Windows CI and interactive smoke test, then integrate according to repository policy.

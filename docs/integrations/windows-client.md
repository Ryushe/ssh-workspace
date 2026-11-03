# Windows client handoff

- Intent: provide a native Windows client and let OpenSSH choose an existing identity, including agent-backed identities and per-host configuration.
- Branch/worktree: `feat/windows-client`, `../ssh-workspace-windows`.
- Base: local `main` / `origin/main` at `7a082e5`; target: `main` via review. Fetch failed with SSH public-key authentication denied, so upstream freshness is unknown.
- Contract: Windows installer builds an executable with PyInstaller, installs it per-user, and adds its directory to PATH. Generated PowerShell scripts invoke that executable; `--host` defaults to the workspace name; optional user, port, and key settings are left to OpenSSH when omitted. An optional selected WSL distribution owns host aliases and keys; Windows can invoke its OpenSSH without copying keys. The CLI can generate new keys in WSL and select a same-named key when saving a host. Linux server behavior is unchanged.
- Evidence: Python unittest suite and generated PowerShell invocation on Linux; PowerShell installer parsing; isolated OpenSSH configuration resolved with ssh -G; Windows-to-WSL execution exercised with an isolated HOME. See final test output for results.
- Blocker: actual Windows build, native OpenSSH connection, and interactive TUI have not been exercised. Run the Windows CI workflow and an interactive SSH connection on a Windows client before release. Native Windows SSH does not share WSL configuration; the workspace client invokes WSL SSH. Windows-only key import is not implemented.
- Activation: changes exist only on this feature branch; no installed client or remote service was changed.
- Next: review against an authenticated, freshly fetched main; run Windows CI and interactive smoke test, then integrate according to repository policy.

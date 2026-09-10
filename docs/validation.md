# Initial validation

2026-09-10, Linux client and Ubuntu/systemd Hoster target.

- 13 Python unittest cases passed: per-machine defaults, default display aliases,
  local-only setting changes, one-time backend override, SSH exit propagation,
  generated shell quoting, relative paths, argument validation, inactive startup,
  client-only execution, failed startup, timeout without restart, unmanaged server
  refusal, and service/backend cgroup ownership checks.
- Bash syntax validation passed for installer and generated launcher.
- `systemd-analyze --user verify` passed for both installed service definitions.
- Hoster server installer succeeded with existing tmux 3.4 and herdr 0.9.0.
- Both managed servers started under `/user.slice/.../user@1000.service/app.slice/`.
  Backend process ownership matched its corresponding service.
- Real SSH/PTTY attachment and clean detach succeeded for both tmux and herdr.
- A fresh SSH connection found both servers still running with unchanged PIDs.
- Rerunning the installer preserved both server PIDs.
- Hoster's existing default herdr server and Ghost tmux service were preserved.
- The temporary managed tmux test service was stopped after verification. Hoster's
  generated launcher reuses the existing Ghost tmux wrapper. The named herdr
  workspace remains available for normal use.

Not exercised: downloading herdr on a clean machine, apt/dnf/pacman package
installation, and enabling lingering on a previously non-lingering user. The
Hoster installation reused dependencies and `Linger=yes`. Herdr's official
installer was inspected to confirm SHA-256 verification. Other distributions
need their own fresh-install validation.

Review: independent design review approved the plan. Code review found relative
path portability, now fixed and covered; additional lifecycle tests and backend
process ownership checks address the review's verification gaps.

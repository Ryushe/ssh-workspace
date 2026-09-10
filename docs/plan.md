# SSH workspace implementation plan

Goal: deliver reusable ssh-<hostname> launchers and a Linux server installer.
Architecture: one standard-library Python CLI, generated Bash wrappers, Bash
installer and two user systemd service templates.

1. Add behavioral unittest coverage for generation, shell quoting, local defaults,
   per-machine isolation, bad arguments and SSH exit codes. Run tests red.
2. Implement bin/ssh-workspace with generate/connect/server/attach commands.
   Test service ownership, failed startup, readiness and inactive startup paths.
3. Add install.sh client/server modes and systemd templates. Install missing
   tmux/herdr dependencies only, enable lingering, reload without restarting.
4. Document installation, generated launcher use, lifecycle and limitations.
5. Run unit tests, Bash syntax and systemd validation. Review implementation.
6. Install client and generated ssh-hoster locally. Copy repository to Hoster,
   install remote support, retain Ghost tmux attachment, and verify isolated
   named herdr server and reconnection. Commit verified files.
7. Report result and any publication step needing account/visibility selection.

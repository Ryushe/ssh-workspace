# SSH workspace

Approved user contract: Linux/systemd targets; generated `ssh-<hostname>`
commands; tmux and herdr backends; per-machine saved defaults; installer installs
both backends and configures persistent user services. Generator prints a script
containing connection details (never key material). Standard SSH remains intact.

The Python standard-library launcher handles generation and local defaults.
Generated shell scripts delegate to the installed launcher with safely quoted
arguments. `default` and `default nothing` display the setting; `default tmux`
and `default herdr` save it without connecting. A positional backend overrides it
once. Defaults live beneath XDG_CONFIG_HOME/ssh-workspace, initially tmux.

The same executable provides the remote attach and foreground server entrypoints.
Each backend has one user service. tmux uses a dedicated socket and foreground
server; herdr uses the named session ssh-workspace, separate from any preexisting
default session. Normal attach starts inactive services and verifies readiness
and user-manager ownership. It never restarts a running service. Automatic
server restart is disabled to avoid concealing lost interactive work.

An optional existing tmux wrapper lets Hoster continue using ghost-workspace.
The general installer does not migrate, stop, or take ownership of existing
workspaces. The named herdr workspace provides a distinct managed workspace for
this launcher without interrupting Hoster's existing default herdr session.

Client installation only needs Python 3 and OpenSSH. Server installation requires
Linux booted with systemd, installs missing dependencies using apt, dnf or pacman,
downloads herdr through its official checksum-verifying installer, enables
lingering and writes user units. Services start on first connection, not boot.
Installer reruns update files and reload units without restarting sessions.

Verification: isolated HOME/config fixtures and fake SSH for generated scripts,
defaults and quoting; mocked service failures and readiness; bash syntax;
real systemd validation and bounded Hoster attach probes. Live installation uses
existing tmux wrapper and a distinct named herdr server. Publishing a GitHub
repository requires selecting the account and visibility after review.

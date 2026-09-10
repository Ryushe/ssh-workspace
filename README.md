# ssh-workspace

Generate `ssh-<hostname>` commands that open persistent tmux or herdr workspaces
on Linux machines. Each command remembers its own default. OpenSSH still handles
authentication, host verification and transport; private keys stay on the client.

## Install

Clone this repository on the client and run:

```bash
git clone https://github.com/ghostonbutterbread/ssh-workspace.git
cd ssh-workspace
./install.sh client
export PATH="$HOME/.local/bin:$PATH"
```

Clone or copy the repository onto each remote Linux machine. Run the server
installer **as your login user**, not with `sudo`:

```bash
./install.sh server
```

The server installer installs missing Python 3, tmux and curl using apt, dnf or
pacman. It installs herdr, if absent, through the [official installer](https://herdr.dev/docs/install/),
which verifies the downloaded binary's SHA-256 checksum. It uses sudo when
needed for packages and `loginctl enable-linger`. Existing herdr installations
are reused without upgrading them.

The host must already be booted with systemd and have SSH access configured.
The installer configures the user systemd manager; it does not replace the host
init system or configure SSH keys/sshd. Other package managers require manually
installing the dependencies first. The client requires Python 3.8 or newer and OpenSSH.

## Generate a connection script

Run on your client:

```bash
ssh-workspace generate --name example --host 192.0.2.10 \
  --user alice --key ~/.ssh/example > ~/.local/bin/ssh-example
chmod +x ~/.local/bin/ssh-example
```

The generator prints the script to stdout, so you can copy and paste it instead.
`--name` supplies the command label; `--host` supplies the SSH address. Optional
`--port 2222` selects a nonstandard SSH port. Scripts use the installed shared
launcher at `~/.local/bin/ssh-workspace`; `--launcher /path/to/ssh-workspace`
overrides that local path. Regenerate scripts when moving them to another user
or changing connection details. Reuse one name for one machine.

```bash
ssh-example                 # Connect using saved default (initially tmux)
ssh-example herdr           # Use herdr just this time
ssh-example tmux            # Use tmux just this time
ssh-example default herdr   # Save default locally; do not connect
ssh-example default tmux
ssh-example default         # Display the current default
ssh-example default nothing # Same as above
```

Defaults live under `${XDG_CONFIG_HOME:-~/.config}/ssh-workspace/defaults/`.
These commands select the multiplexer; they do not switch or migrate running
programs between tmux and herdr.

## Session lifecycle

The remote launcher starts the selected service on demand, checks readiness and
user-manager ownership, and attaches. Both backends can run concurrently. The
tmux server uses socket `ssh-workspace` and session `workspace`; herdr uses named
session `ssh-workspace`, distinct from your normal herdr default session.

Services are not enabled at boot and have no automatic restart policy. They
survive SSH disconnects through the lingering user manager. Running processes
do **not** survive a host reboot or service stop. Application-specific recovery
features are separate from process persistence. Installer reruns never restart
active workspaces.

Detach from tmux with `Ctrl+b`, then `d`; detach from herdr with `Ctrl+b`, then
`q` (default bindings). Reconnect using the same generated command.

On the remote machine:

```bash
~/.local/bin/ssh-workspace attach herdr --check  # Start/check without TUI
systemctl --user status ssh-workspace-herdr.service
journalctl --user -u ssh-workspace-herdr.service
# Explicitly stop the workspace and all programs it owns:
systemctl --user stop ssh-workspace-herdr.service
```

Replace `herdr` with `tmux` for the other service. If a service is active but its
socket is unavailable, the launcher reports an error and does not restart it.
If the reserved session already exists outside the service, it refuses to take
ownership. Inspect that session before choosing how to resolve the conflict.

Herdr attachment uses its client-only entrypoint (`herdr --session ssh-workspace
client`), verified with 0.9.0. This internal upstream entrypoint may change in
future releases. It avoids the implicit server creation performed by bare
`herdr`. Recheck compatibility when upgrading herdr.

## Reuse an existing tmux workspace

For a machine with an existing wrapper that already manages its systemd service:

```bash
ssh-workspace generate --name example --host 192.0.2.10 \
  --user alice --key ~/.ssh/example \
  --tmux-wrapper .local/bin/my-existing-workspace
```

Only tmux connections use that wrapper; herdr uses the managed named service.
The existing wrapper is responsible for its own lifecycle and ownership checks.
This is how Hoster can continue attaching to its Ghost workspace. `--check`
does not apply to existing wrappers. No tmux server migration is performed.

## Development

No Python packages are required.

```bash
python3 -m unittest discover -s tests -v
bash -n install.sh
systemd-analyze --user verify systemd/*.service
```

The tests use isolated defaults and fake SSH/service commands. Live checks are
needed for TUI attachment and distro package installation. Service verification
requires the launcher installed at its expected path.

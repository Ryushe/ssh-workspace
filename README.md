# ssh-workspace

Generate `ssh-<hostname>` commands from Linux, WSL, or Windows PowerShell
that open persistent tmux or herdr workspaces on Linux machines. Each command remembers its own default. OpenSSH still handles
authentication, host verification and transport; private keys stay on the client.

## Install

Clone this repository on the client and run:

```bash
git clone https://github.com/ryushe/ssh-workspace.git
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
installing the dependencies first. The Linux client requires Python 3.8 or newer and OpenSSH. See below for the Windows client.

## Share hosts and identities with WSL

Choose one WSL distribution to hold your SSH configuration and private keys.
Install the Linux client inside that distribution and the Windows client as
shown below. From PowerShell, select it once (list installed distributions with
`wsl --list --quiet`):

```powershell
ssh-workspace wsl use Ubuntu
```

From either WSL or PowerShell, save a host using its IP address:

```text
ssh-workspace host set --name hoster --host 192.0.2.10 --user alice
```

If `~/.ssh/hoster` exists in the selected WSL distribution when you save the
host, it is selected automatically. Otherwise OpenSSH uses its configured
identities and agent. To select another key explicitly, add `--key
/home/your-user/.ssh/key-name` (a path inside WSL). Save the host again if you
add a same-named key later. Host entries are kept under
`~/.ssh/ssh-workspace.d/`, with an Include at the beginning of `~/.ssh/config`;
existing configuration is retained. A managed entry takes precedence for that
alias. The command refuses to rewrite a symlinked SSH config.

To create a new key in the shared WSL location from either environment, run
`ssh-workspace identity generate --name hoster`. OpenSSH prompts for a
passphrase and will not overwrite an existing key. Install the resulting
**public** key on the remote machine using your normal provisioning process.
Existing WSL keys do not need to be imported or copied. Importing a key that
exists only in Windows is not yet automated.

Generate `ssh-hoster` in WSL and `ssh-hoster.ps1` in PowerShell using the
examples below. PowerShell's workspace command starts the selected WSL
instance when necessary and uses its OpenSSH client, config, keys, and any agent
available to that WSL process.
No background synchronization or private-key copies are needed. Standard
`ssh hoster` in WSL also uses the entry. Native Windows `ssh hoster` uses
Windows' own SSH configuration; this setup does not change it. Host aliases
are for SSH, not system-wide DNS names. `--wsl-distro Ubuntu` can explicitly
select a distribution for an individual operation.

## Use an SSH host alias

OpenSSH can associate a convenient name with an IP address, user, port, and
identity. For example, add this to `~/.ssh/config` in WSL or Linux (use your
actual address and account):

```sshconfig
Host hoster
    HostName 192.0.2.10
    User alice
    IdentityFile ~/.ssh/hoster
    IdentitiesOnly yes
```

Native Windows OpenSSH reads `%USERPROFILE%\.ssh\config`. Configure the same
alias there if you also want to connect with native Windows `ssh`. The shared
WSL setup above lets PowerShell workspace commands use the WSL alias instead. Each client reads its own configuration; adding an alias does
not move keys or make a WSL key available to Windows. The `IdentityFile` can be
omitted when the configured agent should choose the identity.

Generate a command using the alias as the workspace name:

```bash
ssh-workspace generate --name hoster > ~/.local/bin/ssh-hoster
chmod +x ~/.local/bin/ssh-hoster
ssh-hoster
```

On Windows, use `ssh-workspace generate --name hoster --output
"$env:LOCALAPPDATA\ssh-workspace\bin\ssh-hoster.ps1"` instead. OpenSSH resolves
the alias at connection time, so changes to its address or identity do not
require regenerating the command. `ssh -G hoster` displays the effective
configuration without connecting. If there is no matching alias, OpenSSH tries
to resolve the name as a network hostname and uses its normal identity and user
selection; ssh-workspace does not guess keys from filenames.

## Generate a connection script

Run on your client:

```bash
ssh-workspace generate --name example --host 192.0.2.10 \
  --user alice --key ~/.ssh/example > ~/.local/bin/ssh-example
chmod +x ~/.local/bin/ssh-example
```

The generator prints the script to stdout, so you can copy and paste it instead.
`--name` supplies the command label and, unless `--host` is provided, the SSH
host or config alias. `--host`, `--user`, `--key`, and `--port` explicitly
select those settings; omitted options are left to OpenSSH. Scripts use the installed shared
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

## Windows and PowerShell client

The remote workspace still runs on Linux. On Windows, install Python 3.8 or
newer and the Windows OpenSSH Client, clone the repository, and run in PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

The installer builds a standalone `ssh-workspace.exe` using PyInstaller (which
it installs with pip for the current user if missing), installs it under
`%LOCALAPPDATA%\ssh-workspace\bin`, and adds that directory to the user PATH.
Open a new PowerShell window afterward. The resulting executable does not need
Python at runtime. Installation does not change the system execution policy.

Generate a PowerShell command in that same directory, which is on PATH:

```powershell
ssh-workspace generate --name example --host 192.0.2.10 --user alice `
  --output "$env:LOCALAPPDATA\ssh-workspace\bin\ssh-example.ps1"
ssh-example
ssh-example default herdr
```

If PowerShell blocks local scripts, follow your organization's policy for
allowing locally created scripts, or run the generated script with
`powershell -ExecutionPolicy Bypass -File <path>`. Use `--key` to select an
explicit Windows private-key path; omit it to let OpenSSH use its normal
configuration and agent. `--output` writes the script with a UTF-8 BOM so it
also works with Windows PowerShell 5.1. The generated command remembers its
local executable path and should be regenerated if moved to another account.

### Identities across Windows and WSL

With `wsl use`, workspace connections from PowerShell use WSL's OpenSSH and
keys directly. Windows' native OpenSSH remains separate. Without a selected WSL
distribution, the Windows client uses native OpenSSH and its configuration.
Defaults and generated launchers remain local to each environment.

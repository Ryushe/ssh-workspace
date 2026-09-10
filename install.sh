#!/usr/bin/env bash
# Run as the account that will own the workspaces, not with sudo.
set -euo pipefail
mode=${1:-}
case "$mode" in
  client|server) [[ $# == 1 ]] || { echo 'usage: ./install.sh client|server' >&2; exit 2; } ;;
  *) echo 'usage: ./install.sh client|server' >&2; exit 2 ;;
esac
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
export PATH="$HOME/.local/bin:$PATH"
fail() { printf 'ssh-workspace install: %s\n' "$*" >&2; exit 1; }

if [[ "$mode" == server ]]; then
  [[ $(uname -s) == Linux && -d /run/systemd/system ]] || fail 'server requires Linux booted with systemd'
  [[ $(id -u) != 0 ]] || fail 'run as your login user; sudo is used only for packages and lingering'
  command -v systemctl >/dev/null || fail 'systemd must already be the host init system'
  packages=()
  for tool in python3 tmux curl; do
    command -v "$tool" >/dev/null || packages+=("$tool")
  done
  if (( ${#packages[@]} )); then
    command -v sudo >/dev/null || fail "install missing packages as root: ${packages[*]}"
    if command -v apt-get >/dev/null; then
      sudo apt-get update
      sudo apt-get install -y "${packages[@]}"
    elif command -v dnf >/dev/null; then
      sudo dnf install -y "${packages[@]}"
    elif command -v pacman >/dev/null; then
      # Arch names its Python 3 package python.
      for i in "${!packages[@]}"; do
        [[ ${packages[$i]} != python3 ]] || packages[$i]=python
      done
      sudo pacman -S --needed --noconfirm "${packages[@]}"
    else
      fail "unsupported package manager; install ${packages[*]} and rerun"
    fi
  fi
  if ! command -v herdr >/dev/null; then
    installer=$(mktemp)
    trap 'rm -f -- "$installer"' EXIT
    curl -fsSL --connect-timeout 10 --max-time 60 https://herdr.dev/install.sh -o "$installer"
    HERDR_INSTALL_DIR="$HOME/.local/bin" sh "$installer"
  fi
  herdr --version
  tmux -V
  if [[ $(loginctl show-user "$(id -un)" -p Linger --value) != yes ]]; then
    sudo loginctl enable-linger "$(id -un)"
  fi
  [[ $(loginctl show-user "$(id -un)" -p Linger --value) == yes ]] || fail 'failed to enable lingering'
  export XDG_RUNTIME_DIR="/run/user/$(id -u)"
  export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
  systemctl --user show-environment >/dev/null || fail 'user manager unavailable; log in again after enabling lingering'
  unit_dir="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
  # Check both destinations before updating the launcher or either unit.
  for backend in tmux herdr; do
    unit="ssh-workspace-$backend.service"
    existing=$(systemctl --user show "$unit" -p FragmentPath --value)
    if [[ -n "$existing" && "$existing" != "$unit_dir/$unit" ]]; then
      fail "$unit is already defined at $existing; inspect its owner first"
    fi
    if [[ -f "$unit_dir/$unit" ]] && ! grep -q '^# Managed by ssh-workspace$' "$unit_dir/$unit"; then
      fail "$unit_dir/$unit is not managed by this installer"
    fi
  done
fi

command -v python3 >/dev/null || fail 'install Python 3 first'
command -v ssh >/dev/null || fail 'install an OpenSSH client first'
install -d "$HOME/.local/bin"
install -m 755 "$repo/bin/ssh-workspace" "$HOME/.local/bin/ssh-workspace"

if [[ "$mode" == server ]]; then
  # Honor systemd/XDG locations; no sessions are stopped or restarted here.
  install -d "$unit_dir"
  for backend in tmux herdr; do
    unit="ssh-workspace-$backend.service"
    install -m 644 "$repo/systemd/$unit" "$unit_dir/$unit"
  done
  systemctl --user daemon-reload
  systemctl --user show ssh-workspace-tmux.service ssh-workspace-herdr.service -p Id -p LoadState -p ActiveState
  echo 'Server installed. Workspaces start on first connection and persist after logout.'
else
  echo 'Client installed.'
fi
echo 'Launcher: ~/.local/bin/ssh-workspace (add ~/.local/bin to PATH if needed)'

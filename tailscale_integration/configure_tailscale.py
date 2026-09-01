"""
Join the robot to a Tailscale tailnet.

Installs Tailscale from the official Tailscale apt repository at a pinned
version, enables tailscaled via systemd, and authenticates using a reusable
auth key from .env.json. Safe to re-run: if the robot is already connected
under the expected hostname, the `tailscale up` step is skipped.

Run from the repo root (where inventory.py lives):
    poetry run pyinfra inventory.py tailscale_integration/configure_tailscale.py

Prerequisites:
  - .env.json in this folder, copied from .env.json.example, with
    TAILSCALE_AUTHKEY set to a reusable auth key. See .env.json.example
    for where to generate one.
"""

import io
import json
import shlex
from pathlib import Path

from pyinfra import host
from pyinfra.facts.server import Command, OsRelease
from pyinfra.operations import apt, files, server, systemd

TAILSCALE_VERSION = "1.98.2"

with open(Path(__file__).parent / ".env.json") as f:
    env_config = json.load(f)

authkey = env_config.get("TAILSCALE_AUTHKEY", "")
if not authkey or authkey == "tskey-auth-xxxxxxxxxxxx":
    raise ValueError(
        "TAILSCALE_AUTHKEY is missing or still a placeholder in .env.json — "
        "create a reusable auth key at "
        "https://login.tailscale.com/admin/settings/keys and set it there."
    )

desired_hostname = env_config.get("TAILSCALE_HOSTNAME") or host.name

# Detect distro for the correct apt repo URL (Raspberry Pi OS reports
# ID=debian on Bookworm, ID=raspbian on older 32-bit images — both are
# served from pkgs.tailscale.com under their own name).
os_info = host.get_fact(OsRelease) or {}
distro_id = os_info.get("id", "debian").lower()
codename = os_info.get("version_codename", "bookworm")

tailscale_base = f"https://pkgs.tailscale.com/stable/{distro_id}"

files.download(
    name="Download Tailscale apt signing key",
    src=f"{tailscale_base}/{codename}.noarmor.gpg",
    dest="/usr/share/keyrings/tailscale-archive-keyring.gpg",
    _sudo=True,
)

files.download(
    name="Download Tailscale apt source list",
    src=f"{tailscale_base}/{codename}.tailscale-keyring.list",
    dest="/etc/apt/sources.list.d/tailscale.list",
    _sudo=True,
)

apt.packages(
    name=f"Install tailscale {TAILSCALE_VERSION}",
    packages=[f"tailscale={TAILSCALE_VERSION}"],
    update=True,
    _sudo=True,
)

systemd.service(
    name="Enable and start tailscaled",
    service="tailscaled",
    enabled=True,
    running=True,
    _sudo=True,
)

# Check whether we're already correctly joined before touching anything,
# so a re-run against an already-connected robot is a true no-op.
status_output = host.get_fact(
    Command, command="tailscale status --json || echo '{}'", _sudo=True
)
try:
    status = json.loads(status_output)
except (TypeError, json.JSONDecodeError):
    status = {}

already_joined = (
    status.get("BackendState") == "Running"
    and status.get("Self", {}).get("HostName") == desired_hostname
)

if not already_joined:
    # Transfer the auth key via SFTP to avoid it appearing in SSH command
    # logs or process argument lists. The temp file is root-only and
    # deleted immediately after use.
    files.put(
        name="Stage auth key for tailscale up",
        src=io.StringIO(authkey),
        dest="/root/.ts_authkey",
        mode="600",
        _sudo=True,
    )

    up_command = " ".join([
        "tailscale up",
        f"--hostname={shlex.quote(desired_hostname)}",
        "--ssh",
        '--authkey="$(cat /root/.ts_authkey)"',
    ])

    server.shell(
        name="Authenticate to tailnet and remove staged key",
        commands=[
            up_command,
            "rm -f /root/.ts_authkey",
        ],
        _sudo=True,
    )

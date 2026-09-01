# Tailscale integration

Joins the robot to a [Tailscale](https://tailscale.com/) tailnet, so it's
reachable from anywhere on the tailnet even when mDNS (`.local` hostnames)
can't reach it — different network, guest Wi-Fi, no multicast, etc.

Shares this repo's `inventory.py`, so it targets whichever robot(s) that
inventory already points at.

## TL;DR

```bash
cp .env.json.example .env.json
# edit .env.json, fill in TAILSCALE_AUTHKEY
poetry run pyinfra inventory.py configure_tailscale.py
```

## Setup

1. Generate a **reusable** auth key at
   [the Tailscale admin console](https://login.tailscale.com/admin/settings/keys).
   Reusable is required so re-running the deploy doesn't fail on a
   already-spent key. Pre-authorized avoids a manual approval step per robot.
2. Copy `.env.json.example` to `.env.json` and set `TAILSCALE_AUTHKEY` to
   that key. `.env.json` is gitignored — never commit it.
3. Optionally set `TAILSCALE_HOSTNAME` in `.env.json` to control the name
   the robot advertises on the tailnet. If left blank, it uses the
   inventory hostname as-is.
4. Run:
   ```bash
   poetry run pyinfra inventory.py configure_tailscale.py
   ```

## What it does

- Installs Tailscale from Tailscale's own apt repository (the official
  install path), pinned to a specific version.
- Enables and starts the `tailscaled` systemd service.
- Runs `tailscale up --ssh` with the auth key, so the robot both joins the
  tailnet and accepts Tailscale SSH — a second, mDNS-independent way to
  reach it for further `pyinfra` runs.

Re-running the script is safe: if the robot is already connected under the
expected hostname, the join step is skipped entirely.

## More detail

See the tailscale-pyinfra labnotes and the orionrobots post (once
published) for the fuller write-up of the approach and how it was tested.

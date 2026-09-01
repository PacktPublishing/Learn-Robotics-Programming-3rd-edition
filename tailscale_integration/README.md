# Tailscale integration

Joins the robot to a [Tailscale](https://tailscale.com/) tailnet, so it's
reachable from anywhere on the tailnet even when mDNS (`.local` hostnames)
can't reach it — different network, guest Wi-Fi, no multicast, etc.

Shares the repo root's `inventory.py`, so it targets whichever robot(s)
that inventory already points at.

## TL;DR

Run from the repo root (where `inventory.py` lives):

```bash
cp tailscale_integration/.env.json.example tailscale_integration/.env.json
# edit tailscale_integration/.env.json, fill in TAILSCALE_AUTHKEY
poetry run pyinfra inventory.py tailscale_integration/configure_tailscale.py
```

## Setup

1. Generate a **reusable** auth key at
   [the Tailscale admin console](https://login.tailscale.com/admin/settings/keys).
   Reusable is required so re-running the deploy doesn't fail on an
   already-spent key. Pre-authorized avoids a manual approval step per robot.
2. Copy `tailscale_integration/.env.json.example` to
   `tailscale_integration/.env.json` and set `TAILSCALE_AUTHKEY` to that
   key. `.env.json` is gitignored — never commit it.
3. Optionally set `TAILSCALE_HOSTNAME` in `.env.json` to control the name
   the robot advertises on the tailnet. If left blank, it uses the
   inventory hostname as-is.
4. Run from the repo root:
   ```bash
   poetry run pyinfra inventory.py tailscale_integration/configure_tailscale.py
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

## Notes for first-time use

- **Auth keys are usually painless** — generating one and pasting it into
  `.env.json` worked first time in testing. If `tailscale up` reports
  `invalid key: API key does not exist`, the key you're using has been
  rotated/revoked — generate a fresh one, it's a 30-second fix.
- **Tailscale SSH needs a one-time interactive approval.** Because this
  script enables `--ssh`, the robot accepts SSH connections authenticated
  via Tailscale. The *first* time you (or a tool) SSH to the robot over
  its tailnet name/IP, Tailscale will want an interactive check
  (a browser approval) before it lets the connection through. Do a manual
  `ssh <robot>` over the tailnet once yourself and approve it, **before**
  pointing any further `pyinfra` run at the robot over the tailnet route —
  a non-interactive pyinfra run has no way to complete that check itself
  and will just hang or fail.

## More detail

See the tailscale-pyinfra labnotes and the orionrobots post (once
published) for the fuller write-up of the approach and how it was tested.

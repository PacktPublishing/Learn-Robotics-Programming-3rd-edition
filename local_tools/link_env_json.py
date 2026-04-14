"""Ensure all chapter stage robot_control .env.json files are symlinks to root .env.json.

Run with pyinfra from repository root, for example:
    poetry run pyinfra @local local_tools/link_env_json.py
"""

from pathlib import Path

from pyinfra import host
from pyinfra.operations import files


REPO_ROOT = Path(__file__).resolve().parent.parent
ROOT_ENV_PATH = REPO_ROOT / ".env.json"
LINK_TARGET = Path("../../../.env.json")


if not ROOT_ENV_PATH.exists():
    raise FileNotFoundError(
        f"Root .env.json not found at {ROOT_ENV_PATH}. "
        "Create it before running this deploy."
    )


robot_control_dirs = sorted(
    path for path in REPO_ROOT.glob("chapter-*/*/robot_control") if path.is_dir()
)

if not robot_control_dirs:
    raise RuntimeError(
        "No chapter stage robot_control directories found under chapter-*/*/robot_control."
    )


for robot_control_dir in robot_control_dirs:
    relative_dir = robot_control_dir.relative_to(REPO_ROOT)
    env_link_path = relative_dir / ".env.json"

    files.link(
        name=f"Link {env_link_path}",
        path=str(env_link_path),
        target=str(LINK_TARGET),
        symbolic=True,
        force=True,
    )


host.noop(
    "Configured .env.json symlinks for "
    f"{len(robot_control_dirs)} robot_control directories"
)

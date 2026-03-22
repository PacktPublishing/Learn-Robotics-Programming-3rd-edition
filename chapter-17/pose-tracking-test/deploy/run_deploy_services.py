import argparse
import ast
import subprocess
import sys
from pathlib import Path


def load_hosts(inventory_path: Path) -> list[str]:
    module = ast.parse(inventory_path.read_text(encoding="utf-8"), filename=str(inventory_path))

    robots_value = None
    for node in module.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "robots":
                    robots_value = ast.literal_eval(node.value)
                    break
        if robots_value is not None:
            break

    if robots_value is None:
        raise RuntimeError(f"Could not find 'robots' in {inventory_path}")

    hosts: list[str] = []
    for entry in robots_value:
        if isinstance(entry, (tuple, list)) and entry:
            host = entry[0]
            if isinstance(host, str) and host not in hosts:
                hosts.append(host)

    if not hosts:
        raise RuntimeError(f"No hostnames found in {inventory_path}")

    return hosts


def choose_host(hosts: list[str], requested_host: str | None) -> str:
    if requested_host:
        if requested_host not in hosts:
            raise RuntimeError(
                f"Host '{requested_host}' not in inventory. Valid hosts: {', '.join(hosts)}"
            )
        return requested_host

    print("Select target host:")
    for index, host in enumerate(hosts, start=1):
        print(f"  {index}) {host}")

    while True:
        response = input("Enter number (default 1): ").strip()
        if not response:
            return hosts[0]
        if response.isdigit():
            selected_index = int(response)
            if 1 <= selected_index <= len(hosts):
                return hosts[selected_index - 1]
        print(f"Invalid selection. Choose 1-{len(hosts)}.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deploy/deploy_services.py via pyinfra")
    parser.add_argument("--host", help="Target hostname from inventory.py")
    args = parser.parse_args()

    workspace_root = Path(__file__).resolve().parents[1]
    inventory_file = workspace_root / "inventory.py"

    hosts = load_hosts(inventory_file)
    host = choose_host(hosts, args.host)

    cmd = [
        "pyinfra",
        "inventory.py",
        "deploy/deploy_services.py",
        "-y",
        "--limit",
        host,
    ]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=workspace_root)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())

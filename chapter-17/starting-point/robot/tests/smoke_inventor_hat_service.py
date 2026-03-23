import ast
from pathlib import Path


def encoder_payload_keys(service_path: Path) -> set[str]:
    module = ast.parse(service_path.read_text())
    keys: set[str] = set()

    for node in ast.walk(module):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name):
            continue
        if node.func.id != "publish_json":
            continue
        if len(node.args) < 3:
            continue

        topic = node.args[1]
        payload = node.args[2]

        if not isinstance(topic, ast.Constant):
            continue
        if topic.value != "sensors/encoders/data":
            continue
        if not isinstance(payload, ast.Dict):
            continue

        for key in payload.keys:
            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                keys.add(key.value)

    return keys


def run_smoke_check() -> None:
    service_path = (
        Path(__file__).resolve().parents[1] / "inventor_hat_service.py"
    )
    keys = encoder_payload_keys(service_path)

    required = {
        "seq",
        "timestamp_ms",
        "left_distance",
        "right_distance",
        "left_mm_per_sec",
        "right_mm_per_sec",
    }
    missing = sorted(required - keys)
    assert not missing, f"Missing encoder payload keys: {missing}"

    print("smoke_inventor_hat_service: PASS")
    print(f"payload keys: {sorted(keys)}")


if __name__ == "__main__":
    run_smoke_check()

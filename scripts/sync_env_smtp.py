"""Copy SMTP_* variables from .env.example into .env (one-time helper)."""

from pathlib import Path


def parse_env(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        data[key.strip()] = value
    return data


def format_env(data: dict[str, str]) -> str:
    lines: list[str] = []
    for key, value in data.items():
        if " " in value or "#" in value:
            lines.append(f'{key}="{value}"')
        else:
            lines.append(f"{key}={value}")
    return "\n".join(lines) + "\n"


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    env_path = root / ".env"
    example_path = root / ".env.example"
    if not env_path.is_file():
        raise SystemExit("Create .env first: copy .env.example .env")

    env = parse_env(env_path)
    example = parse_env(example_path)
    for key in ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD", "SMTP_FROM", "SMTP_USE_TLS"):
        if example.get(key):
            env[key] = example[key]

    if env.get("SMTP_USER") and (
        not env.get("SMTP_FROM") or env["SMTP_FROM"] in ("noreply@example.com", "")
    ):
        env["SMTP_FROM"] = env["SMTP_USER"]

    env_path.write_text(format_env(env), encoding="utf-8")
    print("SMTP settings copied from .env.example to .env")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Interactively choose which service tiles are written to the user config."""
import json
import sys
from pathlib import Path


def main():
    path = Path(sys.argv[1])
    services = json.loads(path.read_text())
    print("Choose the services to show in TV mode.")
    for number, service in enumerate(services, 1):
        print(f"  {number}. {service['name']}")
    answer = input("Numbers separated by spaces (blank keeps all): ").strip()
    if not answer:
        return
    try:
        selected = {int(item) for item in answer.split()}
        chosen = [service for number, service in enumerate(services, 1) if number in selected]
    except ValueError as error:
        raise SystemExit(f"invalid selection: {error}") from error
    if not chosen:
        raise SystemExit("select at least one service")
    path.write_text(json.dumps(chosen, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Smoke test for the built miggo-mcp binary.

Runs a full MCP session (initialize -> tools/list -> tools/call services_count)
against the packaged binary using the same launcher wrapper as manifest.json.
Asserts:
  1. stdout is pure JSON-RPC (no Pyfuze extraction pollution)
  2. initialize handshake returns protocolVersion 2025-06-18
  3. tools/list reports >= 25 tools including services_count
  4. services_count returns a non-negative integer (auth + API round-trip)

Usage:
    MIGGO_PUBLIC_TOKEN=... python scripts/smoke_test.py dist/miggo-mcp
    MIGGO_PUBLIC_TOKEN=... python scripts/smoke_test.py dist/miggo-mcp.exe  # Windows
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys

INIT_ID = 0
LIST_ID = 1
COUNT_ID = 2
EXPECTED_PROTOCOL = "2025-06-18"
MIN_TOOLS = 25


def run_binary(
    binary: str, stdin_payload: str, timeout: int, env: dict[str, str]
) -> subprocess.CompletedProcess:
    """Invoke the binary via the same launcher wrapper as manifest.json."""
    if platform.system() == "Windows":
        # shell=True on Windows prepends `cmd /c` and passes the string through
        # without list2cmdline escaping, so inner quotes survive for cmd to parse.
        cmd: str | list[str] = f'"{binary}" <nul >nul 2>&1 & "{binary}"'
        return subprocess.run(  # noqa: S602
            cmd,
            shell=True,
            input=stdin_payload,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
    cmd = [
        "bash",
        "-c",
        (
            f"chmod +x '{binary}' 2>/dev/null; "
            f"'{binary}' < /dev/null > /dev/null 2>&1; "
            f"exec '{binary}'"
        ),
    ]
    return subprocess.run(
        cmd,
        input=stdin_payload,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )


def fail(msg: str, *, stderr: str | None = None) -> int:
    print(f"FAIL: {msg}", file=sys.stderr)
    if stderr:
        print("--- child stderr ---", file=sys.stderr)
        print(stderr, file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", help="Path to the built miggo-mcp binary")
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()

    token = os.environ.get("MIGGO_PUBLIC_TOKEN")
    if not token:
        return fail("MIGGO_PUBLIC_TOKEN not set")

    requests = [
        {
            "jsonrpc": "2.0",
            "id": INIT_ID,
            "method": "initialize",
            "params": {
                "protocolVersion": EXPECTED_PROTOCOL,
                "capabilities": {},
                "clientInfo": {"name": "smoke", "version": "0"},
            },
        },
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        {"jsonrpc": "2.0", "id": LIST_ID, "method": "tools/list", "params": {}},
        {
            "jsonrpc": "2.0",
            "id": COUNT_ID,
            "method": "tools/call",
            "params": {"name": "services_count", "arguments": {}},
        },
    ]
    stdin_payload = "\n".join(json.dumps(r) for r in requests) + "\n"

    proc = run_binary(
        args.binary,
        stdin_payload,
        args.timeout,
        env={**os.environ, "MIGGO_PUBLIC_TOKEN": token},
    )

    responses: dict[int, dict] = {}
    for lineno, line in enumerate(proc.stdout.splitlines(), 1):
        if not line.strip():
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            return fail(
                f"stdout line {lineno} is not valid JSON: {line[:200]!r}",
                stderr=proc.stderr,
            )
        if "id" in msg:
            responses[msg["id"]] = msg

    init = responses.get(INIT_ID)
    if not init or init.get("result", {}).get("protocolVersion") != EXPECTED_PROTOCOL:
        return fail(f"initialize handshake invalid: {init!r}", stderr=proc.stderr)

    lst = responses.get(LIST_ID)
    tools = (lst or {}).get("result", {}).get("tools", [])
    names = {t["name"] for t in tools}
    if len(tools) < MIN_TOOLS or "services_count" not in names:
        return fail(
            f"tools/list missing tools (got {len(tools)}, need >= {MIN_TOOLS}, services_count present: {'services_count' in names})",
            stderr=proc.stderr,
        )

    cnt = responses.get(COUNT_ID)
    if not cnt:
        return fail("no response to services_count", stderr=proc.stderr)
    if cnt.get("error"):
        return fail(
            f"services_count JSON-RPC error: {cnt['error']}", stderr=proc.stderr
        )
    result = cnt.get("result", {})
    if result.get("isError"):
        return fail(f"services_count tool error: {result}", stderr=proc.stderr)
    data = result.get("structuredContent", {}).get("data")
    if not isinstance(data, int) or data < 0:
        return fail(
            f"services_count returned {data!r}, expected non-negative int",
            stderr=proc.stderr,
        )

    print(
        f"PASS: {len(tools)} tools registered, {data} services reachable",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

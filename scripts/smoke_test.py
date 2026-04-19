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
import time

INIT_ID = 0
LIST_ID = 1
COUNT_ID = 2
EXPECTED_PROTOCOL = "2025-06-18"
MIN_TOOLS = 25
PER_RESPONSE_TIMEOUT = 60


def launch_args(binary: str) -> tuple[str | list[str], bool]:
    """Return (command, shell) matching manifest.json's launcher wrapper."""
    if platform.system() == "Windows":
        # shell=True on Windows prepends `cmd /c` and passes the string through
        # without list2cmdline escaping, so inner quotes survive for cmd to parse.
        return f'"{binary}" <nul >nul 2>&1 & "{binary}"', True
    cmd = [
        "bash",
        "-c",
        (
            f"chmod +x '{binary}' 2>/dev/null; "
            f"'{binary}' < /dev/null > /dev/null 2>&1; "
            f"exec '{binary}'"
        ),
    ]
    return cmd, False


def fail(msg: str, *, stderr: str | None = None) -> int:
    print(f"FAIL: {msg}", file=sys.stderr)
    if stderr:
        print("--- child stderr ---", file=sys.stderr)
        print(stderr, file=sys.stderr)
    return 1


def read_response(
    proc: subprocess.Popen,
    target_id: int,
    non_json: list[tuple[int, str]],
    lineno_ref: list[int],
) -> dict | None:
    """Read stdout lines until a JSON object with `target_id` arrives."""
    deadline = time.time() + PER_RESPONSE_TIMEOUT
    assert proc.stdout is not None  # noqa: S101
    while time.time() < deadline:
        line = proc.stdout.readline()
        if not line:
            return None
        lineno_ref[0] += 1
        stripped = line.strip()
        if not stripped:
            continue
        try:
            msg = json.loads(stripped)
        except json.JSONDecodeError:
            non_json.append((lineno_ref[0], stripped))
            continue
        if msg.get("id") == target_id:
            return msg
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", help="Path to the built miggo-mcp binary")
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Total timeout (seconds) for the session shutdown after requests",
    )
    args = parser.parse_args()

    token = os.environ.get("MIGGO_PUBLIC_TOKEN")
    if not token:
        return fail("MIGGO_PUBLIC_TOKEN not set")

    init_req = {
        "jsonrpc": "2.0",
        "id": INIT_ID,
        "method": "initialize",
        "params": {
            "protocolVersion": EXPECTED_PROTOCOL,
            "capabilities": {},
            "clientInfo": {"name": "smoke", "version": "0"},
        },
    }
    initialized = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {},
    }
    list_req = {"jsonrpc": "2.0", "id": LIST_ID, "method": "tools/list", "params": {}}
    count_req = {
        "jsonrpc": "2.0",
        "id": COUNT_ID,
        "method": "tools/call",
        "params": {"name": "services_count", "arguments": {}},
    }

    cmd, shell = launch_args(args.binary)
    env = {**os.environ, "MIGGO_PUBLIC_TOKEN": token}
    proc = subprocess.Popen(  # noqa: S602 — shell=True is required for Windows cmd quoting
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        env=env,
        shell=shell,
    )
    assert proc.stdin is not None  # noqa: S101

    non_json: list[tuple[int, str]] = []
    lineno_ref = [0]
    responses: dict[int, dict] = {}

    def send(msg: dict) -> None:
        proc.stdin.write(json.dumps(msg) + "\n")  # type: ignore[union-attr]
        proc.stdin.flush()  # type: ignore[union-attr]

    stderr_output = ""
    try:
        send(init_req)
        init = read_response(proc, INIT_ID, non_json, lineno_ref)
        if init is None:
            return fail("no response to initialize", stderr=_drain(proc))
        responses[INIT_ID] = init

        send(initialized)
        send(list_req)
        lst = read_response(proc, LIST_ID, non_json, lineno_ref)
        if lst is None:
            return fail("no response to tools/list", stderr=_drain(proc))
        responses[LIST_ID] = lst

        send(count_req)
        cnt = read_response(proc, COUNT_ID, non_json, lineno_ref)
        if cnt is None:
            return fail("no response to services_count", stderr=_drain(proc))
        responses[COUNT_ID] = cnt
    finally:
        try:
            proc.stdin.close()
        except BrokenPipeError:
            pass
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        assert proc.stderr is not None  # noqa: S101
        stderr_output = proc.stderr.read()

    # Assertion 1: no non-JSON stdout lines
    if non_json:
        lineno, snippet = non_json[0]
        return fail(
            f"stdout line {lineno} is not valid JSON: {snippet[:200]!r}",
            stderr=stderr_output,
        )

    # Assertion 2: handshake
    init = responses[INIT_ID]
    if init.get("result", {}).get("protocolVersion") != EXPECTED_PROTOCOL:
        return fail(f"initialize handshake invalid: {init!r}", stderr=stderr_output)

    # Assertion 3: tools/list
    lst = responses[LIST_ID]
    tools = lst.get("result", {}).get("tools", [])
    names = {t["name"] for t in tools}
    if len(tools) < MIN_TOOLS or "services_count" not in names:
        return fail(
            f"tools/list missing tools (got {len(tools)}, need >= {MIN_TOOLS}, "
            f"services_count present: {'services_count' in names})",
            stderr=stderr_output,
        )

    # Assertion 4: services_count returns a non-negative int
    cnt = responses[COUNT_ID]
    if cnt.get("error"):
        return fail(
            f"services_count JSON-RPC error: {cnt['error']}", stderr=stderr_output
        )
    result = cnt.get("result", {})
    if result.get("isError"):
        return fail(f"services_count tool error: {result}", stderr=stderr_output)
    data = result.get("structuredContent", {}).get("data")
    if not isinstance(data, int) or data < 0:
        return fail(
            f"services_count returned {data!r}, expected non-negative int",
            stderr=stderr_output,
        )

    print(
        f"PASS: {len(tools)} tools registered, {data} services reachable",
        file=sys.stderr,
    )
    return 0


def _drain(proc: subprocess.Popen) -> str:
    """Best-effort stderr drain after a failure."""
    if proc.stdin:
        try:
            proc.stdin.close()
        except BrokenPipeError:
            pass
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    return proc.stderr.read() if proc.stderr else ""


if __name__ == "__main__":
    sys.exit(main())

import os
import subprocess
import sys
from types import SimpleNamespace

import pytest

from pb import main as pb_main

SAMPLE_OUTPUT = (
    "p100\ncbrave\nu1000\nn127.0.0.1:8080\nn*:80\n"
    "p200\ncNetworkMa\nu0\nn*:443\n"
    "p300\ncGoogle Chrome\nu1000\nn[::1]:9000->[::1]:9001\n"
    "p400\ncproc\nu1000\nnlocalhost:service\n"
)

PS_NAMES = {
    "100": "brave",
    "200": "NetworkManager",
    "300": "Google Chrome",
    "400": "proc",
}

PS_ARGS = {
    "100": "/usr/bin/brave",
    "200": "/usr/sbin/NetworkManager",
    "300": "/opt/google/chrome",
    "400": "/usr/bin/proc",
}


@pytest.fixture
def patched_lsof(monkeypatch):
    calls = []

    def fake_check_output(command, *args, **kwargs):
        calls.append(list(command))
        first = command[1] if command and command[0] == "sudo" else command[0]
        if first == "lsof":
            return SAMPLE_OUTPUT
        if first == "ps":
            pid = command[command.index("-p") + 1]
            mode = command[-1]
            if mode.startswith("comm"):
                return PS_NAMES.get(pid, "unknown") + "\n"
            if mode.startswith("args"):
                return PS_ARGS.get(pid, "unknown") + "\n"
            return "\n"
        raise AssertionError(f"unexpected command: {command}")

    pb_main.get_process_name.cache_clear()
    pb_main.get_command_path.cache_clear()
    monkeypatch.setattr(subprocess, "check_output", fake_check_output)
    monkeypatch.setattr(
        pb_main.pwd,
        "getpwuid",
        lambda uid: SimpleNamespace(pw_name=f"testuser-{uid}"),
    )
    yield calls
    pb_main.get_process_name.cache_clear()
    pb_main.get_command_path.cache_clear()


def test_parse_lsof_records():
    records = pb_main.parse_lsof_output(SAMPLE_OUTPUT)
    assert [record["pid"] for record in records] == ["100", "200", "300", "400"]
    assert records[2]["command"] == "Google Chrome"
    assert records[0]["connections"] == ["127.0.0.1:8080", "*:80"]
    assert records[0]["uid"] == "1000"


def test_extract_ports():
    assert pb_main.extract_ports("127.0.0.1:8789->127.0.0.1:39050") == [
        "8789",
        "39050",
    ]
    assert pb_main.extract_ports("[::1]:9000->[::1]:9001") == ["9000", "9001"]
    assert pb_main.extract_ports("*:3390") == ["3390"]
    assert pb_main.extract_ports("localhost:service") == []
    assert pb_main.extract_ports("") == []


def test_list_all_processes(patched_lsof):
    processes = pb_main.list_processes()
    by_name = {name: (key, ports) for key, ports in processes.items() for name in [key[1]]}
    assert set(by_name) == {"brave", "NetworkManager", "Google Chrome", "proc"}
    assert by_name["brave"][0][0] == "testuser-1000"
    assert set(by_name["brave"][1]) == {"80", "8080"}
    assert set(by_name["proc"][1]) == {"any"}
    assert by_name["NetworkManager"][0][0] == "testuser-0"


def test_port_filter_is_exact(patched_lsof):
    processes = pb_main.list_processes(port=80)
    assert len(processes) == 1
    ports = next(iter(processes.values()))
    assert set(ports) == {"80"}


def test_port_filter_substring_is_not_matched(patched_lsof):
    processes = pb_main.list_processes(port=80)
    assert all("8080" not in ports for ports in processes.values())


def test_name_filter_matches_resolved_process_name(patched_lsof):
    processes = pb_main.list_processes(process_name="networkmanager")
    keys = list(processes.keys())
    assert len(keys) == 1
    assert keys[0][1] == "NetworkManager"
    assert keys[0][2] == "200"


def test_enabling_sudo_prefixes_lsof(patched_lsof):
    pb_main.list_processes(elevated=True)
    assert patched_lsof[0][:2] == ["sudo", "lsof"]


def test_missing_lsof_reports_friendly_error(monkeypatch, capsys):
    def boom(command, *args, **kwargs):
        raise FileNotFoundError(2, "No such file or directory", "lsof")

    monkeypatch.setattr(subprocess, "check_output", boom)
    assert pb_main.list_processes() == {}
    assert "lsof" in capsys.readouterr().err


def test_kill_does_not_use_sudo_for_own_processes(patched_lsof, monkeypatch):
    run_calls = []
    monkeypatch.setattr(
        subprocess, "run", lambda command, **kwargs: run_calls.append(list(command))
    )
    monkeypatch.setattr(os, "geteuid", lambda: 1000)
    monkeypatch.setattr(pb_main, "get_current_user", lambda: "testuser-1000")
    killed = pb_main.kill_processes("brave")
    assert run_calls == [["kill", "-9", "100"]]
    assert len(killed) == 1


def test_kill_uses_sudo_for_other_users_processes(patched_lsof, monkeypatch):
    run_calls = []
    monkeypatch.setattr(
        subprocess, "run", lambda command, **kwargs: run_calls.append(list(command))
    )
    monkeypatch.setattr(os, "geteuid", lambda: 1000)
    monkeypatch.setattr(pb_main, "get_current_user", lambda: "testuser-1000")
    killed = pb_main.kill_processes("networkmanager")
    assert run_calls == [["sudo", "kill", "-9", "200"]]
    assert len(killed) == 1


def test_kill_failure_is_reported_and_excluded(patched_lsof, monkeypatch, capsys):
    def failing_run(command, check=False):
        raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr(subprocess, "run", failing_run)
    monkeypatch.setattr(os, "geteuid", lambda: 1000)
    monkeypatch.setattr(pb_main, "get_current_user", lambda: "testuser-1000")
    killed = pb_main.kill_processes("brave")
    assert killed == []
    assert "Failed to kill brave" in capsys.readouterr().out


def test_kill_summary_table_renders(patched_lsof, monkeypatch, capsys):
    monkeypatch.setattr(subprocess, "run", lambda command, **kwargs: None)
    monkeypatch.setattr(os, "geteuid", lambda: 1000)
    monkeypatch.setattr(pb_main, "get_current_user", lambda: "testuser-1000")
    monkeypatch.setattr(sys, "argv", ["pb", "kill", "-n", "networkmanager"])
    pb_main.main()
    output = capsys.readouterr().out
    assert "Summary of actions:" in output
    assert "USER" in output
    assert "NAME" in output
    assert "NetworkManager" in output
    assert "testuser-0" in output


def test_list_table_renders(patched_lsof, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["pb", "list"])
    pb_main.main()
    output = capsys.readouterr().out
    assert "USER" in output
    assert "brave" in output
    assert "NetworkManager" in output


def test_table_sort_key_ordering():
    rows = [["other", "x"], ["root", "y"], ["me", "z"]]
    rows.sort(key=lambda row: pb_main.table_sort_key(row, "me"))
    assert [row[0] for row in rows] == ["root", "me", "other"]


def test_get_current_user_falls_back_to_passwd(monkeypatch):
    def raise_key_error():
        raise KeyError("no environment user")

    monkeypatch.setattr(pb_main.getpass, "getuser", raise_key_error)
    monkeypatch.setattr(os, "getuid", lambda: 1000)
    monkeypatch.setattr(
        pb_main.pwd, "getpwuid", lambda uid: SimpleNamespace(pw_name="fallback")
    )
    assert pb_main.get_current_user() == "fallback"

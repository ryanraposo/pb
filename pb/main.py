import argparse
import getpass
import os
import pwd
import subprocess
import sys
from collections import defaultdict
from functools import lru_cache

from tabulate import tabulate
from termcolor import colored

HEADERS = ["USER", "NAME", "PID", "PORTS", "COMMAND"]


def get_current_user():
    try:
        return getpass.getuser()
    except (KeyError, OSError):
        pass
    try:
        return pwd.getpwuid(os.getuid()).pw_name
    except KeyError:
        return "unknown"


def resolve_user(uid):
    if uid is None:
        return "unknown"
    try:
        return pwd.getpwuid(int(uid)).pw_name
    except (KeyError, ValueError):
        return uid


def parse_lsof_output(output):
    records = []
    current = None
    for line in output.splitlines():
        if not line:
            continue
        field, value = line[0], line[1:]
        if field == "p":
            current = None
            if value.isdigit():
                current = {
                    "pid": value,
                    "uid": None,
                    "command": "",
                    "connections": [],
                }
                records.append(current)
        elif current is not None:
            if field == "c":
                current["command"] = value
            elif field == "u":
                current["uid"] = value
            elif field == "n":
                current["connections"].append(value)
    return records


def extract_ports(connection):
    ports = []
    for endpoint in (connection or "").split("->"):
        port = endpoint.rsplit(":", 1)[-1]
        if port.isdigit():
            ports.append(port)
    return ports


@lru_cache(maxsize=8192)
def get_process_name(pid):
    try:
        return subprocess.check_output(
            ["ps", "-p", pid, "-o", "comm="], text=True
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


@lru_cache(maxsize=8192)
def get_command_path(pid):
    try:
        args = subprocess.check_output(
            ["ps", "-p", pid, "-o", "args="], text=True
        ).strip().split()
        return args[0] if args else "unknown"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def list_processes(process_name=None, port=None, elevated=False):
    command = ["lsof", "-i", "-P", "-n", "-F", "pcun"]
    if elevated:
        command = ["sudo"] + command
    try:
        output = subprocess.check_output(command, text=True)
    except subprocess.CalledProcessError:
        return {}
    except FileNotFoundError:
        print(
            "Error: 'lsof' is not installed or not on your PATH.",
            file=sys.stderr,
        )
        return {}

    processes = defaultdict(list)
    for record in parse_lsof_output(output):
        pid = record["pid"]
        proc_name = get_process_name(pid)
        if process_name and process_name.lower() not in proc_name.lower():
            continue
        ports = []
        for connection in record["connections"]:
            ports.extend(extract_ports(connection))
        if port is not None:
            ports = [candidate for candidate in ports if candidate == str(port)]
            if not ports:
                continue
        ports = ports or ["any"]
        user = resolve_user(record["uid"])
        command_path = get_command_path(pid)
        processes[(user, proc_name, pid, command_path)].extend(ports)
    return processes


def kill_processes(process_name, port=None, elevated=False):
    processes = list_processes(process_name, port, elevated)
    current_user = get_current_user()
    killed = []
    for (user, proc_name, pid, command_path), ports in processes.items():
        display_ports = ", ".join(sorted(set(ports)))
        kill_command = ["kill", "-9", pid]
        if os.geteuid() != 0 and user != current_user:
            kill_command = ["sudo"] + kill_command
        try:
            subprocess.run(kill_command, check=True)
        except subprocess.CalledProcessError:
            print(
                f"Failed to kill {proc_name} with PID {pid} (USER: {user}) "
                f"on ports {display_ports} (COMMAND: {command_path})"
            )
            continue
        killed.append((user, proc_name, pid, command_path, ports))
        print(
            f"Killed {proc_name} with PID {pid} (USER: {user}) "
            f"on ports {display_ports} (COMMAND: {command_path})"
        )
    return killed


def table_sort_key(row, current_user):
    user = row[0]
    if user == "root":
        return (0, user)
    if user == current_user:
        return (1, user)
    return (2, user)


def color_for_user(user, current_user):
    if user == "root":
        return "red"
    if user == current_user:
        return "green"
    return "blue"


def print_process_table(rows, current_user, tablefmt="pretty", maxcolwidths=None):
    rows.sort(key=lambda row: table_sort_key(row, current_user))
    colored_rows = [
        [colored(cell, color_for_user(row[0], current_user)) for cell in row]
        for row in rows
    ]
    print(
        tabulate(
            colored_rows,
            HEADERS,
            tablefmt=tablefmt,
            stralign="left",
            maxcolwidths=maxcolwidths,
        )
    )


def main():
    parser = argparse.ArgumentParser(description="Process management tool")
    subparsers = parser.add_subparsers(dest="command")

    list_parser = subparsers.add_parser("list", help="List processes")
    list_parser.add_argument("-n", "--name", help="Process name")
    list_parser.add_argument("-p", "--port", type=int, help="Port number")
    list_parser.add_argument(
        "--all", action="store_true", help="List all processes with sudo"
    )

    kill_parser = subparsers.add_parser("kill", help="Kill processes")
    kill_parser.add_argument("-n", "--name", required=True, help="Process name")
    kill_parser.add_argument("-p", "--port", type=int, help="Port number")
    kill_parser.add_argument(
        "--all", action="store_true", help="Kill all matching processes with sudo"
    )

    args = parser.parse_args()
    current_user = get_current_user()

    if args.command == "list":
        processes = list_processes(args.name, port=args.port, elevated=args.all)
        if processes:
            table = [
                [user, proc_name, pid, ", ".join(sorted(set(ports))), command_path]
                for (user, proc_name, pid, command_path), ports in processes.items()
            ]
            print_process_table(
                table, current_user, maxcolwidths=[None, 30, None, None, None]
            )
            if not args.all:
                print(
                    "\nNote: Some processes may not be listed without using "
                    "the --all flag for elevated privileges."
                )
        else:
            name_display = args.name if args.name else "ANY"
            port_display = args.port if args.port else "ANY"
            print(
                f"\nNo processes found matching name '{name_display}' "
                f"and port '{port_display}'."
            )

    elif args.command == "kill":
        killed_processes = kill_processes(args.name, args.port, elevated=args.all)
        if killed_processes:
            print("\nSummary of actions:")
            table = [
                [user, proc_name, pid, ", ".join(sorted(set(ports))), command_path]
                for (
                    user,
                    proc_name,
                    pid,
                    command_path,
                    ports,
                ) in killed_processes
            ]
            print_process_table(
                table,
                current_user,
                tablefmt="grid",
                maxcolwidths=[None, 30, None, None, None],
            )
        else:
            name_display = args.name if args.name else "ANY"
            port_display = args.port if args.port else "ANY"
            print(
                f"\nNo processes found matching name '{name_display}' "
                f"and port '{port_display}' to kill."
            )

    else:
        parser.print_help()

    print("\n")


if __name__ == "__main__":
    main()

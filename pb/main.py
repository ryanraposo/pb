import subprocess
import argparse
import os
from collections import defaultdict
from tabulate import tabulate
from termcolor import colored


def list_processes(process_name=None, port=None, elevated=False):
    try:
        # Prepare the command to execute lsof
        command = "sudo lsof -i -P -n" if elevated else "lsof -i -P -n"
        result = subprocess.check_output(command, shell=True, text=True)
        lines = result.strip().split("\n")
        processes = defaultdict(list)

        for line in lines[1:]:  # Skip the header line
            if not process_name or process_name.lower() in line.lower():
                parts = line.split()
                user = parts[2]
                pid = parts[1]
                proc_name = get_process_name(pid)
                connection = parts[8] if len(parts) > 8 else "any port"
                command = get_command_path(pid)
                if port is None or f":{port}" in connection:
                    port_info = (
                        connection.split(":")[-1] if ":" in connection else "any port"
                    )
                    processes[(user, proc_name, pid, command)].append(port_info)

        return processes

    except subprocess.CalledProcessError:
        return {}


def get_process_name(pid):
    try:
        # Get the process name using ps
        command = f"ps -p {pid} -o comm="
        result = subprocess.check_output(command, shell=True, text=True).strip()
        return result
    except subprocess.CalledProcessError:
        return "unknown"


def get_command_path(pid):
    try:
        # Get the full command used to start the process, including the path
        command = f"ps -p {pid} -o args="
        result = (
            subprocess.check_output(command, shell=True, text=True)
            .strip()
            .split(" ")[0]
        )
        return result
    except subprocess.CalledProcessError:
        return "unknown"


def kill_processes(process_name, port=None, elevated=False):
    processes = list_processes(process_name, port, elevated=elevated)
    killed_processes = []
    for (user, proc_name, pid, command_name), ports in processes.items():
        try:
            kill_command = (
                ["sudo", "kill", "-9", pid]
                if os.geteuid() != 0
                else ["kill", "-9", pid]
            )
            subprocess.run(kill_command, check=True)
            killed_processes.append((user, proc_name, pid, command_name, ports))
            print(
                f"Killed {proc_name} with PID {pid} (USER: {user}) on ports {', '.join(ports)} (COMMAND: {command_name})"
            )
        except subprocess.CalledProcessError:
            print(
                f"Failed to kill {proc_name} with PID {pid} (USER: {user}) on ports {', '.join(ports)} (COMMAND: {command_name})"
            )
    return killed_processes


def main():
    parser = argparse.ArgumentParser(description="Process management tool")
    subparsers = parser.add_subparsers(dest="command")

    # List command
    list_parser = subparsers.add_parser("list", help="List processes")
    list_parser.add_argument("-n", "--name", help="Process name")
    list_parser.add_argument("-p", "--port", type=int, help="Port number")
    list_parser.add_argument(
        "--all", action="store_true", help="List all processes with sudo"
    )

    # Kill command
    kill_parser = subparsers.add_parser("kill", help="Kill processes")
    kill_parser.add_argument("-n", "--name", required=True, help="Process name")
    kill_parser.add_argument("-p", "--port", type=int, help="Port number")
    kill_parser.add_argument(
        "--all", action="store_true", help="Kill all processes with sudo"
    )

    args = parser.parse_args()

    if args.command == "list":
        processes = list_processes(args.name, port=args.port, elevated=args.all)
        if processes:
            headers = ["USER", "NAME", "PID", "PORTS", "COMMAND"]
            table = []
            for (user, proc_name, pid, command), ports in processes.items():
                unique_ports = ", ".join(sorted(set(ports)))
                table.append([user, proc_name, pid, unique_ports, command])

            # Custom sort: root first, then current user, then others
            current_user = os.getlogin()

            def custom_sort(row):
                user = row[0]
                if user == "root":
                    return (0, user)
                elif user == current_user:
                    return (1, user)
                else:
                    return (2, user)

            table.sort(key=custom_sort)

            colored_table = []
            for row in table:
                user = row[0]
                color = (
                    "green"
                    if user == current_user
                    else "red" if user == "root" else "blue"
                )
                colored_row = [colored(col, color) for col in row]
                colored_table.append(colored_row)

            print(
                tabulate(
                    colored_table,
                    headers,
                    tablefmt="pretty",
                    stralign="left",
                    maxcolwidths=[None, 30, None, None, None],
                )
            )
            if not args.all:
                print(
                    "\nNote: Some processes may not be listed without using the --all flag for elevated privileges."
                )
        else:
            name_display = args.name if args.name else "ANY"
            port_display = args.port if args.port else "ANY"
            print(
                f"\nNo processes found matching name '{name_display}' and port '{port_display}'."
            )

    elif args.command == "kill":
        killed_processes = kill_processes(args.name, args.port, elevated=args.all)
        if killed_processes:
            print("\nSummary of actions:")
            headers = ["NAME", "USER", "PID", "COMMAND", "PORTS"]
            table = []
            for (user, proc_name, pid, command), ports in killed_processes:
                unique_ports = ", ".join(sorted(set(ports)))
                table.append([user, proc_name, pid, command, unique_ports])

            table.sort(key=custom_sort)

            colored_table = []
            for row in table:
                user = row[0]
                color = (
                    "green"
                    if user == os.getlogin()
                    else "red" if user == "root" else "blue"
                )
                colored_row = [colored(col, color) for col in row]
                colored_table.append(colored_row)

            print(
                tabulate(
                    colored_table,
                    headers,
                    tablefmt="grid",
                    stralign="left",
                    maxcolwidths=[30, 15, None, None, None],
                )
            )
        else:
            name_display = args.name if args.name else "ANY"
            port_display = args.port if args.port else "ANY"
            print(
                f"\nNo processes found matching name '{name_display}' and port '{port_display}' to kill."
            )

    else:
        parser.print_help()

    print("\n")


if __name__ == "__main__":
    main()

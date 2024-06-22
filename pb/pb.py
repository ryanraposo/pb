import subprocess
import argparse
import sys

def list_processes(process_name, port=None):
    try:
        # Execute the lsof command and filter by process name
        command = f"lsof -i -P -n | grep {process_name}"
        result = subprocess.check_output(command, shell=True, text=True)
        lines = result.strip().split('\n')
        processes = []

        for line in lines:
            parts = line.split()
            if len(parts) < 9:
                continue
            proc_name, pid, connection = parts[0], parts[1], parts[8]
            if port is None or f":{port}" in connection:
                processes.append((proc_name, pid, connection))

        return processes

    except subprocess.CalledProcessError:
        return []

def kill_processes(process_name, port=None):
    processes = list_processes(process_name, port)
    for proc_name, pid, connection in processes:
        try:
            subprocess.run(['kill', '-9', pid], check=True)
            print(f"Killed {proc_name} with PID {pid} on {connection}")
        except subprocess.CalledProcessError:
            print(f"Failed to kill {proc_name} with PID {pid} on {connection}")

def main():
    parser = argparse.ArgumentParser(description="Ppb")
    subparsers = parser.add_subparsers(dest='command')

    # List command
    list_parser = subparsers.add_parser('list', help='List processes')
    list_parser.add_argument('-n', '--name', required=True, help='Process name')
    list_parser.add_argument('-p', '--port', type=int, help='Port number')

    # Kill command
    kill_parser = subparsers.add_parser('kill', help='Kill processes')
    kill_parser.add_argument('-n', '--name', required=True, help='Process name')
    kill_parser.add_argument('-p', '--port', type=int, help='Port number')

    args = parser.parse_args()

    if args.command == 'list':
        processes = list_processes(args.name, args.port)
        for proc_name, pid, connection in processes:
            print(f"{proc_name} {pid} {connection}")

    elif args.command == 'kill':
        kill_processes(args.name, args.port)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()

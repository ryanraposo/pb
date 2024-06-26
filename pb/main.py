import subprocess
import argparse
from collections import defaultdict

def list_processes(process_name=None, port=None):
    try:
        # Prepare the command to execute lsof
        command = "lsof -i -P -n"
        result = subprocess.check_output(command, shell=True, text=True)
        lines = result.strip().split('\n')
        processes = defaultdict(list)

        for line in lines[1:]:  # Skip the header line
            if not process_name or process_name.lower() in line.lower():
                parts = line.split()
                proc_name = parts[0]
                pid = parts[1]
                connection = parts[8] if len(parts) > 8 else "any port"
                if port is None or f":{port}" in connection:
                    port_info = connection.split(':')[-1] if ':' in connection else "any port"
                    processes[(proc_name, pid)].append(port_info)

        return processes

    except subprocess.CalledProcessError as e:
        print(e)
        return {}

def kill_processes(process_name, port=None):
    processes = list_processes(process_name, port)
    killed_processes = []
    for (proc_name, pid), ports in processes.items():
        try:
            kill_command = ['kill', '-9', pid]
            subprocess.run(kill_command, check=True)
            killed_processes.append((proc_name, pid, ports))
            print(f"Killed {proc_name} with PID {pid} on ports {', '.join(ports)}")
        except subprocess.CalledProcessError:
            print(f"Failed to kill {proc_name} with PID {pid} on ports {', '.join(ports)}")
    return killed_processes

def main():
    parser = argparse.ArgumentParser(description="Process management tool")
    subparsers = parser.add_subparsers(dest='command')

    # List command
    list_parser = subparsers.add_parser('list', help='List processes')
    list_parser.add_argument('-n', '--name', help='Process name')
    list_parser.add_argument('-p', '--port', type=int, help='Port number')

    # Kill command
    kill_parser = subparsers.add_parser('kill', help='Kill processes')
    kill_parser.add_argument('-n', '--name', required=True, help='Process name')
    kill_parser.add_argument('-p', '--port', type=int, help='Port number')

    args = parser.parse_args()

    if args.command == 'list':
        processes = list_processes(args.name, port=args.port)
        if processes:
            print("\nNAME PID [PORTS]\n-----------------")
            for (proc_name, pid), ports in processes.items():
                unique_ports = ', '.join(sorted(set(ports)))
                print(f"{proc_name} {pid} [{unique_ports}]")  # Square brackets around ports
        else:
            print(f"\nNo processes found matching name '{args.name}' and port '{args.port}'.")

    elif args.command == 'kill':
        killed_processes = kill_processes(args.name, args.port)
        if killed_processes:
            print("\nSummary of actions:")
            for (proc_name, pid), ports in killed_processes:
                unique_ports = ', '.join(sorted(set(ports)))
                print(f"\nKilled {proc_name} with PID {pid} on ports [{unique_ports}]")  # Square brackets around ports
        else:
            print(f"\nNo processes found matching name '{args.name}' and port '{args.port}' to kill.")

    else:
        parser.print_help()

    print("\n")

if __name__ == "__main__":
    main()

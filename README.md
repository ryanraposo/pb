# procboss

Use `pb` to list or kill processes by name or port in Unix-like environments.

![screenshot](https://raw.githubusercontent.com/ryanraposo/pb/main/screenshot.png)

## Features

- List processes by name and/or port number: `pb list -n node`
- Kill processes by name and/or port number: `pb kill -p 3001`
- Option to run commands with elevated privileges: `pb list --all`
- Automatically elevates `kill` permissions when necessary

## Installation

Install `procboss` from PyPI using pip:

```sh
pip install procboss
```

## Usage

### List Processes

To list processes, use the `list` command. You can filter processes by name or port number. To list all processes with elevated privileges, use the `--all` flag.

```sh
pb list [options]
```

#### Options

- `-n, --name NAME`: Filter by process name (optional).
- `-p, --port PORT`: Filter by port number (optional).
- `--all`: List all processes with sudo (optional).

#### Examples

List all processes:

```sh
pb list
```

List processes by name:

```sh
pb list -n <process_name>
```

List processes by port:

```sh
pb list -p <port_number>
```

List all processes with elevated privileges:

```sh
pb list --all
```

### Kill Processes

To kill processes, use the `kill` command. You must specify the process name, and you can optionally filter by port number. To kill all matching processes with elevated privileges, use the `--all` flag.

```sh
pb kill [options]
```

#### Options

- `-n, --name NAME`: **Required**. Specify the process name to kill.
- `-p, --port PORT`: Filter by port number (optional).
- `--all`: Kill all matching processes with sudo (optional).

#### Examples

Kill processes by name:

```sh
pb kill -n <process_name>
```

Kill processes by name and port:

```sh
pb kill -n <process_name> -p <port_number>
```

Kill all matching processes with elevated privileges:

```sh
pb kill -n <process_name> --all
```

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgements

This tool uses `lsof` and `ps` commands to gather process information and `tabulate` to format the output.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes. Keep it simple.

## Contact

For any questions or issues, please open an issue on the [GitHub repository](https://github.com/ryanraposo/pb).

---

**Note:** Running commands with `--all` may prompt for your password depending on your system configuration.

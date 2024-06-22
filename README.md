# pb

`pb` is a process management tool that lists or kills processes by name and port.

## Installation

To install `pb`, run:

```sh
pip install .
```

## Usage

### List Processes

To list processes by name and optionally by port:

```sh
pb list -n <process name> [-p <port>]
```

#### Examples

```sh
pb list -n nginx
pb list -n nginx -p 80
```

### Kill Processes

To kill processes by name and optionally by port:

```sh
pb kill -n <process name> [-p <port>]
```

#### Examples

```sh
pb kill -n nginx
pb kill -n nginx -p 80
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE.md) file for details.

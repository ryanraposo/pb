# pb

`pb` is a process management tool that lists or kills processes by name and port.

## Installation

To install `pb`, run:

```sh
pip install procboss
```

## Usage

### List Processes

To list processes by name and optionally by port:

```sh
pb list -n <process name> [-p <port>]
```

#### Examples

```sh
pb list -n code
sudo pb list -n code
```

### Kill Processes

To kill processes by name and optionally by port:

```sh
pb kill -n <process name> [-p <port>]
```

#### Examples

```sh
pb kill -n code
sudo pb kill -n code
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE.md) file for details.

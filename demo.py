import os
from termcolor import colored
from tabulate import tabulate


def main():
    headers = ["USER", "NAME", "PID", "PORTS", "COMMAND"]
    table = [
        ["root", "NetworkManager", "6898", "873, 22", "/usr/sbin/NetworkManager"],
        ["root", "cupsd", "46815", "515", "/usr/sbin/cupsd"],
        ["ryan", "brave", "10339", "63342, 45100", "/usr/local/bin/brave"],
        ["ryan", "brave", "10378", "8080, 5432", "/usr/local/bin/brave"],
        ["ryan", "chrome", "14573", "33389, 4861", "/usr/bin/google-chrome"],
        ["ryan", "chrome", "14921", "8443, 9999", "/usr/bin/google-chrome"],
        ["ryan", "code", "31312", "3000", "/usr/share/code/bin/code"],
        [
            "avahi",
            "avahi-daemon",
            "1200",
            "4111, 59100, 8654",
            "/usr/sbin/avahi-daemon",
        ],
        ["cups-browsed", "cups-browsed", "46820", "651", "/usr/sbin/cups-browsed"],
        ["ollama", "ollama", "1959", "19876", "/usr/local/bin/ollama"],
        [
            "systemd-resolve",
            "systemd-resolve",
            "1089",
            "53",
            "/lib/systemd/systemd-resolved",
        ],
    ]

    current_user = os.getlogin()

    def get_color(user):
        if user == "root":
            return "red"
        elif user == current_user:
            return "green"
        else:
            return "blue"

    colored_table = []
    for row in table:
        user = row[0]
        color = get_color(user)
        colored_row = [colored(col, color) for col in row]
        colored_table.append(colored_row)

    print(tabulate(colored_table, headers, tablefmt="pretty", stralign="left"))


if __name__ == "__main__":
    main()

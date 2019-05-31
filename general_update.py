#!/usr/bin/env python3

"""
A simple program updating all package managers supported.

It searches for different package management tools like apt,
snap and pip, shows you whether there is something to update and if so asks
you whether to update these.
"""


from __future__ import print_function
from collections import namedtuple


Packager = namedtuple("Packager", "command update_commands upgrade_commands")


def __get_updatable(packager, update_output):
    if packager == "apt":
        packagelist = list(map(lambda line: line.partition('/')[0],
                               update_output.splitlines()))
        del packagelist[0]
    elif packager == "snap":
        packagelist = list(map(lambda line: line.partition(' ')[0],
                               update_output.splitlines()))
        del packagelist[0]

    elif packager in ("pip2", "pip3"):
        packagelist = list(map(lambda line: line.partition(' ')[0],
                               update_output.splitlines()))
        del packagelist[0:2]
    else:
        print("The packager " + packager + " is not supported.")
        packagelist = []
    return packagelist


PACKAGER = [
    Packager(
        "apt",
        [
            ["sudo", "apt", "update"],
            ["apt", "list", "--upgradable"]
        ], [
            ["sudo", "apt", "-y", "upgrade"],
            ["sudo", "apt", "dist-upgrade"],
            ["sudo", "apt", "autoremove"],
            ["sudo", "apt", "autoclean"]
        ]),
    Packager(
        "snap",
        [["snap", "refresh", "--list"]],
        [["sudo", "snap", "refresh"]]),
    # Integrate pip2 check?
    Packager(
        "pip2",
        [["pip2", "list", "--outdated", "--not-required"]],
        [["sudo", "-H", "pipdate"]]),
    # Integrate pip3 check?
    Packager(
        "pip3",
        [["pip3", "list", "--outdated", "--not-required"]],
        [["sudo", "-H", "pipdate3"]]),
]


def command_exists(command):
    """Check whether the given command exists and can be executed."""
    from subprocess import getstatusoutput
    return getstatusoutput("which " + command)[0] == 0


def print_error(message):
    """Print an error message to the console."""
    from sys import stderr
    print("\033[1;31;40m " + message + "\033[0;37;40m", file=stderr)


def print_emph(message):
    """Print an info message easy to recognize for the user."""
    print("\033[1;32;40m " + message + "\033[0;37;40m")


def execute(command, need_output):
    """
    Execute a command.

    param need_output: If True the output is returned otherwise shown on the
    console.
    """
    from subprocess import PIPE, Popen
    if command_exists(command[0]):
        if need_output:
            process = Popen(command, stdout=PIPE, stderr=PIPE)
        else:
            process = Popen(command, stderr=PIPE)
        output, err = process.communicate()
        if process.returncode != 0:
            print_error(" ".join(command) + " failed.")
            print_error(err.decode())
        command_result = (output, process.returncode)
    else:
        print_error("The command " + command[0] + " does not exist.")
        command_result = None
    return command_result


def try_update_packager(packager):
    """Ask whether to update the given package manager and eventually do so."""
    upgrade = None
    while upgrade is None:
        choice = input("Would you like to update? [y/N]")
        if choice == "y":
            upgrade = True
        elif choice in ("n", ""):
            upgrade = False
    if upgrade:
        for upgrade_command in packager.upgrade_commands:
            execute(upgrade_command, False)


def upgrade_package_manager():
    """Search for all known package managers and updates their packages."""
    for packager in PACKAGER:
        if command_exists(packager.command):
            print("Checking " + packager.command)
            for update_command in packager.update_commands:
                output, returncode = execute(update_command, True)
            if returncode == 0:
                # print(err)
                packagelist \
                    = __get_updatable(packager.command, output.decode())
                if packagelist == []:
                    print_emph("All packages are up to date.")
                else:
                    print_emph(str(len(packagelist)) + " packages to update: "
                               + " ".join(packagelist))
                    try_update_packager(packager)


def count_updatable_packages(avoid_sudo):
    """Count all updatable packages."""
    updatable_packages = []
    for packager in PACKAGER:
        if command_exists(packager.command):
            for update_command in packager.update_commands:
                if not (avoid_sudo and update_command[0] == "sudo"):
                    output, returncode = execute(update_command, True)
            if returncode == 0:
                packagelist = __get_updatable(
                    packager.command, output.decode())
                if packagelist != []:
                    updatable_packages.append(
                        (packager.command, len(packagelist)))
            else:
                updatable_packages.append((packager.command, "⛒"))
    return updatable_packages


def main():
    """Parse command line arguments and execute appropriate action."""
    from argparse import ArgumentParser
    from signal import signal, SIGINT

    def signal_handler(_sig, _frame):
        print("generalUpdate got abborted by the user.")
        exit(0)
    signal(SIGINT, signal_handler)

    # TODO Add an option defining choices for selecting which package managers
    # to concern.
    parser = ArgumentParser("Manage updates of a bunch of package managers.")
    parser.add_argument("-c", "--count-updatable",
                        # nargs="?",
                        action="store_true",
                        help="Print the total number of updatable packages "
                             "for each registered package manager.")
    parser.add_argument("--allow-sudo",
                        # nargs="?",
                        action="store_true",
                        help="When -c is specified allow execution of sudo "
                             "commands. You may not want that if you only "
                             "want to know how many packages can be updated "
                             "without having sudo permissions. But you may "
                             "want to specify this option if the number of "
                             "updatable packages should be updated.")
    args = parser.parse_args()
    if args.count_updatable:
        updatable_packages = count_updatable_packages(not args.allow_sudo)
        print(" | ".join(
            map(lambda u: u[0] + ": " + str(u[1]), updatable_packages)))
    else:
        upgrade_package_manager()


if __name__ == "__main__":
    main()

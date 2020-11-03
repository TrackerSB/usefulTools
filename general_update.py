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
suppress_output = False # Suppress any output which goes beyond anything but the actual result


def __get_updatable(packager, update_output):
    if packager == "apt":
        packagelist = list(map(lambda line: line.partition('/')[0],
                               update_output.splitlines()))
        del packagelist[0]
    elif packager == "snap":
        packagelist = list(map(lambda line: line.partition(' ')[0],
                               update_output.splitlines()))
        if packagelist:
            del packagelist[0]

    elif packager in ("pip2", "pip3"):
        packagelist = list(map(lambda line: line.partition(' ')[0],
                               update_output.splitlines()))
        del packagelist[0:2]
    elif packager == "pacman":
        packagelist = list(map(lambda line: line.partition(' ')[0],
                               update_output.splitlines()))
    else:
        print_error("The packager " + packager + " is not supported.")
        packagelist = []
    return packagelist


# NOTE The last command of the update_command sequence mu<F4><F3>st return the list of updatable packages
# NOTE The last command must NOT require sudo privileges
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
        [["sudo", "pipdate"]]),
    # Integrate pip3 check?
    Packager(
        "pip3",
        [["pip3", "list", "--outdated", "--not-required"]],
        [["sudo", "pipdate3"]]),
    Packager(
        "pacman",
        [
            ["sudo", "pacman", "-Sy"],
            ["pacman", "-Qu"]
        ], [
            ["sudo", "pacman", "-Su", "--noconfirm"],
            ["sudo", "pacman", "-Sc", "--noconfirm"],
            ["sudo", "pacman", "-Rs", "$(pacman -Qqdt)", "--noconfirm"] # 2020-11-03: Requires cracklib
        ]),
]


def command_exists(command):
    """Check whether the given command exists and can be executed."""
    from subprocess import getstatusoutput
    return getstatusoutput("which " + command)[0] == 0


def _get_lines_indented(lines, indent):
    if isinstance(lines, str): # It's a single line
        return " "*indent + lines
    else:
        return " "*indent.join(lines)


def print_out(message, indent=0):
    """Print an info message easy to recognize for the user."""
    if not suppress_output:
        print("\033[1;37;40m" + _get_lines_indented(message, indent) + "\033[m")


def print_error(message, indent=0):
    """Print an error message to the console."""
    from sys import stderr
    if not suppress_output:
        print("\033[1;31;40m" + _get_lines_indented(message, indent) + "\033[m", file=stderr)


def print_emph(message, indent=0):
    """Print an info message easy to recognize for the user."""
    if not suppress_output:
        print("\033[1;32;40m" + _get_lines_indented(message, indent) + "\033[m")


def print_note(message, indent=0):
    """Print an debug message or a notice."""
    if not suppress_output:
        print("\033[1;30;40m" + _get_lines_indented(message, indent) + "\033[m")


def print_result(line):
    """Print output relating to actual results of this command"""
    print(line)


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
            print_error("'" + " ".join(command) + "' failed.", 2)
            print_error("Received error:", 2)
            error_output = err.decode()
            print_error(error_output if error_output else "None", 4)
            print_note("Received output:", 2)
            standard_output = output
            print_note(output if output else "None", 4)
        command_result = (output, process.returncode)
    else:
        print_error("The command '" + command[0] + "' does not exist.", 2)
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
            output, returncode = execute(upgrade_command, False)


def upgrade_package_manager():
    """Search for all known package managers and updates their packages."""
    for packager in PACKAGER:
        if command_exists(packager.command):
            print_out("Checking " + packager.command)
            for update_command in packager.update_commands:
                output, returncode = execute(update_command, True)
                if returncode != 0:
                    print_error("Could not update " + packager.command + " => Assume there is no package to update", 2)
                    break;
            if returncode == 0:
                packagelist \
                    = __get_updatable(packager.command, output.decode())
                if packagelist == []:
                    print_emph("All packages are up to date.", 2)
                else:
                    print_emph(str(len(packagelist)) + " packages to update: "
                               + " ".join(packagelist), 2)
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
                updatable_packages.append((packager.command, "❌"))
    return updatable_packages


def main():
    """Parse command line arguments and execute appropriate action."""
    from argparse import ArgumentParser
    from signal import signal, SIGINT

    def signal_handler(_sig, _frame):
        print_error("generalUpdate got abborted by the user.")
        exit(0)
    signal(SIGINT, signal_handler)

    # TODO Add an option defining choices for selecting which package managers
    # to concern.
    parser = ArgumentParser("Manage updates of a bunch of package managers.")
    parser.add_argument("-c", "--count-updatable",
                        # nargs="?",
                        action="store_true",
                        help="Print the total number of updatable packages "
                             "for each registered package manager. Any output "
                             "is disabled per default.")
    parser.add_argument("--enable-output",
                        action="store_true",
                        help="If specified enable error, warning and info "
                             "output.")
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
        global suppress_output
        suppress_output = not args.enable_output
        updatable_packages = count_updatable_packages(not args.allow_sudo)
        print_result(" | ".join(
            map(lambda u: u[0] + ": " + str(u[1]), updatable_packages)))
    else:
        upgrade_package_manager()


if __name__ == "__main__":
    main()

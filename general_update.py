"""
A simple program updating all package managers supported.

It searches for different package management tools like apt,
snap and pip, shows you whether there is something to update and if so asks
you whether to update these.
"""


from __future__ import print_function
from collections import namedtuple


Packager = namedtuple("Packager", "command update_command get_updateable \
        upgrade_commands")


PACKAGER = [
    Packager(
        "apt",
        ["apt", "update"],
        lambda output: (-1, "<list of packages>"),
        [
            ["apt", "upgrade"],
            ["apt", "dist-upgrade"],
            ["apt", "autoremove"],
            ["apt", "autoclean"]
        ]),
    Packager(
        "snap",
        ["snap", "refresh", "--list"],
        lambda output: (-1, "<list of packages>"),
        [
            ["snap", "refresh"]
        ]),
    Packager(
        "pip2",
        ["pip2", "list", "--outdated"],
        lambda output: (output.count("\n") - 2, output),
        [
            ["pip2", "--upgrade"]
        ]),
    Packager(
        "pip3",
        ["pip3", "list", "--outdated"],
        lambda output: (output.count("\n") - 2, output),
        [
            ["pip3", "--upgrade"]
        ])
]


def command_exists(command):
    """Check whether the given command exists and can be executed."""
    from subprocess import getstatusoutput
    return getstatusoutput("which " + command)[0] == 0


def try_update_packager(packager):
    """Ask whether to update the given package manager and eventually do so."""
    from subprocess import check_call
    update = None
    while update is None:
        choice = input("Would you like to update? [y/N]")
        if choice == "y":
            update = True
        elif choice == "n":
            update = False
    if update:
        for command in packager.upgrade_commands:
            check_call(["sudo"] + command)


def iterate_package_manager():
    """Search for all known package managers and updates their packages."""
    from subprocess import Popen, PIPE
    for packager in PACKAGER:
        if command_exists(packager.command):
            print("Checking " + packager.command)
            update_process = Popen(["sudo"] + packager.update_command,
                                   stdout=PIPE, stderr=PIPE)
            output, err = update_process.communicate()
            returncode = update_process.returncode
            if returncode == 0:
                print(err)
                num_updatable, updateables \
                    = packager.get_updateable(output.decode())
                if num_updatable <= 0:
                    print("All packages are up to date.")
                else:
                    print(str(num_updatable)
                          + " packages to update: " + updateables)
                    try_update_packager(packager)
            else:
                print(packager.command + " failed.")
                print(err)


if __name__ == "__main__":
    iterate_package_manager()

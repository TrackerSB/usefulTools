#!/usr/bin/env python3

"""
A simple program updating all package managers supported.

It searches for different package management tools like apt,
snap and pip, shows you whether there is something to update and if so asks
you whether to update these.
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Union, Tuple, Optional, Type, TypeVar

# Suppress any output which goes beyond anything but the actual result
_enable_console_output = True  # NOTE This value may be changed by user parameters


def _get_lines_indented(lines: Union[str, List[str]], indent: int) -> str:
    if isinstance(lines, str):  # It's a single line
        return " " * indent + lines
    else:
        return (" " * indent).join(lines)


def _print_error(message: Union[str, List[str]], indent: int = 0) -> None:
    """Print an error message to the console."""
    from sys import stderr
    if _enable_console_output:
        print("\033[1;91m" + _get_lines_indented(message, indent) + "\033[m", file=stderr)


def _print_warn(message: Union[str, List[str]], indent: int = 0) -> None:
    """Print an error message to the console."""
    from sys import stderr
    if _enable_console_output:
        print("\033[1;93m" + _get_lines_indented(message, indent) + "\033[m", file=stderr)


def _print_emph(message: Union[str, List[str]], indent: int = 0) -> None:
    """Print an info message easy to recognize for the user."""
    if _enable_console_output:
        print("\033[1;32m" + _get_lines_indented(message, indent) + "\033[m")


def _print_note(message: Union[str, List[str]], indent: int = 0) -> None:
    """Print an debug message or a notice."""
    if _enable_console_output:
        print("\033[1;37m" + _get_lines_indented(message, indent) + "\033[m")


def _print_info(message: Union[str, List[str]], indent: int = 0) -> None:
    """Print an info message easy to recognize for the user."""
    if _enable_console_output:
        print("\033[1;90m" + _get_lines_indented(message, indent) + "\033[m")


def _print_result(line: str) -> None:
    """Print output relating to actual results of this script or required for user interaction"""
    print(line)


def _command_exists(command):
    """Check whether the given command exists and can be executed."""
    from subprocess import getstatusoutput
    return getstatusoutput("which " + command)[0] == 0


def _execute(command: List[str], capture_stdout: bool, working_dir: Optional[Path] = None) \
        -> Tuple[Optional[str], int]:
    """
    Execute a command.

    param need_output: If True the stdout of the executed command is captured into a variable; otherwise it's printed
    on the console
    """
    from subprocess import DEVNULL, PIPE, Popen
    if capture_stdout:
        process = Popen(command, stdout=PIPE, stderr=PIPE, cwd=working_dir)
    else:
        if _enable_console_output:
            process = Popen(command, stderr=PIPE, cwd=working_dir)
        else:
            process = Popen(command, stdout=DEVNULL, stderr=PIPE, cwd=working_dir)
    std_out, std_err = process.communicate()
    output = std_out.decode() if std_out else "None"
    if process.returncode != 0:
        _print_error("'" + " ".join(command) + "' failed.", 2)
        _print_error("Received error:", 2)
        error_output = std_err.decode() if std_err else "None"
        _print_error(error_output, 4)
        _print_note("Received output:", 2)
        _print_note(output if output else "None", 4)
    command_result = (output, process.returncode)
    return command_result


class UpdatablePackageManager(ABC):
    @staticmethod
    @abstractmethod
    def get_pretty_name() -> str:
        pass

    @staticmethod
    @abstractmethod
    def is_available() -> bool:
        pass

    @staticmethod
    @abstractmethod
    def update_package_list() -> None:
        pass

    @staticmethod
    @abstractmethod
    def get_updatable_packages() -> List[str]:
        # NOTE This method must not execute any sudo commands
        pass

    @staticmethod
    @abstractmethod
    def upgrade_packages() -> None:
        pass


class Aptitude(UpdatablePackageManager):
    @staticmethod
    def get_pretty_name() -> str:
        return "Aptitude"

    @staticmethod
    def is_available() -> bool:
        return _command_exists("apt")

    @staticmethod
    def update_package_list() -> None:
        _execute(["sudo", "apt", "update"], True)

    @staticmethod
    def get_updatable_packages() -> List[str]:
        output, exit_code = _execute(["apt", "list", "--upgradable"], True)
        if exit_code == 0:
            package_list = list(map(lambda line: line.partition('/')[0], output.splitlines()))
            del package_list[0]
            return package_list
        else:
            return []

    @staticmethod
    def upgrade_packages() -> None:
        _execute(["sudo", "apt", "-y", "upgrade"], False)
        _execute(["sudo", "apt", "-y", "dist-upgrade"], False)
        _execute(["sudo", "apt", "-y", "autoremove"], False)
        _execute(["sudo", "apt", "-y", "autoclean"], False)


class ArchUserRepo(UpdatablePackageManager):
    from pathlib import Path
    from typing import Callable, Dict
    _aur_base_dir: Path = Path("/home/stefan/gitrepos/aurPackages")
    _T: TypeVar = TypeVar("_T")

    @staticmethod
    def get_pretty_name() -> str:
        return "AUR"

    @staticmethod
    def is_available() -> bool:
        return _command_exists("pacman") \
               and _command_exists("git") \
               and _command_exists("makepkg") \
               and ArchUserRepo._aur_base_dir.exists()

    @staticmethod
    def _is_git_dir(path: Path) -> bool:
        is_git_dir = False
        if path.is_dir():
            branch_name, exit_code = _execute(["git", "symbolic-ref", "--short", "HEAD"], True, path)
            if exit_code != 0:
                branch_name, exit_code = _execute(["git", "describe", "--tags", "--always"], True, path)
                if exit_code != 0:
                    _print_warn("Could not determine whether {} is a git directory".format(str(path.absolute())), 2)
            if branch_name:
                is_git_dir = True
        return is_git_dir

    @staticmethod
    def _iterate_git_dirs(root: Path, actions: Callable[[Path], _T]) -> Dict[Path, _T]:
        git_dir_results = {}
        if root.is_dir():
            for path in root.iterdir():
                if path.is_dir():
                    if ArchUserRepo._is_git_dir(path):
                        _print_info("Found git dir '{}'".format(str(path.absolute())))
                        git_dir_results[path] = actions(path)
                    else:
                        git_dir_sub_results = ArchUserRepo._iterate_git_dirs(path, actions)
                        git_dir_results.update(git_dir_sub_results)
        return git_dir_results

    @staticmethod
    def update_package_list() -> None:
        ArchUserRepo._iterate_git_dirs(ArchUserRepo._aur_base_dir,
                                       lambda p: _execute(["git", "fetch", "--all", "--prune"], False, p))

    @staticmethod
    def _get_updatable_git_repos() -> List[Path]:
        updatable_repos = []

        def _remember_if_has_updates(path: Path) -> None:
            # FIXME Do not ignore exit code
            # FIXME Check whether the up count is greater zero, i.e. whether the repo can be updated
            # FIXME Check whether there are any stashes etc.
            # FIXME Detect repos which have up to date history but whose package was not installed
            down_up_count, exit_code \
                = _execute(["git", "rev-list", "--count", "--left-right", "@{upstream}...HEAD"], True, path)
            down_count = down_up_count.split("\t", 1)[0]
            if int(down_count) > 0:
                updatable_repos.append(path)

        ArchUserRepo._iterate_git_dirs(ArchUserRepo._aur_base_dir, lambda p: _remember_if_has_updates(p))
        return updatable_repos

    @staticmethod
    def get_updatable_packages() -> List[str]:
        return list(map(lambda p: p.name, ArchUserRepo._get_updatable_git_repos()))

    @staticmethod
    def upgrade_packages() -> None:
        updatable_git_repos = ArchUserRepo._get_updatable_git_repos()
        for repo_path in updatable_git_repos:
            _execute(["git", "pull"], False, repo_path)
            _execute(["makepkg", "-sri", "--noconfirm"], False, repo_path)


class Pacman(UpdatablePackageManager):
    @staticmethod
    def get_pretty_name() -> str:
        return "Pacman"

    @staticmethod
    def is_available() -> bool:
        return _command_exists("pacman")

    @staticmethod
    def update_package_list() -> None:
        _execute(["sudo", "pacman", "-Syy"], False)

    @staticmethod
    def get_updatable_packages() -> List[str]:
        output, exit_code = _execute(["pacman", "-Quq"], True)
        if exit_code == 0:
            return output.splitlines()
        else:
            return []

    @staticmethod
    def upgrade_packages() -> None:
        _execute(["sudo", "pacman", "-Su", "--noconfirm"], False)
        _execute(["sudo", "pacman", "-Sc", "--noconfirm"], False)


#             ["sudo", "pacman", "-Rs", "$(pacman -Qqdt)", "--noconfirm"]  # 2020-11-03: Requires cracklib


class Python2(UpdatablePackageManager):
    @staticmethod
    def get_pretty_name() -> str:
        return "Python 2"

    @staticmethod
    def is_available() -> bool:
        return _command_exists("pip2")

    @staticmethod
    def update_package_list() -> None:
        _print_warn("Updating package list is not implemented yet", 2)

    @staticmethod
    def get_updatable_packages() -> List[str]:
        output, exit_code = _execute(["pip2", "list", "--outdated", "--not-required"], True)
        if exit_code == 0:
            package_list = list(map(lambda line: line.partition(' ')[0], output.splitlines()))
            del package_list[0:2]
            return package_list
        else:
            return []

    @staticmethod
    def upgrade_packages() -> None:
        _print_warn("Upgrading packages is not implemented yet", 2)


class Python3(UpdatablePackageManager):
    @staticmethod
    def get_pretty_name() -> str:
        return "Python 3"

    @staticmethod
    def is_available() -> bool:
        return _command_exists("pip3")

    @staticmethod
    def update_package_list() -> None:
        _print_warn("Updating package list is not implemented yet", 2)

    @staticmethod
    def get_updatable_packages() -> List[str]:
        output, exit_code = _execute(["pip3", "list", "--outdated", "--not-required"], True)
        if exit_code == 0:
            package_list = list(map(lambda line: line.partition(' ')[0], output.splitlines()))
            del package_list[0:2]
            return package_list
        else:
            return []

    @staticmethod
    def upgrade_packages() -> None:
        _print_warn("Upgrading packages is not implemented yet", 2)


class Snap(UpdatablePackageManager):
    @staticmethod
    def get_pretty_name() -> str:
        return "Snap"

    @staticmethod
    def is_available() -> bool:
        return _command_exists("snap")

    @staticmethod
    def update_package_list() -> None:
        # Not explicitly required since snap package lists are updated automatically
        # See https://snapcraft.io/docs/keeping-snaps-up-to-date
        pass

    @staticmethod
    def get_updatable_packages() -> List[str]:
        output, exit_code = _execute(["snap", "refresh", "--list"], True)
        if exit_code == 0:
            package_list = list(map(lambda line: line.partition(' ')[0], output.splitlines()))
            if package_list:
                del package_list[0]
            return package_list
        else:
            return []

    @staticmethod
    def upgrade_packages() -> None:
        _execute(["sudo", "snap", "refresh"], False)


_PACKAGE_MANAGERS: List[Type[UpdatablePackageManager]] = [
    Aptitude, ArchUserRepo, Pacman, Python2, Python3, Snap
]


def _upgrade_packages():
    for manager in _PACKAGE_MANAGERS:
        _print_result("Check '{}'".format(manager.get_pretty_name()))
        if manager.is_available():
            manager.update_package_list()
            updatable_packages = manager.get_updatable_packages()
            num_updatable_packages = len(updatable_packages)
            if num_updatable_packages > 0:
                _print_emph("Found {:d} updatable packages".format(num_updatable_packages), 2)
                _print_emph(" ".join(updatable_packages), 2)
                user_confirmed_upgrade = None
                while user_confirmed_upgrade is None:
                    choice = input("Would you like to update? [y/N]").lower()
                    if choice == "y":
                        user_confirmed_upgrade = True
                    elif choice in ("n", ""):
                        user_confirmed_upgrade = False
                if user_confirmed_upgrade:
                    manager.upgrade_packages()  # FIXME Enable on user confirmation
                else:
                    _print_info("Upgrade skipped", 2)
            else:
                _print_emph("All packages are up to date", 2)
        else:
            _print_info("'{}' is not installed".format(manager.get_pretty_name()), 2)


def _count_updatable_packages(update_package_lists: bool) -> List[Tuple[str, int]]:
    updatable_packages_per_manager = []
    for manager in _PACKAGE_MANAGERS:
        if manager.is_available():
            if update_package_lists:
                manager.update_package_list()
            num_updatable_packages = len(manager.get_updatable_packages())
            if num_updatable_packages > 0:
                updatable_packages_per_manager.append((manager.get_pretty_name(), num_updatable_packages))
    if not updatable_packages_per_manager:
        updatable_packages_per_manager.append(("No supported package manager found", -1))
    return updatable_packages_per_manager


def _main():
    from argparse import ArgumentParser
    from signal import signal, SIGINT

    def signal_handler(_sig, _frame):
        _print_error("generalUpdate got aborted by the user")
        exit(0)

    signal(SIGINT, signal_handler)

    # TODO Add an option for selecting which package managers to concern
    parser = ArgumentParser("Manage updates of a bunch of package managers.")
    parser.add_argument("-c", "--count-updatable",
                        # nargs="?",
                        action="store_true",
                        help="Print the total number of updatable packages for each registered package manager. Any "
                             "output is disabled per default.")
    parser.add_argument("--quiet",
                        action="store_true",
                        help="If specified disable error, warning and info output.")
    parser.add_argument("--allow-sudo",
                        # nargs="?",
                        action="store_true",
                        help="When -c is specified allow execution of sudo commands. You may not want that if you only "
                             "want to know how many packages can be updated without having sudo permissions. But you "
                             "may want to specify this option if the number of updatable packages should be updated.")
    args = parser.parse_args()
    global _enable_console_output
    _enable_console_output = not args.quiet
    if args.count_updatable:
        updatable_packages = _count_updatable_packages(args.allow_sudo)
        _print_result(" | ".join(map(lambda u: u[0] + ": " + str(u[1]), updatable_packages)))
    else:
        _upgrade_packages()


if __name__ == "__main__":
    _main()

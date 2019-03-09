#!/usr/bin/env python3


def print_error(message):
    """Print an error message to the console."""
    from sys import stderr
    print("\033[1;31;40m " + message + "\033[0;37;40m", file=stderr)


def get_pdf_content(path):
    from subprocess import PIPE, Popen
    process = Popen(["gs", "-dBATCH", "-dNOPAUSE", "-sDEVICE=txtwrite",
                     "-sOutputFile=-", path], stdout=PIPE, stderr=PIPE)
    output, err = process.communicate()
    if process.returncode != 0:
        print_error(" ".join(command) + " failed.")
        print_error(err.decode())
    return output


def count_words(content):
    frequencies = {}
    for line in [line.strip().split(b' ') for line in content.splitlines()]:
        for word in line:
            word = word.lower()
            if word:
                if word not in frequencies:
                    frequencies[word] = 0
                frequencies[word] += 1
    return frequencies


if __name__ == "__main__":
    from argparse import ArgumentParser
    from operator import itemgetter
    from signal import signal, SIGINT

    def signal_handler(sig, frame):
        print("word frequency analysis got abborted by the user.")
        exit(0)

    PARSER = ArgumentParser(description="Return the word frequencies of all "
                            "words in a PDF file")
    PARSER.add_argument("path", metavar="path", type=str, nargs=1,
                        help="The path of the pdf file to analyze.")

    ARGS = PARSER.parse_args()

    signal(SIGINT, signal_handler)
    content = get_pdf_content(ARGS.path[0])
    frequencies = count_words(content)
    for frequence in sorted(frequencies.items(), key=itemgetter(1)):
        print(frequence[0], ": ", frequence[1])

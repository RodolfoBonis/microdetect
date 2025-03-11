import argparse

from microdetect.utils.colors import BRIGHT, INFO, RESET


class ColoredVersionAction(argparse.Action):
    def __init__(
        self, option_strings, version=None, dest=None, default=argparse.SUPPRESS, help="show program's version number and exit"
    ):
        super().__init__(option_strings=option_strings, dest=dest, default=default, nargs=0, help=help)
        self.version = version

    def __call__(self, parser, namespace, values, option_string=None):
        version_text = f"{INFO}✨ MicroDetect {BRIGHT}{self.version}{RESET}"
        parser.exit(message=version_text + "\n")

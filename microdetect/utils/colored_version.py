import argparse

from microdetect.utils.colors import BRIGHT, INFO, RESET


class ColoredVersionAction(argparse.Action):
    def __init__(
        self, option_strings, version=None, dest=None, default=argparse.SUPPRESS, help="show program's version number and exit"
    ):
        super().__init__(option_strings=option_strings, dest=dest, default=default, nargs=0, help=help)
        self.version = version

    def __call__(self, parser, namespace, values, option_string=None):
        version_text = f"{INFO}✨ v{BRIGHT}{self.version}{RESET}"
        from microdetect.utils import get_logo_with_name_ascii

        parser.exit(message=get_logo_with_name_ascii(custom_text=version_text))

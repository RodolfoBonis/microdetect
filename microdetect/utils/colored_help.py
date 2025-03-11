from argparse import RawDescriptionHelpFormatter

from microdetect.utils.colors import BRIGHT, INFO, RESET, SUCCESS


class ColoredHelpFormatter(RawDescriptionHelpFormatter):
    def __init__(self, prog):
        super().__init__(prog, width=100)

    def start_section(self, heading):
        heading = f"{BRIGHT}{INFO}{heading}{RESET}"
        super().start_section(heading)

    def _format_action(self, action):
        result = super()._format_action(action)
        if action.dest == "help" or action.dest == "version":
            return result.replace("--help", f"{SUCCESS}--help{RESET}").replace("--version", f"{SUCCESS}--version{RESET}")
        return result

import argparse
import os
import textwrap

illegal_chars = [
    "@",
    ":",
    "*",
    "?",
    "!",
    '"',
    "'",
    "<",
    ">",
    "|",
    "&",
    "#",
    "%",
    "$",
    "~",
    "+",
    "=",
    "'",
    '"',
    "{",
    "}",
    "^",
]


class DescriptionWrappedNewlineFormatter(argparse.HelpFormatter):
    """
    An argparse formatter that:
        - preserves newlines (like argparse.RawDescriptionHelpFormatter),
        - removes leading indent,
        - applies reasonable text wrapping.

    Source: https://stackoverflow.com/a/64102901/79125
    """

    def _fill_text(self, text, width, indent):
        # Strip the indent from the original python definition that plagues most of us.
        text = textwrap.dedent(text)
        text = textwrap.indent(text, indent)  # Apply any requested indent.
        text = text.splitlines()  # Make a list of lines
        text = [textwrap.fill(line, width) for line in text]  # Wrap each line
        text = "\n".join(text)  # Join the lines again
        return text


class WrappedNewlineFormatter(DescriptionWrappedNewlineFormatter):
    """
    An argparse formatter that:
        - preserves newlines (like argparse.RawTextHelpFormatter),
        - removes leading indent and applies reasonable text wrapping,
        - applies to all help text (description, arguments, epilogue).
    """

    def _split_lines(self, text, width):
        # Allow multiline strings to have common leading indentation.
        text = textwrap.dedent(text)
        text = text.splitlines()
        lines = []
        for line in text:
            wrapped_lines = textwrap.fill(line, width).splitlines()
            lines.extend(subline for subline in wrapped_lines)
            if line:
                lines.append("")  # Preserve line breaks.
        return lines


def build_parser(formatter=WrappedNewlineFormatter):
    program_descripton = """
    =====================================\n\
    Illegal Character Checker v1.0

    steven.cucolo@natgeo.com
    May 2023

    USAGE:
    A script to find and report on all illegal 
    characters in a filesystem.
    
    Default list of illegal chars:
    @ , : * ? ! " ' < > | & # % $ ~ + = { } ^
    
    Add additional search characters with the -e flag.
    
    ======================================
    """

    # def formatter(params):
    #     formatter = argparse.HelpFormatter(max_help_position=72)
    #     return formatter

    # formatter = lambda prog: argparse.HelpFormatter(prog, max_help_position=52)

    parser = argparse.ArgumentParser(
        prog="illegal-character-check",
        description=program_descripton,
        # formatter_class=argparse.RawDescriptionHelpFormatter,
        formatter_class=formatter,
    )
    parser.add_argument(
        "-c",
        "--characters",
        action="store",
        # choices=illegal_chars,
        default=0,
        nargs="*",
        help=textwrap.fill("limit character search to specific values\n"),
        metavar="",
        required=False,
        type=check_list,
    )
    parser.add_argument(
        "-d",
        "--destination",
        default=os.getcwd(),
        help="output locaton for results of the search",
        metavar="<file path>",
        required=False,
        type=check_destination,
    )
    parser.add_argument(
        "-f",
        "--format",
        default=".txt",
        help="select file type for the results, defaults to a .txt file",
        metavar="<file type>",
        required=False,
        type=str,
    )
    parser.add_argument(
        "-p",
        "--path",
        default=None,
        help="required value: path to check against for illegal characters",
        metavar="<file path>",
        required=True,
        type=filesystempath,
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        default=False,
        help="Use flag to perform a recursive check on all directories and files in set --path",
        required=False,
    )
    parser.add_argument(
        "-w",
        "--whitespace",
        action="store_true",
        default=False,
        help="check for illegal whitespace characters in set path",
    )

    args = parser.parse_args()

    return args


def filesystempath(astring):
    if not os.path.exists(astring):
        raise argparse.ArgumentTypeError
    else:
        return os.path.join(astring)


def check_list(astring):
    chars = [x for x in astring]
    char_list = list(set(chars))  # remove duplicate characters

    for x in char_list:
        if x not in illegal_chars:
            raise argparse.ArgumentTypeError
        else:
            continue
    return astring


def check_destination(astring):
    dest = astring
    if os.path.exists(dest):
        return astring
    else:
        raise argparse.ArgumentTypeError


if __name__ == "__main__":
    # set_logger()
    build_parser(formatter=WrappedNewlineFormatter)

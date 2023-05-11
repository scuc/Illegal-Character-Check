#! /usr/bin/env python3

import logging
import os
import re
import sys
from collections import Counter
from pathlib import Path
from time import localtime, strftime

logger = logging.getLogger(__name__)


def check_set_path(args):
    """
    Check each path and look for any illegal characters or whitespace.
    """
    exitcode = 0
    date_start = str(strftime("%A, %d. %B %Y %I:%M%p", localtime()))

    start_msg = f"\n\
    ================================================================\n\
                    START CHECK: {date_start}\n\
    ================================================================\n\
   "
    write_to_file(start_msg=start_msg)

    path_total = {
        "char_limit_count": 0,
        "dir_count": 0,
        "ds_count": 0,
        "file_count": 0,
        "illegal_char_list": [],
        "illegal_dirname_total": 0,
        "illegal_filename_total": 0,
    }

    illegal_total = Counter({"illegalchar_count": 0, "whitespace_count": 0})

    # Note: have to treat recurive and non-recursive seperately because the
    # recursive method uses topdown=false, it will not work for only top-level scan.

    try:
        if args.recursive is not True:
            path_total, illegal_total = check_current_path(
                args, args.path, path_total, illegal_total
            )
            illegal_total = whitespace_check(args.path, illegal_total)
            summary = prepare_summary(path_total, illegal_total)
            write_to_file(summary)
            return exitcode

        else:
            for root, dirs, files in os.walk(args.path, topdown=False):
                # Check all sub-dir in set path
                for name in dirs:
                    path = Path(root, name)
                    path_total["dir_count"] += 1
                    path_total, illegal_total = check_current_path(
                        args, path, path_total, illegal_total
                    )

                # Check all files, in all sub-dir in set path
                for name in files:
                    path = Path(root, name)
                    path_total["file_count"] += 1
                    if (
                        name.startswith(".DS_Store")
                        or name.startswith("._")
                        and os.stat(name).st_size < 5000
                    ):
                        path_total["ds_count"] += 1
                        continue
                    else:
                        illegal_total = whitespace_check(path, illegal_total)
                        path_total, illegal_total = illegalchar_check(
                            args, path, path_total, illegal_total
                        )

                        if len(str(path)) > 255:
                            illegal_path = path
                            char_limit_msg = f"Too many characters for Windows path (>255): \n {illegal_path} "
                            logger.info(char_limit_msg)

                            write_to_file(
                                illegal_path=str(illegal_path),
                                path_length=len(str(illegal_path)),
                            )
                            path_total["char_limit_count"] += 1
                        else:
                            pass

        summary = prepare_summary(args, path_total, illegal_total)
        write_to_file(summary=summary)
        return exitcode

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        excp_msg = f" Exception raised: {e}\n\
                      TYPE: {exc_type},\n\
                      FNAME: {fname},\n\
                      LINENO: {exc_tb.tb_lineno}\n\
                    "
        logger.error(excp_msg)
        exitcode = 1
        return exitcode


def check_current_path(args, path, path_total, illegal_total):
    """
    Check the current path for whitespace and illegal characters.
    """
    try:
        whitespace_match = whitespace_check(path, illegal_total)
        whitespace_count = len(whitespace_match)
        illegal_total.update({"whitespace_count": whitespace_count})

        path_total, illegal_total = illegalchar_check(
            args, path, path_total, illegal_total
        )

        return path_total, illegal_total

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        excp_msg = f" Exception raised: {e}\n\
                      TYPE: {exc_type},\n\
                      FNAME: {fname},\n\
                      LINENO: {exc_tb.tb_lineno}\n\
                    "
        logger.error(excp_msg)


def illegalchar_check(args, path, path_total, illegal_total):
    """
    Check a path name against a list of illegal characters, remove any found.
    """
    illegalchar_count = 0
    illegal_chars = []

    illegalchar_list = [args.characters]

    illegalchar_count = len([x for x in path.name if x in illegalchar_list])

    try:
        # regex to match on:
        # leading and trailing all whitespace
        # period preceding "/" or at the end of a path
        # remove matches and count number of subs

        pattern = re.compile(
            r"(\||\'|\"|\}|\{|\:|\=|\@|\*|\?|\!|\<|\>|\&|\#|\%|\$|\~|\+|\.$|^\.)"
        )

        for match in re.findall(pattern, path.name):
            illegalchar_count += 1 if match[0] != "" else 0
            illegal_chars.append(match[0]) if match[0] != "" else None

            if len(illegal_chars) != 0 and path.is_file():
                path_total["illegal_filename_total"] += 1
            elif len(illegal_chars) != 0 and path.is_dir():
                path_total["illegal_dirname_total"] += 1

            if len(illegal_chars) != 0:
                path_total["illegal_char_list"] += illegal_chars
                count = Counter(illegalchar_count=len(illegal_chars))
                illegal_total.update(count)
                write_to_file(illegal_path=path, illegal_chars=illegal_chars)
            else:
                continue

        return path_total, illegal_total

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        excp_msg = f" Exception raised: {e}\n\
                      TYPE: {exc_type},\n\
                      FNAME: {fname},\n\
                      LINENO: {exc_tb.tb_lineno}\n\
                    "
        logger.error(excp_msg)

    return illegalchar_count, illegal_chars


def whitespace_check(path, illegal_total):
    pattern = re.compile(r"(^\s+|\s+$|\s+/|/\s+)")
    whitespace_match = re.findall(pattern, str(path))
    whitespace_count = len(whitespace_match)
    if whitespace_count != 0:
        write_to_file(
            illegal_path=path,
            whitespace_count=whitespace_count,
        )
        illegal_total.update({"whitespace_count": whitespace_count})
    return illegal_total


def prepare_summary(args, path_total, illegal_total):
    """
    Prepare a summary of totals and pass it to write_to_file method.
    """
    left_curly_brace_total = path_total["illegal_char_list"].count("{")
    right_curly_brace_total = path_total["illegal_char_list"].count("}")
    single_quote_total = path_total["illegal_char_list"].count("'")
    double_quote_total = path_total["illegal_char_list"].count('"')

    date_end = str(strftime("%A, %d. %B %Y %I:%M%p", localtime()))
    summary = f"\n========================== END CHECK: {date_end} ================================\n\
            Recursive check: {args.recursive}\n\
            path checked = {args.path} \n\
            {path_total['dir_count']} sub-directories in path.\n\
            {path_total['file_count']} files in path.\n\
            {path_total['illegal_dirname_total']} directory names with illegal characters.\n\
            {path_total['illegal_filename_total']} filenames with illegal characters.\n\
            {path_total['char_limit_count']} file paths that exceed the 255 Windows limit.\n\
            {illegal_total['whitespace_count']} illegal whitespace characters found.\n\
            {path_total['ds_count']} .DS_Store files found in path.\n\
            {len(path_total['illegal_char_list'])} illegal characters in total: \n\
                @ [{path_total['illegal_char_list'].count('@')}] \n\
                : [{path_total['illegal_char_list'].count(':')}] \n\
                * [{path_total['illegal_char_list'].count('*')}] \n\
                ? [{path_total['illegal_char_list'].count('?')}] \n\
                ! [{path_total['illegal_char_list'].count('!')}] \n\
                > [{path_total['illegal_char_list'].count('>')}] \n\
                < [{path_total['illegal_char_list'].count('<')}] \n\
                | [{path_total['illegal_char_list'].count('|')}] \n\
                & [{path_total['illegal_char_list'].count('&')}] \n\
                # [{path_total['illegal_char_list'].count('#')}] \n\
                % [{path_total['illegal_char_list'].count('%')}] \n\
                $ [{path_total['illegal_char_list'].count('$')}] \n\
                ~ [{path_total['illegal_char_list'].count('~')}] \n\
                + [{path_total['illegal_char_list'].count('+')}] \n\
                = [{path_total['illegal_char_list'].count('+')}] \n\
                {{ [{left_curly_brace_total}] \n\
                }} [{right_curly_brace_total}] \n\
                ' [{single_quote_total}] \n\
                \" [{double_quote_total}] \n\
    =================================================================================================\n\
    "
    logger.info(summary)
    return summary


def write_to_file(*args, **kwargs):
    file_date = str(strftime("%Y%m%d", localtime()))
    loc = os.getcwd()
    print(loc)
    with open(f"{file_date}_illegal_paths.txt", "a+") as f:
        for key, value in kwargs.items():
            print(key, value)
            f.write(f"{key}: {value}\n")
        f.write("\n")
        f.close()
    return


if __name__ == "__main__":
    # one = [
    #         "@",
    #         ":",
    #         "*",
    #         "?",
    #         "!",
    #         '"',
    #         "'",
    #         "<",
    #         ">",
    #         "|",
    #         "&",
    #         "#",
    #         "%",
    #         "$",
    #         "~",
    #         "+",
    #         "=",
    #         "'",
    #         '"',
    #         "{",
    #         "}",
    #         "^",
    #     ],
    # two = "/Users/cucos001/GitHub/Illegal-Character-Check",
    # three = None,
    # four = ".txt",
    # five = "/Users/cucos001/Desktop/test/",
    # six = True,
    check_set_path()

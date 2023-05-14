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
    write_to_file(args_msg=args.args_msg)

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
            path_total, illegal_total = check_path(
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
                    path_total, illegal_total = check_path(
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


def check_path(args, path, path_total, illegal_total):
    """
    Check the current path for whitespace and illegal characters.
    """
    try:
        if args.whitespace is not False:
            whitespace_match = whitespace_check(path, illegal_total)
            whitespace_count = len(whitespace_match)
            illegal_total.update({"whitespace_count": whitespace_count})
        else:
            pass

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

    illegalchar_list = [x for x in args.characters]

    illegalchar_count = len([x for x in path.name if x in illegalchar_list])

    format_illchar_list = ["\\" + x + "|" for x in illegalchar_list]
    # build the regex from the illegal character list
    regex_var = "".join(item for item in format_illchar_list)

    try:
        # regex to match on:
        # leading and trailing all whitespace
        # period preceding "/" or at the end of a path
        # remove matches and count number of subs

        # pattern = re.compile(
        #     r"(\||\'|\"|\}|\{|\:|\=|\@|\*|\?|\!|\<|\>|\&|\#|\%|\$|\~|\+|\.$|^\.)"
        # )

        pattern = re.compile(rf"({regex_var[:-1]})")
        # https://stackoverflow.com/questions/6930982/how-to-use-a-variable-inside-a-regular-expression

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

    unique_char_list = set(path_total["illegal_char_list"])

    summary_list = []
    date_end = str(strftime("%A, %d. %B %Y %I:%M%p", localtime()))

    part_1 = f"\n\
    ========================== SUMMARY ================================\n\
            Check completed on: {date_end}\n\
            Path checked = {args.path} \n\
            Recursive check: {args.recursive}\n\
            WhiteSpace check: {args.whitespace}\n\
            "
    summary_list.append(part_1)

    if args.whitespace is not False:
        part_2 = f"            {illegal_total['whitespace_count']} illegal whitespace characters found."
        summary_list.append(part_2)
    else:
        part_2 = ""

    part_3 = f"\n\
            {path_total['dir_count']} sub-directories in path.\n\
            {path_total['file_count']} files in path.\n\
            {path_total['illegal_dirname_total']} directory names with illegal characters.\n\
            {path_total['illegal_filename_total']} filenames with illegal characters.\n\
            {path_total['char_limit_count']} file paths that exceed the 255 Windows limit.\n\
            {path_total['ds_count']} .DS_Store files found in path.\n\
            {len(path_total['illegal_char_list'])} illegal characters in total: \n\
            \n\
            "

    summary_list.append(part_3)

    part_4 = ""
    for item in unique_char_list:
        line = f"            {item} [{path_total['illegal_char_list'].count(item)}]\n"
        part_4 += line
    part_4 += "================================================================================================\n\
    "
    summary_list.append(part_4)

    # format summary for log files.
    summary_msg = ""
    for x in summary_list:
        summary_msg += x

    logger.info(summary_msg)
    return summary_list


def write_to_file(*args, **kwargs):
    file_date = str(strftime("%Y%m%d", localtime()))
    with open(f"{file_date}_illegal_paths.txt", "a+") as f:
        for key, value in kwargs.items():
            if key != "summary":
                f.write(f"\n{key}: {value}")
            else:
                for line in value:
                    f.write(line + "\n")

        f.write("\n")
        f.close()
    return


if __name__ == "__main__":
    check_set_path()

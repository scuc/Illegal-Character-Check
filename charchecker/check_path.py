import logging
import os
import re
import sys
from collections import Counter
from pathlib import Path
from time import localtime, strftime

logger = logging.getLogger(__name__)


def check_path(args):
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
            for item in os.listdir(Path(args.path)):
                path = Path(args.path, item)
                path_total = update_count(path, path_total)
                path_total = path_len_check(args, path, path_total)

                path_total, illegal_total = illegalchar_check(
                    args, path, path_total, illegal_total
                )

                if args.whitespace is not False:
                    illegal_total = whitespace_check(args, path, illegal_total)
                else:
                    pass

            summary = prepare_summary(args, path_total, illegal_total)
            write_to_file(destination=args.destination, summary=summary)
            return exitcode

        else:
            for root, dirs, files in os.walk(args.path, topdown=False):
                # Check all sub-dir in set path
                for name in dirs:
                    path = Path(root, name)
                    path_total = update_count(path, path_total)
                    path_total, illegal_total = illegalchar_check(
                        args, path, path_total, illegal_total
                    )

                # Check all files, in all sub-dir in set path
                for name in files:
                    path = Path(root, name)
                    path_total = update_count(path, path_total)
                    path_total = path_len_check(args, path, path_total)

                    path_total, illegal_total = illegalchar_check(
                        args, path, path_total, illegal_total
                    )

                    illegal_total = whitespace_check(args, path, illegal_total)

        summary = prepare_summary(args, path_total, illegal_total)
        write_to_file(args, summary=summary)
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


def update_count(path, path_total):
    """
    Update the path_total count.
    Counts files, dirs, and invisible files in
    a given path.
    """
    if path.is_dir():
        path_total["dir_count"] += 1
    else:
        path_total["file_count"] += 1

    if (
        path.name.startswith(".DS_Store")
        or path.name.startswith("._")
        and os.stat(path.name).st_size < 5000
    ):
        path_total["ds_count"] += 1
    else:
        pass

    return path_total


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
            else:
                continue

        if len(illegal_chars) > 0:
            write_to_file(args, illegal_path=path, illegal_chars=illegal_chars)

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


def whitespace_check(args, path, illegal_total):
    """
    Check for leading or trailing whitespace characters in the file path.
    """
    pattern = re.compile(r"(^\s+|\s+$|\s+/|/\s+)")
    whitespace_match = re.findall(pattern, str(path))
    whitespace_count = len(whitespace_match)
    if whitespace_count != 0:
        write_to_file( 
            illegal_path=path,
            whitespace_count=whitespace_count,
        )
        illegal_total.update({"whitespace_count": whitespace_count})
    else:
        illegal_total

    return illegal_total


def path_len_check(args, path, path_total):
    """
    Check the length of a path and if length is over 255 characters
    record the path and the length in the output.txt
    """
    if len(str(path)) > 255:
        illegal_path = path
        char_limit_msg = (
            f"Too many characters for Windows path (>255): \n {illegal_path} "
        )
        logger.info(char_limit_msg)

        write_to_file(
            args, 
            illegal_path=str(illegal_path),
            path_length=len(str(illegal_path)),
        )
        path_total["char_limit_count"] += 1
    else:
        pass

    return path_total


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
            Output file path: {args.destination}\n\
            "
    summary_list.append(part_1)

    part_2 = f"\n\
            {path_total['dir_count']} sub-directories in path.\n\
            {path_total['file_count']} files in path.\n\
            {path_total['illegal_dirname_total']} directory names with illegal characters.\n\
            {path_total['illegal_filename_total']} filenames with illegal characters.\n\
            {path_total['char_limit_count']} file paths that exceed the 255 Windows limit.\n\
            {path_total['ds_count']} .DS_Store files found in path.\n\
            "
    summary_list.append(part_2)

    if args.whitespace is not False:
        part_3 = f"\n            {illegal_total['whitespace_count']} illegal whitespace characters found."
        summary_list.append(part_3)
    else:
        part_3 = ""

    part_4 = ""
    for item in unique_char_list:
        line = f"            {item} [{path_total['illegal_char_list'].count(item)}]\n"
        part_4 += line

    part_5 = "\n================================================================================================\n\
    "
    summary_list.append(part_4)
    summary_list.append(part_5)

    # format summary for log files.
    summary_msg = ""
    for x in summary_list:
        summary_msg += x

    logger.info(summary_msg)
    return summary_list


def write_to_file(*args, **kwargs):
    file_date = str(strftime("%Y%m%d", localtime()))
    filename = f"{file_date}_illegal_paths.txt"

    # keys = list(kwargs.keys())
    # print(list)
    # keys.sort()
    # sorted_dict = {i: kwargs[i] for i in keys}
    # print(sorted_dict)

    for key, value in kwargs.items():

        kwarg_list.append()

        if key != "summary":
            with open(filename, "a+") as f:
                f.write(f"\n{key}: {value}\n")
        else:
            with open(filename, "r+") as f:
                content = f.read()
                f.seek(0, 0)
                for line in value:
                    f.write(line + "\n")

    f.close()

    return


if __name__ == "__main__":
    check_path()

import os
import re
import sys
from collections import Counter, OrderedDict
from pathlib import Path
from time import localtime, strftime

illegalchar_list = [
    "|",
    "/",
    ";",
    ":",
    "'",
    '"',
    "@",
    ",",
    "!",
    "#",
    "$",
    "%",
    "^",
    "&",
    "=",
    "<",
    ">",
    "{",
    "}",
    "*",
    "?",
    "~",
    "+",
]

input = ""
destination = ""


def check_path():
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
    write_to_file()

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

    try:
        for root, dirs, files in os.walk(input, topdown=False):
            # Check all sub-dir in set path
            for name in dirs:
                if not name.startswith("."):
                    path = Path(root, name)
                    path_total = update_count(path, path_total)
                    path_total, illegal_total = illegalchar_check(
                        path, path_total, illegal_total
                    )
                    illegal_total = whitespace_check(path, illegal_total)

                else:
                    continue

            # Check all files, in all sub-dir in set path
            for name in files:
                if not name.startswith("."):
                    path = Path(root, name)
                    path_total = update_count(path, path_total)
                    path_total = path_len_check(path, path_total)

                    path_total, illegal_total = illegalchar_check(
                        path, path_total, illegal_total
                    )

                    illegal_total = whitespace_check(path, illegal_total)
                else:
                    continue

        summary = prepare_summary(path_total, illegal_total)
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
        print(excp_msg)
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


def illegalchar_check(path, path_total, illegal_total):
    """
    Check a path name against a list of illegal characters, remove any found.
    """
    illegalchar_count = 0
    illegal_chars = []

    # build the regex from the illegal character list
    format_illchar_list = ["\\" + x + "|" for x in illegalchar_list]
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

        if len(illegal_chars) != 0:
            path_total["illegal_char_list"] += illegal_chars
            count = Counter(illegalchar_count=len(illegal_chars))
            illegal_total.update(count)

        if len(illegal_chars) != 0 and path.is_file():
            path_total["illegal_filename_total"] += 1
        elif len(illegal_chars) != 0 and path.is_dir():
            path_total["illegal_dirname_total"] += 1

        if len(illegal_chars) > 0:
            illegal_values = OrderedDict(
                {"illegal_path": path, "illegal_chars": illegal_chars}
            )
            write_to_file(illegal_values=illegal_values)

            for key, value in illegal_values.items():
                print(f"{key} : {value}")
            print("")

        return path_total, illegal_total

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        excp_msg = f" Exception raised: {e}\n\
                      TYPE: {exc_type},\n\
                      FNAME: {fname},\n\
                      LINENO: {exc_tb.tb_lineno}\n\
                    "
        print(excp_msg)


def whitespace_check(path, illegal_total):
    """
    Check for leading, trailing, or double whitespace characters in the file path.
    """
    pattern = re.compile(r"(^\s+|\s+$|\s+/|/\s+|\s{2,})")
    whitespace_match = re.findall(pattern, str(path))
    whitespace_count = len(whitespace_match)
    if whitespace_count != 0:
        illegal_values = OrderedDict(
            {"illegal_path": path, "whitespace_count": whitespace_count}
        )

        write_to_file(illegal_values=illegal_values)
        illegal_total.update({"whitespace_count": whitespace_count})

        for key, value in illegal_values.items():
            print(f"{key} : {value}")
        print("")
    else:
        illegal_total

    return illegal_total


def path_len_check(path, path_total):
    """
    Check the length of a path and if length is over 255 characters
    record the path and the length in the output.txt
    """
    if len(str(path)) > 255:
        illegal_path = path
        char_limit_msg = f"Windows path warning (>255 Characters): \n {illegal_path} "

        write_to_file(char_limit_msg)
        path_total["char_limit_count"] += 1
    else:
        pass

    return path_total


def prepare_summary(path_total, illegal_total):
    """
    Prepare a summary of totals and pass it to write_to_file method.
    """

    unique_char_list = set(path_total["illegal_char_list"])

    summary_list = []
    date_end = str(strftime("%A, %d. %B %Y %I:%M%p", localtime()))

    part_1 = f"\n\
    ========================== SUMMARY ================================\n\
            Check completed on: {date_end}\n\
            Path checked = {input} \n\
            Output file path: {destination}\n\
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

    part_3 = f"\n            {illegal_total['whitespace_count']} illegal whitespace characters found.\n"
    summary_list.append(part_3)

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

    print(summary_msg)
    return summary_msg


def write_to_file(*args, **kwargs):
    file_date = str(strftime("%Y%m%d", localtime()))
    filename = f"{file_date}_illegal_paths.txt"
    report = os.path.join(destination, filename)

    for key, value in kwargs.items():
        if key == "illegal_values":
            value = list(value.items())

        with open(report, "a+") as f:
            if key in ["start_msg", "args_msg"]:
                f.write(f"{value}\n")

            if key == "illegal_values":
                formatted_value = f"\n {value[0]} \n{value[1]} \n"
                f.write(f"{formatted_value}\n")

            if key == "summary":
                for line in value:
                    f.write(line)

        f.close()

    return


if __name__ == "__main__":
    check_path()

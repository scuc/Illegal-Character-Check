#! /usr/bin/env python3

# import logging
import os
from pathlib import Path
import re
from collections import Counter
from time import localtime, strftime

# import config

# logger = logging.getLogger(__name__)

# config = config.get_config()


def check_pathname(path):
    """
    Check each path recursively, and elminiate any illegal characters.
    """

    date_start = str(strftime("%A, %d. %B %Y %I:%M%p", localtime()))

    start_msg = f"\n\
    ================================================================\n\
                    START CHECK: {date_start}\n\
    ================================================================\n\
   "
    write_path_to_txt(start_msg=start_msg)
    print(start_msg)

    char_limit_count = 0
    dir_count = 0
    ds_count = 0
    file_count = 0
    illegal_char_list = []
    illegal_dirname_total = 0
    illegal_filename_total = 0
    illegalchar_total = Counter({"illegal_char_count": 0, "whitespace_count": 0})

    # try:
    for root, dirs, files in os.walk(path, topdown=False):
        for name in dirs:
            path = Path(root, name)
            dir_count += 1
            illegalchar_count, illegal_chars = illegalchar_check(path)
            # print(f"1 - DIR NAME: {pathname}")
            illegalchar_total.update(illegalchar_count)
            illegal_char_list += illegal_chars

            if len(illegal_chars) != 0:
                illegal_dirname_total += 1
                # print(f"2 - ILLEGAL CHAR TOTAL: {illegalchar_total}")
            else:
                continue

        for name in files:
            file_count += 1
            path = Path(root, name)
            if (
                name.startswith(".DS_Store")
                or name.startswith("._")
                and os.stat(name).st_size < 5000
            ):
                ds_count += 1
                continue
            else:
                whitespace_match = whitespace_check(path)
                whitespace_count = len(whitespace_match)
                if whitespace_count != 0:
                    write_path_to_txt(
                        illegal_path=path,
                        whitespace_count=whitespace_count,
                    )
                    illegalchar_total.update({"whitespace_count": whitespace_count})

                illegal_char_count, illegal_chars = illegalchar_check(path)

                if len(illegal_chars) != 0:
                    illegal_filename_total += 1
                    illegalchar_total.update(illegal_char_count)
                    # print(illegalchar_total)
                    illegal_char_list += illegal_chars
                    # print(illegal_char_list)

                    write_path_to_txt(illegal_path=path, illegal_chars=illegal_chars)

                else:
                    pass

                if len(str(path)) > 255:
                    illegal_path = path
                    char_limit_msg = f"Too many characters for Windows path (>255): \n {illegal_path} "
                    # logger.info(char_limit_msg)
                    print(char_limit_msg)
                    write_path_to_txt(
                        illegal_path=str(illegal_path),
                        path_length=len(str(illegal_path)),
                    )
                    char_limit_count += 1
                else:
                    # print(" === PASS ON PATH LEN")
                    pass

    # except Exception as e:
    #     file_walk_msg = f"Exception on FILE Walk: \n {e}"
    #     # logger.error(file_walk_msg)
    #     print(file_walk_msg)

    left_curly_brace_total = illegal_char_list.count("{")
    right_curly_brace_total = illegal_char_list.count("}")
    single_quote_total = illegal_char_list.count("'")
    double_quote_total = illegal_char_list.count('"')

    date_end = str(strftime("%A, %d. %B %Y %I:%M%p", localtime()))
    totals = f"\n========================== END CHECK: {date_end} ================================\n\
            path checked = {path} \n\
            {dir_count} sub-directories in path.\n\
            {file_count-ds_count} files in path.\n\
            {illegal_dirname_total} directory names with illegal characters.\n\
            {illegal_filename_total} filenames with illegal characters.\n\
            {char_limit_count} file paths that exceed the 255 Windows limit.\n\
            {illegalchar_total['whitespace_count']} illegal whitespace characters found.\n\
            {ds_count} .DS_Store files found in path.\n\
            {len(illegal_char_list)} illegal characters in total: \n\
            @ [{illegal_char_list.count('@')}] \n\
            : [{illegal_char_list.count(':')}] \n\
            * [{illegal_char_list.count('*')}] \n\
            ? [{illegal_char_list.count('?')}] \n\
            ! [{illegal_char_list.count('!')}] \n\
            > [{illegal_char_list.count('>')}] \n\
            < [{illegal_char_list.count('<')}] \n\
            | [{illegal_char_list.count('|')}] \n\
            & [{illegal_char_list.count('&')}] \n\
            # [{illegal_char_list.count('#')}] \n\
            % [{illegal_char_list.count('%')}] \n\
            $ [{illegal_char_list.count('$')}] \n\
            ~ [{illegal_char_list.count('~')}] \n\
            + [{illegal_char_list.count('+')}] \n\
            = [{illegal_char_list.count('+')}] \n\
            {{ [{left_curly_brace_total}] \n\
            }} [{right_curly_brace_total}] \n\
            ' [{single_quote_total}] \n\
            \" [{double_quote_total}] \n\
    =================================================================================================\n\
            "

    write_path_to_txt(totals=totals)
    print(illegal_char_list)
    print("SCRIPT DONE")
    return


def illegalchar_check(path):
    """
    Check a path name against a list of illegal characters, remove any found.
    """
    illegal_char_count = 0
    illegal_chars = []

    illegalchars = [
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
    illegal_char_count = len([x for x in path.name if x in illegalchars])
    illegal_char = [x for x in path.name if x in illegalchars]
    print(f"3 - ILLEGAL CHAR: {illegal_char}")

    try:
        # regex to match on:
        # leading and trailing all whitespace
        # period preceding "/" or at the end of a path
        # remove matches and count number of subs

        pattern = re.compile(
            r"(\||\'|\"|\}|\{|\:|\=|\@|\*|\?|\!|\<|\>|\&|\#|\%|\$|\~|\+|\.$|^\.)"
        )
        print(f"name: {path.name}")
        for match in re.findall(pattern, path.name):
            illegal_char_count += 1 if match[0] != "" else 0
            illegal_chars.append(match[0]) if match[0] != "" else None

    except Exception as e:
        make_safe_msg = f"Exception raised on attempt find illegal characters: \n {e}"
        # logger.error(make_safe_msg)
        print(make_safe_msg)

    # if illegal_char_count > 0 or whitespace_count > 0:
    #     illegal_path = os.path.join(root, name)
    #     write_path_to_txt(illegal_chars=illegal_path)
    # else:
    #     pass

    illegal_char_totals = {
        "illegal_char_count": illegal_char_count,
    }

    return illegal_char_totals, illegal_chars


def whitespace_check(path):
    pattern = re.compile(r"(^\s+|\s+$|\s+/|/\s+)")
    whitespace_match = re.findall(pattern, str(path))
    print(whitespace_match, len(whitespace_match))
    return whitespace_match


def write_path_to_txt(*args, **kwargs):
    # req_zip_f = os.path.join(illegal_path[:28], "_Archive_REQ_ZIP")
    # os.chdir(req_zip_f)
    file_date = str(strftime("%Y%m%d", localtime()))
    with open(f"{file_date}_illegal_paths.txt", "a+") as f:
        for key, value in kwargs.items():
            f.write(f"{key}: {value}\n")
        f.write(f"\n")
        f.close()
    return


if __name__ == "__main__":
    check_pathname("/Users/cucos001/Desktop/test")

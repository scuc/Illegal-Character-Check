import logging
import logging.config
import os
from datetime import datetime
from time import localtime, strftime

import check_path
import yaml
from argparser import build_parser

logger = logging.getLogger(__name__)

illegal_chars = [
    "@",
    ":",
    "*",
    "?",
    "!",
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


def set_logger():
    """
    Setup logging configuration
    """
    path = os.path.join("charchecker/logging.yaml")

    with open(path, "rt") as f:
        config = yaml.safe_load(f.read())

        # get the file name from the handlers, append the date to the filename.
        for i in config["handlers"].keys():
            if "filename" in config["handlers"][i]:
                log_filename = config["handlers"][i]["filename"]
                base, extension = os.path.splitext(log_filename)
                today = datetime.today()

                log_filename = "{}_{}{}".format(
                    base, today.strftime("%Y%m%d"), extension
                )
                config["handlers"][i]["filename"] = log_filename
            else:
                continue

        logger = logging.config.dictConfig(config)

    return logger


def main():
    args = build_parser()

    print(type(args.characters))

    args.characters = (
        [x for x in args.characters[0]] if args.characters != 0 else illegal_chars
    )

    # args.whitespace = [True if args.whitespace != 0 else False]

    args_msg = f"\n\
     Aruguments used: \n\
        Characters: {args.characters}\n\
        Destination: {args.destination}\n\
        Output: {args.format}\n\
        Path: {args.path}\n\
        Recursive: {args.recursive}\n\
        Whitespace: {args.whitespace}\n\
        "

    args.__dict__.update({"args_msg": args_msg})

    date_start = str(strftime("%A, %d. %B %Y %I:%M%p", localtime()))

    start_msg = f"\n\
    ================================================================\n\
                Illegal Character Check - Start\n\
                    {date_start}\n\
    ================================================================"

    logger.info(start_msg)
    logger.info(args_msg)

    exit_code = check_path.check_set_path(args)

    if exit_code != 0:
        logger.info("\nPath check did not complete sucessfully.\n")
    else:
        date_end = str(strftime("%A, %d. %B %Y %I:%M%p", localtime()))

        complete_msg = f"\n\
        ================================================================\n\
                    Illegal Character Check - Complete\n\
                        {date_end}\n\
        ================================================================\n\
        "
        logger.info(complete_msg)
    return


if __name__ == "__main__":
    set_logger()
    main()

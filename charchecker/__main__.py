import logging
import logging.config
import os
from datetime import datetime
from time import localtime, strftime

import yaml


from argparser import build_parser


logger = logging.getLogger(__name__)


def get_config():
    """
    Setup configuration and credentials
    """

    with open("charchecker/config.yaml", "rt") as f:
        config = yaml.safe_load(f.read())

    return config


config = get_config()


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
    print(args)
    date_start = str(strftime("%A, %d. %B %Y %I:%M%p", localtime()))

    start_msg = f"\n\
    ================================================================\n\
                Illegal Character Check - Start\n\
                    {date_start}\n\
    ================================================================"

    logger.info(start_msg)

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

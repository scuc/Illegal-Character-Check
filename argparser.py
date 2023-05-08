import argparse


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--test", default=0.1, type=float, help="test")
    # Many more arguments
    return parser

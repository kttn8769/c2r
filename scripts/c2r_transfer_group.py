"""Transfer _rlnGroupName and _rlnGroupNumber from one star file to another."""

from email import parser
import os
import sys
import re
import argparse

import numpy as np
import pandas as pd
from tqdm import tqdm

import c2r


TARGET_COLS = (
    '_rlnGroupName',
    '_rlnGroupNumber'
)


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=__doc__
    )
    parser.add_argument('--source_star', type=str, required=True, help='Relion star file which provides the group information.')
    parser.add_argument('--in_star', type=str, required=True, help='Input star file.')
    parser.add_argument('--out_star', type=str, required=True, help='Output star file.')
    args = parser.parse_args()

    print('##### Command #####\n\t' + ' '.join(sys.argv))
    args_print_str = '##### Input parameters #####\n'
    for opt, val in vars(args).items():
        args_print_str += '\t{} : {}\n'.format(opt, val)
    print(args_print_str)
    return args


def main():
    args = parse_args()

    print('Loading star files...')
    md_in = c2r.RelionMetaData.load(args.in_star)
    md_src = c2r.RelionMetaData.load(args.source_star)
    md_out = c2r.RelionMetaData(
        df_data=None,
        df_optics=md_in.df_optics,
        data_type='data_particles'
    )




if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Assign optics groups to a particle star file, based on user-specified filename patterns.
"""

import sys
import argparse

import numpy as np
import pandas as pd
from tqdm import tqdm

from c2r import RelionMetaData


def load_optics_pattern(pattern_file):
    list_groupname = []
    list_group = []
    list_pattern = []
    for line in open(pattern_file):
        words = line.strip().split()
        assert len(words) == 3
        list_groupname.append(words[0])
        list_group.append(words[1])
        list_pattern.append(words[2])
    return list_groupname, list_group, list_pattern


def create_data_optics_record(md, list_groupname, list_group):
    df = md.df_optics
    assert df.shape[0] == 1

    # Duplicate rows
    df = pd.concat([df] * len(list_groupname), ignore_index=True, copy=True)

    for i, (groupname, group) in enumerate(zip(list_groupname, list_group)):
        df.iloc[i]['_rlnOpticsGroupName'] = groupname
        df.iloc[i]['_rlnOpticsGroup'] = group

    md.df_optics = df


def modify_data(md, list_group, list_pattern):
    data = md.df_data.to_numpy(copy=False)
    cols = list(md.df_data.columns)
    idx_mic = cols.index('_rlnMicrographName')
    idx_group = cols.index('_rlnOpticsGroup')

    print('Modifying data records....')
    for i in tqdm(range(data.shape[0])):
        mic = data[i, idx_mic]
        optics_found = False
        for group, pattern in zip(list_group, list_pattern):
            if pattern in mic:
                data[i, idx_group] = group
                optics_found = True
                break
        assert optics_found, f'None of the optics patterns matched. {mic}'


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=__doc__
    )
    parser.add_argument('--pattern_file', type=str, required=True, help='Optics group and filename pattern. Syntax: <_rlnOpticsGroupName> <_rlnOpticsGroup> <filename pattern>.')
    parser.add_argument('--infile', type=str, required=True, help='Input star file.')
    parser.add_argument('--outfile', type=str, required=True, help='Output star file.')
    args = parser.parse_args()
    print('##### Command #####\n\t' + ' '.join(sys.argv))
    args_print_str = '##### Input parameters #####\n'
    for opt, val in vars(args).items():
        args_print_str += '\t{} : {}\n'.format(opt, val)
    print(args_print_str)
    return args


def main():
    args = parse_args()

    list_groupname, list_group, list_pattern = load_optics_pattern(args.pattern_file)

    print('Loading star file.')
    md = RelionMetaData.load(args.infile)

    create_data_optics_record(md, list_groupname, list_group)

    modify_data(md, list_group, list_pattern)

    print('Saving output star file...')
    md.write(args.outfile)


if __name__ == '__main__':
    main()
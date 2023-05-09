#!/usr/bin/env python3

import sys
import argparse

from tqdm import tqdm

from c2r import RelionMetaData

GR = '_rlnOpticsGroup'
GRN = '_rlnOpticsGroupName'

def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=__doc__
    )
    parser.add_argument('--infile', type=str, required=True, help='Input')
    parser.add_argument('--outfile', type=str, required=True, help='Output')
    parser.add_argument('--src-optics-group', type=str, required=True, help='Source optics group (_rlnOpticsGroup).')
    parser.add_argument('--src-optics-group-name', type=str, required=True, help='Source optics group name(_rlnOpticsGroupName).')
    parser.add_argument('--new-optics-group', type=str, required=True, help='New optics group (_rlnOpticsGroup).')
    parser.add_argument('--new-optics-group-name', type=str, required=True, help='New optics group name (_rlnOpticsGroupName).')
    args = parser.parse_args()

    print('##### Command #####\n\t' + ' '.join(sys.argv))
    args_print_str = '##### Input parameters #####\n'
    for opt, val in vars(args).items():
        args_print_str += '\t{} : {}\n'.format(opt, val)
    print(args_print_str)
    return args


def change_optics_group(md, src_group, src_groupname, new_group, new_groupname):
    assert '_rlnOpticsGroup'



def main():
    args = parse_args()

    print('Loading star file.')
    md = RelionMetaData.load(args.infile)

    assert GR in md.df_optics.columns
    assert GRN in md.df_optics.columns

    assert GR in md.df_data.columns

    print('Modifying the optics table...')
    md.df_optics.loc[md.df_optics[GR] == args.src_optics_group, GR] = args.new_optics_group
    md.df_optics.loc[md.df_optics[GRN] == args.src_optics_group_name, GRN] = args.new_optics_group_name

    print('Modifying the data table...')
    md.df_data.loc[md.df_data[GR] == args.src_optics_group, GR] = args.new_optics_group

    md.write(outfile=args.outfile)
    print('end')


if __name__ == '__main__':
    main()

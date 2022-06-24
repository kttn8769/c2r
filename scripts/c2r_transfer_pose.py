#!/usr/bin/env python3
"""Transfer pose parameters (rot + trans) and random subset id (half1 or half2) from a star file created by PyEM csparc2star.py to the original relion star file. Particles not listed in the csparc star file are not included in the output star file.
"""

import os
import sys
import re
import argparse

import numpy as np
import pandas as pd
from tqdm import tqdm

import c2r

POSE_COLS = (
    '_rlnAngleRot',
    '_rlnAngleTilt',
    '_rlnAnglePsi',
    '_rlnOriginXAngst',
    '_rlnOriginYAngst'
)
SUBSET_COL = '_rlnRandomSubset'


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=__doc__
    )
    parser.add_argument('--relion_star', type=str, required=True, help='Relion star file.')
    parser.add_argument('--csparc_star', type=str, required=True, help='cryoSPARC star file created with PyEM csparc2star.py.')
    parser.add_argument('--out_star', type=str, required=True, help='Output star file.')
    parser.add_argument('--csparc_remove_uid', action='store_true', help='Remove the cryoSPARC micrograph UIDs.')
    parser.add_argument('--dont_transfer_random_subset', action='store_true', help='Don\'t transfer _rlnRandomSubset to the output star file.')
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
    md_relion = c2r.RelionMetaData.load(args.relion_star)
    md_csparc = c2r.RelionMetaData.load(args.csparc_star)
    md_out = c2r.RelionMetaData(
        df_data=None,
        df_optics=md_relion.df_optics,
        data_type='data_particles'
    )

    print('Preparing....')
    csparc_cols = list(md_csparc.df_data.columns)
    csparc_data = md_csparc.df_data.to_numpy(copy=True)
    csparc_pose_cols = [x for x in POSE_COLS if x in csparc_cols]
    if not args.dont_transfer_random_subset:
        if SUBSET_COL in csparc_cols:
            csparc_pose_cols.append(SUBSET_COL)
    csparc_pose_idxs = [csparc_cols.index(x) for x in csparc_pose_cols]
    csparc_imgname_idx = csparc_cols.index('_rlnImageName')

    relion_cols = list(md_relion.df_data.columns)
    relion_data = md_relion.df_data.to_numpy(copy=True)
    for csparc_pose_col in csparc_pose_cols:
        if csparc_pose_col not in relion_cols:
            relion_cols.append(csparc_pose_col)
            relion_data = np.concatenate((relion_data, np.empty((relion_data.shape[0], 1))), axis=1)
    relion_pose_cols = csparc_pose_cols
    relion_pose_idxs = [relion_cols.index(x) for x in relion_pose_cols]
    relion_imgname_idx = relion_cols.index('_rlnImageName')

    out_cols = relion_cols
    out_data = []

    print('Listing relion image id...')
    relion_id_dict = {}
    for i in tqdm(range(relion_data.shape[0])):
        relion_id_dict[c2r.imgname_to_imgid(relion_data[i, relion_imgname_idx], rm_uid=False)] = i

    print('Transfering poses....')
    for i in tqdm(range(csparc_data.shape[0])):
        csparc_id = c2r.imgname_to_imgid(csparc_data[i, csparc_imgname_idx], rm_uid=True)
        j = relion_id_dict[csparc_id]
        dst = np.copy(relion_data[j])
        src = csparc_data[i]
        dst[relion_pose_idxs] = src[csparc_pose_idxs]
        out_data.append(dst)

    print('Converting to dataframe...')
    md_out.df_data = pd.DataFrame(out_data, columns=out_cols)

    print('Saving the output star file...')
    md_out.write(args.out_star)


if __name__ == '__main__':
    main()

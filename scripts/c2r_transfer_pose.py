#!/usr/bin/env python3
"""Transfer pose parameters from a star file created by PyEM csparc2star.py to the original relion star file. No other parameters are transfered. Just poses (rot + trans). Particles not listed in the csparc star file are not included in the output star file.
"""

import os
import sys
import re
import argparse

import numpy as np
import pandas as pd
from tqdm import tqdm

from c2r import RelionMetaData


def imgname_to_imgid(imgname, rm_uid=True):
    n, f = imgname.split('@')
    if rm_uid:
        imgid = n + '@' + re.sub('^[0-9]+_', '', os.path.basename(f))
    else:
        imgid = n + '@' + os.path.basename(f)
    return imgid


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=__doc__
    )
    parser.add_argument('--relion_star', type=str, required=True, help='Relion star file.')
    parser.add_argument('--csparc_star', type=str, required=True, help='cryoSPARC star file created with PyEM csparc2star.py.')
    parser.add_argument('--out_star', type=str, required=True, help='Output star file.')
    parser.add_argument('--csparc_remove_uid', action='store_true', help='Remove the cryoSPARC micrograph UIDs.')
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
    md_relion = RelionMetaData.load(args.relion_star)
    md_csparc = RelionMetaData.load(args.csparc_star)
    md_out = RelionMetaData(
        df_particles=None,
        df_optics=md_relion.df_optics
    )

    relion_cols = list(md_relion.df_particles.columns)
    relion_imgname_idx = relion_cols.index('_rlnImageName')
    relion_rot_idx = relion_cols.index('_rlnAngleRot')
    relion_tilt_idx = relion_cols.index('_rlnAngleTilt')
    relion_psi_idx = relion_cols.index('_rlnAnglePsi')
    relion_x_idx = relion_cols.index('_rlnOriginXAngst')
    relion_y_idx = relion_cols.index('_rlnOriginYAngst')
    relion_data = md_relion.df_particles.to_numpy(copy=True)

    csparc_cols = list(md_csparc.df_particles.columns)
    csparc_imgname_idx = csparc_cols.index('_rlnImageName')
    csparc_rot_idx = csparc_cols.index('_rlnAngleRot')
    csparc_tilt_idx = csparc_cols.index('_rlnAngleTilt')
    csparc_psi_idx = csparc_cols.index('_rlnAnglePsi')
    csparc_x_idx = csparc_cols.index('_rlnOriginXAngst')
    csparc_y_idx = csparc_cols.index('_rlnOriginYAngst')
    csparc_data = md_csparc.df_particles.to_numpy(copy=True)

    out_cols = relion_cols
    out_data = []

    print('Listing relion image id...')
    relion_id_dict = {}
    for i in tqdm(range(relion_data.shape[0])):
        relion_id_dict[imgname_to_imgid(relion_data[i, relion_imgname_idx], rm_uid=False)] = i

    print('Transfering poses....')
    for i in tqdm(range(csparc_data.shape[0])):
        csparc_id = imgname_to_imgid(csparc_data[i, csparc_imgname_idx], rm_uid=True)
        j = relion_id_dict[csparc_id]
        dst = np.copy(relion_data[j])
        src = csparc_data[i]
        dst[[relion_rot_idx, relion_tilt_idx, relion_psi_idx, relion_x_idx, relion_y_idx]] = \
            src[[csparc_rot_idx, csparc_tilt_idx, csparc_psi_idx, csparc_x_idx, csparc_y_idx]]
        out_data.append(dst)

    print('Converting to dataframe...')
    md_out.df_particles = pd.DataFrame(out_data, columns=out_cols)

    print('Saving the output star file...')
    md_out.write(args.out_star)


if __name__ == '__main__':
    main()
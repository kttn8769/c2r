#!/usr/bin/env python3
"""Transfer pose parameters from a star file created by PyEM csparc2star.py to the original relion star file. No other parameters are transfered. Just poses (rot + trans). Particles not listed in the csparc star file are not included in the output star file.
"""

from email import parser
import os
import sys
import re
import argparse

import pandas as pd
from yaml import parse

from tqdm import tqdm

from c2r import RelionMetaData


def imgname_to_imgid(md, i, rm_uid=True):
    imgname = md.df_particles.loc[i, '_rlnImageName']
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

    md_relion = RelionMetaData.load(args.relion_star)
    md_csparc = RelionMetaData.load(args.csparc_star)
    md_out = RelionMetaData(
        df_particles=pd.DataFrame(columns=md_relion.df_particles.columns),
        df_optics=md_relion.df_optics
    )

    print('Listing relion image id...')
    relion_id_list = []
    for i in range(len(md_relion.df_particles)):
        relion_id_list.append(imgname_to_imgid(md_relion, i, rm_uid=False))

    print('Transfering poses....')
    for i in tqdm(range(len(md_csparc.df_particles))):
        csparc_id = imgname_to_imgid(md_csparc, i)

        relion_id_found = False
        for relion_id in relion_id_list:
            if csparc_id == relion_id:
                j = len(md_out.df_particles)
                md_out.df_particles.loc[j, :] = md_relion.df_particles.loc[i, :]
                md_out.df_particles.loc[j, '_rlnAngleRot'] = \
                    md_csparc.df_particles.loc[i, '_rlnAngleRot']
                md_out.df_particles.loc[j, '_rlnAngleTilt'] = \
                    md_csparc.df_particles.loc[i, '_rlnAngleTilt']
                md_out.df_particles.loc[j, '_rlnAnglePsi'] = \
                    md_csparc.df_particles.loc[i, '_rlnAnglePsi']
                md_out.df_particles.loc[j, '_rlnOriginXAngst'] = \
                    md_csparc.df_particles.loc[i, '_rlnOriginXAngst']
                md_out.df_particles.loc[j, '_rlnOriginYAngst'] = \
                    md_csparc.df_particles.loc[i, '_rlnOriginYAngst']
                relion_id_found = True
                break
        assert relion_id_found

    print('Saving the output star file...')
    md_out.write(args.out_star)


if __name__ == '__main__':
    main()
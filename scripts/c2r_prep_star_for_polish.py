#!/usr/bin/env python3
"""Prepare a particle star file for particle polish job.

When to use:
* Motion correction was done in RELION.
* The data was exported and processed in cryoSPARC.
* To again process the data in RELION, the data was exported with PyEM csparc2star.py script.
* But RELION particle polish job raises errors relating to micrograph file paths.

What this script does:
* Replace the _rlnMicrographName values (cryoSPARC motioncorr result file) with the corresponding RELION motioncorr result files so that particle polishing can proceed.

Usage example:
# In a RELION project directory,
python3 c2r_prep_star_for_polish.py --i CtfRefine/job079/particles_ctf_refine.star --o CtfRefine/job079/particles_ctf_refine_c2rmodify.star --relion-project-dir . --motioncorr-data-dirs MotionCorr/job003/movies1 MotionCorr/job004/movies2 MotionCorr/job005/movies3
"""

import os
import glob
import sys
import argparse


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description=__doc__
    )
    parser.add_argument(
        '--i', dest='in_star_file', required=True, help='Input particle star file.'
    )
    parser.add_argument(
        '--o', dest='out_star_file', required=True, help='Output particle star file.'
    )
    parser.add_argument(
        '--relion-project-dir', required=True, help='Path to the relion project dir.'
    )
    parser.add_argument(
        '--motioncorr-data-dirs', required=True, nargs='+', help='List of motioncorr data directories, as relative path from the relion project directory.'
    )
    args = parser.parse_args()

    print('##### Command #####\n\t' + ' '.join(sys.argv))
    args_print_str = '##### Input parameters #####\n'
    for opt, val in vars(args).items():
        args_print_str += '\t{} : {}\n'.format(opt, val)
    print(args_print_str)
    return args


def main(in_star_file, out_star_file, relion_project_dir, motioncorr_data_dirs):
    # Assertions
    assert os.path.isdir(relion_project_dir), 'No such directory : {}'.format(relion_project_dir)
    assert os.path.exists(in_star_file), 'No such file exists : {}'.format(in_star_file)
    for motioncorr_data_dir in motioncorr_data_dirs:
        motioncorr_data_dir_path = os.path.join(relion_project_dir, motioncorr_data_dir)
        assert os.path.isdir(motioncorr_data_dir_path), 'No such directory : {}'.format(motioncorr_data_dir_path)
    assert not os.path.exists(out_star_file), 'File already exists : {}'.format(out_star_file)

    # List of motion-corrected micrographs
    mic_names = []
    data_dirs = []
    for motioncorr_data_dir in motioncorr_data_dirs:
        lmic_names = sorted([os.path.basename(x) for x in glob.glob(os.path.join(relion_project_dir, motioncorr_data_dir, '*.mrc'))])
        ldata_dirs = [motioncorr_data_dir] * len(lmic_names)
        mic_names += lmic_names
        data_dirs += ldata_dirs

    print('Now computing....')
    with open(in_star_file) as f:
        out_star_contents = []

        # Read until data_particles
        for line in f:
            out_star_contents.append(line)
            if line.startswith('data_particles'):
                break

        # Real until labels
        for line in f:
            out_star_contents.append(line)
            if line.startswith('loop_'):
                break

        # Read labels, and find the label index of _rlnMicrographName
        rlnMicrographName_index = None
        for line in f:
            if line.startswith('_rlnMicrographName'):
                rlnMicrographName_index = int(line.split()[1].replace('#', '')) - 1
            if not line.startswith('_rln'):
                break
            out_star_contents.append(line)
        assert rlnMicrographName_index is not None, 'Could not find _rlnMicrographName in the data_particles block.'

        # Read data
        for line in f:
            words = line.split()
            if len(words) == 0:
                break

            query_mic_name = os.path.basename(words[rlnMicrographName_index])
            # Remove cryoSPARC UUID
            query_mic_name = '_'.join(query_mic_name.split('_')[1:])

            try:
                mic_index = mic_names.index(query_mic_name)
            except ValueError:
                print('No file name match: {}'.format(query_mic_name), file=sys.stderr)
                sys.exit()

            data_dir = data_dirs[mic_index]
            mic_name = mic_names[mic_index]

            newline = ' '.join(words[:rlnMicrographName_index]) + ' ' + os.path.join(data_dir, mic_name) + ' ' + ' '.join(words[rlnMicrographName_index + 1:]) + '\n'

            out_star_contents.append(newline)

    with open(out_star_file, 'w') as fo:
        fo.writelines(out_star_contents)

if __name__ == '__main__':
    args = parse_args()
    main(args.in_star_file, args.out_star_file, args.relion_project_dir, args.motioncorr_data_dirs)

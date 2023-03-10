#!/usr/bin/env python3

import argparse
import sys
import os


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
        '--orig-apix', type=float, default=-1, help='_rlnMicrographOriginalPixelSize for all the optics groups.'
    )
    parser.add_argument(
        '--add-groupname', action='store_true', help='Add _rlnOpticsGroupName for all the optics groups.'
    )
    parser.add_argument(
        '--overwrite', action='store_true', help='Allow overwriting output file.'
    )
    args = parser.parse_args()

    print('##### Command #####\n\t' + ' '.join(sys.argv))
    args_print_str = '##### Input parameters #####\n'
    for opt, val in vars(args).items():
        args_print_str += '\t{} : {}\n'.format(opt, val)
    print(args_print_str)
    return args


def main(in_star_file: str, out_star_file: str, orig_apix: float, add_groupname: bool, overwrite: bool) -> None:
    assert os.path.exists(in_star_file), 'No such file exists : {}'.format(in_star_file)
    if not overwrite:
        assert not os.path.exists(out_star_file), 'File already exists : {}'.format(out_star_file)

    with open(in_star_file) as f:
        inlines = f.readlines()

    out_star_contents = []
    i = 0

    # Read until data_optics
    for j in range(i, len(inlines)):
        line = inlines[j]
        i += 1
        out_star_contents.append(line)
        if line.startswith('data_optics'):
            break

    # Read until labels
    for j in range(i, len(inlines)):
        line = inlines[j]
        i += 1
        out_star_contents.append(line)
        if line.startswith('loop_'):
            break

    # Read labels
    label_lines = []
    for j in range(i, len(inlines)):
        line = inlines[j]
        i += 1
        if not line.startswith('_rln'):
            i -= 1
            break
        label_lines.append(line)

    if orig_apix > 0:
        for line in label_lines:
            if '_rlnMicrographOriginalPixelSize' in line:
                sys.exit(f'_rlnMicrographOriginalPixelSize is already exist in data_optics table.')
        label_lines.append('_rlnMicrographOriginalPixelSize\n')

    if add_groupname:
        group_col = None
        for k, line in enumerate(label_lines):
            if '_rlnOpticsGroup' in line.split()[0]:
                group_col = k
            if '_rlnOpticsGroupName' in line:
                sys.exit(f'_rlnOpticsGroupName is already exist in data_optics table.')
        label_lines.append('_rlnOpticsGroupName\n')
        if group_col is None:
            sys.exit(f'_rlnOpticsGroup was not found in data_optics table.')

    # Read and modify optics group data block
    data_lines = []
    for j in range(i, len(inlines)):
        line = inlines[j]
        i += 1
        words = line.split()
        if len(words) == 0:
            i -= 1
            break
        if orig_apix > 0:
            words.append(str(orig_apix))
        if add_groupname:
            group = words[group_col]
            groupname = f'opticsGroup{group}'
            words.append(groupname)
        data_lines.append(' '.join(words) + '\n')

    out_star_contents += label_lines + data_lines

    for j in range(i, len(inlines)):
        line = inlines[j]
        i += 1
        out_star_contents.append(line)

    with open(out_star_file, 'w') as f:
        f.writelines(out_star_contents)


if __name__ == '__main__':
    args = parse_args()
    main(
        args.in_star_file,
        args.out_star_file,
        args.orig_apix,
        args.add_groupname,
        args.overwrite
    )

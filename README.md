# c2r
Miscellaneous scripts to help processing cryoSPARC results in RELION.

## Requirements
* Python 3
* Python libraries
  * tqdm
  * NumPy
  * Pandas

## Installation
```bash
git clone https://github.com/kttn8769/c2r.git
```

## Update to the latest
```bash
cd <path to c2r>
git pull
```

## Program help messages
See help message of each script by invoking with --help option.
```bash
<path to c2r>/scripts/<script name> --help
```

For example
```bash
~/softwares/c2r/scripts/c2r_prep_star_for_polish.py --help
```

## TIPS
### Transfer the pose parameters from cryoSPARC to RELION
#### Example
* particles.star is the original RELION particle star file.
* from_csparc.star is the star file created with PyEM's csparc2star.py script.
* UID is prepended to the micrograph name in from_csparc.star.
* The random subset id (half1 or half2) will be also transfered by default (if it exists in csparc_star file)
```bash
c2r_transfer_poses.py --relion_star particles.star --csparc_star from_csparc.star --out_star from_csparc_c2r.star --csparc_remove_uid
```

### Assign optics groups to RELION particle/micrograph star file
#### Example
* particles.star/micrographs.star is the RELION particle/micrograph star file, which has only one opticsGroup.
* A user wants to assign different opticsGroups to them based on the filenames.

* Here is a example of pattern file.
  * syntax: [_rlnOpticsGroupName] [_rlnOpticsGroup] [File name pattern]

```
opticsGroup1 1 _0000_Nov
opticsGroup2 2 _0001_Nov
opticsGroup3 3 _0002_Nov
opticsGroup4 4 _0003_Nov
opticsGroup5 5 _0004_Nov
opticsGroup6 6 _0005_Nov
opticsGroup7 7 _0006_Nov
opticsGroup8 8 _0007_Nov
opticsGroup9 9 _0008_Nov
```
 
* Example command
```bash
c2r_assign_optics_group.py --outfile particles_with_opticsgroup.star --infile particles.star --pattern_file optics_pattern.txt
```

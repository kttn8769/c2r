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
```bash
c2r_transfer_poses.py --relion_star particles.star --csparc_star from_csparc.star --out_star from_csparc_c2r.star --csparc_remove_uid
```

"""c2r common module
"""

import sys
import glob
import os
import re
import datetime
import yaml
import numpy as np
import pandas as pd


def imgname_to_imgid(imgname, rm_uid=True, rm_ext=False):
    n, f = imgname.split('@')
    # shiny.star's n does not have any leading zeros. To avoid complexity, just always remove the leading zeros here.
    n = n.lstrip('0')
    if rm_uid:
        imgid = n + '@' + re.sub('^[0-9]+_', '', os.path.basename(f))
    else:
        imgid = n + '@' + os.path.basename(f)
    if rm_ext:
        imgid = os.path.splitext(imgid)[0]
    return imgid


def imgname_to_imgbasename(imgname, rm_uid=True, rm_ext=True):
    n, f = imgname.split('@')
    # shiny.star's n does not have any leading zeros. To avoid complexity, just always remove the leading zeros here.
    if rm_uid:
        imgbasename = re.sub('^[0-9]+_', '', os.path.basename(f))
    else:
        imgbasename = os.path.basename(f)
    if rm_ext:
        imgbasename = os.path.splitext(imgbasename)[0]
    return imgbasename


def blobpath_and_blobidx_to_imgid(blobpath, blobidx, rm_uid=True, rm_ext=True):
    blobpath = blobpath.decode('UTF-8')
    if rm_uid:
        imgbasename = re.sub('^[0-9]+_', '', os.path.basename(blobpath))
    else:
        imgbasename = os.path.basename(blobpath)
    if rm_ext:
        imgbasename = os.path.splitext(imgbasename)[0]
    # cryoSPARC idx is 0-base
    blobidx += 1
    imgid = str(blobidx) + '@' + imgbasename
    return imgid


def cs_to_imgids(cs, rm_uid=False, rm_ext=False):
    imgids = []
    for i in range(len(cs)):
        # cs idx is 0-base, so add 1
        n = str(int(cs['blob/idx'][i]) + 1)
        f = cs['blob/path'][i].decode('UTF-8')
        imgname = n + '@' + f
        imgid = imgname_to_imgid(imgname, rm_uid=rm_uid)
        if rm_ext:
            imgid = os.splitext(imgid)[0]
        imgids.append(imgid)
    return imgids


def df_data_to_imgids(df_data, rm_uid=False, rm_ext=False):
    imgids = []
    ar = df_data['_rlnImageName'].to_numpy(copy=True)
    for i in range(len(ar)):
        imgid = imgname_to_imgid(ar[i], rm_uid=rm_uid)
        if rm_ext:
            imgid = os.splitext(imgid)[0]
        imgids.append(imgid)
    return imgids


def load_cs(cs_file):
    return np.load(cs_file)


def save_cs(cs_file, cs):
    np.save(cs_file, cs)
    # np.save automatically add .npy extension, thus remove it
    os.rename(cs_file + '.npy', cs_file)


def load_csg(csg_file):
    with open(csg_file, 'r') as f:
        csg = yaml.load(f, Loader=yaml.FullLoader)
    return csg


def save_csg(csg_file, csg):
    with open(csg_file, 'w') as f:
        yaml.dump(csg, stream=f)


def get_metafiles_from_csg(csg_file):
    # Assumes the same directory as csg file
    dirpath = os.path.dirname(csg_file)

    csg = load_csg(csg_file)

    metafiles = []
    for key in csg['results'].keys():
        metafiles.append(csg['results'][key]['metafile'].replace('>', ''))
    metafiles = np.unique(metafiles)

    cs_file = None
    passthrough_file = None
    for metafile in metafiles:
        if 'passthrough_particles.cs' in metafile:
            if passthrough_file is not None and passthrough_file != metafile:
                sys.exit('More than two kinds of passthrough_particles.cs files found.')
            passthrough_file = os.path.join(dirpath, metafile)
        elif 'particles.cs' or 'particles_expanded.cs' or 'downsampled_particles.cs' in metafile:
            if cs_file is not None and cs_file != metafile:
                sys.exit('More than two kinds of particles.cs files found.')
            cs_file = os.path.join(dirpath, metafile)
        else:
            sys.exit(f'Unknown metafile type: {metafile}')

    assert cs_file is not None
    # Some times there is no passthrough file.

    return cs_file, passthrough_file


def find_cryosparc_files(dir):
    """Find required cryoSPARC files from a job directory

    Parameters
    ----------
    dir : string
        Job directory

    Returns
    -------
    cs_file : string
        Particle .cs file

    csg_file : string
        Particle group .csg file

    passthrough_file : string
        Particle passthrough .cs file
    """

    assert os.path.isdir(dir), f'{dir} is not a directory.'

    cs_list = sorted(glob.glob(os.path.join(dir, 'cryosparc*_particles.cs')))
    assert len(cs_list) > 0, f'Particle cs file not found in {dir}'
    # The last cs file found in the directory.
    cs_file = cs_list[-1]

    csg_list = sorted(glob.glob(os.path.join(dir, '*_particles.csg')))
    assert len(csg_list) > 0, f'cs group file (*_particles.csg) was not found in {dir}'
    assert len(csg_list) == 1, f'*_particles.csg matched more than 1 file: {csg_list}'
    csg_file = csg_list[0]

    passthrough_list = sorted(glob.glob(os.path.join(dir, '*_passthrough_particles.cs')))
    assert len(passthrough_list) > 0, f'Particle passthrough file was not found in {dir}'
    assert len(passthrough_list) == 1, f'*_passthrough_particles.cs matched more than 1 file: {passthrough_list}'
    passthrough_file = passthrough_list[0]

    return cs_file, csg_file, passthrough_file


def load_latent_variables(infile, num_components=-1):
    """Loat latent variables from cryoSPARC 3D variability job result.

    Parameters
    ----------
    infile : string
        A particle .cs file containing the latent variables (variability components). Typically like 'cryosparc_<project id>_<job id>_particles.cs'

    num_components : int, optional
        Number of components to use. By default (-1) use all the components.

    Returns
    -------
    ndarray
        Array containing the latent variables. shape=(num_samples, num_variables)
    """

    assert os.path.exists(infile)
    cs = np.load(infile)
    Z = []
    components_mode = 0
    while True:
        if f'components_mode_{components_mode}/value' in cs.dtype.names:
            Z.append(cs[f'components_mode_{components_mode}/value'])
            components_mode += 1
        else:
            break
    assert num_components <= components_mode
    Z = np.vstack(Z).T
    Z = Z[:, :num_components]
    return Z


class CryoSPARCMetaData:
    """cryoSPARC metadata handling class.

    Parameters
    ----------
    cs : ndarray
        Array containing cryoSPARC particles .cs file contents (loaded by np.load)

    csg_template : dict
        Dictionary containing cryoSPARC particles .csg file contents (loaded by yaml.load)

    passthrough : ndarray
        Array containing cryoSPARC passthrough_particles .cs file contents (loaded by np.load)
    """

    def __init__(self, csg, cs, passthrough=None):
        self.cs = cs
        self.csg = csg
        self.passthrough = passthrough

        if self.passthrough is not None:
            assert self.cs.shape[0] == self.passthrough.shape[0]

    @classmethod
    def load(cls, csg_file):
        """Load cryoSPARC metadata from .csg file.

        Parameters
        ----------
        csgfile : string
            particles .csg file.

        Returns
        -------
        CryoSparcMetaData
            CryoSparcMetaData class instance.
        """

        csg = load_csg(csg_file)

        cs_file, passthrough_file = get_metafiles_from_csg(csg_file)

        cs = load_cs(cs_file)
        if passthrough_file:
            passthrough = load_cs(passthrough_file)
        else:
            passthrough = None

        return cls(csg, cs, passthrough)

    def write(self, outdir, outfile_rootname):
        """Save metadata in files.

        Parameters
        ----------
        outdir : string
            Output directory.

        outfile_rootname : string
            Output file rootname.
        """

        os.makedirs(outdir, exist_ok=True)

        cs_file = os.path.join(outdir, outfile_rootname + '_particles.cs')
        save_cs(cs_file, self.cs)

        if self.passthrough is not None:
            passthrough_file = os.path.join(outdir, outfile_rootname + '_passthrough_particles.cs')
            save_cs(passthrough_file, self.passthrough)
        else:
            passthrough_file = None

        csg_file = os.path.join(outdir, outfile_rootname + '_particles.csg')
        self._update_csg(cs_file, passthrough_file)
        save_csg(csg_file, self.csg)

    def _update_csg(self, cs_file, passthrough_file=None):
        """Update cs group file content.

        Parameters
        ----------
        cs_file : string
            Filename of new particles .cs file. (Directory path not required.)

        passthrough_file : string
            Filename of new passthrough_particles .cs file. (Directory path not required.)
        """

        self.csg['created'] = datetime.datetime.now()
        self.csg['group']['description'] = 'Created by cryoPICLS. cryopcls.data_handling.cryosparc.CryoSPARCMetaData._update_csg()'

        num_items = self.cs.shape[0]
        cs_basename = os.path.basename(cs_file)
        if passthrough_file:
            passthrough_basename = os.path.basename(passthrough_file)

        for key in self.csg['results'].keys():
            if 'passthrough_particles.cs' in self.csg['results'][key]['metafile']:
                assert passthrough_file is not None
                self.csg['results'][key]['metafile'] = '>' + passthrough_basename
            elif 'particles.cs' in self.csg['results'][key]['metafile']:
                self.csg['results'][key]['metafile'] = '>' + cs_basename
            else:
                sys.exit(f'Unknown metafile name in {key}: {self.csg["results"][key]["metafile"]}')
            if 'num_items' in self.csg['results'][key].keys():
                self.csg['results'][key]['num_items'] = num_items

    def iloc(self, idxs):
        """Fancy indexing.

        Parameters
        ----------
        idxs : array-like
            Indices to select.

        Returns
        -------
        CryoSPARCMetaData
            New metadata object with the selected rows.
        """

        cs = self.cs[idxs]
        if self.passthrough is not None:
            passthrough = self.passthrough[idxs]
        else:
            passthrough = None
        return self.__class__(self.csg, cs, passthrough)


class RelionMetaData:
    """RELION metadata handling class.
    Parameters
    ----------
    df_data : pandas.DataFrame
        DataFrame containing data block (data_particles or data_micrographs) contents.
    df_optics : pandas.DataFrame, optional
        DataFrame containing optics group data block contents. By default None
    starfile : string
        starfile name
    data_type : string
        'data_particles' or 'data_micrographs'
    """
    def __init__(self, df_data, df_optics=None, starfile=None, data_type=None):
        # data_ block in RELION 2.x/3.0, data_particles block in RELION 3.1
        self.df_data = df_data
        # data_optics block in RELION 3.1
        self.df_optics = df_optics
        self.starfile = starfile
        self.data_type = data_type

    @classmethod
    def load(cls, starfile):
        """Load RELION metadata from a particle star file.
        Parameters
        ----------
        starfile : string
            star file
        Returns
        -------
        RelionMetaData
            RelionMetaData class instance.
        """

        with open(starfile, 'r') as f:
            # Check RELION version
            relion31 = None
            for line in f:
                words = line.strip().split()
                if len(words) == 0:
                    continue
                elif words[0] == 'data_optics':
                    relion31 = True
                    break
                elif words[0] == 'data_':
                    relion31 = False
                    break
                elif words[0][0] == '#':
                    # Comment line
                    continue
            assert relion31 is not None, f'The starfile {starfile} is invalid.'

            data_type = None
            if relion31:
                for line in f:
                    words = line.strip().split()
                    if len(words) == 0:
                        continue
                    elif len(words) == 1 and words[0].startswith('data_'):
                        data_type = words[0]
                        break
                assert data_type is not None, f'Could not determine the data type of this starfile.'

        # Load starfile
        if relion31:
            df_data, df_optics = cls._load_relion31(starfile, data_type)
        else:
            df_data = cls._load_relion(starfile)
            df_optics = None
        return cls(df_data, df_optics, starfile, data_type)

    @classmethod
    def _load_relion31(cls, starfile, data_type):
        """Load RELION 3.1 style starfile
        Parameters
        ----------
        starfile : string
            RELION 3.1 style star file
        data_type : string
            'data_particles' or 'data_micrographs'
        Returns
        -------
        df_data : pandas.DataFrame
            dataframe containing data block
        df_optics : pandas.DataFrame
            dataframe containing optics group data block.
        """

        with open(starfile, 'r') as f:
            headers_optics, data_optics = cls._read_block(f, 'data_optics')
            headers_data, data_data = cls._read_block(
                f, data_type)
        df_optics = pd.DataFrame(data_optics, columns=headers_optics)
        df_data = pd.DataFrame(data_data, columns=headers_data)
        return df_data, df_optics

    @classmethod
    def _load_relion(cls, starfile):
        """Load RELION 2.x/3.0 style starfile
        Parameters
        ----------
        starfile : string
            RELION 2.x/3.0 style starfile
        Returns
        -------
        pandas.DataFrame
            dataframe containing data block
        """

        with open(starfile, 'r') as f:
            headers, data = cls._read_block(f, 'data_')
        df = pd.DataFrame(data, columns=headers)
        return df

    @classmethod
    def _read_block(cls, f, blockname):
        """Read data block from starfile
        Parameters
        ----------
        f : file-like object
            File-like object of starfile
        blockname : string
            Data block name to read.
        Returns
        -------
        headers : list of strings
            Metadata labels
        body : ndarray
            Metadatas
        """

        # Get to the block (data_, data_optics, data_particles, etc...)
        for line in f:
            if line.startswith(blockname):
                break
        # Get to header loop
        for line in f:
            if line.startswith('loop_'):
                break
        # Get list of column headers
        headers = []
        for line in f:
            if line.startswith('_'):
                headers.append(line.strip().split()[0])
            else:
                break
        # All subsequent lines until empty line is the data block body
        body = [line.strip().split()]
        for line in f:
            if line.strip() == '':
                break
            else:
                body.append(line.strip().split())
        body = np.array(body)

        assert len(headers) == body.shape[1]
        return headers, body

    def write(self, outfile):
        """Save metadata in file
        Parameters
        ----------
        outfile : string
            Output file name. Should be .star file.
        """

        with open(outfile, 'w') as f:
            if self.df_optics is not None:
                self._write_block(f, 'data_optics', self.df_optics)
                self._write_block(f, self.data_type, self.df_data)
            else:
                self._write_block(f, 'data_', self.df_data)

    def _write_block(self, f, blockname, df):
        """Write data block as star format
        Parameters
        ----------
        f : File-like object
            Star file object
        blockname : string
            Data block name (e.g. data_optics)
        df : pandas.DataFrame
            DataFrame containing metadata labels and metadatas
        """

        f.write(blockname.strip())
        f.write('\n\n')
        f.write('loop_\n')
        f.write('\n'.join(df.columns))
        f.write('\n')
        for i in df.index:
            f.write(' '.join(df.loc[i]))
            f.write('\n')
        f.write('\n')

    def iloc(self, idxs):
        """Fancy indexing.
        Parameters
        ----------
        idxs : array-like
            Indices to select.
        Returns
        -------
        RelionMetaData
            New metadata object with the selected rows.
        """

        df_data_new = self.df_data.iloc[idxs]
        return self.__class__(df_data=df_data_new,
                              df_optics=self.df_optics,
                              data_type=self.data_type)
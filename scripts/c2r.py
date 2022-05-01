"""c2r common module
"""

import sys
import numpy as np
import pandas as pd

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
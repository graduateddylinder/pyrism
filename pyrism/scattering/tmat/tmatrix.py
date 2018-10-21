import numpy as np
from radarpy import Angles, asarrays, align_all, wavenumber

from .tm_psd import TMatrixPSD
from .tm_single import TMatrixSingle

PI = 3.14159265359


class TMatrix(Angles):

    def __init__(self, iza, vza, iaa, vaa, frequency, radius, eps, alpha=0.0, beta=0.0,
                 radius_type='REV', shape='SPH', orientation='S', axis_ratio=1.0, orientation_pdf=None, n_alpha=5,
                 n_beta=10,
                 angle_unit='DEG', frequency_unit='GHz', psd=None, max_radius=10, num_points=1024,
                 angular_integration=True, normalize=False, nbar=0.0):

        """T-Matrix scattering from nonspherical particles.

        Class for simulating scattering from nonspherical particles with the
        T-Matrix method. Uses a wrapper to the Fortran code by M. Mishchenko.

        Parameters
        ----------
        iza, vza, iaa, vaa : int, float or array_like
            Incidence (iza) and scattering (vza) zenith angle and incidence and viewing
            azimuth angle (ira, vra) in [DEG] or [RAD] (see parameter angle_unit).
        frequency : int float or array_like
            The frequency of incident EM Wave in {'Hz', 'MHz', 'GHz', 'THz'} (see parameter frequency_unit).
        radius : int float or array_like
            Equivalent particle radius in [cm].
        radius_type : {'EV', 'M', 'REA'}
            Specification of particle radius:
                * 'REV': radius is the equivalent volume radius (default).
                * 'M': radius is the maximum radius.
                * 'REA': radius is the equivalent area radius.
        eps : complex
            The complex refractive index.
        axis_ratio : int or float
            The horizontal-to-rotational axis ratio.
        shape : {'SPH', 'CYL'}
            Shape of the particle:
                * 'SPH' : spheroid,
                * 'CYL' : cylinders.
        alpha, beta: int, float or array_like
            The Euler angles of the particle orientation in [DEG] or [RAD] (see parameter angle_unit).
        orientation : {'S', 'AA', 'AF'}
            The function to use to compute the orientational scattering properties:
                * 'S': Single (default).
                * 'AA': Averaged Adaptive
                * 'AF': Averaged Fixed.
        orientation_pdf: {'gauss', 'uniform'}
            Particle orientation Probability Density Function (PDF) for orientational averaging:
                * 'gauss': Use a Gaussian PDF (default).
                * 'uniform': Use a uniform PDR.
        n_alpha : int
            Number of integration points in the alpha Euler angle. Default is 5.
        n_beta : int
            Umber of integration points in the beta Euler angle. Default is 10.
        angle_unit : {'DEG', 'RAD'}, optional
            * 'DEG': All input angles (iza, vza, raa) are in [DEG] (default).
            * 'RAD': All input angles (iza, vza, raa) are in [RAD].
        frequency_unit : {'Hz', 'MHz', 'GHz', 'THz'}
            Unit of entered frequency. Default is 'GHz'.
        psd : callable or None
            Particle Size Distribution Function (PSD). See pyrism.PSD. If None (default) a particle distribution
        num_points : int
            The number of points for which to sample the PSD and
            scattering properties for; default num_points=1024 should be good
            for most purposes
        angular_integration : bool
            If True, also calculate the angle-integrated quantities (scattering cross section,
            extinction cross section, asymmetry parameter). The default is True.
         max_radius : int, float or None:
            Maximum diameter to consider. If None (default) max_radius will be approximated by the PSD functions.
        N : int
            Amount of scatterer. Default is 1.
        normalize : boolean, optional
            Set to 'True' to make kernels 0 at nadir view illumination. Since all implemented kernels are normalized
            the default value is False.
        nbar : float, optional
            The sun or incidence zenith angle at which the isotropic term is set
            to if normalize is True. The default value is 0.0.

        Returns
        -------
        TMatrix.S : array_like
            Complex Scattering Matrix.
        TMatrix.Z : array_like
            Phase Matrix.
        TMatrix.SZ : tuple
             Complex Scattering Matrix and Phase Matrix.
        TMatrix.ksi : tuple
            Scattering intensity for VV and HH polarization.
        TMatrix.ksx : tuple
            Scattering Cross Section for VV and HH polarization.
        TMatrix.kex : tuple
            Extinction Cross Section for VV and HH polarization.
        TMatrix.asx : tuple
            Asymetry Factor for VV and HH polarization.
        TMatrix.save_scatter_table : None
            Save all results to a file. This only works if psd is defined.

        See Also
        --------
        radarpy.Angles
        pyrism.PSD

        """

        # ---- Select single or psd T-Matrix approach ----
        if psd is None:
            self.TM = TMatrixSingle(iza=iza, vza=vza, iaa=iaa, vaa=vaa, frequency=frequency, radius=radius,
                                    eps=eps,
                                    alpha=alpha, beta=beta, radius_type=radius_type, shape=shape,
                                    orientation=orientation, axis_ratio=axis_ratio, orientation_pdf=orientation_pdf,
                                    n_alpha=n_alpha,
                                    n_beta=n_beta, angle_unit=angle_unit, frequency_unit=frequency_unit,
                                    normalize=normalize, nbar=nbar)
            self.psd = None
            self.__NAME = 'SINGLE'

        else:
            self.TM = TMatrixPSD(iza=iza, vza=vza, iaa=iaa, vaa=vaa, frequency=frequency, radius=radius,
                                 eps=eps,
                                 alpha=alpha, beta=beta, radius_type=radius_type, shape=shape,
                                 orientation=orientation, axis_ratio=axis_ratio, orientation_pdf=orientation_pdf,
                                 n_alpha=n_alpha,
                                 n_beta=n_beta, angle_unit=angle_unit, frequency_unit=frequency_unit,

                                 psd=psd, num_points=num_points, angular_integration=angular_integration,
                                 max_radius=max_radius, normalize=normalize, nbar=nbar)

            self.__NAME = 'PSD'

            # Access data from the specific parent class.
            self.psd = self.TM.psd
            self.num_points = self.TM.num_points
            self.D_max = self.TM.D_max
            self.angular_integration = self.TM.angular_integration

            self._S_table = self.TM._S_table
            self._Z_table = self.TM._Z_table
            self._angular_table = self.TM._angular_table

            self._psd_D = self.TM._psd_D

        # ---- Define angles and align data ----
        iza, vza, iaa, vaa, frequency, radius, axis_ratio, alpha, beta = asarrays(
            (iza, vza, iaa, vaa, frequency, radius, axis_ratio, alpha, beta))

        iza, vza, iaa, vaa, frequency, radius, axis_ratio, alpha, beta = align_all(
            (iza, vza, iaa, vaa, frequency, radius, axis_ratio, alpha, beta))

        Angles.__init__(self, iza=iza, vza=vza, raa=None, iaa=iaa, vaa=vaa, alpha=alpha, beta=beta,
                        normalize=normalize, angle_unit=angle_unit, nbar=nbar)

        # ---- Access data from parent class ----
        self.normalize = normalize
        self.radius = self.TM.radius
        self.radius_type = self.TM.radius_type

        self.frequency = self.TM.frequency
        self.wavelength = self.TM.wavelength
        self.eps = self.TM.eps
        self.axis_ratio = self.TM.axis_ratio
        self.shape = self.TM.shape
        self.ddelt = self.TM.ddelt
        self.ndgs = self.TM.ndgs
        self.alpha = self.TM.alpha
        self.beta = self.TM.beta
        self.orient = self.TM.orient

        self.or_pdf = self.TM.or_pdf
        self.n_alpha = self.TM.n_alpha
        self.n_beta = self.TM.n_beta
        self.orientation_pdf = orientation_pdf

        # ---- Pre-calculation for extinction matrix ----
        self.k0 = wavenumber(self.frequency, unit=frequency_unit, output='cm')
        self.a = self.k0 * radius

        self.nmax = self.TM.nmax
        self.factor = complex(0, 2 * PI * self.nmax.mean()) / self.k0


    # ---- Property calls ----
    @property
    def norm(self):
        """
        Normalization matrix. The values for iza = nbar, vza = 0.

        Returns
        -------
        Norm : list or array_like
        """
        return self.TM.norm

    @property
    def S(self):
        """
        Scattering matrix.

        Returns
        -------
        S : list or array_like
        """
        return self.TM.S

    @property
    def Z(self):
        """
        Phase matrix.

        Returns
        -------
        Z : list or array_like
        """
        return self.TM.Z

    @property
    def SZ(self):
        """
        Scattering and phase matrices.

        Returns
        -------
        S, Z : list or array_like
        """
        return self.TM.SZ

    @property
    def ke(self):
        """
        Extinction matrix for the current setup, with polarization.

        Returns
        -------
        VV, HH : list or array_like

        """
        try:
            if len(self.__ke) == 1:
                return self.__ke[0]
            else:
                return self.__ke

        except AttributeError:

            self.__ke = self.__get_ke()

            if len(self.__ke) == 1:
                return self.__ke[0]
            else:
                return self.__ke

    @property
    def ks(self):
        """
        Scattering matrix for the current setup, with polarization.

        Returns
        -------
        VV, HH : list or array_like

        """
        try:
            if len(self.__ks) == 1:
                return self.__ks[0]
            else:
                return self.__ks

        except (AttributeError, TypeError):

            self.__ks = self.__get_ks()

            if len(self.__ks) == 1:
                return self.__ks[0]
            else:
                return self.__ks

    @property
    def ka(self):
        """
        Absorption matrix for the current setup, with polarization.

        Returns
        -------
        VV, HH : list or array_like

        """
        try:
            if len(self.__ka) == 1:
                return self.__ka[0]
            else:
                return self.__ka

        except (AttributeError, TypeError):

            self.__ka = self.__get_ka()

            if len(self.__ka) == 1:
                return self.__ka[0]
            else:
                return self.__ka

    @property
    def omega(self):
        """
        Single scattering albedo matrix for the current setup, with polarization.

        Returns
        -------
        VV, HH : list or array_like

        """
        try:
            if len(self.__omega) == 1:
                return self.__omega[0]
            else:
                return self.__omega

        except (AttributeError, TypeError):

            self.__omega = self.__get_omega()

            if len(self.__omega) == 1:
                return self.__omega[0]
            else:
                return self.__omega

    @property
    def kt(self):
        """
        Transmission matrix for the current setup, with polarization.

        Returns
        -------
        VV, HH : list or array_like

        """
        try:
            if len(self.__kt) == 1:
                return self.__kt[0]
            else:
                return self.__kt

        except AttributeError:

            self.__kt = self.__get_kt()

            if len(self.__kt) == 1:
                return self.__kt[0]
            else:
                return self.__kt

    @property
    def kex(self):
        """
        Extinction cross section for the current setup, with polarization.

        Returns
        -------
        VV, HH : list or array_like

        """
        return self.TM.kex

    @property
    def ksx(self):
        """
        Scattering cross section for the current setup, with polarization.

        Returns
        -------
        VV, HH : list or array_like

        """
        return self.TM.ksx

    @property
    def ksi(self):
        """
        Scattering intensity (phase function) for the current setup.

        Returns
        -------
        VV, HH : list or array_like

        """
        if self.__NAME is 'SINGLE':
            return self.TM.ksi
        else:
            return None

    @property
    def asx(self):
        """
        Asymetry factor cross section for the current setup, with polarization.

        Returns
        -------
        VV, HH : list or array_like

        """
        return self.TM.asx

    @property
    def dblquad(self):
        """
        Half space integration of the phase matrices.

        Returns
        -------
        dbl : list or array_like
        """
        if self.__NAME is 'SINGLE':
            return self.TM.dblquad
        else:
            return None

    # ---- User callable methods ----
    def ifunc_Z(self, iza, iaa, vzaDeg, vaaDeg, alphaDeg, betaDeg, nmax, wavelength, pol=None):
        """
        Function to integrate the phase matrix which is compatible with scipy.integrate.dblquad.

        Parameters
        ----------
        iza, iaa : float
            x and y value of integration (0, pi) and (0, 2*pi) in [RAD], respectively.
        vzaDeg, vaaDeg, alphaDeg, betaDeg: int, float or array_like
            Scattering (vza) zenith angle and viewing azimuth angle (vaa) in [DEG]. Parameter alphaDeg and betaDeg
            are the Euler angles of the particle orientation in [DEG].
        pol : int or None
            Polarization:
                * 0 : VV
                * 1 : HH
                * None (default) : Both.

        Examples
        --------
        scipy.integrate.dblquad(TMatrix.ifunc_Z, 0, 360.0, lambda x: 0.0, lambda x: 180.0, args=(*args ))

        Returns
        -------
        Z : float

        """

        return self.TM.ifunc_Z(iza, iaa, vzaDeg, vaaDeg, alphaDeg, betaDeg, nmax, wavelength, pol)

    def Mpq(self, factor, S):
        """
        Mpq parameter to calculate the extinction matrix.

        Parameters
        ----------
        factor : float
            The factor (i*2*pi)/k0
        S : float
            Element of the scattering matrix.

        Returns
        -------
        Mpq : array_like
        """
        return factor * S

    def init_SZ(self, verbose=False):
        """Initialize the scattering and phase lookup tables.

        Initialize the scattering lookup tables for the different geometries.

        Parameters
        ----------
        verbose : bool
            Print calculation steps.

        Returns
        -------
        None
        """
        if self.__NAME is 'PSD':
            self.TM.init_SZ(verbose)
        else:
            return None

    # ---- Auxiliary functions and private methods ----
    def __get_kt(self):
        self.__kt = list()

        ke = self.ke

        if isinstance(ke, list):
            for item in ke:
                self.__kt.append(1 - item)
        else:
            self.__kt.append(1 - ke)

        return self.__kt

    def __get_ks(self):
        ks_list = list()
        ke = self.ke
        omega = self.omega
        if isinstance(omega, list):

            for i in range(len(omega)):
                ksm = np.zeros((4, 4))

                ksm[0, 0] = self.omega[i][0, 0] * ke[i][0, 0]
                ksm[1, 1] = self.omega[i][1, 1] * ke[i][1, 1]

                ks_list.append(ksm)

        else:
            ksm = np.zeros((4, 4))

            ksm[0, 0] = omega[0, 0] * ke[0, 0]
            ksm[1, 1] = omega[1, 1] * ke[1, 1]

            ks_list.append(ksm)

        return ks_list

    def __get_ka(self):
        ka_list = list()
        ks = self.ks
        omega = self.omega

        if isinstance(omega, list):

            for i in range(len(omega)):
                kam = np.zeros((4, 4))

                kam[0, 0] = (ks[i][0, 0] - omega[i][0, 0] * ks[i][0, 0]) / omega[i][0, 0]
                kam[1, 1] = (ks[i][1, 1] - omega[i][1, 1] * ks[i][1, 1]) / omega[i][1, 1]

                ka_list.append(kam)

        else:
            kam = np.zeros((4, 4))

            kam[0, 0] = (ks[0, 0] - omega[0, 0] * ks[0, 0]) / omega[0, 0]
            kam[1, 1] = (ks[1, 1] - omega[1, 1] * ks[1, 1]) / omega[1, 1]

            ka_list.append(kam)

        return ka_list

    def __get_ke(self):
        self.__ke = list()

        if isinstance(self.TM.S, list):

            for i in range(len(self.TM.S)):
                kem = np.zeros((4, 4))

                kem[0, 0] = -2 * self.Mpq(self.factor[i], self.TM.S[i][0, 0]).real
                kem[0, 1] = 0
                kem[0, 2] = -self.Mpq(self.factor[i], self.TM.S[i][0, 1]).real
                kem[0, 3] = -self.Mpq(self.factor[i], self.TM.S[i][0, 0]).imag

                kem[1, 0] = 0
                kem[1, 1] = -2 * self.Mpq(self.factor[i], self.TM.S[i][1, 1]).real
                kem[1, 2] = -self.Mpq(self.factor[i], self.TM.S[i][1, 0]).real
                kem[1, 3] = -self.Mpq(self.factor[i], self.TM.S[i][1, 0]).imag

                kem[2, 0] = -2 * self.Mpq(self.factor[i], self.TM.S[i][1, 0]).real
                kem[2, 1] = -2 * self.Mpq(self.factor[i], self.TM.S[i][0, 1]).real
                kem[2, 2] = -(self.Mpq(self.factor[i], self.TM.S[i][0, 0]).real + self.Mpq(self.factor[i],
                                                                                           self.TM.S[i][1, 1]).real)
                kem[2, 3] = (self.Mpq(self.factor[i], self.TM.S[i][0, 0]).imag - self.Mpq(self.factor[i],
                                                                                          self.TM.S[i][1, 1]).imag)

                kem[3, 0] = 2 * self.Mpq(self.factor[i], self.TM.S[i][1, 0]).imag
                kem[3, 1] = -2 * self.Mpq(self.factor[i], self.TM.S[i][0, 1]).imag
                kem[3, 2] = -(self.Mpq(self.factor[i], self.TM.S[i][0, 0]).imag - self.Mpq(self.factor[i],
                                                                                           self.TM.S[i][1, 1]).imag)
                kem[3, 3] = -(self.Mpq(self.factor[i], self.TM.S[i][0, 0]).real + self.Mpq(self.factor[i],
                                                                                           self.TM.S[i][1, 1]).real)

                self.__ke.append(kem)

        else:
            self.__ke = list()
            kem = np.zeros((4, 4))

            kem[0, 0] = -2 * self.Mpq(self.factor, self.TM.S[0, 0]).real
            kem[0, 1] = 0
            kem[0, 2] = -self.Mpq(self.factor, self.TM.S[0, 1]).real
            kem[0, 3] = -self.Mpq(self.factor, self.TM.S[0, 0]).imag

            kem[1, 0] = 0
            kem[1, 1] = -2 * self.Mpq(self.factor, self.TM.S[1, 1]).real
            kem[1, 2] = -self.Mpq(self.factor, self.TM.S[1, 0]).real
            kem[1, 3] = -self.Mpq(self.factor, self.TM.S[1, 0]).imag

            kem[2, 0] = -2 * self.Mpq(self.factor, self.TM.S[1, 0]).real
            kem[2, 1] = -2 * self.Mpq(self.factor, self.TM.S[0, 1]).real
            kem[2, 2] = -(self.Mpq(self.factor, self.TM.S[0, 0]).real + self.Mpq(self.factor, self.TM.S[1, 1]).real)
            kem[2, 3] = (self.Mpq(self.factor, self.TM.S[0, 0]).imag - self.Mpq(self.factor, self.TM.S[1, 1]).imag)

            kem[3, 0] = 2 * self.Mpq(self.factor, self.TM.S[1, 0]).imag
            kem[3, 1] = -2 * self.Mpq(self.factor, self.TM.S[0, 1]).imag
            kem[3, 2] = -(self.Mpq(self.factor, self.TM.S[0, 0]).imag - self.Mpq(self.factor, self.TM.S[1, 1]).imag)
            kem[3, 3] = -(self.Mpq(self.factor, self.TM.S[0, 0]).real + self.Mpq(self.factor, self.TM.S[1, 1]).real)

            self.__ke.append(kem)

        return self.__ke

    def __get_asx(self):

        if self.__NAME is 'SINGLE':
            return self.TM.asx

        else:
            try:
                if isinstance(self.geometriesDeg[0], tuple):
                    VV, HH = list(), list()

                    for item in self.geometriesDeg:
                        VV_temp, HH_temp = self.TM.asx(item)

                        VV.append(VV_temp)
                        HH.append(HH_temp)

                    return VV, HH

                else:
                    return self.TM.asx(self.geometriesDeg)

            except AttributeError:
                print("Initialising angular-integrated quantities first.")
                self.TM.init_SZ()

                if isinstance(self.geometriesDeg[0], tuple):
                    VV, HH = list(), list()

                    for item in self.geometriesDeg:
                        VV_temp, HH_temp = self.TM.asx(item)

                        VV.append(VV_temp)
                        HH.append(HH_temp)

                    return VV, HH

                else:
                    return self.TM.asx(self.geometriesDeg)

    def __get_ksx(self):
        if self.__NAME is 'SINGLE':
            return self.TM.ksx

        else:
            try:
                if isinstance(self.geometriesDeg[0], tuple):
                    VV, HH = list(), list()

                    for item in self.geometriesDeg:
                        VV_temp, HH_temp = self.TM.ksx(item)

                        VV.append(VV_temp)
                        HH.append(HH_temp)

                    return VV, HH

                else:
                    return self.TM.ksx(self.geometriesDeg)

            except AttributeError:
                print("Initialising angular-integrated quantities first.")
                self.TM.init_SZ()

                if isinstance(self.geometriesDeg[0], tuple):
                    VV, HH = list(), list()

                    for item in self.geometriesDeg:
                        VV_temp, HH_temp = self.TM.ksx(item)

                        VV.append(VV_temp)
                        HH.append(HH_temp)

                    return VV, HH

                else:
                    return self.TM.ksx(self.geometriesDeg)

    def __get_kex(self):
        if self.__NAME is 'SINGLE':
            return self.TM.kex

        else:
            try:
                if isinstance(self.geometriesDeg[0], tuple):
                    VV, HH = list(), list()

                    for item in self.geometriesDeg:
                        VV_temp, HH_temp = self.TM.kex(item)

                        VV.append(VV_temp)
                        HH.append(HH_temp)

                    return VV, HH

                else:
                    return self.TM.kex(self.geometriesDeg)

            except AttributeError:
                print("Initialising angular-integrated quantities first.")
                self.TM.init_SZ()

                if isinstance(self.geometriesDeg[0], tuple):
                    VV, HH = list(), list()

                    for item in self.geometriesDeg:
                        VV_temp, HH_temp = self.TM.kex(item)

                        VV.append(VV_temp)
                        HH.append(HH_temp)

                    return VV, HH

                else:
                    return self.TM.kex(self.geometriesDeg)

    def __get_omega(self):
        ksVV, ksHH = self.ksx
        keVV, keHH = self.kex
        omega_list = list()

        try:
            slen = len(ksVV)
        except TypeError:
            slen = 0

        if slen > 1:

            for i in range(len(ksVV)):
                omega = np.zeros((4, 4))

                omega[0, 0] = ksVV[i] / keVV[i]
                omega[1, 1] = ksHH[i] / keHH[i]

                omega_list.append(omega)

        else:
            ksm = np.zeros((4, 4))

            ksm[0, 0] = ksVV / keVV
            ksm[1, 1] = ksHH / keHH

            omega_list.append(ksm)

        return omega_list

    def __get_ksi(self):
        if self.__NAME is 'SINGLE':
            return self.TM.ksi

        else:
            return None

    # @classmethod
    # def load_scatter_table(cls, fn=None):
    #     """Load the scattering lookup tables.
    #
    #     Load the scattering lookup tables saved with save_scatter_table.
    #
    #     Args:
    #         fn: The name of the scattering table file.
    #     """
    #     if fn is None:
    #         fn = Files.select_newest()
    #         data = pickle.load(open(os.path.join(Files.path, fn)))
    #     else:
    #         data = pickle.load(open(fn))
    #
    #     if ("version" not in data) or (data["version"] != get_version()):
    #         warnings.warn("Loading data saved with another version.", Warning)
    #
    #     (cls.num_points, cls.D_max, cls._psd_D, cls._S_table, cls._Z_table, cls._angular_table, cls._m_table,
    #      cls.geometriesDeg) = data["psd_scatter"]
    #
    #     (cls.izaDeg, cls.vzaDeg, cls.iaaDeg, cls.vaaDeg, cls.angular_integration, cls.radius, cls.radius_type,
    #      cls.wavelength, cls.eps, cls.axis_ratio, cls.shape, cls.ddelt, cls.ndgs, cls.alpha, cls.beta, cls.orient,
    #      cls.or_pdf, cls.n_alpha, cls.n_beta, cls.psd) = data["parameter"]
    #
    #     print("File {0} load successfully.".format(str(fn)))
    #
    #     return (data["time"], data["description"])

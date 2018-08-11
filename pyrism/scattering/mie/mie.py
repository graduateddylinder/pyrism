from .core.mie_scatt import mie_scattering
import warnings
import numpy as np
from ...core import Kernel
import sys

# python 3.6 comparability
if sys.version_info < (3, 0):
    srange = xrange
else:
    srange = range


class Mie(object):
    """
    Calculate the extinction coefficients in terms of Rayleigh
    scattering (:cite:`Ulaby.2015` and :cite:`Ulaby.2015b`).

    Parameters
    ----------
    frequency : int or float
        Frequency (GHz)
    radius : int, float or array
        Particle size a [m].
    eps_p : complex
        Dielectric constant of the medium (a + bj).
    eps_b : complex
        Dielectric constant of the background a + bj).

    Returns
    -------
    All returns are attributes!
    self.ke : int, float or array_like
        Extinction coefficient.
    self.ks : int, float or array_like
        Scattering coefficient.
    self.ka : int, float or array_like
        Absorption coefficient.
    self.omega : int, float or array_like
        Single scattering albedo.
    self.BSC : int, float or array_like
        Backscatter coefficient sigma 0.
    """

    def __init__(self, frequency, radius, eps_p, eps_b=(1 + 1j)):

        # Check validity

        radius = radius / 100

        lm = 299792458 / (frequency * 1e9)  # Wavelength in meter
        self.condition = (2 * np.pi * radius) / lm

        if np.any(self.condition < 0.5):
            warnings.warn("Mie condition not holds. You schould use Rayleigh scattering.", Warning)
        else:
            pass

        self.ks, self.ka, self.kt, self.ke, self.omega, self.BSC = mie_scattering(frequency, radius, eps_p, eps_b)

    def __str__(self):
        vals = dict()
        vals['cond'], vals['ks'], vals['ka'], vals['kt'], vals['ke'], vals[
            'omega'], vals['bsc'] = self.condition, self.ks, self.ka, self.kt, self.ke, self.omega, self.BSC

        info = 'Class                      : Mie\n' \
               'Particle size              : {cond}\n' \
               'Scattering Coefficient     : {ks}\n' \
               'Absorption Coefficient     : {ka}\n' \
               'Transmission Coefficient   : {kt}\n' \
               'Extinction Coefficient     : {ke}\n' \
               'Backscattering Coefficient : {bsc}\n' \
               'Single Scattering Albedo   : {omega}'.format(**vals)

        return info
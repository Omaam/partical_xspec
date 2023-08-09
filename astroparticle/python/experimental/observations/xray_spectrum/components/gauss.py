"""Energy spectrum component model module.
"""
import math

import tensorflow as tf

from astroparticle.python.experimental.observations.\
    xray_spectrum.components.physical_component import PhysicalComponent
from astroparticle.python.experimental.observations.\
    xray_spectrum.components import util as comp_util


def gauss(energy, line_energy, line_width, norm):
    """Compute probability density for gauss function.

    A(E) = K * 1/(sigma * sqrt(2*pi)) exp(-(E-El)^2)/ 2*sigma^2)
    """
    return norm / line_width / tf.sqrt(2*math.pi) * tf.exp(
        -(energy - line_energy)**2 / 2 / line_width**2)


class Gauss(PhysicalComponent):
    def __init__(self,
                 energy_intervals,
                 energy_line=6.4,
                 energy_width=0.1,
                 normalization=1.0,
                 name="normalization"):
        with tf.name_scope(name) as name:

            self.energy_line = tf.convert_to_tensor(energy_line)
            self.energy_width = tf.convert_to_tensor(energy_width)
            self.normalization = tf.convert_to_tensor(normalization)

            super(Gauss, self).__init__(
                energy_intervals_input=energy_intervals,
                energy_intervals_output=energy_intervals
            )

    def _forward(self, flux):
        """Forward to calculate flux.
        """
        # TODO: Many uses of `tf.newaxis` make a mess.
        # Find another tider way.
        energy_intervals = self.energy_intervals_input[tf.newaxis, ...]
        energy_line = self.energy_line[:, tf.newaxis, tf.newaxis]
        energy_width = self.energy_width[:, tf.newaxis]
        norm = self.normalization[:, tf.newaxis]
        print("enegy_intervals: {}".format(energy_intervals.shape))
        print("enegy_line: {}".format(energy_line.shape))
        print("enegy_width: {}".format(energy_width.shape))
        print("norm: {}".format(norm.shape))

        def _gauss_with_param(energy_edges):
            return gauss(energy_edges, energy_line, energy_width, norm)

        print(comp_util.compute_section_trapezoidal(
            energy_intervals, _gauss_with_param).shape)

        new_flux = norm * comp_util.compute_section_trapezoidal(
            energy_intervals, _gauss_with_param)

        flux = flux + new_flux
        return flux

    def set_parameter(self, x):
        x = tf.unstack(x, axis=-1)
        self.energy_line = x[0]
        self.energy_width = x[1]
        self.normalization = x[2]

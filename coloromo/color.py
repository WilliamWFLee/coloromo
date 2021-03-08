#!/usr/bin/env python3

"""
coloromo.color

MIT License

Copyright (c) 2021 William Lee

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import math as m
from typing import Iterable, Set

from .types import Color, FloatColor, Int

__all__ = ["Palette"]


class CIE:
    """
    A helper class of static methods for CIE-related functions
    """

    SRGB_TO_CIEXYZ_MATRIX = [
        [0.41239080, 0.35758434, 0.18048079],
        [0.21263901, 0.71516868, 0.07219232],
        [0.01933082, 0.11919478, 0.95053215],
    ]

    # Values for standard illuminant D65
    X_n = 0.950489
    Y_n = 1
    Z_n = 1.08884

    # Constants for CIEXYZ to CIELAB
    SIGMA = 6 / 29
    SIGMA_SQUARED = SIGMA ** 2
    SIGMA_CUBED = SIGMA ** 3
    ONE_THIRD = 1 / 3
    FOUR_TWENTYNINTHS = 4 / 29
    TWENTY_FIVE_POWER_SEVEN = 25 ** 7

    # Constants for CIEDE2000
    TAU = 2 * m.pi
    K_L = K_C = K_H = 1

    @classmethod
    def _srgb_to_ciexyz(cls, r: Int, g: Int, b: Int) -> FloatColor:
        # Converts sRGB to CIEXYZ

        def inverse_gamma(u):
            # Implements inverse gamma for gamma expansion
            return u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4

        # RGB components are scaled to [0, 1]
        # and have the inverse gamma function applied
        r, g, b = (inverse_gamma(v / 255) for v in (r, g, b))
        # Linearised RGB values are converted to CIEXYZ by linear transformation
        x, y, z = (
            sum(v * w for w in row)
            for v, row in zip((r, g, b), cls.SRGB_TO_CIEXYZ_MATRIX)
        )
        return (x, y, z)

    @classmethod
    def _ciexyz_to_cielab(cls, x: float, y: float, z: float) -> FloatColor:
        # Converts CIEXYZ to CIELAB

        def f(t):
            return (
                t ** cls.ONE_THIRD
                if t > cls.SIGMA_CUBED
                else (t * cls.ONE_THIRD / cls.SIGMA_SQUARED + cls.FOUR_TWENTYNINTHS)
            )

        f_x = f(x / cls.X_n)
        f_y = f(y / cls.Y_n)
        f_z = f(z / cls.Z_n)

        L = 116 * f_y - 16
        a = 500 * (f_x - f_y)
        b = 200 * (f_y - f_z)

        return (L, a, b)

    @classmethod
    def srgb_to_cielab(cls, r: Int, g: Int, b: Int) -> FloatColor:
        """
        Takes an RGB color value, which each component in the range 0-255
        and converts to a CIELAB color value.

        RGB colors are assumed to be in the sRGB color space.

        :param r: The red value of the color
        :type r: Int
        :param g: The green value of the color
        :type g: Int
        :param b: The blue value of the color
        :type b: Int
        :return: The equivalent CIELAB color value
        :rtype: FloatColor
        """
        L, a, b = cls._ciexyz_to_cielab(*cls._srgb_to_ciexyz(r, g, b))
        return (L, a, b)

    @classmethod
    def radians_to_degrees(cls, angle: float) -> float:
        """
        Converts radians to degrees, accepting values between -pi and pi.

        :raises ValueError: If the angle is not between -pi and pi.
        :return: The angle in degrees, in the range 0 to 360
        :rtype: float
        """
        if angle > m.pi or angle < -m.pi:
            raise ValueError("Angle must be between -pi and pi")
        return m.degrees(angle if angle >= 0 else angle + cls.TAU)

    @classmethod
    def _ciede2000(
        cls,
        L_1: float,
        a_1: float,
        b_1: float,
        L_2: float,
        a_2: float,
        b_2: float,
    ) -> float:
        # Calculates the CIEDE2000 color difference value between two CIELAB colors
        # Source: http://www2.ece.rochester.edu/~gsharma/ciede2000/ciede2000noteCRNA.pdf

        C_star_1_ab = (a_1 ** 2 + b_1 ** 2) ** 0.5
        C_star_2_ab = (a_2 ** 2 + b_2 ** 2) ** 0.5

        C_star_ab_bar = (C_star_1_ab + C_star_2_ab) / 2

        # Equal to G + 1
        G_plus = 1 + 0.5 * (
            1 - (1 / (1 + cls.TWENTY_FIVE_POWER_SEVEN / C_star_ab_bar ** 7)) ** 0.5
        )
        a_prime_1 = G_plus * a_1
        a_prime_2 = G_plus * a_2

        C_prime_1 = (a_prime_1 ** 2 + b_1 ** 2) ** 0.5
        C_prime_2 = (a_prime_2 ** 2 + b_2 ** 2) ** 0.5

        h_prime_1 = (
            0
            if b_1 == 0 and a_prime_1 == 0
            else cls.radians_to_degrees(m.atan2(b_1, a_prime_1))
        )
        h_prime_2 = (
            0
            if b_2 == 0 and a_prime_2 == 0
            else cls.radians_to_degrees(m.atan2(b_2, a_prime_2))
        )

        Delta_L_prime = L_2 - L_1
        Delta_C_prime = C_prime_2 - C_prime_1

        # Optimisations
        h_prime_diff = h_prime_2 - h_prime_1
        abs_h_prime_diff = abs(h_prime_diff)

        if C_prime_1 == 0 or C_prime_2 == 0:
            Delta_h_prime = 0
        elif abs_h_prime_diff <= 180:
            Delta_h_prime = h_prime_diff
        elif h_prime_diff > 180:
            Delta_h_prime = h_prime_diff - 360
        else:
            Delta_h_prime = h_prime_diff + 360

        Delta_H_prime = (
            2 * (C_prime_1 * C_prime_2) ** 0.5 * m.sin(m.radians(Delta_h_prime / 2))
        )

        L_prime_bar = (L_1 + L_2) / 2
        C_prime_bar = (C_prime_1 + C_prime_2) / 2

        # An optimisation
        h_prime_sum = h_prime_1 + h_prime_2
        if C_prime_1 == 0 or C_prime_2 == 0:
            h_prime_bar = h_prime_sum
        elif abs_h_prime_diff <= 180:
            h_prime_bar = h_prime_sum / 2
        elif h_prime_sum < 360:
            h_prime_bar = (h_prime_sum + 360) / 2
        else:
            h_prime_bar = (h_prime_sum - 360) / 2

        T = (
            1
            - 0.17 * m.cos(m.radians(h_prime_bar - 30))
            + 0.24 * m.cos(m.radians(2 * h_prime_bar))
            + 0.32 * m.cos(m.radians(3 * h_prime_bar + 6))
            - 0.2 * m.cos(m.radians(4 * h_prime_bar - 63))
        )

        Delta_theta = 30 * m.exp(-(((h_prime_bar - 275) / 25) ** 2))
        R_C = 2 * (1 / (1 + cls.TWENTY_FIVE_POWER_SEVEN / C_prime_bar ** 7)) ** 0.5
        S_L = (
            1
            + (0.015 * (L_prime_bar - 50) ** 2) / (20 + (L_prime_bar - 50) ** 2) ** 0.5
        )
        S_C = 1 + 0.045 * C_prime_bar
        S_H = 1 + 0.015 * C_prime_bar * T
        R_T = -m.sin(m.radians(2 * Delta_theta)) * R_C

        Delta_E = (
            (Delta_L_prime / (cls.K_L * S_L)) ** 2
            + (Delta_C_prime / (cls.K_C * S_C)) ** 2
            + (Delta_H_prime / (cls.K_H * S_H)) ** 2
            + (
                R_T
                * (Delta_C_prime / (cls.K_C * S_C))
                * (Delta_H_prime / (cls.K_H * S_H))
            )
        ) ** 0.5

        return Delta_E


class Palette:
    """
    A class for holding a palette of colors.
    """

    def __init__(self):
        self.colors: Set[Color] = set()

    def add(self, colors: Iterable[Color]):
        """
        Add colors to the palette

        :param colors: An iterable of color tuples to add to the palette
        :type colors: Iterable[Color]
        """
        self.colors.update(*colors)

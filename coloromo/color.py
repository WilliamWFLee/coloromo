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

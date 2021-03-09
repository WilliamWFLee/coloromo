#!/usr/bin/env python3

"""
coloromo - Image color palette reduction

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

from pathlib import Path
from typing import BinaryIO, Optional, Union

import numpy as np
from PIL import Image

from .color import Palette


class Coloromo:
    """
    A class for performing image palette reductions.
    """

    def __init__(self, palette: Optional[Palette] = None):
        self.palette = palette if palette else Palette()

    def reduce_image(
        self, image: Union[str, Path, BinaryIO, Image.Image]
    ) -> Image.Image:
        if isinstance(image, (str, Path, BinaryIO)):
            image = Image.open(image)
        image_data = [
            [tuple(pixel) for pixel in row] for row in np.array(image).tolist()
        ]
        reduced_image_data = [
            [self.palette.find_nearest(pixel) for pixel in row] for row in image_data
        ]
        reduced_image = Image.fromarray(np.array(reduced_image_data, dtype=np.uint8))
        return reduced_image

#!/usr/bin/env python
#
#    Copyright 2016 Jose Luis Cercos-Pita
#
#    This file is part of Panda3D-mapzen.
#
#    Panda3D-mapzen is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Panda3D-mapzen is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Panda3D-mapzen.  If not, see <http://www.gnu.org/licenses/>.

import sys
import os.path
from distutils.dir_util import mkpath
import numpy as np
from PIL import Image
import urllib2
import StringIO


CACHE_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                          "rsc/cache/")
ELEVATION_URL = "https://terrain-preview.mapzen.com/"
LANDCOVER_URL = "http://a.tile.stamen.com/"


def elevation(tile, force=False):
    """ Download a tile elevation image

    Position arguments:
    tile -- Tuple of 3 values, tilex, tiley and zoom (<= 15)

    Keyword arguments:
    force -- True if the image should be downloaded even though it is already
             available in the cache

    Returned value:
    Numpy array of elevations per pixel
    """
    img_file = CACHE_PATH + "terrarium/{}/{}/{}.png".format(
        int(tile[2]), int(tile[0]), int(tile[1]))
    if os.path.isfile(img_file) and not force:
        # The image is already cached
        pic = Image.open(img_file)
    else:
        # Download the terrarium image
        url = ELEVATION_URL + "terrarium/{}/{}/{}.png".format(
            int(tile[2]), int(tile[0]), int(tile[1]))
        print(url)
        img = urllib2.urlopen(url).read()
        pic = Image.open(StringIO.StringIO(img))
        # Check it is a valid image
        pic.verify()
        pic = Image.open(StringIO.StringIO(img))
        # Save it
        img_folder = os.path.dirname(img_file)
        if not os.path.isdir(img_folder):
            mkpath(img_folder)
        pic.save(img_file)
    # Decode the elevation
    pix = np.array(pic.getdata(), dtype=np.float).reshape(
        pic.size[0], pic.size[1], 3)
    elevation = (pix[:,:,0] * 256 + pix[:,:,1] + pix[:,:,2] / 256) - 32768
    return elevation


def landcover(tile, force=False):
    """ Download a tile elevation image

    Position arguments:
    tile -- Tuple of 3 values, tilex, tiley and zoom (<= 15)

    Keyword arguments:
    force -- True if the image should be downloaded even though it is already
             available in the cache

    Returned value:
    Numpy array with the RGB image content
    """
    img_file = CACHE_PATH + "terrain-background/{}/{}/{}.png".format(
        int(tile[2]), int(tile[0]), int(tile[1]))
    if os.path.isfile(img_file) and not force:
        # The image is already cached
        pic = Image.open(img_file)
    else:
        # Download the shaded landscape image
        url = LANDCOVER_URL + "terrain-background/{}/{}/{}.png".format(
            int(tile[2]), int(tile[0]), int(tile[1]))
        print(url)
        img = urllib2.urlopen(url).read()
        pic = Image.open(StringIO.StringIO(img))
        # Check it is a valid image
        pic.verify()
        pic = Image.open(StringIO.StringIO(img))
        # Convert to HSV and remove Saturation and Value (we are interested
        # just in Hue)
        hsv = pic.convert('HSV')
        pix = np.array(hsv)
        pix[:,:,1] = 100
        pix[:,:,2] = 165
        hsv = Image.fromarray(pix, mode='HSV')
        pic = hsv.convert('RGB')
        # Save it
        img_folder = os.path.dirname(img_file)
        if not os.path.isdir(img_folder):
            mkpath(img_folder)
        pic.save(img_file)
    # Return an scipy image
    return np.array(pic)


def main(tilesx, tilesy, zoom, force=False):
    """ Download a set of tiles

    Position arguments:
    tilesx -- List of x tile values
    tilesy -- List of y tile values
    zoom -- Zoom level, >= 14

    Keyword arguments:
    force -- True if the image should be downloaded even though it is already
             available in the cache
    """
    for tilex in tilesx:
        for tiley in tilesy:
            try:
                elevation((tilex, tiley, zoom), force)
                landcover((tilex, tiley, zoom), force)
            except:
                print("Failed to download {}/{}/{}".format(tilex, tiley, zoom))


if __name__ == "__main__":
    # Call this script with the following command:
    # python zoom [startx endx starty endy]
    # where:
    # zoom is the zoom level (<= 14)
    # startx is the first x tile to download
    # endx is the last x tile to download    
    # starty is the first y tile to download
    # endy is the last y tile to download
    #
    # For instance, to download everything you may execute the following
    # command (BASH):
    # for zoom in {1..15}; do python mapzen/download.py $zoom & done
    if len(sys.argv) != 6 and len(sys.argv) != 2:
        raise ValueError('Wrong number of arguments')
        sys.exit()
    zoom = int(sys.argv[1])
    if len(sys.argv) > 2:
        tilesx = list(range(int(sys.argv[2]), int(sys.argv[3]) + 1))
        tilesy = list(range(int(sys.argv[4]), int(sys.argv[5]) + 1))
    else:
        tilesx = tilesy = list(range(0, 2**zoom))
    main(tilesx, tilesy, zoom)
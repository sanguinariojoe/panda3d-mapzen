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

import time
import os.path
import threading
import numpy as np
from scipy.ndimage import gaussian_filter
from skimage import io, exposure, img_as_uint, img_as_float
from skimage.transform import resize
import urllib2
import StringIO
from PIL import Image
from .globalmaptiles import GlobalMercator
from panda3d.core import ShaderTerrainMesh, Shader, SamplerState


MIN_ZSCALE = 250.0
update_mutex = threading.Lock()


class Generator(threading.Thread):
    def __init__(self, camera, loader, root_node, group=None, target=None,
                 name=None, verbose=None, zoom=15):
        self.__camera = camera
        self.__loader = loader
        self.__root = root_node
        self.__zoom = zoom
        self.__stop = threading.Event()
        self.__tile = None
        self.__tile_back = None
        self.__z0 = 0.0
        self.__zscale = MIN_ZSCALE
        self.__updated = False

        self.terrain_node = ShaderTerrainMesh()
        self.terrain_node.heightfield = self.__loader.loadTexture(
            "mapzen/rsc/elevation.png")
        self.terrain_node.target_triangle_width = 10.0
        self.terrain_node.generate()
        self.terrain = root_node.attach_new_node(self.terrain_node)
        self.terrain.set_scale(1024, 1024, 100)
        self.terrain.set_pos(-512, -512, -70.0)
        terrain_shader = Shader.load(Shader.SL_GLSL,
                                     "mapzen/rsc/terrain.vert.glsl",
                                     "mapzen/rsc/terrain.frag.glsl")
        self.terrain.set_shader(terrain_shader)
        self.terrain.set_shader_input("camera", self.__camera)
        grass_tex = self.__loader.loadTexture("mapzen/rsc/grass.png")
        grass_tex.set_minfilter(SamplerState.FT_linear_mipmap_linear)
        grass_tex.set_anisotropic_degree(16)
        self.terrain.set_texture(grass_tex)

        self.mercator = GlobalMercator()
        self.__orig = np.zeros(3, dtype=np.float)
        threading.Thread.__init__(self, group=group, target=target, name=name,
                                  verbose=verbose)
        return

    def __elevation(self, tile):
        img_file = "mapzen/rsc/cache/elevation_{}_{}_{}.png".format(
            int(self.__zoom), int(tile[0]), int(tile[1]))
        if os.path.isfile(img_file):
            # The image is already cached
            pic = Image.open(img_file)
        else:
            # Download the terrarium image
            url = "https://terrain-preview.mapzen.com/terrarium/{}/{}/{}.png".format(
                int(self.__zoom), int(tile[0]), int(tile[1]))
            print(url)
            img = urllib2.urlopen(url).read()
            pic = Image.open(StringIO.StringIO(img))
            # Check it is a valid image
            pic.verify()
            pic = Image.open(StringIO.StringIO(img))
            img_folder = os.path.dirname(img_file)
            # Save it
            if not os.path.isdir(img_folder):
                os.mkdir(img_folder)
            pic.save(img_file)
        # Decode the elevation
        pix = np.array(pic.getdata(), dtype=np.float).reshape(
            pic.size[0], pic.size[1], 3)
        elevation = (pix[:,:,0] * 256 + pix[:,:,1] + pix[:,:,2] / 256) - 32768
        return elevation

    def generate(self, tile):
        # Generate the terrain elevation image
        exy = None
        for tx in range(tile[0] - 1, tile[0] + 2):
            ey = None
            for ty in range(tile[1] - 1, tile[1] + 2):
                e = self.__elevation((tx, ty))
                ey = e if ey is None else np.concatenate((ey, e), axis=0)
            exy = ey if exy is None else np.concatenate((exy, ey), axis=1)
        # Smooth the image
        exy = gaussian_filter(exy, 1)
        # Resize the image, which should be power of 2
        new_shape = (1 << (exy.shape[0] - 1).bit_length(),
                     1 << (exy.shape[1] - 1).bit_length())
        exy = resize(exy, new_shape)

        update_mutex.acquire()
        self.__z0 = np.min(exy)
        self.__zscale = max(MIN_ZSCALE, np.max(exy) - self.__z0)
        io.use_plugin('freeimage')
        im = (exy - self.__z0) / self.__zscale
        im[im < 0] = 0
        im[im > 1] = 1
        # im = 0.5 * (1.0 + exposure.rescale_intensity(exy, out_range='float'))
        im = img_as_uint(im)
        io.imsave('mapzen/rsc/elevation.png', im)
        self.__tile_back = np.copy(tile)
        # Mark as pending to become updated. The objects should not be updated
        # in a parallel thread, but 
        self.__updated = False
        update_mutex.release()


    def update(self, force=False):
        update_mutex.acquire()
        if not force and self.__updated:
            # Nothing to do
            update_mutex.release()
            return
        tile = self.__tile_back
        xmin, ymin, _, _ = self.mercator.TileBounds(tile[0] - 1,
                                                    tile[1] - 1,
                                                    self.__zoom)
        _, _, xmax, ymax = self.mercator.TileBounds(tile[0] + 1,
                                                    tile[1] + 1,
                                                    self.__zoom)
        xmin -= self.__orig[0]
        ymin -= self.__orig[1]
        xmax -= self.__orig[0]
        ymax -= self.__orig[1]
        self.terrain_node.heightfield.reload()
        # self.terrain_node.generate()
        self.terrain.set_scale(xmax - xmin, ymax - ymin, self.__zscale)
        self.terrain.set_pos(xmin, -ymax, self.__z0 - self.__orig[2])
        self.__updated = True
        update_mutex.release()


    def run(self):
        while not self.__stop.isSet():
            # Check if there is something pe3nding to become updated
            if not self.__updated:
                continue
            if self.__tile is not None and np.any(self.__tile != self.__tile_back):
                self.generate(self.__tile)
            time.sleep(1)
        return

    def stop(self):
        self.__stop.set()

    def stopped(self):
        return self.__stop.isSet()

    @property
    def orig(self):
        return self.__orig

    @orig.setter
    def orig(self, orig):
        update_mutex.acquire()
        self.__orig = np.asarray(orig, dtype=np.float)
        update_mutex.release()

    @property
    def tile(self):
        return self.__tile

    @orig.setter
    def tile(self, tile):
        update_mutex.acquire()
        self.__tile = np.asarray(tile, dtype=np.int)
        update_mutex.release()

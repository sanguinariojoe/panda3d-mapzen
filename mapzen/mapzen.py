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

from direct.task import Task
from .generator import Generator
from .globalmaptiles import GlobalMercator


class Mapzen():
    def __init__(self, camera, loader, root_node, taskMgr,
                 tilex, tiley, zoom=14, buildings_zoom=14):
        """Mapzen scenario generator. This tool is loading tiles from mapzen,
        such that 9 tiles are ever shown around the camera position. When the
        camera is moved out of the tile center, the tool is loading a new set
        of tiles, and removing the old ones.

        Args:
            camera:         Panda3D camera instance
            loader:         Panda3D entities loader
            root_node:      Panda3D node where all the entities will be attached
            taskMgr:        Panda3D task manager
            tilex:          Position of the starting tilex (x = 0.0 global
                            coordinate will be centered in this tile)
            tiley:          Position of the starting tiley (y = 0.0 global
                            coordinate will be centered in this tile)
            zoom:           Zoom level, in range [1, 15]. The lower zoom the
                            larger tiles are considered.
            buildings_zoom: Zoom level, in range [1, 15]. Usually the buildings
                            can be obtained just in higher levels. So a
                            different zoom level can be selected, and the tool
                            will automatically generate buildings along all the
                            tiles required to cover the area required by zoom.
        """
        if not 1 <= zoom <= 15:
            raise ValueError('zoom should be an integer in range [1, 15]')
        self.camera = camera
        self.zoom = zoom
        self.buildings_zoom = buildings_zoom
        self.generator = Generator(camera, loader, root_node, zoom=zoom)
        # Compute the origin for the generator
        self.mercator = GlobalMercator()
        bds = self.mercator.TileBounds(tilex, tiley, zoom)
        self.generator.orig = [0.5 * (bds[0] + bds[2]),
                               0.5 * (bds[1] + bds[3]),
                               0.0]
        # Compute the current tile
        tx, ty = self.mercator.MetersToTile(self.generator.orig[0],
                                            self.generator.orig[1],
                                            zoom)
        self.generator.tile = tx, ty
        self.generator.generate((tx, ty))
        self.generator.update()
        # Start the threads
        self.generator.start()
        taskMgr.add(self.update, "mapzen", uponDeath=self.stop)

    def update(self, task):
        x = self.generator.orig[0] + self.camera.getX()
        y = self.generator.orig[1] - self.camera.getY()
        tx, ty = self.mercator.MetersToTile(x, y, self.zoom)
        self.generator.tile = tx, ty
        self.generator.update()
        return Task.cont

    def stop(self):
        self.generator.stop()

    def __del__(self):
        self.stop()

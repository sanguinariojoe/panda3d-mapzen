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

from direct.showbase.ShowBase import ShowBase
from direct.task.Task import Task
from panda3d.core import ShaderTerrainMesh, Shader, load_prc_file_data
from panda3d.core import SamplerState, Vec3
from mapzen import Mapzen
from movement_controller import MovementController


class ShaderTerrainDemo(ShowBase):
    def __init__(self):

        # Load some configuration variables, its important for this to happen
        # before the ShowBase is initialized
        load_prc_file_data("", """
            textures-power-2 none
            gl-coordinate-system default
            window-title Panda3D ShaderTerrainMesh Demo
        """)

        # Initialize the showbase
        ShowBase.__init__(self)

        # Increase camera FOV as well as the far plane
        self.camLens.set_fov(90)
        self.camLens.set_near_far(0.1, 3000)

        # Start the Mapzen tool
        self.mzen = Mapzen(self.camera, self.loader, self.render, taskMgr,
                           3095, 6430, zoom=14)
        base.finalExitCallbacks.append(self.exit)
        base.exitFunc = self.exit

        """
        # Construct the terrain
        self.terrain_node = ShaderTerrainMesh()

        # Set a heightfield, the heightfield should be a 16-bit png and
        # have a quadratic size of a power of two.
        self.terrain_node.heightfield = self.loader.loadTexture("elevation.png")

        # Set the target triangle width. For a value of 10.0 for example,
        # the terrain will attempt to make every triangle 10 pixels wide on screen.
        self.terrain_node.target_triangle_width = 10.0

        # Generate the terrain
        self.terrain_node.generate()

        # Attach the terrain to the main scene and set its scale. With no scale
        # set, the terrain ranges from (0, 0, 0) to (1, 1, 1)
        self.terrain = self.render.attach_new_node(self.terrain_node)
        self.terrain.set_scale(1024, 1024, 100)
        self.terrain.set_pos(-512, -512, -70.0)

        # Set a shader on the terrain. The ShaderTerrainMesh only works with
        # an applied shader. You can use the shaders used here in your own application
        terrain_shader = Shader.load(Shader.SL_GLSL, "terrain.vert.glsl", "terrain.frag.glsl")
        self.terrain.set_shader(terrain_shader)
        self.terrain.set_shader_input("camera", self.camera)

        # Set some texture on the terrain
        grass_tex = self.loader.loadTexture("textures/grass.png")
        grass_tex.set_minfilter(SamplerState.FT_linear_mipmap_linear)
        grass_tex.set_anisotropic_degree(16)
        self.terrain.set_texture(grass_tex)
        """

        # Shortcut to view the wireframe mesh
        self.accept("f3", self.toggleWireframe)

        """
        # Load a skybox - you can safely ignore this code
        skybox = self.loader.loadModel("models/skybox.bam")
        skybox.reparent_to(self.render)
        skybox.set_scale(20000)

        skybox_texture = self.loader.loadTexture("textures/skybox.jpg")
        skybox_texture.set_minfilter(SamplerState.FT_linear)
        skybox_texture.set_magfilter(SamplerState.FT_linear)
        skybox_texture.set_wrap_u(SamplerState.WM_repeat)
        skybox_texture.set_wrap_v(SamplerState.WM_mirror)
        skybox_texture.set_anisotropic_degree(16)
        skybox.set_texture(skybox_texture)

        skybox_shader = Shader.load(Shader.SL_GLSL, "skybox.vert.glsl", "skybox.frag.glsl")
        skybox.set_shader(skybox_shader)
        """

        # Initialize movement controller
        self.controller = MovementController(self)
        self.controller.set_initial_position_hpr(
            Vec3(0.0, 0.0, 1500.0),
            Vec3(-90.0, 0.0, 0.0))
        self.controller.speed = 5.0
        self.controller.setup()

    def exit(self):
        self.mzen.stop()

ShaderTerrainDemo().run()

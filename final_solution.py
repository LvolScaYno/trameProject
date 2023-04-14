from trame.app import get_server
from trame.ui.vuetify import SinglePageLayout
from trame.widgets import vtk, vuetify

from vtkmodules.vtkFiltersSources import vtkConeSource
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkPolyDataMapper,
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
)

# Required for interactor initialization
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleSwitch  # noqa

# Required for rendering initialization, not necessary for
# local rendering, but doesn't hurt to include it
import vtkmodules.vtkRenderingOpenGL2  # noqa

# additional vtk modules
from vtkmodules.vtkFiltersCore import vtkGlyph3D
from vtkmodules.vtkCommonCore import (
    vtkLookupTable, vtkPoints, vtkDoubleArray, vtkCommand,
)
from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet, vtkPolyData

# -----------------------------------------------------------------------------
# Globals
# -----------------------------------------------------------------------------

DEFAULT_RESOLUTION = 6
step = 0 # 全局 step 非常重要

# -----------------------------------------------------------------------------
# VTK pipeline
# -----------------------------------------------------------------------------

import numpy as np

import solver

class BasicVisualize:
    def __init__(self):
        self.cone = vtkConeSource()

        self.cone.SetResolution(4)
        self.cone.SetHeight(0.8)
        self.cone.SetRadius(0.15)

        self.cones = vtkGlyph3D()
        self.cones.SetSourceConnection(self.cone.GetOutputPort())
        self.cones.SetScaleFactor(0.03)
        self.cones.SetScaleModeToScaleByVector()

        self.lut = vtkLookupTable()
        self.lut.SetHueRange(0.667, 0.0)
        self.lut.Build()
        self.vectorMapper = None
        self.vectorActor = None
        self.scalarRange = None
        self.mbds = None

    def set_mbds(self, mbds):
        self.mbds = mbds
        polydata = self.mbds.GetBlock(0)
        self.cones.SetInputData(polydata)
        self.cones.Update()
        self.scalarRange = [0] * 2
        self.scalarRange[0] = self.cones.GetOutput().GetPointData().GetScalars().GetRange()[0]
        self.scalarRange[1] = self.cones.GetOutput().GetPointData().GetScalars().GetRange()[1]

        self.vectorMapper = vtkPolyDataMapper()
        self.vectorMapper.SetInputConnection(self.cones.GetOutputPort())
        self.vectorMapper.SetScalarRange(self.scalarRange[0], self.scalarRange[1])
        self.vectorMapper.SetLookupTable(self.lut)

        self.vectorActor = vtkActor()
        self.vectorActor.SetMapper(self.vectorMapper)

    def update(self):
        global step
        polydata = self.mbds.GetBlock(step)
        self.cones.SetInputData(polydata)
        self.cones.Update()

        self.vectorMapper = vtkPolyDataMapper()
        self.vectorMapper.SetInputConnection(self.cones.GetOutputPort())
        self.vectorMapper.SetScalarRange(self.scalarRange[0], self.scalarRange[1])
        self.vectorMapper.SetLookupTable(self.lut)
        self.vectorActor.SetMapper(self.vectorMapper)


class ToVtkDataTool:
    def __init__(self, data):
        self.field = data
        print("你蝶来了")

    def get(self):
        mbds = vtkMultiBlockDataSet()
        for t in range(0, len(self.field)):
            polydata = vtkPolyData()
            points = vtkPoints()

            velocities = vtkDoubleArray()
            velocities.SetNumberOfComponents(3)
            velocities.SetName('Velocity')

            scalars = vtkDoubleArray()
            scalars.SetNumberOfComponents(1)
            scalars.SetName("Scalar")

            for (x, y), (u, v) in self.field[t].items():
                points.InsertNextPoint(x, y, 0)
                velocities.InsertNextTuple3(u, v, 0)
                scalars.InsertNextValue(np.sqrt(u ** 2 + v ** 2))

            polydata.SetPoints(points)
            polydata.GetPointData().SetVectors(velocities)
            polydata.GetPointData().SetScalars(scalars)
            mbds.SetBlock(t, polydata)
        return mbds



solver = solver.Solver()
solver.initialize()

nt = 4000

solver.nt = nt
for i in range(nt):
    solver.solve_next_step()

dataTransfer = ToVtkDataTool(solver.retData)
mbds = dataTransfer.get()

bv = BasicVisualize()

bv.set_mbds(mbds)

# 创建渲染器和窗口
renderer = vtkRenderer()
renderer.AddActor(bv.vectorActor)

renderer.ResetCamera()
render_window = vtkRenderWindow()
render_window.AddRenderer(renderer)

# 创建交互器

interactor = vtkRenderWindowInteractor()
interactor.SetRenderWindow(render_window)
interactor.GetInteractorStyle().SetCurrentStyleToTrackballCamera()



# -----------------------------------------------------------------------------
# Trame setup
# -----------------------------------------------------------------------------

server = get_server()
state, ctrl = server.state, server.controller

# -----------------------------------------------------------------------------
# Functions
# -----------------------------------------------------------------------------


@state.change("resolution")
def update_resolution(resolution, **kwargs):
    global step
    step = resolution
    bv.update()
    ctrl.view_update()


def reset_resolution():
    global step
    step = 0
    state.resolution = DEFAULT_RESOLUTION


# -----------------------------------------------------------------------------
# GUI
# -----------------------------------------------------------------------------

with SinglePageLayout(server) as layout:
    layout.title.set_text("Hello trame")

    with layout.content:
        with vuetify.VContainer(
            fluid=True,
            classes="pa-0 fill-height",
        ):
            view = vtk.VtkLocalView(render_window)
            ctrl.view_update = view.update
            ctrl.view_reset_camera = view.reset_camera

    with layout.toolbar:
        vuetify.VSpacer()
        vuetify.VSlider(
            v_model=("resolution", DEFAULT_RESOLUTION),
            min=3,
            max=nt-1,
            step=1,
            hide_details=True,
            dense=True,
            style="max-width: 300px",
        )
        with vuetify.VBtn(icon=True, click=reset_resolution):
            vuetify.VIcon("mdi-restore")

        vuetify.VDivider(vertical=True, classes="mx-2")

        vuetify.VSwitch(
            v_model="$vuetify.theme.dark",
            hide_details=True,
            dense=True,
        )
        with vuetify.VBtn(icon=True, click=ctrl.view_reset_camera):
            vuetify.VIcon("mdi-crop-free")

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    server.start()

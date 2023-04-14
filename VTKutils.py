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
        if mbds is None:
            return
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

    def update(self, step):
        if self.mbds is None:
            return
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

    def get(self):
        if self.field is None:
            return None
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
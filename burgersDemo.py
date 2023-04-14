import os
from trame.app import get_server
from trame.ui.vuetify import SinglePageLayout
from trame.widgets import vtk, vuetify, trame
from vtkmodules.vtkCommonDataModel import vtkDataObject
from vtkmodules.vtkFiltersSources import vtkConeSource
from vtkmodules.vtkFiltersCore import vtkContourFilter
from vtkmodules.vtkIOXML import vtkXMLUnstructuredGridReader
from vtkmodules.vtkRenderingAnnotation import vtkCubeAxesActor
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkDataSetMapper,
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
)
# picture module
import matplotlib.pyplot as plt
from trame.widgets import matplotlib
import numpy as np
import math
from mpl_toolkits.mplot3d import Axes3D
# Required for interactor initialization
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleSwitch  # noqa
import solver
# Required for rendering initialization, not necessary for
# local rendering, but doesn't hurt to include it
import vtkmodules.vtkRenderingOpenGL2  # noqa
from vtkmodules.vtkFiltersCore import vtkGlyph3D
from vtkmodules.vtkCommonCore import (
    vtkLookupTable, vtkPoints, vtkDoubleArray, vtkCommand,
)
from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet, vtkPolyData
CURRENT_DIRECTORY = os.path.abspath(os.path.dirname(__file__))

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

class Representation:
    Points = 0
    Wireframe = 1
    Surface = 2
    SurfaceWithEdges = 3


class LookupTable:
    Rainbow = 0
    Inverted_Rainbow = 1
    Greyscale = 2
    Inverted_Greyscale = 3

# -----------------------------------------------------------------------------
# Trame setup
# -----------------------------------------------------------------------------

server = get_server()
state, ctrl = server.state, server.controller
state.setdefault("active_ui", None)

# -----------------------------------------------------------------------------
# Callbacks
# -----------------------------------------------------------------------------

# Selection Change
def actives_change(ids):
    _id = ids[0]
    if _id == "1":  # Mesh
        state.active_ui = "mesh"
    elif _id == "2":  # Contour
        state.active_ui = "contour"
    else:
        state.active_ui = "nothing"

# Representation Callbacks
def update_representation(actor, mode):
    property = actor.GetProperty()
    if mode == Representation.Points:
        property.SetRepresentationToPoints()
        property.SetPointSize(5)
        property.EdgeVisibilityOff()
    elif mode == Representation.Wireframe:
        property.SetRepresentationToWireframe()
        property.SetPointSize(1)
        property.EdgeVisibilityOff()
    elif mode == Representation.Surface:
        property.SetRepresentationToSurface()
        property.SetPointSize(1)
        property.EdgeVisibilityOff()
    elif mode == Representation.SurfaceWithEdges:
        property.SetRepresentationToSurface()
        property.SetPointSize(1)
        property.EdgeVisibilityOn()

# Color Map Callbacks
def use_preset(actor, preset):
    lut = actor.GetMapper().GetLookupTable()
    if preset == LookupTable.Rainbow:
        lut.SetHueRange(0.666, 0.0)
        lut.SetSaturationRange(1.0, 1.0)
        lut.SetValueRange(1.0, 1.0)
    elif preset == LookupTable.Inverted_Rainbow:
        lut.SetHueRange(0.0, 0.666)
        lut.SetSaturationRange(1.0, 1.0)
        lut.SetValueRange(1.0, 1.0)
    elif preset == LookupTable.Greyscale:
        lut.SetHueRange(0.0, 0.0)
        lut.SetSaturationRange(0.0, 0.0)
        lut.SetValueRange(0.0, 1.0)
    elif preset == LookupTable.Inverted_Greyscale:
        lut.SetHueRange(0.0, 0.666)
        lut.SetSaturationRange(0.0, 0.0)
        lut.SetValueRange(1.0, 0.0)
    lut.Build()

# -----------------------------------------------------------------------------
# GUI elements
# -----------------------------------------------------------------------------


def standard_buttons():
    vuetify.VCheckbox(
        v_model="$vuetify.theme.dark",
        on_icon="mdi-lightbulb-off-outline",
        off_icon="mdi-lightbulb-outline",
        classes="mx-1",
        hide_details=True,
        dense=True,
    )
    
    vuetify.VCheckbox(
        v_model=("viewMode", "local"),
        on_icon="mdi-lan-disconnect",
        off_icon="mdi-lan-connect",
        true_value="local",
        false_value="remote",
        classes="mx-1",
        hide_details=True,
        dense=True,
    )

    with vuetify.VBtn(icon=True, click="$refs.view.resetCamera()"):
        vuetify.VIcon("mdi-crop-free")
    
    vuetify.VCheckbox(
        v_model=("showCard", False),
        on_icon="mdi-toggle-switch",
        off_icon="mdi-toggle-switch-off",
        classes="mx-1",
        hide_details=True,
        dense=True,
    )

# -----------------------------------------------------------------------------
# SOLVER and about SOLVER
# -----------------------------------------------------------------------------

# Global parameters
sv = solver.Solver()
sv.initialize()
temp = np.zeros((sv.nt, 2))
result = np.zeros(sv.nt)

# 开始解算
def start_solve():
        # 时间步归零
        global sv
        sv = solver.Solver()
        # parameters
        sv.nx, sv.ny = int(state.nx), int(state.ny)
        sv.fx, sv.fy = float(state.fx), float(state.fy)
        sv.initX, sv.initY = float(state.initX), float(state.initY)
        sv.nu = float(state.nu)
        sv.x_anchorLT, sv.y_anchorLT = float(state.x_anchorLT), float(state.y_anchorLT)
        sv.x_anchorRB, sv.y_anchorRB = float(state.x_anchorRB), float(state.y_anchorRB)
        sv.CFL = float(state.CFL)
        sv.nt = int(state.nt)
        sv.initialize()
        # reInitialize draw component
        global temp
        global result
        temp = np.zeros((sv.nt, 2))
        result = np.zeros(sv.nt)
        # 开始解算
        start_cal()

# 监听函数，监听是否更改绘图函数或是图片大小发生变化
@state.change("active_figure", "figure_size")
def update_chart(active_figure, **kwargs):
    globals()[active_figure]()

# 监听滑块函数并重新绘图
@state.change("timeStep")
def update_cone(timeStep, **kwargs):
    plt.clf()
    fig, ax = plt.subplots(**figure_size())
    ax.set_xlim(0, sv.nt)
    ax.set_ylim(0, np.max(result[2:-1]))
    ax.set_title("ln(sum(square(cur-last)))")
    ax.set_xlabel("迭代步数")
    ax.set_ylabel("残差值")
    X = range(timeStep)
    ax.plot(X[1:timeStep], result[1:timeStep])
    # 根据时间步渲染画面
    bv.update(timeStep-1)
    ctrl.view_update()
    # 根据时间步绘制残差曲线
    html_figure.update(fig)

# 解算过程函数
def start_cal():
    while sv.solve_next_step() is not True:
        temp[sv.currentTimeStep - 1][0] = np.sum(np.square(sv.u - sv.un))
        temp[sv.currentTimeStep - 1][1] = np.sum(np.square(sv.v - sv.vn))
        result[sv.currentTimeStep - 1] = math.sqrt(
            temp[sv.currentTimeStep - 1][0] * temp[sv.currentTimeStep - 1][0] + temp[sv.currentTimeStep - 1][1] *
            temp[sv.currentTimeStep - 1][1])
        result[sv.currentTimeStep - 1] = math.log(result[sv.currentTimeStep - 1] + 1) * 1000
    #解算完毕，渲染画面及绘制残差曲线
    dataTransfer = ToVtkDataTool(sv.retData)
    mbds = dataTransfer.get()
    bv.set_mbds(mbds)
    bv.update(state.timeStep-1)
    renderer.AddActor(bv.vectorActor)
    ctrl.view_update()

    html_figure.update(start_draw())


# 控制显示图片大小的函数
def figure_size():
    if state.figure_size is None:
        return {}

    dpi = state.figure_size.get("dpi")
    rect = state.figure_size.get("size")
    w_inch = rect.get("width") / dpi
    h_inch = rect.get("height") / dpi

    return {
        "figsize": (w_inch, h_inch),
        "dpi": dpi,
    }

# 绘图函数
def start_draw():
    fig, ax = plt.subplots(**figure_size())
    ax.set_xlim(0, sv.nt)
    ax.set_ylim(0, np.max(result[2:-1]))
    ax.set_title("ln(sum(square(cur-last)))")
    ax.set_xlabel("迭代步数")
    ax.set_ylabel("残差值")
    X = range(len(result))
    ax.plot(X, result)
    return fig

# -----------------------------------------------------------------------------
# VTK pipeline
# -----------------------------------------------------------------------------

from VTKutils import BasicVisualize, ToVtkDataTool

bv = BasicVisualize() # 全局bv

# 创建渲染器和窗口
renderer = vtkRenderer()

renderer.ResetCamera()
render_window = vtkRenderWindow()
render_window.AddRenderer(renderer)

# 创建交互器

interactor = vtkRenderWindowInteractor()
interactor.SetRenderWindow(render_window)
interactor.GetInteractorStyle().SetCurrentStyleToTrackballCamera()

# -----------------------------------------------------------------------------
# GUI
# -----------------------------------------------------------------------------

with SinglePageLayout(server) as layout:
    layout.title.set_text("Viewer")

    with layout.toolbar:
        vuetify.VSpacer()
        vuetify.VDivider(vertical=True, classes="mx-2")
        standard_buttons()

    with layout.content:
        with vuetify.VContainer(
            fluid=True,
            classes="pa-0 fill-height",
        ):
            view = vtk.VtkRemoteLocalView(
                                    render_window, 
                                    namespace="view", 
                                    mode="local", 
                                    interactive_ratio=1
            )
            ctrl.view_update = view.update
            ctrl.view_reset_camera = view.reset_camera
            with vuetify.VHover(
                v_slot = "{hover}",
            ):
                with trame.FloatCard(
                    height = "85%",
                    width = "22%",
                    handle_color = "grey",
                    handle_position = "top",
                    color = "grey",
                    style=("{ opacity: hover ? 1 : .3, transition: 'opacity 0.2s ease-in-out' }",)
                ):
                    with vuetify.VContainer():
                        with vuetify.VBanner(
                            style = "text-align:center"
                        ) as ban:
                            ban.set_text("二维Burgers方程")
                        vuetify.VDivider(classes="mb-2")
                        with vuetify.VForm():
                            with vuetify.VRow():
                                with vuetify.VCol():
                                    vuetify.VTextField(label = "number of X-grid", v_model = ("nx",51))
                                with vuetify.VCol():
                                    vuetify.VTextField(label = "number of Y-grid", v_model = ("ny",51))
                            with vuetify.VRow():
                                with vuetify.VCol():
                                    vuetify.VTextField(label = "field of X", v_model = ("fx",2))
                                with vuetify.VCol():
                                    vuetify.VTextField(label = "field of Y", v_model = ("fy",2))
                            with vuetify.VRow():
                                with vuetify.VCol():
                                    vuetify.VTextField(label = "initial speed of X", v_model = ("initX",2))
                                with vuetify.VCol():
                                    vuetify.VTextField(label = "initial speed of Y", v_model = ("initY",2))
                            with vuetify.VRow():
                                with vuetify.VCol():
                                    vuetify.VTextField(label = "x of anchorLT", v_model = ("x_anchorLT",0.5))
                                with vuetify.VCol():
                                    vuetify.VTextField(label = "y of anchorLT", v_model = ("y_anchorLT",1))
                            with vuetify.VRow():
                                with vuetify.VCol():
                                    vuetify.VTextField(label = "x of anchorRB", v_model = ("x_anchorRB",1))
                                with vuetify.VCol():
                                    vuetify.VTextField(label = "y of anchorRB", v_model = ("y_anchorRB",0.5))
                            vuetify.VTextField(label = "CFL", v_model = ("CFL",0.0009))
                            vuetify.VTextField(label = "nu", v_model = ("nu",0.01))
                            vuetify.VTextField(label = "number of time step", v_model = ("nt",1000))
                        vuetify.VDivider(classes="mb-2")
                        with vuetify.VBtn(icon=True, click=start_solve, block = True, variant = "outlined") as ok:
                            ok.set_text("开算!")
            with trame.FloatCard(
                height='50%', 
                width='30%',
                handle_color="grey", 
                color = "grey",
                handle_position="top",
                v_show=("showCard", False), 
                outlined=True,
                style="left:70%",
                classes="fill-height pa-3",
                ):
                with vuetify.VContainer(fluid=True, classes="fill-height pa-0 ma-0",
                                        v_model=("active_figure", "start_draw")):
                    with trame.SizeObserver("figure_size"):
                        html_figure = matplotlib.Figure()
                        html_figure.update 
                    vuetify.VSlider(
                        v_model=("timeStep", 0),
                        min=1,
                        max=("nt",),
                        step=1,
                        hide_details=True,
                        dense=True,
                        style="30%",
                        thumb_label=True
                    )

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    server.start()

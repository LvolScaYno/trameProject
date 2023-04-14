from trame.app import get_server
from trame.ui.vuetify import SinglePageLayout
from trame.widgets import vtk, vuetify
import trame.widgets.trame
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


# -----------------------------------------------------------------------------
# VTK pipeline
# -----------------------------------------------------------------------------

renderer = vtkRenderer()
renderWindow = vtkRenderWindow()
renderer.SetBackground(224,224,224)
renderWindow.AddRenderer(renderer)

renderWindowInteractor = vtkRenderWindowInteractor()
renderWindowInteractor.SetRenderWindow(renderWindow)
renderWindowInteractor.GetInteractorStyle().SetCurrentStyleToTrackballCamera()

cone_source = vtkConeSource()
mapper = vtkPolyDataMapper()
mapper.SetInputConnection(cone_source.GetOutputPort())
actor = vtkActor()
actor.SetMapper(mapper)

renderer.AddActor(actor)
renderer.ResetCamera()

# -----------------------------------------------------------------------------
# GUI elements
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Function
# -----------------------------------------------------------------------------

def opacityChange():
    print("wuHu!")

# -----------------------------------------------------------------------------
# Trame
# -----------------------------------------------------------------------------

server = get_server()
ctrl, state = server.controller, server.state

with SinglePageLayout(server) as layout:
    with layout.toolbar as toolbar:
        toolbar.set_text("LSY")
        vuetify.VSpacer()
        vuetify.VDivider(vertical=True, classes="mx-2")
        vuetify.VCheckbox(
            v_model = ("menu", False),
            on_icon = "mdi-cog",
            off_icon = "mdi-cog",
            classes = "mx-1",
            hide_details = True,
            dense = True,
        )

    with layout.content:
        with vuetify.VContainer(
            fluid=True,
            classes="pa-0 fill-height",
        ):
            view = vtk.VtkLocalView(renderWindow)
            with vuetify.VHover(
                v_slot = "{hover}",
            ):
                with trame.widgets.trame.FloatCard(
                    # classes = "{'on-hover' : isHovering}",
                    height = "80%",
                    width = "18%",
                    handle_color = "black",
                    handle_position = "right",
                    color = "grey",
                    style = ("{ opacity : hover ? 1 : .3 }",),
                    # v_bind = "isHovering",
                ):
                    with vuetify.VAppBar(
                        classes = "pa-0",
                        dense = True
                    ):
                        with vuetify.VBtn(icon=True, click=""):
                            vuetify.VIcon("mdi-gender-transgender")
                        with vuetify.VBtn(icon=True, click=""):
                            vuetify.VIcon("mdi-file")
                        with vuetify.VBtn(icon=True, click=""):
                            vuetify.VIcon("mdi-crosshairs")
                        with vuetify.VBtn(icon=True, click=""):
                            vuetify.VIcon("mdi-camera")
                        with vuetify.VBtn(icon=True, click=""):
                            vuetify.VIcon("mdi-information-outline")
                        vuetify.VSpacer()
                        vuetify.VDivider(vertical=True, classes="mx-2")
                        with vuetify.VBtn(icon=True, click=""):
                            vuetify.VIcon("mdi-arrow-expand")
                    vuetify.VDivider(vertical=False, classes="mx-2")
                    with vuetify.VContainer(
                        color = "grey",
                    ):
                        vuetify.VTextarea(v_model = ("text", "哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈"))
                    with vuetify.VAppBar(
                        classes = "pa-0",
                        dense = True
                    ):
                        with vuetify.VBtn(icon=True, click=""):
                            vuetify.VIcon("mdi-gender-transgender")
                        with vuetify.VBtn(icon=True, click=""):
                            vuetify.VIcon("mdi-file")
                        with vuetify.VBtn(icon=True, click=""):
                            vuetify.VIcon("mdi-crosshairs")
                        with vuetify.VBtn(icon=True, click=""):
                            vuetify.VIcon("mdi-camera")
                        with vuetify.VBtn(icon=True, click=""):
                            vuetify.VIcon("mdi-information-outline")
                        vuetify.VDivider(vertical=True, classes="mx-2")
                        with vuetify.VBtn(icon=True, click=""):
                            vuetify.VIcon("mdi-arrow-expand")


    with layout.footer as footer:
        footer.set_text("@LSY")

    

                

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    server.start()

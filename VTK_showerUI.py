from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsBlurEffect, QMainWindow
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vtk

class UI_VTKshower(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_mesh_renderer()

    def setup_mesh_renderer(self):
        self.vtk_mesh_widget = QVTKRenderWindowInteractor(self)
        self.setCentralWidget(self.vtk_mesh_widget)
        self.mesh_renderer = vtk.vtkRenderer()
        self.vtk_mesh_widget.GetRenderWindow().AddRenderer(self.mesh_renderer)

        self.mesh_interactor = self.vtk_mesh_widget.GetRenderWindow().GetInteractor()
        self.mesh_interactor.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())
        self.mesh_interactor.Initialize()


    def render_mesh(self, vtk_data):
        # Use vtkSmartVolumeMapper for volume data
        self.volume_mapper = vtk.vtkSmartVolumeMapper()

        gaussian_smooth = vtk.vtkImageGaussianSmooth()
        gaussian_smooth.SetInputData(vtk_data)
        gaussian_smooth.SetStandardDeviations(0.6, 0.6, 0.6)  # Adjust the standard deviations
        gaussian_smooth.Update()


        self.volume_mapper.SetInputData(gaussian_smooth.GetOutput())

        self.volume_property = vtk.vtkVolumeProperty()
        self.volume_property.ShadeOn()
        self.volume_property.SetInterpolationTypeToLinear()

        color_transfer_function = vtk.vtkColorTransferFunction()
        color_transfer_function.AddRGBPoint(0, 0, 0, 0)
        color_transfer_function.AddRGBPoint(1.0, 1, 1, 1)
        self.volume_property.SetColor(color_transfer_function)

        opacity_transfer_function = vtk.vtkPiecewiseFunction()
        opacity_transfer_function.AddPoint(0, 0.0)
        opacity_transfer_function.AddPoint(0.8, 0.8)
        opacity_transfer_function.AddPoint(1.0, 1.0)
        self.volume_property.SetScalarOpacity(opacity_transfer_function)

        self.volume = vtk.vtkVolume()
        self.volume.SetMapper(self.volume_mapper)
        self.volume.SetProperty(self.volume_property)

        self.mesh_renderer.AddVolume(self.volume)
        self.mesh_renderer.ResetCamera()
        self.mesh_renderer.GetActiveCamera().SetViewUp(0.0, 1.0, 0.0)
        self.mesh_interactor.Render()




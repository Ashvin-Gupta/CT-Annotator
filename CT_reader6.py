import os
import sys
import vtkmodules.all as vtk
import numpy as np
import time
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QFileDialog, QGraphicsBlurEffect
import pyqtgraph as pg
import SimpleITK as sitk
from vtk.util import numpy_support

from CT_readerUI3 import UI_CTReaderWindow
from VTK_showerUI import UI_VTKshower
from Calculator import Calculator

class CTReaderApp(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.gui = UI_CTReaderWindow()
        self.calculator = Calculator()
        self.setup_ui()
    
    def setup_ui(self):
        self.gui.setupUI(self)
        self.setCentralWidget(self.gui.centralwidget)
        # Load data buttons
        self.gui.loadBinaryButton.clicked.connect(self.load_binary_file)
        self.gui.loadDicomButton.clicked.connect(self.load_dicom_file)

        # View functions
        self.gui.axial_view.stateChanged.connect(self.axial_clicked)
        self.gui.sagittal_view.stateChanged.connect(self.sagittal_clicked)
        self.gui.coronal_view.stateChanged.connect(self.coronal_clicked)

        # Cropping, ROI and Threshold buttons/sliders 
        self.gui.z_slider.valueChanged.connect(self.update_slice)
        self.gui.x_cropping_slider.valueChanged.connect(self.update_x_slice)
        self.gui.y_cropping_slider.valueChanged.connect(self.update_y_slice)
        self.gui.z_cropping_slider.valueChanged.connect(self.update_z_slice)
        self.gui.axial_rect.sigRegionChangeFinished.connect(self.update_slider_from_rect)
        self.gui.confirm_roi_button.clicked.connect(self.confirm_roi)
        self.gui.threshold_slider.valueChanged.connect(self.update_threshold)
        self.gui.confirm_thresh_button.clicked.connect(self.confirm_threshold)

        # Editing buttons/sliders
        self.gui.edit_slider.valueChanged.connect(self.edit_size)
        self.gui.edit_checkbox.stateChanged.connect(self.edit_checked)
        self.gui.multiple_slices.stateChanged.connect(self.multiple_slices_checked)
        self.gui.erase_button.clicked.connect(self.erase_clicked)
        self.gui.draw_button.clicked.connect(self.draw_clicked)
        self.gui.grow_button.clicked.connect(self.grow_clicked)
        self.gui.undo_button.clicked.connect(self.undo)
       
        # Storing, saving and resetting buttons
        self.gui.store_button.clicked.connect(self.store_file)
        self.gui.reset_button.clicked.connect(self.reset_images)
        self.gui.clear_button.clicked.connect(self.clear_images)

        self.gui.create_final_button.clicked.connect(self.create_final_image)
        self.gui.view_3d.clicked.connect(self.view_3d)

        self.axial = 1
        self.sagittal = 0
        self.coronal = 0
        self.step = 0
        self.saved = 0
        self.overlay = 0
        self.checked = 0
        self.mult_sliced_checked = 0

        self.erase_enabled = False
        self.draw_enabled = False
        self.grow_enabled = False
        self.original_image = None
        
        self.change_history = []
        self.change_history2 = []
        self.binary_images = []
        
        self.filter_volume = None 
        self.first_image_loaded = None

        self.x_min_ROI = None
        self.x_max_ROI = None
        self.y_min_ROI = None
        self.y_max_ROI = None
        self.z_min_ROI = None 
        self.z_max_ROI = None

    # Loading files
    def load_data(self, data_type, data_path):
        data = self.dicom_reader(data_path)
        print(f"{data_type} file loaded: {data_path}")

        if data_type == "DICOM":
            file_name = os.path.basename(data_path)
            self.gui.view_label.setText(file_name)

            self.gui.z_slider.setRange(0, data.shape[2] - 1)
            self.gui.z_slider.setValue(0)

            self.gui.x_cropping_slider.setRange(0, data.shape[0]-1)
            self.gui.y_cropping_slider.setRange(0, data.shape[1]-1)
            self.gui.z_cropping_slider.setRange(0, data.shape[2]-1)

            self.original_image = data.copy()
            self.gui.axial_view.setChecked(True)
            self.gui.confirm_roi_button.setEnabled(True)
            self.gui.loadBinaryButton.setDisabled(True)
            self.gui.loadDicomButton.setDisabled(True)
            self.gui.step2_frame.setGraphicsEffect(None)
            self.gui.step1_frame.setGraphicsEffect(QGraphicsBlurEffect())
            self.update_slice()
        
        elif data_type == 'Binary':
            data = self.dicom_reader(data_path)
            self.binary_images.append(data)

    def load_binary_file(self):
        options = QFileDialog.Options()
        dir_path = QFileDialog.getExistingDirectory(self, "Open Directory Containing DICOM Images", options=options)
        if dir_path:
            self.load_data("Binary", dir_path)

    def load_dicom_file(self):
        options = QFileDialog.Options()
        dir_path = QFileDialog.getExistingDirectory(self, "Open Directory Containing DICOM Images", options=options)
        if dir_path:
            self.load_data("DICOM", dir_path)
    
    def dicom_reader(self, data_path):
        reader = vtk.vtkDICOMImageReader()
        reader.SetDirectoryName(data_path)
        reader.Update()

        _extent = reader.GetDataExtent()
        ConstPixelDims = [_extent[1]-_extent[0]+1, _extent[3]-_extent[2]+1, _extent[5]-_extent[4]+1]
        imageData = reader.GetOutput()
        pointData = imageData.GetPointData()
        assert (pointData.GetNumberOfArrays()==1)
        arrayData = pointData.GetArray(0)

        ArrayDicom = numpy_support.vtk_to_numpy(arrayData)
        ArrayDicom = ArrayDicom.reshape(ConstPixelDims, order='F')
        data = ArrayDicom[:, ::-1, ::-1]

        self.image_position_patient = reader.GetImagePositionPatient()
        self.pixel_spacing = reader.GetPixelSpacing()
        self.image_orientation = reader.GetImageOrientationPatient()

        dicom_files = [os.path.join(data_path, f) for f in os.listdir(data_path)]

        ds = sitk.ReadImage(dicom_files[0])
        self.slice_thickness = float(ds.GetMetaData('0018|0050'))

        return data

    # View handling function
    def update_slice(self):
        if self.original_image is not None:
            z = self.gui.z_slider.value()
            self.gui.z_slider_label.setText(str(z))

            if self.axial or self.sagittal or self.coronal:
                if self.step == 0:
                    if self.axial:
                        self.current_slice = self.original_image[:, :, z]
                    elif self.sagittal:
                        self.current_slice = self.original_image[:, z, :][:, ::-1] 
                    elif self.coronal:
                        self.current_slice = self.original_image[z, :, :][:, ::-1] 
                elif self.step == 1:
                    if self.axial:
                        self.current_slice = self.original_image[:, :, z]
                    elif self.sagittal:
                        self.current_slice = self.original_image[:,  z, :][:, ::-1] 
                    elif self.coronal:
                        self.current_slice = self.original_image[z, :, :][:, ::-1] 
                    self.current_slice = np.where((self.current_slice >= self.lower_threshold) & (self.current_slice <= self.upper_threshold), 1, 0)
                elif self.step == 2:
                    if self.axial:
                        self.current_slice = self.overlayed_image[:, :, z]
                    elif self.sagittal:
                        self.current_slice = self.overlayed_image[:, z, :][:, ::-1] 
                    elif self.coronal:
                        self.current_slice = self.overlayed_image[z, :, :][:, ::-1] 
                image_item = self.gui.image_view.getImageItem()
                window_level, window_width = image_item.getLevels()

                self.handle_slice_display(window_level, window_width)

    def handle_slice_display(self, window_level, window_width):
        if self.first_image_loaded is None:
            self.first_image_loaded = True
            self.gui.image_view.setImage(self.current_slice)
        else:
            previous_state = self.gui.image_view.view.getState()
            self.gui.image_view.setImage(self.current_slice)
            if self.step == 0:
                self.gui.image_view.setLevels(window_level, window_width)
            elif self.step == 2:
                if self.overlay == 0:
                    self.gui.image_view.setLevels(-2048, 3071)
                    self.overlay = 1
                else:
                    self.gui.image_view.setLevels(window_level, window_width)
            self.gui.image_view.view.setState(previous_state)

    def axial_clicked(self, state):
        if state == QtCore.Qt.Checked:
            self.axial = 1
            self.gui.sagittal_view.setChecked(False)
            self.gui.coronal_view.setChecked(False)
            self.gui.z_slider.setRange(0, self.original_image.shape[2] - 1)
            self.gui.axial_rect.show()
        else:
            self.axial = 0
            self.gui.axial_rect.hide()
            
    def coronal_clicked(self, state):
        if state == QtCore.Qt.Checked:
            self.sagittal = 1
            self.gui.axial_view.setChecked(False)
            self.gui.sagittal_view.setChecked(False)
            self.gui.z_slider.setRange(0, self.original_image.shape[1] - 1)
        else:
            self.sagittal = 0    
    
    def sagittal_clicked(self, state):
        if state == QtCore.Qt.Checked:
            self.coronal = 1
            self.gui.coronal_view.setChecked(False)
            self.gui.axial_view.setChecked(False)
            self.gui.z_slider.setRange(0, self.original_image.shape[0] - 1)
        else:
            self.coronal = 0

    # ROI functions
    def update_x_slice(self):
        x_range = self.gui.x_cropping_slider.value()
        self.gui.x_slider_label.setText('X: ' + str(x_range))
        self.update_rectangle()
    
    def update_y_slice(self):
        y_range = self.gui.y_cropping_slider.value()
        self.gui.y_slider_label.setText('Y: ' + str(y_range))
        self.update_rectangle()
    
    def update_z_slice(self):
        z_range = self.gui.z_cropping_slider.value()
        self.gui.z_cropping_slider_label.setText('Z: ' + str(z_range))
        self.update_rectangle()
    
    def update_rectangle(self):
        x_range = self.gui.x_cropping_slider.value()
        x_min = x_range[0]
        x_max = x_range[1]
        
        y_range = self.gui.y_cropping_slider.value()
        y_min = y_range[0]
        y_max = y_range[1]
        
        if self.axial:
            self.gui.axial_rect.setPos([x_min, y_min])
            width = x_max - x_min
            height = y_max - y_min
            self.gui.axial_rect.setSize((width, height))

    def update_slider_from_rect(self, rect_item):
        self.gui.x_cropping_slider.valueChanged.disconnect(self.update_x_slice)
        self.gui.y_cropping_slider.valueChanged.disconnect(self.update_y_slice)

        position = rect_item.parentBounds()
        x_min = position.x()
        y_min = position.y()
        width = position.width()
        height = position.height()

        self.gui.x_cropping_slider.setValue((int(x_min), int(x_min + width)))
        self.gui.y_cropping_slider.setValue((int(y_min), int(y_min + height)))
        self.gui.x_slider_label.setText('X: ' + str(int(x_min)) + ', ' +  str(int(x_min + width)))
        self.gui.y_slider_label.setText('Y: ' + str(int(y_min)) + ', ' +  str(int(y_min + height)))

        self.gui.x_cropping_slider.valueChanged.connect(self.update_x_slice)
        self.gui.y_cropping_slider.valueChanged.connect(self.update_y_slice)
        
    def confirm_roi(self):
        x_range = self.gui.x_cropping_slider.value()
        self.x_min_ROI = x_range[0]
        self.x_max_ROI = x_range[1]

        y_range = self.gui.y_cropping_slider.value()
        self.y_min_ROI = y_range[0]
        self.y_max_ROI = y_range[1]

        z_range = self.gui.z_cropping_slider.value()
        self.z_min_ROI = z_range[0]
        self.z_max_ROI = z_range[1]

        print(f'X Range: {self.x_min_ROI} - {self.x_max_ROI}')
        print(f'Y Range: {self.y_min_ROI} - {self.y_max_ROI}')
        print(f'Z Range: {self.z_min_ROI} - {self.z_max_ROI}')
        self.gui.confirm_thresh_button.setEnabled(True)
        self.gui.confirm_roi_button.setDisabled(True)
        self.gui.step3_frame.setGraphicsEffect(None)
        self.gui.step2_frame.setGraphicsEffect(QGraphicsBlurEffect())
    
    
    # Choosing threshold functions
    def update_threshold(self):
        thresh_value = self.gui.threshold_slider.value()
        self.gui.threshold_label.setText('Threshold: ' + str(thresh_value))
        self.lower_threshold = thresh_value[0]
        self.upper_threshold = thresh_value[1]
        self.step = 1
        self.update_slice()
    
    def confirm_threshold(self):
        self.filter_volume, self.overlayed_image = self.calculator.confrim_threshold(self.original_image, self.x_min_ROI, self.x_max_ROI, self.y_min_ROI, self.y_max_ROI, self.z_min_ROI, self.z_max_ROI, self.lower_threshold, self.upper_threshold, self.saved)
        self.step = 2
        self.gui.draw_button.setEnabled(True)
        self.gui.erase_button.setEnabled(True)
        self.gui.grow_button.setEnabled(True)
        self.gui.undo_button.setEnabled(True)
        self.gui.confirm_thresh_button.setDisabled(True)
        self.gui.store_button.setEnabled(True)
        self.gui.step4_frame.setGraphicsEffect(None)
        self.gui.step3_frame.setGraphicsEffect(QGraphicsBlurEffect())
        self.update_slice()
    
    # Erasing and drawing funcitons
    def edit_size(self):
        size = self.gui.edit_slider.value()
        self.gui.edit_label.setText(f"Size: {size}")

    def get_array_indices(self,x, y):
        view_coords = self.gui.image_view.getView().mapToView(pg.Point(x, y))
        x_index = int(view_coords.x())
        y_index = int(view_coords.y())
        return x_index, y_index

    def get_indices_based_on_plane(self, x, y):
        if self.axial:
            x_index, y_index = self.get_array_indices(x, y)
            z_index = self.gui.z_slider.value()
            return x_index, y_index, z_index
        elif self.sagittal:
            z_max = self.original_image.shape[2]
            x_index, z_index = self.get_array_indices(x, y)
            y_index = self.gui.z_slider.value()
            return x_index, y_index, z_max - z_index
        elif self.coronal:
            z_max = self.original_image.shape[2]
            y_index, z_index = self.get_array_indices(x, y)
            x_index = self.gui.z_slider.value()
            return x_index, y_index, z_max - z_index
    
    def erase_clicked(self):
        self.erase_enabled = not self.erase_enabled  
        if self.erase_enabled:
            self.gui.erase_button.setText('Erasing')
            self.draw_enabled = False
            self.grow_enabled = False
            self.gui.draw_button.setText('Draw')
            self.gui.grow_button.setText('Grow From Seeds')
            self.disconnect_mouse_click()
            self.mouse_click_callback = lambda event, array1=self.overlayed_image, array2=self.filter_volume: self.eraseordrawMouseClicked(event, array1, array2, self.lower_threshold, self.upper_threshold)
            self.gui.image_view.scene.sigMouseClicked.connect(self.mouse_click_callback)
        else:
            self.gui.erase_button.setText('Erase')
            
    def draw_clicked(self):
        self.draw_enabled = not self.draw_enabled 
        if self.draw_enabled:
            self.gui.draw_button.setText('Drawing')
            self.erase_enabled = False
            self.grow_enabled = False
            self.gui.erase_button.setText('Erase')
            self.gui.grow_button.setText('Grow From Seeds')
            self.disconnect_mouse_click()
            self.mouse_click_callback = lambda event, array1=self.overlayed_image, array2=self.filter_volume: self.eraseordrawMouseClicked(event, array1, array2, self.lower_threshold, self.upper_threshold)
            self.gui.image_view.scene.sigMouseClicked.connect(self.mouse_click_callback)
        else:
            self.gui.draw_button.setText('Draw')
    
    def grow_clicked(self):
        self.grow_enabled = not self.grow_enabled
        if self.grow_enabled:
            self.gui.grow_button.setText("Growing")
            self.erase_enabled = False
            self.draw_enabled = False
            self.gui.erase_button.setText('Erase')
            self.gui.draw_button.setText('Draw')
            self.disconnect_mouse_click()
            self.mouse_click_callback = lambda event, array1=self.overlayed_image, array2=self.filter_volume: self.grow_seed(event, array1, array2, self.lower_threshold, self.upper_threshold)
            self.gui.image_view.scene.sigMouseClicked.connect(self.mouse_click_callback)
        else:
            self.gui.grow_button.setText('Grow From Seeds')
            
    def disconnect_mouse_click(self):
        if hasattr(self, 'mouse_click_callback'):
            self.gui.image_view.scene.sigMouseClicked.disconnect(self.mouse_click_callback)

    def edit_checked(self, state):
        if state == QtCore.Qt.Checked:
            self.checked = 1
        else:
            self.checked = 0

    def multiple_slices_checked(self, state):
        if state == QtCore.Qt.Checked:
            self.mult_sliced_checked = 1
        else:
            self.mult_sliced_checked = 0
            
    def eraseordrawMouseClicked(self, event, data, data2, threshold_min, threshold_max):
        x, y = event.scenePos().x(), event.scenePos().y()
        x_index, y_index, z_index = self.get_indices_based_on_plane(x, y)
        size = self.gui.edit_slider.value()

        if (size) <= x_index < (data[1].shape[0] - size) and (size) <= y_index < (data[1].shape[0] - size):
            change, change2 = self.calculator.erase_or_draw(size, x_index, y_index, z_index, data, data2, threshold_min, threshold_max, self.erase_enabled, self.draw_enabled, self.original_image, self.axial, self.sagittal, self.coronal, self.checked, self.mult_sliced_checked)
            self.change_history.append(change)
            self.change_history2.append(change2)
            self.update_slice()
        else:
            print("Click in range")

    def grow_seed(self, event, data, data2, threshold_min, threshold_max):
        x, y = event.scenePos().x(), event.scenePos().y()
        x_index, y_index, z_index = self.get_indices_based_on_plane(x, y)
        change, change2 = self.calculator.grow_from_seeds(x_index, y_index, z_index, self.original_image, data, data2, threshold_min, threshold_max)

        self.change_history.append(change)
        self.change_history2.append(change2)
        print('Finished Growing Seed')
        self.update_slice()

    def undo(self):
        if self.change_history:
            self.gui.draw_button.setText('Draw')
            self.gui.erase_button.setText('Erase')
            self.gui.grow_button.setText('Grow From Seeds')
            last_change = self.change_history.pop()
            last_change2 = self.change_history2.pop()

            original_data = last_change["data"]
            original_data2 = last_change2["data"]
            action = last_change["action"]

            # Update the original data back to the data array
            if action == 'erase' or action =='draw':
                x_index = last_change["x_index"]
                y_index = last_change["y_index"]
                z_index = last_change["z_index"]
                x_index = last_change2["x_index"]
                y_index = last_change2["y_index"]
                z_index = last_change2["z_index"]
                self.overlayed_image[x_index - 8:x_index + 8, y_index - 8: y_index + 8, z_index-8: z_index+8] = original_data
                self.filter_volume[x_index - 8:x_index + 8, y_index - 8: y_index + 8, z_index-8: z_index+8] = original_data2
            elif action == 'grow':
                self.overlayed_image = original_data
                self.filter_volume = original_data2
            self.update_slice()

    # Store image in memory 
    def store_file(self):
        self.binary_images.append(self.filter_volume)
        # self.new_window(self.filter_volume)
        self.saved = 1
        self.reset_images()
        self.gui.create_final_button.setEnabled(True)
        self.gui.view_3d.setEnabled(True)
        self.gui.step6_frame.setGraphicsEffect(None)
        print("Stored Progress")

    def create_final_image(self):
        max_z_dim = self.original_image.shape[2]
        combined_bin_image = np.zeros(self.original_image.shape, dtype=np.int64)

        for image in self.binary_images:
            # print(image.shape[2])
            if image.shape[2] != max_z_dim:
                print('Not the same shape')
                padded_image = np.zeros(self.original_image.shape, dtype=np.int64)
                padded_image[:, :, :image.shape[2]] = image
                combined_bin_image += padded_image
            else:
                scale_factor = 100
                scaled_image = (image * scale_factor).astype(np.int64)
                combined_bin_image += scaled_image

        self.convert_to_original_coordinates(combined_bin_image)
        print("Saved Full Binary File")
        # self.new_window(combined_bin_image)
        self.reset_images()
    
    def view_3d(self):
        if len(self.binary_images) != 0:
            max_z_dim = self.original_image.shape[2]
            combined_bin_image = np.zeros(self.original_image.shape, dtype=np.int64)

            for image in self.binary_images:
                if image.shape[2] != max_z_dim:
                    padded_image = np.zeros(self.original_image.shape, dtype=np.int64)
                    padded_image[:, :, :image.shape[2]] = image
                    combined_bin_image += padded_image
                else:
                    scale_factor = 100
                    scaled_image = (image * scale_factor).astype(np.int64)
                    combined_bin_image += scaled_image
            self.new_window(combined_bin_image)
    
    # Create a new window to display 3D
    def new_window(self, array):
        # Create numpy data
            start_time = time.time()
            numpydata = array
            numpydata = numpydata.astype("float")
            numpydata = np.transpose(array, axes=(0, 2, 1))
            dimension = numpydata.shape
            step1 = time.time() - start_time
            print(f'Transposing array {step1}')

            # Copy to vtk
            vtkarr = numpy_support.numpy_to_vtk(numpydata.flatten(), deep=True, array_type=vtk.VTK_FLOAT)
            origin = [0,0,0]
            spacing = [0.5,1,0.5]
            image_data = vtk.vtkImageData()
            image_data.SetDimensions(dimension[0], dimension[1], dimension[2])
            image_data.SetOrigin(origin[0],origin[1],origin[2])
            image_data.SetSpacing(spacing[0], spacing[1], spacing[2])
            image_data.GetPointData().SetScalars(vtkarr)

            step2 = time.time() - start_time - step1
            print(f'Converting to vtk data {step2}')

            self.second_window = UI_VTKshower()
            self.second_window.render_mesh(image_data)
            self.second_window.show()
            step3 = time.time() - start_time - step2 - step1
            print(f'Showing 3D {step3}')
    
    def convert_to_original_coordinates(self, array):
        spacing = self.pixel_spacing
        origin = self.image_position_patient
       
        series_uid = "A" 
        study_uid = 'B'
        array = array[::-1, :, :]
        array = np.rot90(array, k=-1, axes=(0, 1))
        array = np.transpose(array, axes=(2, 0, 1))
        # array = np.transpose(array[::-1, :, :], axes=(1, 2, 0))
        thickness = self.slice_thickness

        # Create a single SimpleITK image for the entire 3D volume
        new_img = sitk.GetImageFromArray(array)
        # new_img.SetPixelIDValue(sitk.sitkFloat32) 
        new_img.SetSpacing([spacing[0], spacing[1], thickness])
        new_img.SetOrigin((origin[0], origin[1], origin[2]))

        options = QFileDialog.Options()
        output_dir = QFileDialog.getExistingDirectory(None, "Save DICOM Files", "", options=options)    

        if not output_dir:
            print("No output directory selected. Exiting.")
            return

        # Create a subdirectory named "DICOM_{date}" within the selected directory
        date_str = time.strftime("%Y%m%d")
        subdirectory = os.path.join(output_dir, f"{self.gui.view_label.text()}_{date_str}")

        if not os.path.exists(subdirectory):
            os.makedirs(subdirectory)

        writer = sitk.ImageFileWriter()
        writer.KeepOriginalImageUIDOn()

        for i in range(self.original_image.shape[2]):
            # Get the current 2D slice from the 3D volume
            image_slice = new_img[:, :, i]
            image_slice = sitk.Cast(image_slice, sitk.sitkUInt16)

            # Set metadata for each slice
            image_slice.SetMetaData("0010|0010", "Output Patient")
            image_slice.SetMetaData("0010|0020", "CT_vessl")
            image_slice.SetMetaData("0020|000d", study_uid)
            image_slice.SetMetaData("0020|000e", series_uid)
            image_slice.SetMetaData("0008|0020", time.strftime("%Y%m%d"))
            image_slice.SetMetaData("0008|0030", time.strftime("%H%M%S"))
            image_slice.SetMetaData("0018|0088", str(thickness))
            image_slice.SetMetaData("0018|9306", str(thickness))
            image_slice.SetMetaData("0028|0030", f"{spacing[0]}\\{spacing[1]}")
            image_position = f"{origin[0]}\\{origin[1]}\\{origin[2] + i*thickness}"
            image_slice.SetMetaData("0020|0032", image_position)
            image_slice.SetMetaData("0018|0050", str(thickness))
            image_slice.SetMetaData("0018|103e", 'CoW')
            image_slice.SetMetaData("0020|0052", series_uid)
            image_slice.SetMetaData("0008|0012", time.strftime("%Y%m%d"))
            image_slice.SetMetaData("0008|0013", time.strftime("%H%M%S"))
            image_slice.SetMetaData("0008|0060", "CT")
            # image_slice.SetMetaData("0020|0032", "\\".join(map(str, new_img.TransformIndexToPhysicalPoint((-125, -125, i)))))
            image_slice.SetMetaData("0020|0037", "1.000000\\0.000000\\0.000000\\0.000000\\1.000000\\0.000000")
            image_slice.SetMetaData("0020|0013", str(i))

            filename = os.path.join(subdirectory, f"{str(i)}.dcm")
            
            writer.SetFileName(filename)
            writer.Execute(image_slice)
        
        print(f"DICOM files saved in: {subdirectory}")

    def reset_images(self):
        if self.original_image is not None:
            self.filter_volume  = None
            self.change_history = [] 
            self.step = 0
            self.overlay = 0
            self.gui.image_view.setLevels(-2048, 3071)
            self.gui.confirm_roi_button.setEnabled(True)
            self.gui.confirm_thresh_button.setDisabled(True)
            self.gui.erase_button.setDisabled(True)
            self.gui.draw_button.setDisabled(True)
            self.gui.grow_button.setDisabled(True)
            self.gui.undo_button.setDisabled(True)
            self.gui.store_button.setDisabled(True)
            self.gui.loadBinaryButton.setDisabled(True)
            self.gui.loadDicomButton.setDisabled(True)
            self.gui.step1_frame.setGraphicsEffect(QGraphicsBlurEffect())
            self.gui.step2_frame.setGraphicsEffect(None)
            self.gui.step3_frame.setGraphicsEffect(QGraphicsBlurEffect())
            self.gui.step4_frame.setGraphicsEffect(QGraphicsBlurEffect())
            print("Reset Image")
    
    # Clear images
    def clear_images(self):
        self.reset_images()
        self.saved = 0
        self.original_image = None
        self.binary_images = []
        self.gui.loadBinaryButton.setEnabled(True)
        self.gui.loadDicomButton.setEnabled(True)
        self.gui.confirm_roi_button.setDisabled(True)
        self.gui.image_view.clear()
        self.gui.create_final_button.setDisabled(True)
        self.gui.view_3d.setDisabled(True)
        self.gui.step1_frame.setGraphicsEffect(None)
        self.gui.step2_frame.setGraphicsEffect(QGraphicsBlurEffect())
        self.gui.step3_frame.setGraphicsEffect(QGraphicsBlurEffect())
        self.gui.step4_frame.setGraphicsEffect(QGraphicsBlurEffect())
        self.gui.view_label.setText("No file loaded")

if __name__ == "__main__":
    app = QApplication([])
    window = CTReaderApp()
    window.show()
    app.exec_()
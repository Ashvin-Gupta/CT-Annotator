from PyQt5 import QtWidgets, QtGui, QtCore
from qtrangeslider import QRangeSlider
import pyqtgraph as pg
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsBlurEffect, QScrollArea

class UI_CTReaderWindow(object):
    def setupUI(self, CTReaderWindow):
        CTReaderWindow.setObjectName("CTReaderWindow")
        self.centralwidget = QtWidgets.QWidget(CTReaderWindow)

        self.main_layout = QtWidgets.QHBoxLayout()
        self.left_column_layout = QtWidgets.QVBoxLayout()
        self.right_column_layout = QtWidgets.QVBoxLayout()

        self.scroll_area = QScrollArea(self.centralwidget)
        self.scroll_area.setWidgetResizable(True)

        # Create a widget to hold the layout of the right column
        self.right_column_widget = QtWidgets.QWidget()
        self.right_column_widget.setLayout(self.right_column_layout)

        # Set the widget as the content of the scroll area
        self.scroll_area.setWidget(self.right_column_widget)

        # Image viewer 
        self.axial_rect = pg.RectROI([0, 0], [1, 1], pen=(255, 0, 0), removable=True)
        self.image_view = pg.ImageView(self.centralwidget)
        self.image_view.getView().addItem(self.axial_rect)

        # Z slider to change view of image 
        self.z_slider = QtWidgets.QSlider(Qt.Horizontal,self.centralwidget)
        self.z_slider.setGeometry(10, 670, 600, 20)

        self.z_slider_label = QtWidgets.QLabel(self.centralwidget)
        self.z_slider_label.setText('0')
        self.z_slider_label.setGeometry(10, 690, 30, 20)

        # Step 1
        self.layout1 = QtWidgets.QVBoxLayout()
        self.step1_frame = QtWidgets.QFrame(self.centralwidget)
        self.step1_frame.setFrameShape(QtWidgets.QFrame.Box)
        self.step1_frame_layout = QtWidgets.QVBoxLayout(self.step1_frame)

        # Label for step 1
        self.step1_label = QtWidgets.QLabel('Step 1: Load File', self.step1_frame)
        self.step1_label.setAlignment(QtCore.Qt.AlignCenter)
        self.step1_frame_layout.addWidget(self.step1_label)

        # Buttons for loading file and dicom
        self.loadBinaryButton = QtWidgets.QPushButton('Load Binary File', self.step1_frame)
        self.loadDicomButton = QtWidgets.QPushButton('Load Dicom File', self.step1_frame)
        self.step1_frame_layout.addWidget(self.loadBinaryButton)
        self.step1_frame_layout.addWidget(self.loadDicomButton)

        self.layout1.addWidget(self.step1_frame)
    

        # Step 2
        self.layout2 = QtWidgets.QVBoxLayout()
        self.step2_frame = QtWidgets.QFrame(self.centralwidget)
        self.step2_frame.setFrameShape(QtWidgets.QFrame.Box)
        self.step2_frame_layout = QtWidgets.QVBoxLayout(self.step2_frame)

        # Label for step 2
        self.step2_label = QtWidgets.QLabel('Step 2: Choose ROI', self.step2_frame)
        self.step2_label.setAlignment(QtCore.Qt.AlignCenter)
        self.step2_frame_layout.addWidget(self.step2_label)

        # Sliders to crop the image 
        # X Slider
        self.x_cropping_slider = QRangeSlider(Qt.Horizontal, self.step2_frame)
        self.x_slider_label = QtWidgets.QLabel('X', self.step2_frame)
        self.x_slider_label.setAlignment(Qt.AlignCenter)
        self.step2_frame_layout.addWidget(self.x_cropping_slider)
        self.step2_frame_layout.addWidget(self.x_slider_label)
        
        # Y Slider
        self.y_cropping_slider = QRangeSlider(Qt.Horizontal, self.step2_frame)
        self.y_slider_label = QtWidgets.QLabel('Y', self.step2_frame)
        self.y_slider_label.setAlignment(Qt.AlignCenter)
        self.step2_frame_layout.addWidget(self.y_cropping_slider)
        self.step2_frame_layout.addWidget(self.y_slider_label)

        # Z Slider
        self.z_cropping_slider = QRangeSlider(Qt.Horizontal, self.step2_frame)
        self.z_cropping_slider_label = QtWidgets.QLabel('Z', self.step2_frame)
        self.z_cropping_slider_label.setAlignment(Qt.AlignCenter)
        self.step2_frame_layout.addWidget(self.z_cropping_slider)
        self.step2_frame_layout.addWidget(self.z_cropping_slider_label)

        # Create a QPushButton for confirming the ROI
        self.confirm_roi_button = QtWidgets.QPushButton('Confirm ROI', self.step2_frame)
        self.step2_frame_layout.addWidget(self.confirm_roi_button)
        self.confirm_roi_button.setDisabled(True)

        self.step2_frame_layout.setSpacing(5)

        self.step2_frame.setGraphicsEffect(QGraphicsBlurEffect())
        self.layout2.addWidget(self.step2_frame)

        # Step 3
        self.layout3 = QtWidgets.QVBoxLayout()
        self.step3_frame = QtWidgets.QFrame(self.centralwidget)
        self.step3_frame.setFrameShape(QtWidgets.QFrame.Box)
        self.step3_frame_layout = QtWidgets.QVBoxLayout(self.step3_frame)

        # Label for step 3
        self.step3_label = QtWidgets.QLabel('Step 3: Choose Threshold', self.step3_frame)
        self.step3_label.setAlignment(QtCore.Qt.AlignCenter)
        self.step3_frame_layout.addWidget(self.step3_label)

        # Threshold Slider and label
        self.threshold_slider = QRangeSlider(Qt.Horizontal, self.step3_frame)
        self.threshold_label = QtWidgets.QLabel('Threshold: 0', self.step3_frame)
        self.threshold_slider.setRange(0, 1000)
        self.step3_frame_layout.addWidget(self.threshold_slider)
        self.step3_frame_layout.addWidget(self.threshold_label)
        
        # Create a QPushButton for confirming the threshold
        self.confirm_thresh_button = QtWidgets.QPushButton('Confirm Threshold', self.step3_frame)
        self.confirm_thresh_button.setText('Confirm Threshold')
        self.confirm_thresh_button.setDisabled(True)
        self.step3_frame_layout.addWidget(self.confirm_thresh_button)

        self.step3_frame.setGraphicsEffect(QGraphicsBlurEffect())
        self.layout3.addWidget(self.step3_frame)

        # Step 4
        self.layout4 = QtWidgets.QVBoxLayout()
        self.layout4.setSpacing(3)
        self.step4_frame = QtWidgets.QFrame(self.centralwidget)
        self.step4_frame.setFrameShape(QtWidgets.QFrame.Box)
        self.step4_frame_layout = QtWidgets.QVBoxLayout(self.step4_frame)

        # Label for step 4
        self.step4_label = QtWidgets.QLabel('Step 4: Edit Image', self.step4_frame)
        self.step4_label.setAlignment(QtCore.Qt.AlignCenter)
        self.step4_frame_layout.addWidget(self.step4_label)

        checkbox_layout = QtWidgets.QHBoxLayout()
        edit_layout = QtWidgets.QHBoxLayout()

        # Erasing and Drawing slider
        self.edit_slider = QtWidgets.QSlider(Qt.Horizontal, self.step4_frame)
        self.edit_slider.setRange(1,5)
        self.edit_label = QtWidgets.QLabel('Size', self.step4_frame)
        self.step4_frame_layout.addWidget(self.edit_slider)
        checkbox_layout.addWidget(self.edit_label, 2)

        self.multiple_slices = QtWidgets.QCheckBox('Multiple Slices', self.step4_frame)
        checkbox_layout.addWidget(self.multiple_slices, 1)

        self.edit_checkbox = QtWidgets.QCheckBox('Threshold', self.step4_frame)
        checkbox_layout.addWidget(self.edit_checkbox, 1)

        self.step4_frame_layout.addLayout(checkbox_layout)
       
        # Create a QPushButton for erasing tool
        self.erase_button = QtWidgets.QPushButton('Erase', self.step4_frame)
        edit_layout.addWidget(self.erase_button)
        self.erase_button.setDisabled(True)

        # Create a QPushButton for painting tool
        self.draw_button = QtWidgets.QPushButton('Draw', self.step4_frame)
        edit_layout.addWidget(self.draw_button)
        self.draw_button.setDisabled(True)
    
        self.step4_frame_layout.addLayout(edit_layout)

        self.grow_button = QtWidgets.QPushButton('Grow From Seeds', self.step4_frame)
        self.step4_frame_layout.addWidget(self.grow_button)
        self.grow_button.setDisabled(True)

        # Create a QPushButton for undo tool
        self.undo_button = QtWidgets.QPushButton('Undo', self.step4_frame)
        self.step4_frame_layout.addWidget(self.undo_button)
        self.undo_button.setDisabled(True)

        self.step4_frame.setGraphicsEffect(QGraphicsBlurEffect())
        self.layout4.addWidget(self.step4_frame)

        # Step 5
        self.layout5 = QtWidgets.QVBoxLayout()

        self.step5_frame = QtWidgets.QFrame(self.centralwidget)
        self.step5_frame.setFrameShape(QtWidgets.QFrame.Box)
        self.step5_frame_layout = QtWidgets.QVBoxLayout(self.step5_frame)

        # Label for step 5
        self.step5_label = QtWidgets.QLabel('Step 5: Store Progress', self.step5_frame)
        self.step5_label.setAlignment(QtCore.Qt.AlignCenter)
        self.step5_frame_layout.addWidget(self.step5_label)

        # Create a QPushButton for saving file 
        self.store_button = QtWidgets.QPushButton('Store', self.step5_label)
        self.store_button.setDisabled(True)
        self.step5_frame_layout.addWidget(self.store_button)

        # Create a QPushButton for resetting images 
        self.reset_button = QtWidgets.QPushButton('Reset', self.step4_frame)
        self.step5_frame_layout.addWidget(self.reset_button)

        # Create a QPushButton for clearing images 
        self.clear_button = QtWidgets.QPushButton('Clear', self.step5_frame)
        self.step5_frame_layout.addWidget(self.clear_button)

        self.layout5.addWidget(self.step5_frame)

        # Step 6
        self.layout6 = QtWidgets.QVBoxLayout()

        self.step6_frame = QtWidgets.QFrame(self.centralwidget)
        self.step6_frame.setFrameShape(QtWidgets.QFrame.Box)
        self.step6_frame_layout = QtWidgets.QVBoxLayout(self.step6_frame)

        # Label for step 6
        self.step6_label = QtWidgets.QLabel('Step 6: Create Dicom Image', self.step6_frame)
        self.step6_label.setAlignment(QtCore.Qt.AlignCenter)
        self.step6_frame_layout.addWidget(self.step6_label)

        # Create a QPushButton for saving file 
        self.create_final_button = QtWidgets.QPushButton('Save', self.step6_frame)
        self.create_final_button.setDisabled(True)
        self.step6_frame_layout.addWidget(self.create_final_button)

        self.view_3d = QtWidgets.QPushButton('View 3D', self.step6_frame)
        self.step6_frame_layout.addWidget(self.view_3d)

        # self.step6_frame.setGraphicsEffect(QGraphicsBlurEffect())
        self.layout6.addWidget(self.step6_frame)        

        checkboxes = QtWidgets.QHBoxLayout()
        self.checkboxes_frame = QtWidgets.QFrame(self.centralwidget)

        self.view_label = QtWidgets.QLabel('View Manager', self.checkboxes_frame)

        self.axial_view = QtWidgets.QCheckBox('Axial View', self.checkboxes_frame)
        self.sagittal_view = QtWidgets.QCheckBox('Sagittal View', self.checkboxes_frame)
        self.coronal_view = QtWidgets.QCheckBox('Coronal View', self.checkboxes_frame)

        checkboxes.addWidget(self.view_label, 4)
        checkboxes.addWidget(self.axial_view, 1)
        checkboxes.addWidget(self.sagittal_view, 1)
        checkboxes.addWidget(self.coronal_view, 1)

        self.checkboxes_frame.setLayout(checkboxes)
        self.left_column_layout.addWidget(self.checkboxes_frame)
        self.left_column_layout.addWidget(self.image_view)
        self.left_column_layout.addWidget(self.z_slider)
        self.left_column_layout.addWidget(self.z_slider_label)


        self.right_column_layout.addLayout(self.layout1)
        self.right_column_layout.addLayout(self.layout2)
        self.right_column_layout.addLayout(self.layout3)
        self.right_column_layout.addLayout(self.layout4)
        self.right_column_layout.addLayout(self.layout5)
        self.right_column_layout.addLayout(self.layout6)
        self.right_column_layout.setSpacing(3)

        self.main_layout.addLayout(self.left_column_layout, 3)
        self.main_layout.addWidget(self.scroll_area, 1)


        self.centralwidget.setLayout(self.main_layout)

        CTReaderWindow.resize(1000, 600)
        CTReaderWindow.setGeometry(50, 50, 1000, 600)


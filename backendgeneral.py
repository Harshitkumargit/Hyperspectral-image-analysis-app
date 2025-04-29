import sys
import os
import spectral
import numpy as np
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QFileDialog, QListWidgetItem, QGraphicsScene, QGraphicsPixmapItem, QGraphicsRectItem, QLabel, QFrame, QGraphicsTextItem, QDialog, QVBoxLayout, QTextEdit, QPushButton
from hyperspectral_ui import Ui_Dialog
from PyQt5.QtGui import QPen, QColor, QFont
from PyQt5.QtCore import Qt, QRectF, QTimer
from segment_anything import sam_model_registry, SamPredictor
import torch
import cv2
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from info_ui import InfoDialog
from function_info_ui import FunctionInfoDialog
from PyQt5.QtWidgets import QApplication
from welcome import WelcomeDialog

class BoundingBox(QGraphicsRectItem): 
    """A resizable and movable bounding box for object selection."""
    def __init__(self, x, y, width, height, label, color):
        super().__init__(x, y, width, height)
        self.label = label
        self.color = color
        self.setPen(QPen(color, 2))  # Use provided color for border
        self.setBrush(QColor(color.red(), color.green(), color.blue(), 50))  # Semi-transparent fill
        self.setFlag(QGraphicsRectItem.ItemIsMovable)
        self.setFlag(QGraphicsRectItem.ItemIsSelectable)
        self.setFlag(QGraphicsRectItem.ItemSendsGeometryChanges)
        
        # Create label text item
        self.label_item = QGraphicsTextItem(self)
        self.label_item.setPlainText(label)
        self.label_item.setDefaultTextColor(color)
        self.label_item.setPos(x, y - 20)  # Position label above the box
        self.label_item.setZValue(1)  # Ensure label is always on top
        
    def updateLabelPosition(self):
        """Update the position of the label when the box moves"""
        self.label_item.setPos(self.rect().x(), self.rect().y() - 20)
        
    def itemChange(self, change, value):
        """Handle item changes to update label position"""
        if change == QGraphicsRectItem.ItemPositionChange:
            self.updateLabelPosition()
        return super().itemChange(change, value)

class UI_Checker(QtWidgets.QDialog, Ui_Dialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        
        # Set the window title
        self.setWindowTitle("Hyperspectral Image Analysis Tool")
        
        # Set application icon
        icon_path = os.path.join(os.path.dirname(__file__), "app_icon.png")
        if os.path.exists(icon_path):
            app_icon = QtGui.QIcon(icon_path)
            self.setWindowIcon(app_icon)
        
        # Set fixed window size
        self.setFixedSize(QtCore.QSize(1140, 900))
        
        # Create temporary directory for application data
        self.temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_data")
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Connect close event
        self.closeEvent = self.on_close
        
        # Create range button for graphicsView_2
        self.rangeButton = QtWidgets.QPushButton(self)
        self.rangeButton.setGeometry(QtCore.QRect(1000, 500, 100, 30))
        self.rangeButton.setText("Set Range")
        self.rangeButton.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.rangeButton.clicked.connect(self.show_range_dialog)
        self.rangeButton.raise_()
        
        # Create reset button
        self.resetButton = QtWidgets.QPushButton(self)
        self.resetButton.setGeometry(QtCore.QRect(1000, 470, 100, 30))
        self.resetButton.setText("Reset")
        self.resetButton.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px;
                font-weight: bold;
                min-height: 30px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.resetButton.clicked.connect(self.reset_plot)
        self.resetButton.raise_()
        
        # # Connect reset button
        # self.resetButton.clicked.connect(self.reset_plot)
        
        # Connect slider to update band display
        self.horizontalSlider.valueChanged.connect(self.on_slider_value_changed)
        
        # Connect doubleSpinBox to update band display
        self.doubleSpinBox.valueChanged.connect(self.on_spinbox_value_changed)
        
        # Configure doubleSpinBox for integer values
        self.doubleSpinBox.setDecimals(0)  # No decimal places
        self.doubleSpinBox.setSingleStep(1)  # Step by 1
        
        # Initialize plot limits
        self.original_x_min = 0
        self.original_x_max = 0
        self.original_y_min = 0
        self.original_y_max = 0
        
        self.setup_scroll_bars()
        
        # Create function info button first
        self.function_info_button = QtWidgets.QPushButton("Function Info", self)
        self.function_info_button.setGeometry(QtCore.QRect(self.width() - 150, 2, 100, 25))
        self.function_info_button.clicked.connect(self.show_function_info_dialog)
        self.function_info_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 2px;
                font-weight: bold;
                margin: 2px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        
        # Create status bar
        self.statusBar = QtWidgets.QStatusBar(self)
        self.statusBar.setFixedHeight(45)
        self.statusBar.setGeometry(-1, self.height() - 45, self.width() + 2, 45)
        
        # Create close button with custom positioning
        self.close_button = QtWidgets.QPushButton("Close", self.statusBar)
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: #ff5555;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-weight: bold;
                margin: 0px 7px 14px 7px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #ff3333;
            }
        """)
        self.close_button.setFixedSize(70, 31)
        
        # Create wrapper for close button
        wrapper = QtWidgets.QWidget(self.statusBar)
        layout = QtWidgets.QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.close_button)
        layout.setAlignment(self.close_button, QtCore.Qt.AlignBottom)
        
        # Add the wrapper to the status bar
        self.statusBar.addPermanentWidget(wrapper)
        self.close_button.clicked.connect(self.close)

        # Update status bar style
        self.statusBar.setStyleSheet("""
            QStatusBar {
                background-color: #2c3e50;
                color: white;
                border-top: 1px solid #34495e;
                padding: 0px;
                margin: 0px;
                min-height: 45px;
                max-height: 45px;
                min-width: 100%;
            }
            QStatusBar::item {
                border: none;
                padding: 0px;
                margin: 0px;
            }
        """)

        # Create info button
        self.info_button = QtWidgets.QPushButton(self)
        self.info_button.setGeometry(QtCore.QRect(self.width() - 50, 2, 40, 40))
        self.info_button.setToolTip("Product Information")
        
        # Try to load the info icon
        info_icon_path = os.path.join(os.path.dirname(__file__), "info22.png")
        if os.path.exists(info_icon_path):
            self.info_button.setIcon(QtGui.QIcon(info_icon_path))
            self.info_button.setIconSize(QtCore.QSize(28, 28))
        else:
            self.info_button.setText("i")
            
        # Set cursor to hand when hovering over info button
        self.info_button.setCursor(QtCore.Qt.PointingHandCursor)
        
        # Connect info button to show dialog
        self.info_button.clicked.connect(self.show_info_dialog)
        
        # Make sure elements stay on top of other UI elements
        self.info_button.raise_()
        self.statusBar.raise_()
        
        # Ensure info button stays in top right corner when window is resized
        self.resizeEvent = self.on_resize_event

        # Disable user editing of textEdit
        self.textEdit.setReadOnly(True)

        # Connect UI elements to functions
        self.pushButton_2.clicked.connect(self.plot_spectral_signature)
        self.pushButton_4.clicked.connect(self.upload_folder)  
        self.pushButton_5.clicked.connect(self.navigate_back)
        self.listWidget.itemClicked.connect(self.on_folder_click)  
        self.pushButton.pressed.connect(self.show_png_image)  
        self.pushButton.released.connect(self.clear_display)
        self.pushButton_7.clicked.connect(self.clear_all_data)

        # Add tooltip to RGB Display button
        self.pushButton.setToolTip("Tap and Hold")
        self.pushButton.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                font-weight: bold;
            }
        """)
        
        # Set up QGraphicsScene for image display
        self.scene = QGraphicsScene()
        self.graphicsView.setScene(self.scene)

        # Add bounding box properties
        self.bounding_boxes = []  # List to store all bounding boxes
        self.current_box_index = 0  # Index of the current box being drawn
        self.drawing = False
        self.drawing_enabled = False
        self.bounding_box = None
        self.start_pos = None

        # Connect SEGMENT INPUT button
        self.pushButton_3.clicked.connect(self.enable_drawing_mode)

        # Connect mouse events for the graphicsView
        self.graphicsView.mousePressEvent = self.start_drawing
        self.graphicsView.mouseMoveEvent = self.update_drawing
        self.graphicsView.mouseReleaseEvent = self.finish_drawing

        # Add storage for bounding box coordinates
        self.stored_box_coords = None

        # Add storage for current mask
        self.current_mask = None

        # Initialize SAM model
        self.sam_predictor = None

        # Connect Analyze Segments button
        self.pushButton_6.clicked.connect(self.analyze_segments)

        # Connect Mask Display button
        self.pushButton_8.pressed.connect(self.show_mask)
        self.pushButton_8.released.connect(self.show_segmented_image)

        self.pushButton_9.clicked.connect(self.export_all_data)  # Connect EXPORT DATA button
        
        self.pushButton_11.clicked.connect(self.plot_full_spectral_signature)  # PLOT - RESPONSE button

        # Then apply styles
        # Set the main window background color and style
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f2f5;
            }
            QPushButton {
                background-color: #2c3e50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
                min-height: 30px;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
            QPushButton:pressed {
                background-color: #2980b9;
            }
            QListWidget {
                background-color: white;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #ecf0f1;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QSlider::groove:horizontal {
                border: 1px solid #bdc3c7;
                height: 8px;
                background: #ecf0f1;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #2980b9;
                border: 1px solid #2980b9;
                width: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }
            QGraphicsView {
                background-color: white;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
            }
            QStatusBar {
                background-color: #2c3e50;
                color: white;
            }
        """)

        # Style individual elements
        self.info_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 2px solid #3498db;
                border-radius: 20px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: rgba(52, 152, 219, 0.1);
            }
        """)

        # Common button style with adjusted dimensions and increased margins
        button_style = """
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #2573a7;
            }
        """

        # Apply the common style to all three buttons
        self.pushButton_4.setStyleSheet(button_style)
        self.pushButton_5.setStyleSheet(button_style)
        self.pushButton_7.setStyleSheet(button_style)

        self.current_folder = ""  
        self.image_path = None  
        self.hdr_path = None  
        self.hdr_data = None  
        self.current_band = 0  
        self._band_cache = {}  # Cache for processed band images
        self._max_cache_size = 10  # Maximum number of bands to cache
        self._spectral_cache = {}  # Cache for spectral signatures
        self._last_mask_hash = None  # Hash of last mask for cache invalidation
        # Add a variable to track the last display state
        self.last_display_state = "hdr"  # Options: "hdr", "segmentation"
        # Store the original HDR band and segmented image for switching between views
        self.segmented_image = None
        # Initialize variables for plot coordinate tracking
        self.current_spectral_data = None
        self.cursor_annotation = None
        self.cursor_vline = None

        # Remove the question mark from the title bar
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # Load folder icon
        self.folder_icon_path = "folder_icon.png"
        if not os.path.exists(self.folder_icon_path):
            self.folder_icon_path = os.path.join(os.path.dirname(__file__), "folder_icon.png")
        self.folder_icon = QtGui.QIcon(self.folder_icon_path) if os.path.exists(self.folder_icon_path) else QtGui.QIcon()

        # Load folder up icon for Upload Folder button
        folder_up_icon_path = os.path.join(os.path.dirname(__file__), "folderupbutton.png")
        if os.path.exists(folder_up_icon_path):
            self.pushButton_4.setIcon(QtGui.QIcon(folder_up_icon_path))
            self.pushButton_4.setIconSize(QtCore.QSize(20, 20))
            self.pushButton_4.setText(" UPLOAD FOLDER")  # Add space after icon
        else:
            self.pushButton_4.setText("UPLOAD FOLDER")

        # Style only listWidget_2 with word wrap
        self.listWidget_2.setWordWrap(True)
        self.listWidget_2.setUniformItemSizes(False)
        self.listWidget_2.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Remove horizontal scrollbar
        self.listWidget_2.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)  # Always show vertical scrollbar
        self.listWidget_2.setStyleSheet("""
            QListWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10pt;
                border: 1px solid #3c3c3c;
                padding: 5px;
            }
            QListWidget::item {
                padding: 3px;
                border-bottom: 1px solid #3c3c3c;
                white-space: pre-wrap;
            }
            QScrollBar:vertical {
                border: none;
                background: #3c3c3c;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #666666;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #7f7f7f;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        # Configure listWidget (folder navigation) scrollbar
        self.listWidget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.listWidget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.listWidget.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #ecf0f1;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)

        # Display welcome message
        # Add empty items for vertical spacing
        for _ in range(2):
            spacing_item = QListWidgetItem("")
            self.listWidget_2.addItem(spacing_item)
        
        # Welcome message with proper formatting
        welcome_title = QListWidgetItem("Welcome to Hyperspectral Image Analysis")
        welcome_title.setTextAlignment(Qt.AlignCenter)
        welcome_title.setForeground(QtGui.QColor("#4CAF50"))  # Green color
        welcome_title.setFont(QtGui.QFont("Consolas", 12, QtGui.QFont.Bold))
        
        welcome_message = QListWidgetItem("Please upload a sample folder to begin your analysis.")
        welcome_message.setTextAlignment(Qt.AlignCenter)
        welcome_message.setForeground(QtGui.QColor("#90CAF9"))  # Light blue color
        welcome_message.setFont(QtGui.QFont("Consolas", 10))
        
        # Add items to listWidget_2
        self.listWidget_2.addItem(welcome_title)
        
        # Add a small spacing between title and message
        spacing_item = QListWidgetItem("")
        self.listWidget_2.addItem(spacing_item)
        
        self.listWidget_2.addItem(welcome_message)

        # Add RGB animation for pushButton (RGB DISPLAY)
        self.rgb_animation_timer = QTimer(self)
        self.rgb_animation_timer.timeout.connect(self.update_rgb_color)
        self.rgb_animation_timer.start(100)  # Update every 100ms
        self.hue = 0

        # Define colors for different objects
        self.box_colors = [
            QtGui.QColor(255, 0, 0),      # Red
            QtGui.QColor(255, 165, 0),    # Orange
            QtGui.QColor(0, 255, 0),      # Green
            QtGui.QColor(128, 0, 128),    # Purple
            QtGui.QColor(255, 0, 255),    # Magenta
            QtGui.QColor(0, 255, 255),    # Cyan
            QtGui.QColor(255, 255, 0),    # Yellow
            QtGui.QColor(255, 140, 0),    # Dark Orange
            QtGui.QColor(147, 112, 219),  # Medium Purple
            QtGui.QColor(255, 105, 180),  # Hot Pink
            QtGui.QColor(255, 120, 100),  # Light Salmon
            QtGui.QColor(144, 238, 144),  # Light Green
            QtGui.QColor(255, 182, 193),  # Light Pink
            QtGui.QColor(0, 0, 0),        # Black
        ]

        # Add this at the end of __init__
        welcome = WelcomeDialog(self)
        welcome.exec_()

    def setup_scroll_bars(self):
        """Set up scroll bars for the text browser"""
        if hasattr(self, 'textBrowser'):
            # Hide the textBrowser's built-in scroll bars
            self.textBrowser.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.textBrowser.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            
            # Enable the custom scroll bars
            self.horizontalScrollBar.setEnabled(True)
            self.verticalScrollBar.setEnabled(True)
            
            # Set scroll bar ranges based on textBrowser content
            self.horizontalScrollBar.setMaximum(self.textBrowser.horizontalScrollBar().maximum())
            self.verticalScrollBar.setMaximum(self.textBrowser.verticalScrollBar().maximum())
            
            # Set scroll bar steps for smoother scrolling
            self.horizontalScrollBar.setSingleStep(10)
            self.verticalScrollBar.setSingleStep(10)
            self.horizontalScrollBar.setPageStep(100)
            self.verticalScrollBar.setPageStep(100)
            
            # Connect scroll bar value changes to textBrowser scrolling
            self.horizontalScrollBar.valueChanged.connect(self._update_horizontal_scroll)
            self.verticalScrollBar.valueChanged.connect(self._update_vertical_scroll)
            
            # Connect textBrowser scroll changes to update custom scroll bars
            self.textBrowser.horizontalScrollBar().valueChanged.connect(self._sync_horizontal_scroll)
            self.textBrowser.verticalScrollBar().valueChanged.connect(self._sync_vertical_scroll)
            
            # Update scroll bars when content changes
            self.textBrowser.textChanged.connect(self.update_scroll_bars)

    def _update_horizontal_scroll(self, value):
        """Update textBrowser horizontal scroll position"""
        if self.textBrowser.horizontalScrollBar().value() != value:
            self.textBrowser.horizontalScrollBar().setValue(value)

    def _update_vertical_scroll(self, value):
        """Update textBrowser vertical scroll position"""
        if self.textBrowser.verticalScrollBar().value() != value:
            self.textBrowser.verticalScrollBar().setValue(value)

    def _sync_horizontal_scroll(self, value):
        """Sync horizontal scroll bar with textBrowser"""
        if self.horizontalScrollBar.value() != value:
            self.horizontalScrollBar.setValue(value)

    def _sync_vertical_scroll(self, value):
        """Sync vertical scroll bar with textBrowser"""
        if self.verticalScrollBar.value() != value:
            self.verticalScrollBar.setValue(value)

    def update_scroll_bars(self):
        """Update scroll bar ranges based on textBrowser content"""
        if hasattr(self, 'textBrowser'):
            # Update horizontal scroll bar
            h_max = self.textBrowser.horizontalScrollBar().maximum()
            self.horizontalScrollBar.setMaximum(h_max)
            self.horizontalScrollBar.setValue(self.textBrowser.horizontalScrollBar().value())
            
            # Update vertical scroll bar
            v_max = self.textBrowser.verticalScrollBar().maximum()
            self.verticalScrollBar.setMaximum(v_max)
            self.verticalScrollBar.setValue(self.textBrowser.verticalScrollBar().value())

    def update_axis_inputs(self):
        """Update axis range input boxes with current plot limits"""
        if hasattr(self, 'figure') and self.figure is not None:
            ax = self.figure.axes[0]
            x_min, x_max = ax.get_xlim()
            y_min, y_max = ax.get_ylim()
            
            # Only update if the input fields exist and are valid
            if (hasattr(self, 'x_min_input') and self.x_min_input is not None and
                hasattr(self, 'x_max_input') and self.x_max_input is not None and
                hasattr(self, 'y_min_input') and self.y_min_input is not None and
                hasattr(self, 'y_max_input') and self.y_max_input is not None):
                try:
                    self.x_min_input.setText(f"{x_min:.2f}")
                    self.x_max_input.setText(f"{x_max:.2f}")
                    self.y_min_input.setText(f"{y_min:.2f}")
                    self.y_max_input.setText(f"{y_max:.2f}")
                except RuntimeError:
                    # If the widgets have been deleted, clean up the references
                    self.cleanup_range_dialog()

    def apply_axis_range(self):
        """Apply new axis range values from input boxes"""
        try:
            # Get values from input boxes
            x_min = float(self.xMinInput.text())
            x_max = float(self.xMaxInput.text())
            y_min = float(self.yMinInput.text())
            y_max = float(self.yMaxInput.text())
            
            # Validate input ranges
            if x_min >= x_max or y_min >= y_max:
                self.log_message("Invalid range: minimum value must be less than maximum value", "error")
                return
                
            if x_min < self.original_x_min or x_max > self.original_x_max:
                self.log_message("X-axis range must be within the original plot limits", "error")
                return
                
            if y_min < self.original_y_min or y_max > self.original_y_max:
                self.log_message("Y-axis range must be within the original plot limits", "error")
                return
            
            # Apply new limits to the plot
            if hasattr(self, 'figure') and self.figure is not None:
                ax = self.figure.axes[0]
                ax.set_xlim(x_min, x_max)
                ax.set_ylim(y_min, y_max)
                self.canvas.draw_idle()
                self.log_message("Axis range updated successfully", "success")
        except ValueError:
            self.log_message("Please enter valid numeric values for axis ranges", "error")
        except Exception as e:
            self.log_message(f"Error updating axis range: {str(e)}", "error")

    def plot_spectral_signature(self):
        """Plot average spectral signatures for all segmented objects in a single graph."""
        if self.hdr_data is None or self.current_mask is None:
            self.log_message("No hyperspectral data or mask available for plotting", "error")
            return

        if not self.bounding_boxes:
            self.log_message("No segmented objects available. Please create bounding boxes first.", "error")
            return

        # Clear the previous plot
        if self.graphicsView_2.scene() is None:
            self.graphicsView_2.setScene(QGraphicsScene())
        self.graphicsView_2.scene().clear()

        # Create a new matplotlib figure
        figure = Figure(figsize=(5, 4))
        canvas = FigureCanvas(figure)
        ax = figure.add_subplot(111)

        # Store all spectral signatures for statistics
        all_signatures = []

        # Calculate global min/max values from full image
        full_signature = np.mean(self.hdr_data, axis=(0, 1))
        global_min = np.min(full_signature)
        global_max = np.max(full_signature)

        # Plot spectral signature for each bounding box
        for box_data in self.bounding_boxes:
            if hasattr(self, 'segmented_hdr_data') and self.segmented_hdr_data is not None:
                # Get the box coordinates
                x1 = int(box_data['x'])
                y1 = int(box_data['y'])
                x2 = int(x1 + box_data['width'])
                y2 = int(y1 + box_data['height'])

                # Get the data for this region
                region_data = self.hdr_data[y1:y2, x1:x2, :]
                
                if region_data.size > 0:
                    # Calculate average spectral signature for this region
                    avg_spectral_signature = np.mean(region_data, axis=(0, 1))
                    all_signatures.append(avg_spectral_signature)

                    # Update global min/max if needed
                    global_min = min(global_min, np.min(avg_spectral_signature))
                    global_max = max(global_max, np.max(avg_spectral_signature))

                    # Convert QColor to RGB values for matplotlib
                    color = box_data['color']
                    rgb_color = (color.red() / 255.0, color.green() / 255.0, color.blue() / 255.0)

                    # Plot with matching color and label
                    line, = ax.plot(avg_spectral_signature, color=rgb_color, 
                                  label=f"{box_data['label']}", linewidth=2)

        if not all_signatures:
            self.log_message("No valid data in the segmented regions", "error")
            return

        # Set labels and title
        ax.set_xlabel("Band Number", fontsize=10)
        ax.set_ylabel("Reflectance", fontsize=10)
        ax.set_title("Average Spectral Signatures of Segmented Objects", fontsize=12, pad=10)

        # Add grid
        ax.grid(True, linestyle='--', alpha=0.7)

        # Add legend with better positioning
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

        # Set fixed x-axis limits based on the number of bands
        num_bands = self.hdr_data.shape[2]
        ax.set_xlim(0, num_bands - 1)

        # Set fixed y-axis limits with padding
        y_range = global_max - global_min
        y_padding = y_range * 0.1
        ax.set_ylim(global_min - y_padding, global_max + y_padding)

        # Store original limits for range validation
        self.original_x_min, self.original_x_max = ax.get_xlim()
        self.original_y_min, self.original_y_max = ax.get_ylim()

        # Only update axis inputs if they exist
        if hasattr(self, 'x_min_input') and hasattr(self, 'x_max_input') and \
           hasattr(self, 'y_min_input') and hasattr(self, 'y_max_input'):
            self.update_axis_inputs()

        # Add band markers at regular intervals
        num_ticks = min(10, num_bands)
        step = num_bands // num_ticks
        tick_positions = np.arange(0, num_bands, step)
        ax.set_xticks(tick_positions)

        # Format tick labels
        ax.tick_params(axis='both', which='major', labelsize=8)

        # Store the spectral signatures for interaction
        self.current_spectral_data = all_signatures

        # Add cursor tracking annotation
        self.cursor_annotation = ax.annotate('',
            xy=(0, 0),
            xytext=(10, 10),
            textcoords='offset points',
            bbox=dict(
                boxstyle='round,pad=0.5',
                fc='yellow',
                alpha=0.7,
                edgecolor='gray'
            ),
            arrowprops=dict(
                arrowstyle='->',
                connectionstyle='arc3,rad=0',
                color='gray'
            )
        )
        self.cursor_annotation.set_visible(False)

        # Add vertical line for cursor tracking
        self.cursor_vline = ax.axvline(x=0, color='gray', alpha=0.5, linestyle='--', visible=False)

        # Adjust layout to prevent cutting off labels
        figure.tight_layout()

        # Connect events for mouse movement and clicking
        self.canvas_mpl_connect_id = canvas.mpl_connect('motion_notify_event', self.on_plot_hover)
        self.canvas_mpl_click_id = canvas.mpl_connect('button_press_event', self.on_plot_click)

        # Add the matplotlib canvas to the QGraphicsScene
        scene = self.graphicsView_2.scene()
        scene.addWidget(canvas)
        self.graphicsView_2.setScene(scene)

        # Save references
        self.canvas = canvas
        self.figure = figure

        # Log statistics for each object
        for i, (box_data, signature) in enumerate(zip(self.bounding_boxes, all_signatures)):
            self.log_message(f"\nStatistics for {box_data['label']}:", "info")
            self.log_message(f"Min intensity: {np.min(signature):.2f}")
            self.log_message(f"Max intensity: {np.max(signature):.2f}")
            self.log_message(f"Mean intensity: {np.mean(signature):.2f}")

    def plot_full_spectral_signature(self):
        """Plot the spectral signature for the entire image."""
        if self.hdr_data is None:
            self.log_message("No hyperspectral data available for plotting", "error")
            return

        # Clear the previous plot
        if self.graphicsView_2.scene() is None:
            self.graphicsView_2.setScene(QGraphicsScene())
        self.graphicsView_2.scene().clear()

        # Create a new matplotlib figure
        figure = Figure(figsize=(5, 4))
        canvas = FigureCanvas(figure)
        ax = figure.add_subplot(111)

        # Calculate average spectral signature for the entire image
        full_signature = np.mean(self.hdr_data, axis=(0, 1))

        # Plot the spectral signature
        ax.plot(full_signature, color='blue', linewidth=2, label='Full Image')

        # Set labels and title
        ax.set_xlabel("Band Number", fontsize=10)
        ax.set_ylabel("Reflectance", fontsize=10)
        ax.set_title("Average Spectral Signature of the Entire Image", fontsize=12, pad=10)

        # Add grid
        ax.grid(True, linestyle='--', alpha=0.7)

        # Add legend
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

        # Set x-axis limits
        num_bands = self.hdr_data.shape[2]
        ax.set_xlim(0, num_bands - 1)

        # Set y-axis limits with padding
        y_min, y_max = np.min(full_signature), np.max(full_signature)
        y_range = y_max - y_min
        y_padding = y_range * 0.1
        ax.set_ylim(y_min - y_padding, y_max + y_padding)

        # Store original limits for range validation
        self.original_x_min, self.original_x_max = ax.get_xlim()
        self.original_y_min, self.original_y_max = ax.get_ylim()

        # Add band markers at regular intervals
        num_ticks = min(10, num_bands)
        step = num_bands // num_ticks
        tick_positions = np.arange(0, num_bands, step)
        ax.set_xticks(tick_positions)

        # Format tick labels
        ax.tick_params(axis='both', which='major', labelsize=8)

        # Store the spectral data for interaction
        self.current_spectral_data = full_signature

        # Add cursor tracking annotation with improved positioning
        self.cursor_annotation = ax.annotate('',
            xy=(0, 0),
            xytext=(10, 10),
            textcoords='offset points',
            bbox=dict(
                boxstyle='round,pad=0.5',
                fc='yellow',
                alpha=0.7,
                edgecolor='gray'
            ),
            arrowprops=dict(
                arrowstyle='->',
                connectionstyle='arc3,rad=0',
                color='gray'
            )
        )
        self.cursor_annotation.set_visible(False)

        # Add vertical line for cursor tracking
        self.cursor_vline = ax.axvline(x=0, color='gray', alpha=0.5, linestyle='--', visible=False)

        # Adjust layout to prevent cutting off labels
        figure.tight_layout()

        # Connect events for mouse movement and clicking
        self.canvas_mpl_connect_id = canvas.mpl_connect('motion_notify_event', self.on_plot_hover)
        self.canvas_mpl_click_id = canvas.mpl_connect('button_press_event', self.on_plot_click)

        # Add the matplotlib canvas to the QGraphicsScene
        scene = self.graphicsView_2.scene()
        scene.addWidget(canvas)
        self.graphicsView_2.setScene(scene)

        # Save references
        self.canvas = canvas
        self.figure = figure

        # Log statistics
        self.log_message("\nFull Image Statistics:", "info")
        self.log_message(f"Min intensity: {np.min(full_signature):.2f}")
        self.log_message(f"Max intensity: {np.max(full_signature):.2f}")
        self.log_message(f"Mean intensity: {np.mean(full_signature):.2f}")

    def on_plot_hover(self, event):
        """Handle mouse movement over the spectral plot."""
        if not hasattr(self, 'statusBar') or not hasattr(self, 'current_spectral_data'):
            return
            
        if event.inaxes:
            # Get x and y coordinates
            x, y = int(round(event.xdata)), event.ydata
            
            # Update vertical line position
            if hasattr(self, 'cursor_vline') and self.cursor_vline:
                self.cursor_vline.set_xdata([x, x])
                self.cursor_vline.set_visible(True)
            
            # Update annotation with coordinates
            if 0 <= x < self.hdr_data.shape[2]:  # Check against actual number of bands
                # Handle both single signature and multiple signatures
                if isinstance(self.current_spectral_data, list):
                    # Multiple signatures case
                    y_values = [sig[x] for sig in self.current_spectral_data]
                    
                    # Format the annotation text for each object
                    annotation_text = f"Band: {x}\nReflectance:\n"
                    for i, value in enumerate(y_values, 1):
                        annotation_text += f"O{i}: {value:.4f}\n"
                    
                    # Use the first value for cursor position
                    y_actual = y_values[0]
                else:
                    # Single signature case
                    y_actual = self.current_spectral_data[x]
                    annotation_text = f"Band: {x}\nReflectance: {y_actual:.4f}"
                
                # Update annotation on graph
                if hasattr(self, 'cursor_annotation') and self.cursor_annotation:
                    # Calculate position based on cursor location
                    ax = self.figure.axes[0]
                    xlim = ax.get_xlim()
                    ylim = ax.get_ylim()
                    
                    # Determine if cursor is in left or right half of plot
                    x_mid = (xlim[1] - xlim[0]) / 2
                    if x < x_mid:
                        # Cursor in left half, place annotation on right
                        x_offset = 20
                        ha = 'left'
                    else:
                        # Cursor in right half, place annotation on left
                        x_offset = -20
                        ha = 'right'
                    
                    # Calculate vertical position with more granular control
                    y_range = ylim[1] - ylim[0]
                    y_position = (y - ylim[0]) / y_range  # 0 to 1 scale
                    
                    # Adjust vertical position based on cursor location with more extreme offsets
                    if y_position > 0.9:  # Very top of plot
                        y_offset = -60  # Move annotation down significantly
                        va = 'top'
                    elif y_position > 0.8:  # Near top
                        y_offset = -50
                        va = 'top'
                    elif y_position > 0.7:  # Upper middle
                        y_offset = -40
                        va = 'top'
                    elif y_position < 0.1:  # Very bottom of plot
                        y_offset = 60  # Move annotation up significantly
                        va = 'bottom'
                    elif y_position < 0.2:  # Near bottom
                        y_offset = 50
                        va = 'bottom'
                    elif y_position < 0.3:  # Lower middle
                        y_offset = 40
                        va = 'bottom'
                    else:  # Middle of plot
                        y_offset = 0
                        va = 'center'
                    
                    # Update annotation position and properties
                    self.cursor_annotation.xy = (x, y_actual)
                    self.cursor_annotation.set_text(annotation_text)
                    self.cursor_annotation.xyann = (x_offset, y_offset)
                    self.cursor_annotation.set_ha(ha)
                    self.cursor_annotation.set_va(va)
                    self.cursor_annotation.set_visible(True)
                
                # Update status bar with more detailed information
                if isinstance(self.current_spectral_data, list):
                    status_text = f"Band: {x}"
                    for i, value in enumerate(y_values, 1):
                        status_text += f" | O{i}: {value:.6f}"
                    self.statusBar.showMessage(status_text)
                else:
                    self.statusBar.showMessage(f"Band: {x} | Value: {y_actual:.6f}")
            else:
                if hasattr(self, 'cursor_annotation') and self.cursor_annotation:
                    self.cursor_annotation.set_visible(False)
                self.statusBar.clearMessage()
            
            # Redraw canvas
            if hasattr(self, 'canvas') and self.canvas:
                self.canvas.draw_idle()
        else:
            # Hide annotation and line when cursor leaves plot
            if hasattr(self, 'cursor_annotation') and self.cursor_annotation:
                self.cursor_annotation.set_visible(False)
            if hasattr(self, 'cursor_vline') and self.cursor_vline:
                self.cursor_vline.set_visible(False)
            if hasattr(self, 'canvas') and self.canvas:
                self.canvas.draw_idle()
            self.statusBar.clearMessage()

    def on_plot_click(self, event):
        """Handle mouse clicks on the spectral plot."""
        if event.inaxes:
            x = int(round(event.xdata))
            
            # Check if x is within valid band range
            if 0 <= x < self.hdr_data.shape[2]:
                # Update the band slider and display
                self.horizontalSlider.setValue(x)
                self.doubleSpinBox.setValue(x)
                self.current_band = x
                self.update_hdr_band()
                
                # Update status bar with band information
                if isinstance(self.current_spectral_data, list):
                    # Multiple signatures case
                    y_values = [sig[x] for sig in self.current_spectral_data]
                    status_text = f"Band: {x}"
                    for i, value in enumerate(y_values, 1):
                        status_text += f" | O{i}: {value:.6f}"
                    self.statusBar.showMessage(status_text)
                else:
                    # Single signature case
                    y_value = self.current_spectral_data[x]
                    self.statusBar.showMessage(f"Band: {x} | Value: {y_value:.6f}")
                
                self.log_message(f"Switched to band {x}", "info")

    def on_scroll(self, event):
        """Handle mouse scroll events for zooming."""
        if event.inaxes:
            ax = self.figure.axes[0]
            x_min, x_max = ax.get_xlim()
            y_min, y_max = ax.get_ylim()
            
            # Check if cursor is near an axis (within 20 pixels)
            x_axis_region = (event.y < 20)  # Bottom of plot
            y_axis_region = (event.x < 20)  # Left of plot
            
            if x_axis_region or y_axis_region:
                # Calculate zoom factor based on scroll direction
                if event.button == 'up':
                    zoom_factor = 1.1  # Zoom in
                else:
                    zoom_factor = 0.9  # Zoom out
                
                if x_axis_region:
                    # Zoom x-axis
                    x_range = x_max - x_min
                    new_x_range = x_range / zoom_factor
                    
                    # Apply zoom limits
                    if new_x_range < (self.original_x_max - self.original_x_min) / self.max_zoom_factor:
                        new_x_range = (self.original_x_max - self.original_x_min) / self.max_zoom_factor
                    elif new_x_range > (self.original_x_max - self.original_x_min) / self.min_zoom_factor:
                        new_x_range = (self.original_x_max - self.original_x_min) / self.min_zoom_factor
                    
                    # Calculate new limits centered on cursor position
                    center_x = event.xdata
                    new_x_min = center_x - new_x_range / 2
                    new_x_max = center_x + new_x_range / 2
                    
                    # Ensure we don't go beyond original limits
                    if new_x_min < self.original_x_min:
                        new_x_min = self.original_x_min
                        new_x_max = new_x_min + new_x_range
                    if new_x_max > self.original_x_max:
                        new_x_max = self.original_x_max
                        new_x_min = new_x_max - new_x_range
                    
                    ax.set_xlim(new_x_min, new_x_max)
                else:  # y-axis
                    # Zoom y-axis
                    y_range = y_max - y_min
                    new_y_range = y_range / zoom_factor
                    
                    # Apply zoom limits
                    if new_y_range < (self.original_y_max - self.original_y_min) / self.max_zoom_factor:
                        new_y_range = (self.original_y_max - self.original_y_min) / self.max_zoom_factor
                    elif new_y_range > (self.original_y_max - self.original_y_min) / self.min_zoom_factor:
                        new_y_range = (self.original_y_max - self.original_y_min) / self.min_zoom_factor
                    
                    # Calculate new limits centered on cursor position
                    center_y = event.ydata
                    new_y_min = center_y - new_y_range / 2
                    new_y_max = center_y + new_y_range / 2
                    
                    # Ensure we don't go beyond original limits
                    if new_y_min < self.original_y_min:
                        new_y_min = self.original_y_min
                        new_y_max = new_y_min + new_y_range
                    if new_y_max > self.original_y_max:
                        new_y_max = self.original_y_max
                        new_y_min = new_y_max - new_y_range
                    
                    ax.set_ylim(new_y_min, new_y_max)
                
                # Redraw the plot
                self.canvas.draw_idle()

    def upload_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.current_folder = os.path.normpath(folder_path)  # Normalize path
            self.display_folder_contents(self.current_folder)

    def navigate_back(self):
        if self.current_folder:
            parent_folder = os.path.dirname(self.current_folder)
            if os.path.exists(parent_folder) and parent_folder != self.current_folder:
                self.current_folder = parent_folder
                self.display_folder_contents(parent_folder)

    def display_folder_contents(self, folder_path):
        """Displays the list of subfolders sorted by date (latest first)."""
        self.listWidget.clear()
        folder_path = os.path.normpath(folder_path)  

        if not os.path.exists(folder_path):
            self.log_message(f"Error: The folder '{folder_path}' does not exist.", "error")
            return

        folders = [
            (item, os.path.getmtime(os.path.join(folder_path, item))) 
            for item in os.listdir(folder_path) 
            if os.path.isdir(os.path.join(folder_path, item))
        ]

        folders.sort(key=lambda x: x[1], reverse=True)  

        for folder_name, _ in folders:
            list_item = QListWidgetItem(self.folder_icon, folder_name)
            self.listWidget.addItem(list_item)
        
        QtCore.QTimer.singleShot(100, self.listWidget.scrollToTop)

    def on_folder_click(self, item):
        """Handles clicking on a folder and processes it."""
        selected_folder = os.path.join(self.current_folder, item.text())
        selected_folder = os.path.normpath(selected_folder)  # Normalize path

        if os.path.exists(selected_folder):
            self.process_selected_folder(selected_folder)
        else:
            self.log_message(f"Error: The folder '{selected_folder}' does not exist.", "error")

    def process_selected_folder(self, folder_path):
        """Clears previous data and processes the selected folder."""
        folder_path = os.path.normpath(folder_path)  

        if not os.path.exists(folder_path):
            self.log_message(f"Error: The folder '{folder_path}' does not exist.", "error")
            return  

        # Display the selected folder name
        folder_name = os.path.basename(folder_path)
        self.log_message(f"Selected folder: {folder_name}", "info")

        self.clear_previous_data()
        self.current_folder = folder_path
        self.image_path = None  
        self.hdr_path = None  
        self.hdr_data = None  

        # Search for PNG files in the selected folder and subfolders
        png_files = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(".png"):
                    png_files.append(os.path.join(root, file))
        
        # If PNG files found, use the first one
        if png_files:
            self.image_path = png_files[0]
            if len(png_files) > 1:
                self.log_message(f"Multiple PNG files found. Using: {os.path.basename(self.image_path)}", "info")

        # Search for HDR files in the selected folder and subfolders
        hdr_files = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(".hdr"):
                    hdr_path = os.path.join(root, file)
                    # Check for corresponding raw file
                    base_name = os.path.splitext(hdr_path)[0]
                    raw_exists = any(
                        os.path.exists(base_name + ext) 
                        for ext in ['.raw', '.RAW', '.bil', '.BIL', '.bsq', '.BSQ']
                    )
                    if raw_exists:
                        hdr_files.append(hdr_path)

        # If HDR files found, use the first one
        if hdr_files:
            self.hdr_path = hdr_files[0]
            if len(hdr_files) > 1:
                self.log_message(f"Multiple HDR files found. Using: {os.path.basename(self.hdr_path)}", "info")
            
            # Load the HDR file and adjust UI based on actual band count
            self.load_hdr_file()
        else:
            self.log_message("No HDR files with corresponding raw data found", "warning")

        self.update_ui()

    def clear_previous_data(self):
        """Clears all previously loaded data before loading a new folder."""
        self.scene.clear()  
        self.hdr_data = None
        self.image_path = None
        self.hdr_path = None
        self.current_band = 0
        self.horizontalSlider.setValue(0)
        self.listWidget.clearSelection()  

    def update_ui(self):
        """Refresh the UI after processing a new folder."""
        self.scene.clear()  

        if self.hdr_data is not None:
            # Set the range for both slider and spinbox
            max_band = self.hdr_data.shape[2] - 1
            self.horizontalSlider.setMinimum(0)
            self.horizontalSlider.setMaximum(max_band)
            self.doubleSpinBox.setMinimum(0)
            self.doubleSpinBox.setMaximum(max_band)
            self.current_band = 0
            self.update_hdr_band()

        elif self.image_path and os.path.exists(self.image_path):
            self.show_png_image()  

    def load_hdr_file(self):
        """Load and process HDR file with automatic band detection."""
        try:
            hdr_image = spectral.open_image(self.hdr_path)
            self.hdr_data = hdr_image.load()
            
            if self.hdr_data is None or len(self.hdr_data.shape) < 3:
                raise ValueError("Invalid HDR file structure")
                
            # Add validation for data dimensions
            if self.hdr_data.shape[0] == 0 or self.hdr_data.shape[1] == 0:
                raise ValueError("Empty image dimensions")
                
            # Get the number of bands from the loaded data
            num_bands = self.hdr_data.shape[2]
            
            # Update UI elements based on the actual number of bands
            self.horizontalSlider.setMinimum(0)
            self.horizontalSlider.setMaximum(num_bands - 1)
            self.doubleSpinBox.setMinimum(0)
            self.doubleSpinBox.setMaximum(num_bands - 1)
            self.doubleSpinBox.setDecimals(0)  # Set decimals to 0 for integer band numbers
            self.doubleSpinBox.setSingleStep(1)  # Set step size to 1
            
            # Log the number of bands found
            self.log_message(f"Loaded HDR file with {num_bands} bands", "info")
            
            # Initialize to first band and update display
            self.current_band = 0
            self.update_hdr_band()
            self.log_message("HDR file loaded successfully", "success")
        except FileNotFoundError:
            self.log_message("Error: HDR file not found", "error")
        except ValueError as e:
            self.log_message(f"Error: {str(e)}", "error")
        except Exception as e:
            self.log_message(f"Unexpected error: {str(e)}", "error")

    def update_hdr_band(self):
        """Modified to handle both regular and segmented views"""
        if self.hdr_data is not None:
            self.current_band = self.horizontalSlider.value()

            # Check if we're in segmented view
            if hasattr(self, 'segmented_hdr_data') and self.segmented_hdr_data is not None:
                self.update_segmented_band(self.current_band)
            else:
                # Original HDR band display code
                band_image = self.hdr_data[:, :, self.current_band]
                band_image = np.squeeze(band_image)
                band_image = np.rot90(band_image, k=-1)
                
                min_val, max_val = np.min(band_image), np.max(band_image)
                if max_val > min_val:
                    band_image = ((band_image - min_val) / (max_val - min_val) * 255).astype(np.uint8)
                else:
                    band_image = np.zeros_like(band_image, dtype=np.uint8)

                height, width = band_image.shape
                band_image_bytes = band_image.tobytes()
                image = QtGui.QImage(band_image_bytes, width, height, width, QtGui.QImage.Format_Grayscale8)
                pixmap = QtGui.QPixmap.fromImage(image)

                self.scene.clear()
                self.scene.addItem(QGraphicsPixmapItem(pixmap))
                self.graphicsView.fitInView(self.scene.itemsBoundingRect(), QtCore.Qt.KeepAspectRatio)
                self.log_message("HDR band updated successfully", "success")

    def display_hdr_data(self, data):
        """Display HDR data in the graphics view."""
        try:
            if data is None:
                self.log_message("No data to display", "error")
                return
                
            height, width = data.shape
            if height == 0 or width == 0:
                self.log_message("Invalid image dimensions", "error")
                return
                
            # Ensure data is in the correct range [0, 1]
            data = np.clip(data, 0, 1)
            
            # Convert to uint8 and create contiguous array
            img_data = (data * 255).astype(np.uint8)
            
            # Create QImage directly from numpy array
            bytes_per_line = width
            image = QtGui.QImage(img_data.data, width, height, bytes_per_line, QtGui.QImage.Format_Grayscale8)
            
            # Create a deep copy of the image to ensure data persistence
            image = image.copy()
            
            # Create pixmap and display
            pixmap = QtGui.QPixmap.fromImage(image)
            self.scene.clear()
            pixmap_item = QGraphicsPixmapItem(pixmap)
            self.scene.addItem(pixmap_item)
            
            # Fit to view while maintaining aspect ratio
            self.graphicsView.setSceneRect(pixmap_item.boundingRect())
            self.graphicsView.fitInView(self.scene.itemsBoundingRect(), QtCore.Qt.KeepAspectRatio)
            
        except Exception as e:
            self.log_message(f"Error displaying HDR data: {str(e)}", "error")
            import traceback
            self.log_message(traceback.format_exc(), "error")

    def show_png_image(self):
        """Display a PNG image in the graphics view."""
        try:
            # Check if HDR data has only 10 bands
            if self.hdr_data is not None and self.hdr_data.shape[2] == 10:
                self.log_message("No PNG image available for this sample (10-band HDR data)", "info")
                return
                
            if self.image_path and os.path.exists(self.image_path):
                image = QtGui.QImage(self.image_path)
                if not image.isNull():
                    pixmap = QtGui.QPixmap.fromImage(image)
                    self.scene.clear()
                    self.scene.addItem(QGraphicsPixmapItem(pixmap))
                    self.graphicsView.fitInView(self.scene.itemsBoundingRect(), QtCore.Qt.KeepAspectRatio)
                    self.log_message("PNG image displayed successfully", "success")
                else:
                    self.log_message("Error: Invalid PNG file", "error")
            else:
                self.log_message("Error: PNG file not found", "error")
        except Exception as e:
            self.log_message(f"Error displaying PNG image: {str(e)}", "error")

    def clear_display(self):
        self.scene.clear()
        self.update_ui()

    def clear_all_data(self):
        """Clears all displayed data including images, plots, masks, and segmentation data."""
        # Clear the main image display
        self.scene.clear()

        # Clear the plot in graphicsView_2
        if hasattr(self, 'graphicsView_2'):
            if self.graphicsView_2.scene() is None:
                self.graphicsView_2.setScene(QGraphicsScene())
            self.graphicsView_2.scene().clear()

        # Reset all data variables
        self.hdr_data = None
        self.image_path = None
        self.hdr_path = None
        self.current_band = 0
        self.current_mask = None
        self.bounding_boxes = []  # Clear the list of bounding boxes
        self.current_box_index = 0  # Reset the box index
        self.segmented_hdr_data = None
        self.current_spectral_data = None
        self._band_cache.clear()
        self._spectral_cache.clear()
        self._last_mask_hash = None

        # Reset UI elements
        self.horizontalSlider.setValue(0)
        self.doubleSpinBox.setValue(0)
        self.horizontalSlider.setMinimum(0)
        self.horizontalSlider.setMaximum(99)
        self.doubleSpinBox.setMinimum(0)
        self.doubleSpinBox.setMaximum(99)

        # Clear any matplotlib plots
        if hasattr(self, 'canvas'):
            if self.graphicsView_2.scene() is not None:
                self.graphicsView_2.scene().clear()
            self.canvas = None
            self.figure = None
            self.cursor_annotation = None
            self.cursor_vline = None

        # Reset drawing mode
        self.drawing = False
        self.drawing_enabled = False
        self.start_pos = None
        self.bounding_box = None

        # Clear SAM predictor
        if hasattr(self, 'sam_predictor'):
            self.sam_predictor = None

        # Preserve the original folder list without navigating into any subfolder
        if self.current_folder and os.path.exists(self.current_folder):
            self.display_folder_contents(self.current_folder)

        # Clear selection without changing content
        self.listWidget.clearSelection()

        self.log_message("All data cleared successfully", "success")

    def restore_hdr_image(self):
        """Restore HDR display when the RGB Display button is released."""
        self.scene.clear()
        if self.hdr_data is not None:
            self.update_hdr_band()

    def enable_drawing_mode(self):
        """Enable/disable drawing mode when SEGMENT INPUT is clicked"""
        self.drawing_enabled = not self.drawing_enabled  # Toggle drawing mode
        
        if self.drawing_enabled:
            try:
                # Remove existing bounding box if present
                if self.bounding_box and self.bounding_box.scene():
                    self.scene.removeItem(self.bounding_box)
            except RuntimeError:
                pass
            self.bounding_box = None
            self.log_message("Click and drag on the image to draw bounding boxes. Click SELECT ROI again to stop.", "info")
        else:
            self.log_message("Drawing mode disabled. Click SELECT ROI to draw more boxes.", "info")

    def start_drawing(self, event):
        """Start drawing the bounding box"""
        if hasattr(self, 'drawing_enabled') and self.drawing_enabled and event.button() == Qt.LeftButton:
            self.drawing = True
            scene_pos = self.graphicsView.mapToScene(event.pos())
            self.start_pos = scene_pos

            # Create new bounding box with label and color
            label = f"Object {self.current_box_index + 1}"
            color = self.box_colors[self.current_box_index % len(self.box_colors)]
            
            self.bounding_box = BoundingBox(
                scene_pos.x(),
                scene_pos.y(),
                0,  # Initial width
                0,  # Initial height
                label,
                color
            )
            self.scene.addItem(self.bounding_box)

    def update_drawing(self, event):
        """Update the bounding box size while drawing"""
        if self.drawing and self.bounding_box and self.start_pos:
            current_pos = self.graphicsView.mapToScene(event.pos())

            # Calculate width and height
            width = current_pos.x() - self.start_pos.x()
            height = current_pos.y() - self.start_pos.y()

            # Update bounding box geometry
            x = self.start_pos.x() if width >= 0 else current_pos.x()
            y = self.start_pos.y() if height >= 0 else current_pos.y()
            width = abs(width)
            height = abs(height)

            self.bounding_box.setRect(x, y, width, height)

    def finish_drawing(self, event):
        """Finish drawing the bounding box"""
        if self.drawing:
            self.drawing = False
            if self.bounding_box:
                rect = self.bounding_box.rect()
                # Store the coordinates when finishing the drawing
                box_data = {
                    'x': rect.x(),
                    'y': rect.y(),
                    'width': rect.width(),
                    'height': rect.height(),
                    'label': self.bounding_box.label,
                    'color': self.bounding_box.color
                }
                self.bounding_boxes.append(box_data)
                self.current_box_index += 1
                self.log_message(f"Bounding box {self.bounding_box.label} created: x={rect.x():.1f}, y={rect.y():.1f}, "
                              f"width={rect.width():.1f}, height={rect.height():.1f}", "info")
                # Clear the current bounding box but keep drawing mode enabled
                self.bounding_box = None

    def initialize_sam_model(self):
        """Initialize the SAM model if not already initialized"""
        if self.sam_predictor is None:
            try:
                # # Get the base directory for the executable
                # if getattr(sys, 'frozen', False):
                #     # Running as compiled executable
                #     base_dir = sys._MEIPASS
                # else:
                #     # Running as script
                #       base_dir = os.path.dirname(os.path.abspath(__file__))
                self.show_loading_overlay()
                QtWidgets.QApplication.processEvents()

                # Update path to SAM model checkpoint
                sam_checkpoint = os.path.join(os.path.dirname(__file__), "sam_vit_h_4b8939.pth")
                model_type = "vit_h"
                device = "cpu"  # Force CPU for better compatibility
                
                sam = sam_model_registry[model_type](checkpoint=sam_checkpoint)
                sam.to(device=device)
                self.sam_predictor = SamPredictor(sam)
                self.log_message("SAM model initialized successfully", "success")
                return True
            except Exception as e:
                self.log_message(f"Error initializing SAM model: {e}", "error")
                return False
            finally:
                self.hide_loading_overlay()
        return True

    def show_loading_overlay(self):
        """Show loading overlay with 'Loading...' text"""
        # Create semi-transparent overlay
        self.overlay = QFrame(self)
        self.overlay.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 100);
            }
        """)
        self.overlay.setGeometry(self.rect())
        
        # Create loading text box
        self.loading_box = QLabel(self.overlay)
        self.loading_box.setText("Processing...")
        self.loading_box.setStyleSheet("""
            QLabel {
                background-color: white;
                color: black;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        
        self.loading_box.adjustSize()
        
        # Center the loading box
        box_x = (self.width() - self.loading_box.width()) // 2
        box_y = (self.height() - self.loading_box.height()) // 2
        self.loading_box.move(box_x, box_y)
        
        # Show overlay and change cursor
        self.overlay.show()
        self.overlay.raise_()  # Bring overlay to front
        self.loading_box.raise_()  # Ensure loading box is visible
        QApplication.processEvents()  # Force update of the UI
        
        # Change cursor and disable interaction
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.setEnabled(False)  # Disable user interaction

    def hide_loading_overlay(self):
        """Hide loading overlay and restore normal state"""
        if hasattr(self, 'overlay'):
            self.overlay.hide()
            self.overlay.deleteLater()
            QApplication.restoreOverrideCursor()  # Restore normal cursor
            self.setEnabled(True)  # Re-enable user interaction

    def analyze_segments(self):
        """Perform segmentation using SAM model and display results"""
        if not self.bounding_boxes or self.hdr_data is None:
            self.log_message("Please draw bounding boxes and ensure HDR data is loaded", "error")
            return
                
        # Create custom dialog without icons
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Confirm Segmentation")
        dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # Create layout
        layout = QtWidgets.QVBoxLayout()
        
        # Add message label
        message = QtWidgets.QLabel("This process may take some time. Are you sure you want to proceed with the segmentation?")
        layout.addWidget(message)
        
        # Create button box with wider buttons
        button_box = QtWidgets.QDialogButtonBox(Qt.Horizontal)
        yes_button = QtWidgets.QPushButton("Yes")
        no_button = QtWidgets.QPushButton("No")
        
        # Set fixed width for buttons
        button_width = 65  # Adjust this value to make buttons wider or narrower
        yes_button.setFixedWidth(button_width)
        no_button.setFixedWidth(button_width)
        
        # Add buttons to button box
        button_box.addButton(yes_button, QtWidgets.QDialogButtonBox.AcceptRole)
        button_box.addButton(no_button, QtWidgets.QDialogButtonBox.RejectRole)
        
        # Connect button signals
        yes_button.clicked.connect(dialog.accept)
        no_button.clicked.connect(dialog.reject)
        
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        
        # Show dialog and get result
        reply = dialog.exec_()
        
        if reply == QtWidgets.QDialog.Rejected:
            self.log_message("Segmentation cancelled by user", "info")
            return
                
            self.show_loading_overlay()
            
        try:
            import time
            start_time = time.time()
            
            if not self.initialize_sam_model():
                self.log_message("Failed to initialize SAM model", "error")
                return
            
            device = "GPU" if torch.cuda.is_available() else "CPU"
            # device ="CPU"
            self.log_message(f"Running segmentation on {device}", "info")
            
            # Get the current band image for segmentation
            current_band_image = self.hdr_data[:, :, self.current_band]
            current_band_image = np.rot90(current_band_image, k=-1)  # Rotate for display
            
            # Normalize the image
            normalized_image = ((current_band_image - current_band_image.min()) / 
                              (current_band_image.max() - current_band_image.min()) * 255).astype(np.uint8)
            rgb_image = cv2.cvtColor(normalized_image, cv2.COLOR_GRAY2RGB)

            # Set image in predictor
            self.sam_predictor.set_image(rgb_image)

            # Scale box coordinates
            image_height, image_width = rgb_image.shape[:2]
            view_rect = self.graphicsView.viewport().rect()
            scale_x = image_width / view_rect.width()
            scale_y = image_height / view_rect.height()

            # Initialize combined mask
            combined_mask = np.zeros((image_height, image_width), dtype=np.uint8)
            
            # Store individual masks and scores for metrics
            all_masks = []
            all_scores = []
            
            # Process each bounding box
            for box_data in self.bounding_boxes:
                x1 = int(box_data['x'] * scale_x)
                y1 = int(box_data['y'] * scale_y)
                x2 = int((box_data['x'] + box_data['width']) * scale_x)
                y2 = int((box_data['y'] + box_data['height']) * scale_y)

                # Ensure coordinates are within bounds
                x1 = max(0, min(x1, image_width - 1))
                y1 = max(0, min(y1, image_height - 1))
                x2 = max(0, min(x2, image_width - 1))
                y2 = max(0, min(y2, image_height - 1))

                box = np.array([x1, y1, x2, y2])

                # Get masks from SAM
                masks, scores, _ = self.sam_predictor.predict(
                    box=box,
                    multimask_output=True
                )

                # Store masks and scores
                all_masks.append(masks)
                all_scores.append(scores)

                # Select the mask with highest score
                best_mask_idx = np.argmax(scores)
                best_mask = masks[best_mask_idx]
                best_score = scores[best_mask_idx]

                # Add the mask to the combined mask
                combined_mask = np.logical_or(combined_mask, best_mask)

            # Store the combined mask
            self.current_mask = combined_mask
                
            # Create a masked version of the HDR data
            self.segmented_hdr_data = np.zeros_like(self.hdr_data)
            
            # Rotate mask back to match HDR data orientation
            rotated_mask = np.rot90(self.current_mask, k=1)
            
            # Create 3D mask
            mask_3d = np.expand_dims(rotated_mask, axis=2)
            mask_3d = np.repeat(mask_3d, self.hdr_data.shape[2], axis=2)
            
            # Apply mask to HDR data
            self.segmented_hdr_data = np.where(mask_3d, self.hdr_data, 0)

            # Display the current band
            self.update_segmented_band(self.current_band)

            # Calculate and display metrics
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Calculate average confidence score
            avg_confidence = np.mean([np.max(scores) for scores in all_scores])
            
            # Calculate IoU (Intersection over Union) for each box
            ious = []
            for i, masks in enumerate(all_masks):
                best_mask = masks[np.argmax(all_scores[i])]
                # Create ground truth mask from bounding box
                gt_mask = np.zeros_like(best_mask)
                box = self.bounding_boxes[i]
                x1, y1 = int(box['x'] * scale_x), int(box['y'] * scale_y)
                x2, y2 = int((box['x'] + box['width']) * scale_x), int((box['y'] + box['height']) * scale_y)
                gt_mask[y1:y2, x1:x2] = 1
                
                # Calculate IoU
                intersection = np.logical_and(best_mask, gt_mask).sum()
                union = np.logical_or(best_mask, gt_mask).sum()
                iou = intersection / union if union > 0 else 0
                ious.append(iou)
            
            avg_iou = np.mean(ious)
            
            # Calculate mask coverage
            total_pixels = image_height * image_width
            segmented_pixels = np.sum(combined_mask)
            coverage_percentage = (segmented_pixels / total_pixels) * 100
            
            # Calculate segmentation quality metrics
            # 1. Boundary smoothness (using edge detection)
            edges = cv2.Canny(combined_mask.astype(np.uint8) * 255, 100, 200)
            edge_pixels = np.sum(edges > 0)
            boundary_smoothness = 1.0 - (edge_pixels / (2 * np.sqrt(segmented_pixels))) if segmented_pixels > 0 else 0
            
            # 2. Segmentation compactness (perimeter^2 / area)
            contours, _ = cv2.findContours(combined_mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                total_perimeter = sum(cv2.arcLength(contour, True) for contour in contours)
                total_area = segmented_pixels
                compactness = (4 * np.pi * total_area) / (total_perimeter * total_perimeter) if total_perimeter > 0 else 0
            else:
                compactness = 0
            
            # Log metrics
            self.log_message("\nSegmentation Metrics:", "info")
            self.log_message(f"Execution Time: {execution_time:.2f} seconds", "info")
            self.log_message(f"Average Confidence Score: {avg_confidence:.4f}", "info")
            self.log_message(f"Average IoU: {avg_iou:.4f}", "info")
            self.log_message(f"Mask Coverage: {coverage_percentage:.2f}%", "info")
            self.log_message(f"Boundary Smoothness: {boundary_smoothness:.4f}", "info")
            self.log_message(f"Segmentation Compactness: {compactness:.4f}", "info")
            
            # Log individual box metrics
            self.log_message("\nIndividual Box Metrics:", "info")
            for i, (iou, score) in enumerate(zip(ious, [np.max(scores) for scores in all_scores])):
                self.log_message(f"Box {i+1}: IoU = {iou:.4f}, Confidence = {score:.4f}", "info")

        except Exception as e:
            self.log_message(f"Error during segmentation: {e}", "error")
            import traceback
            print(traceback.format_exc())
        finally:
            self.hide_loading_overlay()

    def update_segmented_band(self, band_index):
        """Display the specified band of the segmented data"""
        if hasattr(self, 'segmented_hdr_data') and self.segmented_hdr_data is not None:
            try:
                # Get the band data
                band_image = self.segmented_hdr_data[:, :, band_index].copy()
                
                # Rotate the band image for display
                band_image = np.rot90(band_image, k=-1)
                
                # Check if this is a 10-band sample
                is_10_band = self.hdr_data.shape[2] == 10
                
                if is_10_band:
                    # Create initial mask for segmented regions
                    segmented_mask = (band_image > 0)
                    
                    if np.any(segmented_mask):
                        # Create a working copy for processing
                        processed_image = np.zeros_like(band_image, dtype=np.float32)
                        
                        # Get values only from segmented regions
                        segmented_values = band_image[segmented_mask]
                        
                        # Calculate robust percentiles for normalization
                        p1, p99 = np.percentile(segmented_values[segmented_values > 0], (1, 99))
                        
                        # Normalize the segmented regions
                        processed_image[segmented_mask] = np.clip(
                            ((band_image[segmented_mask] - p1) / (p99 - p1) * 255),
                            0, 255
                        )
                        
                        # Convert to uint8 for further processing
                        processed_image = processed_image.astype(np.uint8)
                        
                        # Apply CLAHE to the entire image
                        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
                        enhanced_image = clahe.apply(processed_image)
                        
                        # Keep only the enhanced regions where we had segmented data
                        processed_image = np.zeros_like(enhanced_image)
                        processed_image[segmented_mask] = enhanced_image[segmented_mask]
                        
                        # Strong contrast enhancement for segmented regions
                        alpha = 2.0  # Increased contrast
                        beta = 30    # Increased brightness
                        enhanced = cv2.convertScaleAbs(processed_image, alpha=alpha, beta=beta)
                        
                        # Create final image
                        band_image = np.zeros_like(enhanced)
                        band_image[segmented_mask] = enhanced[segmented_mask]
                        
                        # Add edge enhancement to make boundaries more visible
                        kernel = np.ones((3,3), np.uint8)
                        dilated = cv2.dilate(band_image, kernel, iterations=1)
                        edge = dilated - band_image
                        band_image[edge > 0] = 255  # Make edges white
                    else:
                        band_image = np.zeros_like(band_image, dtype=np.uint8)
                else:
                    # Standard normalization for other samples
                    non_zero_mask = band_image != 0
                    if np.any(non_zero_mask):
                        min_val = np.min(band_image[non_zero_mask])
                        max_val = np.max(band_image[non_zero_mask])
                        if max_val > min_val:
                            normalized = np.zeros_like(band_image)
                            normalized[non_zero_mask] = ((band_image[non_zero_mask] - min_val) / (max_val - min_val) * 255)
                            band_image = normalized.astype(np.uint8)
                    else:
                        band_image = np.zeros_like(band_image, dtype=np.uint8)

                # Convert to QImage and display
                height, width = band_image.shape
                band_image_bytes = band_image.tobytes()
                image = QtGui.QImage(band_image_bytes, width, height, width, QtGui.QImage.Format_Grayscale8)
                pixmap = QtGui.QPixmap.fromImage(image)

                self.scene.clear()
                self.scene.addItem(QGraphicsPixmapItem(pixmap))
                self.graphicsView.fitInView(self.scene.itemsBoundingRect(), QtCore.Qt.KeepAspectRatio)
                
                # Calculate and log display coverage
                non_zero_count = np.count_nonzero(band_image)
                total_pixels = band_image.size
                coverage = (non_zero_count / total_pixels) * 100
                self.log_message(f"Display coverage: {coverage:.2f}%", "info")
                
                if coverage < 0.1:
                    self.log_message("Warning: Very low display coverage. Try adjusting contrast parameters.", "error")
                
            except Exception as e:
                self.log_message(f"Error displaying segmented band: {str(e)}", "error")
                import traceback
                print(traceback.format_exc())

    def show_segmented_image(self):
        """Show the segmented image"""
        if not hasattr(self, 'segmented_hdr_data') or self.segmented_hdr_data is None:
            self.log_message("No segmented image available to display", "error")
            return

        # Get the current band of the segmented data
        band_image = self.segmented_hdr_data[:, :, self.current_band]
        
        # Rotate the band image for display
        band_image = np.rot90(band_image, k=-1)
        
        # Normalize the band data for display
        non_zero_mask = band_image != 0
        if np.any(non_zero_mask):
            min_val = np.min(band_image[non_zero_mask])
            max_val = np.max(band_image[non_zero_mask])
            if max_val > min_val:
                normalized = np.zeros_like(band_image)
                normalized[non_zero_mask] = ((band_image[non_zero_mask] - min_val) / (max_val - min_val) * 255)
                band_image = normalized.astype(np.uint8)
            else:
                band_image = np.zeros_like(band_image, dtype=np.uint8)
        else:
            band_image = np.zeros_like(band_image, dtype=np.uint8)

        # Convert to QImage and display
        height, width = band_image.shape
        band_image_bytes = band_image.tobytes()
        image = QtGui.QImage(band_image_bytes, width, height, width, QtGui.QImage.Format_Grayscale8)
        pixmap = QtGui.QPixmap.fromImage(image)
            
        self.scene.clear()
        self.scene.addItem(QGraphicsPixmapItem(pixmap))
        self.graphicsView.fitInView(self.scene.itemsBoundingRect(), QtCore.Qt.KeepAspectRatio)
        self.log_message("Segmented image displayed successfully", "success")

    def show_mask(self):
        """Show the mask of the segmented image with colors matching the bounding boxes"""
        if self.current_mask is None:
            self.log_message("No mask available to display", "error")
            return

        try:
            # Get the dimensions from the mask
            height, width = self.current_mask.shape[:2]
            
            # Create a black background (3-channel RGB image)
            rgb_image = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Create a colored overlay
            overlay = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Apply colors from bounding boxes to the mask
            for box_data in self.bounding_boxes:
                # Get the color from the bounding box
                color = box_data['color']
                rgb_color = np.array([color.red(), color.green(), color.blue()], dtype=np.uint8)
                
                # Get the box coordinates
                x1 = int(box_data['x'])
                y1 = int(box_data['y'])
                x2 = int(x1 + box_data['width'])
                y2 = int(y1 + box_data['height'])
                
                # Ensure coordinates are within bounds
                x1 = max(0, min(x1, width - 1))
                y1 = max(0, min(y1, height - 1))
                x2 = max(0, min(x2, width - 1))
                y2 = max(0, min(y2, height - 1))
                
                # Get the region mask
                region_mask = self.current_mask[y1:y2, x1:x2]
                
                # Apply the color to the region
                for c in range(3):
                    overlay[y1:y2, x1:x2, c][region_mask] = rgb_color[c]
            
            # Blend the overlay with the black background
            alpha = 1.0  # Full opacity for colored regions
            result = cv2.addWeighted(rgb_image, 1.0, overlay, alpha, 0)
            
            # Convert numpy array to bytes, ensuring it's contiguous in memory
            result = np.ascontiguousarray(result)
            bytes_per_line = 3 * width
            
            # Create QImage using the array's buffer
            q_image = QtGui.QImage(result.tobytes(), 
                                  width, 
                                  height, 
                                  bytes_per_line,
                                  QtGui.QImage.Format_RGB888)
            
            pixmap = QtGui.QPixmap.fromImage(q_image)
            
            self.scene.clear()
            self.scene.addItem(QGraphicsPixmapItem(pixmap))
            self.graphicsView.fitInView(self.scene.itemsBoundingRect(), QtCore.Qt.KeepAspectRatio)
            self.log_message("Colored mask displayed successfully", "success")
            
        except Exception as e:
            self.log_message(f"Error displaying mask: {str(e)}", "error")
            import traceback
            print(traceback.format_exc())

    def show_info_dialog(self):
        """Show the product information dialog."""
        info_dialog = InfoDialog(self)
        info_dialog.exec_()
         
    def on_resize_event(self, event):
        """Keep elements positioned correctly when the window is resized."""
        # Update function info button position with new size
        self.function_info_button.setGeometry(QtCore.QRect(self.width() - 150, 2, 100, 25))
        
        # Update info button position (moves with window width)
        self.info_button.setGeometry(QtCore.QRect(self.width() - 50, 2, 40, 40))
        
        # Update status bar position with new height
        if hasattr(self, 'statusBar'):
            self.statusBar.setGeometry(-1, self.height() - 45, self.width() + 2, 45)
        
        # Call the original resize event
        super().resizeEvent(event)

    def show_function_info_dialog(self):
        """Show the function information dialog."""
        function_info_dialog = FunctionInfoDialog(self)
        function_info_dialog.exec_()

    def on_slider_value_changed(self, value):
        """Handle slider value changes"""
        # Update doubleSpinBox without triggering its valueChanged signal
        self.doubleSpinBox.blockSignals(True)
        self.doubleSpinBox.setValue(int(value))  # Convert to integer
        self.doubleSpinBox.blockSignals(False)
        self.update_hdr_band()

    def on_spinbox_value_changed(self, value):
        """Handle spinbox value changes"""
        # Update slider without triggering its valueChanged signal
        self.horizontalSlider.blockSignals(True)
        self.horizontalSlider.setValue(int(value))  # Convert to integer
        self.horizontalSlider.blockSignals(False)
        self.update_hdr_band()

    def log_message(self, message, message_type="Function info"):
        """Add a formatted message to listWidget_2"""
        timestamp = QtCore.QDateTime.currentDateTime().toString("hh:mm:ss")
        
        # Format based on message type
        if message_type == "error":
            formatted_message = f"[{timestamp}] ❌ ERROR: {message}"
            color = "#ff6b6b"
        elif message_type == "success":
            formatted_message = f"[{timestamp}] ✓ SUCCESS: {message}"
            color = "#69db7c"
        else:  # info
            formatted_message = f"[{timestamp}] ℹ {message}"
            color = "#ffffff"
        
        # Create item and set its color
        item = QListWidgetItem(formatted_message)
        item.setForeground(QtGui.QColor(color))
        
        # Add item to list and scroll to it
        self.listWidget_2.addItem(item)
        self.listWidget_2.scrollToBottom()

    def update_rgb_color(self):
        """Update the RGB color of the RGB DISPLAY button"""
        self.hue = (self.hue + 5) % 360
        color = QtGui.QColor.fromHsv(self.hue, 255, 255)
        self.pushButton.setStyleSheet(f"""
            QPushButton {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 {color.name()}, 
                    stop:1 {QtGui.QColor.fromHsv((self.hue + 60) % 360, 255, 255).name()});
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 {QtGui.QColor.fromHsv(self.hue, 255, 230).name()}, 
                    stop:1 {QtGui.QColor.fromHsv((self.hue + 60) % 360, 255, 230).name()});
            }}
            QPushButton:pressed {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 {QtGui.QColor.fromHsv(self.hue, 255, 200).name()}, 
                    stop:1 {QtGui.QColor.fromHsv((self.hue + 60) % 360, 255, 200).name()});
            }}
        """)

    def export_all_data(self):
        """Exports all data including plots, images, and metadata to a folder."""
        if self.hdr_path is None:
            self.log_message("Error: No data available to export.", "error")
            return
            
        try:
            # Create export directory
            base_dir = os.path.dirname(self.hdr_path)
            timestamp = QtCore.QDateTime.currentDateTime().toString("yyyyMMdd_hhmmss")
            export_dir = os.path.join(base_dir, f"export_{timestamp}")
            os.makedirs(export_dir, exist_ok=True)

            # Create subdirectories
            plots_dir = os.path.join(export_dir, "plots")
            images_dir = os.path.join(export_dir, "images")
            bands_dir = os.path.join(export_dir, "bands")
            os.makedirs(plots_dir, exist_ok=True)
            os.makedirs(images_dir, exist_ok=True)
            os.makedirs(bands_dir, exist_ok=True)

            # 1. Export spectral signatures of segmented objects
            if self.bounding_boxes and self.hdr_data is not None:
                # Prepare data arrays and headers
                all_signatures = []
                header = ["Band"]
                
                # Collect spectral signatures for each segmented object
                for box_data in self.bounding_boxes:
                    # Get box coordinates
                    x1 = int(box_data['x'])
                    y1 = int(box_data['y'])
                    x2 = int(x1 + box_data['width'])
                    y2 = int(y1 + box_data['height'])

                    # Get region data and calculate average spectral signature
                    region_data = self.hdr_data[y1:y2, x1:x2, :]
                    if region_data.size > 0:
                        avg_spectral_signature = np.mean(region_data, axis=(0, 1))
                        all_signatures.append(avg_spectral_signature)
                        header.append(f"{box_data['label']}")

                if all_signatures:
                    # Create band numbers array
                    bands = np.arange(self.hdr_data.shape[2])
                    
                    # Combine band numbers with all signatures
                    csv_data = np.column_stack([bands] + all_signatures)
                    
                    # Save to CSV file
                    np.savetxt(os.path.join(plots_dir, "segmented_objects_spectral_signatures.csv"),
                            csv_data,
                            delimiter=",",
                            header=",".join(header),
                            comments='',
                            fmt='%.6f')  # Use 6 decimal places for precision
                    
            # # Save the current plot as PNG
            # if hasattr(self, 'figure') and self.figure is not None:
            #     # Save with high resolution
            #     self.figure.savefig(os.path.join(plots_dir, "spectral_signatures_plot.png"), 
            #                     dpi=300, 
            #                     bbox_inches='tight',
            #                     format='png')
            

            # # 1. Export spectral signatures
            # if self.current_spectral_data is not None:
            #     # Export segmented region spectral signature
            #     seg_data = np.column_stack((np.arange(len(self.current_spectral_data)), 
            #                               self.current_spectral_data))
            #     np.savetxt(os.path.join(plots_dir, "segmented_spectral_signature.csv"),
            #               seg_data, delimiter=",", header="Band,Reflectance", comments='')

            # Export full image spectral signature
            if self.hdr_data is not None:
                full_signature = self.hdr_data.mean(axis=(0, 1))
                full_data = np.column_stack((np.arange(len(full_signature)), full_signature))
                np.savetxt(os.path.join(plots_dir, "full_spectral_signature.csv"),
                          full_data, delimiter=",", header="Band,Reflectance", comments='')
            

            # 2. Export bounding box coordinates
            if self.bounding_boxes:
                with open(os.path.join(export_dir, "bounding_boxes.txt"), 'w') as f:
                    for box_data in self.bounding_boxes:
                        f.write(f"{box_data['label']}: x={box_data['x']:.1f}, y={box_data['y']:.1f}, "
                                f"width={box_data['width']:.1f}, height={box_data['height']:.1f}\n")

            # 3. Export RGB image
            if self.image_path and os.path.exists(self.image_path):
                rgb_dest = os.path.join(images_dir, "rgb_image.png")
                import shutil
                shutil.copy2(self.image_path, rgb_dest)

            # 4. Export current segmented image
            if hasattr(self, 'segmented_hdr_data') and self.segmented_hdr_data is not None:
                current_band = self.segmented_hdr_data[:, :, self.current_band]
                current_band = np.rot90(current_band, k=-1)
                cv2.imwrite(os.path.join(images_dir, "segmented_image.png"),
                           self.normalize_for_export(current_band))

            # 5. Export segmentation mask
            if self.current_mask is not None:
                mask_image = np.zeros((self.current_mask.shape[0], 
                                     self.current_mask.shape[1]), dtype=np.uint8)
                mask_image[self.current_mask] = 255
                cv2.imwrite(os.path.join(images_dir, "segmentation_mask.png"), mask_image)

            # 6. Export all segmented bands
            if hasattr(self, 'segmented_hdr_data') and self.segmented_hdr_data is not None:
                for band in range(self.segmented_hdr_data.shape[2]):
                    band_image = self.segmented_hdr_data[:, :, band]
                    band_image = np.rot90(band_image, k=-1)
                    cv2.imwrite(os.path.join(bands_dir, f"segmented_band_{band:03d}.png"),
                              self.normalize_for_export(band_image))

            # 7. Export metadata
            self.export_metadata(export_dir)

            self.log_message(f"All data exported successfully to {export_dir}", "success")
            
        except Exception as e:
            self.log_message(f"Error exporting data: {str(e)}", "error")
            import traceback
            print(traceback.format_exc())

    def normalize_for_export(self, image):
        """Normalize image data for export."""
        non_zero_mask = image != 0
        if np.any(non_zero_mask):
            min_val = np.min(image[non_zero_mask])
            max_val = np.max(image[non_zero_mask])
            if max_val > min_val:
                normalized = np.zeros_like(image)
                normalized[non_zero_mask] = ((image[non_zero_mask] - min_val) / 
                                           (max_val - min_val) * 255)
                return normalized.astype(np.uint8)
        return np.zeros_like(image, dtype=np.uint8)

    def export_metadata(self, export_dir):
        """Export metadata about the analysis."""
        metadata = {
            "Export Date": QtCore.QDateTime.currentDateTime().toString(),
            "HDR File": self.hdr_path if self.hdr_path else "None",
            "Image Dimensions": str(self.hdr_data.shape) if self.hdr_data is not None else "None",
            "Number of Bands": str(self.hdr_data.shape[2]) if self.hdr_data is not None else "None",
            "Selected Band": str(self.current_band),
        }
        
        with open(os.path.join(export_dir, "metadata.txt"), 'w') as f:
            for key, value in metadata.items():
                f.write(f"{key}: {value}\n")

    def show_range_dialog(self):
        """Show dialog to set x and y axis ranges."""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Set Axis Ranges")
        dialog.setFixedWidth(300)
        
        layout = QtWidgets.QVBoxLayout()
        
        # X-axis range inputs
        x_group = QtWidgets.QGroupBox("X-axis Range")
        x_layout = QtWidgets.QHBoxLayout()
        self.x_min_input = QtWidgets.QLineEdit()
        self.x_max_input = QtWidgets.QLineEdit()
        x_layout.addWidget(QtWidgets.QLabel("Min:"))
        x_layout.addWidget(self.x_min_input)
        x_layout.addWidget(QtWidgets.QLabel("Max:"))
        x_layout.addWidget(self.x_max_input)
        x_group.setLayout(x_layout)
        
        # Y-axis range inputs
        y_group = QtWidgets.QGroupBox("Y-axis Range")
        y_layout = QtWidgets.QHBoxLayout()
        self.y_min_input = QtWidgets.QLineEdit()
        self.y_max_input = QtWidgets.QLineEdit()
        y_layout.addWidget(QtWidgets.QLabel("Min:"))
        y_layout.addWidget(self.y_min_input)
        y_layout.addWidget(QtWidgets.QLabel("Max:"))
        y_layout.addWidget(self.y_max_input)
        y_group.setLayout(y_layout)
        
        # Add groups to main layout
        layout.addWidget(x_group)
        layout.addWidget(y_group)
        
        # Add Apply button
        apply_button = QtWidgets.QPushButton("Apply")
        apply_button.clicked.connect(lambda: self.apply_axis_ranges(dialog))
        layout.addWidget(apply_button)
        
        dialog.setLayout(layout)
        
        # Position dialog near the range button
        button_pos = self.rangeButton.mapToGlobal(QtCore.QPoint(0, 0))
        dialog.move(button_pos.x() - dialog.width() + self.rangeButton.width(),
                   button_pos.y() - dialog.height() - 10)
        
        # Store references to input fields
        self.range_dialog = dialog
        self.range_dialog.finished.connect(self.cleanup_range_dialog)
        
        dialog.exec_()

    def cleanup_range_dialog(self):
        """Clean up range dialog references when closed."""
        if hasattr(self, 'range_dialog'):
            self.x_min_input = None
            self.x_max_input = None
            self.y_min_input = None
            self.y_max_input = None
            self.range_dialog = None

    def update_axis_inputs(self):
        """Update axis range input boxes with current plot limits"""
        if hasattr(self, 'figure') and self.figure is not None:
            ax = self.figure.axes[0]
            x_min, x_max = ax.get_xlim()
            y_min, y_max = ax.get_ylim()
            
            # Only update if the input fields exist and are valid
            if (hasattr(self, 'x_min_input') and self.x_min_input is not None and
                hasattr(self, 'x_max_input') and self.x_max_input is not None and
                hasattr(self, 'y_min_input') and self.y_min_input is not None and
                hasattr(self, 'y_max_input') and self.y_max_input is not None):
                try:
                    self.x_min_input.setText(f"{x_min:.2f}")
                    self.x_max_input.setText(f"{x_max:.2f}")
                    self.y_min_input.setText(f"{y_min:.2f}")
                    self.y_max_input.setText(f"{y_max:.2f}")
                except RuntimeError:
                    # If the widgets have been deleted, clean up the references
                    self.cleanup_range_dialog()

    def apply_axis_ranges(self, dialog):
        """Apply the new axis ranges to the plot."""
        try:
            # Get current plot limits
            if hasattr(self, 'figure') and self.figure is not None:
                ax = self.figure.axes[0]
                current_x_min, current_x_max = ax.get_xlim()
                current_y_min, current_y_max = ax.get_ylim()
                
                # Get new values from inputs
                new_x_min = float(self.x_min_input.text()) if self.x_min_input.text() else current_x_min
                new_x_max = float(self.x_max_input.text()) if self.x_max_input.text() else current_x_max
                new_y_min = float(self.y_min_input.text()) if self.y_min_input.text() else current_y_min
                new_y_max = float(self.y_max_input.text()) if self.y_max_input.text() else current_y_max
                
                # Validate ranges
                if new_x_min >= new_x_max or new_y_min >= new_y_max:
                    QtWidgets.QMessageBox.warning(self, "Invalid Range", 
                                               "Minimum value must be less than maximum value.")
                    return
                
                # Apply new ranges
                ax.set_xlim(new_x_min, new_x_max)
                ax.set_ylim(new_y_min, new_y_max)
                
                # Update the plot
                if hasattr(self, 'canvas') and self.canvas is not None:
                    self.canvas.draw()
                
                dialog.accept()
                self.log_message("Axis ranges updated successfully", "success")
            else:
                QtWidgets.QMessageBox.warning(self, "No Plot", 
                                           "No plot is currently displayed.")
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Invalid Input", 
                                       "Please enter valid numbers for the ranges.")

    def reset_plot(self):
        """Reset the plot to its original state."""
        if hasattr(self, 'figure') and self.figure is not None:
            ax = self.figure.axes[0]
            # Reset to original limits
            ax.set_xlim(self.original_x_min, self.original_x_max)
            ax.set_ylim(self.original_y_min, self.original_y_max)
            
            # Update the plot
            if hasattr(self, 'canvas') and self.canvas is not None:
                self.canvas.draw()
            
            self.log_message("Plot reset to original state", "success")
        else:
            self.log_message("No plot available to reset", "error")

    def on_close(self, event):
        """Handle cleanup when the application is closed"""
        try:
            # Clear any temporary files
            if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir)
            
            # Clear any cached data
            if hasattr(self, '_band_cache'):
                self._band_cache.clear()
            if hasattr(self, '_spectral_cache'):
                self._spectral_cache.clear()
            
            # Clear any loaded data
            self.hdr_data = None
            self.image_path = None
            self.hdr_path = None
            self.current_mask = None
            self.segmented_hdr_data = None
            self.bounding_boxes = []
            
            # Clear SAM model
            if hasattr(self, 'sam_predictor'):
                self.sam_predictor = None
            
            # Accept the close event
            event.accept()
        except Exception as e:
            self.log_message(f"Error during cleanup: {str(e)}", "error")
            event.accept()  # Still close even if cleanup fails

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    
    # Set application icon
    icon_path = os.path.join(os.path.dirname(__file__), "app_icon.png")
    if os.path.exists(icon_path):
        app_icon = QtGui.QIcon(icon_path)
        app.setWindowIcon(app_icon)
    
    window = UI_Checker()
    window.show()
    sys.exit(app.exec_())
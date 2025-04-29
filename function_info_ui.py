import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

class FunctionInfoDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(FunctionInfoDialog, self).__init__(parent)
        self.setWindowTitle("Function Information")
        self.setFixedSize(800, 700)

        # Remove the question mark from the title bar
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)    
        
        # Set dialog style
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
            }
        """)
        
        # Create the main layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Create a horizontal layout for the icon and title
        title_layout = QtWidgets.QHBoxLayout()
        
        # Load the icon
        icon_label = QtWidgets.QLabel()
        icon_pixmap = QtGui.QPixmap("app_icon.png").scaled(60, 50, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        icon_label.setPixmap(icon_pixmap)
        
        # Add the icon and title to the horizontal layout
        title_layout.addWidget(icon_label)
        
        # Title label with modern styling
        title_label = QtWidgets.QLabel("Hyperspectral Image Analysis Tool")
        title_font = QtGui.QFont()
        title_font.setBold(True)
        title_font.setPointSize(20)
        title_font.setFamily("Segoe UI")
        title_label.setFont(title_font)
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                padding: 10px;
                margin-bottom: 10px;
            }
        """)
        
        # Add the title to the title layout
        title_layout.addWidget(title_label)
        
        # Center the title layout
        title_layout.setAlignment(QtCore.Qt.AlignCenter)
        
        # Add the title layout to the main layout
        main_layout.addLayout(title_layout)
        
        # Create styled scroll area
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #ffffff;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                min-height: 30px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # Content widget with modern styling
        content_widget = QtWidgets.QWidget()
        content_layout = QtWidgets.QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        
        # App Description Section with enhanced styling
        desc_label = QtWidgets.QLabel("About This Application")
        desc_font = QtGui.QFont("Segoe UI", 14, QtGui.QFont.Bold)
        desc_label.setFont(desc_font)
        desc_label.setStyleSheet("color: #60a5fa; margin-top: 15px;")
        
        desc_text = QtWidgets.QTextEdit()
        desc_text.setReadOnly(True)
        desc_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                padding: 10px;
                color: #495057;
                font-family: 'Segoe UI';
                font-size: 13px;
                line-height: 1.6;
            }
        """)
        
        # Enhanced HTML styling for description
        description_html = """
        <style>
            p { line-height: 1.6; color: #495057; }
            h3 { color: #2c3e50; margin-top: 20px; margin-bottom: 10px; }
            li { margin-bottom: 8px; color: #495057; }
            ul, ol { margin-left: 20px; }
        </style>
        
        <p style='font-size: 14px;'>This application is designed for analyzing hyperspectral images using advanced segmentation techniques. It combines traditional image processing with machine learning to provide detailed spectral analysis of selected regions.</p>
        
        <h3>How It Works:</h3>
        <ol>
            <li><b>Data Loading:</b> Upload a folder containing hyperspectral images and their corresponding RGB previews.</li>
            <li><b>Region Selection:</b> Use the SELECT ROI tool to draw bounding boxes around areas of interest.</li>
            <li><b>Segmentation:</b> The application uses the SAM (Segment Anything Model) to perform precise segmentation of selected regions.</li>
            <li><b>Analysis:</b> View spectral signatures, compare different regions, and export results for further analysis.</li>
        </ol>
        
        <h3>Key Features:</h3>
        <ul>
            <li>Interactive region selection with visual feedback</li>
            <li>Advanced segmentation using SAM model</li>
            <li>Spectral signature analysis and visualization</li>
            <li>Data export capabilities</li>
            <li>Real-time preview and comparison tools</li>
        </ul>
        """
        desc_text.setHtml(description_html)
        
        # Button Functions Section with enhanced styling
        button_label = QtWidgets.QLabel("Button Functions")
        button_label.setFont(desc_font)
        button_label.setStyleSheet("color: #60a5fa; margin-top: 15px;")
        
        # Enhanced styling for button info
        info_text = QtWidgets.QTextEdit()
        info_text.setReadOnly(True)
        info_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                padding: 10px;
                color: #495057;
                font-family: 'Segoe UI';
                font-size: 13px;
                line-height: 1.6;
            }
        """)
        
        # Enhanced HTML styling for function information
        function_html = """
        <style>
            table { 
                width: 100%; 
                border-collapse: collapse; 
                margin-bottom: 10px;
            }
            td { 
                padding: 12px; 
                border-bottom: 1px solid #e9ecef;
                line-height: 1.5;
            }
            td:first-child { 
                font-weight: bold; 
                width: 150px;
                color: #2c3e50;
            }
            .section { 
                margin-top: 25px; 
                background-color: #ffffff;
                border-radius: 8px;
                padding: 10px;
            }
            .section-title { 
                font-weight: bold; 
                color: #2c3e50; 
                font-size: 16px;
                margin: 15px 0;
                padding-bottom: 8px;
                border-bottom: 2px solid #3498db;
            }
        </style>
        
        <div class="section">
            <div class="section-title">File Operations</div>
            <table>
                <tr>
                    <td><b>UPLOAD FOLDER:</b></td>
                    <td>Opens a dialog to select a folder containing hyperspectral images and RGB previews.</td>
                </tr>
                <tr>
                    <td><b>EXPORT DATA:</b></td>
                    <td>Exports all analysis results, including spectral signatures, masks, and metadata to a timestamped folder.</td>
                </tr>
                <tr>
                    <td><b>BACK:</b></td>
                    <td>Navigates back to the parent folder in the file browser.</td>
                </tr>
            </table>
        </div>

        <div class="section">
            <div class="section-title">Display Controls</div>
            <table>
                <tr>
                    <td><b>RGB DISPLAY:</b></td>
                    <td>Displays the RGB preview image from the selected folder. Hold to view, release to return to hyperspectral view.</td>
                </tr>
                <tr>
                    <td><b>MASK DISPLAY:</b></td>
                    <td>Toggles between displaying the segmented image and its colored mask overlay.</td>
                </tr>
            </table>
        </div>

        <div class="section">
            <div class="section-title">Analysis Tools</div>
            <table>
                <tr>
                    <td><b>SELECT ROI:</b></td>
                    <td>Enables drawing mode to select regions of interest. Click again to disable drawing mode.</td>
                </tr>
                <tr>
                    <td><b>SEGMENTATION:</b></td>
                    <td>Performs segmentation on selected regions using the SAM model. Shows a loading overlay during processing.</td>
                </tr>
                <tr>
                    <td><b>ENTIRE SPECTRUM:</b></td>
                    <td>Plots the spectral response of the entire image across all bands.</td>
                </tr>
                <tr>
                    <td><b>SEGMENTED SPECTRUM:</b></td>
                    <td>Displays and compares the spectral response of all segmented regions.</td>
                </tr>
            </table>
        </div>

        <div class="section">
            <div class="section-title">Utility Functions</div>
            <table>
                <tr>
                    <td><b>CLEAR ALL:</b></td>
                    <td>Clears all displayed data, including images, plots, masks, and segmentation data. Resets the UI to initial state.</td>
                </tr>
                <tr>
                    <td><b>SET RANGE:</b></td>
                    <td>Opens a dialog to set custom axis ranges for spectral plots.</td>
                </tr>
                <tr>
                    <td><b>RESET:</b></td>
                    <td>Resets the current plot to its original axis ranges.</td>
                </tr>
            </table>
        </div>
        """
        info_text.setHtml(function_html)
        
        # Add all sections to content layout
        content_layout.addWidget(desc_label)
        content_layout.addWidget(desc_text)
        content_layout.addWidget(button_label)
        content_layout.addWidget(info_text)
        
        # Set the content widget to the scroll area
        scroll.setWidget(content_widget)
        
        # Add the scroll area to the main layout
        main_layout.addWidget(scroll)
        
        # Modern styled close button
        close_button = QtWidgets.QPushButton("Close")
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 14px;
                min-width: 120px;
                font-family: 'Segoe UI';
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #2573a7;
            }
        """)
        close_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        close_button.clicked.connect(self.accept)
        
        # Add the close button to the main layout
        main_layout.addWidget(close_button, 0, QtCore.Qt.AlignCenter)
        
        # Set the main layout
        self.setLayout(main_layout)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    dialog = FunctionInfoDialog()
    dialog.show()
    sys.exit(app.exec_())
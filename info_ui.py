import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

class InfoDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(InfoDialog, self).__init__(parent)
        self.setWindowTitle("Product Information")
        self.setFixedSize(800, 700)  # Increased size to match function_info_ui.py

        # Remove the question mark from the title bar
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # Set dialog style with enhanced appearance
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
            }
        """)
        
        # Create main layout with proper margins
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Create a horizontal layout for icon and title
        title_layout = QtWidgets.QHBoxLayout()
        
        # Load the icon
        icon_label = QtWidgets.QLabel()
        icon_pixmap = QtGui.QPixmap("app_icon.png").scaled(60, 50, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        icon_label.setPixmap(icon_pixmap)
        title_layout.addWidget(icon_label)
        
        # Enhanced title label
        title_label = QtWidgets.QLabel("Hyperspectral Image Analysis Tool")
        title_font = QtGui.QFont("Segoe UI", 20, QtGui.QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                padding: 10px;
                margin-bottom: 10px;
            }
        """)
        title_layout.addWidget(title_label)
        title_layout.setAlignment(QtCore.Qt.AlignCenter)
        
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
        
        # Content widget
        content_widget = QtWidgets.QWidget()
        content_layout = QtWidgets.QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        
        # Info text with enhanced styling
        info_text = QtWidgets.QTextEdit()
        info_text.setReadOnly(True)
        info_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                padding: 15px;
                color: #495057;
                font-family: 'Segoe UI';
                font-size: 13px;
                line-height: 1.6;
            }
        """)
        
        # Enhanced HTML content with modern styling
        info_html = """
        <style>
            body {
                font-family: 'Segoe UI', sans-serif;
                line-height: 1.6;
                color: #495057;
            }
            table { 
                width: 100%; 
                border-collapse: collapse; 
                margin-bottom: 20px;
                background-color: #ffffff;
                border-radius: 8px;
                overflow: hidden;
            }
            tr:hover {
                background-color: #f8f9fa;
            }
            td:first-child { 
                font-weight: bold; 
                width: 150px; 
                color: #2c3e50;
                background-color: #f8f9fa;
            }
            td { 
                padding: 12px; 
                border-bottom: 1px solid #e9ecef;
            }
            .version-history {
                margin-top: 25px;
                border: 2px solid #e9ecef;
                padding: 15px;
                background-color: #ffffff;
                border-radius: 8px;
            }
            .version-title {
                font-weight: bold;
                color: #2c3e50;
                font-size: 16px;
                margin-bottom: 15px;
                padding-bottom: 8px;
                border-bottom: 2px solid #3498db;
            }
            .version-entry {
                margin-bottom: 15px;
                padding: 15px;
                background-color: #f8f9fa;
                border-radius: 6px;
            }
            .version-number {
                color: #3498db;
                font-weight: bold;
                font-size: 14px;
            }
            .version-date {
                color: #7f8c8d;
                font-size: 0.9em;
                margin-left: 10px;
            }
            ul {
                margin: 10px 0 0 20px;
                padding: 0;
            }
            li {
                margin-bottom: 8px;
                color: #495057;
            }
            li:last-child {
                margin-bottom: 0;
            }
        </style>
        
        <table>
            <tr>
                <td>Product Name</td>
                <td>Hyperspectral Image Analysis Tool</td>
            </tr>
            <tr>
                <td>Current Version</td>
                <td><span style="color: #3498db; font-weight: bold;">3.2.0</span></td>
            </tr>
            <tr>
                <td>Type</td>
                <td>Desktop Application</td>
            </tr>
            <tr>
                <td>Description</td>
                <td>Advanced tool for analyzing and processing hyperspectral images with segmentation capabilities and spectral signature analysis.</td>
            </tr>
            <tr>
                <td>Copyright</td>
                <td>Copyright © 2025 PIL, IITK</td>
            </tr>
            <tr>
                <td>Developed by</td>
                <td>Harshit Kumar & Sejal Sahu<br><span style="color: #7f8c8d;">PIL Intern'25, IIT Kanpur</span></td>
            </tr>
            <tr>
                <td>Guided by</td>
                <td>Prof. Tushar Balasaheb Sandhan<br><span style="color: #7f8c8d;">IIT Kanpur</span></td>
            </tr>
            <tr>
                <td>Last Modified</td>
                <td>April 9, 2025</td>
            </tr>
        </table>

        <div class="version-history">
            <div class="version-title">Version History</div>

            <div class="version-entry">
                <span class="version-number">Version 3.2.0</span>
                <span class="version-date">April 9, 2025</span>
                <ul>
                    <li>Added support for multiple segmentation with multiple bounding boxes</li>
                    <li>Implemented graph axis range customization feature</li>
                    <li>Added comprehensive data export functionality to save all analysis results</li>
                    <li>Enhanced user control over visualization parameters</li>
                    <li>Added batch processing capability for multiple images</li>
                    <li>Added support for custom color mapping and visualization presets</li>
                    <li>Enhanced performance with multi-threading support</li>
                </ul>
            </div>

            <div class="version-entry">
                <span class="version-number">Version 3.1.0</span>
                <span class="version-date">March 28, 2025</span>
                <ul>
                    <li>Added comprehensive product information and function details</li>
                    <li>Implemented logging system for command outputs</li>
                    <li>Enhanced UI with real-time feedback and modern styling</li>
                </ul>
            </div>
            
            <div class="version-entry">
                <span class="version-number">Version 3.0.0</span>
                <span class="version-date">March 22, 2025</span>
                <ul>
                    <li>Improved segmentation accuracy using SAM model</li>
                    <li>Added spectral signature plots for full image & segmented regions</li>
                    <li>Implemented data export functionality with detailed analytics</li>
                </ul>
            </div>

            <div class="version-entry">
                <span class="version-number">Version 2.0.0</span>
                <span class="version-date">March 14, 2025</span>
                <ul>
                    <li>Added support for multiple hyperspectral file formats</li>
                    <li>Introduced advanced band selection functionality</li>
                    <li>Enabled spectral signature analysis for segmented regions</li>
                </ul>
            </div>

            <div class="version-entry">
                <span class="version-number">Version 1.0.0</span>
                <span class="version-date">March 5, 2025</span>
                <ul>
                    <li>Initial release with core functionality</li>
                    <li>Basic hyperspectral image viewing capabilities</li>
                    <li>Implemented bounding box drawing tool</li>
                    <li>Integrated Segment Anything Model (SAM)</li>
                    <li>Added segmented mask display feature</li>
                </ul>
            </div>
        </div>
        """
        
        info_text.setHtml(info_html)
        
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
        
        # Add widgets to layouts
        main_layout.addLayout(title_layout)
        content_layout.addWidget(info_text)
        
        # Set the content widget to the scroll area
        scroll.setWidget(content_widget)
        
        # Add scroll area and close button to main layout
        main_layout.addWidget(scroll)
        main_layout.addWidget(close_button, 0, QtCore.Qt.AlignCenter)
        
        self.setLayout(main_layout)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    dialog = InfoDialog()
    dialog.show()
    sys.exit(app.exec_())

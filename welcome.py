from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QLabel, QApplication, QHBoxLayout
from PyQt5.QtCore import Qt
import os

class WelcomeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome")
        self.setFixedSize(800, 600)  # Increased size for better readability
        
        # Remove help button from title bar
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # Set dialog style with enhanced appearance
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
            }
        """)
        
        # Create main layout with proper margins
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Create a horizontal layout for icon and title
        title_layout = QHBoxLayout()
        
        # Load the icon
        icon_label = QLabel()
        icon_path = os.path.join(os.path.dirname(__file__), "app_icon.png")
        if os.path.exists(icon_path):
            icon_pixmap = QtGui.QPixmap(icon_path).scaled(60, 50, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            icon_label.setPixmap(icon_pixmap)
            # Set application icon
            app_icon = QtGui.QIcon(icon_path)
            self.setWindowIcon(app_icon)
            if hasattr(QApplication.instance(), 'setWindowIcon'):
                QApplication.instance().setWindowIcon(app_icon)
        
        title_layout.addWidget(icon_label)
        
        # Enhanced title
        title = QLabel("Welcome to Hyperspectral Image Analysis")
        title_font = QtGui.QFont('Segoe UI', 20, QtGui.QFont.Bold)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                padding: 10px;
                margin-bottom: 10px;
            }
        """)
        title_layout.addWidget(title)
        title_layout.setAlignment(Qt.AlignCenter)
        
        layout.addLayout(title_layout)
        
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
        
        # Enhanced text editor
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet("""
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
        
        # Enhanced welcome text with modern styling
        welcome_text = """
        <style>
            body {
                font-family: 'Segoe UI', sans-serif;
                line-height: 1.6;
                color: #495057;
            }
            h2 {
                color: #2c3e50;
                text-align: center;
                margin-bottom: 25px;
                font-size: 24px;
            }
            .feature-box {
                background-color: #ffffff;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
            }
            .feature-title {
                color: #3498db;
                font-size: 18px;
                font-weight: bold;
                margin: 0 0 15px 0;
                padding-bottom: 10px;
                border-bottom: 2px solid #3498db;
            }
            ul {
                margin: 0;
                padding-left: 20px;
            }
            li {
                margin-bottom: 12px;
                color: #495057;
            }
            .info-icon {
                color: #3498db;
                font-weight: bold;
            }
            .success-text {
                color: #27ae60;
                font-weight: bold;
            }
            .error-text {
                color: #e74c3c;
                font-weight: bold;
            }
            .warning-text {
                color: #f39c12;
                font-weight: bold;
            }
            .info-text {
                color: #3498db;
                font-weight: bold;
            }
            .start-text {
                text-align: center;
                margin-top: 25px;
                padding: 15px;
                background-color: #f8f9fa;
                border-radius: 8px;
                font-weight: bold;
                color: #2c3e50;
            }
        </style>
        
        <h2>Getting Started Guide</h2>
        
        <div class="feature-box">
            <div class="feature-title">📌 Help Features</div>
            <ul>
                <li>
                    <b>Info Button <span class="info-icon">( ℹ )</span></b>
                    <ul>
                        <li>Quick access to application information</li>
                        <li>Version details and documentation</li>
                        <li>Developer contact information</li>
                    </ul>
                </li>
                <li>
                    <b>Function Info Button</b>
                    <ul>
                        <li>Comprehensive guide to all features</li>
                        <li>Detailed button descriptions</li>
                        <li>Step-by-step usage instructions</li>
                    </ul>
                </li>
            </ul>
        </div>

        <div class="feature-box">
            <div class="feature-title">📋 Log Messages Guide</div>
            <ul>
                <li>
                    <span class="info-text">ℹ️ Information Messages</span>
                    <ul>
                        <li>Show current operation status</li>
                        <li>Display processing steps</li>
                        <li>Indicate data loading progress</li>
                    </ul>
                </li>
                <li>
                    <span class="success-text">✓ Success Messages</span>
                    <ul>
                        <li>Confirm operation completion</li>
                        <li>Indicate successful file processing</li>
                        <li>Show when analysis is complete</li>
                    </ul>
                </li>
                <li>
                    <span class="warning-text">⚠️ Warning Messages</span>
                    <ul>
                        <li>Alert about potential issues</li>
                        <li>Suggest recommended actions</li>
                        <li>Highlight important considerations</li>
                    </ul>
                </li>
                <li>
                    <span class="error-text">❌ Error Messages</span>
                    <ul>
                        <li>Indicate operation failures</li>
                        <li>Show file loading errors</li>
                        <li>Display processing problems</li>
                    </ul>
                </li>
            </ul>
        </div>

        <div class="feature-box">
            <div class="feature-title">⚠️ Important Tips</div>
            <ul>
                <li>
                    <b>Always Monitor Logs:</b>
                    <ul>
                        <li>Keep an eye on the log window during operations</li>
                        <li>Check for any warnings or errors</li>
                        <li>Follow suggested troubleshooting steps if shown</li>
                    </ul>
                </li>
                <li>
                    <b>Processing Status:</b>
                    <ul>
                        <li>Log messages show real-time processing status</li>
                        <li>Wait for success message before proceeding</li>
                        <li>Don't close application during active processing</li>
                    </ul>
                </li>
            </ul>
        </div>

        <div class="start-text">
            Click "Start Application" to begin your analysis journey
        </div>
        """
        
        text_edit.setHtml(welcome_text)
        content_layout.addWidget(text_edit)
        
        # Set the content widget to the scroll area
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
        # Enhanced start button
        ok_button = QPushButton("Start Application")
        ok_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 14px;
                min-width: 180px;
                font-family: 'Segoe UI';
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #2573a7;
            }
        """)
        ok_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button, alignment=Qt.AlignCenter)
        
        self.setLayout(layout)

if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    welcome = WelcomeDialog()
    welcome.exec_()
    sys.exit(app.exec_())
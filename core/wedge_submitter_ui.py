import sys
import os
import subprocess
import json
import qdarkstyle
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QFileDialog, QVBoxLayout,
    QLabel, QTextEdit, QMessageBox
)
from PyQt5.QtCore import Qt


class WedgeRunner(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_folder = None
        self.wedge_config_path = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Wedge Config UI")
        self.setGeometry(100, 100, 700, 600)

        layout = QVBoxLayout()

        self.folder_button = QPushButton("1. Select Config Folder", self)
        self.folder_button.clicked.connect(self.pick_folder)
        layout.addWidget(self.folder_button)

        self.path_label = QLabel("", self)
        self.path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.path_label)

        self.config_display = QTextEdit(self)
        layout.addWidget(self.config_display)

        self.save_button = QPushButton("Save Changes to Config", self)
        self.save_button.clicked.connect(self.save_config_changes)
        self.save_button.setEnabled(False)
        layout.addWidget(self.save_button)

        self.run_button = QPushButton("2. Submit Wedges", self)
        self.run_button.clicked.connect(self.run_script)
        self.run_button.setEnabled(False)
        layout.addWidget(self.run_button)

        self.setLayout(layout)

    def pick_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder Containing JSON Files")
        if not folder:
            return

        workflow_path = os.path.join(folder, "workflow_api.json")
        wedge_config_path = os.path.join(folder, "wedge_config.json")

        if not os.path.exists(workflow_path) or not os.path.exists(wedge_config_path):
            QMessageBox.warning(self, "Missing Files", "workflow_api.json or wedge_config.json not found.")
            return

        self.selected_folder = folder
        self.wedge_config_path = wedge_config_path

        self.path_label.setText(
            f"workflow_api.json: {workflow_path}\nwedge_config.json: {wedge_config_path}"
        )

        try:
            with open(wedge_config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                self.config_display.setText(json.dumps(config, indent=4))
                self.run_button.setEnabled(True)
                self.save_button.setEnabled(True)
        except Exception as e:
            self.config_display.setText(f"Error loading config: {str(e)}")
            self.run_button.setEnabled(False)
            self.save_button.setEnabled(False)

    def save_config_changes(self):
        text = self.config_display.toPlainText()
        try:
            parsed_json = json.loads(text)
            with open(self.wedge_config_path, "w", encoding="utf-8") as f:
                json.dump(parsed_json, f, indent=4)
            QMessageBox.information(self, "Saved", "wedge_config.json updated successfully.")
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Invalid JSON", f"Could not save:\n{e}")

    def run_script(self):
        if not self.selected_folder:
            QMessageBox.warning(self, "No Folder Selected", "Please select a folder first.")
            return

        try:
            # Get the absolute path to wedge_submitter.py next to this script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            wedge_submitter_path = os.path.join(script_dir, "wedge_submitter.py")

            if not os.path.exists(wedge_submitter_path):
                QMessageBox.critical(self, "Script Not Found", f"Could not find wedge_submitter.py at:\n{wedge_submitter_path}")
                return

            # Run the script with subprocess
            subprocess.Popen(["python", wedge_submitter_path, "--json-folder", self.selected_folder])
            QMessageBox.information(self, "Submitted", "Wedge submission started!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not run the script:\n{str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    window = WedgeRunner()
    window.show()
    sys.exit(app.exec_())

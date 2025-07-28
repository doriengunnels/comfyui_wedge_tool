import sys
import os
import json
from PIL import Image
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QSlider, QComboBox,
    QFileDialog, QPushButton, QMainWindow, QScrollArea
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
import qdarkstyle


class WedgeViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wedge Viewer")

        self.image_label = QLabel("Load a PNG to start", alignment=Qt.AlignCenter)
        self.image_label.setObjectName("imageLabel")  # Set object name to style it specifically
        self.image_label.setScaledContents(False)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.image_label)

        self.load_button = QPushButton("Load Image")
        self.load_button.clicked.connect(self.load_image)

        self.slider_container = QWidget()
        self.slider_layout = QVBoxLayout()
        self.slider_container.setLayout(self.slider_layout)

        self.param_sliders = {}
        self.metadata = {}
        self.folder_path = ""
        self.filename_prefix = ""
        self.current_pixmap = None

        central_layout = QVBoxLayout()
        central_layout.addWidget(self.load_button)
        central_layout.addWidget(self.scroll_area)
        central_layout.addWidget(self.slider_container)

        central_widget = QWidget()
        central_widget.setLayout(central_layout)
        self.setCentralWidget(central_widget)

    def load_image(self):
        
        default_directory = "D:\\AI\ComfyUI\\output"
        if not os.path.isdir(default_directory):
            default_directory = ""
        
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Image", default_directory, "PNG Images (*.png)")
        if not file_path:
            return

        self.folder_path = os.path.dirname(file_path)

        try:
            # image = Image.open(file_path)
            # wedge_info_json = image.info.get("Wedge Info", "")

            with Image.open(file_path) as img:
                metadata = json.loads(img.info.get("prompt"))
                for k, v in metadata.items():
                    if v["_meta"]["title"] == "WEDGE_string":
                        # wedge_info_json = json.loads(v["inputs"]["value"])
                        wedge_info_json = v["inputs"]["value"]
                        
        except Exception as e:
            self.image_label.setText(f"Failed to read image: {e}")
            return

        if not wedge_info_json:
            self.image_label.setText("No 'Wedge Info' metadata found in image.")
            return

        try:
            self.metadata = json.loads(wedge_info_json)
        except json.JSONDecodeError:
            self.image_label.setText("Invalid JSON in 'Wedge Info' metadata.")
            return

        self.filename_prefix = self.metadata.get("filename_prefix", "image")
        self.wedge_params = self.metadata.get("param_wedges", {})
        print(self.wedge_params)

        # Clear old UI elements
        for i in reversed(range(self.slider_layout.count())):
            self.slider_layout.itemAt(i).widget().setParent(None)

        self.param_sliders.clear()

        for param, value in self.wedge_params.items():
            range_type = value[2]
            if range_type == "explicit":
                values = value[1]

                # If all values are strings, use a dropdown
                if all(isinstance(v, str) for v in values):
                    dropdown = QComboBox()
                    dropdown.addItems(values)
                    dropdown.currentIndexChanged.connect(self.make_dropdown_callback(param, dropdown, values))

                    label = QLabel(f"{param}: {values[0]}")
                    self.slider_layout.addWidget(label)
                    self.slider_layout.addWidget(dropdown)

                    self.param_sliders[param] = {
                        "dropdown": dropdown,
                        "values": values,
                        "label": label
                    }
                    continue

            elif range_type == "minmax":
                min_val, max_val, step = value[1]
                num_steps = int(round((max_val - min_val) / step)) + 1
                values = [round(min_val + i * step, 10) for i in range(num_steps)]
            else:
                continue  # Unknown type

            # Create slider
            slider = QSlider(Qt.Horizontal)
            slider.setMinimum(0)
            slider.setMaximum(len(values) - 1)
            slider.setTickInterval(1)
            slider.setValue(0)
            slider.setSingleStep(1)

            label = QLabel(f"{param}: {values[0]}")
            slider.valueChanged.connect(self.make_slider_callback(param, slider, label, values))

            self.slider_layout.addWidget(label)
            self.slider_layout.addWidget(slider)
            self.param_sliders[param] = {
                "slider": slider,
                "values": values,
                "label": label
            }

        self.update_image_display()

    def make_slider_callback(self, param, slider, label, values):
        def callback(value_index):
            val = values[value_index]
            label.setText(f"{param}: {val}")
            self.update_image_display()
        return callback

    def make_dropdown_callback(self, param, dropdown, values):
        def callback(index):
            val = values[index]
            self.param_sliders[param]["label"].setText(f"{param}: {val}")
            self.update_image_display()
        return callback

    def update_image_display(self):
        if not self.folder_path:
            return

        parts = [self.filename_prefix]
        for param in self.param_sliders:
            control_data = self.param_sliders[param]
            values = control_data["values"]

            # Get current value
            if "slider" in control_data:
                value_index = control_data["slider"].value()
            elif "dropdown" in control_data:
                value_index = control_data["dropdown"].currentIndex()
            else:
                continue

            value = values[value_index]

            # Format value correctly
            if isinstance(value, str):
                value_str = value
            else:
                is_float_series = any(isinstance(v, float) and not v.is_integer() for v in values)
                if is_float_series:
                    max_decimals = max(
                        len(str(v).split(".")[1]) if isinstance(v, float) else 0
                        for v in values
                    )
                    value_str = f"{value:.{max_decimals}f}"
                else:
                    value_str = str(int(value))

            parts.append(f"{param}-{value_str}")

        filename = "__".join(parts) + "_00001_.png"
        full_path = os.path.join(self.folder_path, filename)

        if os.path.exists(full_path):
            self.current_pixmap = QPixmap(full_path)
            self.resize_image_to_fit()
        else:
            self.image_label.setPixmap(QPixmap())  # Clear image
            self.image_label.setText(f"Image not found:\n{filename}")

    def resize_image_to_fit(self):
        if not self.current_pixmap or self.current_pixmap.isNull():
            return

        scroll_size = self.scroll_area.viewport().size()
        scaled_pixmap = self.current_pixmap.scaled(
            scroll_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.image_label.setPixmap(scaled_pixmap)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resize_image_to_fit()


if __name__ == "__main__":

    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    viewer = WedgeViewer()
    viewer.resize(1000, 700)
    viewer.show()
    sys.exit(app.exec_())

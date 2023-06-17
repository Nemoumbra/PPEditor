import os
import shutil
import sys

from PyQt5 import QtWidgets

from data import resource_path
from interface import main_window
from interface.line_edit_field import QLineEditField
from param.param import Param
from settings.settings import Settings


class Application(QtWidgets.QMainWindow, main_window.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.set_connections()

        self.settings = Settings(open(resource_path("res/settings.txt")).readlines())
        self.param = Param(None, self.settings)
        self.path = None

        # If opened via cmd with parameters
        if len(sys.argv) > 1:
            if sys.argv[1]:
                file = sys.argv[1]
                file = file.replace("\\", "/")
                self.load_param_file(file)

    def set_connections(self):
        """
        Set UI element connections
        """
        self.action_load.triggered.connect(self.select_param)
        self.action_save.triggered.connect(self.save_param_file)
        self.action_refresh.triggered.connect(self.refresh)
        self.cb_sections.currentTextChanged.connect(self.selected_section_changed)
        self.cb_entries.currentTextChanged.connect(self.selected_entry_changed)

    def select_param(self):
        """
        Opens select param
        """
        input_file = QtWidgets.QFileDialog.getOpenFileName(self, "Open")
        if input_file:
            if input_file[0] != "":
                self.load_param_file(input_file[0])

    def load_param_file(self, file):
        """
        Read Param file
        """
        with open(file, "r+b") as f:
            data = f.read()
            self.path = file
            self.param.load_from_data(data)
            self.output_path = os.path.dirname(os.path.abspath(self.path))
            self.file_name = os.path.basename(os.path.abspath(self.path))
            self.refresh()

    def save_param_file(self):
        """
        Saves Param file
        """

        # Save backup if enabled in settings
        if not self.check_backup.isChecked:
            shutil.copy(self.path, f"{self.path}.bak")

        # Save file
        if self.path and self.param:
            with open(self.path, "wb") as f:
                f.write(self.param.to_bytes())

    def refresh(self):
        """
        Refreshes UI
        """
        if self.param is None:
            return

        self.cb_sections.clear()
        for section in self.param.section_list:
            self.cb_sections.addItem(
                f"Section {section.id+1} ({section.entry_amount} entries)"
            )

        self.cb_entries.clear()
        for entry in self.param.get_section_entries():
            self.cb_entries.addItem(f"{entry.id+1} ({entry.get_name()})")

    def selected_section_changed(self):
        """
        Loads entry list of selected section
        """
        self.cb_entries.clear()
        for entry in self.param.get_section_entries(self.cb_sections.currentIndex()):
            self.cb_entries.addItem(f"{entry.id+1} ({entry.get_name()})")

    def selected_entry_changed(self):
        """
        Loads field list of current entry
        """
        self.clear_form_items()

        current_section = self.cb_sections.currentIndex()
        current_entry = self.cb_entries.currentIndex()

        for field in self.param.get_section_entry(
            current_section, current_entry
        ).fields:
            editor = QLineEditField(self.sc_content)
            editor.set_field(field)
            label = QtWidgets.QLabel(field.settings.name)
            self.fl_fields.addRow(label, editor)

    def clear_form_items(self):
        """
        Clears all items in form
        """
        for i in reversed(range(self.fl_fields.count())):
            self.fl_fields.itemAt(i).widget().setParent(None)

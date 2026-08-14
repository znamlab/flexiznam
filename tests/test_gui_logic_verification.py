import importlib.util
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.integration


class TestFlexiGuiLogic(unittest.TestCase):
    def setUp(self):
        # 1. Mock all dependencies
        self.mock_tk = MagicMock()
        sys.modules["tkinter"] = self.mock_tk
        sys.modules["tkinter.ttk"] = MagicMock()
        sys.modules["ttkwidgets"] = MagicMock()
        sys.modules["yaml"] = MagicMock()

        # Mock flexiznam and its submodules
        self.mock_flz = MagicMock()
        # Configure PARAMETERS for FlexiGui
        self.mock_flz.PARAMETERS = {"project_ids": {"test_project": "id1"}}
        sys.modules["flexiznam"] = self.mock_flz
        sys.modules["flexiznam.camp"] = MagicMock()
        sys.modules["flexiznam.camp.sync_data"] = MagicMock()

        # 2. Load flexigui.py from source
        file_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../flexiznam/gui/flexigui.py")
        )
        spec = importlib.util.spec_from_file_location("flexigui_module", file_path)
        flexigui_module = importlib.util.module_from_spec(spec)
        # We need to add it to sys.modules so relative imports inside it (if any)
        # or circular refs work?
        # flexigui.py uses absolute imports for flexiznam.
        sys.modules["flexigui_module"] = flexigui_module
        spec.loader.exec_module(flexigui_module)

        self.FlexiGui = flexigui_module.FlexiGui

        # 3. Instantiate FlexiGui
        # Since it inherits from tk.Tk (which is a mock), calling it calls the mock.
        # But the class itself is real.
        # __init__ calls super().__init__(), then self methods.

        # We need to ensure tk.Tk is a class we can inherit from?
        # MagicMock can be inherited from? No.
        # But if tk.Tk is a MagicMock object, class FlexiGui(tk.Tk) creates a
        # class inheriting from MagicMock type?
        # Actually, sys.modules['tkinter'].Tk should be a class, not an
        # instance, for inheritance to work smoothly.
        # But MagicMock usually handles this by being a callable that returns
        # a mock.

        # Let's try to make tk.Tk a proper mock class
        # self.mock_tk.Tk = MagicMock # This makes it a class

        # Actually, let's just patch __init__ to be safe, now that we have the
        # real class object.
        with patch.object(self.FlexiGui, "__init__", return_value=None):
            self.gui = self.FlexiGui()

        # Manually set up attributes
        self.gui.treeview = MagicMock()
        self.gui.recording_info_label = MagicMock()
        self.gui.selected_item = MagicMock()
        self.gui.textview = MagicMock()
        self.gui.FLEXILIMS_ONLY_FIELDS = ("children", "project", "origin_id")
        self.gui.report = MagicMock()
        self.gui._entity_by_itemid = {}
        self.gui.frames = {"R": MagicMock()}

    def test_on_treeview_select_recording(self):
        # Setup data
        item_id = "item1"
        self.gui.treeview.focus.return_value = item_id
        data = {"type": "recording", "some_field": "value"}
        self.gui._entity_by_itemid[item_id] = ("recording_name", data)

        # Call the method
        # We need to mock yaml inside the module we loaded
        # Since we loaded it as 'flexigui_module', we can patch it there?
        # Or just patch sys.modules['yaml'] which we already did.

        self.FlexiGui.on_treeview_select(self.gui, MagicMock())

        # Verify label is shown
        self.gui.recording_info_label.grid.assert_called_once()
        self.gui.recording_info_label.grid_remove.assert_not_called()

    def test_on_treeview_select_other(self):
        # Setup data
        item_id = "item2"
        self.gui.treeview.focus.return_value = item_id
        data = {"type": "dataset", "some_field": "value"}
        self.gui._entity_by_itemid[item_id] = ("dataset_name", data)

        # Call the method
        self.FlexiGui.on_treeview_select(self.gui, MagicMock())

        # Verify label is hidden
        self.gui.recording_info_label.grid.assert_not_called()
        self.gui.recording_info_label.grid_remove.assert_called_once()


if __name__ == "__main__":
    unittest.main()

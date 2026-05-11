import unittest
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from flexiznam.cli import gui


class TestCliGui(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        # Mock FlexiGui
        self.mock_gui_cls_patcher = patch("flexiznam.gui.flexigui.FlexiGui")
        self.MockFlexiGui = self.mock_gui_cls_patcher.start()
        self.mock_app = self.MockFlexiGui.return_value

        # Mock StringVars on the app instance
        # Since Tkinter variables might need a root window or just be mocked
        self.mock_app.root_folder = MagicMock()
        self.mock_app.project = MagicMock()
        self.mock_app.origin_name = MagicMock()

    def tearDown(self):
        self.mock_gui_cls_patcher.stop()

    def test_gui_default_args(self):
        with self.runner.isolated_filesystem():
            # Create a dummy directory to use as root
            pass

        # We need an existing directory for click.Path(exists=True)
        # Using '.' as default
        result = self.runner.invoke(gui, [])
        self.assertEqual(result.exit_code, 0)

        # Check defaults
        # default root_folder is "."
        self.mock_app.root_folder.set.assert_called_with(".")
        self.mock_app.project.set.assert_not_called()
        self.mock_app.origin_name.set.assert_not_called()
        self.mock_app.mainloop.assert_called_once()

    def test_gui_with_args(self):
        project_val = "my_project"
        origin_val = "my_origin"
        root_val = "."  # needs to exist

        result = self.runner.invoke(
            gui, [root_val, "--project", project_val, "--origin", origin_val]
        )

        if result.exit_code != 0:
            print(result.output)

        self.assertEqual(result.exit_code, 0)

        self.mock_app.root_folder.set.assert_called_with(root_val)
        self.mock_app.project.set.assert_called_with(project_val)
        self.mock_app.origin_name.set.assert_called_with(origin_val)
        self.mock_app.mainloop.assert_called_once()

    def test_gui_short_flags(self):
        project_val = "p_short"
        origin_val = "o_short"

        result = self.runner.invoke(gui, [".", "-p", project_val, "-o", origin_val])

        self.assertEqual(result.exit_code, 0)

        self.mock_app.project.set.assert_called_with(project_val)
        self.mock_app.origin_name.set.assert_called_with(origin_val)


if __name__ == "__main__":
    unittest.main()

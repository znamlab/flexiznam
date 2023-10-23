import os
import tkinter as tk
from tkinter import ttk
from ttkwidgets import CheckboxTreeview
import yaml
from pathlib import Path
import flexiznam as flz
import flexiznam.camp.sync_data


class FlexiGui(tk.Tk):
    FLEXILIMS_ONLY_FIELDS = ("children", "project", "origin_id")
    RESOURCES = Path(__file__).parent

    def __init__(self):
        super().__init__()

        self.title("FlexiZnam GUI")
        self.geometry("800x600")

        self.rowconfigure(1, weight=10)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=3)

        self.frames = dict()
        self._create_frames()
        self._setup_widgets()
        self._entity_by_itemid = {}
        self.contains_errors = False
        self.data = {}

    ############# GUI setup methods #############
    # These methods are used to create the GUI elements

    def _setup_widgets(self):
        self._create_frames()
        self._create_buttons()
        self._create_treeview()
        self._create_textview()
        self._create_statusbar()

    def _create_frames(self):
        self.frames["T"] = tk.Frame(self)
        self.frames["T"].grid(
            row=0, column=0, padx=10, pady=5, columnspan=2, sticky="nwe"
        )
        self.frames["T"].rowconfigure(0, weight=1)
        self.frames["T"].rowconfigure(1, weight=1)
        for i in range(10):
            self.frames["T"].columnconfigure(i, weight=1)
        self.frames["T"].columnconfigure(3, weight=10)
        self.frames["L"] = tk.Frame(self)
        self.frames["L"].grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.frames["L"].rowconfigure(0, weight=1)
        self.frames["L"].columnconfigure(0, weight=1)
        self.frames["R"] = tk.Frame(self)
        self.frames["R"].grid(row=1, column=1, padx=10, pady=5, sticky="nsew")
        self.frames["R"].rowconfigure(0, weight=1)
        self.frames["R"].rowconfigure(1, weight=30)
        self.frames["R"].rowconfigure(2, weight=1)
        self.frames["R"].columnconfigure(0, weight=1)
        self.frames["B"] = tk.Frame(self)
        self.frames["B"].grid(
            row=2, column=0, columnspan=2, padx=10, pady=5, sticky="sew"
        )
        self.frames["B"].rowconfigure(0, weight=1)
        self.frames["B"].columnconfigure(0, weight=10)

    def _create_treeview(self):
        # Create the Treeview
        self.treeview = CheckboxTreeview(
            self.frames["L"],
            columns=("datatype",),
            selectmode="browse",
        )

        self.treeview.grid(row=0, column=0, sticky="nsew")
        self.treeview.heading("datatype", text="Datatype")
        self.treeview.column("datatype", width=200)
        # Bind the Treeview selection event
        self.treeview.bind("<<TreeviewSelect>>", self.on_treeview_select)
        self.treeview.tag_configure("error", background="red")

    def _create_textview(self):
        # Create the Text widget
        tk.Label(self.frames["R"], text="Selected item:").grid(
            row=0,
            column=0,
            sticky="nw",
        )
        self.selected_item = tk.StringVar()
        self.selected_item.set("None")
        l = tk.Label(self.frames["R"], textvariable=self.selected_item)
        l.grid(row=0, column=1, sticky="new")
        self.textview = tk.Text(self.frames["R"], width=40, height=10, wrap="none")
        self.textview.grid(row=1, column=0, sticky="nsew", columnspan=2)
        self.textview.bind("<<Modified>>", self.on_textview_change)
        self.update_item_btn = tk.Button(
            self.frames["R"], text="Update item", command=self.update_item
        )
        self.update_item_btn.grid(row=2, column=1, sticky="nsw")

    def _create_buttons(self):
        topf = self.frames["T"]
        self.parse_btn = tk.Button(topf, text="Parse", command=self.parse_folder)
        self.parse_btn.grid(row=0, column=0, sticky="w")
        self.load_btn = tk.Button(topf, text="Load", command=self.load_yaml)
        self.load_btn.grid(row=0, column=1, sticky="w")
        self.write_btn = tk.Button(topf, text="Write", command=self.write_yaml)
        self.write_btn.grid(row=0, column=2)

        # add project dropdown and label
        tk.Label(topf, text="Project:").grid(row=0, column=3, sticky="w")
        self.project = tk.StringVar(self)
        self.project.set("SELECT PROJECT")
        self.proj_ddwn = tk.OptionMenu(
            topf,
            self.project,
            "SELECT PROJECT",
            *flz.PARAMETERS["project_ids"].keys(),
        ).grid(row=0, column=4, columnspan=3, sticky="w")
        self.upload_btn = tk.Button(topf, text="Upload", command=self.upload)
        self.upload_btn.grid(row=0, column=7)

        # add conflicts dropdown and label
        tk.Label(topf, text="Conflicts:").grid(row=0, column=8, sticky="w")
        self.conflicts = tk.StringVar(self)
        self.conflicts.set("abort")
        self.conflicts_ddwn = tk.OptionMenu(
            topf, self.conflicts, "abort", "overwrite", "skip"
        )
        self.conflicts_ddwn.grid(row=0, column=9, sticky="w")
        self.quit_btn = tk.Button(topf, text="Quit", command=self.quit)
        self.quit_btn.grid(row=0, column=10, sticky="e")

        # add origin name and root dir
        tk.Label(topf, text="Origin name:").grid(row=1, column=0, sticky="w")
        self.origin_name = tk.StringVar(self)
        self.origin_name.set("ENTER FLEXILIMS ORIGIN NAME")
        self.origin_name_entry = tk.Entry(topf, textvariable=self.origin_name)
        self.origin_name_entry.grid(row=1, column=1, columnspan=2, sticky="nsew")
        tk.Label(topf, text="Root directory:").grid(row=1, column=3, sticky="w")
        self.root_folder = tk.StringVar(self)
        self.root_folder.set(os.getcwd())
        self.root_folder_entry = tk.Entry(topf, textvariable=self.root_folder)
        self.root_folder_entry.grid(row=1, column=4, columnspan=6, sticky="nsew")
        self.chg_dir_btn = tk.Button(topf, text="...", command=self.chg_root_folder)
        self.chg_dir_btn.grid(row=1, column=10)

    def _create_statusbar(self):
        self.sb_msg = tk.StringVar()
        self.statusbar = tk.Label(
            self.frames["B"], textvariable=self.sb_msg, bd=1, relief=tk.SUNKEN
        )
        self.statusbar.grid(row=0, column=0, sticky="sw")
        self.sb_msg.set("Ready")

    ############# GUI update methods #############
    # These methods are used to actually do stuff with the GUI elements
    def get_checked_data(self, item=None, checked_data=None):
        if checked_data is None:
            checked_data = dict(children=dict())
            for k in ["project", "origin_name", "root_folder"]:
                checked_data[k] = self.data[k]

        for child in self.treeview.get_children(item=item):
            if self.treeview.tag_has("checked", child) or self.treeview.tag_has(
                "tristate", child
            ):
                name, data = self._entity_by_itemid[child]
                data = data.copy()
                if "children" in data:
                    data["children"] = {}
                data = self.get_checked_data(item=child, checked_data=data)
                checked_data["children"][name] = data
        return checked_data

    def report(self, message):
        self.sb_msg.set(message)
        print(message)
        self.update()

    def _check_options_are_set(self, options=("project", "origin_name")):
        self.report("Checking options")
        init_values = dict(project="SELECT", origin_name="ENTER")
        for option in options:
            value = getattr(self, option).get()
            if value.startswith(init_values[option]):
                tk.messagebox.showerror("Error", f"Error: enter {option} first!")
                return False
        self.report("Options are set")
        return True

    def parse_folder(self):
        if not self._check_options_are_set():
            return
        folder = tk.filedialog.askdirectory(
            initialdir=self.root_folder.get(), title="Select directory to parse"
        )
        self.report(f"Parsing folder {folder}...")
        self.root_folder.set(folder)
        data = flz.camp.sync_data.create_yaml_dict(
            folder_to_parse=folder,
            project=self.project.get(),
            origin_name=self.origin_name.get(),
            format_yaml=True,
        )
        self.report("Parsing done. Validating data...")
        data, errors = flz.camp.sync_data.check_yaml_validity(data)
        self.data = data
        self.update_data(remove_unchecked=False)
        checked = self.get_checked_data(item=None, checked_data=None)
        assert checked == self.data
        self.report("Done")

    def chg_root_folder(self):
        self.report("Changing root folder")
        self.root_folder.set(
            tk.filedialog.askdirectory(
                initialdir=self.root_folder.get(), title="Select root directory"
            )
        )

    def on_treeview_select(self, event):
        item = self.treeview.focus()
        name, data = self._entity_by_itemid[item]
        self.report(f"Selected item: {name}")
        self.selected_item.set(name)
        display = {k: v for k, v in data.items() if k not in self.FLEXILIMS_ONLY_FIELDS}
        self.textview.delete(1.0, tk.END)
        self.textview.insert(tk.END, yaml.dump(display))

    def on_textview_change(self, event):
        return

    def load_yaml(self):
        """Load a YAML file and display it in the treeview"""
        self.report("Select YAML file to load")
        filetypes = (("Yaml files", "*.yml *.yaml"), ("All files", "*.*"))

        filename = tk.filedialog.askopenfilename(
            title="Select YAML file to load", filetypes=filetypes
        )
        if not filename:
            return
        self.report(f"Loading YAML file {filename}...")
        with open(filename, "r") as f:
            self.data = yaml.safe_load(f)
        self.update_data()
        self.report("Done")

    def update_data(self, name_to_select=None, remove_unchecked=True):
        """Update GUI data from self.data

        Args:
            name_to_select (str, optional): Name of item to select in treeview.
                Defaults to None."""
        self.report("Updating GUI")
        if remove_unchecked:
            self.data = self.get_checked_data()
        self.textview.delete("1.0", tk.END)
        self.selected_item.set("None")
        self.treeview.delete(*self.treeview.get_children())
        self._entity_by_itemid = {}

        if "project" in self.data:
            self.project.set(self.data["project"])
        if "origin_name" in self.data:
            self.origin_name.set(self.data["origin_name"])
        if "root_folder" in self.data:
            self.root_folder.set(self.data["root_folder"])

        self.contains_errors = False
        self._insert_yaml_data(self.data["children"], name_to_select=name_to_select)

    def _insert_yaml_data(self, data, parent="", name_to_select=None):
        assert isinstance(data, dict), "data must be a dict"
        for child, child_data in data.items():
            assert "type" in child_data, f"datatype missing for {child}"
            dtype = child_data["type"]
            item = self.treeview.insert(
                parent,
                "end",
                text=child,
                values=[dtype],
                open=True,
            )
            if any(
                [
                    v.startswith("XXERRORXX")
                    for v in child_data.values()
                    if isinstance(v, str)
                ]
            ):
                self.contains_errors = True
                self.report(f"ERROR: {child} contains errors")
                self.treeview.item(item, tags=("error", "checked"))
            self.treeview.change_state(item, "checked")
            self._entity_by_itemid[item] = (child, child_data)
            if name_to_select and child == name_to_select:
                self.treeview.focus(item)
                self.treeview.selection_set(item)

            if "children" in child_data:
                self._insert_yaml_data(
                    child_data["children"], parent=item, name_to_select=name_to_select
                )

    def write_yaml(self):
        """Write the current data to a YAML file"""
        self.report("Select YAML file to write")
        target = tk.filedialog.asksaveasfilename(
            initialdir=self.root_folder.get(),
            title="Select YAML file to write",
            filetypes=(("Yaml files", "*.yml *.yaml"), ("All files", "*.*")),
        )
        if not target:
            self.report("No file selected. Cancel")
            return
        data = dict(self.data)
        data["project"] = self.project.get()
        data["root_folder"] = self.root_folder.get()
        with open(target, "w") as f:
            yaml.dump(data, f)
        self.report('Wrote YAML file "{}"'.format(target))

    def upload(self):
        """Upload data to flexilims"""
        print("Uploading data to flexilims")
        if not self._check_options_are_set():
            return

        if not self.data:
            tk.messagebox.showerror("Error", "No data loaded")
            return

        self.report("Validating data...")
        self.update_data()
        data, errors = flz.camp.sync_data.check_yaml_validity(self.get_checked_data())

        if self.contains_errors:
            tk.messagebox.showerror(
                "Error",
                "There are still errors. Please fix them before uploading",
            )
            return

        data = dict(self.data)
        # remove unchecked items
        for item in self.treeview.get_children():
            if not self.treeview.tag_has("checked", item):
                name, _ = self._entity_by_itemid[item]
                self.report(f"Removing item {name}")
                data["children"].pop(name)

        data["project"] = self.project.get()
        data["root_folder"] = self.root_folder.get()

        self.report("Validating data...")
        flz.camp.sync_data.upload_yaml(
            source_yaml=data,
            raw_data_folder=data["root_folder"],
            verbose=True,
            log_func=print,
            flexilims_session=None,
            conflicts=self.conflicts.get(),
        )
        self.report("Done")

    def update_item(self):
        """Update the selected item with the textview contents"""

        text = self.textview.get(1.0, tk.END)
        if not text.strip():
            return
        item = self.treeview.focus()
        name, original_data = self._entity_by_itemid[item]
        self.report(f"Updating item {name}")
        assert name == self.selected_item.get(), "Selected item does not match"
        data = yaml.safe_load(text)
        for field in self.FLEXILIMS_ONLY_FIELDS:
            if field in original_data:
                data[field] = original_data[field]
        self._entity_by_itemid[item] = (name, data)
        parents = []
        parent_id = item
        while True:
            parent = self.treeview.parent(parent_id)
            if not parent:
                break
            parents.append(self._entity_by_itemid[parent][0])
            parent_id = parent
        ref = self.data
        for parent in reversed(parents):
            ref = ref["children"][parent]
        ref["children"][name] = data
        self.update_data(name_to_select=name)
        self.report("Done")


if __name__ == "__main__":

    def diffofdict(d1, d2, diff=None, level=""):
        """Find differences between 2 dictionary of dictionaries"""

        if diff is None:
            diff = []
        all_keys = set(list(d1.keys()) + list(d2.keys()))
        for k in all_keys:
            level = level + k + "."
            if k not in d2:
                diff.append(f"{level} (missing in d2)")
            elif k not in d1:
                diff.append(f"{level} (missing in d1)")
            elif isinstance(d1[k], dict):
                diff = diffofdict(d1[k], d2[k], diff, level)
            elif d1[k] != d2[k]:
                diff.append(f"{level} ({d1[k]} != {d2[k]})")
        return diff

    app = FlexiGui()
    app.root_folder.set(
        "/Volumes/lab-znamenskiyp/data/instruments/raw_data/projects/blota_onix_pilote/BRYA142.5d/"
    )
    app.origin_name.set("BRYA142.5d")
    app.project.set("blota_onix_pilote")
    app.mainloop()
    df = diffofdict(app.data["children"], app.get_checked_data()["children"])
    a = app.data["children"]["S20230915"]["children"]
    b = app.get_checked_data()["children"]["S20230915"]["children"]
    a == b

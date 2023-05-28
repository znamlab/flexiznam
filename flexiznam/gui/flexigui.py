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

        self.data = {}

    def _setup_widgets(self):
        self._create_frames()
        self._create_buttons()
        self._create_treeview()
        self._create_textview()

    def _create_frames(self):
        self.frames["t"] = tk.Frame(self)
        self.frames["t"].grid(
            row=0, column=0, padx=10, pady=5, columnspan=2, sticky="nwe"
        )
        self.frames["t"].rowconfigure(0, weight=1)
        self.frames["t"].rowconfigure(1, weight=1)
        for i in range(10):
            self.frames["t"].columnconfigure(i, weight=1)
        self.frames["t"].columnconfigure(3, weight=10)
        self.frames["bl"] = tk.Frame(self)
        self.frames["bl"].grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.frames["bl"].rowconfigure(0, weight=1)
        self.frames["bl"].columnconfigure(0, weight=1)
        self.frames["br"] = tk.Frame(self)
        self.frames["br"].grid(row=1, column=1, padx=10, pady=5, sticky="nsew")
        self.frames["br"].rowconfigure(0, weight=1)
        self.frames["br"].rowconfigure(1, weight=30)
        self.frames["br"].rowconfigure(2, weight=1)
        self.frames["br"].columnconfigure(0, weight=1)

    def _create_treeview(self):
        # Create the Treeview
        self.treeview = CheckboxTreeview(
            self.frames["bl"],
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
        tk.Label(self.frames["br"], text="Selected item:").grid(
            row=0,
            column=0,
            sticky="nw",
        )
        self.selected_item = tk.StringVar()
        self.selected_item.set("None")
        l = tk.Label(self.frames["br"], textvariable=self.selected_item)
        l.grid(row=0, column=1, sticky="new")
        self.textview = tk.Text(self.frames["br"], width=40, height=10, wrap="none")
        self.textview.grid(row=1, column=0, sticky="nsew", columnspan=2)
        self.textview.bind("<<Modified>>", self.on_textview_change)
        self.update_item_btn = tk.Button(
            self.frames["br"], text="Update item", command=self.update_item
        )
        self.update_item_btn.grid(row=2, column=1, sticky="nsw")

    def _check_options_are_set(self, options=("project", "origin_name")):
        init_values = dict(project="SELECT", origin_name="ENTER")
        for option in options:
            value = getattr(self, option).get()
            if value.startswith(init_values[option]):
                tk.messagebox.showerror("Error", f"Error: enter {option} first!")
                return False
        return True

    def parse_folder(self):
        if not self._check_options_are_set():
            return
        folder = tk.filedialog.askdirectory(
            initialdir=self.root_folder.get(), title="Select directory to parse"
        )
        self.root_folder.set(folder)
        data = flz.camp.sync_data.create_yaml_dict(
            root_folder=folder,
            project=self.project.get(),
            origin_name=self.origin_name.get(),
            format_yaml=True,
        )
        self.data = data
        self.update_data()

    def _create_buttons(self):
        topf = self.frames["t"]
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
        fllogo = tk.PhotoImage(file=str(self.RESOURCES / "flexilims_logo.png"))
        fllogo = fllogo.subsample(10, 10)
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

    def chg_root_folder(self):
        self.root_folder.set(
            tk.filedialog.askdirectory(
                initialdir=self.root_folder.get(), title="Select root directory"
            )
        )

    def on_treeview_select(self, event):
        item = self.treeview.focus()
        name, data = self._entity_by_itemid[item]
        self.selected_item.set(name)
        display = {k: v for k, v in data.items() if k not in self.FLEXILIMS_ONLY_FIELDS}
        self.textview.delete(1.0, tk.END)
        self.textview.insert(tk.END, yaml.dump(display))

    def on_textview_change(self, event):
        print('Textview changed: "{}"'.format(event))

    def load_yaml(self):
        """Load a YAML file and display it in the treeview"""
        print("Select YAML file to load")
        filetypes = (("Yaml files", "*.yml *.yaml"), ("All files", "*.*"))

        filename = tk.filedialog.askopenfilename(
            title="Select YAML file to load", filetypes=filetypes
        )
        if not filename:
            return
        with open(filename, "r") as f:
            self.data = yaml.safe_load(f)
        print('Loaded YAML file "{}"'.format(filename))
        self.update_data()

    def update_data(self, name_to_select=None):
        """Update GUI data from self.data

        Args:
            name_to_select (str, optional): Name of item to select in treeview.
                Defaults to None."""
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
            self.treeview.change_state(item, "checked")
            if any(
                [
                    v.startswith("XXERRORXX")
                    for v in child_data.values()
                    if isinstance(v, str)
                ]
            ):
                self.treeview.item(item, tags=("error",))

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
        target = tk.filedialog.asksaveasfilename(
            initialdir=self.root_folder.get(),
            title="Select YAML file to write",
            filetypes=(("Yaml files", "*.yml *.yaml"), ("All files", "*.*")),
        )
        data = dict(self.data)
        data["project"] = self.project.get()
        data["root_folder"] = self.root_folder.get()
        with open(target, "w") as f:
            yaml.dump(data, f)
        print('Wrote YAML file "{}"'.format(target))

    def upload(self):
        """Upload data to flexilims"""
        print("Uploading data to flexilims")
        if not self._check_options_are_set():
            return

        data = dict(self.data)
        if not data:
            tk.messagebox.showerror("Error", "No data loaded")
            return
        data["project"] = self.project.get()
        data["root_folder"] = self.root_folder.get()
        if data["project"].startswith("XXERRORXX"):
            print("Project name not set")
            return
        flz.camp.sync_data.upload_yaml(
            source_yaml=data,
            raw_data_folder=data["root_folder"],
            verbose=True,
            log_func=print,
            flexilims_session=None,
            conflicts=self.conflicts.get(),
        )
        print("Done")

    def update_item(self):
        """Update the selected item with the textview contents"""
        text = self.textview.get(1.0, tk.END)
        if not text.strip():
            return
        item = self.treeview.focus()
        name, original_data = self._entity_by_itemid[item]
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


if __name__ == "__main__":
    app = FlexiGui()
    app.mainloop()

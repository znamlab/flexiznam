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

    def parse_folder(self):
        genealogy = self.genealogy.get()
        if genealogy.startswith("ENTER COMMA"):
            tk.messagebox.showerror("Error", "Error: enter genealogy first!")
            return
        project = self.project.get()
        if project == "SELECT PROJECT":
            tk.messagebox.showerror("Error", "Error: select project first!")
            return
        genealogy = [g.strip() for g in genealogy.split(",")]
        self.root_folder.set(
            tk.filedialog.askdirectory(
                initialdir=self.root_folder.get(), title="Select directory to parse"
            )
        )
        data = flz.camp.sync_data.create_yaml_dict(
            root_folder=self.root_folder.get(),
            project=project,
            genealogy=genealogy,
            format_yaml=True,
        )
        self.data = data
        self.update_data()

    def _create_buttons(self):
        topf = self.frames["t"]
        self.parse_btn = tk.Button(topf, text="Parse folder", command=self.parse_folder)
        self.parse_btn.grid(row=0, column=0, sticky="w")
        self.load_btn = tk.Button(topf, text="Load yaml", command=self.load_yaml)
        self.load_btn.grid(row=0, column=1, sticky="w")
        self.write_btn = tk.Button(topf, text="Write yaml", command=self.write_yaml)
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
        self.upload_btn = tk.Button(topf, text="Upload to flexilims")
        self.upload_btn.grid(row=0, column=7)

        self.quit_btn = tk.Button(topf, text="Quit", command=self.quit)
        self.quit_btn.grid(row=0, column=10, sticky="e")

        # add genealogy and root dir
        tk.Label(topf, text="Genealogy:").grid(row=1, column=0, sticky="w")
        self.genealogy = tk.StringVar(self)
        self.genealogy.set("ENTER COMMA SEPARATED GENEALOGY")
        self.genealogy_entry = tk.Entry(topf, textvariable=self.genealogy)
        self.genealogy_entry.grid(row=1, column=1, columnspan=3, sticky="nsew")
        tk.Label(topf, text="Root directory:").grid(row=1, column=4, sticky="w")
        self.root_folder = tk.StringVar(self)
        self.root_folder.set(os.getcwd())
        self.root_folder_entry = tk.Entry(topf, textvariable=self.root_folder)
        self.root_folder_entry.grid(row=1, column=5, columnspan=5, sticky="nsew")
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

        self.filename = tk.filedialog.askopenfilename(
            title="Select YAML file to load", filetypes=filetypes
        )
        with open(self.filename, "r") as f:
            self.data = yaml.safe_load(f)
        print('Loaded YAML file "{}"'.format(self.filename))
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
    with open("test.yml", "r") as f:
        data = yaml.safe_load(f)
    app.data = data
    app.update_data()
    app.mainloop()

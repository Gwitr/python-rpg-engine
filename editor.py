import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

import threading

import objects
from utilities import *

class KeyvaluePopup():

    def __init__(self, root, is_key):
        self.is_key = is_key
        
        self.root = root
        self.popup_root = tk.Toplevel()
        self.popup_root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.popup_root.title(f"Set {'key name' if is_key else 'value'}")
        self.popup_root.grab_set()
        self.popup_root.focus_set()

        self.entry = ttk.Entry(master=self.popup_root, width=80)
        self.entry.grid()
        self.entry.bind("<Return>", self.finalize)
        self.entry.focus_set()
        if is_key:
            self.entry.insert(tk.END, self.root.key_list_widget.item(self.root.key_list_widget.focus())["text"])
        else:
            self.entry.insert(tk.END, self.root.value_list_widget.item(self.root.value_list_widget.focus())["text"])
        self.entry.select_range(0, tk.END)
        self.entry.icursor(tk.END)
        
        self.root.current_popup = self

    def on_close(self):
        self.popup_root.grab_release()
        self.popup_root.destroy()
        self.root.current_popup = None

    def finalize(self, event):
        new_value = self.entry.get()
        
        obj = self.root.last_objects[int(self.root.object_list_widget.focus())]
        if self.is_key:
            if new_value in obj.keyvalues.keys():
                self.popup_root.withdraw()
                messagebox.showwarning("Editor error", "Key %r already exists in this object" % new_value, master=self.popup_root)
            else:
                old_key = self.root.key_list_widget.item(self.root.key_list_widget.focus())["text"]
                if old_key == "":
                    obj.keyvalues[new_value] = "[new value]"
                else:
                    obj.keyvalues = CaseInsensitiveDict({(new_value if k == old_key else k): v for k, v in obj.keyvalues.items()})
        else:
            key = self.root.key_list_widget.item(self.root.value_list_widget.focus())["text"]
            if key == "":
                obj.keyvalues["[new key]"] = new_value
            else:
                obj.keyvalues[key] = new_value

        self.root.update_keyvalues()
        
        self.popup_root.grab_release()
        self.popup_root.destroy()
        self.root.current_popup = None

class EditorThread(threading.Thread):

    def __init__(self, game):
        super().__init__()
        self.game = game

        self.root = None
        self.current_popup = None

        self.notebook = None
        self.objects_frame = None
        self.game_frame = None
        
        self.object_list_widget = None
        self.key_list_widget = None
        self.value_list_widget = None
        self.keyvalues_frame = None
        self.keyvalue_buttons_frame = None
        self.new_keyvalue_button = None
        self.del_keyvalue_button = None
        self.object_button_frame = None
        self.new_object_button = None
        self.del_object_button = None
        self.object_data_frame = None
        self.object_type_widget = None
        self.object_name_widget = None
        self.last_objects = ()
        self.name_object_map = {}
        
        self.state_list_widget = None
        self.state_frame = None
        self.music_persistent_widget = None

    def run(self):
        self.root = tk.Tk()

        ### Initialize the notebook
        self.notebook = ttk.Notebook(master=self.root)
        self.game_frame = ttk.Frame(master=self.root)
        self.objects_frame = ttk.Frame(master=self.root)
        self.notebook.add(self.objects_frame, text="Objects")
        self.notebook.add(self.game_frame, text="Game")
        self.notebook.pack()

        ### Initialize the object tab
        ## Initialize the objects editor
        # Initialize the list of objects
        self.object_list_widget = ttk.Treeview(master=self.objects_frame, height=30)# , exportselection=False)
        self.object_list_widget.heading("#0", text="Objects")
        self.object_list_widget.column("#0", minwidth=200, width=200)
        self.object_list_widget.grid(row=1, column=0)
        self.object_list_widget.bind("<Delete>", self.on_object_delete)
        self.object_list_widget.bind("<<TreeviewSelect>>", self.on_object_selected)
        
        # Initialize the button frame
        self.object_button_frame = ttk.Frame(master=self.objects_frame)
        self.object_button_frame.grid(row=2, column=0)

        # Initialize the "new object" button
        self.new_object_button = ttk.Button(master=self.object_button_frame, text="New object", command=self.on_newobj_pressed)
        self.new_object_button.grid(row=1, column=1)

        # Initialize the "delete object" button
        self.del_object_button = ttk.Button(master=self.object_button_frame, text="Delete object", command=self.on_delobj_pressed)
        self.del_object_button.grid(row=1, column=2)

        ## Initalize the keyvalue editing widgets
        # Initialize the parent frame for the lists
        self.keyvalues_frame = ttk.Frame(master=self.objects_frame)
        self.keyvalues_frame.grid(row=1, column=1)

        # Initialize list of keys
        self.key_list_widget = ttk.Treeview(master=self.keyvalues_frame, height=30)
        self.key_list_widget.heading("#0", text="Object keys")
        self.key_list_widget.column("#0", minwidth=250, width=250)
        self.key_list_widget.grid(row=1, column=1)
        self.key_list_widget.bind("<Double-Button-1>", self.on_key_interacted)
        self.key_list_widget.bind("<Delete>", self.on_keyvalue_delete)
        self.key_list_widget.bind("<<TreeviewSelect>>", self.on_key_selected)
        
        # Initialize list of values
        self.value_list_widget = ttk.Treeview(master=self.keyvalues_frame, height=30)
        self.value_list_widget.heading("#0", text="Object values")
        self.value_list_widget.column("#0", minwidth=550, width=550)
        self.value_list_widget.grid(row=1, column=2)
        self.value_list_widget.bind("<Double-Button-1>", self.on_value_interacted)
        self.value_list_widget.bind("<Delete>", self.on_keyvalue_delete)
        self.value_list_widget.bind("<<TreeviewSelect>>", self.on_value_selected)

        # Initialize the parent frame of the buttons
        self.keyvalue_buttons_frame = ttk.Frame(master=self.objects_frame)
        self.keyvalue_buttons_frame.grid(row=2, column=1)

        # Initialize the "new keyvalue pair" button
        self.new_keyvalue_button = ttk.Button(master=self.keyvalue_buttons_frame, text="New keyvalue pair", command=self.on_newkvpair_pressed)
        self.new_keyvalue_button.grid(row=1, column=1)

        # Initialize the "delete keyvalue pair" button
        self.del_keyvalue_button = ttk.Button(master=self.keyvalue_buttons_frame, text="Delete keyvalue pair", command=self.on_delkvpair_pressed)
        self.del_keyvalue_button.grid(row=1, column=2)

        ### Initialize the object data view

        ## Initialize the frame
        self.object_data_frame = ttk.Frame(master=self.objects_frame)
        self.object_data_frame.grid(row=1, column=2, sticky="NW")
        self.object_data_frame.grid_columnconfigure(1, minsize=50)

        ## Initialize the object name entry
        ttk.Label(master=self.object_data_frame, text="Name:").grid(row=1, column=1)
        self.object_name_widget = ttk.Entry(master=self.object_data_frame, width=23)
        self.object_name_widget.bind("<Return>", self.on_object_name_change)
        self.object_name_widget.grid(row=1, column=2)
        self.object_name_widget.configure(state="disabled")
        
        ## Initialize the object type combobox
        ttk.Label(master=self.object_data_frame, text="Type:").grid(row=2, column=1)
        self.object_type_widget = ttk.Combobox(master=self.object_data_frame, state="readonly", values=list(objects.NAME2OBJTYPE.keys()))
        self.object_type_widget.bind("<<ComboboxSelected>>", self.on_object_type_change)
        self.object_type_widget.grid(row=2, column=2)
        self.object_type_widget.configure(state="disabled")
        
        ### Initialize the game tab
        ## Initalize the state selection box
        # Initialize the frame
        self.state_frame = ttk.Frame(master=self.game_frame)
        self.state_frame.grid(row=0, column=0)

        # Initialize the combobox
        ttk.Label(master=self.state_frame, text="Current game state: ").grid(row=0, column=0)
        self.state_list_widget = ttk.Combobox(master=self.state_frame, state="readonly", values=list(self.game.state_map.keys()))
        self.state_list_widget.grid(row=0, column=1)
        self.state_list_widget.bind('<<ComboboxSelected>>', self.on_game_state_changed)

        ## Initialize the music persistent box
        self.music_persistent_var = tk.IntVar(master=self.game_frame, value=0)
        self.music_persistent_widget = ttk.Checkbutton(master=self.game_frame, text="Destroy all new music objects", variable=self.music_persistent_var, command=self.on_mpers_changed)
        self.music_persistent_widget.grid(row=1, column=0, sticky=tk.W)
        
        ### Main program code
        self.root.after(50, self.update)
        self.root.mainloop()

    def on_mpers_changed(self):
        self.game.music_persistent = bool(self.music_persistent_var.get())

    def on_object_name_change(self, e):
        obj = self.last_objects[int(self.object_list_widget.focus())]
        obj.name = e.widget.get()
        
        self.update_objects()
        for i, x in enumerate(self.last_objects):
            if x is obj:
                self.object_list_widget.focus(i)
                self.object_list_widget.selection_set(i)

    def on_object_type_change(self, e):
        old_obj = self.last_objects[int(self.object_list_widget.focus())]
        new_obj = objects.NAME2OBJTYPE[e.widget["values"][e.widget.current()]](old_obj.name, CaseInsensitiveDict(old_obj.keyvalues), old_obj.game)
        new_obj.started = old_obj.started
        new_obj.x = old_obj.x
        new_obj.y = old_obj.y
        self.game.objects = OrderedSet([(new_obj if i is old_obj else i) for i in self.game.objects])
        new_obj.trigger_input("start", "")
        
        self.update_objects()
        for i, x in enumerate(self.last_objects):
            if x is new_obj:
                self.object_list_widget.focus(i)
                self.object_list_widget.selection_set(i)

    def on_newobj_pressed(self):
        new_obj = objects.Object("New object", CaseInsensitiveDict({}), self.game)
        self.game.objects.add(new_obj)
        
        self.update_objects()
        for i, x in enumerate(self.last_objects):
            if x is new_obj:
                self.object_list_widget.focus(i)
                self.object_list_widget.selection_set(i)

    def on_delobj_pressed(self):
        self.on_object_delete(None, show_error=True)

    def on_key_selected(self, event):
        if self.value_list_widget.focus() == event.widget.focus():
            return
        
        self.value_list_widget.focus(event.widget.focus())
        self.value_list_widget.selection_set(event.widget.focus())

    def on_value_selected(self, event):
        if self.key_list_widget.focus() == event.widget.focus():
            return
        
        self.key_list_widget.focus(event.widget.focus())
        self.key_list_widget.selection_set(event.widget.focus())

    def on_delkvpair_pressed(self):
        self.on_keyvalue_delete(None, show_error=True)

    def on_object_delete(self, event, show_error=False):
        sel = self.object_list_widget.focus()
        if sel == "":
            if show_error:
                messagebox.showwarning("Editor error", "Please select an object first.")
            return

        obj = self.last_objects[int(sel)]
        self.game.objects.remove(obj)

    def on_keyvalue_delete(self, event, show_error=False):
        sel = self.object_list_widget.focus()
        if sel == "":
            if show_error:
                messagebox.showwarning("Editor error", "Please select an object first.")
            return
        
        iid = self.key_list_widget.focus()
        if iid == "":
            if show_error:
                messagebox.showwarning("Editor error", "Please select a keyvalue pair.")
            return
        
        obj = self.last_objects[int(sel)]
        
        del obj.keyvalues[self.key_list_widget.item(iid)["text"]]
        self.update_keyvalues()

    def on_newkvpair_pressed(self):
        sel = self.object_list_widget.focus()
        if sel == "":
            messagebox.showwarning("Editor error", "Please select an object first.")
        else:
            obj = self.last_objects[int(sel)]
            obj.keyvalues["[new key]"] = "[new value]"
            self.update_keyvalues()
    
    def on_game_state_changed(self, event):
        self.game.state = event.widget["values"][event.widget.current()]

    def on_object_selected(self, event):
        obj = self.last_objects[int(self.object_list_widget.focus())]

        # Update the object data
        self.object_type_widget.configure(state="readonly")
        self.object_name_widget.configure(state="enabled")
        for name, klass in objects.NAME2OBJTYPE.items():
            if klass == obj.__class__:
                for i, x in enumerate(self.object_type_widget["values"]):
                    if x == name:
                        self.object_type_widget.current(i)
                        break
                break
        
        self.object_name_widget.delete(0, tk.END)
        self.object_name_widget.insert(tk.END, obj.name)
        self.update_keyvalues()

    def on_key_interacted(self, event):
        if self.object_list_widget.focus() == "":
            messagebox.showwarning("Editor error", "Please select an object first.")
        else:
            KeyvaluePopup(self, True)

    def on_value_interacted(self, event):
        if self.object_list_widget.focus() == "":
            messagebox.showwarning("Editor error", "Please select an object first.")
        else:
            KeyvaluePopup(self, False)

    def update_keyvalues(self):
        self.key_list_widget.delete(*self.key_list_widget.get_children())
        self.value_list_widget.delete(*self.value_list_widget.get_children())
        
        selection = self.object_list_widget.focus()
        if selection == "":
            return
        c = 0
        for key, value in self.last_objects[int(selection)].keyvalues.items():
            iid = "KV" + str(c)
            self.key_list_widget.insert("", tk.END, iid=iid, text=key)
            self.value_list_widget.insert("", tk.END, iid=iid, text=str(value))
            c += 1

    def update_objects(self):
        self.last_objects = tuple(self.game.objects)
        
        self.object_list_widget.delete(*self.object_list_widget.get_children())
        self.name_object_map = {}
        c = 0
        for i in self.game.objects:
            name = i.name + " (" + i.__class__.__name__ + ")"
            self.object_list_widget.insert("", tk.END, iid=str(c), text=name)
            self.name_object_map[name] = i
            c += 1

        self.update_keyvalues()

    def update(self):
        # Update the object list
        if self.game.objects != set(self.last_objects):
            self.update_objects()

        # Update the current selected state
        for i, x in enumerate(self.state_list_widget["values"]):
            if self.game.state == x:
                self.state_list_widget.current(i)
        
        # Unlock the object data if an object is selected
        if self.object_list_widget.focus() == "":
            self.object_type_widget.configure(state="disabled")
            self.object_name_widget.configure(state="disabled")
        else:
            self.object_type_widget.configure(state="readonly")
            self.object_name_widget.configure(state="enabled")

        # Update the "is music persistent" checkbox
        self.music_persistent_var.set(int(self.game.music_persistent))
        
        self.root.after(50, self.update)
        
        if not self.game.running:
            self.root.destroy()

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import os
import json
from PIL import Image, ImageTk
import win32api
import win32con
import win32ui
import win32gui

class ExeLauncher:
    def __init__(self, root):
        self.root = root
        
        # Customize window title here
        self.root.title("Emulator Launcher")
        self.root.geometry("600x500")
        
        # Set window icon if launcher_icon.ico exists
        if os.path.exists("launcher_icon.ico"):
            try:
                self.root.iconbitmap("launcher_icon.ico")
            except Exception as e:
                print(f"Could not load window icon: {e}")
        
        # Store exe data: {display_name: exe_path}
        self.exe_list = {}
        self.config_file = "launcher_config.json"
        
        # Icon cache
        self.icon_cache = {}
        
        self.setup_ui()
        self.load_config()
        
    def setup_ui(self):
        # Top frame with buttons
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill=tk.X)
        
        ttk.Button(top_frame, text="Add EXE", command=self.add_exe).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Remove Selected", command=self.remove_exe).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Rename Selected", command=self.rename_exe).pack(side=tk.LEFT, padx=5)
        
        # Main frame with canvas for scrolling
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas and scrollbar for icon list
        self.canvas = tk.Canvas(main_frame, bg="white")
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Store frame widgets for selection
        self.exe_frames = {}
        self.selected_item = None
        
        # Bottom frame with path display
        bottom_frame = ttk.Frame(self.root, padding="10")
        bottom_frame.pack(fill=tk.X)
        
        ttk.Label(bottom_frame, text="Path:").pack(side=tk.LEFT)
        self.path_label = ttk.Label(bottom_frame, text="", foreground="blue")
        self.path_label.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
    def extract_icon(self, exe_path):
        """Extract icon from EXE file"""
        if exe_path in self.icon_cache:
            return self.icon_cache[exe_path]
        
        try:
            # Get the icon from the exe
            ico_x = 32
            ico_y = 32
            
            large, small = win32gui.ExtractIconEx(exe_path, 0)
            if large:
                if small:
                    win32gui.DestroyIcon(small[0])
                
                hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
                hbmp = win32ui.CreateBitmap()
                hbmp.CreateCompatibleBitmap(hdc, ico_x, ico_y)
                hdc = hdc.CreateCompatibleDC()
                
                hdc.SelectObject(hbmp)
                hdc.DrawIcon((0, 0), large[0])
                
                # Convert to PIL Image
                bmpstr = hbmp.GetBitmapBits(True)
                img = Image.frombuffer('RGB', (ico_x, ico_y), bmpstr, 'raw', 'BGRX', 0, 1)
                
                win32gui.DestroyIcon(large[0])
                
                # Resize to 32x32 for display
                img = img.resize((32, 32), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                
                self.icon_cache[exe_path] = photo
                return photo
        except Exception as e:
            print(f"Could not extract icon from {exe_path}: {e}")
            return None
        
    def add_exe(self):
        """Add a new EXE to the launcher"""
        file_path = filedialog.askopenfilename(
            title="Select EXE file",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )
        
        if file_path:
            # Default name is the filename without extension
            default_name = os.path.splitext(os.path.basename(file_path))[0]
            
            # Check if already exists
            if file_path in self.exe_list.values():
                messagebox.showwarning("Duplicate", "This EXE is already in the launcher!")
                return
            
            # Make sure name is unique
            base_name = default_name
            counter = 1
            while default_name in self.exe_list:
                default_name = f"{base_name} ({counter})"
                counter += 1
            
            self.exe_list[default_name] = file_path
            self.refresh_display()
            self.save_config()
            
    def remove_exe(self):
        """Remove selected EXE from launcher"""
        if not self.selected_item:
            messagebox.showwarning("No Selection", "Please select an EXE to remove")
            return
        
        if messagebox.askyesno("Confirm", f"Remove '{self.selected_item}' from launcher?"):
            del self.exe_list[self.selected_item]
            self.selected_item = None
            self.refresh_display()
            self.save_config()
            
    def rename_exe(self):
        """Rename the display name of selected EXE"""
        if not self.selected_item:
            messagebox.showwarning("No Selection", "Please select an EXE to rename")
            return
        
        old_name = self.selected_item
        
        # Create dialog for new name
        dialog = tk.Toplevel(self.root)
        dialog.title("Rename")
        dialog.geometry("300x100")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="New name:").pack(pady=10)
        
        entry = ttk.Entry(dialog, width=30)
        entry.insert(0, old_name)
        entry.pack(pady=5)
        entry.select_range(0, tk.END)
        entry.focus()
        
        def do_rename():
            new_name = entry.get().strip()
            if not new_name:
                messagebox.showwarning("Invalid", "Name cannot be empty")
                return
            
            if new_name != old_name and new_name in self.exe_list:
                messagebox.showwarning("Duplicate", "This name already exists")
                return
            
            # Update the dictionary
            self.exe_list[new_name] = self.exe_list.pop(old_name)
            self.selected_item = new_name
            self.refresh_display()
            self.save_config()
            dialog.destroy()
        
        ttk.Button(dialog, text="OK", command=do_rename).pack(pady=5)
        entry.bind("<Return>", lambda e: do_rename())
        
    def launch_exe(self, display_name):
        """Launch the specified EXE"""
        exe_path = self.exe_list[display_name]
        
        if not os.path.exists(exe_path):
            messagebox.showerror("Error", f"EXE not found:\n{exe_path}")
            return
        
        try:
            subprocess.Popen(exe_path)
        except Exception as e:
            messagebox.showerror("Launch Error", f"Could not launch EXE:\n{str(e)}")
    
    def select_item(self, display_name):
        """Handle item selection"""
        # Deselect previous
        if self.selected_item and self.selected_item in self.exe_frames:
            frame = self.exe_frames[self.selected_item]
            frame.configure(bg="white")
            for widget in frame.winfo_children():
                if isinstance(widget, tk.Label):
                    widget.configure(bg="white")
        
        # Select new
        self.selected_item = display_name
        if display_name in self.exe_frames:
            frame = self.exe_frames[display_name]
            frame.configure(bg="lightblue")
            for widget in frame.winfo_children():
                if isinstance(widget, tk.Label):
                    widget.configure(bg="lightblue")
        
        # Update path display
        self.path_label.config(text=self.exe_list[display_name])
            
    def refresh_display(self):
        """Refresh the display with current EXE list"""
        # Clear existing frames
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.exe_frames.clear()
        
        # Create frames for each EXE
        for display_name in sorted(self.exe_list.keys()):
            exe_path = self.exe_list[display_name]
            
            # Create frame for this item
            item_frame = tk.Frame(self.scrollable_frame, bg="white", relief=tk.FLAT, 
                                 borderwidth=1, highlightthickness=1, highlightbackground="gray")
            item_frame.pack(fill=tk.X, padx=5, pady=2)
            
            # Extract and display icon
            icon = self.extract_icon(exe_path)
            if icon:
                icon_label = tk.Label(item_frame, image=icon, bg="white")
                icon_label.image = icon  # Keep a reference
                icon_label.pack(side=tk.LEFT, padx=5, pady=5)
            
            # Display name
            name_label = tk.Label(item_frame, text=display_name, bg="white", 
                                 font=("Arial", 10), anchor="w")
            name_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            
            # Store frame reference
            self.exe_frames[display_name] = item_frame
            
            # Bind click events
            def make_select_handler(name):
                return lambda e: self.select_item(name)
            
            def make_launch_handler(name):
                return lambda e: self.launch_exe(name)
            
            for widget in [item_frame, name_label]:
                widget.bind("<Button-1>", make_select_handler(display_name))
                widget.bind("<Double-Button-1>", make_launch_handler(display_name))
            
            if icon:
                icon_label.bind("<Button-1>", make_select_handler(display_name))
                icon_label.bind("<Double-Button-1>", make_launch_handler(display_name))
        
        # Restore selection if still valid
        if self.selected_item and self.selected_item in self.exe_frames:
            self.exe_frames[self.selected_item].configure(bg="lightblue")
            for widget in self.exe_frames[self.selected_item].winfo_children():
                if isinstance(widget, tk.Label):
                    widget.configure(bg="lightblue")
            self.path_label.config(text=self.exe_list[self.selected_item])
        else:
            self.selected_item = None
            self.path_label.config(text="")
            
    def save_config(self):
        """Save the EXE list to a config file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.exe_list, f, indent=2)
        except Exception as e:
            print(f"Could not save config: {e}")
            
    def load_config(self):
        """Load the EXE list from config file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.exe_list = json.load(f)
                self.refresh_display()
        except Exception as e:
            print(f"Could not load config: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ExeLauncher(root)
    root.mainloop()
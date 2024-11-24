import arcpy
import json
import os
import csv
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
import webbrowser
from tkinter import ttk


def validate_feature_class(fc):
    """Validate the existence of the feature class."""
    if not arcpy.Exists(fc):
        messagebox.showerror("Error", f"Feature class '{fc}' does not exist.")
        return False
    return True


def serialize_feature(feature):
    """Serialize feature properties, converting non-JSON serializable objects (like datetime) to strings."""
    for key, value in feature.items():
        if isinstance(value, datetime):  # Check for datetime objects
            feature[key] = value.isoformat()  # Convert datetime to ISO 8601 string
    return feature


def export_feature_class(fc_path, fc_name, export_type, output_dir, custom_filename=None):
    """Export the feature class to the specified format (csv, json, geojson)."""
    full_fc_path = os.path.join(fc_path, fc_name)
    if not validate_feature_class(full_fc_path):
        return

    if not custom_filename:
        custom_filename = f"{fc_name.replace('.', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    output_file = os.path.join(output_dir, f"{custom_filename}.{export_type}")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    fields = [field.name for field in arcpy.ListFields(full_fc_path)] + ["SHAPE@"]

    features = []

    try:
        status_var.set("Export in Progress...")
        root.update_idletasks()  # Update the UI while processing
        with arcpy.da.SearchCursor(full_fc_path, fields) as cursor:
            for row in cursor:
                feature = {field: value for field, value in zip(fields[:-1], row[:-1])}
                geometry = row[-1]
                if geometry:
                    geometry = geometry.projectAs(arcpy.SpatialReference(4326)).__geo_interface__
                feature["geometry"] = geometry
                features.append(serialize_feature(feature))

        if not features:
            messagebox.showinfo("Info", "The feature class has no data to export.")
            status_var.set("No data to export.")
            return

        if export_type == 'geojson':
            geojson_output = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": feature["geometry"],
                        "properties": {key: feature[key] for key in feature if key != "geometry"}
                    }
                    for feature in features
                ]
            }
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(geojson_output, f, ensure_ascii=False, indent=4)

        elif export_type == 'json':
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(features, f, ensure_ascii=False, indent=4)

        elif export_type == 'csv':
            with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=features[0].keys())
                writer.writeheader()
                for feature in features:
                    writer.writerow(feature)

        status_var.set(f"Export successful: {export_type.upper()} saved to {output_file}")
        messagebox.showinfo("Success", f"Feature class exported to {export_type.upper()}:\n{output_file}")

        open_link = tk.Label(root, text="Click here to open the folder", fg="blue", cursor="hand2", bg="white")
        open_link.grid(row=9, column=0, columnspan=3, pady=5)
        open_link.bind("<Button-1>", lambda e: webbrowser.open(f'file:///{output_dir}'))

    except arcpy.ExecuteError as e:
        messagebox.showerror("ArcPy Error", f"ArcPy error occurred: {e}")
        status_var.set(f"Error: {e}")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
        status_var.set(f"Error: {e}")


def browse_fc_path():
    """Open a file dialog to select a .gdb folder or .sde file."""
    fc_type = fc_type_var.get()
    if fc_type == ".gdb":
        folder_path = filedialog.askdirectory(title="Select Geodatabase (.gdb) Folder")
        if folder_path:
            fc_path_var.set(folder_path)
    elif fc_type == ".sde":
        file_path = filedialog.askopenfilename(
            title="Select SDE Connection File",
            filetypes=[("SDE Files", "*.sde")]
        )
        if file_path:
            fc_path_var.set(file_path)
    update_filename()


def browse_output_dir():
    """Open a directory dialog to select the output folder."""
    dir_path = filedialog.askdirectory(title="Select Output Directory")
    if dir_path:
        output_dir_var.set(dir_path)


def update_filename(*args):
    """Update the prepopulated output file name."""
    fc_name = fc_name_var.get()
    if fc_name:
        custom_filename_var.set(f"{fc_name.replace('.', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    else:
        custom_filename_var.set(f"FC_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        



# GUI Colors
bg_color = "white"
input_bg_color = "#f0f0f0"  # Lightest grey

# Initialize GUI
root = tk.Tk()
root.title("Feature Class Export Tool")
root.configure(bg=bg_color)
root.geometry("600x400")
root.resizable(True, True)

# Variables
fc_type_var = tk.StringVar(value=".sde")
fc_path_var = tk.StringVar(value="")
fc_name_var = tk.StringVar(value="")
output_dir_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Downloads"))
custom_filename_var = tk.StringVar()
export_type_var = tk.StringVar(value="csv")
status_var = tk.StringVar(value="Ready")

fc_name_var.trace_add("write", update_filename)

# UI Components
tk.Label(root, text="Connection Type:", bg=bg_color).grid(row=0, column=0, sticky="w", padx=10, pady=5)
ttk.Combobox(root, textvariable=fc_type_var, values=[".sde", ".gdb"], width=37).grid(row=0, column=1, padx=10, pady=5, sticky="we")

tk.Label(root, text="FC Path:", bg=bg_color).grid(row=1, column=0, sticky="w", padx=10, pady=5)
tk.Entry(root, textvariable=fc_path_var, bg=input_bg_color, relief="flat").grid(row=1, column=1, padx=10, pady=5, sticky="we")
tk.Button(root, text="Browse", command=browse_fc_path).grid(row=1, column=2, padx=5, pady=5, sticky="e")

tk.Label(root, text="FC Name:", bg=bg_color).grid(row=2, column=0, sticky="w", padx=10, pady=5)
tk.Entry(root, textvariable=fc_name_var, bg=input_bg_color, relief="flat").grid(row=2, column=1, padx=10, pady=5, sticky="we")

tk.Label(root, text="Output Folder:", bg=bg_color).grid(row=3, column=0, sticky="w", padx=10, pady=5)
tk.Entry(root, textvariable=output_dir_var, bg=input_bg_color, relief="flat").grid(row=3, column=1, padx=10, pady=5, sticky="we")
tk.Button(root, text="Browse", command=browse_output_dir).grid(row=3, column=2, padx=5, pady=5, sticky="e")

tk.Label(root, text="Output File Name:", bg=bg_color).grid(row=4, column=0, sticky="w", padx=10, pady=5)
tk.Entry(root, textvariable=custom_filename_var, bg=input_bg_color, relief="flat").grid(row=4, column=1, padx=10, pady=5, sticky="we")

tk.Label(root, text="Export Type:", bg=bg_color).grid(row=5, column=0, sticky="w", padx=10, pady=5)
ttk.Combobox(root, textvariable=export_type_var, values=["csv", "json", "geojson"], width=37).grid(row=5, column=1, padx=10, pady=5, sticky="we")

tk.Button(root, text="Export", bg="#2196f3", fg="white", relief="flat",
          command=lambda: export_feature_class(fc_path_var.get(), fc_name_var.get(),
                                               export_type_var.get(), output_dir_var.get(),
                                               custom_filename_var.get())).grid(row=6, column=0, columnspan=3, pady=10)

tk.Label(root, textvariable=status_var, bg=bg_color, fg="green").grid(row=7, column=0, columnspan=3, pady=5)

tk.Label(root, text="Developed by: Rana Muhammad Rameez\nEmail: mrameezrana99@gmail.com", bg=bg_color,
         fg="gray", font=("Arial", 8)).grid(row=8, column=0, columnspan=3, pady=10)

# Call update_filename to initialize the filename on startup
update_filename()

root.mainloop()

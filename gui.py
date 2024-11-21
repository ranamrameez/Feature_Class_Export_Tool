import arcpy
import json
import os
import csv
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
import webbrowser
import os.path

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

    # If no custom filename, generate a default one
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
                features.append(serialize_feature(feature))  # Serialize feature properties

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
            # Writing CSV with BOM for UTF-8 encoding
            with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=features[0].keys())
                writer.writeheader()
                for feature in features:
                    writer.writerow(feature)

        # Update status and show success message with file/folder link
        status_var.set(f"Export successful: {export_type.upper()} saved to {output_file}")
        messagebox.showinfo("Success", f"Feature class exported to {export_type.upper()}:\n{output_file}")
        
        # Provide a clickable link to open the file/folder
        open_link = tk.Label(root, text="Click here to open the folder", fg="blue", cursor="hand2")
        open_link.grid(row=8, column=0, columnspan=3, pady=5)
        open_link.bind("<Button-1>", lambda e: open_export_folder(output_dir))

    except arcpy.ExecuteError as e:
        messagebox.showerror("ArcPy Error", f"ArcPy error occurred: {e}")
        status_var.set(f"Error: {e}")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
        status_var.set(f"Error: {e}")

def open_export_folder(folder_path):
    """Open the folder containing the exported file."""
    webbrowser.open(f'file:///{folder_path}')

def browse_output_dir():
    """Open a directory dialog to select the output folder."""
    dir_path = filedialog.askdirectory(title="Select Output Directory")
    output_dir_var.set(dir_path)

def generate_dynamic_filename():
    """Generate a dynamic file name based on the Feature Class Path and Name."""
    fc_name = fc_name_var.get()
    return f"{fc_name.replace('.', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Initialize GUI
root = tk.Tk()
root.title("Feature Class Export Tool")
root.geometry("500x500")  # Adjusted window height

# Default output directory set to Downloads folder
downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
output_dir_var = tk.StringVar(value=downloads_folder)  # Default to Downloads directory

# Variables
fc_path_var = tk.StringVar(value=r"D:\ArcPro Projects\Explore_GIS_Data\ExploreGISDatasets\Oracle-AGENPRD-AGENPRD(topopublic).sde\\")
fc_name_var = tk.StringVar(value="TOPO.QatarLandmark")
custom_filename_var = tk.StringVar(value=generate_dynamic_filename())  # Prepopulate with dynamic filename
export_type_var = tk.StringVar(value="csv")
status_var = tk.StringVar(value="Ready")

# Tooltips
def show_tooltip(event, text):
    tooltip = tk.Label(root, text=text, relief="solid", bg="lightyellow", font=("Arial", 8))
    tooltip.place(x=event.x + 10, y=event.y + 20)
    def on_leave(event):
        tooltip.destroy()
    event.widget.bind("<Leave>", on_leave)

# Labels and Inputs
tk.Label(root, text="Feature Class Path:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
fc_path_entry = tk.Entry(root, textvariable=fc_path_var, width=45)
fc_path_entry.grid(row=0, column=1, padx=10, pady=10)
fc_path_entry.bind("<Enter>", lambda e: show_tooltip(e, "Path to the SDE connection for the feature class"))

tk.Label(root, text="Feature Class Name:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
fc_name_entry = tk.Entry(root, textvariable=fc_name_var, width=45)
fc_name_entry.grid(row=1, column=1, padx=10, pady=10)
fc_name_entry.bind("<Enter>", lambda e: show_tooltip(e, "The name of the feature class to export"))

tk.Label(root, text="Output Directory:").grid(row=2, column=0, padx=10, pady=10, sticky="e")
output_dir_entry = tk.Entry(root, textvariable=output_dir_var, width=45)
output_dir_entry.grid(row=2, column=1, padx=10, pady=10)
output_dir_entry.bind("<Enter>", lambda e: show_tooltip(e, "Select the directory where the output file will be saved"))
tk.Button(root, text="Browse", command=browse_output_dir).grid(row=2, column=2, padx=10, pady=10)

tk.Label(root, text="Output File Name:").grid(row=3, column=0, padx=10, pady=10, sticky="e")
output_file_entry = tk.Entry(root, textvariable=custom_filename_var, width=45)
output_file_entry.grid(row=3, column=1, padx=10, pady=10)
output_file_entry.bind("<Enter>", lambda e: show_tooltip(e, "Optional custom file name for the output"))

tk.Label(root, text="Export Format:").grid(row=4, column=0, padx=10, pady=10, sticky="e")
tk.OptionMenu(root, export_type_var, "csv", "json", "geojson").grid(row=4, column=1, padx=10, pady=10)

tk.Label(root, text="Status:").grid(row=5, column=0, padx=10, pady=10, sticky="e")
status_label = tk.Label(root, textvariable=status_var, width=40, anchor="w")
status_label.grid(row=5, column=1, padx=10, pady=10, columnspan=2)

# Export Button
export_button = tk.Button(root, text="Export", command=lambda: export_feature_class(
    fc_path_var.get(),
    fc_name_var.get(),
    export_type_var.get(),
    output_dir_var.get(),
    custom_filename_var.get()))
export_button.grid(row=6, column=0, columnspan=3, pady=20)

# Credit Label
credit_label = tk.Label(root, text="Created by Rana Muhammad Rameez | Email: mrameezrana99@gmail.com", font=("Arial", 8), fg="gray")
credit_label.grid(row=9, column=0, columnspan=3, pady=5)

root.mainloop()

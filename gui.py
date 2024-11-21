import arcpy
import json
import os
import csv
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox

def validate_feature_class(fc):
    """
    Validate the existence of the feature class.
    """
    if not arcpy.Exists(fc):
        messagebox.showerror("Error", f"Feature class '{fc}' does not exist.")
        return False
    return True

def serialize_feature(feature):
    """
    Serialize feature properties, converting non-JSON serializable objects (like datetime) to strings.
    """
    for key, value in feature.items():
        if isinstance(value, datetime):  # Check for datetime objects
            feature[key] = value.isoformat()  # Convert datetime to ISO 8601 string
    return feature

def export_feature_class(fc_path, fc_name, export_type, output_dir, custom_filename=None):
    """
    Export the feature class to the specified format (csv, json, geojson).
    """
    full_fc_path = os.path.join(fc_path, fc_name)
    if not validate_feature_class(full_fc_path):
        return

    # If no custom filename, generate a default one
    if not custom_filename:
        custom_filename = f"feature_class_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    output_file = os.path.join(output_dir, f"{custom_filename}.{export_type}")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    fields = [field.name for field in arcpy.ListFields(full_fc_path)] + ["SHAPE@"]

    features = []

    try:
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

        messagebox.showinfo("Success", f"Feature class exported to {export_type.upper()}:\n{output_file}")

    except arcpy.ExecuteError as e:
        messagebox.showerror("ArcPy Error", f"ArcPy error occurred: {e}")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

def browse_output_dir():
    """
    Open a directory dialog to select the output folder.
    """
    dir_path = filedialog.askdirectory(title="Select Output Directory")
    output_dir_var.set(dir_path)

def start_export():
    """
    Start the export process based on the GUI inputs.
    """
    fc_path = fc_path_var.get()
    fc_name = fc_name_var.get()
    output_dir = output_dir_var.get()
    export_type = export_type_var.get()
    custom_filename = custom_filename_var.get()

    if not fc_path or not fc_name or not output_dir or not export_type:
        messagebox.showerror("Error", "All fields must be filled in.")
        return

    export_feature_class(fc_path, fc_name, export_type, output_dir, custom_filename)

# Create the GUI
root = tk.Tk()
root.title("Feature Class Export Tool")
root.geometry("500x400")

# Variables
fc_path_var = tk.StringVar(value=r"D:\ArcPro Projects\Explore_GIS_Data\ExploreGISDatasets\Oracle-AGENPRD-AGENPRD(topopublic).sde\\")
fc_name_var = tk.StringVar(value="TOPO.QatarLandmark")
output_dir_var = tk.StringVar()
export_type_var = tk.StringVar(value="csv")
custom_filename_var = tk.StringVar()

# Labels and Inputs
tk.Label(root, text="Feature Class Path:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
tk.Entry(root, textvariable=fc_path_var, width=40).grid(row=0, column=1, padx=10, pady=10)

tk.Label(root, text="Feature Class Name:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
tk.Entry(root, textvariable=fc_name_var, width=40).grid(row=1, column=1, padx=10, pady=10)

tk.Label(root, text="Output Directory:").grid(row=2, column=0, padx=10, pady=10, sticky="e")
tk.Entry(root, textvariable=output_dir_var, width=40).grid(row=2, column=1, padx=10, pady=10)
tk.Button(root, text="Browse", command=browse_output_dir).grid(row=2, column=2, padx=10, pady=10)

tk.Label(root, text="Export Format:").grid(row=3, column=0, padx=10, pady=10, sticky="e")
tk.OptionMenu(root, export_type_var, "csv", "json", "geojson").grid(row=3, column=1, padx=10, pady=10, sticky="w")

tk.Label(root, text="Custom File Name (Optional):").grid(row=4, column=0, padx=10, pady=10, sticky="e")
tk.Entry(root, textvariable=custom_filename_var, width=40).grid(row=4, column=1, padx=10, pady=10)

# Export Button
tk.Button(root, text="Export", command=start_export, bg="green", fg="white", width=15).grid(row=5, column=1, pady=20)

# Run the GUI
root.mainloop()

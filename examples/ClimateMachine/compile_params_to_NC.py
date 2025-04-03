import os
import re
import argparse
import numpy as np
import xarray as xr

def extract_parameters_from_file(filepath):
    """Extracts parameters and their values from a Julia file."""
    parameters = {}
    with open(filepath, 'r') as file:
        content = file.read()
    
    # Regex to match parameter name and value
    matches = re.findall(r'([A-Za-z0-9_]+)\(::EarthParameterSet\) =\s+([0-9\.eE\-]+)', content)
    
    for param, value in matches:
        parameters[param] = float(value)
    
    return parameters

def get_unique_filename(base_filename):
    """Generates a unique filename by appending _000, _001, etc., if the file already exists."""
    if not os.path.exists(base_filename):
        return base_filename
    
    index = 0
    while True:
        new_filename = f"{base_filename.rsplit('.', 1)[0]}_{index:03d}.nc"
        if not os.path.exists(new_filename):
            return new_filename
        index += 1

def compile_to_netcdf(directory, output_filename, file_prefix):
    """Reads all Julia parameter files, extracts parameters, and saves to NetCDF."""
    files = [f for f in os.listdir(directory) if f.startswith(file_prefix) and f.endswith(".jl")]
    files.sort()  # Sort to maintain order
    
    all_params = {}
    file_ids = list(range(len(files)))  # Incremented index for file dimension
    
    for i, file in enumerate(files):
        file_path = os.path.join(directory, file)
        params = extract_parameters_from_file(file_path)
        
        for param, value in params.items():
            if param not in all_params:
                all_params[param] = []
            all_params[param].append(value)
    
    # Convert to xarray dataset
    num_files = len(file_ids)
    param_names = list(all_params.keys())
    
    # Ensure all parameters have the same length
    for param in param_names:
        if len(all_params[param]) < num_files:
            all_params[param].extend([np.nan] * (num_files - len(all_params[param])))
    
    sample_nmb = np.array([f"{i:03d}" for i in range(num_files)], dtype="<U3")
    data_vars = {param: ("nmb_sim", all_params[param]) for param in param_names}
    data_vars["Sample_nmb"] = ("nmb_sim", sample_nmb)
    
    ds = xr.Dataset(
        data_vars,
        coords={"nmb_sim": file_ids}
    )
    
    # Get a unique filename
    unique_filename = get_unique_filename(output_filename)
    
    # Save to NetCDF
    ds.to_netcdf(unique_filename)
    print(f"Saved to {unique_filename}")

def main():
    parser = argparse.ArgumentParser(description="Extract Julia parameter files and compile into NetCDF.")
    parser.add_argument("-d", "--directory", type=str, required=True, help="Directory containing Julia parameter files")
    parser.add_argument("-o", "--output", type=str, required=True, help="Output NetCDF file")
    parser.add_argument("-p", "--prefix", type=str, default="clima_param_defs_", help="Prefix of Julia parameter files")
    args = parser.parse_args()
    
    compile_to_netcdf(args.directory, args.output, args.prefix)

if __name__ == "__main__":
    # Example usage:
    # python script.py -d ./julia_files -o clima_parameters.nc -p clima_param_defs_
    main()

import os
import subprocess
from tqdm import tqdm  # Import tqdm

# Paths
base_input_dir = r'stimuli\Scenes_corrected'
base_output_dir = r'mp4\stimuli\Scenes_corrected'

# Function to convert .avi to .mp4
def convert_avi_to_mp4(input_file, output_file):
    command = ['ffmpeg', '-i', input_file, output_file]
    with open(os.devnull, 'wb') as devnull:
        subprocess.run(command, stdout=devnull, stderr=devnull, check=True)

# List of all .avi files to be converted
avi_files = []

# Iterate through all subdirectories and collect .avi files
for root, dirs, files in os.walk(base_input_dir):
    # Determine the subfolder path
    subfolder = os.path.relpath(root, base_input_dir)
    output_subfolder = os.path.join(base_output_dir, subfolder)
    
    # Create the output directory if it doesn't exist
    if not os.path.exists(output_subfolder):
        os.makedirs(output_subfolder)
    
    # Collect all .avi files
    for file_name in files:
        if file_name.endswith('.avi'):
            # Construct the output file path
            output_file = os.path.join(output_subfolder, file_name.replace('.avi', '.mp4'))
            
            # Only add files that need conversion
            if not os.path.exists(output_file):
                avi_files.append({
                    'input': os.path.join(root, file_name),
                    'output': output_file
                })

# Convert .avi files to .mp4 with progress bar
for avi_file in tqdm(avi_files, desc="Converting files"):
    print(f"Converting {avi_file['input']} to {avi_file['output']}")
    convert_avi_to_mp4(avi_file['input'], avi_file['output'])

print("Conversion completed.")

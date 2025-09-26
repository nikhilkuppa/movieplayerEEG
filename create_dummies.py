import cv2
import numpy as np
import os
import math

# --- Configuration ---
# This matches the folder structure mentioned in your README and app.py
BASE_INPUT_DIR = 'stimuli/Scenes_corrected' 
MOVIE_TITLE = 'The_Big_Sick'
OUTPUT_DIR = os.path.join(BASE_INPUT_DIR, MOVIE_TITLE)

# Video parameters for the dummy files
WIDTH, HEIGHT = 640, 480
FPS = 30

# Scene data from your T_scene_combined.xlsx screenshot for "The Big Sick"
# stimuli_id = 1
scenes_to_create = [
    {'scene_no': 1, 'duration': 41.3998344},
    {'scene_no': 2, 'duration': 55.249779}
    # Add more scenes here if needed
]

def create_dummy_video(movie_name, scene_number, duration_seconds):
    """Generates a dummy AVI video file with text overlay."""
    
    # Ensure the output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Format filename exactly as the frontend/backend expects
    # e.g., The_Big_Sick_scene_01_tc.avi
    scene_str = str(scene_number).zfill(2)
    filename = f"{movie_name}_scene_{scene_str}_tc.avi"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    # Define the codec and create VideoWriter object
    # DIVX is a common codec for .avi files
    fourcc = cv2.VideoWriter_fourcc(*'DIVX')
    out = cv2.VideoWriter(filepath, fourcc, FPS, (WIDTH, HEIGHT))
    
    total_frames = math.ceil(duration_seconds * FPS)
    
    print(f"Creating scene {scene_str}: '{filename}' ({duration_seconds:.2f}s, {total_frames} frames)...")

    for i in range(total_frames):
        # Create a black frame
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        
        # Add informative text to the frame
        font = cv2.FONT_HERSHEY_SIMPLEX
        text1 = f"{movie_name.replace('_', ' ')}"
        text2 = f"Scene: {scene_str}"
        text3 = f"Duration: {duration_seconds:.2f}s"
        
        cv2.putText(frame, text1, (50, 50), font, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, text2, (50, 100), font, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, text3, (50, 150), font, 1, (255, 255, 255), 2, cv2.LINE_AA)
        
        # Write the frame to the video file
        out.write(frame)
        
    # Release everything when job is finished
    out.release()
    print(f"✅ Finished: {filename}")

# --- Main execution ---
if __name__ == "__main__":
    print(f"Starting dummy video generation for '{MOVIE_TITLE}'...")
    for scene in scenes_to_create:
        create_dummy_video(
            movie_name=MOVIE_TITLE,
            scene_number=scene['scene_no'],
            duration_seconds=scene['duration']
        )
    print("\nAll dummy AVI files created successfully.")
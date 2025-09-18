import numpy as np
import cv2
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

# Global variable to store the x-coordinate of the clicked point
clicked_x = None

def on_click(event):
    global clicked_x
    if event.inaxes is not None:
        clicked_x = event.xdata
        print(f"Clicked at x={clicked_x}")

def create_time_series_plot(eeg_data):
    # Create a plot
    fig, ax = plt.subplots(figsize=(8, 3))  # Adjust the figsize as needed
    ax.plot(eeg_data.index, eeg_data.values)
    ax.set_title('ISC_EEG Time Series')
    ax.set_xlabel('Time (index)')
    ax.set_ylabel('ISC_EEG Value')

    # Connect the click event handler to the figure
    fig.canvas.mpl_connect('button_press_event', on_click)

    # Save the plot to a file
    canvas = FigureCanvas(fig)
    canvas.draw()
    img = np.frombuffer(canvas.tostring_rgb(), dtype=np.uint8)
    img = img.reshape(canvas.get_width_height()[::-1] + (3,))

    return img  # Return the image

# Load the CSV file and extract the ISC_EEG column
df = pd.read_excel('C:\\nikhilkuppa\\movie_player_project\\T_scene_combined.xlsx')
eeg_data = df['ISC_EEG']  # Replace 'ISC_EEG' with the actual column name if different

# Create the time series plot
plot_img = create_time_series_plot(eeg_data)

# Open the video file for capturing frames
cap = cv2.VideoCapture('stimuli/Scenes_corrected/Whiplash/Whiplash_scene_11_tc.avi')

# Get the video properties
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)

# Loop through the video frames
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Display the combined image
    cv2.imshow('Video with Time Series Plot', frame)

    # Check if the user pressed 'q' to quit
    if cv2.waitKey(int(1000 / fps)) & 0xFF == ord('q'):
        break

    # Example: Use the clicked point to jump to a specific frame in the video
    if clicked_x is not None:
        # Assuming the x-axis in the plot corresponds to the video time in seconds
        # target_time = clicked_x
        # target_frame = int(target_time * fps)
        # cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        clicked_x = None  # Reset after handling the click

    # Process pending matplotlib events (to ensure click events are handled)
    plt.pause(0.00001)

# Release the video capture object
cap.release()

# Close all OpenCV windows
cv2.destroyAllWindows()

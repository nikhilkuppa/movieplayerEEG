import numpy as np
import pandas as pd
import cv2
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.widgets import Slider, Button
import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

# Global variables
clicked_x = None
frame_duration = None
fps = None
scene_index = 0
cap = None
dot = None  # To store the dot artist
current_scene_start = None  # To keep track of the current scene start time
current_scene_isc_eeg = None  # To keep track of the current scene ISC_EEG value

def on_click(event):
    global clicked_x
    if event.inaxes is not None:
        clicked_x = event.xdata
        print(f"Clicked at x={clicked_x}")  # Debugging line to check if click is registered

def toggle_fullscreen(event=None):
    global is_fullscreen
    is_fullscreen = not is_fullscreen
    root.attributes("-fullscreen", is_fullscreen)
    root.bind("<Escape>", end_fullscreen)  # Bind Esc key to exit fullscreen

def end_fullscreen(event=None):
    global is_fullscreen
    is_fullscreen = False
    root.attributes("-fullscreen", False)
    root.bind("<F11>", toggle_fullscreen)  # Bind F11 key to enter fullscreen

def reset_plot():
    global ax, reset_df
    ax.set_xlim(reset_df['scene_start'].min(), reset_df['scene_end'].max())
    ax.set_ylim(reset_df['ISC_EEG'].min() - 0.05, reset_df['ISC_EEG'].max() + 0.05)
    fig.canvas.draw()

def plot_signal_and_video(window_width=1500, interval=5, df=None, stim_title=None):
    global clicked_x, scene_index, cap, frame_duration, fps, dot, current_scene_start, current_scene_isc_eeg, is_fullscreen, reset_df

    reset_df = df.copy()

    video_dir = f'stimuli\\Scenes_corrected\\{stim_title}'

    if df is None or stim_title is None or video_dir is None:
        raise ValueError("DataFrame, stimulus title, and video directory must be provided")

    # Initialize Tkinter window
    global root
    root = tk.Tk()
    root.title("OpenCV and Matplotlib Integration")

    # Initialize fullscreen mode
    is_fullscreen = False
    root.bind("<F11>", toggle_fullscreen)  # Bind F11 key to toggle fullscreen

    # Set background color to black
    root.configure(bg='black')

    # Create frames for layout
    main_frame = ttk.Frame(root, style="MainFrame.TFrame")
    main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    top_frame = ttk.Frame(main_frame, style="TopFrame.TFrame")
    top_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    bottom_frame = ttk.Frame(main_frame, style="BottomFrame.TFrame")
    bottom_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

    # Create a frame for video and metadata
    video_frame = ttk.Frame(top_frame, style="VideoFrame.TFrame")
    video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    metadata_frame = ttk.Frame(top_frame)
    metadata_frame.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.Y, expand=True)

    # Create a label widget for displaying OpenCV frames
    opencv_label = ttk.Label(video_frame, background='black')
    opencv_label.pack(fill=tk.BOTH, expand=True)  # Make label expand to fill frame

    # Create a canvas for the plot with scrollbar
    plot_canvas_frame = ttk.Frame(bottom_frame)
    plot_canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Create a canvas and a scrollbar
    plot_canvas = tk.Canvas(plot_canvas_frame)
    plot_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar = ttk.Scrollbar(plot_canvas_frame, orient="horizontal", command=plot_canvas.xview)
    scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

    # Create a frame inside the canvas to hold the plot
    plot_frame = ttk.Frame(plot_canvas)
    plot_canvas.create_window((0, 0), window=plot_frame, anchor="nw")

    # Set up the Matplotlib plot with black background
    global fig, ax
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor('black')
    ax.set_facecolor('black')
    ax.tick_params(axis='both', colors='white')  # Set tick color to white

    def draw_bars():
        global dot  # Use global dot
        ax.clear()
        for _, row in df.iterrows():
            ax.bar(row['scene_start'], row['ISC_EEG'], width=row['scene_duration'],
                   align='edge', edgecolor='white', color='skyblue')

            y_pos = row['ISC_EEG']
            x_pos = row['scene_start'] + row['scene_duration'] / 2

            if y_pos < 0:
                ax.text(x_pos, y_pos - 0.01, str(int(row['scene_no'])),
                        ha='center', va='top', fontsize=9, color='white')
            else:
                ax.text(x_pos, y_pos + 0.01, str(int(row['scene_no'])),
                        ha='center', va='bottom', fontsize=9, color='white')

        ax.set_xlabel('Time (seconds)', color='white')
        ax.set_ylabel('ISC_EEG', color='white')

        # Initialize the moving dot
        dot = ax.plot([], [], marker='o', markersize=8, color='red', zorder=5)[0]

    draw_bars()  # Draw the initial plot

    # Create the Matplotlib canvas and add it to the Tkinter frame
    canvas = FigureCanvasTkAgg(fig, master=plot_frame)
    canvas.mpl_connect('button_press_event', on_click)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # Update scrollbar region
    def on_canvas_configure(event):
        plot_canvas.configure(scrollregion=plot_canvas.bbox("all"))

    plot_canvas_frame.bind("<Configure>", on_canvas_configure)

    def update_plot():
        global clicked_x, scene_index, cap, frame_duration, fps, dot, current_scene_start, current_scene_isc_eeg

        video_files = sorted([f for f in os.listdir(video_dir) if f.endswith('.avi')])

        if cap is None or not cap.isOpened():
            if scene_index >= len(video_files):
                return  # No more scenes, stop updating
            video_path = os.path.join(video_dir, video_files[scene_index])
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                print(f"Error opening video file: {video_path}")
                return
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_duration = 1000 / (fps*2)
            print(f"Starting video: {video_path} with FPS: {fps}")

            # Update the dot to the start of the new scene
            current_scene_start = df.iloc[scene_index]['scene_start']
            current_scene_isc_eeg = df.iloc[scene_index]['ISC_EEG']
            dot.set_data([current_scene_start], [current_scene_isc_eeg])

        ret, frame = cap.read()
        if not ret:
            scene_index += 1  # Move to the next scene when the video ends
            if scene_index >= len(video_files):
                return  # No more scenes to play
            current_scene_start = df.iloc[scene_index]['scene_start']
            current_scene_isc_eeg = df.iloc[scene_index]['ISC_EEG']
            dot.set_data([current_scene_start], [current_scene_isc_eeg])

            cap.release()
            cap = None
            root.after(0, update_plot)  # Continue updating after releasing the video
            return

        # Convert the frame to a format suitable for Tkinter display
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(frame_rgb)
        imgtk = ImageTk.PhotoImage(image=img_pil)

        # Update the label widget with the new frame
        opencv_label.imgtk = imgtk
        opencv_label.configure(image=imgtk)

        # Handle click events to jump to specific scenes
        if clicked_x is not None:
            target_time = clicked_x
            scene_row = df[(df['scene_start'] <= target_time) & (df['scene_end'] >= target_time)]
            if not scene_row.empty:
                scene_no = scene_row['scene_no'].values[0]
                new_scene_file = f'{stim_title}_scene_{str(scene_no).zfill(2)}_tc.avi'
                if new_scene_file in video_files:
                    scene_index = video_files.index(new_scene_file)
                    current_scene_start = df.iloc[scene_index]['scene_start']
                    current_scene_isc_eeg = df.iloc[scene_index]['ISC_EEG']
                    dot.set_data([current_scene_start], [current_scene_isc_eeg])
                clicked_x = None

        # Update the dot position and redraw the plot
        if dot:
            current_pos = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000  # Current position in seconds
            dot.set_data([current_pos], [current_scene_isc_eeg])
            ax.set_xlim(current_pos - window_width / 2, current_pos + window_width / 2)
            canvas.draw()

        root.after(int(frame_duration), update_plot)  # Continue updating at the next frame

    # Start video playback and plot update
    root.after(0, update_plot)

    # Create reset button
    reset_button = tk.Button(bottom_frame, text="Reset", command=reset_plot, background='gray', foreground='white')
    reset_button.pack(side=tk.BOTTOM, pady=5)

    # Run the Tkinter main loop
    root.mainloop()


# Load movie and scene information
movie_info = pd.read_excel(r'C:\nikhilkuppa\movie_player_project\T_movie_information.xlsx')
movie_info = movie_info[['stimuli_title', 'stimuli_id']]
print("\n ", movie_info.to_string(index=False))
stim_id = 3
# int(input('\nChoose a Stimuli ID from the above to analyze the ISC_EEG to that Stimulus:\n'))
stim_title = movie_info[movie_info['stimuli_id'] == stim_id]['stimuli_title'].values[0]
scenes_info_df = pd.read_excel(r'C:\nikhilkuppa\movie_player_project\T_scene_combined.xlsx')
stimuli_scenes = scenes_info_df[scenes_info_df['stimuli_id'] == stim_id]
stimuli_scenes_filt = stimuli_scenes[['scene_no', 'scene_start', 'scene_end', 'scene_duration', 'ISC_EEG']]

scenes_dir = f'stimuli\\Scenes_corrected\\{stim_title}'

# Call the function to plot signal and video
plot_signal_and_video(df=stimuli_scenes_filt, stim_title=stim_title)

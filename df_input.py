import numpy as np
import pandas as pd
import cv2
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, messagebox
import os

class InitialScreen:
    def __init__(self, root):
        self.root = root
        self.root.title("Select Stimulus")
        self.root.configure(bg='black')
        self.setup_ui()
        self.root.mainloop()

    def setup_ui(self):
        # Load movie information
        self.movie_info = pd.read_excel(r'C:\nikhilkuppa\movie_player_project\T_movie_information.xlsx')
        self.movie_info = self.movie_info[['stimuli_title', 'stimuli_id']]

        # Display movie information in a table
        table_frame = tk.Frame(self.root, bg='black')
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        heading_label = tk.Label(table_frame, text="Available Stimuli", font=("Arial", 16, "bold"), pady=10, fg='white', bg='black')
        heading_label.grid(row=0, column=0, columnspan=2, sticky='w')

        self.tree = ttk.Treeview(table_frame, columns=("Stimuli Title", "Stimuli ID"), show='headings')
        self.tree.heading("Stimuli Title", text="Stimuli Title")
        self.tree.heading("Stimuli ID", text="Stimuli ID")
        self.tree.column("Stimuli Title", width=250, anchor='w')
        self.tree.column("Stimuli ID", width=100, anchor='w')
        self.tree.grid(row=1, column=0, columnspan=2, sticky='nsew')

        for _, row in self.movie_info.iterrows():
            self.tree.insert("", "end", values=(row['stimuli_title'], row['stimuli_id']))

        # Input for Stimulus ID
        input_frame = tk.Frame(self.root, bg='black')
        input_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(input_frame, text="Enter Stimulus ID:", font=("Arial", 14), fg='white', bg='black').pack(side=tk.LEFT, padx=10)
        self.stim_id_entry = tk.Entry(input_frame, font=("Arial", 14))
        self.stim_id_entry.pack(side=tk.LEFT, padx=10)
        tk.Button(input_frame, text="Submit", font=("Arial", 14), command=self.submit_stim_id, bg='#1f77b4', fg='white').pack(side=tk.LEFT, padx=10)

    def submit_stim_id(self):
        stim_id = self.stim_id_entry.get()
        self.scenes_info = pd.read_excel(r'C:\nikhilkuppa\movie_player_project\T_scene_combined.xlsx')

        if stim_id.isdigit():
            stim_id = int(stim_id)
            stim_title = self.movie_info[self.movie_info['stimuli_id'] == stim_id]['stimuli_title'].values[0]
            stim_title = stim_title.replace(" ", "_").rstrip("_")
            stim_df = self.scenes_info[self.scenes_info['stimuli_id'] == stim_id]

            self.root.withdraw()  # Hide the initial window
            VideoPlotterApp(stim_df, stim_title)
        else:
            messagebox.showerror("Invalid Input", "Please enter a valid Stimulus ID.")

class VideoPlotterApp:
    def __init__(self, df, stim_title):
        self.df = df
        self.stim_title = stim_title
        self.clicked_x = None
        self.frame_duration = None
        self.fps = None
        self.scene_index = 0
        self.cap = None
        self.dot = None
        self.current_scene_start = None
        self.current_scene_isc_eeg = None
        self.is_fullscreen = False
        self.root = tk.Toplevel()
        self.setup_ui()
        self.setup_plot()
        self.update_metadata()
        self.root.after(0, self.update_plot)
        self.root.mainloop()

    def setup_ui(self):
        main_frame = tk.Frame(self.root, bg='black')
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        top_frame = tk.Frame(main_frame, bg='black')
        top_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        bottom_frame = tk.Frame(main_frame, bg='black')
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        video_frame = tk.Frame(top_frame, bg='black')
        video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        metadata_frame = tk.Frame(top_frame, bg='black')
        metadata_frame.pack(side=tk.RIGHT, pady=10, fill=tk.Y, expand=True)

        self.opencv_label = tk.Label(video_frame, background='black')
        self.opencv_label.pack(fill=tk.BOTH, expand=True)

        self.metadata_frame = metadata_frame
        display_labels = [
            "Scene Number", "Duration (s)", "Scene Descriptor", "Soundtrack",
            "Special Effects", "Scene Genre: Sex", "Scene Genre: Action", "Scene Genre: Transport",
            "Scene Genre: Violence", "Food", "Alcohol", "Drugs"
        ]
        self.labels = [
            "scene_no", "scene_duration", "scene_descriptor", "Soundtrack",
            "Special_effects", "Sexual_scene", "Action_scene", "Transport_Scene",
            "Violence", "Eating_/_food", "Drinking_alcohol", "Doing_drugs"
        ]

        self.label_widgets = []
        self.value_widgets = []

        heading_label = tk.Label(metadata_frame, text=f"{self.stim_title} - Scene Information", font=("Arial", 16, "bold"), pady=35, fg='white', bg='black')
        heading_label.grid(row=0, column=0, columnspan=5, sticky='w')

        for i, label_text in enumerate(display_labels):
            label = tk.Label(metadata_frame, text=label_text, anchor='w', padx=10, width=25, relief='solid', borderwidth=1, fg='white', bg='black')
            label.grid(row=i + 1, column=0, sticky='w')

            value_label = tk.Label(metadata_frame, text="", anchor='w', padx=10, width=50, relief='solid', borderwidth=1, fg='white', bg='black')
            value_label.grid(row=i + 1, column=1, sticky='w')

            self.label_widgets.append(label)
            self.value_widgets.append(value_label)

        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", self.end_fullscreen)

    def setup_plot(self):
        self.fig, self.ax = plt.subplots(figsize=(14, 7))
        self.fig.patch.set_facecolor('black')
        self.ax.set_facecolor('black')
        self.ax.tick_params(axis='both', colors='white')

        self.draw_bars()

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def draw_bars(self):
        self.ax.clear()
        self.ax.spines['top'].set_color('white')
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['right'].set_color('white')
        self.ax.spines['left'].set_color('white')

        for _, row in self.df.iterrows():
            self.ax.bar(row['scene_start'], row['ISC_EEG'], width=row['scene_duration'],
                        align='edge', edgecolor='white', color='#1f77b4')

            y_pos = row['ISC_EEG']
            x_pos = row['scene_start'] + row['scene_duration'] / 2
            self.ax.text(x_pos, y_pos - 0.01 if y_pos > 0 else y_pos + 0.01, str(int(row['scene_no'])),
                         ha='center', va='top' if y_pos > 0 else 'bottom', fontsize=9, color='black')

        self.ax.set_xlim(self.df['scene_start'].min(), self.df['scene_end'].max())
        self.ax.set_ylim(self.df['ISC_EEG'].min() - 0.05, self.df['ISC_EEG'].max() + 0.05)
        self.ax.set_xlabel('Time (seconds)', color='white')
        self.ax.set_ylabel('ISC_EEG', color='white')
        self.ax.set_title(f'ISC_EEG Plot for {self.stim_title}', color='white', fontsize=14)
        self.ax.grid(True, which='both', linestyle='--', linewidth=0.5, color='grey')
        self.ax.ticklabel_format(style='scientific', axis='y', scilimits=(0,0))
        self.dot = self.ax.plot([], [], marker='o', markersize=8, color='red', zorder=5)[0]

    def update_metadata(self):
        if self.current_scene_start is not None:
            scene_data = self.df[self.df['scene_start'] == self.current_scene_start].iloc[0]
            for i, label in enumerate(self.labels):
                self.value_widgets[i].config(text=str(scene_data.get(label, "")))

    def update_plot_data(self, current_time):
        self.ax.set_xlim(current_time - 500, current_time + 500)
        self.fig.canvas.draw()

    def update_plot(self):
        video_dir = f'C:\\nikhilkuppa\\movie_player_project\\stimuli\\Scenes_corrected\\{self.stim_title}'
        video_files = sorted(f for f in os.listdir(video_dir) if f.endswith('.avi'))

        if self.cap is None or not self.cap.isOpened():
            if self.scene_index >= len(video_files):
                return
            video_path = os.path.join(video_dir, video_files[self.scene_index])
            self.cap = cv2.VideoCapture(video_path)

            if not self.cap.isOpened():
                print(f"Error opening video file: {video_path}")
                return

            self.fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.frame_duration = 1000 / (self.fps * 2) if self.fps > 0 else 1000 / 30
            self.current_scene_start = self.df.iloc[self.scene_index]['scene_start']
            self.current_scene_isc_eeg = self.df.iloc[self.scene_index]['ISC_EEG']
            self.dot.set_data([self.current_scene_start], [self.current_scene_isc_eeg])
            current_time = self.current_scene_start + (self.cap.get(cv2.CAP_PROP_POS_MSEC) / 1000)
            self.update_plot_data(current_time)
            self.update_metadata()

        ret, frame = self.cap.read()
        if not ret:
            self.scene_index += 1
            if self.scene_index >= len(video_files):
                return
            self.current_scene_start = self.df.iloc[self.scene_index]['scene_start']
            self.current_scene_isc_eeg = self.df.iloc[self.scene_index]['ISC_EEG']
            self.dot.set_data([self.current_scene_start], [self.current_scene_isc_eeg])

            self.cap.release()
            self.cap = None
            self.root.after(0, self.update_plot)
            return

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(frame_rgb)
        self.imgtk = ImageTk.PhotoImage(image=img_pil)
        self.opencv_label.imgtk = self.imgtk
        self.opencv_label.configure(image=self.imgtk)

        if self.clicked_x is not None:
            target_time = self.clicked_x
            scene_row = self.df[(self.df['scene_start'] <= target_time) & (self.df['scene_end'] >= target_time)]
            if not scene_row.empty:
                scene_no = scene_row['scene_no'].values[0]
                new_scene_file = f'{self.stim_title}_scene_{str(scene_no).zfill(2)}_tc.avi'
                if new_scene_file in video_files:
                    self.scene_index = video_files.index(new_scene_file)
                    self.current_scene_start = self.df.iloc[self.scene_index]['scene_start']
                    self.current_scene_isc_eeg = self.df.iloc[self.scene_index]['ISC_EEG']
                    self.clicked_x = None
                    self.cap.release()
                    self.cap = None
                    self.root.after(0, self.update_plot)
                    return

        current_time = self.current_scene_start + (self.cap.get(cv2.CAP_PROP_POS_MSEC) / 1000)
        self.dot.set_data([current_time], [self.current_scene_isc_eeg])
        self.update_plot_data(current_time)
        self.canvas.draw()

        self.root.after(int(self.frame_duration/8), self.update_plot)

    def on_click(self, event):
        if event.inaxes is not None:
            self.clicked_x = event.xdata
            print(f"Clicked at x={self.clicked_x}")

    def toggle_fullscreen(self, event=None):
        self.is_fullscreen = True
        self.root.attributes("-fullscreen", True)

    def end_fullscreen(self, event=None):
        self.is_fullscreen = False
        self.root.attributes("-fullscreen", False)

if __name__ == "__main__":
    root = tk.Tk()
    app = InitialScreen(root)

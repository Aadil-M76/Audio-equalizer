import tkinter as tk
from tkinter import ttk
import numpy as np
import sounddevice as sd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from scipy import signal
import queue

# Configuration
FS = 44100  # Sample rate
BLOCK_SIZE = 1024  # Audio block size
CENTER_FREQS = [60, 230, 910, 3600, 14000]  # Center frequencies in Hz
Q_FACTOR = 2.0  # Filter quality factor

# Increased font sizes and dimensions
LARGE_FONT = ('Helvetica', 14)
BUTTON_FONT = ('Helvetica', 16, 'bold')
SLIDER_LENGTH = 400
PLOT_SIZE = (10, 4)

class AudioEqualizer:
    def __init__(self):
        self.design_filters()
        self.initialize_state()
        self.gains_db = {i: 0.0 for i in range(len(CENTER_FREQS))}
        self.fft_queue = queue.Queue(maxsize=5)

    def design_filters(self):
        self.sos_filters = []
        for f in CENTER_FREQS:
            bandwidth = f / Q_FACTOR
            lowcut = max(20, f - bandwidth/2)
            highcut = min(FS/2 - 1, f + bandwidth/2)
            sos = signal.butter(2, [lowcut, highcut], btype='bandpass', fs=FS, output='sos')
            self.sos_filters.append(sos)

    def initialize_state(self):
        self.filter_states = [signal.sosfilt_zi(sos) * 0 for sos in self.sos_filters]

    def audio_callback(self, indata, outdata, frames, time, status):
        if status:
            print(status)
            
        input_signal = np.mean(indata, axis=1) if indata.ndim > 1 else indata.flatten()
        output = input_signal.copy().astype(np.float32)
        
        for i, sos in enumerate(self.sos_filters):
            filtered, self.filter_states[i] = signal.sosfilt(
                sos, input_signal, zi=self.filter_states[i]
            )
            gain_linear = 10 ** (self.gains_db[i] / 20)
            output += (gain_linear - 1) * filtered

        fft = np.fft.rfft(output)
        freqs = np.fft.rfftfreq(len(output), d=1/FS)
        magnitude = 20 * np.log10(np.abs(fft) + 1e-6)
        
        try:
            self.fft_queue.put_nowait((freqs, magnitude))
        except queue.Full:
            pass

        outdata[:] = np.column_stack((output, output))

class EqualizerGUI(tk.Tk):
    def __init__(self, equalizer):
        super().__init__()
        self.title("Real-Time Audio Equalizer")
        self.equalizer = equalizer
        self.geometry("1000x800")  # Larger window size
        
        # Configure styles for larger widgets
        self.style = ttk.Style()
        self.style.configure('.', font=LARGE_FONT)
        self.style.configure('TScale', sliderlength=40)
        
        self.create_controls()
        self.create_visualization()
        self.setup_audio_stream()
        self.update_plot()

    def create_controls(self):
        control_frame = ttk.Frame(self, padding=20)
        control_frame.pack(fill='x', padx=20, pady=20)
        
        self.sliders = []
        for idx, freq in enumerate(CENTER_FREQS):
            frame = ttk.Frame(control_frame)
            frame.pack(fill='x', pady=10)
            
            label = ttk.Label(frame, text=f"{freq} Hz", width=10, font=LARGE_FONT)
            label.pack(side='left', padx=10)
            
            slider = ttk.Scale(
                frame, 
                from_=-24, 
                to=24, 
                orient='horizontal',
                length=SLIDER_LENGTH,
                command=lambda val, i=idx: self.update_gain(i, float(val))
            )
            slider.set(0)
            slider.pack(side='right', fill='x', expand=True, padx=10)
            self.sliders.append(slider)
            
        self.start_button = ttk.Button(
            control_frame, 
            text="Start Processing", 
            command=self.toggle_processing,
            style='Large.TButton'
        )
        self.start_button.pack(pady=20, ipadx=20, ipady=10)
        
        # Custom style for large button
        self.style.configure('Large.TButton', font=BUTTON_FONT, padding=10)

    def create_visualization(self):
        fig_frame = ttk.Frame(self, padding=20)
        fig_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        self.fig, self.ax = plt.subplots(figsize=PLOT_SIZE)
        self.line, = self.ax.semilogx([], [])
        
        # Larger plot labels and ticks
        self.ax.set_xlim(20, 20000)
        self.ax.set_ylim(-60, 60)
        self.ax.set_xlabel("Frequency (Hz)", fontsize=14)
        self.ax.set_ylabel("Magnitude (dB)", fontsize=14)
        self.ax.tick_params(axis='both', which='major', labelsize=12)
        self.ax.grid(True)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=fig_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

    def setup_audio_stream(self):
        self.stream = None
        self.processing = False

    def toggle_processing(self):
        if self.processing:
            self.stream.stop()
            self.stream.close()
            self.start_button.config(text="Start Processing")
            self.processing = False
        else:
            self.stream = sd.Stream(
                samplerate=FS,
                blocksize=BLOCK_SIZE,
                dtype=np.float32,
                channels=(1, 2),
                callback=self.equalizer.audio_callback
            )
            self.stream.start()
            self.start_button.config(text="Stop Processing")
            self.processing = True

    def update_gain(self, idx, value):
        self.equalizer.gains_db[idx] = value

    def update_plot(self):
        try:
            freqs, magnitude = self.equalizer.fft_queue.get_nowait()
            self.line.set_data(freqs, magnitude)
            self.ax.relim()
            self.ax.autoscale_view(scalex=False, scaley=True)
            self.canvas.draw()
        except queue.Empty:
            pass
        self.after(50, self.update_plot)

if __name__ == "__main__":
    eq = AudioEqualizer()
    app = EqualizerGUI(eq)
    app.mainloop()
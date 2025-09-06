from DetectorController import DetectorController

import queue
import threading
import tkinter as tk
from datetime import datetime
from tkinter import ttk, scrolledtext

class DetectorGUI:
    """Simple GUI for the detector control system"""
    
    def __init__(self, controller: DetectorController):
        self.controller = controller
        self.acquisition_thread = None
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("Muon Detector Control")
        self.root.geometry("800x600")
        
        self.setup_gui()
        self.update_stats()
        
    def setup_gui(self):
        """Setup the GUI elements"""
        # Control frame
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        self.start_button = ttk.Button(control_frame, text="Start", 
                                     command=self.start_acquisition)
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.stop_button = ttk.Button(control_frame, text="Stop", 
                                    command=self.stop_acquisition, 
                                    state="disabled")
        self.stop_button.grid(row=0, column=1, padx=5)
        
        # Statistics frame
        stats_frame = ttk.LabelFrame(self.root, text="Statistics", padding="10")
        stats_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), 
                        padx=10, pady=5)
        
        self.stats_labels = {}
        stats_info = [
            ('Events:', 'events'),
            ('Total Hits:', 'total_hits'),
            ('Runtime (s):', 'runtime'),
            ('Event Rate (Hz):', 'event_rate'),
            ('Hit Rate (Hz):', 'hit_rate')
        ]
        
        for i, (label_text, key) in enumerate(stats_info):
            label = ttk.Label(stats_frame, text=label_text)
            label.grid(row=i//3, column=(i%3)*2, sticky=tk.W, padx=5)
            
            value_label = ttk.Label(stats_frame, text="0")
            value_label.grid(row=i//3, column=(i%3)*2+1, sticky=tk.W, padx=15)
            self.stats_labels[key] = value_label
        
        # Log frame
        log_frame = ttk.LabelFrame(self.root, text="Event Log", padding="10")
        log_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), 
                      padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights for resizing
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(2, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
    def log_message(self, message: str):
        """Add a message to the log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, full_message)
        self.log_text.see(tk.END)
        
    def start_acquisition(self):
        """Start data acquisition in a separate thread"""
        if not self.controller.running:
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            
            self.acquisition_thread = threading.Thread(
                target=self.controller.run_acquisition,
                args=(self.log_message,),
                daemon=True
            )
            self.acquisition_thread.start()
            
    def stop_acquisition(self):
        """Stop data acquisition"""
        self.controller.stop_acquisition()
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        
    def update_stats(self):
        """Update statistics display"""
        stats = self.controller.get_statistics()
        
        self.stats_labels['events'].config(text=str(stats['events']))
        self.stats_labels['total_hits'].config(text=str(stats['total_hits']))
        self.stats_labels['runtime'].config(text=f"{stats['runtime_seconds']:.1f}")
        self.stats_labels['event_rate'].config(text=f"{stats['event_rate']:.2f}")
        self.stats_labels['hit_rate'].config(text=f"{stats['hit_rate']:.2f}")
        
        # Check for new events
        try:
            while True:
                event = self.controller.event_queue.get_nowait()
                # Could add more detailed event display here
        except queue.Empty:
            pass
        
        # Schedule next update
        self.root.after(1000, self.update_stats)  # Update every second
        
    def run(self):
        """Run the GUI"""
        self.root.mainloop()
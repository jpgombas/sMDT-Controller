#!/usr/bin/env python3
"""
DetectorGUI.py - GUI Module for Muon Detector Control System
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import queue
import base64
from io import BytesIO
from datetime import datetime

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    print("Warning: PIL/Pillow not found. Image display disabled.")
    PIL_AVAILABLE = False

# Import the reconstruction algorithm
try:
    from Reconstruction import ReconstructionAlg
    RECONSTRUCTION_AVAILABLE = True
except ImportError:
    print("Warning: Reconstruction.py not found. Reconstruction features disabled.")
    RECONSTRUCTION_AVAILABLE = False


class DetectorGUI:
    """Enhanced GUI for the detector control system with reconstruction visualization"""
    
    def __init__(self, controller):
        self.controller = controller
        self.acquisition_thread = None
        self.current_reconstruction = None
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("Muon Detector Control & Reconstruction")
        self.root.geometry("1000x800")
        
        self.setup_gui()
        self.update_stats()
        
    def setup_gui(self):
        """Setup the single window GUI with left-right split"""
        # Create main horizontal frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left side - Control and Status (original control tab content)
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.setup_control_panel(left_frame)
        
        # Right side - Reconstruction plots (if available)
        if RECONSTRUCTION_AVAILABLE and PIL_AVAILABLE:
            right_frame = ttk.Frame(main_frame)
            right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
            self.setup_reconstruction_panel(right_frame)
        elif RECONSTRUCTION_AVAILABLE:
            print("Note: Reconstruction available but PIL not installed - visualization disabled")
    
    def setup_control_panel(self, parent):
        """Setup the control and status panel (left side)"""
        # Control buttons
        control_button_frame = ttk.Frame(parent, padding="10")
        control_button_frame.pack(side=tk.TOP, fill=tk.X)
        
        self.start_button = ttk.Button(control_button_frame, text="Start", 
                                     command=self.start_acquisition)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(control_button_frame, text="Stop", 
                                    command=self.stop_acquisition, 
                                    state="disabled")
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Statistics frame
        stats_frame = ttk.LabelFrame(parent, text="Statistics", padding="10")
        stats_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        
        self.stats_labels = {}
        stats_info = [
            ('Events:', 'events'),
            ('Total Hits:', 'total_hits'),
            ('Runtime (s):', 'runtime'),
            ('Event Rate (Hz):', 'event_rate'),
            ('Hit Rate (Hz):', 'hit_rate'),
            ('Reconstructed:', 'reconstructed_events'),
            ('Reco Efficiency:', 'reconstruction_efficiency')
        ]
        
        # Arrange statistics in a grid (2 columns)
        for i, (label_text, key) in enumerate(stats_info):
            row = i // 2
            col = (i % 2) * 2
            
            label = ttk.Label(stats_frame, text=label_text)
            label.grid(row=row, column=col, sticky=tk.W, padx=5, pady=2)
            
            value_label = ttk.Label(stats_frame, text="0")
            value_label.grid(row=row, column=col+1, sticky=tk.W, padx=15, pady=2)
            self.stats_labels[key] = value_label
        
        # Log frame
        log_frame = ttk.LabelFrame(parent, text="Event Log", padding="10")
        log_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=60)
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def setup_reconstruction_panel(self, parent):
        """Setup the reconstruction visualization panel (right side)"""
        # Header with reconstruction info
        reco_header_frame = ttk.Frame(parent, padding="10")
        reco_header_frame.pack(side=tk.TOP, fill=tk.X)
        
        # Chamber 0 visualization frame
        chamber0_frame = ttk.LabelFrame(parent, text="Chamber 0 - Track Visualization", padding="10")
        chamber0_frame.pack(side=tk.TOP, fill=tk.Y, expand=True, pady=(0, 5))
        
        # Canvas for chamber 0 reconstruction plot
        self.plot_canvas_0 = tk.Canvas(chamber0_frame, bg='white', width=500, height=280)
        self.plot_canvas_0.pack(fill=tk.Y, expand=True)
        
        # Chamber 1 visualization frame
        chamber1_frame = ttk.LabelFrame(parent, text="Chamber 1 - Track Visualization", padding="10")
        chamber1_frame.pack(side=tk.TOP, fill=tk.Y, expand=True, pady=(5, 0))
        
        # Canvas for chamber 1 reconstruction plot
        self.plot_canvas_1 = tk.Canvas(chamber1_frame, bg='white', width=500, height=280)
        self.plot_canvas_1.pack(fill=tk.Y, expand=True)
    
    def update_reconstruction_plot(self):
        """Update both reconstruction plots simultaneously"""
        if not self.current_reconstruction or not RECONSTRUCTION_AVAILABLE or not PIL_AVAILABLE:
            return
        
        # Update both chamber plots
        for chamber in [0, 1]:
            try:
                canvas = self.plot_canvas_0 if chamber == 0 else self.plot_canvas_1
                
                image_b64 = self.controller.recon_alg.plot_reconstruction(
                    self.current_reconstruction, chamber)
                
                if image_b64:
                    # Decode base64 image
                    image_data = base64.b64decode(image_b64)
                    image = Image.open(BytesIO(image_data))
                    
                    # Resize to fit canvas
                    canvas_width = canvas.winfo_width()
                    canvas_height = canvas.winfo_height()
                    
                    if canvas_width > 1 and canvas_height > 1:  # Canvas is initialized
                        image = image.resize((canvas_width-20, canvas_height-20), Image.Resampling.LANCZOS)
                    
                    photo = ImageTk.PhotoImage(image)
                    
                    # Clear canvas and display image
                    canvas.delete("all")
                    canvas.create_image(canvas_width//2, canvas_height//2, 
                                              image=photo, anchor=tk.CENTER)
                    # Keep a reference to prevent garbage collection
                    if chamber == 0:
                        canvas.image_0 = photo
                    else:
                        canvas.image_1 = photo
                        
            except Exception as e:
                print(f"Error updating reconstruction plot for chamber {chamber}: {e}")
            
    
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
        
        if 'reconstructed_events' in self.stats_labels:
            self.stats_labels['reconstructed_events'].config(text=str(stats['reconstructed_events']))
            self.stats_labels['reconstruction_efficiency'].config(
                text=f"{stats['reconstruction_efficiency']:.2f}")
        
        # Check for new events
        try:
            while True:
                self.controller.event_queue.get_nowait()
        except queue.Empty:
            pass
        
        # Check for new reconstructions
        if RECONSTRUCTION_AVAILABLE:
            try:
                while True:
                    reconstruction = self.controller.reconstruction_queue.get_nowait()
                    self.current_reconstruction = reconstruction
                    if not reconstruction: continue      
                    # Update both plots
                    if hasattr(self, 'plot_canvas_0') and hasattr(self, 'plot_canvas_1') and PIL_AVAILABLE:
                        self.update_reconstruction_plot()
                            
            except queue.Empty:
                pass
        
        # Schedule next update
        self.root.after(1000, self.update_stats)  # Update every second
        
    def run(self):
        """Run the GUI"""
        self.root.mainloop()
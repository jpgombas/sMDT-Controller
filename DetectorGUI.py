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
from PIL import Image, ImageTk
import traceback

class DetectorGUI:
    """Enhanced GUI for the detector control system with reconstruction visualization"""
    
    def __init__(self, controller):
        self.controller = controller
        self.acquisition_thread = None
        self.current_reconstruction = None
        self.events_processed = 0
        self.reconstructions_processed = 0
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("Muon Detector Control & Reconstruction")
        self.root.geometry("800x600")  # Increased size for better proportions
        self.root.minsize(800, 600)  # Set minimum size
        
        self.setup_gui()
        self.update_stats()
        
    def setup_gui(self):
        """Setup with equal division between left and right panels"""
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configure grid to have equal weight columns
        main_frame.grid_columnconfigure(0, weight=1, uniform="column")  # Left half
        main_frame.grid_columnconfigure(1, weight=1, uniform="column")  # Right half
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Left side - Control panel and logs
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        self.setup_control_panel(left_frame)
        
        # Right side - Reconstruction visualization
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        self.setup_reconstruction_panel(right_frame)
    
    def setup_control_panel(self, parent):
        """Setup the control and status panel (left side)"""
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(2, weight=1)  # Make log frame expandable
        
        # Control buttons
        control_button_frame = ttk.Frame(parent)
        control_button_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        self.start_button = ttk.Button(control_button_frame, text="Start", 
                                     command=self.start_acquisition)
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_button = ttk.Button(control_button_frame, text="Stop", 
                                    command=self.stop_acquisition, 
                                    state="disabled")
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Statistics frame
        stats_frame = ttk.LabelFrame(parent, text="Statistics", padding="10")
        stats_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        
        self.stats_labels = {}
        stats_info = [
            ('Events:', 'events'),
            ('Runtime (s):', 'runtime'),
            ('Event Rate (Hz):', 'event_rate'),
            ('Events in Reco Buffer:', 'reconstruction_queue_size')
        ]
        
        # Arrange statistics in a grid (2 columns)
        for i, (label_text, key) in enumerate(stats_info):
            row = i // 2
            col = (i % 2) * 2
            
            label = ttk.Label(stats_frame, text=label_text)
            label.grid(row=row, column=col, sticky=tk.W, padx=(0, 5), pady=2)
            
            value_label = ttk.Label(stats_frame, text="0")
            value_label.grid(row=row, column=col+1, sticky=tk.W, padx=(0, 15), pady=2)
            self.stats_labels[key] = value_label
        
        # Log frame
        log_frame = ttk.LabelFrame(parent, text="Event Log", padding="5")
        log_frame.grid(row=2, column=0, sticky="nsew")
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky="nsew")
    
    def setup_reconstruction_panel(self, parent):
        """Setup the reconstruction visualization panel (right side)"""
        parent.grid_rowconfigure(0, weight=1, uniform="chamber")  # Chamber 0
        parent.grid_rowconfigure(1, weight=1, uniform="chamber")  # Chamber 1
        parent.grid_columnconfigure(0, weight=1)
        
        # Chamber 0 visualization frame
        chamber0_container = ttk.LabelFrame(parent, text="Chamber 0", padding="5")
        chamber0_container.grid(row=0, column=0, sticky="nsew", pady=(0, 5))
        chamber0_container.grid_rowconfigure(0, weight=1)
        chamber0_container.grid_columnconfigure(0, weight=1)
        
        # Canvas for chamber 0 reconstruction plot with 8:6 aspect ratio
        self.plot_canvas_0 = tk.Canvas(chamber0_container, bg='white')
        self.plot_canvas_0.grid(row=0, column=0, sticky="nsew")
        self.plot_canvas_0.bind('<Configure>', lambda e: self.on_canvas_configure(e, 0))
        
        # Chamber 1 visualization frame
        chamber1_container = ttk.LabelFrame(parent, text="Chamber 1", padding="5")
        chamber1_container.grid(row=1, column=0, sticky="nsew", pady=(5, 0))
        chamber1_container.grid_rowconfigure(0, weight=1)
        chamber1_container.grid_columnconfigure(0, weight=1)
        
        # Canvas for chamber 1 reconstruction plot with 8:6 aspect ratio
        self.plot_canvas_1 = tk.Canvas(chamber1_container, bg='white')
        self.plot_canvas_1.grid(row=0, column=0, sticky="nsew")
        self.plot_canvas_1.bind('<Configure>', lambda e: self.on_canvas_configure(e, 1))
    
    def on_canvas_configure(self, event, chamber):
        """Handle canvas resize events to maintain aspect ratio"""
        canvas = event.widget
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        
        # Calculate dimensions maintaining 8:6 aspect ratio (4:3)
        aspect_ratio = 8.0 / 6.0
        
        if canvas_width / canvas_height > aspect_ratio:
            # Width is limiting factor
            plot_height = canvas_height - 20  # Leave some margin
            plot_width = int(plot_height * aspect_ratio)
        else:
            # Height is limiting factor
            plot_width = canvas_width - 20  # Leave some margin
            plot_height = int(plot_width / aspect_ratio)
        
        # Store the calculated dimensions for use in update_reconstruction_plot
        if chamber == 0:
            self.plot_canvas_0.plot_width = plot_width
            self.plot_canvas_0.plot_height = plot_height
        else:
            self.plot_canvas_1.plot_width = plot_width
            self.plot_canvas_1.plot_height = plot_height
        
        # Update the plot if we have current reconstruction data
        if self.current_reconstruction:
            self.update_reconstruction_plot()
    
    def update_reconstruction_plot(self):
        """Update both reconstruction plots simultaneously with proper aspect ratio"""
        if not self.current_reconstruction:
            return
        
        # Update both chamber plots
        for chamber in [0, 1]:
            try:
                canvas = self.plot_canvas_0 if chamber == 0 else self.plot_canvas_1
                
                # Skip if canvas dimensions haven't been calculated yet
                if not hasattr(canvas, 'plot_width') or not hasattr(canvas, 'plot_height'):
                    continue
                
                image_b64 = self.controller.recon_alg.plot_reconstruction(
                    self.current_reconstruction, chamber)
                
                if image_b64:
                    # Decode base64 image
                    image_data = base64.b64decode(image_b64)
                    image = Image.open(BytesIO(image_data))
                    
                    # Resize to maintain 8:6 aspect ratio
                    plot_width = getattr(canvas, 'plot_width', 400)
                    plot_height = getattr(canvas, 'plot_height', 300)
                    
                    image = image.resize((plot_width, plot_height), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(image)
                    
                    # Clear canvas and display image centered
                    canvas.delete("all")
                    canvas_width = canvas.winfo_width()
                    canvas_height = canvas.winfo_height()
                    
                    canvas.create_image(canvas_width//2, canvas_height//2, 
                                      image=photo, anchor=tk.CENTER)
                    
                    # Keep a reference to prevent garbage collection
                    if chamber == 0:
                        canvas.image_0 = photo
                    else:
                        canvas.image_1 = photo
                        
            except Exception as e:
                print(f"ERROR: Error updating reconstruction plot for chamber {chamber}: {e}")
                traceback.print_exc()
            
    
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
        try:
            stats = self.controller.get_statistics()
            
            self.stats_labels['events'].config(text=str(stats['events']))
            self.stats_labels['runtime'].config(text=f"{stats['runtime_seconds']:.1f}")
            self.stats_labels['event_rate'].config(text=f"{stats['event_rate']:.2f}")
            
            if 'reconstruction_queue_size' in self.stats_labels:
                self.stats_labels['reconstruction_queue_size'].config(text=str(stats['reconstruction_queue_size']))
            
            events_this_update = 0
            try:
                while events_this_update < 10:  # Limit to prevent GUI freezing
                    self.controller.event_queue.get_nowait()
                    self.events_processed += 1
                    events_this_update += 1
            except queue.Empty:
                pass
            
            reconstructions_this_update = 0
            plot_updated = False
            try:
                while reconstructions_this_update < 10:  # Limit to prevent GUI freezing
                    reconstruction = self.controller.reconstruction_queue.get_nowait()
                    self.reconstructions_processed += 1
                    reconstructions_this_update += 1
                    
                    # Update current reconstruction (keep the most recent one)
                    self.current_reconstruction = reconstruction
                    plot_updated = True                    
            except queue.Empty:
                pass
            
            # Update plots if we got new reconstruction data
            if plot_updated and hasattr(self, 'plot_canvas_0') and hasattr(self, 'plot_canvas_1'):
                self.update_reconstruction_plot()  
        except Exception as e:
            print(f"ERROR: Exception in update_stats: {e}")
            import traceback
            traceback.print_exc()
        
        # Schedule next update
        self.root.after(500, self.update_stats)  # Update every 0.5 seconds
        
    def run(self):
        """Run the GUI"""
        self.root.mainloop()
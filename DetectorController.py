#!/usr/bin/env python3
"""
DetectorController.py - Main controller for the muon detector system
"""

from EventData import EventData
from DetectorHardware import DetectorHardware
import time
import queue
import json
from datetime import datetime
from typing import Dict, Optional

# Import the reconstruction algorithm
try:
    from Reconstruction import ReconstructionAlg
    RECONSTRUCTION_AVAILABLE = True
except ImportError:
    print("Warning: Reconstruction.py not found. Reconstruction features disabled.")
    RECONSTRUCTION_AVAILABLE = False


class DetectorController:
    """Main controller for the muon detector system"""
    
    def __init__(self, output_file: str = "detector_events.json"):
        self.hardware = DetectorHardware()
        self.output_file = output_file
        self.running = False
        self.event_counter = 0
        self.total_hits = 0
        self.event_queue = queue.Queue()
        self.reconstruction_queue = queue.Queue()
        
        # Initialize reconstruction algorithm
        if RECONSTRUCTION_AVAILABLE:
            self.recon_alg = ReconstructionAlg()
        else:
            self.recon_alg = None
        
        # Statistics
        self.start_time = None
        self.stop_time = None
        self.last_event_time = None
        self.reconstructed_events = 0

    def process_event(self) -> Optional[EventData]:
        """Process a single triggered event"""
        event = EventData(self.event_counter)
        self.event_counter += 1
        
        # Read all tubes
        for tube_num in range(96):
            result = self.hardware.read_tube_data(tube_num)
            if result != -1:
                tof, tot = result
                event.add_hit(tube_num, tof, tot)
                self.total_hits += 1
        
        self.last_event_time = datetime.now()
        
        # Attempt reconstruction if available and enough hits
        if self.recon_alg and len(event.hits) >= 4:
            try:
                reconstruction = self.recon_alg.reconstruct_event(event.hits)
                if reconstruction:
                    event.reconstruction = reconstruction
                    self.reconstructed_events += 1
            except Exception as e:
                print(f"Reconstruction failed for event {event.event_id}: {e}")
        
        return event

    def save_event(self, event: EventData):
        """Save event data to file"""
        try:
            with open(self.output_file, 'a') as f:
                json.dump(event.to_dict(), f)
                f.write('\n')
        except Exception as e:
            print(f"Error saving event: {e}")

    def run_acquisition(self, log_callback=None):
        """Main acquisition loop"""
        self.running = True
        self.start_time = datetime.now()
        
        if log_callback:
            log_callback("Starting data acquisition...")
        
        try:
            while self.running:
                if self.hardware.check_trigger():
                    if log_callback:
                        log_callback("Trigger detected, processing event...")
                    
                    # Process the event
                    event = self.process_event()
                    
                    # Save to file
                    self.save_event(event)
                    
                    # Reset trigger for next event
                    self.hardware.reset_trigger()
                    
                    # Log event info
                    if log_callback:
                        log_callback(f"Recorded: {event.get_summary()}")
                    
                    # Put event in queue for GUI updates
                    if hasattr(self, 'event_queue'):
                        try:
                            self.event_queue.put_nowait(event)
                        except queue.Full:
                            pass
                    
                    # Put reconstruction in queue for GUI if available
                    if hasattr(event, 'reconstruction') and hasattr(self, 'reconstruction_queue'):
                        try:
                            self.reconstruction_queue.put_nowait((event.reconstruction))
                        except queue.Full:
                            pass
                
                else:
                    # Small delay to prevent excessive CPU usage
                    time.sleep(0.001)  # 1ms
                    
        except KeyboardInterrupt:
            if log_callback:
                log_callback("Acquisition interrupted by user")
        except Exception as e:
            if log_callback:
                log_callback(f"Error during acquisition: {e}")
        finally:
            self.running = False
            if log_callback:
                log_callback("Data acquisition stopped")

    def stop_acquisition(self):
        """Stop the acquisition loop"""
        self.running = False
        self.stop_time = datetime.now()

    def get_statistics(self) -> Dict:
        """Get acquisition statistics"""
        runtime = 0
        if self.start_time:
            if self.stop_time:
                runtime = (self.stop_time - self.start_time).total_seconds()
            else:
                runtime = (datetime.now() - self.start_time).total_seconds()
        
        stats = {
            'events': self.event_counter,
            'total_hits': self.total_hits,
            'runtime_seconds': runtime,
            'event_rate': self.event_counter / runtime if runtime > 0 else 0,
            'hit_rate': self.total_hits / runtime if runtime > 0 else 0,
            'reconstructed_events': self.reconstructed_events
        }
        
        if self.event_counter > 0:
            stats['reconstruction_efficiency'] = self.reconstructed_events / self.event_counter
        else:
            stats['reconstruction_efficiency'] = 0
            
        return stats
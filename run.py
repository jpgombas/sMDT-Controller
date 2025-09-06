#!/usr/bin/env python3
"""
Muon Drift Tube Detector Control System
For Raspberry Pi with GPIO control

Detector Configuration:
- 2 chambers of 4 layers each
- 12 cylindrical muon drift tubes per layer
- Total: 96 tubes (indexed 0-95)
- Chamber 2 rotated 90° relative to Chamber 1
- Scintillator on top for time-of-flight trigger
"""

from DetectorGUI import DetectorGUI
from DetectorController import DetectorController

import time
import argparse
import threading
from datetime import datetime

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Muon Detector Control System")
    parser.add_argument("--headless", action="store_true", 
                       help="Run in headless mode without GUI")
    parser.add_argument("--output", default="detector_events.json",
                       help="Output file for event data")
    parser.add_argument("--duration", type=float,
                       help="Run duration in seconds (headless mode only)")
    
    args = parser.parse_args()
    
    # Create controller
    controller = DetectorController(output_file=args.output)
    
    if args.headless:
        # Headless mode
        print("Starting headless acquisition...")
        print(f"Output file: {args.output}")
        
        def console_logger(message):
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        
        try:
            if args.duration:
                # Run for specified duration
                controller.run_acquisition(console_logger)
                
                # Stop after duration
                def stop_after_duration():
                    time.sleep(args.duration)
                    controller.stop_acquisition()
                
                timer_thread = threading.Thread(target=stop_after_duration, daemon=True)
                timer_thread.start()
                timer_thread.join()
            else:
                # Run until interrupted
                controller.run_acquisition(console_logger)
                
        except KeyboardInterrupt:
            print("\nStopping acquisition...")
            controller.stop_acquisition()
        
        # Print final statistics
        stats = controller.get_statistics()
        print("\nFinal Statistics:")
        print(f"Events: {stats['events']}")
        print(f"Total Hits: {stats['total_hits']}")
        print(f"Runtime: {stats['runtime_seconds']:.1f}s")
        print(f"Event Rate: {1/stats['event_rate']:.2f} seconds")
        
    else:
        # GUI mode
        gui = DetectorGUI(controller)
        gui.run()


if __name__ == "__main__":
    main()
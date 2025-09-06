from typing import Tuple

class DetectorHardware:
    """Abstract hardware interface for the muon detector"""
    
    def __init__(self):
        self.trigger_count = 0
        self.simulated = True  # Set to False when real GPIO is implemented
        
    def check_trigger(self) -> bool:
        """
        Check if an event has been triggered
        Returns: True if event triggered, False otherwise
        """
        if self.simulated:
            # Simulate random triggers for testing
            import random
            return random.random() < 0.0005  # 0.05% chance per check
        
        # TODO: Implement actual GPIO trigger check
        # return gpio.read_trigger_pin()
        return False
    
    def read_tube_data(self, tube_number: int) -> Tuple[float, float] | int:
        """
        Read data from a specific tube
        Args:
            tube_number: Tube index (0-95)
        Returns:
            Tuple of (time_of_flight, time_over_threshold) or -1 if no hit
        """
        if not (0 <= tube_number <= 95):
            raise ValueError("Tube number must be between 0 and 95")
        
        if self.simulated:
            import random
            # Simulate hit probability and timing data
            if random.random() < 0.1:  # 30% hit probability
                tof = random.uniform(10.0, 100.0)  # ns
                tot = random.uniform(5.0, 50.0)    # ns
                return (tof, tot)
            else:
                return -1
        
        # TODO: Implement actual GPIO tube readout
        # return gpio.read_tube(tube_number)
        return -1
    
    def reset_trigger(self):
        """Reset the trigger system for next event"""
        if self.simulated:
            self.trigger_count += 1
            
        # TODO: Implement actual GPIO trigger reset
        # gpio.reset_trigger()
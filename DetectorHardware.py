from typing import Tuple

class DetectorHardware:
    """Abstract hardware interface for the muon detector"""
    
    def __init__(self):
        self.trigger_count = 0
        self.simulated = True  # Set to False when real GPIO is implemented
        # REMOVE when hardware is developed
        self.next_event_hits = []
        
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
        return False
    
    def read_tube_data(self, tube_number: int, post_arm: bool = True) -> Tuple[float, float] | int:
        """
        Read data from a specific tube. Arm the TDC if post_arm = True.
        Args:
            tube_number: Tube index (0-95)
            post_arm: Arm the TDC right after reading 
        Returns:
            Tuple of (time_of_flight, time_over_threshold) or -1 if no hit
        """
        if not (0 <= tube_number <= 95):
            raise ValueError("Tube number must be between 0 and 95")
        
        if self.simulated:
            import random
            # Simulate hit probability and timing data
            if tube_number in self.next_event_hits:  # Check if this tube was hit
                tof = random.uniform(10.0, 100.0)  # ns
                tot = random.uniform(5.0, 50.0)    # ns
                return (tof, tot)
            else:
                return -1
        
        # TODO: Implement actual GPIO tube readout
        return -1
    
    def arm_TDC(self, tube_number: int):
        """
        Arm the TDC for the next time measurments. Each TDC needs to be armed
        after each measurment. Use this function if you used the read_tube_data()
        function and haven't armed the TDC.
        """
        # TODO: Implement this function when hardware becomes available
        return
    
    def read_and_arm_tube(self, tube_number: int):
        """
        Reads the data from the specified tube_number, and automatically
        re-arms the TDC for the next mesurment.
        Args:
            tube_number: Tube index (0-95)
        Returns:
            Tuple of (time_of_flight, time_over_threshold) or -1 if no hit
        """
        return self.read_tube_data(tube_number, post_arm=True)
        

    def reset_trigger(self):
        """Reset the trigger system for next event"""
        if self.simulated:
            self.trigger_count += 1
            
        # TODO: Implement actual GPIO trigger reset

    ############################################
    ##### Simulation Code
    ############################################

    def generate_event(self):
        """Enhanced event simulation with configurable parameters"""
        import random
        self.next_event_hits = []
        
        # Configurable parameters
        config = {
            "chambers": [
                {"start": 0, "end": 48, "rows": 4, "tubes_per_row": 12},
                {"start": 48, "end": 96, "rows": 4, "tubes_per_row": 12}
            ],
            "adjacent_hit_probability": 0.1,
            "track_efficiency": 0.9  # Probability of detecting a hit
        }
                
        for i, chamber in enumerate(config["chambers"]):
            orientation = random.randint(-1, 1)
                        
            # Generate track hits for this chamber
            chamber_hits = self._generate_chamber_track(chamber, orientation, config)
            self.next_event_hits.extend(chamber_hits)

    def _generate_adjacent_hits(self, center_tube, row_start, row_end, 
                            adjacent_probability=0.1):
        """Generate adjacent hits due to noise"""
        import random
        adjacent_hits = []
        
        # Left adjacent tube
        if center_tube - 1 >= row_start and random.random() < adjacent_probability:
            adjacent_hits.append(center_tube - 1)
        
        # Right adjacent tube
        if center_tube + 1 <= row_end and random.random() < adjacent_probability:
            adjacent_hits.append(center_tube + 1)
        
        return adjacent_hits

    def _generate_chamber_track(self, chamber, orientation, config):
        """Advanced chamber track generation with efficiency and noise modeling"""
        import random
        hits = []
        
        # Starting tube in first row of chamber
        first_row_start = chamber["start"]
        first_row_end = first_row_start + chamber["tubes_per_row"] - 1
        tube_num = random.randint(first_row_start, first_row_end)
        
        for row in range(chamber["rows"]):
            # Check if we're still within chamber bounds
            if tube_num < chamber["start"] or tube_num >= chamber["end"]:
                break

            # Check if we're still within the correct row
            if (tube_num%48)//12 != row:
                break 
            
            # Simulate detection efficiency
            if random.random() < config["track_efficiency"]:
                hits.append(tube_num)
                
                # Add adjacent hits (noise/scattering)
                row_start = (chamber["start"] // chamber["tubes_per_row"] + row) * chamber["tubes_per_row"]
                row_end = row_start + chamber["tubes_per_row"] - 1
                
                adjacent_hits = self._generate_adjacent_hits(
                    tube_num, row_start, row_end, 
                    config["adjacent_hit_probability"]
                )
                hits.extend(adjacent_hits)
            
            # Move to next row
            tube_num += chamber["tubes_per_row"] + orientation
        
        return hits
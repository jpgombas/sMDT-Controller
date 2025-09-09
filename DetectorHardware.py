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
            if tube_number in self.next_event_hits:  # Check if this tube was hit
                tof = random.uniform(10.0, 100.0)  # ns
                tot = random.uniform(5.0, 50.0)    # ns
                return (tof, tot)
            else:
                return -1
        
        # TODO: Implement actual GPIO tube readout
        return -1
    
    def reset_trigger(self):
        """Reset the trigger system for next event"""
        if self.simulated:
            self.trigger_count += 1
            
        # TODO: Implement actual GPIO trigger reset

    def generate_event(self):
        """Creates a more convincing event simulation"""
        import random
        # -1 is a track from left to right
        # 0 is straight
        # 1 is a track from right to left

        # Chamber 0 
        self.next_event_hits = []
        orientation = random.randint(-1, 1)
        tube_num = random.randint(0,12)
        row = 0

        while tube_num < 48:
            self.next_event_hits.append(tube_num)
            tube_num += 12 + orientation
            row += 1

            # Add probability of adjacent hit (10%)
            if random.random() < 0.1:
                self.next_event_hits.append(tube_num-1)
            if random.random() < 0.1:
                self.next_event_hits.append(tube_num+1)

            # if track goes off from chamber, go to next chamber
            if tube_num//12 != row: 
                break

        # Chamber 1
        orientation = random.randint(-1, 1)
        tube_num = random.randint(48,60)
        row = 4

        while tube_num < 96:
            self.next_event_hits.append(tube_num)
            tube_num += 12 + orientation
            row += 1

            # Add probability of adjacent hit (10%)
            if random.random() < 0.1:
                self.next_event_hits.append(tube_num-1)
            if random.random() < 0.1:
                self.next_event_hits.append(tube_num+1)

            # if track goes off from chamber, go to next chamber
            if tube_num//12 != row: 
                break

    # Alternative implementation with additional features
    def generate_event_advanced(self):
        """Enhanced event simulation with configurable parameters"""
        import random
        self.next_event_hits = []
        
        # Configurable parameters
        config = {
            "chambers": [
                {"start": 0, "end": 48, "rows": 4, "tubes_per_row": 12},
                {"start": 48, "end": 96, "rows": 4, "tubes_per_row": 12}
            ],
            "adjacent_hit_probability": 0.15,
            "track_efficiency": 0.9  # Probability of detecting a hit
        }
                
        for i, chamber in enumerate(config["chambers"]):
            orientation = random.randint(-1, 1)
                        
            # Generate track hits for this chamber
            chamber_hits = self._generate_chamber_track(chamber, orientation, config)
            self.next_event_hits.extend(chamber_hits)

    def _generate_adjacent_hits(self, center_tube, row_start, row_end, 
                            adjacent_probability=0.1):
        """Generate adjacent hits due to noise or particle scattering"""
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
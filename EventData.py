"""
EventData.py - Container for a single detector event
"""

from datetime import datetime
from typing import Dict, List, Optional


class EventData:
    """Container for a single detector event"""
    
    def __init__(self, event_id: int):
        self.event_id = event_id
        self.timestamp = datetime.now()
        self.hits: List[Dict] = []
        self.reconstruction: Optional[Dict] = None
        
    def add_hit(self, tube_number: int, tof: float, tot: float):
        """Add a hit to this event"""
        chamber = 0 if tube_number < 48 else 1
        layer = (tube_number % 48) // 12
        tube_in_layer = tube_number % 12
        
        hit_data = {
            'tube_number': tube_number,
            'chamber': chamber,
            'layer': layer,
            'tube_in_layer': tube_in_layer,
            'time_of_flight': tof,
            'time_over_threshold': tot
        }
        self.hits.append(hit_data)
    
    def get_summary(self) -> str:
        """Get a summary string for this event"""
        if not self.hits:
            return f"Event {self.event_id}: No hits"
        
        chamber_0_hits = sum(1 for hit in self.hits if hit['chamber'] == 0)
        chamber_1_hits = sum(1 for hit in self.hits if hit['chamber'] == 1)
        
        summary = (f"Event {self.event_id}: {len(self.hits)} hits "
                  f"(C0: {chamber_0_hits}, C1: {chamber_1_hits})")
        
        return summary
    
    def to_dict(self) -> Dict:
        """Convert event to dictionary for JSON serialization"""
        event_dict = {
            'event_id': self.event_id,
            'timestamp': self.timestamp.isoformat(),
            'hit_count': len(self.hits),
            'hits': self.hits
        }
        
        if self.reconstruction:
            event_dict['reconstruction'] = self.reconstruction
            
        return event_dict
# Hardware Integration Guide

This document outlines the transition from simulation to real hardware operation for the muon detector control system.

## Current Simulation vs. Future Hardware

### Simulation Mode (Current)
The system currently operates with simulated hardware interactions:
- Random event generation
- Configurable hit patterns and noise
- Simulated timing measurements
- No actual GPIO or hardware dependencies

### Hardware Mode (Future)
The real hardware implementation will interface with:
- Raspberry Pi GPIO pins
- Time-to-Digital Converters (TDCs)
- Scintillator-based trigger system
- 96 individual drift tube readouts

## Required Hardware Components

### Primary Hardware
- **Raspberry Pi 4** (recommended for processing power)
- **96 TDC channels** for precise timing measurements
- **GPIO expansion boards** for tube addressing
- **Scintillator trigger system** with PMT readout
- **Power distribution system** for tube high voltages
- **Signal conditioning electronics**

### Connectivity Requirements
- **SPI/I2C interfaces** for TDC communication
- **Digital I/O pins** for tube selection and control
- **Analog input** for trigger threshold setting
- **Serial communication** for external monitoring (optional)

## Code Modifications Required

### 1. DetectorHardware.py - Complete Overhaul

The `DetectorHardware` class requires substantial modifications:

#### Functions to Implement:
```python
def __init__(self):
    """Initialize GPIO pins and TDC interfaces"""
    # Remove simulation flags
    # Initialize RPi.GPIO or gpiozero
    # Setup SPI/I2C for TDC communication
    # Configure trigger input pin
    # Initialize tube selection multiplexers
    
def check_trigger(self) -> bool:
    """Read actual trigger pin state"""
    # Replace simulation with GPIO.input(TRIGGER_PIN)
    # Implement debouncing if necessary
    # Return True when scintillator fires
    
def read_tube_data(self, tube_number: int, post_arm: bool = True):
    """Read TDC data from specified tube"""
    # Select tube via multiplexer/address lines
    # Read TDC registers via SPI/I2C
    # Parse timing data (TOF/TOT)
    # Handle communication errors
    # Return (-1) for no-hit or (tof, tot) for valid hits
    
def arm_TDC(self, tube_number: int):
    """Reset and arm TDC for next measurement"""
    # Send arm command to specific TDC channel
    # Clear previous measurement data
    # Set TDC to ready state
    
def reset_trigger(self):
    """Reset trigger system for next event"""
    # Clear trigger latch
    # Reset any timing circuits
    # Prepare for next scintillator pulse
```

#### New Functions to Add:
```python
def initialize_tdcs(self):
    """Initialize all TDC channels with proper configuration"""
    
def set_tube_voltage(self, tube_number: int, voltage: float):
    """Set high voltage for drift tube (if software controlled)"""
    
def get_system_status(self) -> dict:
    """Return hardware health and status information"""
    
def calibrate_timing(self):
    """Run timing calibration sequence"""
```

#### Functions to Remove:
- `generate_event()` - No longer needed
- `_generate_adjacent_hits()` - Hardware will provide real hits
- `_generate_chamber_track()` - Real tracks from cosmic rays
- All simulation-related code and parameters

### 2. DetectorController.py - Minor Modifications

#### Changes Required:
```python
def __init__(self, output_file: str = "detector_events.json"):
    # Remove simulation-specific initialization
    # Add hardware health checking
    # Initialize calibration parameters
    
def process_event(self) -> Optional[EventData]:
    """Process a single triggered event"""
    # Remove TODO comment and generate_event() call
    # Add error handling for hardware communication failures
    # Implement timeout handling for TDC readouts
    # Add data validation checks
```

#### New Methods to Add:
```python
def run_calibration(self):
    """Run system calibration routine"""
    
def check_hardware_health(self) -> bool:
    """Verify all hardware components are responding"""
    
def handle_communication_error(self, error_type: str, details: str):
    """Handle and log hardware communication errors"""
```

### 3. Reconstruction.py - Calibration Updates

#### Functions to Modify:
```python
def calibrated_radius(self, tof: float, tot: float) -> float:
    """Convert time measurements to drift radius"""
    # Replace placeholder with real calibration function
    # Use lookup tables or polynomial fits from calibration data
    # Account for temperature and pressure corrections
    # Handle out-of-range measurements gracefully
```

#### New Calibration Methods:
```python
def load_calibration_data(self, calibration_file: str):
    """Load calibration constants from file"""
    
def update_environmental_corrections(self, temperature: float, pressure: float):
    """Apply environmental corrections to drift calculations"""
```

### 4. Hardware Configuration Files

Create new configuration management:

#### config/hardware_config.json:
```json
{
  "gpio_pins": {
    "trigger_input": 18,
    "address_lines": [19, 20, 21, 22, 23, 24],
    "tdc_spi_cs": [8, 9, 10, 11],
    "status_led": 25
  },
  "timing": {
    "tdc_timeout_us": 100,
    "trigger_debounce_ms": 10,
    "acquisition_delay_us": 5
  },
  "calibration": {
    "drift_velocity_mm_per_ns": 0.055,
    "tube_radius_mm": 15.0,
    "calibration_file": "calibration_data.json"
  }
}
```

## Installation Requirements

### Hardware Dependencies
```bash
# GPIO control
sudo apt-get install python3-rpi.gpio
pip install gpiozero

# SPI communication
sudo apt-get install python3-spidev
pip install spidev

# I2C communication (if needed)
sudo apt-get install python3-smbus
pip install smbus2
```

### System Configuration
```bash
# Enable SPI interface
sudo raspi-config
# Navigate to Interfacing Options -> SPI -> Enable

# Enable I2C interface (if needed)
sudo raspi-config  
# Navigate to Interfacing Options -> I2C -> Enable

# Set GPIO permissions
sudo usermod -a -G gpio $USER
```

## Testing Strategy

### Phase 1: Basic Hardware Communication
1. Test GPIO trigger input functionality
2. Verify TDC communication protocols
3. Test tube selection mechanisms
4. Validate timing measurement accuracy

### Phase 2: Single Tube Testing
1. Test individual tube readouts
2. Validate TOF/TOT measurements
3. Test trigger-to-readout timing
4. Verify data consistency

### Phase 3: Multi-Tube Integration
1. Test simultaneous readouts
2. Validate event reconstruction
3. Test system performance under load
4. Calibrate timing relationships

### Phase 4: Full System Validation
1. Compare with simulation results
2. Validate track reconstruction accuracy
3. Test long-term stability
4. Performance optimization

## Debugging and Diagnostics

### Hardware Debug Tools
```python
class HardwareDebugger:
    def test_all_tubes(self):
        """Test each tube for basic functionality"""
        
    def measure_trigger_timing(self):
        """Measure trigger response characteristics"""
        
    def validate_tdc_accuracy(self):
        """Test TDC timing accuracy with known delays"""
        
    def check_signal_integrity(self):
        """Verify signal quality and noise levels"""
```

### Common Hardware Issues
- **TDC communication failures**: Check SPI/I2C connections and timing
- **Missing triggers**: Verify scintillator PMT power and thresholds
- **Inconsistent timing**: Check clock distribution and TDC calibration
- **GPIO conflicts**: Ensure no pin conflicts with other system services

## Calibration Procedures

### Timing Calibration
1. Use precision delay generators for TDC calibration
2. Measure system response with known cosmic ray sources
3. Cross-calibrate between chambers using through-going tracks
4. Account for cable delays and electronic delays

### Spatial Calibration
1. Use alignment fixtures during detector assembly
2. Survey tube positions with precision measurement tools
3. Validate alignment using reconstructed straight tracks
4. Correct for any systematic position offsets

## Performance Expectations

### Real Hardware vs. Simulation
- **Event rates**: Expect ~1-10 events/minute (cosmic ray rate)
- **Hit multiplicities**: Typically 4-8 hits per event
- **Reconstruction efficiency**: Target >95% for good tracks
- **Timing resolution**: ~1-2 ns with proper TDCs

### System Resources
- **CPU usage**: <20% on Raspberry Pi 4
- **Memory usage**: <100MB typical
- **Storage**: ~1MB per hour of data
- **Power consumption**: <10W total system

## Backup and Recovery

### Configuration Backup
- Regularly backup calibration constants
- Version control hardware configuration files
- Document hardware modifications and repairs

### Error Recovery
- Implement watchdog timers for hung processes
- Automatic restart procedures for communication failures
- Graceful degradation when tubes are offline

## Migration Checklist

- [ ] Procure and test all hardware components
- [ ] Modify DetectorHardware.py for GPIO/TDC interface
- [ ] Update calibrated_radius() function with real calibration
- [ ] Create hardware configuration management system
- [ ] Implement comprehensive error handling
- [ ] Develop hardware testing and diagnostic tools
- [ ] Validate timing accuracy and calibration procedures
- [ ] Test full system integration and performance
- [ ] Document hardware-specific operating procedures
- [ ] Train operators on hardware-mode operation

## Future Enhancements

### Potential Upgrades
- **Multi-threading**: Parallel TDC readouts for faster processing
- **Real-time filtering**: Hardware-based event selection
- **Remote monitoring**: Web-based system status interface
- **Automated calibration**: Periodic self-calibration routines
- **Advanced triggering**: Coincidence requirements between chambers
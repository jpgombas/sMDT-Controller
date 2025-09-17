# Hardware Integration Guide

This document outlines the transition from simulation to real hardware operation for the muon detector control system.

## Code Modifications Required

### 1. DetectorHardware.py - Complete Overhaul

The `DetectorHardware` class requires substantial modifications:

#### Functions to Implement:
```python
def __init__(self):
    """Initialize GPIO pins and TDC interfaces"""
    # Remove simulation flags
    # Initialize RPi.GPIO or gpiozero
    # Setup SPI for TDC communication
    # Configure trigger input pin
    # Initialize tube selection multiplexers
    
def check_trigger(self) -> bool:
    """Read actual trigger pin state"""
    # Replace simulation with GPIO.input(TRIGGER_PIN)
    # Return True when TRIGGER_PIN is HIGH
    
def read_tube_data(self, tube_number: int, post_arm: bool = True):
    """Read TDC data from specified tube"""
    # Select tube via shift-register address line
    # Read TDC registers via common SPI line
    # Parse timing data (Time of FLight/Time over Threshold)
    # Return (-1) for no-hit or (tof, tot) for valid hits
    
def arm_TDC(self, tube_number: int):
    """Reset and arm TDC for next measurement"""
    # Send reset command to specific TDC channel
    
def reset_trigger(self):
    """Reset trigger system for next event"""
    # Write HIGH to TRIGGER_RESET line
```

#### New Functions that could be added:
```python
def initialize_tdcs(self):
    """Initialize all TDC channels with proper configuration"""
    
def set_tube_voltage(self, tube_number: int, voltage: float):
    """Set high voltage for drift tube (if software controlled)"""
```

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

### 3. Reconstruction.py - Calibration Updates

#### Functions to Modify:
```python
def calibrated_radius(self, tof: float, tot: float) -> float:
    """Convert time measurements to drift radius"""
    # Replace placeholder with real calibration function
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

## Migration Checklist

- [ ] Procure and test all hardware components
- [ ] Modify DetectorHardware.py for GPIO/TDC interface
- [ ] Update calibrated_radius() function with real calibration
- [ ] Test full system integration and performance

## Future Enhancements

### Potential Upgrades
- **Toggle Simulation On/Off**: Ability to switch on/off real data vs simulation
- **Automated calibration**: Periodic self-calibration routines
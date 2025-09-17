# Muon Detector Control System

A comprehensive control and data acquisition system for a dual-chamber muon drift tube detector designed for cosmic ray detection and particle physics research.

## Overview

This system controls and monitors a 96-tube muon detector consisting of two chambers arranged perpendicular to each other. The detector uses drift tubes to measure muon trajectories and provides real-time reconstruction and visualization capabilities.

### Detector Configuration

- **Total tubes**: 96 (indexed 0-95)
- **Chamber layout**: 2 chambers × 4 layers × 12 tubes per layer
- **Chamber orientation**: Chamber 1 measures X-Z plane, Chamber 2 measures Y-Z plane (rotated 90°)
- **Trigger system**: Scintillator-based time-of-flight trigger
- **Data collection**: Time-of-flight (TOF) and time-over-threshold (TOT) measurements

## System Architecture

The system follows a modular design with clear separation of concerns:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   DetectorGUI   │    │ DetectorControl  │    │ DetectorHardwar │
│   (Interface)   │◄──►│    (Logic)       │◄──►│   (Hardware)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Reconstruction │    │   EventData     │
                       │  (Analysis)     │    │  (Data Model)   │
                       └─────────────────┘    └─────────────────┘
```

## Core Components

### 1. DetectorController (DetectorController.py)
The main orchestrator that:
- Manages the acquisition loop
- Coordinates hardware interactions
- Processes events and triggers reconstruction
- Handles data logging and statistics
- Provides thread-safe queues for GUI communication

### 2. DetectorHardware (DetectorHardware.py)
Hardware abstraction layer that:
- Interfaces with GPIO pins (future implementation)
- Manages TDC (Time-to-Digital Converter) operations
- Handles trigger detection and reset
- Provides simulation mode for development and testing

### 3. Reconstruction (Reconstruction.py)
Advanced track reconstruction engine that:
- Fits lines through hit patterns in both chambers
- Converts chamber angles to spherical coordinates
- Generates visualization plots
- Calculates drift radii from timing measurements

### 4. EventData (EventData.py)
Data container that:
- Stores hit information with chamber/layer mapping
- Manages event metadata and timestamps
- Provides JSON serialization for data storage

### 5. DetectorGUI (DetectorGUI.py)
User interface that:
- Provides start/stop controls for data acquisition
- Displays real-time statistics and event logs
- Shows live reconstruction plots for both chambers
- Maintains responsive threading for smooth operation

### 6. Main Entry Point (run.py)
Application launcher supporting:
- GUI mode for interactive operation
- Headless mode for automated data collection
- Command-line configuration options

## Installation and Setup

### Requirements
```bash
pip install numpy scipy matplotlib pillow tkinter
```

### Running the System

**GUI Mode:**
```bash
python run.py
```

**Headless Mode:**
```bash
# Run indefinitely
python run.py --headless --output my_data.json

# Run for specific duration
python run.py --headless --duration 3600 --output hour_run.json
```

## Data Format

Events are saved as newline-delimited JSON with the following structure:

```json
{
  "event_id": 123,
  "timestamp": "2025-01-15T14:30:00.123456",
  "hit_count": 8,
  "hits": [
    {
      "tube_number": 15,
      "chamber": 0,
      "layer": 1,
      "tube_in_layer": 3,
      "time_of_flight": 45.6,
      "time_over_threshold": 12.3
    }
  ]
}
```

## Current Status: Simulation Mode

The system currently operates in simulation mode while hardware development is ongoing. The simulation includes:

- **Track generation**: Creates muon-like tracks across both chambers
- **Noise modeling**: Simulates adjacent hits and detection efficiency
- **Configurable parameters**: Hit probability, track angles, chamber efficiency
- **Event timing**: Semi-realistic trigger rates and processing delays

## Key Features

### Real-time Reconstruction
- Simultaneous track fitting in both detector chambers
- Conversion from chamber angles to 3D spherical coordinates
- Visual feedback with matplotlib-generated plots

### Thread-Safe Design
- Separate acquisition thread prevents GUI freezing
- Queue-based communication between threads
- Proper resource cleanup on shutdown

### Comprehensive Statistics
- Event rates and processing statistics
- Hit distribution analysis
- Reconstruction success rates
- Runtime monitoring

### Flexible Operation Modes
- Interactive GUI for development and monitoring
- Headless mode for automated data collection
- Configurable output formats and durations

## Future Hardware Integration

See [HARDWARE_INTEGRATION.md](HARDWARE_INTEGRATION.md) for detailed information about transitioning from simulation to real hardware operation.

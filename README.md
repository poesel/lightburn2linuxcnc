# LightBurn to LinuxCNC Bridge (l2l)

A Python-based TCP server that acts as a bridge between LightBurn (laser cutting software) and LinuxCNC (CNC machine control software). This program simulates a GRBL-controlled machine for LightBurn while capturing and storing G-code programs for use with LinuxCNC.

## Features

- **GRBL Simulation**: Presents itself as a GRBL 1.1f controller to LightBurn
- **G-Code Capture**: Receives and stores G-code programs from LightBurn
- **Status Monitoring**: Real-time connection status with visual indicators
- **Program Management**: 
  - Automatic backup creation with timestamps
  - Program viewer in separate window
  - Clean program status display
- **Internationalization**: Prepared for multi-language support (German/English)
- **Robust Connection Handling**: Proper socket management and port reuse

## Requirements

- Python 3.6 or higher
- tkinter (usually included with Python)
- Linux system with LinuxCNC (for the target use case)

## Installation

1. Clone or download the repository
2. Ensure Python 3.6+ is installed
3. No additional dependencies required (uses only standard library)

## Usage

### Starting the Program

```bash
python3 lightburn2linuxcnc.py
```

### Configuration

The program uses these default settings (can be modified in the code):
- **Host**: 0.0.0.0 (accepts connections from any IP)
- **Port**: 23 (standard telnet port)
- **Log File**: `lightburn_log.txt`
- **Program File**: `lightburn_program.ngc`

### LightBurn Setup

1. In LightBurn, go to **Machine Settings**
2. Set **Connection Type** to **Network**
3. Enter the IP address of the computer running this bridge
4. Set **Port** to **23**
5. Set **Controller** to **GRBL**

### Program Interface

The main window displays:
- **Status Section**: Connection status and program reception status
- **Status Light**: Visual indicator (gray=waiting, green=connected, red=error)
- **Action Buttons**:
  - **Create Backup**: Creates timestamped backup of current program
  - **Current Program**: Opens program viewer window
  - **Quit**: Safely closes the program

### Program Viewer

Click **"Current Program"** to open a separate window showing:
- Complete G-code program content
- Read-only display
- Close button to return to main window

## File Structure

```
lightburn2linuxcnc/
├── lightburn2linuxcnc.py    # Main program
├── lightburn_log.txt        # Communication log (created automatically)
├── lightburn_program.ngc    # Current G-code program (created automatically)
├── lightburn_program_YYYYMMDD_HHMMSS.ngc  # Backup files (created on demand)
└── README.md               # This file
```

## How It Works

1. **Server Startup**: Program starts TCP server on port 23
2. **LightBurn Connection**: LightBurn connects and receives GRBL identification
3. **G-Code Reception**: Program receives G-code commands from LightBurn
4. **Status Simulation**: Responds with appropriate GRBL status messages
5. **File Storage**: Saves G-code to `lightburn_program.ngc`
6. **Program Completion**: LightBurn receives completion status

## Status Messages

- **"Receiving program..."**: Displayed when first G-code command arrives
- **"Program received"**: Displayed when connection ends (program complete)

## Backup System

- **Automatic**: Program file is always updated with latest G-code
- **Manual**: Click **"Create Backup"** to create timestamped copy
- **Format**: `lightburn_program_YYYYMMDD_HHMMSS.ngc`

## Troubleshooting

### Port Already in Use
- The program includes proper socket cleanup
- If you get "address already in use", wait a few seconds and try again
- The program uses `SO_REUSEADDR` to allow immediate restart

### Connection Issues
- Ensure firewall allows connections on port 23
- Check that LightBurn is configured for the correct IP address
- Verify network connectivity between LightBurn and bridge computer

### Program Not Receiving
- Check status light (should be green when connected)
- Verify LightBurn is sending to correct IP/port
- Check log file for error messages

## Development

### Internationalization
The program is prepared for internationalization:
- Translation dictionaries for German and English
- `get_text()` function for text retrieval
- Easy to add new languages

### Extending Functionality
- Add new buttons in the button frame
- Extend GCodeServer class for additional commands
- Modify status display for custom information

## License

This project is open source. See LICENSE file for details.

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve the program.

## Version History

- **v1.0**: Initial release with basic GRBL simulation and G-code capture
- Features: TCP server, status monitoring, backup system, program viewer

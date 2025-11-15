# SSD1681 E-Paper Display Driver for MicroPython

A MicroPython driver for SSD1681-based e-paper displays with support for 3-color displays (black/white/red).

## Features

- Support for multiple orientations (0°, 90°, 180°, 270°)
- Text rendering with scalable fonts
- Pixel-level drawing control
- Three-color support (black, white, red)
- Configurable display dimensions

## Hardware Tested

- Waveshare 1.54" e-Paper Display Module (200x200 pixels)
- Raspberry Pi Pico/Pico W

## Quick Start

```python
from ssd1681_driver import create_display, COLOR_BLACK, COLOR_RED

# Initialize display
display = create_display(cs_pin=17, dc_pin=16, rst_pin=20, busy_pin=21)
display.init()

# Draw text and shapes
display.text("Hello World!", 10, 10, color=COLOR_BLACK, font_size=2)
display.pixel(50, 50, COLOR_RED)

# Update display
display.show()
```

## Files

- `ssd1681_driver.py` - Main driver
- `ssd1681_driver_fonts.py` - Font data
- `example_ssd1681.py` - Demo/example code

## Contributing

This driver was developed as a personal learning project. While comments and suggestions are welcome, please note no active development or support is planned. Feel free to fork and modify for your own needs!

## License

MIT License - see LICENSE file for details.
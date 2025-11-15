# SSD1681 E-Paper Display Driver for MicroPython for 4-wire SPI interface
# Developed with assistance from GitHub Copilot

## Tested Hardware ##
# Waveshare 1.54" e-Paper Display Module (B)** - 200x200 pixels, Red/Black/White
# Raspberry Pi Pico (W)
# Other SSD1681-based displays should work with pin configuration adjustments

from machine import Pin, SPI
import time
from b_torp_temp_display.ssd1681_driver_fonts import FONT_8X8

# SSD1681 Command Constants
CMD_SW_RESET = 0x12
CMD_GATE_DRIVING_VOLTAGE = 0x01
CMD_DATA_ENTRY_MODE = 0x11
CMD_SET_RAM_X_RANGE = 0x44
CMD_SET_RAM_Y_RANGE = 0x45
CMD_SET_RAM_X_COUNTER = 0x4E
CMD_SET_RAM_Y_COUNTER = 0x4F
CMD_WRITE_RAM_BW = 0x24
CMD_WRITE_RAM_RED = 0x26
CMD_LOAD_LUT = 0x22
CMD_ACTIVATE_DISPLAY = 0x20
CMD_DISPLAY_UPDATE = 0x22
CMD_MASTER_ACTIVATE = 0x20
CMD_DEEP_SLEEP = 0x10
CMD_SOFT_START = 0x0C

# Display update modes
UPDATE_MODE_FULL = 0xF7  # Full update with temperature measurement

# Data entry modes
DATA_ENTRY_MODE_DEFAULT = 0x03  # X increment, Y increment

# Color constants
COLOR_WHITE = 0
COLOR_BLACK = 1
COLOR_RED = 2

# Display orientation constants
ORIENTATION_0 = 0    # Board text bottom-right (connector at bottom)
ORIENTATION_90 = 1   # Board text bottom-left (connector at left)
ORIENTATION_180 = 2  # Board text top-left (connector at top)
ORIENTATION_270 = 3  # Board text top-right (connector at right)

class SSD1681:
    
    def __init__(self, spi, cs, dc, rst, busy, width=200, height=200, orientation=ORIENTATION_0):
        self.spi = spi
        self.cs = cs
        self.dc = dc
        self.rst = rst
        self.busy = busy
        self.width = width
        self.height = height
        self.orientation = orientation
        
        # Initialize buffers
        self._buffer_size = width * height // 8
        self.buffer = bytearray([0xFF] * self._buffer_size)  # White background
        self.red_buffer = bytearray([0x00] * self._buffer_size)  # No red initially
        
        # Initialize pins
        self._init_pins()
    
    def _init_pins(self):
        """Initialize GPIO pins"""
        self.cs.init(Pin.OUT, value=1)
        self.dc.init(Pin.OUT, value=0)
        self.rst.init(Pin.OUT, value=1)
        self.busy.init(Pin.IN, Pin.PULL_UP)
    
    def _command(self, cmd, data=None):
        """Send command to display"""
        self.dc.value(0)  # Command mode
        self.cs.value(0)
        self.spi.write(bytearray([cmd]))
        self.cs.value(1)
        time.sleep_ms(1)
        
        if data is not None:
            self._data(data)
    
    def _data(self, data):
        """Send data to display"""
        self.dc.value(1)  # Data mode
        self.cs.value(0)
        if isinstance(data, (list, tuple)):
            self.spi.write(bytearray(data))
        elif isinstance(data, (bytes, bytearray)):
            self.spi.write(data)
        else:
            self.spi.write(bytearray([data]))
        self.cs.value(1)
        time.sleep_ms(1)
    
    def _wait_busy(self, timeout_ms=15000):
        """Wait for display to be ready"""
        start = time.ticks_ms()
        while self.busy.value() and (time.ticks_diff(time.ticks_ms(), start) < timeout_ms):
            time.sleep_ms(50)
        return time.ticks_diff(time.ticks_ms(), start) < timeout_ms
    
    def _reset_ram_address(self):
        """Reset RAM address counters to origin"""
        self._command(CMD_SET_RAM_X_COUNTER, [0x00])
        self._command(CMD_SET_RAM_Y_COUNTER, [0x00, 0x00])
    
    def _map_coordinates(self, x, y):
        """Map user coordinates to display memory layout for pixels"""
        # Apply orientation transformation
        if self.orientation == ORIENTATION_0:
            # Board text bottom-right (connector at bottom) - our established working orientation
            hw_x = self.width - 1 - x
            hw_y = self.height - 1 - y
        elif self.orientation == ORIENTATION_90:
            # Board text bottom-left (connector at left)
            hw_x = y
            hw_y = self.width - 1 - x
        elif self.orientation == ORIENTATION_180:
            # Board text top-left (connector at top)
            hw_x = x
            hw_y = y
        elif self.orientation == ORIENTATION_270:
            # Board text top-right (connector at right)
            hw_x = self.height - 1 - y
            hw_y = x
        else:
            # Default to ORIENTATION_0
            hw_x = self.width - 1 - x
            hw_y = self.height - 1 - y
        
        # Standard row-major layout
        byte_index = (hw_y * self.width + hw_x) // 8
        bit_index = hw_x % 8
        return byte_index, bit_index
    
    def _set_pixel_buffer(self, x, y, buffer, value):
        """
        Set a pixel in the specified buffer
        
        Args:
            x: X coordinate
            y: Y coordinate
            buffer: Target buffer (self.buffer or self.red_buffer)
            value: True to set bit, False to clear bit
        """
        if not (0 <= x < self.width and 0 <= y < self.height):
            return
            
        byte_index, bit_index = self._map_coordinates(x, y)
        if value:
            buffer[byte_index] |= (0x80 >> bit_index)
        else:
            buffer[byte_index] &= ~(0x80 >> bit_index)
    
    def reset(self):
        """Hardware reset sequence"""
        self.rst.value(1)
        time.sleep_ms(200)
        self.rst.value(0)
        time.sleep_ms(10)
        self.rst.value(1)
        time.sleep_ms(200)
    
    def _power_on_sequence(self):
        """Power on and reset sequence"""
        self.reset()
        self._wait_busy()
        self._command(CMD_SW_RESET)
        self._wait_busy()
    
    def _configure_ram(self):
        """Configure RAM settings and addressing"""
        # Set gate driver output
        self._command(CMD_GATE_DRIVING_VOLTAGE, [0xC7, 0x00, 0x00])
        
        # Set display RAM size and data entry mode (dynamic based on display size)
        self._command(CMD_DATA_ENTRY_MODE, [DATA_ENTRY_MODE_DEFAULT])
        
        # Calculate RAM ranges based on actual display dimensions
        # X range: width in bytes (width // 8)
        x_end = (self.width // 8) - 1
        self._command(CMD_SET_RAM_X_RANGE, [0x00, x_end])
        
        # Y range: height in pixels
        y_end_low = (self.height - 1) & 0xFF
        y_end_high = ((self.height - 1) >> 8) & 0xFF
        self._command(CMD_SET_RAM_Y_RANGE, [0x00, 0x00, y_end_low, y_end_high])
        
        # Reset address counters
        self._reset_ram_address()
    
    def _load_lut(self):
        """Load Look-Up Table from OTP"""
        self._command(CMD_LOAD_LUT, [0xB1])
        self._command(CMD_ACTIVATE_DISPLAY)
        self._wait_busy()
    
    def init(self):
        """Initialize the display following official sequence"""
        self._power_on_sequence()
        self._configure_ram()
        self._load_lut()
        self._wait_busy()
    
    def clear(self):
        """Clear the display buffer (set to all white)"""
        # Set all bits to 1 since 1=white pixel in black/white buffer
        for i in range(self._buffer_size):
            self.buffer[i] = 0xFF
        # Clear red buffer (0=no red)
        for i in range(self._buffer_size):
            self.red_buffer[i] = 0x00
    
    def pixel(self, x, y, color=COLOR_BLACK):
        """
        Set a pixel in the buffer
        
        Args:
            x: X coordinate
            y: Y coordinate  
            color: COLOR_WHITE, COLOR_BLACK, or COLOR_RED
        """
        x, y = int(x), int(y)
        
        if color == COLOR_WHITE:
            # White: set bit in main buffer, clear red buffer
            self._set_pixel_buffer(x, y, self.buffer, True)
            self._set_pixel_buffer(x, y, self.red_buffer, False)
        elif color == COLOR_BLACK:
            # Black: clear bit in main buffer, clear red buffer
            self._set_pixel_buffer(x, y, self.buffer, False)
            self._set_pixel_buffer(x, y, self.red_buffer, False)
        elif color == COLOR_RED:
            # Red: set bit in main buffer (white background), set red buffer
            self._set_pixel_buffer(x, y, self.buffer, True)
            self._set_pixel_buffer(x, y, self.red_buffer, True)
    
    def text(self, string, x, y, color=COLOR_BLACK, font_size=1):
        """
        Draw text to the buffer
        
        Args:
            string: Text to draw
            x: X position (left edge)
            y: Y position (top edge)
            color: COLOR_WHITE, COLOR_BLACK, or COLOR_RED
            font_size: Scale factor for text (1=8x8, 2=16x16, etc.)
        """
        x, y = int(x), int(y)
        char_width = 8 * font_size
        
        for char_index, char in enumerate(string):
            char_x = x + (char_index * char_width)
            if char_x + char_width > self.width:
                break
            self._draw_char(char, char_x, y, color, font_size)
    
    def _draw_char(self, char, x, y, color, font_size=1):
        """Draw a single character with optional scaling - uses standard orientation"""
        char_data = FONT_8X8.get(char, FONT_8X8[' '])
        
        # Always render in standard orientation - let pixel() handle coordinate mapping
        for row in range(8):
            for col in range(8):
                # Standard character rendering (same as ORIENTATION_0 was doing)
                if char_data[7-col] & (1 << row):
                    # Draw scaled pixel block
                    for scale_row in range(font_size):
                        for scale_col in range(font_size):
                            pixel_x = x + (7 - col) * font_size + scale_col
                            pixel_y = y + row * font_size + scale_row
                            self.pixel(pixel_x, pixel_y, color)
    
    def show(self):
        """Update the display with buffer contents"""
        # Write black/white image data
        self._reset_ram_address()
        self._command(CMD_WRITE_RAM_BW, self.buffer)
        
        # Write red image data
        self._reset_ram_address()
        self._command(CMD_WRITE_RAM_RED, self.red_buffer)
        
        # Configure soft start and trigger display update
        self._command(CMD_SOFT_START, [0xD7, 0xD6, 0x9D])
        self._command(CMD_DISPLAY_UPDATE, [UPDATE_MODE_FULL])
        self._command(CMD_MASTER_ACTIVATE)
        
        # Wait for update completion
        self._wait_busy()
    
    def sleep(self):
        """Put display into deep sleep mode"""
        self._command(CMD_DEEP_SLEEP, [0x01])


def create_display(cs_pin=17, dc_pin=16, rst_pin=20, busy_pin=21, sck_pin=18, mosi_pin=19, orientation=ORIENTATION_0, width=200, height=200):
    """
    Create and return a configured SSD1681 display instance
    
    Args:
        cs_pin: Chip Select pin number (default: 17)
        dc_pin: Data/Command pin number (default: 16) 
        rst_pin: Reset pin number (default: 20)
        busy_pin: Busy status pin number (default: 21)
        sck_pin: SPI Clock pin number (default: 18)
        mosi_pin: SPI MOSI pin number (default: 19)
        orientation: Display orientation (default: ORIENTATION_0)
        width: Display width in pixels (default: 200)
        height: Display height in pixels (default: 200)
    
    Default wiring for Raspberry Pi Pico:
    VCC  → Pin 40 (VBUS - 5V) or Pin 36 (3V3)
    GND  → Pin 38 (GND) 
    DIN  → Pin 25 (GPIO 19 - MOSI)
    CLK  → Pin 24 (GPIO 18 - SCK)
    CS   → Pin 22 (GPIO 17)
    DC   → Pin 21 (GPIO 16)
    RST  → Pin 26 (GPIO 20)
    BUSY → Pin 27 (GPIO 21)
    """
    spi = SPI(0, baudrate=1000000, polarity=0, phase=0, sck=Pin(sck_pin), mosi=Pin(mosi_pin))
    
    return SSD1681(
        spi=spi,
        cs=Pin(cs_pin),
        dc=Pin(dc_pin), 
        rst=Pin(rst_pin),
        busy=Pin(busy_pin),
        orientation=orientation,
        width=width,
        height=height
    )
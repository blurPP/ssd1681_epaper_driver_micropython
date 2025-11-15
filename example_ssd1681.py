# SSD1681 driver demonstration
# Load this file to your Pico and run it to test your e-paper display
# Features: Dual demo runs with 20-second interval, text, shapes, and graphics
# Demo tested using a Waveshare 1.54" e-paper display (200x200, b/w/red)

from ssd1681_driver import create_display, COLOR_WHITE, COLOR_BLACK, COLOR_RED, ORIENTATION_0, ORIENTATION_90, ORIENTATION_180, ORIENTATION_270
import time

def draw_demo_content(display):
    """Draw the demo content on the display"""
    # Clear display buffer
    display.clear()
    
    # Draw text with different sizes and colors
    display.text("HELLO WORLD!", 10, 10, color=COLOR_BLACK, font_size=2)
    display.text("SSD1681: OK", 10, 40, color=COLOR_BLACK, font_size=2)
    display.text("TEMP: 25.3 C", 10, 100, color=COLOR_RED, font_size=2)
    
    # Draw a 20x20 black square below the TEMP line
    for x in range(10, 30):
        for y in range(130, 150):
            display.pixel(x, y, COLOR_BLACK)
    
    # Draw a 20x20 red square to the right of the black square
    for x in range(35, 55):
        for y in range(130, 150):
            display.pixel(x, y, COLOR_RED)
    
    # Draw a cross in the bottom right corner using black and red lines
    # Cross center at (175, 175), each arm 15 pixels long
    cross_center_x, cross_center_y = 175, 175
    cross_size = 15
    
    # Draw black horizontal line
    for x in range(cross_center_x - cross_size, cross_center_x + cross_size + 1):
        display.pixel(x, cross_center_y, COLOR_BLACK)
    
    # Draw red vertical line
    for y in range(cross_center_y - cross_size, cross_center_y + cross_size + 1):
        display.pixel(cross_center_x, y, COLOR_RED)
    
    # Add some smaller text
    display.text("BYE WORLD!", 10, 180, color=COLOR_RED, font_size=1)

def main():
    """Enhanced demo function with orientation change between demos"""
    print("Initializing SSD1681 display for enhanced demo.")
    
    # Create display instance with correct pin configuration (default orientation 0)
    display = create_display(cs_pin=17, dc_pin=16, rst_pin=20, busy_pin=21, orientation=ORIENTATION_0)
    
    # Initialize the display
    display.init()
    print("Display initialized successfully!")
    
    # First demo (0 degrees)
    print("Running Demo #1 (0 degrees orientation)...")
    draw_demo_content(display)
    print("Updating display...")
    display.show()
    print("Demo #1 complete! Check your display.")
    
    # 20 second sleep between demos
    print("Waiting 20 seconds before Demo #2...")
    time.sleep(20)
    
    # Create new display instance with 90-degree orientation
    print("Switching to 90-degree orientation for Demo #2...")
    display = create_display(cs_pin=17, dc_pin=16, rst_pin=20, busy_pin=21, orientation=ORIENTATION_90)
    display.init()
    
    # Second demo (90 degrees orientation)
    print("Running Demo #2 (90 degrees orientation)...")
    draw_demo_content(display)
    print("Updating display...")
    display.show()
    print("Demo #2 complete! Both demos finished.")
    
    # Put display to sleep to save power
    time.sleep(2)
    display.sleep()
    print("Display put to sleep mode.")

if __name__ == "__main__":
    main()

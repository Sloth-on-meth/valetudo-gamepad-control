
import aiohttp
import logging

class ValetudoTUI:
    """Handles the curses-based TUI."""

    def __init__(self, stdscr):
        self.stdscr = stdscr

    def draw_labels(self, robot_battery, speed_index, fan_state):
        self.stdscr.addstr(0, 0, "Valetudo TUI")
        self.stdscr.addstr(2, 0, f"Robot battery:     {robot_battery}%   ")
        self.stdscr.addstr(3, 0, f"Speed level:       {SPEED_LEVELS[speed_index]}    ")
        self.stdscr.addstr(4, 0, f"Fan mode:          {fan_state}       ")
        self.stdscr.addstr(6, 0, "X: Toggle fan mode")
        self.stdscr.addstr(7, 0, "Circle: Cycle speed")
        self.stdscr.addstr(8, 0, "Square: Play sound")
        self.stdscr.addstr(9, 0, "Triangle: Dock robot")
        self.stdscr.refresh()

    def draw_joystick(self, x_axis, y_axis):
        self.stdscr.addstr(11, 0, "Joystick X: [{:<20}] {:.2f} ".format("=" * int((x_axis + 1) * 10), x_axis))
        self.stdscr.addstr(12, 0, "Joystick Y: [{:<20}] {:.2f} ".format("=" * int((y_axis + 1) * 10), y_axis))
        self.stdscr.refresh()
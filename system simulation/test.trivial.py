import pygame
import random
import sys
import math

# Initialize pygame
pygame.init()

# Set frame rate
FPS = 60
cycle_time = 1 / FPS

# Global configurations
NUM_ROBOTS_X = 5
NUM_ROBOTS_Y = 8
NUM_WORKSTATIONS = 5
WORKSTATION_POSITIONS = [(1, 0), (1, 1), (0, 1), (-1, 0), (-1, 1)]
NUM_MACHINES_PER_WORKSTATION = 3
ROBOT_DIAMETER = 40  # Increase robot diameter

# Set screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 800
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Factory Simulation with Workstations, Main Gate, and Robots")

# Define colors
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_YELLOW = (255, 255, 0)
COLOR_GREEN = (0, 255, 0)
COLOR_LIGHT_GREY = (211, 211, 211)
COLOR_LIGHT_BLUE = (173, 216, 230)  # Light blue for processing and queue
COLOR_ORANGE = (255, 165, 0)  # Orange for output and occupied

# Define fonts
font = pygame.font.SysFont('consolas', 18)

# Define global time control for consumption rate
CONSUMPTION_RATE = 1 / 10  # 1/10 items per second
INPUT_FLOW_RATE = 1.5  # 2 items per second (for the main gate)
ROBOT_SPEED = 0.5  # Robot moves at 0.5 units per second

# Define the real-world bounds for the screen
WORLD_WIDTH = 3.0  # From -1.5 to 1.5
WORLD_HEIGHT = 2.0  # From -0.5 to 1.5

# Map real-world positions to screen coordinates
def map_to_screen(pos):
    screen_x = int((pos[0] + 1.5) / WORLD_WIDTH * SCREEN_WIDTH)
    screen_y = int((1.5 - pos[1]) / WORLD_HEIGHT * SCREEN_HEIGHT)
    return screen_x, screen_y

class Machine:
    def __init__(self, idx):
        self.idx = idx  # Machine index
        self.status = 'idle'
        self.timer = 0  # Timer for consumption
        self.total_busy_time = 0  # Track total time spent in busy state
        self.total_time = 0  # Track total active time

    def update(self):
        self.total_time += cycle_time  # Increment total time every update cycle
        if self.status == 'busy':
            self.timer += cycle_time
            self.total_busy_time += cycle_time  # Increment busy time only if the machine is busy
            if self.timer >= 1 / CONSUMPTION_RATE:
                self.status = 'occupied'  # Waiting to be picked up
                self.timer = 0

    def get_status_text(self):
        if self.status == 'busy':
            percentage_complete = int((self.timer / (1 / CONSUMPTION_RATE)) * 100)
            return f'M{self.idx}: Busy {percentage_complete:2d}%', COLOR_GREEN
        elif self.status == 'occupied':
            return f'M{self.idx}: Occupied', COLOR_ORANGE
        elif self.status == 'occupied (wait)':
            return f'M{self.idx}: Occupied (wait)', COLOR_ORANGE
        else:
            return f'M{self.idx}: Idle', COLOR_YELLOW

    def get_busy_ratio(self):
        # Return the busy ratio, avoid division by zero
        if self.total_time > 0:
            return self.total_busy_time / self.total_time
        else:
            return 0  # If no time has passed, busy ratio is 0


class Workstation:
    def __init__(self, pos, workstation_id):
        self.pos = pos
        self.workstation_id = workstation_id
        self.machines = [Machine(i) for i in range(NUM_MACHINES_PER_WORKSTATION)]  # Configurable number of machines
        self.queue = 0  # Shared input queue

    def update(self):
        # Machines take items from the shared queue if they are idle
        for machine in self.machines:
            if machine.status == 'idle' and self.queue > 0:
                machine.status = 'busy'
                self.queue -= 1
            machine.update()

    def get_mean_busy_ratio(self):
        # Calculate the mean busy ratio for all machines in this workstation
        total_busy_ratio = sum(machine.get_busy_ratio() for machine in self.machines)
        return total_busy_ratio / len(self.machines)

    def draw(self, screen):
        # Get the mean busy ratio of all machines in the workstation
        mean_busy_ratio = self.get_mean_busy_ratio()

        # Create the text for the workstation, with the first line being the workstation name
        workstation_text = [
            (f'workstation_{self.workstation_id}', COLOR_LIGHT_GREY)  # First line: workstation name
        ]

        # Add machine info to the text, with machine index included
        for machine in self.machines:
            status_text, color = machine.get_status_text()
            workstation_text.append((status_text, color))

        # Display the mean busy ratio of the machines in this workstation
        workstation_text.append((f'Busy Ratio:{mean_busy_ratio * 100:3.0f}%', COLOR_LIGHT_BLUE))
        workstation_text.append((f'Queue: {self.queue}', COLOR_LIGHT_BLUE))

        # Draw the text box at the designated position
        box_pos = map_to_screen(self.pos)
        if self.pos[1] == 1:  # For top workstations, bottom center aligned
            draw_text_box_bottom_center(screen, workstation_text, box_pos)
        else:  # For lower workstations, top center aligned
            draw_text_box_top_center(screen, workstation_text, box_pos)


class MainGate:
    def __init__(self, pos):
        self.pos = pos
        self.input_queue = 0
        self.total_input_items = 0  # Track total input items added to the system
        self.total_output_items = 0  # Track total output items delivered to the output gate
        self.processing = 0
        self.output_count = 0  # Count for output
        self.input_rate = INPUT_FLOW_RATE  # 2 items per second (configured globally)
        self.start_time = 0  # To track elapsed time

    def update(self):
        # Add items to input queue at a rate of 2 items per second
        if self.start_time == 0:
            self.start_time = pygame.time.get_ticks()  # Initialize start time during the first update

        new_input_items = self.input_rate * cycle_time  # Items added per cycle
        self.input_queue += new_input_items
        self.total_input_items += new_input_items  # Accumulate total input items

    def get_elapsed_minutes(self):
        # Calculate elapsed time in minutes
        elapsed_time_ms = pygame.time.get_ticks() - self.start_time
        return elapsed_time_ms / 1000 / 60  # Convert milliseconds to minutes

    def get_output_rate(self):
        # Calculate output rate as total output items divided by total elapsed time
        elapsed_minutes = self.get_elapsed_minutes()
        if elapsed_minutes > 0:
            return self.total_output_items / elapsed_minutes
        else:
            return 0  # Avoid division by zero

    def get_input_rate(self):
        # Calculate input rate as total input items divided by total elapsed time
        elapsed_minutes = self.get_elapsed_minutes()
        if elapsed_minutes > 0:
            return self.total_input_items / elapsed_minutes
        else:
            return 0  # Avoid division by zero

    def draw(self, screen):
        # Create the text for the main gate, with the first line being the name
        main_gate_text = [
            (f'Main Gate', COLOR_LIGHT_GREY),  # First line: Main Gate name
            (f'Output: {self.output_count}', COLOR_LIGHT_BLUE),  # Second line with orange background for output
            (f'Output: {self.get_output_rate():.0f} /min', COLOR_LIGHT_BLUE),  # New output rate line
            (f'Input: {self.get_input_rate():.0f} /min', COLOR_LIGHT_BLUE),  # New input rate line
            (f'Processing: {self.processing}', COLOR_LIGHT_BLUE),  # Third line with light blue background
            (f'Queue: {int(self.input_queue)}', COLOR_LIGHT_BLUE)  # Fourth line with light blue background, showing integer queue
        ]

        # Draw the text box at the designated position, top center aligned
        box_pos = map_to_screen(self.pos)
        draw_text_box_top_center(screen, main_gate_text, box_pos)

    def increment_output_count(self):
        self.output_count += 1  # Increment the number of output items
        self.processing -= 1
        self.total_output_items += 1  # Track total output items for output rate calculation


# Robot X class that moves items from the input gate to random workstations
class RobotX:
    def __init__(self, workstations, main_gate):
        self.pos = (0, 0)  # Start at the main gate in real-world coordinates
        self.target = None
        self.workstations = workstations
        self.main_gate = main_gate
        self.speed = ROBOT_SPEED
        self.carrying_item = False
        self.status = 'idle'
        self.returning = False  # Flag indicating whether the robot is returning to the gate
        self.distance_traveled = 0  # Track percentage of distance traveled

    def update(self, screen):
        if not self.carrying_item and not self.returning and self.main_gate.input_queue > 0:
            # If robot is idle and there's an item at the input gate, pick it up
            self.target = random.choice(self.workstations)
            self.carrying_item = True
            self.main_gate.input_queue -= 1
            self.main_gate.processing += 1
            self.status = 'busy'
            self.returning = False
            self.distance_traveled = 0
        elif self.carrying_item:
            # Move to the workstation and deliver the item
            dx, dy = self.target.pos[0] - self.pos[0], self.target.pos[1] - self.pos[1]
            dist = math.sqrt(dx**2 + dy**2)
            if dist > 0:
                travel_fraction = min(1, self.speed * cycle_time / dist)  # Fraction of distance traveled this cycle
                self.pos = (self.pos[0] + dx * travel_fraction, self.pos[1] + dy * travel_fraction)
                self.distance_traveled = min(self.distance_traveled + travel_fraction * 100, 100)  # Cap at 100%

            if dist <= self.speed * cycle_time:
                self.pos = self.target.pos  # Snap to workstation
                self.target.queue += 1
                self.carrying_item = False
                self.returning = True
                self.distance_traveled = 0
        elif self.returning:
            # Return to the input gate
            dx, dy = self.main_gate.pos[0] - self.pos[0], self.main_gate.pos[1] - self.pos[1]
            dist = math.sqrt(dx**2 + dy**2)
            if dist > 0:
                travel_fraction = min(1, self.speed * cycle_time / dist)
                self.pos = (self.pos[0] + dx * travel_fraction, self.pos[1] + dy * travel_fraction)
                self.distance_traveled = min(self.distance_traveled + travel_fraction * 100, 100)  # Cap at 100%

            if dist <= self.speed * cycle_time:
                self.pos = self.main_gate.pos  # Snap to input gate
                self.status = 'idle'
                self.returning = False
                self.distance_traveled = 0

        # Draw the robot with percentage of distance traveled
        self.draw(screen)

    def draw(self, screen):
        color = COLOR_GREEN if self.status == 'busy' else COLOR_YELLOW
        screen_pos = map_to_screen(self.pos)
        pygame.draw.circle(screen, color, screen_pos, ROBOT_DIAMETER // 2)
        # Display percentage of distance traveled on robot
        percentage_text = font.render(f'{int(self.distance_traveled)}%', True, COLOR_BLACK)
        screen.blit(percentage_text, (screen_pos[0] - 15, screen_pos[1] - 35))
        # Mark 'X' on the robot for Robot X
        robot_mark_text = font.render('X', True, COLOR_BLACK)
        screen.blit(robot_mark_text, (screen_pos[0] - 8, screen_pos[1] - 8))

# Robot Y class for output item transfer
class RobotY:
    def __init__(self, workstations, main_gate):
        self.pos = (0, 0)  # Start at the output gate in real-world coordinates
        self.target_machine = None
        self.workstations = workstations
        self.main_gate = main_gate
        self.speed = ROBOT_SPEED
        self.carrying_item = False
        self.status = 'idle'
        self.target = None  # New target, could be a workstation or the output gate
        self.distance_traveled = 0  # Track percentage of distance traveled

    def update(self, screen):
        # Check if any machine has a finished item (status: 'occupied') if not carrying any item
        if self.status == 'idle':
            for ws in self.workstations:
                for machine in ws.machines:
                    if machine.status == 'occupied':
                        machine.status = 'occupied (wait)'
                        self.target_machine = machine
                        self.target = ws.pos  # Set the target as the workstation's position
                        self.status = 'busy'
                        break

        elif self.status == 'busy' and not self.carrying_item and self.target_machine:
            # Move to the workstation (which represents the machine) to pick up the item
            dx, dy = self.target[0] - self.pos[0], self.target[1] - self.pos[1]
            dist = math.sqrt(dx**2 + dy**2)
            if dist > 0:
                travel_fraction = min(1, self.speed * cycle_time / dist)  # Fraction of distance traveled this cycle
                self.pos = (self.pos[0] + dx * travel_fraction, self.pos[1] + dy * travel_fraction)
                self.distance_traveled = min(self.distance_traveled + travel_fraction * 100, 100)  # Cap at 100%

            if dist <= self.speed * cycle_time:
                # Robot reaches the workstation (machine)
                self.pos = self.target  # Snap to workstation position
                self.target_machine.status = 'idle'  # Machine becomes idle
                self.target_machine = None  # Clear target machine
                self.carrying_item = True  # Robot now carries the item
                self.target = self.main_gate.pos  # Set target to the output gate
                self.distance_traveled = 0  # Reset distance traveled

        elif self.status == 'busy' and self.carrying_item:
            # Move to the output gate
            dx, dy = self.target[0] - self.pos[0], self.target[1] - self.pos[1]
            dist = math.sqrt(dx**2 + dy**2)
            if dist > 0:
                travel_fraction = min(1, self.speed * cycle_time / dist)
                self.pos = (self.pos[0] + dx * travel_fraction, self.pos[1] + dy * travel_fraction)
                self.distance_traveled = min(self.distance_traveled + travel_fraction * 100, 100)  # Cap at 100%

            if dist <= self.speed * cycle_time:
                # Robot reaches the output gate
                self.pos = self.main_gate.pos  # Snap to output gate
                self.main_gate.increment_output_count()
                self.carrying_item = False  # Robot is no longer carrying the item
                self.target_machine = None
                self.status = 'idle'  # Robot becomes idle
                self.distance_traveled = 0  # Reset distance traveled

        # Draw the robot
        self.draw(screen)

    def draw(self, screen):
        color = COLOR_GREEN if self.status == 'busy' else COLOR_YELLOW
        screen_pos = map_to_screen(self.pos)
        pygame.draw.circle(screen, color, screen_pos, ROBOT_DIAMETER // 2)
        percentage_text = font.render(f'{int(self.distance_traveled)}%', True, COLOR_BLACK)
        screen.blit(percentage_text, (screen_pos[0] - 15, screen_pos[1] - 35))
        # Mark 'Y' on the robot for Robot Y
        robot_mark_text = font.render('Y', True, COLOR_BLACK)
        screen.blit(robot_mark_text, (screen_pos[0] - 8, screen_pos[1] - 8))


# Draw text box function with colored background for each line, and with a black border around the box
def draw_text_box_bottom_center(screen, text_lines, position):
    max_width = 200
    line_height = 30
    padding = 10

    total_height = len(text_lines) * line_height + padding

    # Calculate the top left position to center the text box at the bottom center of the workstation or gate
    box_x = position[0] - max_width // 2
    box_y = position[1] - total_height  # Align the bottom of the text box with the position

    # Draw the black border around the text box
    pygame.draw.rect(screen, COLOR_BLACK, (box_x - 5, box_y - 5, max_width + 10, total_height + 10), 2)

    # Draw the text with background colors for each line and center the text
    for i, (text, bg_color) in enumerate(text_lines):
        line_surface = font.render(text, True, COLOR_BLACK)
        line_rect = pygame.Rect(box_x, box_y + i * line_height, max_width, line_height)
        pygame.draw.rect(screen, bg_color, line_rect)
        # Center the text inside the line
        text_rect = line_surface.get_rect(center=(line_rect.centerx, line_rect.centery))
        screen.blit(line_surface, text_rect)

# Draw text box function for top center alignment
def draw_text_box_top_center(screen, text_lines, position):
    max_width = 200
    line_height = 30
    padding = 10

    total_height = len(text_lines) * line_height + padding

    # Calculate the top left position to center the text box at the top center of the workstation or gate
    box_x = position[0] - max_width // 2
    box_y = position[1]  # Align the top of the text box with the position

    # Draw the black border around the text box
    pygame.draw.rect(screen, COLOR_BLACK, (box_x - 5, box_y - 5, max_width + 10, total_height + 10), 2)

    # Draw the text with background colors for each line and center the text
    for i, (text, bg_color) in enumerate(text_lines):
        line_surface = font.render(text, True, COLOR_BLACK)
        line_rect = pygame.Rect(box_x, box_y + i * line_height, max_width, line_height)
        pygame.draw.rect(screen, bg_color, line_rect)
        # Center the text inside the line
        text_rect = line_surface.get_rect(center=(line_rect.centerx, line_rect.centery))
        screen.blit(line_surface, text_rect)

# Main game loop function
def main():
    # Initialize workstations and main gate
    workstations = [Workstation(pos, i + 1) for i, pos in enumerate(WORKSTATION_POSITIONS)]
    main_gate = MainGate((0, 0))  # Main gate position at (0, 0)

    # Initialize Robot X and Robot Y objects
    robots_x = [RobotX(workstations, main_gate) for _ in range(NUM_ROBOTS_X)]
    robots_y = [RobotY(workstations, main_gate) for _ in range(NUM_ROBOTS_Y)]

    # Set frame rate
    clock = pygame.time.Clock()

    # Main game loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Clear screen
        screen.fill(COLOR_WHITE)

        # Update and draw workstations
        for workstation in workstations:
            workstation.update()
            workstation.draw(screen)

        # Update and draw main gate
        main_gate.update()  # Update to increment the input queue based on the input flow rate
        main_gate.draw(screen)

        # Update and draw Robot Xs
        for robot in robots_x:
            robot.update(screen)

        # Update and draw Robot Ys
        for robot in robots_y:
            robot.update(screen)

        # Update the display
        pygame.display.flip()

        # Cap the frame rate
        clock.tick(FPS)

# Run the game if this file is executed directly
if __name__ == "__main__":
    main()


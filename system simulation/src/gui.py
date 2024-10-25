from global_def import *
import pygame


class GraphicUserInterface:
    def __init__(self, factory):
        pygame.init()

        self.factory = factory

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(f"Factory Simulator (Speed x{BACKEND_SPEED_RATIO})")


        # Define fonts
        self.font = pygame.font.SysFont(FONT_FAMILY, FONT_SIZE)

        self.clock = pygame.time.Clock()
        self.running = False

        self.paused = False

    def draw_status(self):
        # Draw a status indicator on the screen showing whether the system is paused
        color = (200, 0, 0) if self.paused else (0, 200, 0)
        font = pygame.font.SysFont(None, 50)
        status_text = "Paused" if self.paused else f"Running (X{BACKEND_SPEED_RATIO})"
        label = font.render(status_text, True, color)
        self.screen.blit(label, (SCREEN_WIDTH - 400, SCREEN_HEIGHT - 75))
        pass

    def handle_screen_click(self):
        # Toggle pause/resume when the screen is clicked
        self.paused = not self.paused
        self.factory.is_paused = self.paused  # Update the global pause flag

    def run(self):
        self.running = True

        while self.running:

            # Handle Pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_screen_click()  # Handle click anywhere on the screen

            # Clear screen
            self.screen.fill(COLOR_LIGHT_GREY)


            # update the factory
            self.factory.draw(self.screen)

            # Draw current status (Paused/Running)
            self.draw_status()

            # Update the display
            pygame.display.flip()

            # Cap the frame rate
            self.clock.tick(int(1 / FRONTEND_CYCLE_TIME))

    def stop(self):
        pygame.quit()

        # TODO: logging and saving status

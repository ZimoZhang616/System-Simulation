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

    def run(self):
        self.running = True

        while self.running:

            # Handle Pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Send user commands or inputs back to the backend
            # if pygame.key.get_pressed()[pygame.K_SPACE]:
            #     global_cmd_queue.put("START_OPERATION")  # Example command

            # Clear screen
            self.screen.fill(COLOR_LIGHT_GREY)

            # update the factory
            self.factory.draw(self.screen)

            # Update the display
            pygame.display.flip()

            # Cap the frame rate
            self.clock.tick(int(1 / FRONTEND_CYCLE_TIME))

    def stop(self):
        pygame.quit()

        # TODO: logging and saving status

"""Robot arena simulation main entry point."""
import pygame
import sys
from arena_renderer import ArenaRenderer


def main():
    """Run the simulation."""
    # Initialize pygame
    pygame.init()
    
    # Create arena renderer
    arena = ArenaRenderer()
    
    # Create display window
    screen = pygame.display.set_mode((arena.display_width, arena.display_height))
    pygame.display.set_caption("Robot Arena Simulation")
    
    # Clock for controlling frame rate
    clock = pygame.time.Clock()
    
    # Main simulation loop
    running = True
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    running = False
        
        # Draw arena
        arena.draw(screen)
        
        # Update display
        pygame.display.flip()
        
        # Control frame rate (60 FPS)
        clock.tick(60)
    
    # Clean up
    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()

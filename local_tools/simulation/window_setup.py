"""Window setup and configuration for the simulation."""
import os
import logging
import pygame


def is_wsl():
    """Check if running in WSL environment.

    Returns:
        bool: True if running in WSL, False otherwise
    """
    try:
        if os.path.exists('/proc/version'):
            with open('/proc/version', 'r') as f:
                return 'microsoft' in f.read().lower()
    except Exception:
        pass
    return False


def setup_window_topmost_linux():
    """Set pygame window as topmost on native Linux using SDL2."""
    try:
        from pygame._sdl2 import Window
        window = Window.from_display_module()
        window.always_on_top = True
    except (ImportError, AttributeError):
        logging.warning("SDL2 window management not available")


def create_display(width, height, title="Robot Arena Simulation"):
    """Create and configure the pygame display window.

    Args:
        width: Window width in pixels
        height: Window height in pixels
        title: Window title text

    Returns:
        pygame.Surface: The display surface
    """
    # Position window in top-right corner on native Linux
    if not is_wsl():
        os.environ['SDL_VIDEO_WINDOW_POS'] = f"{1920-width-20},40"

    # Create window
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption(title)


    return screen

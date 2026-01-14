"""Window setup and configuration for the simulation."""
import os
import logging
import subprocess
import time
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


def setup_window_topmost_wsl():
    """Set pygame window as topmost in WSL using PowerShell.

    This uses PowerShell to call Windows API and set the window
    as HWND_TOPMOST so it stays above other windows.
    """
    try:
        time.sleep(0.5)  # Give window time to appear
        ps_script = """
        $window = Get-Process | Where-Object {$_.MainWindowTitle -like '*Robot Arena Simulation*'} | Select-Object -First 1
        if ($window) {
            Add-Type @"
                using System;
                using System.Runtime.InteropServices;
                public class Win32 {
                    [DllImport("user32.dll")]
                    public static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);
                    public static readonly IntPtr HWND_TOPMOST = new IntPtr(-1);
                    public const uint SWP_NOMOVE = 0x0002;
                    public const uint SWP_NOSIZE = 0x0001;
                }
"@
            [Win32]::SetWindowPos($window.MainWindowHandle, [Win32]::HWND_TOPMOST, 0, 0, 0, 0, [Win32]::SWP_NOMOVE -bor [Win32]::SWP_NOSIZE)
        }
        """
        subprocess.Popen(
            ['powershell.exe', '-Command', ps_script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception as e:
        logging.warning(f"Could not set window topmost in WSL: {e}")


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

    # Set window as topmost
    if is_wsl():
        setup_window_topmost_wsl()
    else:
        setup_window_topmost_linux()

    return screen

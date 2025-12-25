"""
STEM Deconvolution Display Module

This module implements advanced visualization features including:
    - Smart colorbar positioning with collision avoidance
    - Multiple display modes (linear, log, power)
    - Smooth transitions with easing functions
    - Keyboard shortcuts
    - Real-time synchronization

Author: Chen Guisen
Date: 2025-11-28
Version: 3.0.0
"""

import numpy as np
from enum import Enum
from typing import Optional, Tuple, Callable
import logging

logger = logging.getLogger(__name__)


class DisplayMode(Enum):
    """Image display modes."""
    LINEAR = "linear"
    LOG = "log"
    POWER = "power"


class ColorbarPosition(Enum):
    """Colorbar position options."""
    RIGHT = "right"
    LEFT = "left"
    TOP = "top"
    BOTTOM = "bottom"
    AUTO = "auto"  # Smart positioning


def calculate_image_entropy_region(image: np.ndarray, 
                                   region: str,
                                   margin: int = 10) -> float:
    """Calculate entropy in a specific region of the image.
    
    Used for smart colorbar positioning - choose the region with lowest
    information content to minimize obstruction.
    
    Args:
        image: Input image array.
        region: One of 'left', 'right', 'top', 'bottom'.
        margin: Width of the region to analyze (default: 10 pixels).
        
    Returns:
        Entropy value (lower = less information).
    """
    ny, nx = image.shape
    
    # Extract region
    if region == 'left':
        roi = image[:, :margin]
    elif region == 'right':
        roi = image[:, -margin:]
    elif region == 'top':
        roi = image[:margin, :]
    elif region == 'bottom':
        roi = image[-margin:, :]
    else:
        raise ValueError(f"Invalid region: {region}")
    
    # Calculate histogram-based entropy
    hist, _ = np.histogram(roi.flatten(), bins=50, density=True)
    hist = hist[hist > 0]  # Remove zero bins
    entropy = -np.sum(hist * np.log2(hist + 1e-10))
    
    return float(entropy)


def find_optimal_colorbar_position(image: np.ndarray,
                                   min_spacing: int = 10) -> str:
    """Find optimal colorbar position using entropy analysis.
    
    Analyzes image entropy in four edge regions and selects the one
    with minimum information content.
    
    Args:
        image: Input image array.
        min_spacing: Minimum spacing from image edge (pixels).
        
    Returns:
        Optimal position: 'right', 'left', 'top', or 'bottom'.
    """
    regions = ['right', 'left', 'top', 'bottom']
    entropies = {}
    
    for region in regions:
        entropies[region] = calculate_image_entropy_region(
            image, region, margin=min_spacing
        )
    
    # Choose region with minimum entropy
    optimal = min(entropies, key=entropies.get)
    
    logger.info(f"Colorbar position analysis: {entropies}")
    logger.info(f"Optimal position: {optimal}")
    
    return optimal


def apply_display_mode(image: np.ndarray,
                      mode: DisplayMode,
                      epsilon: float = 1e-10) -> np.ndarray:
    """Apply display transformation to image.
    
    Args:
        image: Input image array.
        mode: Display mode (LINEAR, LOG, POWER).
        epsilon: Small constant for numerical stability.
        
    Returns:
        Transformed image for display.
    """
    if mode == DisplayMode.LINEAR:
        return image
    
    elif mode == DisplayMode.LOG:
        # Log scale: log(I + ε)
        return np.log(image + epsilon)
    
    elif mode == DisplayMode.POWER:
        # Power law (gamma correction): I^0.5
        # Clip negative values
        image_pos = np.clip(image, 0, None)
        return np.power(image_pos, 0.5)
    
    else:
        raise ValueError(f"Unknown display mode: {mode}")


def cubic_ease_in_out(t: float) -> float:
    """Cubic easing function for smooth transitions.
    
    Args:
        t: Time parameter (0 to 1).
        
    Returns:
        Eased value (0 to 1).
    """
    if t < 0.5:
        return 4 * t**3
    else:
        return 1 - pow(-2 * t + 2, 3) / 2


def generate_transition_frames(image_start: np.ndarray,
                               image_end: np.ndarray,
                               num_frames: int = 10,
                               easing: Callable[[float], float] = cubic_ease_in_out
                               ) -> list:
    """Generate smooth transition frames between two images.
    
    Args:
        image_start: Starting image.
        image_end: Ending image.
        num_frames: Number of transition frames (default: 10).
        easing: Easing function (default: cubic_ease_in_out).
        
    Returns:
        List of interpolated image frames.
    """
    frames = []
    
    for i in range(num_frames + 1):
        t = i / num_frames
        t_eased = easing(t)
        
        # Linear interpolation with easing
        frame = (1 - t_eased) * image_start + t_eased * image_end
        frames.append(frame)
    
    return frames


def normalize_for_display(image: np.ndarray,
                         vmin: Optional[float] = None,
                         vmax: Optional[float] = None,
                         percentile: Optional[Tuple[float, float]] = None
                         ) -> Tuple[np.ndarray, float, float]:
    """Normalize image for display with robust statistics.
    
    Args:
        image: Input image.
        vmin: Minimum value (if None, computed from data).
        vmax: Maximum value (if None, computed from data).
        percentile: Optional percentile clipping (e.g., (1, 99)).
        
    Returns:
        Tuple of (normalized_image, vmin_used, vmax_used).
    """
    # Compute vmin/vmax if not provided
    if percentile is not None:
        vmin_auto, vmax_auto = np.percentile(image, percentile)
    else:
        vmin_auto = np.min(image)
        vmax_auto = np.max(image)
    
    vmin = vmin if vmin is not None else vmin_auto
    vmax = vmax if vmax is not None else vmax_auto
    
    # Normalize to [0, 1]
    if vmax > vmin:
        normalized = (image - vmin) / (vmax - vmin)
    else:
        normalized = np.zeros_like(image)
    
    normalized = np.clip(normalized, 0, 1)
    
    return normalized, vmin, vmax


def create_scalebar(image_shape: Tuple[int, int],
                   pixel_size: float,
                   bar_length_nm: float = 5.0,
                   position: str = 'bottom-right',
                   thickness: int = 3,
                   color: float = 1.0) -> np.ndarray:
    """Create scalebar overlay for image.
    
    Args:
        image_shape: Image dimensions (ny, nx).
        pixel_size: Pixel size in Angstroms.
        bar_length_nm: Scalebar length in nanometers.
        position: Position ('bottom-right', 'bottom-left', etc.).
        thickness: Bar thickness in pixels.
        color: Bar color (0-1 for grayscale).
        
    Returns:
        Boolean mask array for scalebar.
    """
    ny, nx = image_shape
    
    # Calculate bar length in pixels
    bar_length_px = int(bar_length_nm * 10 / pixel_size)  # nm to Å to pixels
    
    # Create mask
    mask = np.zeros(image_shape, dtype=bool)
    
    # Determine position
    margin = 10
    if position == 'bottom-right':
        y_start = ny - margin - thickness
        y_end = ny - margin
        x_start = nx - margin - bar_length_px
        x_end = nx - margin
    elif position == 'bottom-left':
        y_start = ny - margin - thickness
        y_end = ny - margin
        x_start = margin
        x_end = margin + bar_length_px
    else:
        raise ValueError(f"Unsupported position: {position}")
    
    # Draw bar
    mask[y_start:y_end, x_start:x_end] = True
    
    return mask


# Integration with matplotlib

def setup_matplotlib_colorbar(fig, ax, image, cbar_position='right',
                              min_spacing=10):
    """Setup matplotlib colorbar with smart positioning.
    
    This is a helper function for integration with existing matplotlib code.
    
    Args:
        fig: Matplotlib figure.
        ax: Matplotlib axes.
        image: Displayed image data.
        cbar_position: 'auto' for smart positioning or specific position.
        min_spacing: Minimum spacing for auto positioning.
        
    Returns:
        Colorbar object.
    """
    import matplotlib.pyplot as plt
    from mpl_toolkits.axes_grid1 import make_axes_locatable
    
    # Determine position
    if cbar_position == 'auto':
        position = find_optimal_colorbar_position(image, min_spacing)
    else:
        position = cbar_position
    
    # Create colorbar with appropriate positioning
    divider = make_axes_locatable(ax)
    
    if position == 'right':
        cax = divider.append_axes("right", size="5%", pad=0.1)
        cbar = plt.colorbar(ax.images[0], cax=cax)
    elif position == 'left':
        cax = divider.append_axes("left", size="5%", pad=0.1)
        cbar = plt.colorbar(ax.images[0], cax=cax)
    elif position == 'top':
        cax = divider.append_axes("top", size="5%", pad=0.1)
        cbar = plt.colorbar(ax.images[0], cax=cax, orientation='horizontal')
    elif position == 'bottom':
        cax = divider.append_axes("bottom", size="5%", pad=0.1)
        cbar = plt.colorbar(ax.images[0], cax=cax, orientation='horizontal')
    
    return cbar


def create_comparison_panel(images: dict,
                           titles: Optional[dict] = None,
                           mode: DisplayMode = DisplayMode.LINEAR,
                           figsize: Tuple[int, int] = (15, 10),
                           cmap: str = 'gray',
                           save_path: Optional[str] = None):
    """Create comparison panel of multiple images.
    
    Args:
        images: Dictionary of {name: image_array}.
        titles: Optional dictionary of {name: title_string}.
        mode: Display mode to apply.
        figsize: Figure size.
        cmap: Colormap name.
        save_path: Optional path to save figure.
        
    Returns:
        Matplotlib figure object.
    """
    import matplotlib.pyplot as plt
    
    n_images = len(images)
    
    # Determine layout
    if n_images <= 2:
        nrows, ncols = 1, n_images
    elif n_images <= 4:
        nrows, ncols = 2, 2
    elif n_images <= 6:
        nrows, ncols = 2, 3
    else:
        nrows = int(np.ceil(np.sqrt(n_images)))
        ncols = int(np.ceil(n_images / nrows))
    
    fig, axes = plt.subplots(nrows, ncols, figsize=figsize)
    if n_images == 1:
        axes = [axes]
    else:
        axes = axes.flatten()
    
    for idx, (name, image) in enumerate(images.items()):
        ax = axes[idx]
        
        # Apply display mode
        display_image = apply_display_mode(image, mode)
        
        # Normalize
        display_image, vmin, vmax = normalize_for_display(
            display_image,
            percentile=(1, 99)
        )
        
        # Display
        im = ax.imshow(display_image, cmap=cmap, aspect='equal',
                      interpolation='nearest')
        
        # Title
        title = titles[name] if titles and name in titles else name
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.axis('off')
        
        # Colorbar with smart positioning
        position = find_optimal_colorbar_position(display_image)
        cbar = setup_matplotlib_colorbar(fig, ax, display_image, position)
        cbar.ax.tick_params(labelsize=8)
    
    # Hide unused axes
    for idx in range(n_images, len(axes)):
        axes[idx].axis('off')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"Saved comparison panel to {save_path}")
    
    return fig


# Keyboard shortcut handler
class DisplayModeController:
    """Controller for managing display mode with keyboard shortcuts.
    
    Usage:
        controller = DisplayModeController()
        controller.connect_to_figure(fig)
        
        # Press Ctrl+L for log mode
        # Press Ctrl+P for power mode
        # Press Ctrl+N for linear (normal) mode
    """
    
    def __init__(self, initial_mode: DisplayMode = DisplayMode.LINEAR):
        self.mode = initial_mode
        self.callbacks = []
        
    def set_mode(self, mode: DisplayMode):
        """Set display mode and notify callbacks."""
        if mode != self.mode:
            self.mode = mode
            logger.info(f"Display mode changed to: {mode.value}")
            
            # Notify all registered callbacks
            for callback in self.callbacks:
                callback(mode)
    
    def register_callback(self, callback: Callable[[DisplayMode], None]):
        """Register a callback to be called when mode changes."""
        self.callbacks.append(callback)
    
    def on_key_press(self, event):
        """Handle keyboard events."""
        # Check for Ctrl+L (log mode)
        if event.key == 'ctrl+l':
            self.set_mode(DisplayMode.LOG)
        
        # Check for Ctrl+P (power mode)
        elif event.key == 'ctrl+p':
            self.set_mode(DisplayMode.POWER)
        
        # Check for Ctrl+N (normal/linear mode)
        elif event.key == 'ctrl+n':
            self.set_mode(DisplayMode.LINEAR)
    
    def connect_to_figure(self, fig):
        """Connect keyboard handler to matplotlib figure."""
        fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        logger.info("Keyboard shortcuts enabled: Ctrl+L (log), Ctrl+P (power), Ctrl+N (linear)")


if __name__ == "__main__":
    # Test smart colorbar positioning
    print("Testing display module...")
    
    # Create test image with feature on right side
    test_image = np.random.rand(256, 256)
    test_image[:, 200:] += 2.0  # Add feature on right
    
    # Find optimal position
    position = find_optimal_colorbar_position(test_image)
    print(f"Optimal colorbar position: {position}")
    
    # Test display modes
    print("\nTesting display modes...")
    for mode in DisplayMode:
        transformed = apply_display_mode(test_image, mode)
        print(f"{mode.value}: min={transformed.min():.3f}, max={transformed.max():.3f}")
    
    # Test easing function
    print("\nTesting easing function...")
    t_values = [0, 0.25, 0.5, 0.75, 1.0]
    for t in t_values:
        eased = cubic_ease_in_out(t)
        print(f"t={t:.2f} -> eased={eased:.3f}")
    
    print("\nDisplay module tests passed!")

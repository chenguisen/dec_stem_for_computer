import numpy as np
from scipy.ndimage import convolve1d

def total_variation_gradient(image):
    """
    Calculate the curvature term for Total Variation (TV) regularization.
    Returns div(grad(u)/|grad(u)|) using stable forward/backward differences.
    """
    epsilon = 1e-8
    
    def get_curvature(data):
        # Forward differences
        # dx[i,j] = u[i, j+1] - u[i, j]
        dx = np.roll(data, -1, axis=1) - data
        # dy[i,j] = u[i+1, j] - u[i, j]
        dy = np.roll(data, -1, axis=0) - data
        
        norm = np.sqrt(dx**2 + dy**2 + epsilon)
        
        # Normalized gradients
        nx = dx / norm
        ny = dy / norm
        
        # Backward divergence
        # div_x = nx[i,j] - nx[i, j-1]
        div_x = nx - np.roll(nx, 1, axis=1)
        # div_y = ny[i,j] - ny[i-1, j]
        div_y = ny - np.roll(ny, 1, axis=0)
        
        return div_x + div_y

    if np.iscomplexobj(image):
        curv_r = get_curvature(image.real)
        curv_i = get_curvature(image.imag)
        return curv_r + 1j * curv_i
    else:
        return get_curvature(image)

def tikhonov_miller_regularization(image, lambda_reg, pixel_size, wavelength):
    """
    Calculate the Tikhonov-Miller regularization term.
    Strictly follows C++ implementation: 1 - 2 * lambda * (FirstDerivativeSum) * scal
    
    Args:
        image (np.ndarray): Complex image.
        lambda_reg (float): Regularization parameter.
        pixel_size (float): Pixel size in Angstrom (or nm, must match wavelength units).
        wavelength (float): Wavelength in Angstrom (or nm).
        
    Returns:
        np.ndarray: The regularization term (denominator for Multiplicative RL).
    """
    # Coefficients for 9-point stencil (First Derivative)
    f0 = 4.0 / 5.0
    f1 = -1.0 / 5.0
    f2 = 8.0 / 210.0
    f3 = -1.0 / 280.0
    
    # Kernel construction for convolution
    # We want f0*(x[i+1] - x[i-1]) + ...
    # Convolution: sum k[j] * x[i-j]
    # For x[i+1] (j=-1), we need k[-1] = f0.
    # For x[i-1] (j=1), we need k[1] = -f0.
    # Kernel indices: [-4, -3, -2, -1, 0, 1, 2, 3, 4]
    # Values: [f3, f2, f1, f0, 0, -f0, -f1, -f2, -f3]
    weights = np.array([f3, f2, f1, f0, 0, -f0, -f1, -f2, -f3], dtype=np.float32)
    
    # C++ passes pixel_size^2 as dx/dy
    dx = pixel_size * pixel_size + 1e-16 # Avoid div by zero
    dy = pixel_size * pixel_size + 1e-16
    
    scal_ = wavelength / (4.0 * np.pi)
    
    def get_diff_sum(data):
        # Convolve along axis 1 (x) and axis 0 (y)
        # mode='wrap' for periodic boundary conditions
        diff_x = convolve1d(data, weights, axis=1, mode='wrap') / dx
        diff_y = convolve1d(data, weights, axis=0, mode='wrap') / dy
        return (diff_x + diff_y) * scal_

    if np.iscomplexobj(image):
        term_r = get_diff_sum(image.real)
        term_i = get_diff_sum(image.imag)
        term = term_r + 1j * term_i
    else:
        term = get_diff_sum(image)
        
    # C++: out = 1 - 2 * lambda * out
    return 1.0 - 2.0 * lambda_reg * term + 1e-16



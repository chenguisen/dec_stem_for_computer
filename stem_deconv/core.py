import numpy as np
from .utils import fft2, ifft2, fftshift, ifftshift
from .regularization import total_variation_gradient, tikhonov_miller_regularization

def richardson_lucy_additive(image, probe, iterations, lambda_reg=0, reg_type="None", alpha=1.0, boundary_handling=False):
    """
    Richardson-Lucy Additive Deconvolution.
    """
    # Boundary Handling: Pad image and probe
    if boundary_handling:
        pad_y = image.shape[0] // 8
        pad_x = image.shape[1] // 8
        pad_width = ((pad_y, pad_y), (pad_x, pad_x))
        image = np.pad(image, pad_width, mode='reflect')
        # Probe is padded with zeros to maintain field of view but extend grid
        probe = np.pad(probe, pad_width, mode='constant')

    # Initialize object estimate with the image
    object_data = image.astype(np.float32)
    
    # C++: Probe is spatial domain, centered (from CalProbe -> IFFT -> Rearrange)
    # But RL function takes `fftwf_complex * probe`.
    # And does `m_math.FlipMatrix(probe_flip, probe)` (spatial flip)
    # Then `FFT(probe)` and `FFT(probe_flip)`.
    # Note: C++ FFT expects corner-zero. If probe is centered, FFT result has phase shift.
    # But `probe` passed to RL is likely centered.
    # Let's assume we work with centered spatial images throughout.
    
    probe_spatial = np.abs(probe).astype(np.float32)
    
    # Normalize probe
    probe_sum = np.sum(probe_spatial)
    if probe_sum != 0:
        probe_spatial /= probe_sum
    
    # C++ FlipMatrix: y[i] = x[N-i] (Circular flip)
    # This keeps index 0 at 0.
    # np.flip flips 0 to N-1.
    # np.roll(np.flip(x), 1) gives circular flip.
    probe_flip_spatial = np.roll(np.flip(np.flip(probe_spatial, 0), 1), (1, 1), (0, 1))
    
    # FFTs
    # C++ uses FFTW_FORWARD (unnormalized).
    # We use scipy.fft.fft2 (unnormalized).
    probe_fft = fft2(probe_spatial)
    probe_flip_fft = fft2(probe_flip_spatial)
    
    # Scale factor for IFFT
    # C++ does IFFT (unnormalized) then Scale(1/N).
    # scipy.fft.ifft2 is normalized (1/N).
    # So ifft2(fft2(x)) == x. Matches C++.
    
    for i in range(iterations):
        # 1. Convolve Object with Probe: O * P
        obj_fft = fft2(object_data)
        blurred_fft = obj_fft * probe_fft
        blurred = np.real(fftshift(ifft2(blurred_fft)))
        
        # 2. Calculate Ratio: I / (O * P)
        denom = np.maximum(blurred, 1e-9)
        ratio = image / denom
        
        # 3. Convolve Ratio with Flipped Probe: Ratio * P_flip
        ratio_fft = fft2(ratio)
        gradient_fft = ratio_fft * probe_flip_fft
        gradient = np.real(fftshift(ifft2(gradient_fft)))
        
        # 4. Update Step
        # C++: tempImage = gradient
        # tempImage = tempImage - 1
        update_term = gradient - 1.0
        
        # Regularization
        if reg_type == "TV":
            # Standard TV: Add lambda * curvature (smoothing)
            # curvature = div(grad/|grad|)
            curv = total_variation_gradient(object_data)
            update_term = update_term + lambda_reg * curv
            
        elif reg_type == "TM":
            # Standard TM: Add lambda * Laplacian (smoothing)
            # But TM usually minimizes ||grad u||^2 + ||u-f||^2
            # Gradient descent: u_new = u_old + (f - u) + lambda * Laplacian u
            # RL Additive: u_new = u_old + (Ratio - 1) + lambda * Laplacian u
            # So we add lambda * Laplacian.
            
            # Note: C++ TM implementation was weird (1 - 2*lambda*div).
            # We use standard Laplacian here.
            # lap = tikhonov_miller_regularization(object_data, pixel_size=1.0) # pixel_size not passed to RL Additive currently?
            # Assuming pixel_size=1.0 for now or we need to update signature.
            # Additive RL signature doesn't have pixel_size.
            
            # update_term = update_term + lambda_reg * lap
            pass # Not implemented for Additive in C++ strictly speaking, or requires pixel_size/wavelength
            
        # Apply alpha
        update_term = update_term * alpha
        
        # Update Object
        object_data = object_data + update_term
        
        # Resolution Limit (Optional, based on C++ code)
        # ...
        
    if boundary_handling:
        object_data = object_data[pad_y:-pad_y, pad_x:-pad_x]

    return object_data

def richardson_lucy_multiplicative(image, probe, iterations, lambda_reg=0, reg_type="None", pixel_size=1.0, wavelength=1.0, acceleration=False, boundary_handling=False, damping_threshold=None, background_level=0.0):
    """
    Richardson-Lucy Multiplicative Deconvolution.
    Supports Biggs-Andrews acceleration, Damping, and Background handling.
    
    Args:
        damping_threshold (float): Threshold (in sigma) for damped RL. 
                                   If set, suppresses noise amplification in flat regions.
        background_level (float): Estimated background level to subtract/model during deconvolution.
                                  RL assumes Poisson noise on (Signal + Background).
    """
    # Boundary Handling: Pad image and probe
    if boundary_handling:
        pad_y = image.shape[0] // 8
        pad_x = image.shape[1] // 8
        pad_width = ((pad_y, pad_y), (pad_x, pad_x))
        image = np.pad(image, pad_width, mode='reflect')
        probe = np.pad(probe, pad_width, mode='constant')

    object_data = image.astype(np.float32)
    probe_spatial = np.abs(probe).astype(np.float32)
    
    # Normalize probe to preserve energy (sum = 1)
    # This is critical for Richardson-Lucy, especially with background modeling
    probe_sum = np.sum(probe_spatial)
    if probe_sum != 0:
        probe_spatial /= probe_sum
    
    probe_flip_spatial = np.roll(np.flip(np.flip(probe_spatial, 0), 1), (1, 1), (0, 1))
    
    probe_fft = fft2(probe_spatial)
    probe_flip_fft = fft2(probe_flip_spatial)
    
    # Acceleration variables
    if acceleration:
        g_tm1 = object_data.copy()
        g_tm2 = object_data.copy()
        alpha_acc = 0.0

    for i in range(iterations):
        # Prediction step for acceleration
        if acceleration and i > 1:
            # Biggs-Andrews Acceleration
            alpha_acc = (i - 1) / (i + 2) 
            prediction = object_data + alpha_acc * (object_data - g_tm1)
            prediction[prediction < 0] = 0 # Positivity constraint
            current_estimate = prediction
        else:
            current_estimate = object_data

        # 1. O * P + Background
        obj_fft = fft2(current_estimate)
        blurred = np.real(fftshift(ifft2(obj_fft * probe_fft)))
        
        # Add background to the model prediction
        blurred_with_bg = blurred + background_level
        blurred_with_bg[blurred_with_bg < 1e-9] = 1e-9 # Avoid division by zero
        
        # 2. I / (O * P + B)
        ratio = image / blurred_with_bg
        
        # Damping (White 1994)
        if damping_threshold is not None:
            # Calculate local noise threshold based on Poisson statistics
            # sigma = sqrt(Model)
            # We want to suppress updates if |Data - Model| < N * sigma
            # |Ratio - 1| = |Data/Model - 1| = |Data - Model| / Model
            # So we check if |Ratio - 1| < N * sigma / Model = N / sqrt(Model)
            
            # Avoid div by zero in sqrt
            model_mag = blurred_with_bg
            model_mag = np.maximum(model_mag, 1e-9)
            
            local_threshold = damping_threshold / np.sqrt(model_mag)
            
            mask_damp = np.abs(ratio - 1.0) < local_threshold
            ratio[mask_damp] = 1.0
        
        # 3. Ratio * P_flip
        gradient = np.real(fftshift(ifft2(fft2(ratio) * probe_flip_fft)))
        
        # 4. Update
        if reg_type == "TV":
            # Multiplicative TV: O_new = O_old * Gradient / (1 - lambda * curv)
            curv = total_variation_gradient(current_estimate)
            divisor = 1.0 - lambda_reg * curv
            # Ensure divisor is positive to prevent sign flipping and division by zero
            divisor = np.maximum(divisor, 1e-6)
            
            new_object = current_estimate * gradient / divisor
            
        elif reg_type == "TM":
            # Multiplicative TM
            tm_term = tikhonov_miller_regularization(current_estimate, lambda_reg, pixel_size, wavelength)
            divisor = tm_term
            # Ensure divisor is positive
            divisor = np.maximum(divisor, 1e-6)
            
            new_object = current_estimate * gradient / divisor
            
        else:
            new_object = current_estimate * gradient
            
        if acceleration:
            g_tm1 = object_data.copy()
            object_data = new_object
        else:
            object_data = new_object
            
    if boundary_handling:
        object_data = object_data[pad_y:-pad_y, pad_x:-pad_x]

    return object_data

def fista_deconvolution(image, probe, iterations, lambda_reg=0.001, boundary_handling=False):
    """
    Fast Iterative Shrinkage-Thresholding Algorithm (FISTA) for TV regularization.
    Minimizes ||Ax - b||^2 + lambda * TV(x)
    """
    # Boundary Handling: Pad image and probe
    if boundary_handling:
        pad_y = image.shape[0] // 8
        pad_x = image.shape[1] // 8
        pad_width = ((pad_y, pad_y), (pad_x, pad_x))
        image = np.pad(image, pad_width, mode='reflect')
        probe = np.pad(probe, pad_width, mode='constant')

    # A is convolution with probe
    # A^T is convolution with flipped probe
    
    x = image.astype(np.float32)
    y = x.copy()
    t = 1.0
    
    probe_spatial = np.abs(probe).astype(np.float32)
    
    # Normalize probe
    probe_sum = np.sum(probe_spatial)
    if probe_sum != 0:
        probe_spatial /= probe_sum
        
    probe_flip_spatial = np.roll(np.flip(np.flip(probe_spatial, 0), 1), (1, 1), (0, 1))
    
    probe_fft = fft2(probe_spatial)
    probe_flip_fft = fft2(probe_flip_spatial)
    
    # Lipschitz constant estimation (max eigenvalue of A^T A)
    # For convolution, it's max(|FFT(probe)|^2)
    L = np.max(np.abs(probe_fft)**2)
    if L == 0: L = 1.0
    step_size = 1.0 / L
    
    for k in range(iterations):
        # Gradient descent step on data fidelity: x - step * A^T (Ax - b)
        # Ax
        Ax_fft = fft2(y) * probe_fft
        Ax = np.real(fftshift(ifft2(Ax_fft)))
        
        # Residual Ax - b
        residual = Ax - image
        
        # A^T (Residual)
        grad_fft = fft2(residual) * probe_flip_fft
        grad = np.real(fftshift(ifft2(grad_fft)))
        
        x_next = y - step_size * grad
        
        # Proximal operator for TV (Denoising)
        # Here we approximate Prox_TV with a few steps of gradient descent on TV dual or similar
        # Or use a simple TV denoising subroutine (e.g. Chambolle's algorithm)
        # For simplicity/speed in this context, we can use the gradient-based TV reduction 
        # or a soft-thresholding if we were doing L1 (Wavelet).
        # Let's implement a simple TV-gradient step as a proxy for Prox_TV for now, 
        # or better: Chambolle's projection algorithm is standard for FISTA-TV.
        
        # Simplified TV Proximal (Gradient Descent on TV term)
        # x_next = x_next - lambda * step_size * grad(TV)
        # This turns it into Forward-Backward splitting.
        tv_grad = total_variation_gradient(x_next)
        # TV grad returns div(grad/|grad|), which is negative of descent direction?
        # TV functional J(u) = sum |grad u|. Grad J(u) = -div(grad u / |grad u|).
        # So we want x_new = x - step * (-div) = x + step * div.
        # Our total_variation_gradient returns div(...).
        # So:
        x_next = x_next + lambda_reg * step_size * tv_grad
        
        # FISTA Momentum update
        t_next = (1.0 + np.sqrt(1.0 + 4.0 * t**2)) / 2.0
        y = x_next + ((t - 1.0) / t_next) * (x_next - x)
        
        x = x_next
        t = t_next
        
    if boundary_handling:
        x = x[pad_y:-pad_y, pad_x:-pad_x]

    return x

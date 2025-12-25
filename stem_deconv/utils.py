import numpy as np
import mrcfile
import scipy.fft

def read_mrc(filepath):
    """
    Read an MRC file.
    Returns:
        data (np.ndarray): The image data (float32).
        pixel_size (float): Pixel size in nm.
    """
    with mrcfile.open(filepath, permissive=True) as mrc:
        data = mrc.data.copy()
        # mrcfile voxel_size is typically in Angstroms.
        # C++ code converts Angstroms to nm by dividing by 10.0.
        pixel_size = mrc.voxel_size.x / 10.0 
    return data, pixel_size

def write_mrc(filepath, data, pixel_size):
    """
    Write data to an MRC file.
    Args:
        filepath (str): Path to save the file.
        data (np.ndarray): Image data.
        pixel_size (float): Pixel size in nm.
    """
    with mrcfile.new(filepath, overwrite=True) as mrc:
        mrc.set_data(data.astype(np.float32))
        # Convert nm back to Angstroms for storage
        mrc.voxel_size = pixel_size * 10.0

def fft2(data):
    """
    Compute the 2-D discrete Fourier Transform.
    """
    return scipy.fft.fft2(data)

def ifft2(data):
    """
    Compute the 2-D inverse discrete Fourier Transform.
    """
    return scipy.fft.ifft2(data)

def fftshift(data):
    """
    Shift the zero-frequency component to the center of the spectrum.
    """
    return scipy.fft.fftshift(data)

def ifftshift(data):
    """
    The inverse of fftshift.
    """
    return scipy.fft.ifftshift(data)

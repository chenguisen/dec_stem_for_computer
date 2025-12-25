"""
[IO] Input/Output module for MRC file operations.

This module handles reading and writing MRC files with robust error handling
and automatic parameter extraction.

IMPORTANT: This module returns pixel_size in NANOMETERS (nm) to match
the unit convention used throughout the c_2_p backend.

Functions:
    load_mrc: Load MRC file with automatic pixel size extraction
    save_mrc: Save numpy array as MRC file
    extract_pixel_size: Extract or calculate pixel size from MRC header
    validate_mrc_file: Validate MRC file format and structure
"""

import numpy as np
import mrcfile
from typing import Tuple, Optional, Dict, Any
import warnings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MRCFileError(Exception):
    """Custom exception for MRC file operations."""
    pass


class PixelSizeError(Exception):
    """Custom exception for pixel size extraction errors."""
    pass


def validate_mrc_file(filepath: str) -> Dict[str, Any]:
    """
    Validate MRC file format and extract metadata.
    
    Args:
        filepath: Path to MRC file
        
    Returns:
        Dictionary containing file metadata
        
    Raises:
        MRCFileError: If file is invalid or corrupted
        
    Examples:
        >>> metadata = validate_mrc_file('image.mrc')
        >>> print(metadata['shape'])
        (512, 512)
    """
    try:
        with mrcfile.open(filepath, mode='r', permissive=True) as mrc:
            # Check if file can be opened
            if mrc.data is None:
                raise MRCFileError(f"Cannot read data from {filepath}")
            
            # Extract metadata
            metadata = {
                'filepath': filepath,
                'shape': mrc.data.shape,
                'dtype': mrc.data.dtype,
                'nx': mrc.header.nx,
                'ny': mrc.header.ny,
                'nz': mrc.header.nz,
                'mode': mrc.header.mode,
                'voxel_size': (
                    float(mrc.voxel_size.x),
                    float(mrc.voxel_size.y),
                    float(mrc.voxel_size.z)
                ),
                'data_min': float(mrc.header.dmin),
                'data_max': float(mrc.header.dmax),
                'data_mean': float(mrc.header.dmean),
            }
            
            logger.info(f"MRC file validated: {filepath}")
            logger.debug(f"Shape: {metadata['shape']}, Mode: {metadata['mode']}")
            
            return metadata
            
    except Exception as e:
        raise MRCFileError(f"Failed to validate MRC file {filepath}: {str(e)}")


def extract_pixel_size(
    filepath: str,
    fallback_value: Optional[float] = None,
    validate_range: Tuple[float, float] = (0.0001, 1.0)
) -> float:
    """
    Extract or calculate pixel size from MRC file header.
    
    This function attempts to extract pixel size from the MRC header with
    robust error handling for various edge cases:
    - Missing voxel_size information
    - Zero or negative values
    - Out of reasonable range values
    
    IMPORTANT: Returns pixel size in NANOMETERS (nm), not Angstroms.
    MRC headers store values in Angstroms, but this function converts to nm.
    
    Args:
        filepath: Path to MRC file
        fallback_value: Default value if extraction fails (nanometers)
        validate_range: Valid range for pixel size (min, max) in nanometers
        
    Returns:
        Pixel size in nanometers
        
    Raises:
        PixelSizeError: If pixel size cannot be extracted and no fallback provided
        
    Examples:
        >>> pixel_size = extract_pixel_size('image.mrc')
        >>> print(f"Pixel size: {pixel_size:.4f} nm")
        Pixel size: 0.0100 nm
        
        >>> # With fallback
        >>> pixel_size = extract_pixel_size('bad.mrc', fallback_value=0.01)
    """
    min_val, max_val = validate_range
    
    try:
        with mrcfile.open(filepath, mode='r', permissive=True) as mrc:
            # Try to get voxel_size from header (in Angstroms)
            voxel_x = float(mrc.voxel_size.x)
            voxel_y = float(mrc.voxel_size.y)
            
            # Check for zero or negative values
            if voxel_x <= 0 or voxel_y <= 0:
                logger.warning(f"Invalid voxel size: x={voxel_x}, y={voxel_y}")
                raise PixelSizeError("Voxel size is zero or negative")
            
            # Use average of x and y if they differ
            if abs(voxel_x - voxel_y) > 1e-6:
                pixel_size_angstrom = (voxel_x + voxel_y) / 2.0
                logger.warning(
                    f"Different x/y voxel sizes: x={voxel_x:.4f}, "
                    f"y={voxel_y:.4f}, using average={pixel_size_angstrom:.4f} Å"
                )
            else:
                pixel_size_angstrom = voxel_x
            
            # Convert Angstroms to nanometers
            pixel_size = pixel_size_angstrom / 10.0
            
            # Validate range
            if not (min_val <= pixel_size <= max_val):
                logger.warning(
                    f"Pixel size {pixel_size:.4f} nm out of valid range "
                    f"[{min_val}, {max_val}]"
                )
                raise PixelSizeError(
                    f"Pixel size {pixel_size:.4f} nm out of range "
                    f"[{min_val}, {max_val}]"
                )
            
            logger.info(f"Extracted pixel size: {pixel_size:.4f} nm ({pixel_size_angstrom:.4f} Å)")
            return pixel_size
            
    except (AttributeError, ValueError, TypeError) as e:
        logger.warning(f"Cannot extract pixel size from header: {str(e)}")
        
        # Try alternative method: calculate from cell dimensions
        try:
            with mrcfile.open(filepath, mode='r', permissive=True) as mrc:
                # Cell dimensions / number of pixels
                if mrc.header.cella.x > 0 and mrc.header.nx > 0:
                    pixel_size_angstrom = float(mrc.header.cella.x) / float(mrc.header.nx)
                    pixel_size = pixel_size_angstrom / 10.0  # Convert to nm
                    
                    if min_val <= pixel_size <= max_val:
                        logger.info(
                            f"Calculated pixel size from cell: {pixel_size:.4f} nm ({pixel_size_angstrom:.4f} Å)"
                        )
                        return pixel_size
        except Exception:
            pass
        
        # Use fallback value
        if fallback_value is not None:
            if min_val <= fallback_value <= max_val:
                logger.info(f"Using fallback pixel size: {fallback_value:.4f} nm")
                return fallback_value
            else:
                raise PixelSizeError(
                    f"Fallback value {fallback_value} out of range [{min_val}, {max_val}]"
                )
        
        # No fallback, raise error
        raise PixelSizeError(
            f"Cannot extract pixel size from {filepath} and no valid fallback provided"
        )


def load_mrc(
    filepath: str,
    normalize: bool = True,
    auto_pixel_size: bool = True,
    fallback_pixel_size: Optional[float] = 0.01
) -> Tuple[np.ndarray, float]:
    """
    Load MRC file and return image data with pixel size.
    
    IMPORTANT: Returns pixel size in NANOMETERS (nm).
    
    Args:
        filepath: Path to MRC file
        normalize: Whether to normalize image to [0, 1]
        auto_pixel_size: Whether to automatically extract pixel size
        fallback_pixel_size: Default pixel size if extraction fails (nm)
        
    Returns:
        Tuple of (image_data, pixel_size_in_nm)
        
    Raises:
        MRCFileError: If file cannot be loaded
        
    Examples:
        >>> image, pixel_size = load_mrc('data.mrc')
        >>> print(f"Image shape: {image.shape}, Pixel size: {pixel_size} nm")
        Image shape: (512, 512), Pixel size: 0.01 nm
    """
    try:
        # Validate file first
        metadata = validate_mrc_file(filepath)
        
        # Load data
        with mrcfile.open(filepath, mode='r', permissive=True) as mrc:
            data = mrc.data.copy()
        
        # Handle different dimensionalities
        if data.ndim == 3:
            if data.shape[0] == 1:
                data = data[0]  # Remove singleton dimension
                logger.info("Removed singleton z-dimension")
            else:
                logger.warning(
                    f"3D data detected with shape {data.shape}, "
                    f"using first slice"
                )
                data = data[0]
        elif data.ndim != 2:
            raise MRCFileError(
                f"Expected 2D or 3D data, got {data.ndim}D"
            )
        
        # Normalize if requested
        if normalize:
            data_min = data.min()
            data_max = data.max()
            
            if data_max - data_min < 1e-10:
                logger.warning("Image has constant value, cannot normalize")
                data = np.zeros_like(data, dtype=np.float32)
            else:
                data = (data - data_min) / (data_max - data_min)
                data = data.astype(np.float32)
                logger.debug(f"Normalized image to [0, 1]")
        
        # Extract pixel size
        if auto_pixel_size:
            try:
                pixel_size = extract_pixel_size(filepath, fallback_pixel_size)
            except PixelSizeError as e:
                logger.error(f"Pixel size extraction failed: {str(e)}")
                raise
        else:
            if fallback_pixel_size is None:
                raise ValueError("Must provide fallback_pixel_size when auto_pixel_size=False")
            pixel_size = fallback_pixel_size
            logger.info(f"Using provided pixel size: {pixel_size:.4f} nm")
        
        logger.info(
            f"Loaded MRC: shape={data.shape}, "
            f"dtype={data.dtype}, pixel_size={pixel_size:.4f} nm"
        )
        
        return data, pixel_size
        
    except Exception as e:
        raise MRCFileError(f"Failed to load MRC file {filepath}: {str(e)}")


class ParameterExtractionError(Exception):
    """Exception raised when parameter extraction fails."""
    pass


def load_mrc_with_params(
    filepath: str,
    normalize: bool = True,
    auto_pixel_size: bool = True,
    fallback_pixel_size: Optional[float] = 0.01
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Load MRC file and return image data with detailed parameters dictionary.
    
    This is a wrapper around load_mrc() that returns parameters in a dictionary
    format, compatible with GUI applications.
    
    IMPORTANT: pixel_size in returned dictionary is in NANOMETERS (nm).
    
    Args:
        filepath: Path to MRC file
        normalize: Whether to normalize image to [0, 1]
        auto_pixel_size: Whether to automatically extract pixel size
        fallback_pixel_size: Default pixel size if extraction fails (nm)
        
    Returns:
        Tuple of (image_data, parameters_dict) where parameters_dict contains:
            - 'pixel_size': float in nm or None
            - 'source': str describing extraction method
            - 'metadata': dict with file metadata
        
    Raises:
        MRCFileError: If file cannot be loaded
        ParameterExtractionError: If parameter extraction fails critically
        
    Examples:
        >>> image, params = load_mrc_with_params('data.mrc')
        >>> print(f"Pixel size: {params['pixel_size']} nm from {params['source']}")
        Pixel size: 0.01 nm from voxel_size
    """
    try:
        # Load image and pixel size
        image, pixel_size = load_mrc(
            filepath,
            normalize=normalize,
            auto_pixel_size=auto_pixel_size,
            fallback_pixel_size=fallback_pixel_size
        )
        
        # Get metadata
        metadata = validate_mrc_file(filepath)
        
        # Determine source of pixel size
        if auto_pixel_size:
            # Try to determine how pixel size was extracted
            voxel_x = metadata['voxel_size'][0]
            if voxel_x > 0.01 and voxel_x < 100.0:  # Valid Angstrom range
                source = 'voxel_size'
            elif metadata['nx'] > 0:
                # Might be from cell calculation
                source = 'cell_calculation'
            else:
                source = 'fallback'
        else:
            source = 'user_provided'
        
        # Build parameters dictionary
        params = {
            'pixel_size': pixel_size if pixel_size is not None else fallback_pixel_size,
            'source': source,
            'metadata': metadata,
            'shape': image.shape,
            'dtype': str(image.dtype)
        }
        
        return image, params
        
    except MRCFileError:
        raise
    except Exception as e:
        raise ParameterExtractionError(
            f"Failed to extract parameters from {filepath}: {str(e)}"
        )


def save_mrc(
    filepath: str,
    data: np.ndarray,
    pixel_size: Optional[float] = None,
    overwrite: bool = True
) -> None:
    """
    Save numpy array as MRC file.
    
    IMPORTANT: pixel_size should be provided in NANOMETERS (nm).
    It will be converted to Angstroms for MRC storage.
    
    Args:
        filepath: Output file path
        data: Image data to save
        pixel_size: Pixel size in nanometers
        overwrite: Whether to overwrite existing file
        
    Raises:
        MRCFileError: If save operation fails
        
    Examples:
        >>> save_mrc('output.mrc', image_data, pixel_size=0.01)
    """
    try:
        # Ensure data is 2D or 3D
        if data.ndim not in [2, 3]:
            raise ValueError(f"Data must be 2D or 3D, got {data.ndim}D")
        
        # Convert to float32
        data_to_save = data.astype(np.float32)
        
        # Create MRC file
        with mrcfile.new(filepath, overwrite=overwrite) as mrc:
            mrc.set_data(data_to_save)
            
            # Set voxel size if provided
            if pixel_size is not None:
                if pixel_size <= 0:
                    raise ValueError(f"Pixel size must be positive, got {pixel_size}")
                # Convert nm to Angstroms for MRC storage
                pixel_size_angstrom = pixel_size * 10.0
                mrc.voxel_size = pixel_size_angstrom
                logger.debug(f"Set voxel size: {pixel_size} nm ({pixel_size_angstrom} Å)")
            
            # Set header information
            mrc.update_header_from_data()
            mrc.update_header_stats()
        
        logger.info(f"Saved MRC file: {filepath}")
        
    except Exception as e:
        raise MRCFileError(f"Failed to save MRC file {filepath}: {str(e)}")


def batch_load_mrc(
    filepaths: list,
    normalize: bool = True,
    **kwargs
) -> Dict[str, Tuple[np.ndarray, float]]:
    """
    Load multiple MRC files.
    
    IMPORTANT: pixel_size values in results are in NANOMETERS (nm).
    
    Args:
        filepaths: List of file paths
        normalize: Whether to normalize images
        **kwargs: Additional arguments for load_mrc
        
    Returns:
        Dictionary mapping filepath to (data, pixel_size_in_nm)
        
    Examples:
        >>> files = ['a.mrc', 'b.mrc', 'c.mrc']
        >>> results = batch_load_mrc(files)
        >>> for path, (img, ps) in results.items():
        ...     print(f"{path}: {img.shape}, {ps} nm")
    """
    results = {}
    failed = []
    
    for filepath in filepaths:
        try:
            data, pixel_size = load_mrc(filepath, normalize=normalize, **kwargs)
            results[filepath] = (data, pixel_size)
        except Exception as e:
            logger.error(f"Failed to load {filepath}: {str(e)}")
            failed.append(filepath)
    
    if failed:
        logger.warning(f"Failed to load {len(failed)}/{len(filepaths)} files")
    
    return results

import sys
import os
import numpy as np
from stem_deconv.utils import read_mrc
from stem_deconv.physics import calculate_ctf, calculate_probe, calculate_wavelength
from stem_deconv.core import richardson_lucy_multiplicative

# Load Image
image_path = "/media/chenguisen/WD_BLACK/cgs/待发表文章/dev_code/data/HAADF 14.0 Mx 20211225 0002 DCFI(HAADF)_Real_0.mrc"
if os.path.exists(image_path):
    image_data, pixel_size = read_mrc(image_path)
else:
    print("Image not found!")
    sys.exit(1)

print(f"Image shape: {image_data.shape}")
print(f"Pixel size: {pixel_size} nm")
print(f"Image dtype: {image_data.dtype}")
print(f"Image range: [{image_data.min():.2f}, {image_data.max():.2f}]")
print(f"Image mean: {image_data.mean():.2f}")

# Generate Probe (same as run_deconv.py)
voltage = 300.0
cs3 = 0.5
cs5 = 0.0
defocus = -44.0
obj_aperture = 16.0

print("\n========== Generating Probe ==========")
ctf = calculate_ctf(image_data.shape, pixel_size, voltage, 
                    cs3, cs5, defocus, obj_aperture / 1000.0)
probe = calculate_probe(ctf, image_data.shape[1]/2, image_data.shape[0]/2)
wavelength_nm = calculate_wavelength(voltage)

print(f"Probe shape: {probe.shape}")
print(f"Probe dtype: {probe.dtype}")
print(f"Probe is complex: {np.iscomplexobj(probe)}")
print(f"Probe abs range: [{np.abs(probe).min():.6f}, {np.abs(probe).max():.6f}]")
print(f"Probe sum: {np.abs(probe).sum():.6f}")
print(f"Wavelength: {wavelength_nm} nm")

# Test parameters from run_deconv.py
print("\n========== run_deconv.py Parameters ==========")
print(f"iterations: 15")
print(f"lambda_reg: 0.002")
print(f"reg_type: TV")
print(f"pixel_size: {pixel_size} nm")
print(f"wavelength: {wavelength_nm} nm")
print(f"acceleration: True")
print(f"boundary_handling: True")
print(f"damping_threshold: None")
bg_level = np.percentile(image_data, 1.0)
print(f"background_level: {bg_level}")

# Run with run_deconv.py parameters
print("\n========== Running RL Multiplicative ==========")
result = richardson_lucy_multiplicative(
    image_data, probe, iterations=15, lambda_reg=0.002, reg_type="TV", 
    pixel_size=pixel_size, wavelength=wavelength_nm, 
    acceleration=True, boundary_handling=True,
    damping_threshold=None,
    background_level=bg_level
)

print(f"Result dtype: {result.dtype}")
print(f"Result is complex: {np.iscomplexobj(result)}")
print(f"Result range: [{result.min():.2f}, {result.max():.2f}]")
print(f"Result mean: {result.mean():.2f}")
print(f"Result has NaN: {np.isnan(result).any()}")
print(f"Result has Inf: {np.isinf(result).any()}")

# Check what GUI would receive (with unit conversion)
print("\n========== GUI Unit Conversion Check ==========")
print(f"GUI pixel_size (Å): {pixel_size * 10.0}")
print(f"GUI wavelength (Å): {wavelength_nm * 10.0}")
print(f"Backend expects: nm")
print(f"GUI wrapper should divide by 10.0")

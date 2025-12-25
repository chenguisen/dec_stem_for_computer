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
    # Dummy data
    image_data = np.random.rand(256, 256).astype(np.float32) * 1000 + 100
    pixel_size = 0.1

print(f"Image shape: {image_data.shape}, Pixel size: {pixel_size} nm")
print(f"Image range: [{image_data.min():.2f}, {image_data.max():.2f}]")

# Generate Probe
voltage = 300.0
cs3 = 0.5
cs5 = 0.0
defocus = -44.0
obj_aperture = 16.0

ctf = calculate_ctf(image_data.shape, pixel_size, voltage, 
                    cs3, cs5, defocus, obj_aperture / 1000.0)
probe = calculate_probe(ctf, image_data.shape[1]/2, image_data.shape[0]/2)
wavelength_nm = calculate_wavelength(voltage)

# Test 1: damping_threshold = None
print("\n========== Test 1: damping_threshold = None ==========")
result_no_damp = richardson_lucy_multiplicative(
    image_data, probe, iterations=5, lambda_reg=0.002, reg_type="TV", 
    pixel_size=pixel_size, wavelength=wavelength_nm, 
    acceleration=True, boundary_handling=True,
    damping_threshold=None,
    background_level=0.0
)
print(f"Result (no damp) range: [{np.real(result_no_damp).min():.2f}, {np.real(result_no_damp).max():.2f}]")
print(f"Result (no damp) mean: {np.real(result_no_damp).mean():.2f}")
print(f"Result (no damp) is complex: {np.iscomplexobj(result_no_damp)}")
print(f"Result (no damp) dtype: {result_no_damp.dtype}")

# Test 2: damping_threshold = 1.0
print("\n========== Test 2: damping_threshold = 1.0 ==========")
bg_level = np.percentile(image_data, 1.0)
result_with_damp = richardson_lucy_multiplicative(
    image_data, probe, iterations=5, lambda_reg=0.002, reg_type="TV", 
    pixel_size=pixel_size, wavelength=wavelength_nm, 
    acceleration=True, boundary_handling=True,
    damping_threshold=1.0,
    background_level=bg_level
)
print(f"Result (with damp) range: [{np.real(result_with_damp).min():.2f}, {np.real(result_with_damp).max():.2f}]")
print(f"Result (with damp) mean: {np.real(result_with_damp).mean():.2f}")
print(f"Result (with damp) is complex: {np.iscomplexobj(result_with_damp)}")
print(f"Result (with damp) dtype: {result_with_damp.dtype}")

# Compare
print("\n========== Comparison ==========")
diff = np.abs(np.real(result_no_damp) - np.real(result_with_damp))
print(f"Absolute difference range: [{diff.min():.2f}, {diff.max():.2f}]")
print(f"Mean absolute difference: {diff.mean():.2f}")
print(f"Relative difference: {(diff.mean() / np.real(result_no_damp).mean() * 100):.2f}%")

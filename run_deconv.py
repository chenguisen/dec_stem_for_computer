import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from stem_deconv.utils import read_mrc, write_mrc
from stem_deconv.physics import calculate_ctf, calculate_probe, calculate_wavelength
from stem_deconv.core import richardson_lucy_additive, richardson_lucy_multiplicative, fista_deconvolution
from stem_deconv.postprocess import radial_wiener_filter, p_spline_wiener_filter

def main():
    # Example parameters (should be loaded from config or args)
    image_path = "/media/chenguisen/WD_BLACK/cgs/待发表文章/dev_code/data/HAADF 14.0 Mx 20211225 0002 DCFI(HAADF)_Real_0.mrc" # Replace with actual path
    output_path = "restored/result.mrc"
    
    # Microscope parameters
    voltage = 300.0 # kV
    cs3 = 0.5 # mm
    cs5 = 0.0 # mm
    defocus = -44.0 # nm
    obj_aperture = 16.0 # mrad
    
    # Post-processing parameters
    apply_wiener = True
    use_p_spline = True # New option
    information_limit = None # Auto-estimate if None. Units: 1/pixel_unit (e.g. 1/nm or 1/A)
    
    # Load Image
    if not os.path.exists(image_path):
        print(f"Image not found: {image_path}")
        # Create a dummy image for testing
        img_size = 256
        image_data = np.random.rand(img_size, img_size).astype(np.float32)
        pixel_size = 0.1 # nm
    else:
        image_data, pixel_size = read_mrc(image_path)
        
    print(f"Image shape: {image_data.shape}, Pixel size: {pixel_size} nm")
    
    # Generate Probe
    print("Generating Probe...")
    ctf = calculate_ctf(image_data.shape, pixel_size, voltage, 
                        cs3, cs5, defocus, obj_aperture / 1000.0) # mrad -> rad
    probe = calculate_probe(ctf, image_data.shape[1]/2, image_data.shape[0]/2) # Pass center coords to match C++ calls
    
    wavelength_nm = calculate_wavelength(voltage)

    # Run Deconvolution
    print("Running Richardson-Lucy Additive (TV Reg, Boundary Handling)...")
    result_add = richardson_lucy_additive(image_data, probe, iterations=15, lambda_reg=0.002, reg_type="TV", boundary_handling=True)
    
    print("Running Richardson-Lucy Multiplicative (TV Reg, Accelerated, Boundary Handling, Damped, Background-Aware)...")
    # Estimate background (simple minimum or percentile)
    bg_level = np.percentile(image_data, 1.0) # 1st percentile as background estimate
    print(f"Estimated Background Level: {bg_level}")
    
    result_mul = richardson_lucy_multiplicative(
        image_data, probe, iterations=15, lambda_reg=0.002, reg_type="TV", 
        pixel_size=pixel_size, wavelength=wavelength_nm, 
        acceleration=True, boundary_handling=True,
        damping_threshold=None, # 1 sigma damping
        background_level=bg_level
    )

    print("Running FISTA Deconvolution (TV Reg, Boundary Handling)...")
    result_fista = fista_deconvolution(image_data, probe, iterations=15, lambda_reg=0.005, boundary_handling=True)

    # Post-processing: Radial Wiener Filter
    if apply_wiener:
        if use_p_spline:
            print("Applying P-spline Wiener Filter (2D Background Estimation)...")
            # Using lambda=1000.0 as a starting point for background smoothing
            result_add = p_spline_wiener_filter(np.abs(result_add), pixel_size, lambda_val=1000.0, information_limit=information_limit)
            result_mul = p_spline_wiener_filter(np.abs(result_mul), pixel_size, lambda_val=1000.0, information_limit=information_limit)
            result_fista = p_spline_wiener_filter(np.abs(result_fista), pixel_size, lambda_val=1000.0, information_limit=information_limit)
        else:
            print("Applying Radial Wiener Filter...")
            result_add = radial_wiener_filter(np.abs(result_add), pixel_size, information_limit)
            result_mul = radial_wiener_filter(np.abs(result_mul), pixel_size, information_limit)
            result_fista = radial_wiener_filter(np.abs(result_fista), pixel_size, information_limit)
    
    # Save Results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    write_mrc(output_path.replace(".mrc", "_add.mrc"), np.abs(result_add), pixel_size)
    write_mrc(output_path.replace(".mrc", "_mul.mrc"), np.abs(result_mul), pixel_size)
    write_mrc(output_path.replace(".mrc", "_fista.mrc"), np.abs(result_fista), pixel_size)
    
    print("Done.")

if __name__ == "__main__":
    main()

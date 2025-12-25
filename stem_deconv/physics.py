import numpy as np
from .utils import fft2, ifft2, fftshift, ifftshift

def calculate_wavelength(voltage_kv):
    """
    Calculate relativistic electron wavelength in nm.
    Args:
        voltage_kv (float): Acceleration voltage in kV.
    Returns:
        float: Wavelength in nm.
    """
    # Constants
    emass = 510.99906  # keV
    hc = 12.3984244    # keV * A
    
    # Formula: lambda = hc / sqrt(V * (2*m0*c^2 + V))
    # voltage_kv is V in the formula (but in kV units matching constants)
    wavelen_angstrom = hc / np.sqrt(voltage_kv * (2 * emass + voltage_kv))
    
    return wavelen_angstrom / 10.0  # Convert A to nm

def calculate_ctf(shape, pixel_size_nm, voltage_kv, 
                  cs3_mm, cs5_mm, defocus_nm, 
                  obj_aperture_rad, 
                  a2_amp_nm=0, a2_angle_rad=0,
                  a3_amp_nm=0, a3_angle_rad=0,
                  b2_amp_nm=0, b2_angle_rad=0,
                  focal_spread_nm=0, convergence_angle_rad=0):
    """
    Calculate the Contrast Transfer Function (CTF).
    
    Args:
        shape (tuple): (height, width) of the image.
        pixel_size_nm (float): Pixel size in nm.
        voltage_kv (float): Voltage in kV.
        cs3_mm (float): Spherical aberration (3rd order) in mm.
        cs5_mm (float): Spherical aberration (5th order) in mm.
        defocus_nm (float): Defocus in nm.
        obj_aperture_rad (float): Objective aperture in rad.
        a2_amp_nm (float): 2-fold astigmatism amplitude in nm.
        a2_angle_rad (float): 2-fold astigmatism angle in rad.
        a3_amp_nm (float): 3-fold astigmatism amplitude in nm.
        a3_angle_rad (float): 3-fold astigmatism angle in rad.
        b2_amp_nm (float): Axial coma (B2) amplitude in nm.
        b2_angle_rad (float): Axial coma (B2) angle in rad.
        focal_spread_nm (float): Focal spread in nm.
        convergence_angle_rad (float): Convergence angle in rad.
        
    Returns:
        np.ndarray: Complex CTF array.
    """
    ny, nx = shape
    wavelength_nm = calculate_wavelength(voltage_kv)
    wavelength_A = wavelength_nm * 10.0
    
    # Frequency grid setup
    # C++: delta_kx = 1.0 / (pixelSize * nx) (in 1/A)
    # We work in nm mostly, but let's stick to C++ units (Angstroms) for internal calc if needed
    # or convert everything to nm.
    # C++ uses Angstroms for k_square calculation: k_square = kx*kx + ky*ky (in 1/A^2)
    
    pixel_size_A = pixel_size_nm * 10.0
    
    ky = np.fft.fftfreq(ny, d=pixel_size_A)
    kx = np.fft.fftfreq(nx, d=pixel_size_A)
    KX, KY = np.meshgrid(kx, ky)
    
    K2 = KX**2 + KY**2 # k_square in 1/A^2
    K = np.sqrt(K2)
    
    # Aperture cutoff
    # kmax = alpha / lambda
    if obj_aperture_rad > 0.0001:
        kmax = obj_aperture_rad / wavelength_A
        kmax2 = kmax**2
    else:
        kmax2 = 1.0e7 # No aperture
        
    # Angle for astigmatism
    # C++: ang = acos((kx*kx + k_square - ky*ky) / (2*kx*k)) which simplifies to atan2(ky, kx) logic
    # but C++ handles quadrants manually. np.arctan2 is safer.
    # Note: C++ code has `if (ky < 0.0) ang = -ang;`
    PHI = np.arctan2(KY, KX)
    
    # Aberration function (Chi / Kai)
    # All parameters need to be in consistent units.
    # C++ uses Angstroms for wavelength and k.
    # Cs3 is in mm -> convert to Angstroms: * 1e7
    # Cs5 is in mm -> convert to Angstroms: * 1e7
    # Defocus is in nm -> convert to Angstroms: * 10
    # Astigmatism/Coma are in nm -> convert to Angstroms: * 10
    
    cs3_A = cs3_mm * 1e7
    cs5_A = cs5_mm * 1e7
    defocus_A = defocus_nm * 10.0
    a2_A = a2_amp_nm * 10.0
    a3_A = a3_amp_nm * 10.0
    b2_A = b2_amp_nm * 10.0
    
    # Phase shift calculation (Chi)
    # kai = 0.5 * defocus * k^2 * lambda^2 ... wait, C++ formula:
    # kai = 0.5 * defocus * k_square * wal2
    #     + 0.25 * Cs3 * k_square^2 * wal2^2  <-- Wait, standard formula is different?
    # Standard Chi(k) = 2*pi/lambda * (0.5*D*lambda^2*k^2 + 0.25*Cs*lambda^4*k^4)
    # C++: kai = kai * 2.0 * pi / wal;
    # So inside the sum it is:
    # 0.5 * defocus * k^2 * lambda^2
    # 0.25 * Cs3 * k^4 * lambda^4
    # This matches standard theory if k is spatial frequency (1/d).
    
    wal = wavelength_A
    wal2 = wal**2
    wal3 = wal**3
    
    term_defocus = 0.5 * defocus_A * K2 * wal2
    term_cs3 = 0.25 * cs3_A * (K2**2) * (wal2**2)
    term_cs5 = 0.16667 * cs5_A * (K2**3) * (wal3**2)
    
    term_a2 = 0.5 * a2_A * K2 * wal2 * np.cos(2.0 * (PHI - a2_angle_rad))
    term_b2 = 0.3333 * b2_A * K2 * K * wal3 * np.cos(PHI - b2_angle_rad)
    term_a3 = 0.3333 * a3_A * K2 * K * wal3 * np.cos(3.0 * (PHI - a3_angle_rad))
    
    kai = (term_defocus + term_cs3 + term_cs5 + term_a2 + term_b2 + term_a3)
    kai = kai * 2.0 * np.pi / wal
    
    # Envelope Functions
    # Spatial Coherence (Es)
    # Es1 = pi * conAngle * Cs3 * wal2 ??
    # C++: Es1 = pi * conAngle * Cs3 * wal2; Es2 = pi * conAngle; Es3 = Es2 * defocus;
    # Es = exp(-k_square * (Es1*k_square + Es3)^2)
    # This looks like damping due to source size / convergence.
    
    es1 = np.pi * convergence_angle_rad * cs3_A * wal2
    es2 = np.pi * convergence_angle_rad
    es3 = es2 * defocus_A
    
    # Note: C++ code uses `k_square` in the exponent.
    # Es = exp(-k_square * (Es1*k_square + Es3)*(Es1*k_square + Es3))
    # Wait, `Es1*k_square`? Usually it's `Cs*lambda^2*k^2`.
    # Let's stick to the C++ implementation exactly.
    
    Es_exponent = -K2 * (es1 * K2 + es3)**2
    Es = np.exp(Es_exponent)
    
    # Chromatic Coherence (Ecc)
    # Ec = -0.5 * pi^2 * wal2 * focalSpread^2
    # Ecc = exp(Ec * k_square^2) ... wait C++ says:
    # Ecc = exp(Ec * k_square * k_square)
    # focalSpread is in nm -> convert to A: * 10
    focal_spread_A = focal_spread_nm * 10.0
    Ec = -0.5 * (np.pi**2) * wal2 * (focal_spread_A**2)
    Ecc = np.exp(Ec * (K2**2))
    
    Envelope = Es * Ecc
    
    # CTF
    # C++: CTF[index][0] = Esc * cosf(kai);
    #      CTF[index][1] = -Esc * sinf(kai);
    # So CTF = Envelope * (cos(kai) - i * sin(kai)) = Envelope * exp(-i * kai)
    
    CTF = Envelope * np.exp(-1j * kai)
    
    # Apply Aperture
    mask = K2 < kmax2
    CTF = CTF * mask
    
    return CTF

def calculate_probe(ctf, xp=0, yp=0):
    """
    Calculate the Probe function from the CTF.
    Probe = IFFT(CTF) (Complex wavefunction).
    
    Args:
        ctf (np.ndarray): Complex CTF.
        xp (float): Probe position x (unused in C++ due to cos(90)=0).
        yp (float): Probe position y (unused in C++ due to cos(90)=0).
        
    Returns:
        np.ndarray: Complex Probe.
    """
    # C++: 
    # k = (kx * xp + ky * yp + kx * yp + ky * xp) * cosf(90.0f * pi / 180.0f);
    # Since cos(90) is 0, k is always 0.
    # probe[index][0] = cos(0)*CTF[0] - sin(0)*CTF[1] = CTF[0]
    # probe[index][1] = cos(0)*CTF[1] + sin(0)*CTF[0] = CTF[1]
    # So probe is initialized with CTF.
    
    # fftwf_execute_dft(planIFFT, probe, probe); // reciprocal -> real
    # p.Rearrange(probe, sx, sy); // fftshift
    
    # Note: The CTF generated by calculate_ctf has zero frequency at corners (standard FFT layout).
    # So we can directly apply IFFT.
    
    probe = ifft2(ctf)
    
    # C++ Rearrange puts zero frequency at center.
    probe = fftshift(probe)
    
    # Effective Probe Calculation (Intensity)
    # C++:
    # for (int i = 0; i < N; ++i)
    # {
    #     probe[i][0] = (probe[i][0] * probe[i][0] + probe[i][1] * probe[i][1]);
    #     probe[i][1] = 0.0f;
    # }
    # This means the probe used for deconvolution is actually the intensity |Psi|^2,
    # and the imaginary part is set to 0.
    
    probe_intensity = np.abs(probe)**2
    # Return as complex array with 0 imaginary part to match C++ structure if needed,
    # or just real array since imaginary part is explicitly 0.
    # The deconvolution functions cast to complex64 anyway.
    
    return probe_intensity.astype(np.complex64)


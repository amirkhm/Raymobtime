import numpy as np
from src.modules.postprocessing.mimo_channels import (
    arrayFactorGivenAngleForULA,
    dft_codebook,
    dft_codebook_upa,
    rotate_vectors
)

def test_arrayFactorGivenAngleForULA_broadside_and_magnitude():
    num_antennas = 4
    theta = np.pi / 2
    normalized_dist = 0.5
    
    
    af_normal = arrayFactorGivenAngleForULA(
        numAntennaElements=num_antennas, 
        theta=theta, 
        normalizedAntDistance=normalized_dist, 
        angleWithArrayNormal=1
    )
    
    expected_magnitude = 1 / np.sqrt(num_antennas)
    np.testing.assert_allclose(np.abs(af_normal), expected_magnitude, rtol=1e-5)
    
    # ULA Steering vector phase modeling for angleWithArrayNormal=1:
    # a(\theta) = (1/\sqrt{N}) * \exp(-j * 2\pi * d * \sin(\theta) * k)
    indices = np.arange(num_antennas)
    expected_af = np.exp(-1j * np.pi * indices) / np.sqrt(num_antennas)
    np.testing.assert_allclose(af_normal, expected_af, rtol=1e-5)

def test_dft_codebook_orthogonality():
    dim = 4
    
    w = dft_codebook(dim)
    
    identity_check = (w.conj().T @ w) / dim
    np.testing.assert_allclose(identity_check, np.eye(dim), atol=1e-10)

def test_dft_codebook_upa_dimensions():
    rows = 2
    cols = 3
    expected_dim = rows * cols
    
    w_upa = dft_codebook_upa(rows, cols)
    
    assert w_upa.shape == (expected_dim, expected_dim)
    identity_check = (w_upa.conj().T @ w_upa) / expected_dim
    np.testing.assert_allclose(identity_check, np.eye(expected_dim), atol=1e-10)

def test_rotate_vectors_yaw_90_degrees():
    azimuths = [0.0, 90.0]
    zeniths = [90.0, 90.0] 
    alpha = 90.0 
    beta = 0.0
    gamma = 0.0
    
    rot_az, rot_zen = rotate_vectors(azimuths, zeniths, alpha, beta, gamma)
    
    np.testing.assert_allclose(rot_az, [90.0, 180.0], atol=1e-5)
    np.testing.assert_allclose(rot_zen, [90.0, 90.0], atol=1e-5)
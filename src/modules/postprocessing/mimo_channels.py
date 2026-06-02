import numpy as np
import pandas as pd
import math

def arrayFactorGivenAngleForULA(
    numAntennaElements,
    theta,
    normalizedAntDistance=0.5,
    angleWithArrayNormal=0
):
    """
    Compute the normalized array response vector for a Uniform Linear Array.

    This function calculates the steering vector of a ULA for a given incident
    or departure angle. The angle can be interpreted either with respect to the
    array normal or using the default cosine-based convention.

    Args:
        numAntennaElements: Number of antenna elements in the ULA.
        theta: Angle in radians used to compute the array response.
        normalizedAntDistance: Antenna spacing normalized by the wavelength.
            Defaults to 0.5.
        angleWithArrayNormal: If set to 1, the angle is interpreted with
            respect to the array normal using ``sin(theta)``. Otherwise,
            ``cos(theta)`` is used. Defaults to 0.

    Returns:
        A normalized complex array response vector with unit norm.
    """
    indices = np.arange(numAntennaElements)
    if (angleWithArrayNormal == 1):
        arrayFactor = np.exp(-1j * 2 * np.pi * normalizedAntDistance * indices * np.sin(theta))
    else:  # default
        arrayFactor = np.exp(-1j * 2 * np.pi * normalizedAntDistance * indices * np.cos(theta))
    return arrayFactor / np.sqrt(numAntennaElements)  # normalize to have unitary norm

def getNarrowBandULAMIMOChannel(
    azimuths_tx,
    azimuths_rx,
    p_gainsdB,
    number_Tx_antennas,
    number_Rx_antennas,
    normalizedAntDistance=0.5,
    angleWithArrayNormal=0,
    pathPhases=None
):
    """
    Compute a narrowband MIMO channel matrix using ULA arrays at TX and RX.

    This function builds the narrowband channel matrix by summing the
    contribution of all propagation rays. Each ray is represented by its
    transmit azimuth, receive azimuth, path gain, and phase. If path phases are
    not provided, random phases are generated.

    Args:
        azimuths_tx: Transmit azimuth angles in degrees for each propagation ray.
        azimuths_rx: Receive azimuth angles in degrees for each propagation ray.
        p_gainsdB: Path gains in dB for each propagation ray.
        number_Tx_antennas: Number of transmit antenna elements.
        number_Rx_antennas: Number of receive antenna elements.
        normalizedAntDistance: Antenna spacing normalized by the wavelength.
            Defaults to 0.5.
        angleWithArrayNormal: Angle convention flag passed to
            ``arrayFactorGivenAngleForULA``. Defaults to 0.
        pathPhases: Optional path phases in degrees. If ``None``, random phases
            are generated.

    Returns:
        Complex narrowband MIMO channel matrix with shape
        ``(number_Rx_antennas, number_Tx_antennas)``.
    """
    
    azimuths_tx = np.deg2rad(azimuths_tx)
    azimuths_rx = np.deg2rad(azimuths_rx)
    # nt = number_Rx_antennas * number_Tx_antennas #np.power(antenna_number, 2)
    m = np.shape(azimuths_tx)[0]  # number of rays
    H = np.matrix(np.zeros((number_Rx_antennas, number_Tx_antennas)))

    gain_dB = p_gainsdB
    path_gain = np.power(10, gain_dB / 10)
    path_gain = np.sqrt(path_gain)

    #generate uniformly distributed random phase in radians
    if pathPhases is None:
        pathPhases = 2*np.pi * np.random.rand(len(path_gain))
    else:
        #convert from degrees to radians
        pathPhases = np.deg2rad(pathPhases)

    #include phase information, converting gains in complex-values
    path_complexGains = path_gain * np.exp(1j * pathPhases)

    # recall that in the narrowband case, the time-domain H is the same as the
    # frequency-domain H
    for i in range(m):
        at = np.matrix(arrayFactorGivenAngleForULA(number_Tx_antennas, azimuths_tx[i], normalizedAntDistance,
                                                   angleWithArrayNormal))
        ar = np.matrix(arrayFactorGivenAngleForULA(number_Rx_antennas, azimuths_rx[i], normalizedAntDistance,
                                                   angleWithArrayNormal))
        H = H + path_complexGains[i] * ar.conj().T * at  # outer product of ar Hermitian and at
        #H = H + path_complexGains[i] * ar
    # factor = (np.linalg.norm(path_complexGains) / np.sum(path_complexGains)) * np.sqrt(
    #     number_Rx_antennas * number_Tx_antennas)  # scale channel matrix
    # H *= factor  # normalize for compatibility with Anum's Matlab code

    return H

def watts_to_dbm(power_watts):
    """
    Convert power from watts to dBm.

    Args:
        power_watts: Power value in watts.

    Returns:
        Power value converted to dBm.
    """
    dbm = 10 * math.log10(power_watts * 1000)
    return dbm

def dbm_to_watts(dbm):
    """
    Convert power from dBm to watts.

    Args:
        dbm: Power value in dBm.

    Returns:
        Power value converted to watts.
    """
    return 10 ** (dbm / 10)

def degrees_to_radians(degrees):
    """
    Convert angles from degrees to radians.

    Args:
        degrees: Angle in degrees.

    Returns:
        Angle in radians.
    """
    return np.radians(degrees)

def dft_codebook(dim):
    """
    Generate a Discrete Fourier Transform codebook matrix.

    This function creates a square DFT matrix of size ``dim x dim``. The matrix
    can be used as a beamforming or combining codebook.

    Args:
        dim: Number of antenna elements or codebook dimension.

    Returns:
        A complex DFT codebook matrix.
    """

    seq = np.matrix(np.arange(dim))
    mat = seq.conj().T * seq
    w = np.exp(-1j * 2 * np.pi * mat / dim)
    return w

def getDFTOperatedChannel(H, number_Tx_antennas, number_Rx_antennas):
    """
    Apply DFT precoding and combining to a MIMO channel matrix.

    This function generates DFT codebooks for the transmitter and receiver and
    applies them to the channel matrix to obtain the equivalent beamspace
    channel.

    Args:
        H: MIMO channel matrix.
        number_Tx_antennas: Number of transmit antenna elements.
        number_Rx_antennas: Number of receive antenna elements.

    Returns:
        Equivalent channel after DFT precoding and combining.
    """
    wt = dft_codebook(number_Tx_antennas)
    wr = dft_codebook(number_Rx_antennas)
    dictionaryOperatedChannel = wr.conj().T * H * wt

    return dictionaryOperatedChannel  # return equivalent channel after precoding and combining

'''def deep_mimo_array_response(Dod, DoA, M_TX, M_RX, fc, c=3e8):
     # TX Array Response - BS
    gamma_TX = 1j * kd_TX * np.array([np.sin(np.radians(DoD_theta)) * np.cos(np.radians(DoD_phi)),
                                      np.sin(np.radians(DoD_theta)) * np.sin(np.radians(DoD_phi)),
                                      np.cos(np.radians(DoD_theta))])
    array_response_TX = np.exp(M_TX_ind @ gamma_TX)

    # RX Array Response - UE or BS
    gamma_RX = 1j * kd_RX * np.array([np.sin(np.radians(DoA_theta)) * np.cos(np.radians(DoA_phi)),
                                      np.sin(np.radians(DoA_theta)) * np.sin(np.radians(DoA_phi)),
                                      np.cos(np.radians(DoA_theta))])
    array_response_RX = np.exp(M_RX_ind @ gamma_RX)'''

def dft_codebook_upa(rows, cols):
    """
    Generate a DFT codebook for a Uniform Planar Array.

    This function creates a 2D UPA codebook by computing the Kronecker product
    of two 1D DFT codebooks, one for the row dimension and one for the column
    dimension.

    Args:
        rows: Number of antenna elements along the row dimension.
        cols: Number of antenna elements along the column dimension.

    Returns:
        Complex DFT codebook matrix for a UPA with ``rows * cols`` elements.
    """
    
    # DFT matrices for rows and columns
    w_row = dft_codebook(rows)
    w_col = dft_codebook(cols)
    
    # Create 2D codebook by outer product
    upa_codebook = np.kron(w_row, w_col)  # Kronecker product to create 2D beams
    return upa_codebook

def calc_omega(elevationAngles, azimuthAngles, normalizedAntDistance=0.5):
    """
    Compute spatial frequency components for UPA array responses.

    This function calculates the x and y spatial frequency terms associated
    with the given elevation and azimuth angles.

    Args:
        elevationAngles: Elevation angles in radians.
        azimuthAngles: Azimuth angles in radians.
        normalizedAntDistance: Antenna spacing normalized by the wavelength.
            Defaults to 0.5.

    Returns:
        A 2-row matrix containing the x and y spatial frequency components.
    """
    sinElevations = np.sin(elevationAngles)
    omegax = 2 * np.pi * normalizedAntDistance * sinElevations * np.cos(azimuthAngles)  #x
    omegay = 2 * np.pi * normalizedAntDistance * sinElevations * np.sin(azimuthAngles)  #y
    #omegay = 2 * np.pi * normalizedAntDistance * np.cos(elevationAngles)  #new          #z
    return np.matrix((omegax, omegay))

def calc_vec_i(i, omega, antenna_range):
    """
    Compute the Kronecker array response vector for one propagation ray.

    Args:
        i: Index of the propagation ray.
        omega: Matrix containing spatial frequency components.
        antenna_range: Array of antenna element indices.

    Returns:
        Complex array response vector for the selected ray.
    """
    print('a ', omega[:, i])
    print('b ', omega[:, i].shape)
    vec = np.exp(1j * omega[:, i] * antenna_range)
    print('c ', np.matrix(np.kron(vec[1], vec[0])).shape)
    return np.matrix(np.kron(vec[1], vec[0]))

def getNarrowBandUPAMIMOChannel(
    departureElevation,
    departureAzimuth,
    arrivalElevation,
    arrivalAzimuth,
    p_gainsdB,
    pathPhases,
    number_Tx_antennasX,
    number_Tx_antennasY,
    number_Rx_antennasX,
    number_Rx_antennasY,
    normalizedAntDistance=0.5
):
    """
    Compute a narrowband MIMO channel matrix using UPA arrays at TX and RX.

    This function builds the MIMO channel matrix by summing the contribution of
    each propagation ray. Each ray is defined by departure and arrival elevation
    and azimuth angles, path gain, and phase. Uniform Planar Arrays are assumed
    at both transmitter and receiver.

    Args:
        departureElevation: Departure elevation angles in degrees.
        departureAzimuth: Departure azimuth angles in degrees.
        arrivalElevation: Arrival elevation angles in degrees.
        arrivalAzimuth: Arrival azimuth angles in degrees.
        p_gainsdB: Path gains in dB for each propagation ray.
        pathPhases: Path phases in degrees. If ``None``, random phases are
            generated.
        number_Tx_antennasX: Number of transmit antenna elements along x.
        number_Tx_antennasY: Number of transmit antenna elements along y.
        number_Rx_antennasX: Number of receive antenna elements along x.
        number_Rx_antennasY: Number of receive antenna elements along y.
        normalizedAntDistance: Antenna spacing normalized by the wavelength.
            Defaults to 0.5.

    Returns:
        Complex narrowband MIMO channel matrix with shape
        ``(number_Rx_antennasX * number_Rx_antennasY,
        number_Tx_antennasX * number_Tx_antennasY)``.
    """
    number_Tx_antennas = number_Tx_antennasX * number_Tx_antennasY
    number_Rx_antennas = number_Rx_antennasX * number_Rx_antennasY
    departureElevation = np.deg2rad(departureElevation)
    departureAzimuth = np.deg2rad(departureAzimuth)
    arrivalElevation = np.deg2rad(arrivalElevation)
    arrivalAzimuth = np.deg2rad(arrivalAzimuth)

    numRays = np.shape(departureElevation)[0]
    #number_Rx_antennas is the total number of antenna elements of the array, idem Tx
    H = np.matrix(np.zeros((number_Rx_antennas, number_Tx_antennas)))

    path_gain = np.power(10, p_gainsdB / 10)

    #generate uniformly distributed random phase in radians
    if pathPhases is None:
        pathPhases = 2*np.pi * np.random.rand(len(path_gain))
    else:
        #convert from degrees to radians the phase obtained with simulator (InSite)
        pathPhases = np.deg2rad(pathPhases)

    #include phase information, converting gains in complex-values
    path_complexGains = path_gain * np.exp(1j * pathPhases)

    # recall that in the narrowband case, the time-domain H is the same as the
    # frequency-domain H
    # Each vector below has the x and y values for each ray. Example 2 x 25 dimension
    departure_omega = calc_omega(departureElevation, departureAzimuth, normalizedAntDistance)
    arrival_omega = calc_omega(arrivalElevation, arrivalAzimuth, normalizedAntDistance)

    rangeTx_x = np.arange(number_Tx_antennasX)
    rangeTx_y = np.arange(number_Tx_antennasY)
    rangeRx_x = np.arange(number_Rx_antennasX)
    rangeRx_y = np.arange(number_Rx_antennasY)
    
    # Normalization factors eq (7.25) Tse's book
    norm_Tx = 1/np.sqrt(number_Tx_antennasX * number_Tx_antennasY)  # Tx array normalization
    norm_Rx = 1/np.sqrt(number_Rx_antennasX * number_Rx_antennasY)  # Rx array normalization
    
    for ray_i in range(numRays):
        #departure
        vecx = np.exp(-1j * departure_omega[0,ray_i] * rangeTx_x)
        vecy = np.exp(-1j * departure_omega[1,ray_i] * rangeTx_y)
        departure_vec = norm_Tx * np.matrix(np.kron(vecx, vecy)) #1xn             #y x expands first x then y
        #arrival
        vecx = np.exp(-1j * arrival_omega[0,ray_i] * rangeRx_x)
        vecy = np.exp(-1j * arrival_omega[1,ray_i] * rangeRx_y)
        arrival_vec = norm_Rx * np.matrix(np.kron(vecx, vecy)) #1xn

        antenna_pattern_gain_Tx = 1
        antenna_pattern_gain_Rx = 1
        pattern_gain = antenna_pattern_gain_Tx * antenna_pattern_gain_Rx

        # eq (7.29) Tse's book 
        H = H + path_complexGains[ray_i] * pattern_gain * arrival_vec.T * departure_vec.conj()
    return H

def getCodebookOperatedChannel(H, Wt, Wr):
    """
    Apply transmit and receive codebooks to a MIMO channel matrix.

    This function computes the equivalent beamspace channel after precoding and
    combining. It also supports single-antenna cases where either the transmit
    or receive codebook is ``None``.

    Args:
        H: MIMO channel matrix.
        Wt: Transmit precoding codebook. If ``None``, no transmit precoding is
            applied.
        Wr: Receive combining codebook. If ``None``, no receive combining is
            applied.

    Returns:
        Equivalent channel after applying the available codebooks.
    """
    if Wr is None: #only 1 antenna at Rx, and Wr was passed as None
        return H * Wt
    if Wt is None: #only 1 antenna at Tx
        return Wr.conj().T * H
    try:
        result = Wr.conj().T * H * Wt
    except Exception as e:
        print(f'ERROR: {e}')
    return result # return equivalent channel after precoding and combining

def rotate_vectors(azimuths, zeniths, alpha, beta, gamma):
    """
    Rotate spherical direction vectors and return the rotated angles.

    This function converts azimuth and zenith angles to Cartesian unit vectors,
    applies rotations around the z, y, and x axes, and converts the rotated
    vectors back to spherical angles.

    Args:
        azimuths: Azimuth angles in degrees.
        zeniths: Zenith angles in degrees.
        alpha: Rotation angle around the z axis in degrees.
        beta: Rotation angle around the y axis in degrees.
        gamma: Rotation angle around the x axis in degrees.

    Returns:
        A tuple containing:
            - rotated_azimuths: Rotated azimuth angles in degrees.
            - rotated_zeniths: Rotated zenith angles in degrees.
    """
    # Convert list to arrays numpy
    azimuths = np.array(azimuths)
    zeniths = np.array(zeniths)
    
    # Convert angles to radians
    alpha, beta, gamma = np.radians([alpha, beta, gamma])
    
    # Rotation matrix arround WI Z axis
    Rz = np.array([
        [np.cos(alpha), -np.sin(alpha), 0],
        [np.sin(alpha), np.cos(alpha), 0],
        [0, 0, 1]
    ])
    
    # Rotation matrix arround WI Y axis
    Ry = np.array([
        [np.cos(beta), 0, np.sin(beta)],
        [0, 1, 0],
        [-np.sin(beta), 0, np.cos(beta)]
    ])
    
    # Rotation matrix arround WI X axis
    Rx = np.array([
        [1, 0, 0],
        [0, np.cos(gamma), -np.sin(gamma)],
        [0, np.sin(gamma), np.cos(gamma)]
    ])
    
    # Total rotation matrix R = Rx * Ry * Rz
    R = Rx @ Ry @ Rz
    
    # Convert azimuth and zenith to cartesian coordinates
    x = np.sin(np.radians(zeniths)) * np.cos(np.radians(azimuths))
    y = np.sin(np.radians(zeniths)) * np.sin(np.radians(azimuths))
    z = np.cos(np.radians(zeniths))
    
    # Apply rotation
    rotated_vectors = R @ np.vstack((x, y, z))
    
    # Convert back to spherical coordinates
    rotated_zeniths = np.degrees(np.arccos(rotated_vectors[2]))
    rotated_azimuths = np.degrees(np.arctan2(rotated_vectors[1], rotated_vectors[0]))
    
    # Ensure that azimuths are in the range [0, 360]
    rotated_azimuths = np.mod(rotated_azimuths, 360)
    
    # Convert arrays to lists
    return rotated_azimuths.tolist(), rotated_zeniths.tolist()
    
def import_mimo_channel(H_csv):
    """
    Import a complex MIMO channel matrix from a Wireless InSite CSV file.

    This function reads an H-matrix CSV file exported by Wireless InSite,
    identifies the number of receiver and transmitter elements, and reconstructs
    the complex channel matrix from real and imaginary columns.

    Args:
        H_csv: Path to the Wireless InSite H-matrix CSV file.

    Returns:
        Complex MIMO channel matrix with shape ``(num_rx, num_tx)``.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
        KeyError: If the expected ``<Rx Element>`` column is missing.
        ValueError: If real or imaginary entries cannot be converted to complex
            values.
    """
    # Load CSV ignoring comment lines
    # csvName is a string
    df = pd.read_csv(H_csv, header=3)#comment="#", header=0 
    num_rx = df["<Rx Element>"].nunique()  # Count unique Rx elements
    num_tx = (df.shape[1] - 2) // 2  # Each Tx has 2 columns (real and imaginary)

    # Initialize matrix H (Rx x Tx) as an array of complex numbers
    H = np.zeros((num_rx, num_tx), dtype=complex)

    # Fill the matrix H
    for i, row in df.iterrows():
        rx_index = int(row["<Rx Element>"]) - 1  # Adjustment for index 0
        for tx_index in range(num_tx):
            real_part = row.iloc[2 + 2 * tx_index]  # Real column
            imag_part = row.iloc[3 + 2 * tx_index]  # Imaginary column
            H[rx_index, tx_index] = complex(real_part, imag_part)
    return H

def calc_rx_power(departure_angle, arrival_angle, p_gain, antenna_number, frequency=6e10):
    """This .m file uses a m*m SQUARE UPA, so the antenna number at TX, RX will be antenna_number^2.

    - antenna_number^2 number of element arrays in TX, same in RX
    - assumes one beam per antenna element

    the first column will be the elevation angle, and the second column is the azimuth angle correspondingly.
    p_gain will be a matrix size of (L, 1)
    departure angle/arrival angle will be a matrix as size of (L, 2), where L is the number of paths

    t1 will be a matrix of size (nt, nr), each
    element of index (i,j) will be the received
    power with the i-th precoder and the j-th
    combiner in the departing and arrival codebooks
    respectively

    :param departure_angle: ((elevation angle, azimuth angle),) (L, 2) where L is the number of paths
    :param arrival_angle: ((elevation angle, azimuth angle),) (L, 2) where L is the number of paths
    :param p_gain: path gain (L, 1) where L is the number of paths
    :param antenna_number: antenna number at TX, RX is antenna_number**2
    :param frequency: default
    :return:
    """
    departure_angle = np.deg2rad(departure_angle)
    arrival_angle = np.deg2rad(arrival_angle)
    c = 3e8
    mlambda = c / frequency
    k = 2 * np.pi / mlambda
    d = mlambda / 2
    nt = np.power(antenna_number, 2)
    m = np.shape(departure_angle)[0]
    nr = nt
    wt = dft_codebook(nt)
    wr = dft_codebook(nr)
    H = np.matrix(np.zeros((nt, nr)))

    # TO DO: need to generate random phase and convert gains in complex-values
    gain_dB = p_gain
    path_gain = np.power(10, gain_dB / 10)
    antenna_range = np.arange(antenna_number)

    def calc_omega(angle):
        sin = np.sin(angle)
        omegay = k * d * sin[:, 1] * sin[:, 0]
        omegax = k * d * sin[:, 0] * np.cos(angle[:, 1])
        return np.matrix((omegax, omegay))

    departure_omega = calc_omega(departure_angle)
    arrival_omega = calc_omega(arrival_angle)

    def calc_vec_i(i, omega, antenna_range):
        vec = np.exp(1j * omega[:, i] * antenna_range)
        return np.matrix(np.kron(vec[1], vec[0]))

    for i in range(m):
        departure_vec = calc_vec_i(i, departure_omega, antenna_range)
        arrival_vec = calc_vec_i(i, arrival_omega, antenna_range)
        H = H + path_gain[i] * departure_vec.conj().T * arrival_vec
    t1 = wt.conj().T * H * wr
    return t1
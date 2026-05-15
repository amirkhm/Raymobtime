import numpy as np

def compute_pixel_position(
    Pob, # [x, y, z] no mundo (X=frente, Y=esquerda, Z=cima)
    Pcam, # [x, y, z] no mundo
    yaw, # Z rotation
    roll, # x rotation
    pitch, # y rotation
    K
    ):
    # 1. Vetor relativo (objeto - câmera)
    # vetor_relativo = np.array(Pob) - np.array(Pcam)

    # 2. Matriz de rotação do azimuth (rotação em Z)
    cos_phi = np.cos(yaw)
    sin_phi = np.sin(yaw)
    Rz = np.array([
    [cos_phi, -sin_phi, 0],
    [sin_phi, cos_phi, 0],
    [0, 0, 1]
    ])

    cos_phi = np.cos(roll)
    sin_phi = np.sin(roll)
    Rx = np.array([
    [1, 0, 0],
    [0, cos_phi, -sin_phi],
    [0, sin_phi, cos_phi]
    ])

    # 3. Matriz de rotação da elevação (rotação em Y)
    cos_theta = np.cos(pitch)
    sin_theta = np.sin(pitch)
    Ry = np.array([
    [cos_theta, 0, -sin_theta],
    [0, 1, 0],
    [sin_theta, 0, cos_theta]
    ])

    # 4. Rotação total: R = Ry(φ) * Rz(θ)
    R = np.dot(Ry.T, Rx.T)
    R = np.dot(Rz.T, R)

    # 5. Aplica a rotação ao vetor relativo
    P_obj_cam = np.dot(R, Pob - Pcam)

    # 6. Ajusta os eixos para o sistema da câmera:
    # x_c = -P_obj_cam[1] # -Y global vira X da câmera (direita positivo)
    # y_c = -P_obj_cam[2] # -Z global vira Y da câmera (para baixo positivo)
    # z_c = P_obj_cam[0] # X global vira Z da câmera (profundidade)

    # Blender Cam points to Y positive global
    x_c = P_obj_cam[0] # X global vira X da câmera (direita positivo)
    y_c = -P_obj_cam[2] # -Z global vira Y da câmera (para baixo positivo)
    z_c = P_obj_cam[1] # Y global vira Z da câmera (profundidade)

    # Projeção no plano da imagem
    if z_c <= 0:
        raise ValueError("O objeto está atrás da câmera!")

    print("Posições do carro relativo a imagem")
    print(x_c, y_c, z_c)

    # Conversão para coordenadas de imagem
    p_img = K @ np.array([x_c/z_c, y_c/z_c, 1])
    u, v, _ = p_img
    return u, v
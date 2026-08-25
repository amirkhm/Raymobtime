import pytest
import numpy as np
from unittest.mock import patch, mock_open
from typing import Dict, Any

from src.modules.data_processing.sumoOutputFile import angle_sumo2wi, read_csv_sumo

class TestSumoOutputFile:
    @pytest.mark.parametrize(
        "angle_sumo, expected_wi",
        [
            (0.0, 90.0),      # SUMO Norte -> WI Norte
            (90.0, 0.0),      # SUMO Leste -> WI Leste
            (270.0, 180.0),   # SUMO Oeste -> WI Oeste
            (360.0, 90.0),    # SUMO Norte -> WI Norte
            (450.0, 0.0),     # Excedente rotacional Leste
        ],
    )
    def test_angle_sumo2wi_normalization(self, angle_sumo: float, expected_wi: float) -> None:
        result: float = angle_sumo2wi(angle_sumo)
        assert np.isclose(result, expected_wi)

    @patch(
        "builtins.open", 
        new_callable=mock_open, 
        read_data=(
            "episode,1,2,3,4,vehID,6,7,pos_x,pos_y,10,11,12,13,angle,15,16,17,pos_z\n"
            "data_run,1,2,3,4,v_001,6,7,10.0,20.0,10,11,12,13,90.0,15,16,17,5.0\n"
        )
    )
    def test_read_csv_sumo_data_extraction(self, mock_csv: Any) -> None:
        expected_position: np.ndarray = np.array([10.0, 20.0, 5.0], dtype=np.float64)
        expected_angle_wi: float = 0.0  # (90 - 90) % 360
        
        result: Dict[str, Any] = read_csv_sumo("dummy_trajectory.csv")
        
        assert "v_001" in result
        assert np.allclose(result["v_001"]["position"], expected_position)
        assert np.isclose(result["v_001"]["angle"], expected_angle_wi)
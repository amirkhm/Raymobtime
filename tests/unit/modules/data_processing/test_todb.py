import pytest
from unittest.mock import patch
from typing import Any
import numpy as np

from src.modules.data_processing.todb import set_angle_range, count_model_paths

class TestToDB:
    @pytest.mark.parametrize(
        "input_angle, expected_angle",
        [
            (190.0, -170.0),
            (-190.0, 170.0),
            (0.0, 0.0),
            (180.0, 180.0),
            (360.0, 0.0),
            (-360.0, 0.0),
        ],
    )
    def test_set_angle_range_boundary_limits(self, input_angle: float, expected_angle: float) -> None:
        assert np.isclose(set_angle_range(input_angle), expected_angle)

    @patch("os.walk")
    def test_count_model_paths_directory_traversal(self, mock_walk: Any) -> None:
        mock_walk.return_value = [
            ("/sim_data/study_01", [], ["model.paths.t001_01.r002.p2m", "metadata.json"]),
            ("/sim_data/study_02", [], ["model.paths.t001_01.r003.p2m", "other_file.txt"]),
            ("/sim_data/study_03", [], ["ignore_this.csv"]),
        ]
        
        count: int = count_model_paths("/sim_data")
        
        assert count == 2
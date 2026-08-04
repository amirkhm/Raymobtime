import pytest
import numpy as np
from typing import Any

from src.modules.data_processing.save5gmdata import InsiteObject, Scene, Ray
from src.modules.rt.wi.modeling.errors import FormatError

class TestInsiteObject:
    def test_dimension_array_assignment(self) -> None:
        obj: InsiteObject = InsiteObject()
        expected_dim: np.ndarray = np.array([4.0, 2.0, 1.5], dtype=np.float64)
        
        obj.dimension = expected_dim
        
        assert np.allclose(obj.dimension, expected_dim)

    def test_dimension_invalid_shape_raises_format_error(self) -> None:
        obj: InsiteObject = InsiteObject()
        invalid_dim: np.ndarray = np.array([4.0, 2.0], dtype=np.float64)
        
        with pytest.raises(FormatError):
            obj.dimension = invalid_dim

    def test_vertice_array_coercion_and_shape(self) -> None:
        obj: InsiteObject = InsiteObject()
        vertices: np.ndarray = np.array(
            [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [2.0, 2.0, 2.0]], 
            dtype=np.float64
        )
        
        obj.vertice_array = vertices
        
        assert obj.vertice_array.shape[1] == 3
        assert np.allclose(obj.vertice_array, vertices)

class TestScene:
    def test_study_area_boundary_assignment(self) -> None:
        scene: Scene = Scene()
        bounds: np.ndarray = np.array(
            [[0.0, 0.0, 0.0], [843.0, 523.0, 50.0]], 
            dtype=np.float64
        )
        
        scene.study_area = bounds
        
        assert scene.study_area.shape == (2, 3)
        assert np.allclose(scene.study_area, bounds)

class TestRay:
    @pytest.mark.parametrize(
        "interactions, expected_los",
        [
            ("1-2", True),
            ("1-2-3", False),
            ("1-2-3-4", False),
            ("", False),
        ],
    )
    def test_line_of_sight_parsing(self, interactions: str, expected_los: bool) -> None:
        ray: Ray = Ray(interactions=interactions)
        assert ray.is_los is expected_los
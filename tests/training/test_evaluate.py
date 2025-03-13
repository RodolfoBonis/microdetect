# tests/training/test_evaluate.py
import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from microdetect.training.evaluate import ModelEvaluator


@pytest.fixture
def mock_yolo_results():
    """Create a mock for YOLO validation results."""
    mock_results = MagicMock()

    # Configure mock for box metrics
    mock_results.box = MagicMock()
    mock_results.box.map = 0.85  # mAP50-95
    mock_results.box.map50 = 0.92  # mAP50
    mock_results.box.recall = 0.88
    mock_results.box.precision = 0.90

    # Configure per-class metrics
    mock_results.box.ap_class_index = np.array([0, 1, 2])
    mock_results.box.ap50 = np.array([0.95, 0.90, 0.85])
    mock_results.box.r = np.array([0.92, 0.87, 0.82])  # Recall
    mock_results.box.p = np.array([0.94, 0.89, 0.84])  # Precision

    # Configure class names
    mock_results.names = {0: "0-levedura", 1: "1-fungo", 2: "2-micro-alga"}

    return mock_results


@pytest.fixture
def output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def model_path():
    """Create a temporary file to represent a model path."""
    with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as temp:
        temp_path = temp.name

    # Return the path and ensure it's cleaned up after the test
    yield temp_path
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@patch("microdetect.training.evaluate.YOLO")
def test_evaluate_model(mock_yolo, mock_yolo_results, model_path):
    """Test evaluating a model and extracting metrics."""
    # Configure YOLO mock
    mock_model = MagicMock()
    mock_model.val.return_value = mock_yolo_results
    mock_yolo.return_value = mock_model

    # Create evaluator
    evaluator = ModelEvaluator()

    # Call evaluate_model with actual file path that exists
    metrics = evaluator.evaluate_model(model_path, "path/to/data.yaml")

    # Check that YOLO was initialized and validate was called
    mock_yolo.assert_called_once_with(model_path)
    mock_model.val.assert_called_once_with(data="path/to/data.yaml", conf=0.25, iou=0.7)

    # Check extracted metrics
    assert "metricas_gerais" in metrics
    assert "metricas_por_classe" in metrics

    # Check general metrics
    general_metrics = metrics["metricas_gerais"]
    assert general_metrics["Precisão (mAP50)"] == 0.92
    assert general_metrics["Precisão (mAP50-95)"] == 0.85
    assert general_metrics["Recall"] == 0.88
    assert general_metrics["Precisão"] == 0.90

    # Check class metrics
    class_metrics = metrics["metricas_por_classe"]
    assert len(class_metrics) == 3

    # Check first class metrics
    assert class_metrics[0]["Classe"] == "0-levedura"
    assert class_metrics[0]["Precisão (AP50)"] == 0.95
    assert class_metrics[0]["Recall"] == 0.92
    assert class_metrics[0]["Precisão"] == 0.94


@patch("microdetect.training.evaluate.YOLO")
def test_evaluate_model_with_custom_thresholds(mock_yolo, mock_yolo_results, model_path):
    """Test evaluating a model with custom confidence and IoU thresholds."""
    # Configure YOLO mock
    mock_model = MagicMock()
    mock_model.val.return_value = mock_yolo_results
    mock_yolo.return_value = mock_model

    # Create evaluator
    evaluator = ModelEvaluator()

    # Call evaluate_model with custom thresholds
    metrics = evaluator.evaluate_model(
        model_path,
        "path/to/data.yaml",
        conf_threshold=0.4,
        iou_threshold=0.6
    )

    # Check that validate was called with correct parameters
    mock_model.val.assert_called_once_with(data="path/to/data.yaml", conf=0.4, iou=0.6)


@patch("microdetect.training.evaluate.YOLO")
def test_generate_report(mock_yolo, mock_yolo_results, output_dir):
    """Test generating evaluation reports."""
    # Configure mock
    mock_model = MagicMock()
    mock_yolo.return_value = mock_model

    # Sample metrics
    metrics = {
        "metricas_gerais": {
            "Precisão (mAP50)": 0.92,
            "Precisão (mAP50-95)": 0.85,
            "Recall": 0.88,
            "Precisão": 0.90,
            "F1-Score": 0.89,
            "Taxa de Erro": 0.08,
        },
        "metricas_por_classe": [
            {"Classe": "0-levedura", "Precisão (AP50)": 0.95, "Recall": 0.92, "Precisão": 0.94, "F1-Score": 0.93},
            {"Classe": "1-fungo", "Precisão (AP50)": 0.90, "Recall": 0.87, "Precisão": 0.89, "F1-Score": 0.88},
        ],
    }

    # Create evaluator
    evaluator = ModelEvaluator(output_dir)

    # Generate reports
    report_paths = evaluator.generate_report(metrics, "path/to/model.pt")

    # Check results
    assert "csv" in report_paths
    assert "json" in report_paths
    assert "graphs" in report_paths

    # Check that files exist
    assert os.path.exists(report_paths["csv"])
    assert os.path.exists(report_paths["json"])
    assert os.path.exists(report_paths["graphs"])

    # Check JSON content
    with open(report_paths["json"], "r") as f:
        json_data = json.load(f)

    assert "modelo" in json_data
    assert "metricas_gerais" in json_data
    assert "metricas_por_classe" in json_data
    assert json_data["modelo"]["nome"] == os.path.basename("path/to/model.pt")
    assert json_data["metricas_gerais"]["Precisão (mAP50)"] == 0.92


def test_calculate_f1():
    """Test F1 score calculation."""
    evaluator = ModelEvaluator()

    # Test with normal values
    f1 = evaluator._calculate_f1(precision=0.9, recall=0.8)
    expected_f1 = 2 * (0.9 * 0.8) / (0.9 + 0.8)
    assert f1 == pytest.approx(expected_f1)

    # Test with edge cases
    assert evaluator._calculate_f1(1.0, 1.0) == pytest.approx(1.0)
    assert evaluator._calculate_f1(0.0, 0.8) == pytest.approx(0.0)
    assert evaluator._calculate_f1(0.9, 0.0) == pytest.approx(0.0)

    # Test with zero precision and recall (avoid division by zero)
    assert evaluator._calculate_f1(0.0, 0.0) == pytest.approx(0.0)

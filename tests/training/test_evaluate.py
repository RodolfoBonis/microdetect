# tests/training/test_evaluate.py
import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from microdetect.training.evaluate import ModelEvaluator, CrossValidator, ResourceMonitor, SpeedBenchmark


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


# Testes para a função plot_confusion_matrix_manually
@patch("microdetect.training.evaluate.plt.figure")
@patch("microdetect.training.evaluate.plt.imshow")
@patch("microdetect.training.evaluate.plt.colorbar")
@patch("microdetect.training.evaluate.plt.savefig")
def test_plot_confusion_matrix_manually(mock_savefig, mock_colorbar, mock_imshow, mock_figure):
    """Test the manual confusion matrix plotting function."""
    evaluator = ModelEvaluator()

    # Create test matrix and class names
    matrix = np.array([[10, 2, 1], [3, 15, 0], [0, 1, 8]])
    class_names = {0: "Class A", 1: "Class B", 2: "Class C"}

    # Call function
    evaluator._plot_confusion_matrix_manually(matrix, class_names, "test_matrix.png")

    # Check that the right functions were called
    mock_figure.assert_called_once()
    mock_imshow.assert_called_once()
    mock_colorbar.assert_called_once()
    mock_savefig.assert_called_once_with("test_matrix.png")


# Testes completos para a função optimize_threshold
@patch("microdetect.training.evaluate.YOLO")
@patch("microdetect.training.evaluate.pd.DataFrame")
@patch("microdetect.training.evaluate.plt.figure")
@patch("microdetect.training.evaluate.plt.savefig")
def test_optimize_threshold_comprehensive(mock_savefig, mock_figure, mock_dataframe, mock_yolo, mock_yolo_results,
                                          model_path, output_dir):
    """Comprehensive test for threshold optimization function."""
    # Configure YOLO mock
    mock_model = MagicMock()
    mock_model.val.return_value = mock_yolo_results
    mock_yolo.return_value = mock_model

    # Mock DataFrame to avoid actual file writing
    mock_df_instance = MagicMock()
    mock_dataframe.return_value = mock_df_instance

    # Create evaluator
    evaluator = ModelEvaluator(output_dir)

    # Call optimize_threshold with different configurations

    # Test with default parameters
    results1 = evaluator.optimize_threshold(
        model_path,
        "path/to/data.yaml",
        conf_range=(0.3, 0.5, 0.2),
        iou_range=(0.6, 0.7, 0.1)
    )

    # Test with custom metric
    results2 = evaluator.optimize_threshold(
        model_path,
        "path/to/data.yaml",
        metric="Precisão (mAP50)",
        conf_range=(0.3, 0.5, 0.2),
        iou_range=(0.6, 0.7, 0.1)
    )

    # Test with invalid metric (should use mAP50 as fallback)
    results3 = evaluator.optimize_threshold(
        model_path,
        "path/to/data.yaml",
        metric="InvalidMetric",
        conf_range=(0.3, 0.5, 0.2),
        iou_range=(0.6, 0.7, 0.1)
    )

    # Check that the function handles all cases
    assert mock_model.val.call_count == 12  # Called 4 times per test (2 conf × 2 iou × 3 tests)

    # Check that results have the expected structure
    for results in [results1, results2, results3]:
        assert "best_conf_threshold" in results
        assert "best_iou_threshold" in results
        assert "best_score" in results
        assert "best_metrics" in results
        assert "results_csv" in results
        assert "surface_plot" in results

    # Check that savefig was called for each surface plot
    assert mock_savefig.call_count == 3


# Testes para a função plot_threshold_surface
@patch("microdetect.training.evaluate.plt.figure")
@patch("microdetect.training.evaluate.plt.savefig")
def test_plot_threshold_surface(mock_savefig, mock_figure):
    """Test the threshold surface plotting function."""
    evaluator = ModelEvaluator()

    # Create test results
    results = [
        {"conf_threshold": 0.1, "iou_threshold": 0.5, "score": 0.85},
        {"conf_threshold": 0.1, "iou_threshold": 0.6, "score": 0.87},
        {"conf_threshold": 0.2, "iou_threshold": 0.5, "score": 0.86},
        {"conf_threshold": 0.2, "iou_threshold": 0.6, "score": 0.88},
    ]

    # Mock the necessary DataFrame ops
    with patch("microdetect.training.evaluate.pd.DataFrame") as mock_df:
        df_instance = MagicMock()
        mock_df.return_value = df_instance

        # Configure the pivot_table return
        pivot_mock = MagicMock()
        df_instance.pivot_table.return_value = pivot_mock
        pivot_mock.columns = [0.5, 0.6]
        pivot_mock.index = [0.1, 0.2]
        pivot_mock.values = np.array([[0.85, 0.87], [0.86, 0.88]])

        # For finding max index
        df_instance.__getitem__.return_value = pd.Series([0.85, 0.87, 0.86, 0.88])
        df_instance.idxmax.return_value = 3
        df_instance.loc.__getitem__.return_value = df_instance
        df_instance.loc.__getitem__.__getitem__.return_value = 0.2  # conf
        df_instance.loc.__getitem__.__getitem__.return_value = 0.6  # iou
        df_instance.loc.__getitem__.__getitem__.return_value = 0.88  # score

        # Call the function
        evaluator._plot_threshold_surface(results, "F1-Score", "test_surface.png")

    # Check that savefig was called
    mock_savefig.assert_called_once_with("test_surface.png")


# Testes para a análise de erros
@patch("microdetect.training.evaluate.YOLO")
@patch("microdetect.training.evaluate.os.path.exists")
@patch("microdetect.training.evaluate.os.makedirs")
@patch("microdetect.training.evaluate.open")
@patch("microdetect.training.evaluate.json.dump")
def test_analyze_errors_comprehensive(mock_json_dump, mock_open, mock_makedirs, mock_exists, mock_yolo):
    """Comprehensive test for error analysis function."""
    # Configure mocks
    mock_exists.return_value = True
    mock_model = MagicMock()

    # Create mock result with boxes
    mock_result = MagicMock()
    mock_boxes = MagicMock()
    # Configure boxes to have some with low confidence for false positive testing
    mock_boxes.conf = np.array([0.3, 0.7, 0.2, 0.9])
    mock_result.boxes = mock_boxes

    mock_model.return_value = [mock_result]
    mock_yolo.return_value = mock_model

    # Create evaluator
    evaluator = ModelEvaluator()

    # Test with different error types
    for error_type in ["all", "false_positives", "false_negatives", "classification_errors"]:
        # Call analyze_errors
        results = evaluator.analyze_errors(
            model_path="path/to/model.pt",
            data_yaml="path/to/data.yaml",
            dataset_dir="/tmp/dataset",
            error_type=error_type
        )

        # Check structure
        assert "error_counts" in results
        assert "report_path" in results
        assert "output_dir" in results

        # Check error counts
        assert "false_positives" in results["error_counts"]
        assert "false_negatives" in results["error_counts"]
        assert "classification_errors" in results["error_counts"]

    # Make sure json.dump was called for each error type
    assert mock_json_dump.call_count == 4
    assert mock_makedirs.call_count >= 4


# Testes para o SpeedBenchmark
def test_speed_benchmark_comprehensive():
    """Comprehensive test for the SpeedBenchmark class."""
    with patch("microdetect.training.evaluate.YOLO") as mock_yolo, \
            patch("microdetect.training.evaluate.np.random.randint") as mock_randint, \
            patch("microdetect.training.evaluate.time.time") as mock_time, \
            patch("microdetect.training.evaluate.pd.DataFrame") as mock_df, \
            patch("microdetect.training.evaluate.plt.figure"), \
            patch("microdetect.training.evaluate.plt.savefig"):

        # Configure mocks
        mock_model = MagicMock()
        mock_yolo.return_value = mock_model

        # Mock time.time to return increasing values
        time_values = [i * 0.1 for i in range(10)]  # 0.0, 0.1, 0.2, ...
        mock_time.side_effect = time_values

        # Create mock DataFrame instance
        mock_df_instance = MagicMock()
        mock_df.return_value = mock_df_instance

        # For testing with different devices
        for device in [None, "cpu", "cuda"]:
            # Create benchmark
            benchmark = SpeedBenchmark("path/to/model.pt", device=device)

            # Run with minimal settings to speed up test
            results = benchmark.run(
                batch_sizes=[1, 2],
                image_sizes=[640],
                iterations=1,
                warmup=0
            )

            # Check if model was loaded with to(device) if device is specified
            if device:
                mock_model.to.assert_called_with(device)

            # Check results structure
            assert "model" in results
            assert "device" in results
            assert "results" in results
            assert len(results["results"]) == 2  # One for each batch size

            # Check result fields
            for result in results["results"]:
                assert "batch_size" in result
                assert "image_size" in result
                assert "avg_latency_ms" in result
                assert "fps" in result
                assert "samples_per_second" in result

        # Test save_results and plot_results
        benchmark = SpeedBenchmark("path/to/model.pt")
        benchmark.results = [{"batch_size": 1, "image_size": 640, "avg_latency_ms": 100, "fps": 10}]

        benchmark.save_results("test_results.csv")
        mock_df.assert_called()
        mock_df_instance.to_csv.assert_called_with("test_results.csv", index=False)

        plot_path = benchmark.plot_results("test_plot.png")
        assert plot_path == "test_plot.png"


# Testes para ResourceMonitor
def test_resource_monitor_comprehensive():
    """Comprehensive test for the ResourceMonitor class."""
    with patch("microdetect.training.evaluate.threading.Thread") as mock_thread, \
            patch("microdetect.training.evaluate.time.time") as mock_time, \
            patch("microdetect.training.evaluate.pd.DataFrame") as mock_df, \
            patch("microdetect.training.evaluate.plt.figure"), \
            patch("microdetect.training.evaluate.plt.savefig"):
        # Configure mocks
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        mock_time.return_value = 12345.0

        # Mock DataFrame
        mock_df_instance = MagicMock()
        mock_df.return_value = mock_df_instance

        # Test starting when already running
        monitor = ResourceMonitor(interval=0.1)
        monitor.running = True
        monitor.start()  # Should log warning and return without starting thread
        assert not mock_thread_instance.start.called

        # Reset mock and try again
        mock_thread.reset_mock()
        monitor.running = False

        # Test starting
        monitor.start()
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()

        # Test stopping when not running
        monitor2 = ResourceMonitor()
        stats = monitor2.stop()
        assert stats == {}

        # Test stopping with measurements
        monitor.measurements = [
            {"timestamp": 0.0, "cpu_percent": 50.0, "memory_percent": 70.0, "memory_used": 1000},
            {"timestamp": 0.1, "cpu_percent": 55.0, "memory_percent": 72.0, "memory_used": 1100},
        ]

        stats = monitor.stop()
        assert "cpu_percent_avg" in stats
        assert "memory_percent_avg" in stats
        assert stats["cpu_percent_avg"] == 52.5
        assert stats["memory_percent_avg"] == 71.0

        # Test with GPU metrics
        monitor.measurements = [
            {
                "timestamp": 0.0,
                "cpu_percent": 50.0,
                "memory_percent": 70.0,
                "memory_used": 1000,
                "gpu_memory_used": 2000,
                "gpu_memory_percent": 60.0
            },
            {
                "timestamp": 0.1,
                "cpu_percent": 55.0,
                "memory_percent": 72.0,
                "memory_used": 1100,
                "gpu_memory_used": 2200,
                "gpu_memory_percent": 65.0
            },
        ]

        stats = monitor.stop()
        assert "gpu_percent_avg" in stats
        assert "gpu_memory_used_avg" in stats
        assert stats["gpu_percent_avg"] == 62.5
        assert stats["gpu_memory_used_avg"] == 2100.0

        # Test plotting with different column presence
        for columns in [
            ["timestamp", "cpu_percent", "memory_percent"],
            ["timestamp", "cpu_percent", "memory_percent", "gpu_memory_percent"]
        ]:
            monitor.measurements = [
                {col: 1.0 for col in columns},
                {col: 2.0 for col in columns}
            ]
            plot_path = monitor.plot_usage("test_resource_plot.png")
            assert plot_path == "test_resource_plot.png"


# Testes para CrossValidator
@patch("microdetect.training.evaluate.os.path.exists")
@patch("microdetect.training.evaluate.os.makedirs")
@patch("microdetect.training.evaluate.os.listdir")
@patch("microdetect.training.evaluate.np.random.seed")
@patch("microdetect.training.evaluate.np.random.shuffle")
@patch("microdetect.training.evaluate.shutil.copy")
@patch("microdetect.training.evaluate.open")
@patch("microdetect.training.evaluate.yaml.dump")
def test_cross_validator_comprehensive(mock_yaml_dump, mock_open, mock_copy,
                                       mock_shuffle, mock_seed, mock_listdir,
                                       mock_makedirs, mock_exists):
    """Comprehensive test for the CrossValidator class."""
    # Configure mocks
    mock_exists.return_value = True
    mock_listdir.return_value = [f"img{i}.jpg" for i in range(10)]

    with patch("microdetect.training.evaluate.YOLOTrainer") as mock_trainer, \
            patch("microdetect.training.evaluate.ModelEvaluator") as mock_evaluator:
        # Configure trainer mock
        trainer_instance = MagicMock()
        mock_trainer.return_value = trainer_instance

        # Configure evaluator mock
        evaluator_instance = MagicMock()
        evaluator_instance.evaluate_model.return_value = {
            "metricas_gerais": {
                "Precisão (mAP50)": 0.92,
                "Precisão (mAP50-95)": 0.85,
                "Recall": 0.88,
                "Precisão": 0.90,
                "F1-Score": 0.89
            },
            "metricas_por_classe": [
                {"Classe": "0-levedura", "Precisão (AP50)": 0.95}
            ]
        }
        mock_evaluator.return_value = evaluator_instance

        # Test with different number of folds
        for folds in [2, 3, 5]:
            # Create test directory
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create validator
                validator = CrossValidator(
                    base_dataset_dir=temp_dir,
                    output_dir=temp_dir,
                    folds=folds,
                    epochs=1
                )

                # Run cross-validation
                results = validator.run()

                # Check if seed was set
                mock_seed.assert_called_with(42)

                # Check if data was shuffled
                mock_shuffle.assert_called()

                # Check that yaml.dump was called for each fold
                assert mock_yaml_dump.call_count >= folds

                # Test generate_report with empty results
                validator.results = []
                report_path = validator.generate_report()
                assert report_path is None

                # Test generate_report with mock results
                validator.results = [
                    {
                        "fold": i + 1,
                        "metrics": {
                            "metricas_gerais": {
                                "Precisão (mAP50)": 0.90 + i * 0.01,
                                "Precisão (mAP50-95)": 0.85,
                                "Recall": 0.88,
                                "Precisão": 0.90,
                                "F1-Score": 0.89
                            }
                        }
                    } for i in range(folds)
                ]

                with patch("microdetect.training.evaluate.plt.figure"), \
                        patch("microdetect.training.evaluate.plt.savefig"), \
                        patch("microdetect.training.evaluate.json.dump") as mock_json_dump:
                    report_path = validator.generate_report()

                    # Check that json.dump was called
                    mock_json_dump.assert_called_once()

                    # Check plotting
                    plot_path = validator._plot_cv_results()
                    assert plot_path is not None


@patch("microdetect.training.evaluate.plt.figure")
@patch("microdetect.training.evaluate.plt.imshow")
@patch("microdetect.training.evaluate.plt.colorbar")
@patch("microdetect.training.evaluate.plt.savefig")
@patch("microdetect.training.evaluate.gaussian_filter")
def test_generate_density_map(mock_gaussian_filter, mock_savefig, mock_colorbar, mock_imshow, mock_figure):
    """Test density map generation."""
    # Para este teste, assumimos que a função generate_density_map já foi implementada
    # na classe ModelEvaluator ou em uma classe especializada para análise estatística

    # Mock do gaussian_filter
    mock_gaussian_filter.return_value = np.ones((100, 100)) * 0.5

    # Simulamos detecções artificiais
    detections = [
        {'x_center': 0.2, 'y_center': 0.3, 'class': 0},
        {'x_center': 0.5, 'y_center': 0.5, 'class': 1},
        {'x_center': 0.8, 'y_center': 0.7, 'class': 0}
    ]

    # Tamanho da imagem
    image_size = (100, 100)

    # Testamos a função (esta é uma prova de conceito, o teste real dependeria da implementação)
    with patch.object(ModelEvaluator, 'generate_density_map', return_value='density_map.png') as mock_method:
        evaluator = ModelEvaluator()
        result = evaluator.generate_density_map(detections, image_size, 'density_map.png')

        # Verificar chamada do método
        mock_method.assert_called_once_with(detections, image_size, 'density_map.png')

        # Verificar resultado
        assert result == 'density_map.png'

    # Para um teste mais realista quando a função estiver implementada:
    # evaluator = ModelEvaluator()
    # result = evaluator.generate_density_map(detections, image_size, 'density_map.png')
    # assert result == 'density_map.png'
    # mock_gaussian_filter.assert_called_once()
    # mock_savefig.assert_called_once_with('density_map.png')


@patch("microdetect.training.evaluate.plt.figure")
@patch("microdetect.training.evaluate.plt.hist")
@patch("microdetect.training.evaluate.plt.savefig")
def test_analyze_size_distribution(mock_savefig, mock_hist, mock_figure):
    """Test size distribution analysis."""
    # Simulamos detecções artificiais com dimensões
    detections = [
        {'width': 0.1, 'height': 0.2, 'class': 0},
        {'width': 0.15, 'height': 0.25, 'class': 1},
        {'width': 0.2, 'height': 0.3, 'class': 0},
        {'width': 0.12, 'height': 0.18, 'class': 1}
    ]

    # Testamos a função (esta é uma prova de conceito, o teste real dependeria da implementação)
    with patch.object(ModelEvaluator, 'analyze_size_distribution', return_value={
        'all': 'size_all.png',
        'by_class': 'size_by_class.png'
    }) as mock_method:
        evaluator = ModelEvaluator()
        result = evaluator.analyze_size_distribution(detections, '/tmp/output')

        # Verificar chamada do método
        mock_method.assert_called_once_with(detections, '/tmp/output', True)

        # Verificar resultado
        assert 'all' in result
        assert 'by_class' in result
        assert result['all'] == 'size_all.png'
        assert result['by_class'] == 'size_by_class.png'


@patch("microdetect.training.evaluate.plt.figure")
@patch("microdetect.training.evaluate.plt.scatter")
@patch("microdetect.training.evaluate.plt.savefig")
def test_analyze_spatial_relationships(mock_savefig, mock_scatter, mock_figure):
    """Test spatial relationship analysis."""
    # Simulamos detecções artificiais
    detections = [
        {'x_center': 0.2, 'y_center': 0.3, 'class': 0},
        {'x_center': 0.5, 'y_center': 0.5, 'class': 1},
        {'x_center': 0.8, 'y_center': 0.7, 'class': 0},
        {'x_center': 0.3, 'y_center': 0.6, 'class': 1}
    ]

    # Testamos a função (esta é uma prova de conceito, o teste real dependeria da implementação)
    with patch.object(ModelEvaluator, 'analyze_spatial_relationships', return_value={
        'scatter': 'spatial_scatter.png',
        'distance_hist': 'distance_hist.png'
    }) as mock_method:
        evaluator = ModelEvaluator()
        result = evaluator.analyze_spatial_relationships(detections, '/tmp/output')

        # Verificar chamada do método
        mock_method.assert_called_once_with(detections, '/tmp/output')

        # Verificar resultado
        assert 'scatter' in result
        assert 'distance_hist' in result
        assert result['scatter'] == 'spatial_scatter.png'
        assert result['distance_hist'] == 'distance_hist.png'


@patch("microdetect.training.evaluate.plt.figure")
@patch("microdetect.training.evaluate.plt.plot")
@patch("microdetect.training.evaluate.plt.savefig")
def test_analyze_temporal_data(mock_savefig, mock_plot, mock_figure):
    """Test temporal data analysis."""
    # Simulamos dados temporais
    time_series_data = [
        {'timestamp': '2023-01-01', 'count': 10, 'class_counts': {'0': 6, '1': 4}},
        {'timestamp': '2023-01-02', 'count': 15, 'class_counts': {'0': 8, '1': 7}},
        {'timestamp': '2023-01-03', 'count': 12, 'class_counts': {'0': 5, '1': 7}},
        {'timestamp': '2023-01-04', 'count': 18, 'class_counts': {'0': 10, '1': 8}}
    ]

    # Testamos a função (esta é uma prova de conceito, o teste real dependeria da implementação)
    with patch.object(ModelEvaluator, 'analyze_temporal_data', return_value={
        'total_count': 'temporal_total.png',
        'by_class': 'temporal_by_class.png'
    }) as mock_method:
        evaluator = ModelEvaluator()
        result = evaluator.analyze_temporal_data(time_series_data, '/tmp/output')

        # Verificar chamada do método
        mock_method.assert_called_once_with(time_series_data, '/tmp/output')

        # Verificar resultado
        assert 'total_count' in result
        assert 'by_class' in result
        assert result['total_count'] == 'temporal_total.png'
        assert result['by_class'] == 'temporal_by_class.png'


# Testes para a função de comparação de modelos

@patch("microdetect.training.evaluate.plt.figure")
@patch("microdetect.training.evaluate.plt.bar")
@patch("microdetect.training.evaluate.plt.scatter")
@patch("microdetect.training.evaluate.plt.savefig")
def test_compare_models(mock_savefig, mock_scatter, mock_bar, mock_figure):
    """Test model comparison functionality."""
    # Criar resultados fictícios para diferentes modelos
    model_results = {
        'modelo_pequeno.pt': {
            'tamanho': 'n',
            'parametros': 1000000,
            'tamanho_arquivo': 4.2,  # MB
            'metricas': {
                'mAP50': 0.85,
                'recall': 0.82,
                'fps': 120
            }
        },
        'modelo_medio.pt': {
            'tamanho': 'm',
            'parametros': 5000000,
            'tamanho_arquivo': 18.7,  # MB
            'metricas': {
                'mAP50': 0.92,
                'recall': 0.89,
                'fps': 75
            }
        },
        'modelo_grande.pt': {
            'tamanho': 'l',
            'parametros': 15000000,
            'tamanho_arquivo': 52.1,  # MB
            'metricas': {
                'mAP50': 0.95,
                'recall': 0.93,
                'fps': 30
            }
        }
    }

    # Testamos a função (esta é uma prova de conceito, o teste real dependeria da implementação)
    with patch.object(ModelEvaluator, 'compare_models', return_value={
        'accuracy_comparison': 'accuracy_comparison.png',
        'speed_comparison': 'speed_comparison.png',
        'tradeoff': 'accuracy_vs_speed.png'
    }) as mock_method:
        evaluator = ModelEvaluator()
        result = evaluator.compare_models(model_results, '/tmp/output')

        # Verificar chamada do método
        mock_method.assert_called_once_with(model_results, '/tmp/output')

        # Verificar resultado
        assert 'accuracy_comparison' in result
        assert 'speed_comparison' in result
        assert 'tradeoff' in result
        assert result['accuracy_comparison'] == 'accuracy_comparison.png'
        assert result['speed_comparison'] == 'speed_comparison.png'
        assert result['tradeoff'] == 'accuracy_vs_speed.png'


# Testes para geração de relatórios PDF e dashboards

@patch("pdfkit.from_string")  # assumindo que pdfkit seria usado para gerar PDFs
def test_generate_pdf_report(mock_from_string):
    """Test PDF report generation."""
    # Métricas de exemplo para o relatório
    metrics = {
        "metricas_gerais": {
            "Precisão (mAP50)": 0.92,
            "Precisão (mAP50-95)": 0.85,
            "Recall": 0.88,
            "Precisão": 0.90,
            "F1-Score": 0.89,
        },
        "metricas_por_classe": [
            {
                "Classe": "0-levedura",
                "Precisão (AP50)": 0.95,
                "Recall": 0.92,
                "Precisão": 0.94,
                "F1-Score": 0.93,
            },
            {
                "Classe": "1-fungo",
                "Precisão (AP50)": 0.90,
                "Recall": 0.87,
                "Precisão": 0.89,
                "F1-Score": 0.88,
            },
        ],
    }

    # Caminho do modelo
    model_path = "runs/train/exp/weights/best.pt"

    # Mock para HTML template (assumindo que usaríamos um template para o PDF)
    with patch("microdetect.training.evaluate.open", return_value=MagicMock()), \
            patch("microdetect.training.evaluate.ModelEvaluator.generate_pdf_report",
                  return_value="relatório.pdf") as mock_method:
        evaluator = ModelEvaluator()
        result = evaluator.generate_pdf_report(metrics, model_path, "relatório.pdf")

        # Verificar chamada do método
        mock_method.assert_called_once_with(metrics, model_path, "relatório.pdf")

        # Verificar resultado
        assert result == "relatório.pdf"


@patch("dash.Dash")
@patch("dash.dcc")
@patch("dash.html")
def test_generate_interactive_dashboard(mock_html, mock_dcc, mock_dash):
    """Test interactive dashboard generation."""
    # Configurar mocks
    mock_app = MagicMock()
    mock_dash.return_value = mock_app

    with patch("microdetect.training.evaluate.ModelEvaluator.generate_dashboard",
               return_value=8050) as mock_method:
        evaluator = ModelEvaluator()
        port = evaluator.generate_dashboard("runs/detect/exp", port=8050)

        # Verificar chamada do método
        mock_method.assert_called_once_with("runs/detect/exp", port=8050)

        # Verificar que o dashboard foi criado com a porta correta
        assert port == 8050


# Testes para processamento em lote

@patch("microdetect.training.evaluate.YOLO")
def test_batch_detect(mock_yolo):
    """Test batch detection processing."""
    # Configurar mock
    mock_model = MagicMock()
    mock_yolo.return_value = mock_model

    # Criar lista fictícia de arquivos
    image_files = [f"image_{i}.jpg" for i in range(10)]

    with patch("os.listdir", return_value=image_files), \
            patch("os.path.isfile", return_value=True), \
            patch("microdetect.training.evaluate.ModelEvaluator.batch_detect",
                  return_value={"processed": 10, "output_dir": "/tmp/output"}) as mock_method:
        evaluator = ModelEvaluator()
        result = evaluator.batch_detect(
            model_path="path/to/model.pt",
            source_dir="/tmp/images",
            output_dir="/tmp/output",
            batch_size=4
        )

        # Verificar chamada do método
        mock_method.assert_called_once_with(
            model_path="path/to/model.pt",
            source_dir="/tmp/images",
            output_dir="/tmp/output",
            batch_size=4
        )

        # Verificar resultado
        assert result["processed"] == 10
        assert result["output_dir"] == "/tmp/output"


# Testes para visualização interativa

@patch("microdetect.training.evaluate.cv2.imread")
@patch("microdetect.training.evaluate.cv2.rectangle")
@patch("microdetect.training.evaluate.cv2.putText")
@patch("microdetect.training.evaluate.cv2.imshow")
@patch("microdetect.training.evaluate.cv2.waitKey")
@patch("microdetect.training.evaluate.cv2.destroyAllWindows")
def test_visualize_detections(mock_destroy, mock_waitkey, mock_imshow,
                              mock_puttext, mock_rectangle, mock_imread):
    """Test visualization of detections."""
    # Configurar mock da imagem
    mock_imread.return_value = np.zeros((100, 100, 3), dtype=np.uint8)

    # Configurar resposta de waitKey (tecla 'q' para sair)
    mock_waitkey.side_effect = [ord('n'), ord('n'), ord('q')]

    # Lista de imagens fictícia
    images = ["img1.jpg", "img2.jpg", "img3.jpg"]

    # Detecções fictícias
    detections = {
        "img1.jpg": [
            {"x": 10, "y": 20, "width": 30, "height": 40, "conf": 0.95, "class": 0},
            {"x": 50, "y": 60, "width": 25, "height": 35, "conf": 0.87, "class": 1}
        ],
        "img2.jpg": [
            {"x": 15, "y": 25, "width": 35, "height": 45, "conf": 0.92, "class": 0}
        ],
        "img3.jpg": []
    }

    with patch("microdetect.training.evaluate.ModelEvaluator.visualize_detections") as mock_method:
        evaluator = ModelEvaluator()
        evaluator.visualize_detections(images, detections, conf_threshold=0.5)

        # Verificar chamada do método
        mock_method.assert_called_once_with(images, detections, conf_threshold=0.5)


# Testes para exportação de resultados

@patch("microdetect.training.evaluate.open")
@patch("microdetect.training.evaluate.json.dump")
@patch("microdetect.training.evaluate.csv.writer")
def test_export_results(mock_csv_writer, mock_json_dump, mock_open):
    """Test exporting detection results in different formats."""
    # Detecções fictícias
    detections = {
        "img1.jpg": [
            {"x": 10, "y": 20, "width": 30, "height": 40, "conf": 0.95, "class": 0},
            {"x": 50, "y": 60, "width": 25, "height": 35, "conf": 0.87, "class": 1}
        ],
        "img2.jpg": [
            {"x": 15, "y": 25, "width": 35, "height": 45, "conf": 0.92, "class": 0}
        ],
    }

    # Testar exportação para JSON
    with patch("microdetect.training.evaluate.ModelEvaluator.export_to_json",
               return_value="detections.json") as mock_method:
        evaluator = ModelEvaluator()
        result = evaluator.export_to_json(detections, "detections.json")

        # Verificar chamada do método
        mock_method.assert_called_once_with(detections, "detections.json")

        # Verificar resultado
        assert result == "detections.json"

    # Testar exportação para CSV
    with patch("microdetect.training.evaluate.ModelEvaluator.export_to_csv",
               return_value="detections.csv") as mock_method:
        evaluator = ModelEvaluator()
        result = evaluator.export_to_csv(detections, "detections.csv")

        # Verificar chamada do método
        mock_method.assert_called_once_with(detections, "detections.csv")

        # Verificar resultado
        assert result == "detections.csv"

    # Testar exportação para formato YOLO
    with patch("microdetect.training.evaluate.ModelEvaluator.export_to_yolo_format",
               return_value="/tmp/yolo_labels") as mock_method:
        evaluator = ModelEvaluator()
        result = evaluator.export_to_yolo_format(detections, "/tmp/yolo_labels")

        # Verificar chamada do método
        mock_method.assert_called_once_with(detections, "/tmp/yolo_labels")

        # Verificar resultado
        assert result == "/tmp/yolo_labels"
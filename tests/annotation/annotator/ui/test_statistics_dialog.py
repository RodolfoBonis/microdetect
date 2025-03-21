import unittest.mock as mock

import pytest

from microdetect.annotation.annotator.ui.statistics_dialog import StatisticsDialog


class TestStatisticsDialog:

    @pytest.fixture
    def statistics_dialog(self):
        """Create StatisticsDialog with test parameters"""
        output_dir = '/path/to/output'
        classes = ['0-class1', '1-class2', '2-class3']
        return StatisticsDialog(output_dir, classes)

    def test_get_class_name(self, statistics_dialog):
        """Test getting class name from class ID"""
        # Test with existing class
        assert statistics_dialog._get_class_name('0') == '0-class1'
        assert statistics_dialog._get_class_name('1') == '1-class2'

        # Test with non-existent class
        assert statistics_dialog._get_class_name('99') == 'Classe 99'

    @mock.patch('glob.glob')
    @mock.patch('builtins.open', new_callable=mock.mock_open)
    def test_count_annotations_by_class(self, mock_open, mock_glob, statistics_dialog):
        """Test counting annotations by class"""
        # Setup mocks
        mock_glob.return_value = [
            '/path/to/output/img1.txt',
            '/path/to/output/img2.txt'
        ]

        # Mock reading annotation files
        mock_open.return_value.read.return_value = ""
        mock_open.return_value.__iter__.return_value = [
            '0 0.5 0.5 0.1 0.1\n',
            '0 0.6 0.6 0.1 0.1\n',
            '1 0.7 0.7 0.1 0.1\n'
        ]

        # Call method
        class_counts, total_boxes = statistics_dialog._count_annotations_by_class()

        # Verify results
        assert class_counts['0'] == 2
        assert class_counts['1'] == 1
        assert class_counts['2'] == 0
        assert total_boxes == 3

    @mock.patch('microdetect.annotation.annotator.ui.base.create_secure_dialog')
    @mock.patch('microdetect.annotation.annotator.ui.statistics_dialog.StatisticsDialog._count_annotations_by_class')
    @mock.patch('glob.glob')
    def test_show(self, mock_glob, mock_count, mock_create_dialog, statistics_dialog):
        """Test showing statistics dialog"""
        # Setup mocks
        mock_dialog = mock.MagicMock()
        mock_create_dialog.return_value = mock_dialog

        mock_count.return_value = ({'0': 5, '1': 3, '2': 0}, 8)
        mock_glob.return_value = ['/path/to/output/img1.txt', '/path/to/output/img2.txt']

        # Set matplotlib availability flag
        statistics_dialog.mpl_available = False

        # Call show method
        statistics_dialog.show()

        # Verify dialog creation
        mock_dialog.title.assert_called_once_with("Dashboard de Estatísticas de Anotação")
        mock_dialog.wait_window.assert_called_once()
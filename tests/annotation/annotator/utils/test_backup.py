import unittest.mock as mock

import pytest

from microdetect.annotation.annotator.utils.backup import AnnotationBackup


class TestAnnotationBackup:

    @pytest.fixture
    def backup_manager(self):
        """Create an AnnotationBackup with test parameters"""
        return AnnotationBackup(progress_file=".test_progress.json", max_backups=3)

    def test_initialization(self, backup_manager):
        """Test backup manager initialization"""
        assert backup_manager.progress_file == ".test_progress.json"
        assert backup_manager.max_backups == 3

    @mock.patch("os.makedirs")
    @mock.patch("glob.glob")
    @mock.patch("os.path.exists")
    @mock.patch("shutil.copy2")
    def test_create_backup(self, mock_copy, mock_exists, mock_glob, mock_makedirs, backup_manager):
        """Test creating backup of annotation files"""
        # Setup mocks
        mock_exists.return_value = True
        mock_glob.return_value = ["/labels/file1.txt", "/labels/.test_progress.json", "/labels/file2.txt"]  # Should be skipped

        # Call create_backup
        result = backup_manager.create_backup("/labels")

        # Verify backups were created
        mock_makedirs.assert_called()
        assert mock_copy.call_count == 2  # 2 files excluding progress file
        assert result is not None

    @mock.patch("os.makedirs")
    @mock.patch("glob.glob")
    @mock.patch("os.path.exists")
    @mock.patch("shutil.copy2")
    def test_create_backup_empty(self, mock_copy, mock_exists, mock_glob, mock_makedirs, backup_manager):
        """Test creating backup with no annotation files"""
        # Setup mocks
        mock_exists.return_value = True
        mock_glob.return_value = ["/labels/.test_progress.json"]  # Only progress file

        # Call create_backup
        result = backup_manager.create_backup("/labels")

        # Verify no backups were created
        mock_copy.assert_not_called()
        assert result is None

    @mock.patch("os.listdir")
    @mock.patch("os.path.isdir")
    @mock.patch("shutil.rmtree")
    def test_cleanup_old_backups(self, mock_rmtree, mock_isdir, mock_listdir, backup_manager):
        """Test cleaning up old backup directories"""
        # Setup mocks
        mock_listdir.return_value = [
            "backup_annotations_20230101_120000",
            "backup_annotations_20230102_120000",
            "backup_annotations_20230103_120000",
            "backup_annotations_20230104_120000",
            "other_directory",
        ]

        # Make all look like directories except 'other_directory'
        def is_dir_check(path):
            return "other_directory" not in path

        mock_isdir.side_effect = is_dir_check

        # Call cleanup
        backup_manager._cleanup_old_backups("/backups")

        # Verify oldest backup was removed (only one, since max_backups=3)
        assert mock_rmtree.call_count == 1
        args, _ = mock_rmtree.call_args
        assert "20230101" in args[0]  # Should remove oldest

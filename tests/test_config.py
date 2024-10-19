import pytest

from src.file_handler import FileHandler

@pytest.fixture(scope='module')
def file_handler():
    class NullLogger:
        """
        Null logger, used for testing
        """

        def __getattr__(self, item):
            return lambda *args, **kwargs: None

    yield FileHandler(NullLogger())

    print("Tear down")


def test_config_load(file_handler):
    config_file_path = 'config.json'

    # Load the config file
    file_handler.config_load(config_file_path)

    # Test passes if no exceptions are raised
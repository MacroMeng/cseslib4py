import pytest
import cses


@pytest.fixture()
def sample_schedule():
    return cses.CSES.from_file("./cses_example.yaml")


def test_cses_version(sample_schedule):
    assert sample_schedule.version == 1

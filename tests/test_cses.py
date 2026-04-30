import pytest
import cses


@pytest.fixture()
def sample_schedule():
    return cses.CSES.load_from("./cses_example_v2.yaml")


def test_cses_version(sample_schedule):
    assert sample_schedule.version == 1

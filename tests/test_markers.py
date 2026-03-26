import pytest

@pytest.mark.gazu_only
def test_gazu():
    assert True

@pytest.mark.shotgun_only
def test_shotgun():
    assert True

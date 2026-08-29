import pytest


def test_load_connectors_includes_available_connector(mocker):
    from rez_production_context.connectors import _load_connectors

    mock_cls = mocker.MagicMock()
    mock_cls.available.return_value = True
    mock_module = mocker.MagicMock()
    mock_module.FakeConnector = mock_cls

    mocker.patch(
        "rez_production_context.connectors._CONNECTOR_REGISTRY",
        [(".fake", "FakeConnector")],
    )
    mocker.patch("importlib.import_module", return_value=mock_module)

    result = _load_connectors()
    assert mock_cls in result


def test_load_connectors_excludes_unavailable_connector(mocker):
    from rez_production_context.connectors import _load_connectors

    mock_cls = mocker.MagicMock()
    mock_cls.available.return_value = False
    mock_module = mocker.MagicMock()
    mock_module.FakeConnector = mock_cls

    mocker.patch(
        "rez_production_context.connectors._CONNECTOR_REGISTRY",
        [(".fake", "FakeConnector")],
    )
    mocker.patch("importlib.import_module", return_value=mock_module)

    result = _load_connectors()
    assert result == []


def test_load_connectors_skips_broken_module(mocker):
    from rez_production_context.connectors import _load_connectors

    mocker.patch(
        "rez_production_context.connectors._CONNECTOR_REGISTRY",
        [(".broken", "Broken")],
    )
    mocker.patch("importlib.import_module", side_effect=ImportError("broken module"))

    result = _load_connectors()
    assert result == []
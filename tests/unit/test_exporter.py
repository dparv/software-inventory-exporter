"""Exporter unit tests."""
import subprocess

import pytest
from fastapi.testclient import TestClient

from software_inventory_exporter import exporter

client = TestClient(exporter.app)


def test_main(mocker):
    """Test the main function."""
    testargs = ["bin/software-inventory-exporter", "-c", "/tmp/config.yaml"]
    mocker.patch.object(exporter.sys, "argv", testargs)
    uvicorn_mock = mocker.patch.object(exporter.uvicorn, "run")
    mocked_config_file = mocker.mock_open(
        read_data="settings:\n  bind_address: 0.0.0.0\n  port: 8675"
    )
    mocker.patch("builtins.open", mocked_config_file)
    exporter.main()
    uvicorn_mock.assert_called_once()


def test_main_exit(mocker):
    """Test the main function when exit."""
    testargs = ["bin/software-inventory-exporter", "/tmp/config.yaml"]
    mocker.patch.object(exporter.sys, "argv", testargs)
    uvicorn_mock = mocker.patch.object(exporter.uvicorn, "run")
    with pytest.raises(SystemExit) as mock_exception:
        exporter.main()
    assert mock_exception.value.code == 1
    uvicorn_mock.assert_not_called()


def test_hostname(mocker):
    """Test the hostname endpoint."""
    hostname = "juju-70b49f-3"
    mocker.patch.object(exporter.socket, "gethostname", return_value=hostname)
    response = client.get("/hostname")
    assert response.status_code == 200
    assert response.text == hostname


def test_hostname_error(mocker):
    """Test possible errors in the hostname endpoint."""
    mocker.patch.object(exporter.socket, "gethostname", side_effect=ValueError("some error"))
    response = client.get("/hostname")
    assert response.status_code == 500


def test_kernel(mocker):
    """Test the kernel endpoint."""
    mocker.patch.object(exporter.platform, "release", return_value="5.19.0-32-test")
    response = client.get("/kernel")
    assert response.status_code == 200
    assert response.json() == {"kernel": "5.19.0-32-test"}


def test_dpkg(mocker, list_dpkg):
    """Test the dpkg endpoint."""
    mocker.patch.object(exporter.subprocess, "check_output", return_value=list_dpkg)
    response = client.get("/dpkg")
    assert response.status_code == 200
    assert response.json() == [
        {"package": "accountsservice", "version": "22.07.5-2ubuntu1.3"},
        {"package": "acl", "version": "2.3.1-1"},
    ]


@pytest.mark.parametrize(
    "raise_error",
    [
        subprocess.TimeoutExpired(cmd=None, timeout=1),
        subprocess.CalledProcessError(cmd=None, returncode=1),
        ValueError,
    ],
)
def test_dpkg_error(mocker, raise_error):
    """Test possible errors in the dpkg endpoint."""
    mocker.patch.object(exporter.subprocess, "check_output", side_effect=raise_error)
    response = client.get("/dpkg")
    assert response.status_code == 500


def test_snap(mocker, list_snap):
    """Test the snap endpoint."""
    mocker.patch.object(exporter.subprocess, "check_output", return_value=list_snap)
    response = client.get("/snap")
    assert response.status_code == 200
    assert response.json() == [
        {"snap": "bare", "version": "1.0", "revision": "5", "tracking": "latest/stable"},
        {
            "snap": "charmcraft",
            "version": "2.2.0",
            "revision": "1171",
            "tracking": "latest/stable",
        },
    ]


@pytest.mark.parametrize(
    "raise_error",
    [
        subprocess.TimeoutExpired(cmd=None, timeout=1),
        subprocess.CalledProcessError(cmd=None, returncode=1),
        ValueError,
    ],
)
def test_snap_error(mocker, raise_error):
    """Test possible errors in the snap endpoint."""
    mocker.patch.object(exporter.subprocess, "check_output", side_effect=raise_error)
    response = client.get("/snap")
    assert response.status_code == 500

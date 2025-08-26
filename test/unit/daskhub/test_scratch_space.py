import os
import tempfile
import pytest

# Optional: Skip distributed tests unless Dask is available
dask = pytest.importorskip("dask")
distributed = pytest.importorskip("dask.distributed")


@pytest.mark.parametrize("mount_path", ["/scratch_space"])
def test_scratch_space_local_exists(mount_path):
    """Check that /scratch_space exists and is a directory."""
    assert os.path.exists(mount_path), f"{mount_path} does not exist"
    assert os.path.isdir(mount_path), f"{mount_path} is not a directory"


@pytest.mark.parametrize("mount_path", ["/scratch_space"])
def test_scratch_space_local_writable(mount_path):
    """Check that /scratch_space is writable."""
    try:
        with tempfile.NamedTemporaryFile(dir=mount_path, delete=True) as tf:
            tf.write(b"test")
    except Exception as e:
        pytest.fail(f"Write test failed in {mount_path}: {e}")


@pytest.mark.parametrize("mount_path", ["/scratch_space"])
def test_scratch_space_on_dask_workers(mount_path):
    """Check /scratch_space exists and is writable on all Dask workers."""
    from dask.distributed import Client

    client = Client()  # Assumes local or remote Dask client already configured

    def _check_mount(path):
        import os
        import tempfile

        if not os.path.exists(path):
            return f"missing: {path}"
        if not os.path.isdir(path):
            return f"not-a-dir: {path}"
        try:
            with tempfile.NamedTemporaryFile(dir=path, delete=True) as tf:
                tf.write(b"test")
            return "OK"
        except Exception as e:
            return f"write-failed: {e}"

    results = client.run(_check_mount, path=mount_path)
    for worker, result in results.items():
        assert result == "OK", f"Worker {worker} failed: {result}"

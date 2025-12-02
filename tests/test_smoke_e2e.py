from __future__ import annotations

import pytest


@pytest.mark.skip(reason="Full from-install smoke test is intended for CI/release pipeline, not unit test runs.")
def test_smoke_e2e_script_importable() -> None:
    # Ensures the smoke script is syntactically valid and can be imported.
    import scripts.smoke_e2e as smoke  # type: ignore  # noqa: F401

    assert hasattr(smoke, "run_smoke")


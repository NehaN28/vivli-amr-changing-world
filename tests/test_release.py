from pathlib import Path
import tomllib

import yaml
from streamlit.testing.v1 import AppTest

from amr_changing_world import __version__


ROOT = Path(__file__).resolve().parents[1]


def test_release_versions_are_synchronised():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    citation = yaml.safe_load((ROOT / "CITATION.cff").read_text())
    project = yaml.safe_load((ROOT / "config/project.yml").read_text())
    assert {
        pyproject["project"]["version"],
        citation["version"],
        project["project"]["pipeline_version"],
        __version__,
    } == {"0.8.0"}


def test_package_metadata_declares_dashboard_dependencies():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    dependencies = pyproject["project"]["dependencies"]
    assert any(item.startswith("streamlit") for item in dependencies)
    assert any(item.startswith("plotly") for item in dependencies)


def test_streamlit_requirements_install_local_package():
    requirements = [
        line.strip()
        for line in (ROOT / "requirements.txt").read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert "-e ." in requirements


def test_streamlit_entry_point_smoke_test():
    app = AppTest.from_file(ROOT / "app.py", default_timeout=30).run()
    assert not app.exception
    assert [title.value for title in app.title] == ["Human AMR trends in a changing world"]


def test_deployment_requires_data_use_confirmation():
    guide = (ROOT / "DEPLOYMENT.md").read_text()
    assert "data-use agreement" in guide
    assert "Do not make the repository or dashboard public" in guide

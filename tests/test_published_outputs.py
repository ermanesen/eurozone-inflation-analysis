import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_figures_are_nonempty():
    for name in (
        "inflation_trend.svg",
        "phillips_partial_scatter.svg",
        "model_coefficients.svg",
    ):
        assert (ROOT / "figures" / name).stat().st_size > 1_000


def test_notebook_is_executed_and_explained():
    notebook = json.loads(
        (ROOT / "notebooks" / "eurozone_phillips_curve.ipynb").read_text(
            encoding="utf-8"
        )
    )
    code_cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
    markdown_cells = [
        cell for cell in notebook["cells"] if cell["cell_type"] == "markdown"
    ]
    assert len(markdown_cells) >= 5
    assert all(cell["execution_count"] is not None for cell in code_cells)
    assert not any(
        output.get("output_type") == "error"
        for cell in code_cells
        for output in cell.get("outputs", [])
    )

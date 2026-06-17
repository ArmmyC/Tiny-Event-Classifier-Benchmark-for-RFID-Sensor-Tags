from __future__ import annotations

from pathlib import Path

from tinysnnrfid.clean_outputs import clean_outputs


def test_clean_outputs_removes_representative_generated_files(tmp_path) -> None:
    files = [
        tmp_path / "data" / "generated" / "sample.npy",
        tmp_path / "results" / "benchmark_results.json",
        tmp_path / "results" / "accuracy" / "metrics.json",
        tmp_path / "sim.out",
    ]
    for path in files:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("generated\n", encoding="utf-8")

    summary = clean_outputs(tmp_path)

    assert summary.removed_files == len(files)
    assert all(not path.exists() for path in files)


def test_clean_outputs_removes_representative_generated_directories(tmp_path) -> None:
    dirs = [
        tmp_path / "results" / "rtl",
        tmp_path / "results" / "sweeps" / "runs",
        tmp_path / "results" / "smoke",
    ]
    for path in dirs:
        path.mkdir(parents=True)
        (path / "artifact.txt").write_text("generated\n", encoding="utf-8")

    summary = clean_outputs(tmp_path)

    assert summary.removed_directories == len(dirs)
    assert all(not path.exists() for path in dirs)


def test_clean_outputs_ignores_missing_paths(tmp_path) -> None:
    summary = clean_outputs(tmp_path)

    assert summary.removed_files == 0
    assert summary.removed_directories == 0
    assert summary.missing_patterns > 0


def test_clean_outputs_does_not_remove_representative_source_files(tmp_path) -> None:
    source_files = [
        tmp_path / "python" / "tinysnnrfid" / "module.py",
        tmp_path / "rtl" / "snn" / "detector.sv",
        tmp_path / "tests" / "test_example.py",
        tmp_path / "docs" / "specs" / "spec.md",
        tmp_path / "configs" / "default.json",
    ]
    for path in source_files:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("source\n", encoding="utf-8")

    clean_outputs(tmp_path)

    assert all(path.read_text(encoding="utf-8") == "source\n" for path in source_files)


def _clean_recipe(makefile_text: str) -> str:
    lines = makefile_text.splitlines()
    start = lines.index("clean:")
    recipe: list[str] = []
    for line in lines[start + 1 :]:
        if line and not line.startswith("\t") and not line.startswith(" "):
            break
        recipe.append(line)
    return "\n".join(recipe)


def test_makefile_clean_target_uses_python_wrapper_without_rm() -> None:
    text = Path("Makefile").read_text(encoding="utf-8")
    recipe = _clean_recipe(text)

    assert "rm -f" not in recipe
    assert "python python/clean_outputs.py" in recipe

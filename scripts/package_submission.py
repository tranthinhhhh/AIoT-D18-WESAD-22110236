from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUBMISSION = ROOT / "submission"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def zip_members() -> list[Path]:
    members: list[Path] = []
    for name in ["README.md", "requirements.txt", "TranTienThinh_final.ipynb"]:
        members.append(ROOT / name)
    for folder, pattern in [("configs", "*.yaml"), ("src", "*.py"), ("scripts", "*.py"), ("docs", "*.md")]:
        members.extend(sorted((ROOT / folder).glob(pattern)))
    for name in ["manifest.json", "preprocessing_summary.json"]:
        members.append(ROOT / "data" / "processed" / "wesad_d18_v2" / name)
    fixed_outputs = [
        "outputs/analysis_summary.json", "outputs/benchmark_cpu.json",
        "outputs/baselines/baseline_metrics.json",
        "outputs/audit/smoke_test.json", "outputs/audit/failure_case_selection.json",
        "outputs/audit/qc_audit_summary.json", "outputs/audit/qc_review_selection.csv",
        "outputs/tables/overall_results_v2.csv", "outputs/tables/paired_subject_deltas.csv",
        "outputs/runs/A0_summary.json", "outputs/runs/A1_summary.json", "outputs/runs/A3_summary.json",
    ]
    members.extend(ROOT / item for item in fixed_outputs)
    members.extend(sorted((ROOT / "outputs" / "figures").glob("*.png")))
    for variant in ["A0", "A1", "A3"]:
        for seed in [42, 123, 999]:
            run = ROOT / "outputs" / "runs" / f"{variant}_seed{seed}"
            for name in ["best.pt", "metrics.json", "training_log.csv"]:
                members.append(run / name)
    # Prediction CSVs used by the default notebook/figures, without last checkpoints.
    members.extend([
        ROOT / "outputs" / "runs" / "A0_seed42" / "test_predictions.csv",
        ROOT / "outputs" / "runs" / "A0_seed42" / "validation_predictions.csv",
        ROOT / "outputs" / "baselines" / "E1_test_predictions.csv",
        ROOT / "outputs" / "baselines" / "E1_validation_predictions.csv",
    ])
    missing = [path for path in members if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing package members:\n" + "\n".join(map(str, missing)))
    return sorted(set(members), key=lambda p: p.relative_to(ROOT).as_posix())


def main() -> None:
    SUBMISSION.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "TranTienThinh_final.docx", SUBMISSION / "TranTienThinh_final.docx")
    shutil.copy2(ROOT / "TranTienThinh_final.ipynb", SUBMISSION / "TranTienThinh_final.ipynb")
    shutil.copy2(ROOT / ".qa" / "report_render2" / "TranTienThinh_final.pdf", SUBMISSION / "TranTienThinh_final.pdf")
    shutil.copy2(ROOT / "docs" / "SUBMISSION_CHECKLIST.md", SUBMISSION / "SUBMISSION_CHECKLIST.md")

    archive = SUBMISSION / "TranTienThinh_code.zip"
    members = zip_members()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in members:
            zf.write(path, path.relative_to(ROOT).as_posix())

    files = []
    for path in sorted(SUBMISSION.iterdir(), key=lambda p: p.name.lower()):
        if path.is_file() and path.name != "FILE_MANIFEST.json":
            files.append({"name": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)})
    manifest = {
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "student": "Trần Tiến Thịnh",
        "student_id": "22110236",
        "project": "Đ18",
        "github_status": "pending_real_repository_url",
        "lms_submission": "not_performed",
        "files": files,
        "zip_member_count": len(members),
        "exclusions": ["raw WESAD", "virtual environments", "cache", "last.pt", "processed windows/metadata/audit"],
    }
    (SUBMISSION / "FILE_MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

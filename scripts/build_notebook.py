from __future__ import annotations

from pathlib import Path

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    nb = nbf.v4.new_notebook()
    nb["metadata"] = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.12"},
        "title": "Đ18 — Ước lượng nhịp tim từ BVP cổ tay",
    }
    cells = []
    cells.append(nbf.v4.new_markdown_cell(
        "# Đ18 — Ước lượng nhịp tim từ BVP cổ tay\n\n"
        "**Sinh viên:** Trần Tiến Thịnh — **MSSV:** 22110236  \n"
        "Notebook cuối kỳ này **đánh giá lại checkpoint đã huấn luyện**, kiểm tra hash và tái tính metric trên tập test. "
        "ECG chỉ dùng để tạo HR tham chiếu; đầu vào mô hình là BVP."
    ))
    cells.append(nbf.v4.new_markdown_cell(
        "## Giao thức đã khóa\n\n"
        "- WESAD; train S2–S10, validation S11/S13, test S14–S17 (không trùng người).\n"
        "- Cửa sổ 8 s, bước 2 s; BVP 64→32 Hz, Butterworth bậc 4, 0,5–8 Hz.\n"
        "- ECG 5–25 Hz và detector đỉnh R thích nghi (không gọi là Pan–Tompkins).\n"
        "- Metric chính: trung bình MAE theo người (MAE_macro). Test không được dùng để chọn checkpoint."
    ))
    cells.append(nbf.v4.new_code_cell(
        "from pathlib import Path\n"
        "import json\n"
        "import numpy as np\n"
        "import pandas as pd\n"
        "import torch\n"
        "import matplotlib.pyplot as plt\n"
        "from IPython.display import display, Image\n\n"
        "ROOT = Path.cwd()\n"
        "if not (ROOT / 'configs' / 'final.yaml').exists():\n"
        "    raise RuntimeError('Hãy chạy notebook từ thư mục gốc của dự án.')\n"
        "from src.common import load_config, load_processed\n"
        "from src.model import make_model\n"
        "from src.train import predict, make_prediction_frame\n"
        "from src.metrics import summarize_predictions\n"
        "cfg = load_config(ROOT / 'configs' / 'final.yaml')\n"
        "metadata, arrays, manifest = load_processed(cfg)\n"
        "print('Config hash  :', cfg['_config_hash'])\n"
        "print('Manifest hash:', manifest['manifest_hash'])\n"
        "print('Shape BVP     :', arrays['bvp_normalized'].shape)"
    ))
    cells.append(nbf.v4.new_code_cell(
        "summary = json.loads((ROOT/'data/processed/wesad_d18_v2/preprocessing_summary.json').read_text(encoding='utf-8'))\n"
        "assert summary['manifest_hash'] == manifest['manifest_hash']\n"
        "assert summary['checks']['finite'] and summary['checks']['alignment']\n"
        "overview = pd.DataFrame({\n"
        "    'Số cửa sổ': [summary['windows_before_qc'], summary['windows_kept'], summary['windows_rejected']],\n"
        "}, index=['Trước QC', 'Giữ lại', 'Loại'])\n"
        "display(overview)\n"
        "display(metadata.groupby(['split','condition']).size().unstack(fill_value=0))"
    ))
    cells.append(nbf.v4.new_markdown_cell(
        "## Kết quả E0/E1/E2 và ablation\n\n"
        "Sai số dưới đây đều lấy từ cùng manifest v2. Độ lệch chuẩn của CNN là độ lệch chuẩn mẫu qua ba seed 42/123/999."
    ))
    cells.append(nbf.v4.new_code_cell(
        "result_table = pd.read_csv(ROOT/'outputs/tables/overall_results_v2.csv')\n"
        "display(result_table.round(3))\n"
        "best = result_table.loc[result_table['mae_macro_mean_bpm'].idxmin()]\n"
        "print(f\"Cấu hình có MAE_macro thấp nhất trong các run đã chạy: {best['method']} = {best['mae_macro_mean_bpm']:.3f} BPM\")"
    ))
    cells.append(nbf.v4.new_code_cell(
        "display(Image(filename=str(ROOT/'outputs/figures/overall_mae_macro.png'), width=800))"
    ))
    cells.append(nbf.v4.new_markdown_cell(
        "## Tái tính độc lập A0, seed 42\n\n"
        "Cell này nạp `best.pt`, chạy suy luận lại toàn bộ 4.444 cửa sổ test và so khớp với metric đã lưu. "
        "Đây là đường đánh giá; không khởi động huấn luyện."
    ))
    cells.append(nbf.v4.new_code_cell(
        "run_dir = ROOT/'outputs/runs/A0_seed42'\n"
        "saved = json.loads((run_dir/'metrics.json').read_text(encoding='utf-8'))\n"
        "checkpoint = torch.load(run_dir/'best.pt', map_location='cpu', weights_only=False)\n"
        "assert checkpoint['manifest_hash'] == manifest['manifest_hash']\n"
        "assert checkpoint['config_hash'] == cfg['_config_hash']\n"
        "model = make_model(cfg, 'A0')\n"
        "model.load_state_dict(checkpoint['model_state'])\n"
        "test_mask = metadata['split'].eq('test').to_numpy()\n"
        "pred = predict(model, arrays['bvp_normalized'][test_mask], cfg['training']['batch_size'], torch.device('cpu'))\n"
        "frame = make_prediction_frame(metadata, test_mask, pred)\n"
        "recomputed = summarize_predictions(frame, 'hr_pred_bpm')\n"
        "expected = saved['metrics']['test']['mae_macro_bpm']\n"
        "assert abs(recomputed['mae_macro_bpm'] - expected) < 1e-6\n"
        "pd.DataFrame([{\n"
        "    'MAE_macro (BPM)': recomputed['mae_macro_bpm'],\n"
        "    'MAE pooled (BPM)': recomputed['pooled']['mae_bpm'],\n"
        "    'RMSE pooled (BPM)': recomputed['pooled']['rmse_bpm'],\n"
        "    'Pearson r': recomputed['pooled']['pearson_r'],\n"
        "    'Bias (BPM)': recomputed['pooled']['bias_bpm'],\n"
        "}]).round(3)"
    ))
    cells.append(nbf.v4.new_code_cell(
        "condition = pd.DataFrame(recomputed['by_condition'])[['condition','n_windows','mae_macro_bpm','rmse_macro_bpm']]\n"
        "subject = pd.DataFrame(recomputed['by_subject'])[['subject','n_windows','mae_bpm','rmse_bpm','bias_bpm','pearson_r']]\n"
        "display(condition.round(3))\n"
        "display(subject.round(3))"
    ))
    cells.append(nbf.v4.new_code_cell(
        "fig, axes = plt.subplots(1, 2, figsize=(12, 4))\n"
        "axes[0].scatter(frame.hr_ref_bpm, frame.hr_pred_bpm, s=6, alpha=.25)\n"
        "lims = [min(frame.hr_ref_bpm.min(), frame.hr_pred_bpm.min()), max(frame.hr_ref_bpm.max(), frame.hr_pred_bpm.max())]\n"
        "axes[0].plot(lims, lims, '--', color='black', lw=1)\n"
        "axes[0].set(xlabel='HR tham chiếu (BPM)', ylabel='HR dự đoán (BPM)', title='A0 seed 42 — test')\n"
        "frame.assign(abs_error=frame.error_bpm.abs()).groupby('condition').abs_error.mean().sort_values().plot.bar(ax=axes[1], color='#1565C0')\n"
        "axes[1].set(ylabel='MAE pooled (BPM)', xlabel='', title='Sai số theo trạng thái')\n"
        "plt.tight_layout(); plt.show()"
    ))
    cells.append(nbf.v4.new_markdown_cell(
        "## Diễn giải và giới hạn\n\n"
        "- A0 giảm MAE_macro khoảng **35,0%** so với FFT, đạt mục tiêu giảm ≥20%, nhưng chưa đạt ngưỡng tuyệt đối 7 BPM.\n"
        "- A3 (MSE) tốt hơn A0 trong ba seed đã chạy; đây là kết quả thực nghiệm, không phải lựa chọn sau khi xem test.\n"
        "- Lỗi lớn tập trung ở stress và khác biệt giữa người, đặc biệt S16; HR tham chiếu vẫn là nhãn tự động từ ECG.\n"
        "- Các hình scatter/timeline dùng seed 42 được cố định; ca lỗi được chọn trên validation, không chọn từ test."
    ))
    cells.append(nbf.v4.new_code_cell(
        "benchmark = json.loads((ROOT/'outputs/benchmark_cpu.json').read_text(encoding='utf-8'))\n"
        "pd.DataFrame([{\n"
        "    'Network median (ms)': benchmark['network_only']['median_ms'],\n"
        "    'Network P95 (ms)': benchmark['network_only']['p95_ms'],\n"
        "    'Ước lượng end-to-end median (ms)': benchmark['end_to_end_additive_offline_estimate_ms']['median'],\n"
        "    'Tham số': benchmark['trainable_parameters'],\n"
        "    'Checkpoint (bytes)': benchmark['checkpoint_bytes'],\n"
        "}]).round(4)"
    ))
    cells.append(nbf.v4.new_markdown_cell(
        "## Lệnh tái lập\n\n"
        "```powershell\n"
        "python -m src.pipeline preprocess\n"
        "python -m src.pipeline baselines\n"
        "python -m src.pipeline smoke\n"
        "python -m src.pipeline train --variant A0 --seed all\n"
        "python -m src.pipeline train --variant A3 --seed all\n"
        "python -m src.analysis\n"
        "python -m src.benchmark\n"
        "```\n\n"
        "> Huấn luyện đầy đủ được để thành lệnh riêng vì tốn thời gian. Notebook mặc định chỉ đánh giá checkpoint tương thích với hash."
    ))
    nb["cells"] = cells
    nb["nbformat"] = 4
    nb["nbformat_minor"] = 5
    path = ROOT / "TranTienThinh_final.ipynb"
    nbf.write(nb, path)
    print(path.name)


if __name__ == "__main__":
    main()

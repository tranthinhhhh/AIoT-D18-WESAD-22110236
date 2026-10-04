# Đ18 — Ước lượng nhịp tim từ BVP cổ tay trên WESAD

**Sinh viên:** Trần Tiến Thịnh — **MSSV:** 22110236

**Học phần:** Trí tuệ nhân tạo cho IoT

**Giảng viên:** ThS. Hồ Nhựt Minh

Project này tái lập bài toán hồi quy nhịp tim trung bình từ **duy nhất BVP cổ tay**. ECG ngực chỉ tạo HR tham chiếu tự động. Split được khóa theo người: train S2–S10, validation S11/S13, test S14–S17. Metric chính là MAE từng người rồi lấy trung bình đều (`MAE_macro`).

## Kết quả đã chạy

| Phương pháp | Test MAE_macro (BPM) |
|---|---:|
| E0 — median train | 17,768 |
| E1 — FFT | 13,637 |
| A0/E2 — CNN, Huber, 3 seed | 8,867 ± 0,253 |
| A1 — bỏ z-score, 3 seed | 9,139 ± 0,095 |
| A3 — MSE, 3 seed | 8,280 ± 0,328 |

A0 giảm 35,0% so với E1, đạt mục tiêu giảm ≥20% nhưng chưa đạt mục tiêu tuyệt đối ≤7 BPM. A3 thấp nhất trong các cấu hình đã chạy. A2 chưa chạy và không được trình bày như đã hoàn tất.

## Môi trường

- Python 3.12.10; PyTorch 2.14.0 CPU; NumPy 2.5.3; SciPy 1.18.1.
- Cài dependency: `python -m pip install -r requirements.txt`.
- Raw WESAD không nằm trong gói nộp. Đặt các tệp theo cấu trúc `<raw>/S2/S2.pkl`, …, `<raw>/S17/S17.pkl`, rồi chỉnh `project.raw_data_dir` trong `configs/final.yaml` nếu cần.

## Thứ tự chạy

```powershell
python -m src.pipeline preprocess
python -m src.pipeline baselines
python -m src.pipeline smoke
python -m src.pipeline train --variant A0 --seed all
python -m src.pipeline train --variant A3 --seed all
python -m src.pipeline evaluate --variant A1 --seed all
python -m src.analysis
python -m src.benchmark
python -m src.qc_audit
```

`train` tự dùng lại metric đã hoàn tất khi `run_hash` khớp và chỉ resume `last.pt` khi config/manifest tương thích. Không mở tiến trình train thứ hai cho cùng run.

## Đánh giá nhanh bằng notebook

Mở `TranTienThinh_final.ipynb` từ thư mục gốc. Notebook đã được thực thi đến cuối; nó kiểm tra hash, nạp `best.pt` A0 seed 42, suy luận lại 4.444 cửa sổ test và đối chiếu metric đã lưu. Lệnh huấn luyện đầy đủ được tách riêng để tránh train lại ngoài ý muốn.

## Artifact chính

- `configs/final.yaml`: protocol khóa.
- `data/processed/wesad_d18_v2/manifest.json`: hash, nguồn, SOS, phiên bản thư viện.
- `outputs/runs/<variant>_seed<seed>/`: `best.pt`, `last.pt`, log, prediction và metric.
- `outputs/figures/`, `outputs/tables/`: hình/bảng báo cáo.
- `outputs/audit/`: smoke test, chọn ca lỗi, QC review.
- `TranTienThinh_final.docx`, `TranTienThinh_final.ipynb`, `submission/TranTienThinh_final.pptx`.

Config hash: `a9c5a3bfb869a6b473307e3c61b7d4e7b5d23ffe37f3cd8406d7612d1172bf0a`

Manifest hash: `bcc3bd93f84648772e6fad66980cbbcafa93c381ef3724b7d82aeff013841bd8`

## Phạm vi kết luận

Kết quả chỉ áp dụng cho split WESAD cố định và các cửa sổ qua QC. Tiền xử lý dùng lọc zero-phase toàn bản ghi, nên benchmark không chứng minh latency streaming nhân quả. Đây không phải thiết bị y tế hay bằng chứng về độ chính xác lâm sàng.

## GitHub và nộp bài

Repository remote chưa được xác minh. Báo cáo hiện ghi rõ trạng thái này và phải được thay bằng URL GitHub thật trước khi nộp. Hệ thống không tự nộp LMS.

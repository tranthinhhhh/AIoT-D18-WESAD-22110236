# Ma trận yêu cầu đồ án Đ18

Thời điểm audit ban đầu: 16:03 ngày 04/10/2026, múi giờ Asia/Ho_Chi_Minh. Hạn nộp: 23:59 ngày 05/10/2026. Ngân sách còn lại tại thời điểm audit: khoảng 31 giờ 56 phút.

| Yêu cầu | Nguồn | Hiện trạng trước khi sửa | Minh chứng | Thiếu hoặc sai khác | Hành động khóa |
|---|---|---|---|---|---|
| BVP là đầu vào duy nhất, ECG chỉ tạo HR tham chiếu | Đề cương D18 mục 1–3 | Mã giữa kỳ tuân thủ ranh giới đầu vào | `giuaky_cuoiKy/src/de18_pipeline.py` | Kết quả cũ dùng protocol tiền xử lý khác | Giữ ranh giới này trong toàn bộ mã mới |
| Split S2–S10 / S11,S13 / S14–S17 | Đề cương D18 bảng 2 | Đủ 15 tệp `.pkl`; split cũ đúng danh sách | `giuaky_cuoiKy/data/raw/WESAD`; `outputs/tables/split_verification.csv` | Chưa có manifest/hash theo protocol mới | Tạo dataset version và manifest mới |
| Cửa sổ [t,t+8 s), bước 2 s, 256 mẫu BVP | Đề cương D18 mục 2.4 | Pipeline cũ dùng 8 s/2 s và 256 mẫu | `g1_pipeline.py`; `preprocessing_summary.json` | Metadata cũ chưa có cấu hình/hash mới | Tạo `window_id`, thời gian và hash mới |
| BVP 64→32 Hz, Butterworth SOS bậc 4, 0,5–8 Hz | Đề cương D18 bảng 3 | Cũ: bậc 3, 0,6–3,5 Hz | `preprocessing_summary.json` | Không tương thích | Viết và chạy preprocessing v2, không ghi đè output cũ |
| ECG 5–25 Hz và QRS có mô tả đúng | Đề cương D18 mục 2.5 | Cũ: 5–30 Hz, `find_peaks` thích nghi | `g1_pipeline.py` | Không được gọi Pan–Tompkins; dải khác đề cương | Dùng detector năng lượng thích nghi, ghi rõ không phải Pan–Tompkins |
| QC, purity ≥90%, ≥4 R-peak, 35–200 BPM | Đề cương D18 bảng 4 | Có một phần trong G1 cũ | `wesad_de18_window_audit.csv` | Cần định nghĩa plateau/clipping/dropout/RR và thứ tự loại mới | Khóa ngưỡng trong config trước khi dự đoán test |
| E0 median train | Yêu cầu UTEx cập nhật | Chưa có | Không có artifact | Thiếu hoàn toàn | Cài đặt cùng manifest với E1/E2 |
| E1 Hann, NFFT 4096, miền 35/60–200/60 Hz | Đề cương D18 mục 3.2 | Cũ dùng 0,6–3,5 Hz | `fft_metrics.json` | Kết quả cũ chỉ là historical | Chạy lại E1 trên manifest v2 |
| CNN đúng bảng 6, 11.153 tham số | Đề cương D18 bảng 6 | Cũ báo 11.265 tham số | `cnn_metrics_summary.json` | Kiến trúc cũ sai khác | Cài đúng Linear 64→32→1, xác nhận đếm tham số |
| Huber δ=5, AdamW, 100 epoch, patience 15 theo validation MAE_macro | Đề cương D18 mục 3.5, 4.1 | Cũ: Huber mặc định, 60 epoch, patience 10, chọn pooled MAE | `de18_pipeline.py`; log cũ | Không tương thích | Cài train/resume mới, chọn checkpoint theo subject-macro |
| Ba seed 42, 123, 999 | Đề cương D18 mục 4.1 | Có ba run cũ | checkpoint/log giữa kỳ | Không được tái sử dụng vì manifest/config khác | Chạy ba run mới |
| A3 MSE ưu tiên, A1/A2 nếu đủ thời gian | Đề cương D18 bảng 8 | Chưa chạy | Không có artifact | Thiếu | Chạy A3 trước; ghi rõ A1/A2 nếu chưa hoàn tất |
| MAE_macro là chỉ số chính | Đề cương D18 mục 4.4 | Kết quả cũ lấy pooled MAE làm chính | JSON cũ | Không tương thích | Tính subject-macro, pooled và theo điều kiện |
| CPU latency 100 warm-up, ≥1000 lượt, threads=1 | Đề cương D18 mục 4.5 | Cũ chỉ đo 500 lượt, network-only | `cnn_metrics_summary.json` | Thiếu preprocessing/end-to-end và P95 chuẩn | Benchmark lại |
| Báo cáo 15–25 trang, bìa theo mẫu | UTEx và yêu cầu người dùng | Chưa có báo cáo cuối kỳ | Mẫu bìa đã render 10 trang; trang 1 đã kiểm tra | Báo cáo cũ là giữa kỳ, bìa sai mẫu | Tạo `TranTienThinh_final.docx`, render toàn bộ |
| Notebook đánh giá chạy đến cuối | UTEx | Notebook cũ mâu thuẫn protocol mới | `TranTienThinh_22110236_De18_Full.ipynb` | Không dùng làm bản cuối | Tạo notebook mới, full train ở cell riêng |
| PPTX 10–12 slide, 5–7 phút | UTEx cập nhật | Có deck giữa kỳ 9 slide | PPTX cũ | Nội dung và protocol cũ | Tạo deck mới, có notes, render toàn bộ |
| GitHub link thật trong Word | UTEx | Workspace/project không phải Git repo | `git status` báo không có repository | Thiếu repo/account/visibility xác định | Hoàn thiện local trước; chỉ chèn link sau khi xác minh remote |
| Submission sạch và ZIP code | UTEx | Chưa có | `Cuối Kỳ` chỉ có 2 DOCX nguồn | Thiếu | Tạo `submission/`, loại raw data, venv và cache |

## Phân loại kết quả cũ

Các số 43.385/16.432 và split 9.784/2.208/4.440 đã được xác minh có artifact G1 tương ứng nhưng thuộc pipeline bậc 3, BVP 0,6–3,5 Hz và ECG 5–30 Hz. Các metric FFT 11,987 BPM và CNN pooled MAE 7,921 ± 0,188 BPM cũng thuộc protocol cũ, dùng kiến trúc 11.265 tham số và quy tắc chọn checkpoint khác. Tất cả được gắn nhãn **historical** và không được dùng làm kết quả protocol cuối kỳ v2.

## Đối chiếu sau thực thi

- Protocol v2, E0/E1, E2/A0 ba seed, A3 ba seed, A1 ba seed, phân tích, QC, benchmark, notebook, Word và PPTX đều có artifact và đã kiểm tra.
- A2 chưa chạy, đúng ưu tiên thời gian; báo cáo/slide ghi rõ.
- Word 21 trang và PPTX 11 slide đạt giới hạn hình thức; notebook chạy hết.
- Yêu cầu còn mở duy nhất là URL GitHub thật. Không tạo hoặc chèn URL giả; bản hiện tại được đánh dấu chưa sẵn sàng nộp.

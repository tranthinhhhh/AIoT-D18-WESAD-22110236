# Kế hoạch hoàn thiện theo hạn nộp

Mốc lập kế hoạch: 16:03 ngày 04/10/2026. Hạn nộp: 23:59 ngày 05/10/2026. Kế hoạch ưu tiên bằng chứng tái lập và ba sản phẩm bắt buộc trước các mở rộng.

| Chặng | Kết quả phải có | Ngân sách dự kiến | Điều kiện chuyển chặng |
|---|---|---:|---|
| 1. Audit và đóng băng protocol | Ma trận yêu cầu, config v2, kiểm tra dữ liệu/môi trường | 2 giờ | Sai khác giữa kỳ đã được gắn historical |
| 2. Preprocess v2 và QC | NPZ/CSV/audit/hash/hình kiểm tra | 4 giờ | Split, alignment, finite, QC counts đều pass |
| 3. E0/E1 và smoke test E2 | Prediction theo `window_id`, overfit subset, model 11.153 params | 2 giờ | Không có prediction fail, gradient/loss hợp lệ |
| 4. E2 ba seed | Best/last checkpoint, log, prediction, metric theo seed | 5 giờ | Ba seed hoàn tất hoặc resume được |
| 5. A3 | Ba seed MSE trên cùng manifest | 4 giờ | Có artifact đầy đủ; A1/A2 chỉ chạy nếu còn dư thời gian |
| 6. Phân tích và latency | Bảng/hình, paired delta, benchmark CPU | 3 giờ | Tất cả số lấy từ output v2 |
| 7. Notebook, báo cáo, PPTX | IPYNB, DOCX 15–25 trang, PPTX 10–12 slide | 8 giờ | Render và kiểm tra trực quan đạt |
| 8. Đóng gói và kiểm tra nộp | README, demo guide, ZIP, checklist | 3 giờ | Submission không chứa raw/venv/cache |

Mốc bảo vệ: bắt đầu viết phần phương pháp ngay sau khi manifest v2 khóa; chèn kết quả chỉ sau khi metric v2 hoàn tất. Không chờ A1/A2 nếu ảnh hưởng DOCX/PPTX. Không tự nộp LMS.

## Cập nhật thực thi 16:54 ngày 04/10/2026

Các chặng 1–7 đã hoàn tất và có artifact thật. A1 cũng hoàn tất do còn thời gian; A2 không chạy. Chặng 8 đã đóng gói cục bộ nhưng còn chờ URL GitHub thật trước khi có thể đánh dấu “sẵn sàng nộp”.

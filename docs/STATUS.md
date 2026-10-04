# Trạng thái đồ án Đ18

Cập nhật: 16:54 ngày 04/10/2026, Asia/Ho_Chi_Minh. Hạn nộp: 23:59 ngày 05/10/2026.

## Hoàn tất và đã xác minh

- Dataset v2: 43.385 cửa sổ trước QC, giữ 16.422; train/validation/test = 9.770/2.208/4.444.
- Config hash `a9c5a3bfb869a6b473307e3c61b7d4e7b5d23ffe37f3cd8406d7612d1172bf0a`.
- Manifest hash `bcc3bd93f84648772e6fad66980cbbcafa93c381ef3724b7d82aeff013841bd8`.
- E0 MAE_macro 17,768 BPM; E1 13,637 BPM.
- A0/E2: 8,867 ± 0,253 BPM qua seed 42/123/999; giảm 35,0% so E1.
- A3: 8,280 ± 0,328 BPM; A1: 9,139 ± 0,095 BPM. A2 chưa chạy.
- Smoke test pass; CNN A0 có 11.153 tham số.
- CPU network median/P95 = 0,2829/0,3260 ms; 100 warm-up, 1.000 lượt, 1 thread.
- QC trực quan: 225 cửa sổ hợp lệ và 17 cửa sổ bị gắn cờ đã vẽ.
- Notebook cuối kỳ chạy hết 14 cell, tái tính A0 seed 42 và khớp metric.
- Word 21 trang đã render/duyệt; PPTX 11 slide đã finalizer/render/duyệt.
- Git repo cục bộ đã khởi tạo trên nhánh `main`; raw/cache/processed tensor/`last.pt` đều bị loại khỏi tracking.

## Không có tiến trình đang chạy

Không có process train ở thời điểm cập nhật. Không cần tải lại WESAD hoặc train lại các run đã hoàn tất và đúng hash.

## Chặn duy nhất

Chưa có repository/remote GitHub thật được xác minh. Word và slide đang đánh dấu đỏ trạng thái này, vì vậy chưa được gọi là bản sẵn sàng nộp. Không có CUDA; kết quả hợp lệ được huấn luyện/đo trên CPU.

## Kết quả lịch sử không dùng

Kết quả giữa kỳ dùng BVP 0,6–3,5 Hz, Butterworth bậc 3 và kiến trúc 11.265 tham số chỉ là provenance; không trộn vào metric v2.

# Hướng dẫn duyệt QC

## Phạm vi

Bộ QC dùng đúng manifest `bcc3bd93f84648772e6fad66980cbbcafa93c381ef3724b7d82aeff013841bd8`. File `outputs/audit/qc_review_selection.csv` chứa 225 cửa sổ hợp lệ — đúng 5 cửa sổ cho mỗi tổ hợp 15 người × 3 điều kiện — cùng 17 cửa sổ bị gắn cờ chất lượng.

## Cách đọc montage

Mỗi file `outputs/figures/qc/<subject>_qc_15_windows.png` có 5 hàng và 3 cột Baseline/Stress/Amusement. BVP màu xanh và ECG màu cam được chuẩn hóa riêng rồi chồng lên nhau chỉ để xem hình dạng. Dấu × là đỉnh R tự động. ECG không phải đầu vào CNN.

Khi duyệt, kiểm tra:

- BVP còn tính tuần hoàn hợp lý, không phẳng hoặc bão hòa kéo dài.
- Đỉnh R có thứ tự tăng, không dày bất thường và phủ tương đối đều cửa sổ.
- HR hiển thị phù hợp sơ bộ với mật độ đỉnh R.
- Các cửa sổ Stress có thể méo hoặc nhanh hơn, nhưng không tự động xem đó là lỗi.
- Không sửa/xóa cửa sổ chỉ vì CNN hoặc FFT dự đoán kém.

Hai file `flagged_quality_page_1.png` và `flagged_quality_page_2.png` hiển thị 17 cửa sổ bị loại theo `rr_suspicious` hoặc `ecg_clipping`. Đây là audit tính hợp lý hình dạng và nhãn tự động, không phải thẩm định y khoa.

## Kết quả kiểm tra tự động

- 43.385 cửa sổ trước QC; 16.422 giữ lại; 26.963 loại.
- 26.812 cửa sổ ngoài phạm vi điều kiện; 134 không đạt purity; 13 RR đáng ngờ; 4 ECG clipping.
- Tensor 256 mẫu, hữu hạn, thẳng hàng metadata, window_id duy nhất và split không trùng người.

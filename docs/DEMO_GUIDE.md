# Kịch bản thuyết trình 5–7 phút

Deck: `submission/TranTienThinh_final.pptx`. Mỗi slide đã có speaker notes.

| Slide | Thời lượng | Ý chính |
|---:|---:|---|
| 1 | 20 s | Đ18, BVP là đầu vào duy nhất; nêu kết quả A0. |
| 2 | 35 s | Bài toán hồi quy và split theo người; test không tuning. |
| 3 | 40 s | Pipeline v2, QC có dấu vết; scope không đồng nghĩa nhiễu. |
| 4 | 35 s | CNN 11.153 tham số; ECG không vào suy luận. |
| 5 | 35 s | AdamW, ba seed, early stopping theo validation MAE_macro. |
| 6 | 50 s | A0 giảm 35,0% so FFT; chưa đạt 7 BPM; A3 thấp nhất. |
| 7 | 40 s | S16 và Stress khó; không suy diễn nhân quả. |
| 8 | 45 s | Scatter và ca lỗi validation 67,5 BPM; nhãn ECG vẫn tự động. |
| 9 | 40 s | A1/A3; A2 chưa chạy; không bịa ablation đầy đủ. |
| 10 | 35 s | Network <1 ms nhưng pipeline offline và cửa sổ 8 s. |
| 11 | 35 s | Kết luận, giới hạn, hướng tiếp theo và trạng thái GitHub. |

Tổng khoảng 6 phút. Nếu bị hỏi về “ground truth”, dùng thuật ngữ **HR tham chiếu suy ra tự động từ ECG**, không gọi là chân lý tuyệt đối. Nếu bị hỏi vì sao A3 tốt hơn A0, trả lời đây là kết quả trên split hiện tại, chưa đủ để kết luận MSE luôn tốt hơn Huber.

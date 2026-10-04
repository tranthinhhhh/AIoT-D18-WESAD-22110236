# Tiếp tục công việc

## Trạng thái khóa

- Project: `D:\TriTueNhanTaoIOT\Cuối Kỳ`
- Raw WESAD dùng tại chỗ: `D:\TriTueNhanTaoIOT\giuaky_cuoiKy\data\raw\WESAD`
- Python: `D:\TriTueNhanTaoIOT\giuaky_cuoiKy\.venv\Scripts\python.exe`
- Device: CPU; không có process train đang chạy.
- Config/manifest hash: xem `docs/STATUS.md`.

## Việc tiếp theo bắt buộc

1. Nhận URL GitHub thật và lựa chọn public/private từ người dùng.
2. Khởi tạo/kiểm tra local Git, commit và push đúng repository; không đưa raw WESAD, venv, cache hoặc artifact quá lớn ngoài chủ đích.
3. Thay hai cảnh báo GitHub trong `scripts/build_report.py` và cảnh báo slide 11 trong `.build/pptx/build_deck.mjs` bằng URL thật.
4. Dựng lại DOCX/PPTX, render và kiểm tra các trang/slide thay đổi.
5. Cập nhật `docs/SUBMISSION_CHECKLIST.md`, tạo lại ZIP và để người dùng tự nộp LMS.

## Không chạy lại

- Không chạy `preprocess`, E0/E1, A0, A1 hoặc A3 nếu artifact còn đủ và hash khớp.
- Không mở process train thứ hai. A2 chỉ chạy nếu người dùng ưu tiên mở rộng sau khi sản phẩm nộp đã an toàn.

## Lệnh kiểm tra nhanh

```powershell
cd 'D:\TriTueNhanTaoIOT\Cuối Kỳ'
& '..\giuaky_cuoiKy\.venv\Scripts\python.exe' -m compileall -q src scripts
& '..\giuaky_cuoiKy\.venv\Scripts\python.exe' -c "import json; n=json.load(open('TranTienThinh_final.ipynb',encoding='utf-8')); print(sum(o.get('output_type')=='error' for c in n['cells'] for o in c.get('outputs',[])))"
```

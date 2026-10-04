# Tiếp tục công việc

## Trạng thái khóa

- Project: `D:\TriTueNhanTaoIOT\Cuối Kỳ`
- Raw WESAD dùng tại chỗ: `D:\TriTueNhanTaoIOT\giuaky_cuoiKy\data\raw\WESAD`
- Python: `D:\TriTueNhanTaoIOT\giuaky_cuoiKy\.venv\Scripts\python.exe`
- Device: CPU; không có process train đang chạy.
- Config/manifest hash: xem `docs/STATUS.md`.

## Repository

Repository public đã được tạo: `https://github.com/tranthinhhhh/AIoT-D18-WESAD-22110236`.

Nếu tiếp tục sau mốc hoàn thiện, trước hết kiểm tra `git status`, `git remote -v` và trạng thái branch GitHub; không chạy lại thí nghiệm khi artifact/hash vẫn hợp lệ.

## Không chạy lại

- Không chạy `preprocess`, E0/E1, A0, A1 hoặc A3 nếu artifact còn đủ và hash khớp.
- Không mở process train thứ hai. A2 chỉ chạy nếu người dùng ưu tiên mở rộng sau khi sản phẩm nộp đã an toàn.

## Lệnh kiểm tra nhanh

```powershell
cd 'D:\TriTueNhanTaoIOT\Cuối Kỳ'
& '..\giuaky_cuoiKy\.venv\Scripts\python.exe' -m compileall -q src scripts
& '..\giuaky_cuoiKy\.venv\Scripts\python.exe' -c "import json; n=json.load(open('TranTienThinh_final.ipynb',encoding='utf-8')); print(sum(o.get('output_type')=='error' for c in n['cells'] for o in c.get('outputs',[])))"
```

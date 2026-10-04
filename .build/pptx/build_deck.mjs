import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const workspaceDir = "D:/TriTueNhanTaoIOT/Cuối Kỳ";
const buildDir = path.join(workspaceDir, ".build/pptx");
const skillDir = "C:/Users/THINH 9A9/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.12148/skills/presentations";
const { applyPresentationChartFont } = await import(
  pathToFileURL(path.join(skillDir, "container_tools/artifact_tool_utils.mjs")).href,
);

const FONT = "Arial";
const NAVY = "#103A5C";
const BLUE = "#1769AA";
const RED = "#D32F2F";
const ORANGE = "#F28E2B";
const GREEN = "#59A14F";
const PALE = "#EAF3F8";
const INK = "#17242E";
const MUTED = "#5F6B73";
const WHITE = "#FFFFFF";
const LIGHT = "#F6F8FA";
const GITHUB_URL = (process.env.GITHUB_URL ?? "").trim();

await fs.mkdir(path.join(buildDir, "previews"), { recursive: true });
const presentation = Presentation.create({ slideSize: { width: 1280, height: 720 } });

function addShape(slide, geometry, x, y, w, h, fill, line = "none", radius = null) {
  const shape = slide.shapes.add({
    geometry,
    position: { left: x, top: y, width: w, height: h },
    fill: fill === "none" ? "none" : fill,
    line: line === "none" ? { fill: "none", width: 0 } : { fill: line, width: 1 },
  });
  if (radius !== null) shape.borderRadius = radius;
  return shape;
}

function addText(slide, text, x, y, w, h, options = {}) {
  const shape = addShape(slide, "textbox", x, y, w, h, options.fill ?? "none", options.line ?? "none");
  shape.text = text;
  shape.text.style = {
    typeface: FONT,
    fontSize: options.fontSize ?? 24,
    bold: options.bold ?? false,
    color: options.color ?? INK,
    autoFit: options.autoFit ?? "shrinkText",
    verticalAlignment: options.verticalAlignment ?? "middle",
    alignment: options.alignment ?? "left",
  };
  return shape;
}

function addTitle(slide, title, subtitle = null) {
  addText(slide, title, 72, 38, 1110, 58, { fontSize: 34, bold: true, color: NAVY, autoFit: "none" });
  addShape(slide, "rect", 72, 105, 86, 5, RED, "none");
  if (subtitle) addText(slide, subtitle, 175, 91, 1000, 30, { fontSize: 15, color: MUTED });
}

function addFooter(slide, number) {
  addShape(slide, "line", 72, 679, 1136, 1, "none", "#C9D3DB");
  addText(slide, "Đ18 • Trần Tiến Thịnh • 22110236", 72, 683, 560, 22, { fontSize: 11, color: MUTED });
  addText(slide, String(number).padStart(2, "0"), 1130, 683, 78, 22, { fontSize: 11, color: MUTED, alignment: "right" });
}

function addNotes(slide, text) {
  slide.speakerNotes.textFrame.setText(text);
}

async function addImage(slide, relPath, x, y, w, h, alt, fit = "contain") {
  const abs = path.join(workspaceDir, relPath);
  const bytes = await fs.readFile(abs);
  return slide.images.add({
    blob: new Uint8Array(bytes), contentType: "image/png", alt, fit,
    position: { left: x, top: y, width: w, height: h },
  });
}

function styleTable(table, rows, cols, headerFill = NAVY) {
  table.borders.assign({ style: "solid", fill: "#B8C5CE", width: 1 });
  table.cells.block({ row: 0, column: 0, rowCount: 1, columnCount: cols }).assign({
    fill: headerFill,
    textStyle: { typeface: FONT, fontSize: 15, bold: true, color: WHITE },
    margins: { left: 10, right: 10, top: 7, bottom: 7 },
    anchor: "middle",
  });
  if (rows > 1) {
    table.cells.block({ row: 1, column: 0, rowCount: rows - 1, columnCount: cols }).assign({
      textStyle: { typeface: FONT, fontSize: 14, color: INK },
      margins: { left: 10, right: 10, top: 6, bottom: 6 },
      anchor: "middle",
    });
  }
}

// 1 — Cover
{
  const slide = presentation.slides.add();
  slide.background.fill = NAVY;
  addShape(slide, "rect", 0, 0, 22, 720, RED, "none");
  await addImage(slide, ".build/pptx/hcmute-logo.png", 94, 70, 115, 150, "Logo HCMUTE", "contain");
  addText(slide, "BÁO CÁO CUỐI KỲ", 250, 76, 890, 42, { fontSize: 22, bold: true, color: "#B9D8EA" });
  addText(slide, "ƯỚC LƯỢNG NHỊP TIM\nTỪ BVP CỔ TAY", 250, 132, 920, 150, { fontSize: 53, bold: true, color: WHITE, autoFit: "none" });
  addText(slide, "WESAD • CNN 1-D • tham chiếu ECG ngực", 255, 292, 830, 40, { fontSize: 23, color: "#D9EAF4" });
  addShape(slide, "rect", 250, 365, 770, 2, "#7DAEC9", "none");
  addText(slide, "Đ18", 250, 395, 160, 62, { fontSize: 38, bold: true, color: "#FFCE56" });
  addText(slide, "Trần Tiến Thịnh  •  MSSV 22110236", 425, 397, 650, 54, { fontSize: 24, bold: true, color: WHITE });
  addText(slide, "GVHD: ThS. Hồ Nhựt Minh\nHọc phần Trí tuệ nhân tạo cho IoT • 2026–2027", 250, 496, 790, 74, { fontSize: 18, color: "#D9EAF4" });
  addText(slide, "Kết quả chính: A0 8,867 ± 0,253 BPM • giảm 35,0% so với FFT", 250, 614, 875, 36, { fontSize: 18, bold: true, color: "#FFCE56" });
  addNotes(slide, "Mở đầu: đề tài Đ18 ước lượng nhịp tim chỉ từ BVP cổ tay. ECG ngực chỉ tạo nhãn tham chiếu. Nêu ngay kết quả chính nhưng nhấn đây không phải chỉ số lâm sàng. Nguồn: outputs/runs/A0_summary.json; outputs/baselines/baseline_metrics.json.");
}

// 2 — Problem & split
{
  const slide = presentation.slides.add(); slide.background.fill = WHITE; addTitle(slide, "Bài toán và nguyên tắc đánh giá", "Không để thông tin test đi ngược vào huấn luyện");
  addText(slide, "Đầu vào", 78, 153, 240, 30, { fontSize: 18, bold: true, color: BLUE });
  addText(slide, "BVP 8 giây\n256 mẫu @ 32 Hz", 78, 190, 240, 110, { fontSize: 28, bold: true, color: WHITE, fill: BLUE, alignment: "center" });
  addShape(slide, "rightArrow", 335, 220, 95, 48, "#B8CDD9", "none");
  addText(slide, "CNN 1-D", 450, 190, 260, 110, { fontSize: 29, bold: true, color: WHITE, fill: NAVY, alignment: "center" });
  addShape(slide, "rightArrow", 730, 220, 95, 48, "#B8CDD9", "none");
  addText(slide, "Đầu ra\nHR trung bình (BPM)", 845, 190, 320, 110, { fontSize: 27, bold: true, color: WHITE, fill: RED, alignment: "center" });
  addText(slide, "Split theo người", 78, 348, 260, 36, { fontSize: 21, bold: true, color: NAVY });
  const splits = [
    ["TRAIN", "S2–S10", "9.770 cửa sổ", BLUE],
    ["VALIDATION", "S11, S13", "2.208 cửa sổ", ORANGE],
    ["TEST", "S14–S17", "4.444 cửa sổ", GREEN],
  ];
  splits.forEach((s, i) => {
    const x = 78 + i * 365;
    addText(slide, s[0], x, 405, 325, 34, { fontSize: 16, bold: true, color: WHITE, fill: s[3], alignment: "center" });
    addText(slide, `${s[1]}\n${s[2]}`, x, 442, 325, 92, { fontSize: 23, bold: true, color: INK, fill: LIGHT, alignment: "center" });
  });
  addText(slide, "Metric chính: MAE từng người → trung bình đều (MAE_macro)", 78, 576, 1080, 48, { fontSize: 24, bold: true, color: NAVY, fill: PALE, alignment: "center" });
  addFooter(slide, 2);
  addNotes(slide, "Giải thích ranh giới: mô hình chỉ nhận BVP. ECG, mã người và nhãn condition không vào tensor. Split được khóa theo người; validation chọn checkpoint, test chỉ đánh giá cuối. Nguồn: configs/final.yaml; data/processed/wesad_d18_v2/preprocessing_summary.json.");
}

// 3 — Pipeline and QC
{
  const slide = presentation.slides.add(); slide.background.fill = WHITE; addTitle(slide, "Pipeline dữ liệu có dấu vết", "Mọi cửa sổ gắn window_id, config hash và manifest hash");
  const steps = [
    ["1", "WESAD", "BVP 64 Hz\nECG 700 Hz"],
    ["2", "BVP", "64→32 Hz\n0,5–8 Hz"],
    ["3", "ECG", "5–25 Hz\nđỉnh R thích nghi"],
    ["4", "Cửa sổ", "8 s • bước 2 s\npurity ≥90%"],
    ["5", "Artifact", "NPZ + CSV\nmanifest + audit"],
  ];
  steps.forEach((s, i) => {
    const x = 64 + i * 241;
    addShape(slide, "roundRect", x, 166, 195, 164, i === 4 ? NAVY : PALE, i === 4 ? NAVY : "#AAC4D3", 12);
    addText(slide, s[0], x + 14, 178, 36, 36, { fontSize: 18, bold: true, color: WHITE, fill: i === 4 ? RED : BLUE, alignment: "center" });
    addText(slide, s[1], x + 18, 218, 160, 34, { fontSize: 22, bold: true, color: i === 4 ? WHITE : NAVY, alignment: "center" });
    addText(slide, s[2], x + 14, 257, 168, 56, { fontSize: 16, color: i === 4 ? "#DDEBF2" : INK, alignment: "center" });
    if (i < 4) addShape(slide, "rightArrow", x + 198, 225, 33, 35, "#A9BAC5", "none");
  });
  const kpis = [
    ["43.385", "cửa sổ trước QC"], ["16.422", "cửa sổ giữ lại"],
    ["225", "cửa sổ xem QC"], ["17", "cửa sổ gắn cờ đã vẽ"],
  ];
  kpis.forEach((k, i) => {
    const x = 78 + i * 285;
    addText(slide, k[0], x, 390, 245, 58, { fontSize: 35, bold: true, color: i === 1 ? GREEN : NAVY, alignment: "center" });
    addText(slide, k[1], x, 450, 245, 40, { fontSize: 15, color: MUTED, alignment: "center" });
  });
  addText(slide, "QC scope ≠ nhiễu: 26.812 cửa sổ ngoài điều kiện nghiên cứu được tách riêng.", 92, 530, 1040, 42, { fontSize: 21, bold: true, color: RED, alignment: "center" });
  addText(slide, "Detector ECG là thuật toán thích nghi theo cực tính; không gọi là Pan–Tompkins.", 92, 578, 1040, 36, { fontSize: 18, color: INK, fill: LIGHT, alignment: "center" });
  addFooter(slide, 3);
  addNotes(slide, "Tóm tắt pipeline v2. Phân biệt loại do phạm vi điều kiện với loại do chất lượng. Bộ QC trực quan có 5 cửa sổ cho mỗi người/điều kiện, tổng 225. Nguồn: data/processed/wesad_d18_v2/preprocessing_summary.json; outputs/audit/qc_audit_summary.json.");
}

// 4 — Architecture
{
  const slide = presentation.slides.add(); slide.background.fill = WHITE; addTitle(slide, "CNN 1-D gọn nhẹ", "Ba khối tích chập + global pooling + head hồi quy");
  const blocks = [
    ["BVP", "1×256", 130, PALE, INK],
    ["Conv1", "16×128", 160, "#CFE5F2", NAVY],
    ["Conv2", "32×64", 170, "#A9D1E7", NAVY],
    ["Conv3", "64×32", 185, "#74B1D1", WHITE],
    ["GAP", "64×1", 140, BLUE, WHITE],
    ["MLP", "64→32→1", 170, NAVY, WHITE],
  ];
  let x = 60;
  blocks.forEach((b, i) => {
    addShape(slide, "roundRect", x, 224, b[2], 136, b[3], "#7A9CB0", 12);
    addText(slide, b[0], x + 10, 242, b[2] - 20, 42, { fontSize: 24, bold: true, color: b[4], alignment: "center" });
    addText(slide, b[1], x + 10, 290, b[2] - 20, 34, { fontSize: 17, color: b[4], alignment: "center" });
    if (i < blocks.length - 1) addShape(slide, "rightArrow", x + b[2] + 7, 270, 30, 34, "#AAB9C2", "none");
    x += b[2] + 36;
  });
  addText(slide, "11.153", 126, 426, 255, 64, { fontSize: 42, bold: true, color: RED, alignment: "center" });
  addText(slide, "tham số học được", 126, 490, 255, 32, { fontSize: 17, color: MUTED, alignment: "center" });
  addText(slide, "A0: z-score + Huber δ=5 + BatchNorm\nA1: bỏ z-score  •  A3: MSE thay Huber", 430, 430, 690, 92, { fontSize: 22, bold: true, color: NAVY, fill: PALE, alignment: "center" });
  addText(slide, "ECG không xuất hiện trong nhánh suy luận", 310, 560, 660, 44, { fontSize: 22, bold: true, color: WHITE, fill: RED, alignment: "center" });
  addFooter(slide, 4);
  addNotes(slide, "Kiến trúc đúng bảng đặc tả: Conv1/2/3, AdaptiveAvgPool1d và head 64→32→1. Với BatchNorm có 11.153 tham số. A0 là E2 chính; A1 và A3 chỉ đổi một yếu tố. Nguồn: src/model.py; configs/final.yaml; outputs/audit/smoke_test.json.");
}

// 5 — Experiment design table
{
  const slide = presentation.slides.add(); slide.background.fill = WHITE; addTitle(slide, "Thiết kế thực nghiệm khóa trước test", "Checkpoint chọn theo validation MAE_macro");
  const values = [
    ["Hạng mục", "Cấu hình"],
    ["Optimizer", "AdamW • lr 10⁻³ • weight decay 10⁻⁴"],
    ["Huấn luyện", "batch 64 • tối đa 100 epoch • patience 15"],
    ["Seed", "42 • 123 • 999"],
    ["Checkpoint", "epoch có validation MAE_macro thấp nhất"],
    ["Đánh giá", "model.eval() • test không tuning"],
    ["CPU benchmark", "batch=1 • 1 thread • 100 warm-up • 1.000 lượt"],
  ];
  const tbl = slide.tables.add({ rows: values.length, columns: 2, left: 90, top: 150, width: 1100, height: 380, columnWidths: [330, 770], values });
  styleTable(tbl, values.length, 2);
  addText(slide, "MAE_macro = trung bình đều MAE của S14, S15, S16, S17", 120, 558, 1040, 48, { fontSize: 24, bold: true, color: NAVY, fill: PALE, alignment: "center" });
  addText(slide, "Ba seed mô tả biến thiên huấn luyện — không phải ba tập test độc lập.", 120, 615, 1040, 34, { fontSize: 18, color: MUTED, alignment: "center" });
  addFooter(slide, 5);
  addNotes(slide, "Nhấn cách ngăn leakage: early stopping và checkpoint chỉ nhìn validation. Test được mở sau khi protocol khóa. Metric chính là MAE_macro theo người. Nguồn: configs/final.yaml; src/train.py.");
}

// 6 — Overall results
{
  const slide = presentation.slides.add(); slide.background.fill = WHITE; addTitle(slide, "Kết quả tổng thể trên cùng manifest v2", "MAE_macro test — thấp hơn là tốt hơn");
  const chart = slide.charts.add("bar", {
    position: { left: 70, top: 145, width: 750, height: 450 },
    categories: ["E0", "E1", "A0", "A1", "A3"],
    series: [{ name: "MAE_macro (BPM)", values: [17.768, 13.637, 8.867, 9.139, 8.280], fill: BLUE }],
    barOptions: { direction: "column", grouping: "clustered" },
    hasLegend: false,
    dataLabels: { showValue: true, position: "outEnd" },
  });
  applyPresentationChartFont(chart, { fontFamily: FONT });
  addText(slide, "A0", 870, 160, 270, 42, { fontSize: 21, bold: true, color: BLUE });
  addText(slide, "8,867 ± 0,253 BPM", 870, 200, 305, 54, { fontSize: 31, bold: true, color: NAVY });
  addText(slide, "↓ 35,0% so với FFT", 870, 258, 305, 42, { fontSize: 22, bold: true, color: GREEN });
  addText(slide, "A3 thấp nhất", 870, 345, 305, 38, { fontSize: 20, bold: true, color: RED });
  addText(slide, "8,280 ± 0,328 BPM", 870, 385, 305, 54, { fontSize: 29, bold: true, color: NAVY });
  addText(slide, "Mục tiêu ≤7 BPM: chưa đạt", 850, 485, 345, 62, { fontSize: 22, bold: true, color: WHITE, fill: RED, alignment: "center" });
  addText(slide, "Mục tiêu giảm ≥20%: đạt", 850, 558, 345, 48, { fontSize: 20, bold: true, color: WHITE, fill: GREEN, alignment: "center" });
  addFooter(slide, 6);
  addNotes(slide, "E0 là median train, E1 là FFT. A0 đạt mục tiêu giảm tương đối nhưng không đạt 7 BPM. A3 dùng MSE cho kết quả tốt nhất trong các cấu hình đã chạy; báo cáo đúng thực nghiệm, không đổi tên mô hình chính sau test. Nguồn: outputs/tables/overall_results_v2.csv; outputs/runs/A0_summary.json; outputs/runs/A3_summary.json.");
}

// 7 — Stratified results
{
  const slide = presentation.slides.add(); slide.background.fill = WHITE; addTitle(slide, "Sai số không đồng đều", "Stress và khác biệt giữa người là hai điểm nghẽn chính");
  const chart1 = slide.charts.add("bar", {
    position: { left: 58, top: 150, width: 565, height: 390 },
    categories: ["S14", "S15", "S16", "S17"],
    series: [{ name: "MAE", values: [9.406, 3.855, 12.498, 9.708], fill: BLUE }],
    barOptions: { direction: "column", grouping: "clustered" }, hasLegend: false,
    dataLabels: { showValue: true, position: "outEnd" },
  });
  applyPresentationChartFont(chart1, { fontFamily: FONT });
  addText(slide, "A0 theo người", 180, 132, 320, 32, { fontSize: 18, bold: true, color: NAVY, alignment: "center" });
  const chart2 = slide.charts.add("bar", {
    position: { left: 660, top: 150, width: 565, height: 390 },
    categories: ["Amusement", "Baseline", "Stress"],
    series: [{ name: "MAE_macro", values: [3.461, 4.167, 19.869], fill: ORANGE }],
    barOptions: { direction: "column", grouping: "clustered" }, hasLegend: false,
    dataLabels: { showValue: true, position: "outEnd" },
  });
  applyPresentationChartFont(chart2, { fontFamily: FONT });
  addText(slide, "A0 theo điều kiện", 780, 132, 320, 32, { fontSize: 18, bold: true, color: NAVY, alignment: "center" });
  addText(slide, "S16 cao nhất • Stress ≈ 4,8× Baseline", 110, 565, 1060, 48, { fontSize: 25, bold: true, color: WHITE, fill: NAVY, alignment: "center" });
  addText(slide, "Mô tả trên split hiện tại; không suy diễn Stress gây ra sai số.", 110, 620, 1060, 30, { fontSize: 17, color: MUTED, alignment: "center" });
  addFooter(slide, 7);
  addNotes(slide, "Các giá trị là trung bình A0 qua ba seed. S16 khó nhất; Stress chi phối lỗi. Tuy nhiên condition đồng biến với HR, vận động và subject nên không kết luận nhân quả. Nguồn: outputs/runs/A0_summary.json; outputs/figures/error_by_subject_condition.png.");
}

// 8 — Failure evidence
{
  const slide = presentation.slides.add(); slide.background.fill = WHITE; addTitle(slide, "Bằng chứng lỗi: mô hình co về vùng HR trung bình", "Ca lỗi được chọn trên validation, không chọn từ test");
  await addImage(slide, "outputs/figures/scatter_identity.png", 58, 145, 490, 380, "Scatter HR tham chiếu và dự đoán", "contain");
  await addImage(slide, "outputs/figures/failure_case_validation_fixed.png", 570, 142, 650, 395, "Ca lỗi validation với BVP, FFT, ECG và đỉnh R", "contain");
  addText(slide, "S11 • Stress", 90, 548, 260, 34, { fontSize: 18, bold: true, color: RED });
  addText(slide, "HR_ref 132,6 → CNN 65,2 BPM\n|error| = 67,5 BPM", 90, 582, 390, 67, { fontSize: 23, bold: true, color: NAVY });
  addText(slide, "Bias A0: −4,04 ± 0,86 BPM\nPearson r: 0,835 ± 0,009", 680, 558, 430, 74, { fontSize: 22, bold: true, color: INK, fill: PALE, alignment: "center" });
  addFooter(slide, 8);
  addNotes(slide, "Hình scatter dùng seed 42 cố định. Ca lỗi lớn nhất được chọn trên validation: S11, Stress, HR tham chiếu 132,6 nhưng CNN 65,2. ECG và R-peaks được đưa vào hình để kiểm tra nhãn, không phải đầu vào mô hình. Nguồn: outputs/audit/failure_case_selection.json; outputs/figures/scatter_identity.png; outputs/figures/failure_case_validation_fixed.png.");
}

// 9 — Ablation
{
  const slide = presentation.slides.add(); slide.background.fill = WHITE; addTitle(slide, "Ablation: thay đúng một yếu tố", "Ba seed cho A0, A1, A3; A2 được ghi rõ chưa chạy");
  const values = [
    ["Biến thể", "Thay đổi", "MAE_macro", "So với E1"],
    ["A0", "z-score + Huber + BN", "8,867 ± 0,253", "−35,0%"],
    ["A1", "Bỏ z-score", "9,139 ± 0,095", "−33,0%"],
    ["A2", "Bỏ BatchNorm", "Chưa chạy", "—"],
    ["A3", "MSE thay Huber", "8,280 ± 0,328", "−39,3%"],
  ];
  const tbl = slide.tables.add({ rows: values.length, columns: 4, left: 70, top: 155, width: 1140, height: 280, columnWidths: [170, 410, 300, 260], values });
  styleTable(tbl, values.length, 4);
  tbl.getCell(4, 0).fill = "#E5F3E3"; tbl.getCell(4, 1).fill = "#E5F3E3"; tbl.getCell(4, 2).fill = "#E5F3E3"; tbl.getCell(4, 3).fill = "#E5F3E3";
  await addImage(slide, "outputs/figures/learning_curves_v2.png", 100, 455, 620, 180, "Đường học train và validation", "contain");
  addText(slide, "Kết luận", 770, 470, 335, 36, { fontSize: 20, bold: true, color: RED, alignment: "center" });
  addText(slide, "Z-score giúp A0 tốt hơn A1.\nMSE tốt hơn Huber trên split này.\nChưa đủ để khái quát ngoài WESAD.", 745, 510, 390, 118, { fontSize: 21, bold: true, color: NAVY, fill: PALE, alignment: "center" });
  addFooter(slide, 9);
  addNotes(slide, "A1 cho thấy bỏ z-score làm xấu kết quả. A3 bất ngờ tốt hơn A0. A2 chưa chạy vì ưu tiên sản phẩm bắt buộc; không trình bày như đã hoàn thành. Nguồn: outputs/runs/A0_summary.json; A1_summary.json; A3_summary.json; outputs/figures/learning_curves_v2.png.");
}

// 10 — Latency
{
  const slide = presentation.slides.add(); slide.background.fill = WHITE; addTitle(slide, "Độ trễ CPU nhỏ — nhưng pipeline hiện tại vẫn offline", "Intel CPU • PyTorch 2.14 CPU • 1 thread • batch=1");
  const chart = slide.charts.add("bar", {
    position: { left: 70, top: 165, width: 610, height: 380 },
    categories: ["Network median", "Network P95", "E2E median*"],
    series: [{ name: "µs", values: [282.9, 326.0, 291.0], fill: BLUE }],
    barOptions: { direction: "column", grouping: "clustered" }, hasLegend: false,
    dataLabels: { showValue: true, position: "outEnd" },
  });
  applyPresentationChartFont(chart, { fontFamily: FONT });
  addText(slide, "Đơn vị biểu đồ: µs (1.000 µs = 1 ms)", 115, 548, 520, 24, { fontSize: 15, color: MUTED, alignment: "center" });
  addText(slide, "11.153", 760, 165, 360, 74, { fontSize: 48, bold: true, color: RED, alignment: "center" });
  addText(slide, "tham số", 760, 238, 360, 30, { fontSize: 18, color: MUTED, alignment: "center" });
  addText(slide, "53.089 byte", 760, 300, 360, 60, { fontSize: 34, bold: true, color: NAVY, alignment: "center" });
  addText(slide, "checkpoint", 760, 360, 360, 30, { fontSize: 18, color: MUTED, alignment: "center" });
  addText(slide, "8 s quan sát  •  cập nhật mỗi 2 s", 730, 435, 420, 54, { fontSize: 23, bold: true, color: WHITE, fill: NAVY, alignment: "center" });
  addText(slide, "*E2E là ước lượng cộng dồn từ tiền xử lý offline amortized — không phải latency streaming nhân quả.", 95, 576, 1070, 58, { fontSize: 18, bold: true, color: RED, fill: "#FFF1F1", alignment: "center" });
  addFooter(slide, 10);
  addNotes(slide, "Network inference dưới 1 ms trên CPU, nhưng cửa sổ phải tích lũy 8 giây và lọc hiện tại là sosfiltfilt toàn bản ghi. Vì vậy không tuyên bố end-to-end streaming dưới 1 ms hay MCU-ready. Nguồn: outputs/benchmark_cpu.json.");
}

// 11 — Conclusion
{
  const slide = presentation.slides.add(); slide.background.fill = NAVY;
  addText(slide, "KẾT LUẬN", 76, 54, 480, 58, { fontSize: 36, bold: true, color: WHITE });
  addShape(slide, "rect", 76, 123, 92, 5, RED, "none");
  const items = [
    ["01", "Đạt mục tiêu tương đối", "A0 giảm 35,0% MAE_macro so với FFT."],
    ["02", "Chưa đạt 7 BPM", "A0 8,867 ± 0,253; A3 8,280 ± 0,328 BPM."],
    ["03", "Điểm nghẽn rõ ràng", "Stress, S16 và xu hướng đánh giá thấp HR cao."],
    ["04", "Bằng chứng tái lập", "Hash, checkpoint, log, prediction, notebook và QC đầy đủ."],
  ];
  items.forEach((it, i) => {
    const y = 165 + i * 98;
    addText(slide, it[0], 86, y, 72, 55, { fontSize: 23, bold: true, color: "#FFCE56", alignment: "center" });
    addText(slide, it[1], 180, y, 390, 34, { fontSize: 22, bold: true, color: WHITE });
    addText(slide, it[2], 180, y + 35, 800, 36, { fontSize: 17, color: "#D9EAF4" });
  });
  addShape(slide, "roundRect", 780, 174, 395, 330, "#164C74", "#6F99B4", 16);
  addText(slide, "Bước tiếp theo", 820, 205, 315, 42, { fontSize: 26, bold: true, color: "#FFCE56", alignment: "center" });
  addText(slide, "• Xác minh nhãn ECG theo mẫu\n• Vùng tiếp nhận dài hơn\n• LOSO + validation nội bộ\n• Tiền xử lý streaming nhân quả\n• Benchmark trên phần cứng đích", 820, 260, 315, 205, { fontSize: 20, color: WHITE });
  addText(slide, GITHUB_URL ? `GitHub: ${GITHUB_URL}` : "GitHub: chờ URL repository thật trước khi nộp", 110, 600, 1060, 46, { fontSize: GITHUB_URL ? 18 : 21, bold: true, color: WHITE, fill: GITHUB_URL ? GREEN : RED, alignment: "center" });
  addText(slide, "Không tự nộp LMS", 495, 660, 290, 28, { fontSize: 14, color: "#B9D8EA", alignment: "center" });
  addNotes(slide, "Kết luận ngắn gọn: mục tiêu tương đối đạt, mục tiêu tuyệt đối chưa đạt. Giá trị chính là pipeline minh bạch và tái lập. Nêu hướng tiếp theo. Trước khi nộp phải thay trường GitHub bằng URL thật; không tự nộp LMS. Nguồn: toàn bộ artifact protocol v2 trong dự án.");
}

const candidatePath = path.join(buildDir, "candidate.pptx");
await (await PresentationFile.exportPptx(presentation)).save(candidatePath);
for (let i = 0; i < presentation.slides.items.length; i += 1) {
  const slide = presentation.slides.items[i];
  const preview = await presentation.export({ slide, format: "png", scale: 1 });
  await fs.writeFile(path.join(buildDir, "previews", `slide-${String(i + 1).padStart(2, "0")}.png`), new Uint8Array(await preview.arrayBuffer()));
  const layout = await slide.export({ format: "layout" });
  await fs.writeFile(path.join(buildDir, "previews", `slide-${String(i + 1).padStart(2, "0")}.layout.json`), await layout.text());
}
console.log(candidatePath);

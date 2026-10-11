import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { Presentation, PresentationFile } from "file:///C:/Users/trand/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";

const root = process.cwd();
const out = path.join(root, "deliverables");
const build = path.join(root, ".phase4_ppt_build");
const skillDir = "C:/Users/trand/.codex/plugins/cache/openai-primary-runtime/presentations/26.1009.11318/skills/presentations";
const runtimePython = "C:/Users/trand/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe";
const finalPptx = path.join(out, "Project_08_trinh_bay_bao_ve.pptx");
await fs.mkdir(out, { recursive: true });
await fs.mkdir(build, { recursive: true });

const deck = Presentation.create({ slideSize: { width: 1280, height: 720 } });
const navy = "#183B5B", blue = "#2D638D", ink = "#17212B", muted = "#526170", pale = "#F7F9FB", font = "Arial";
function text(slide, value, left, top, width, height, size, opts = {}) {
  const item = slide.shapes.add({ geometry: "textbox", position: { left, top, width, height }, fill: "none", line: { style: "solid", fill: "none", width: 0 } });
  item.text = value;
  item.text.style = { fontFamily: font, fontSize: size, color: opts.color || ink, bold: opts.bold || false, verticalAlignment: opts.verticalAlignment || "middle", paragraphAlignment: opts.align || "left" };
  return item;
}
function line(slide, left, top, width, color = blue) { return slide.shapes.add({ geometry: "rect", position: { left, top, width, height: 5 }, fill: color, line: { style: "solid", fill: color, width: 0 } }); }
function base(title, subtitle = "") { const slide = deck.slides.add(); slide.background.fill = pale; line(slide, 0, 0, 1280, navy); text(slide, title, 72, 42, 1136, 54, 32, { bold: true, color: navy }); if (subtitle) text(slide, subtitle, 74, 102, 1100, 32, 17, { color: muted }); return slide; }
function points(slide, items, { left = 88, top = 172, width = 500, size = 22, gap = 74 } = {}) { items.forEach((item, i) => text(slide, item, left, top + i * gap, width, 60, size, { color: ink })); }
function footer(slide, number) { text(slide, `Project 08 | ${number}/11`, 1020, 676, 180, 22, 11, { color: muted, align: "right" }); }
async function image(slide, relative, left, top, width, height, alt) { const bytes = await fs.readFile(path.join(root, relative)); slide.images.add({ blob: bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength), contentType: "image/png", alt, fit: "contain", position: { left, top, width, height } }); }

let s = deck.slides.add(); s.background.fill = navy; line(s, 88, 112, 115, "#8BC7D4"); text(s, "Dự đoán nguy cơ trễ hạn", 88, 166, 920, 62, 42, { bold: true, color: "#FFFFFF" }); text(s, "thanh toán thẻ tín dụng", 88, 225, 920, 62, 42, { bold: true, color: "#FFFFFF" }); text(s, "Project 08 | Học máy cơ bản", 90, 314, 680, 32, 21, { color: "#C6DDE8" }); text(s, "Thành viên: Trần Huy, Duy Huy\nGiảng viên: [bổ sung]\nNgày báo cáo: [bổ sung]", 90, 530, 520, 70, 18, { color: "#E5EFF4" });

s = base("Bài toán và mục tiêu", "Dự đoán nguy cơ default trong tháng kế tiếp từ dữ liệu lịch sử"); points(s, ["Đầu vào: hạn mức, PAY_*, số dư hóa đơn và khoản thanh toán 6 tháng.", "Đầu ra: xác suất default và cảnh báo theo ngưỡng đã chốt.", "Phạm vi: học tập và hỗ trợ nhắc thanh toán."], { width: 830, top: 190, gap: 92 }); text(s, "Không dùng mô hình để tự động quyết định cấp tín dụng.", 88, 514, 810, 44, 21, { bold: true, color: blue }); footer(s, 2);

s = base("Dữ liệu UCI", "Default of Credit Card Clients: 30.000 khách hàng, 25 cột"); points(s, ["Target: default_payment_next_month.", "23 đặc trưng: 14 biến số liên tục và 9 biến phân loại.", "ID chỉ phục vụ quản lý bản ghi, không đưa vào mô hình."], { width: 530, top: 177, size: 20, gap: 80 }); await image(s, "reports/figures/train_target_distribution.png", 680, 170, 465, 355, "Phân bố lớp trên train"); text(s, "Hình: phân bố target chỉ trên train", 725, 543, 390, 22, 13, { color: muted, align: "center" }); footer(s, 3);

s = base("Quy trình và chống rò rỉ dữ liệu", "Train/validation/test giữ vai trò tách biệt"); points(s, ["Chia stratify 60/20/20 với random_state = 42.", "EDA chỉ thực hiện trên train.", "Imputation, scaling và one-hot nằm trong Pipeline.", "Validation chọn C và ngưỡng; test chỉ đánh giá cuối cùng."], { width: 535, top: 164, size: 19, gap: 68 }); await image(s, "reports/figures/train_continuous_feature_correlation.png", 646, 154, 518, 394, "Heatmap tương quan trên train"); text(s, "Hình: tương quan biến liên tục trên train", 700, 558, 420, 22, 13, { color: muted, align: "center" }); footer(s, 4);

s = base("Baseline và mô hình chính", "So sánh công bằng bằng Stratified Cross-Validation trên train"); points(s, ["Baseline: luôn dự đoán không-default.", "Ứng viên: Logistic Regression không trọng số và class_weight = balanced.", "C = 1,0 được chọn bằng CV; Pipeline fit riêng trong từng fold.", "Chọn bản không trọng số dựa trên chi phí validation và Brier score."], { width: 1010, top: 162, size: 21, gap: 76 }); text(s, "Không xem chênh lệch AP rất nhỏ là bằng chứng hơn hẳn.", 90, 503, 940, 38, 19, { bold: true, color: blue }); footer(s, 5);

s = base("Bốn thí nghiệm", "Các chỉ số được xem cùng nhau thay vì chỉ dựa vào accuracy"); points(s, ["Accuracy, Average Precision và recall lớp default.", "Calibration: reliability diagram và Brier score.", "Ngưỡng 0,500, 0,1667 và ngưỡng tối ưu trên validation.", "Audit theo SEX, EDUCATION và MARRIAGE."], { width: 540, top: 165, size: 21, gap: 75 }); await image(s, "reports/figures/validation_reliability_diagram.png", 670, 173, 455, 315, "Reliability diagram validation"); text(s, "Hình: calibration trên validation", 710, 505, 380, 22, 13, { color: muted, align: "center" }); footer(s, 6);

s = base("Ngưỡng quyết định theo chi phí", "Ma trận chi phí giả định: FP = 1, FN = 5, TP = TN = 0"); points(s, ["Ngưỡng lý thuyết theo chi phí: 0,1667.", "Ngưỡng chọn trên validation: 0,150.", "Chi phí validation: 3.405, tương đương 0,5675 mỗi khách hàng.", "Ngưỡng thấp tăng recall và tăng số cảnh báo nhầm."], { width: 550, top: 164, size: 20, gap: 69 }); await image(s, "reports/figures/validation_confusion_matrix_threshold_0.150.png", 700, 150, 400, 400, "Ma trận nhầm lẫn validation ở threshold 0.150"); footer(s, 7);

s = base("Kết quả test sau khi đóng băng", "Test được đánh giá một lần sau khi khóa pipeline, C, calibration và threshold"); points(s, ["Accuracy 64,52% | Precision 35,42% | Recall 73,40% | F1 47,78%.", "Average Precision 52,54% | ROC-AUC 75,91% | Brier 0,1388.", "TN 2.897 | FP 1.776 | FN 353 | TP 974.", "Chi phí giả định: 3.541, tương đương 0,5902 mỗi khách hàng."], { width: 590, top: 162, size: 18, gap: 68 }); await image(s, "reports/figures/final_test_confusion_matrix.png", 700, 145, 415, 415, "Ma trận nhầm lẫn test"); footer(s, 8);

s = base("Khả năng xếp hạng và audit theo nhóm", "Audit mang tính mô tả, không chứng minh mô hình công bằng"); points(s, ["SEX=1: recall 78,61%; SEX=2: recall 69,58%.", "Các nhóm EDUCATION 0, 4, 5, 6 và MARRIAGE 0, 3 có ít mẫu.", "Giữ mã chưa rõ nghĩa thành nhóm riêng khi báo cáo."], { width: 550, top: 166, size: 20, gap: 79 }); await image(s, "reports/figures/final_test_group_audit_rates.png", 650, 150, 525, 385, "Biểu đồ audit theo nhóm"); footer(s, 9);

s = base("Sản phẩm triển khai", "FastAPI phục vụ pipeline đã đóng băng; ứng dụng không huấn luyện theo request"); points(s, ["POST /api/risk-score nhận đúng 23 đặc trưng.", "API từ chối ID, target, dữ liệu thiếu, sai kiểu hoặc không hữu hạn.", "Kết quả gồm xác suất default, ngưỡng 0,150 và cảnh báo.", "Web có ba màn hình: Giới thiệu, Mô phỏng, Dashboard/model card."], { width: 980, top: 165, size: 21, gap: 76 }); text(s, "Thanh trượt dashboard chỉ minh họa trade-off trên validation.", 90, 518, 980, 36, 19, { bold: true, color: blue }); footer(s, 10);

s = base("Kết luận", "Pipeline tái lập được từ dữ liệu thô đến đánh giá và ứng dụng web"); points(s, ["Nhóm giữ test độc lập và chọn ngưỡng bằng validation theo chi phí giả định.", "Mô hình ưu tiên phát hiện default, chấp nhận đánh đổi bằng cảnh báo nhầm.", "Hạn chế: dữ liệu lịch sử một nguồn; ngưỡng chi phí cần nghiệp vụ xác nhận.", "Hướng tiếp theo: kiểm tra trên dữ liệu mới, theo dõi drift và đánh giá định kỳ."], { width: 1035, top: 160, size: 21, gap: 74 }); text(s, "Cảm ơn thầy/cô và các bạn", 88, 540, 800, 45, 26, { bold: true, color: navy }); footer(s, 11);

const { finalizePresentation } = await import(pathToFileURL(path.join(skillDir, "container_tools", "artifact_tool_utils.mjs")).href);
const candidate = path.join(build, "bao_ve_candidate.pptx");
const pptx = await PresentationFile.exportPptx(deck);
await pptx.save(candidate);
await finalizePresentation({ workspaceDir: root, candidatePath: candidate, finalPath: finalPptx, pythonExecutable: runtimePython, integrityValidatorPath: path.join(skillDir, "container_tools", "inspect_presentation_package_integrity.py"), layoutValidatorPath: path.join(skillDir, "container_tools", "inspect_presentation_layout_geometry.py"), layoutArgs: ["--expected-slide-size-emu", "12192000,6858000", "--validate-bullet-geometry", "--validate-heading-fit"], fontPolicy: { basis: "design", families: [font] }, verifyArtifactToolImport: true, receiptPath: path.join(build, "bao_ve_validation.json") });

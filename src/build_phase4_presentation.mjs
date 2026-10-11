import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "file:///C:/Users/trand/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";

const root = process.cwd();
const out = path.join(root, "deliverables");
const build = path.join(root, ".phase4_ppt_build");
await fs.mkdir(out, { recursive: true });
await fs.mkdir(build, { recursive: true });

const deck = Presentation.create({ slideSize: { width: 1280, height: 720 } });
const navy = "#12355B", teal = "#007C83", ink = "#16202A", muted = "#53616E", pale = "#F5F8FA";
function box(slide, text, left, top, width, height, size, opts = {}) {
  const s = slide.shapes.add({geometry:"textbox",position:{left,top,width,height},fill:"none",line:{style:"solid",fill:"none",width:0}});
  s.text = text; s.text.style = {fontFamily:"Arial",fontSize:size,color:opts.color||ink,bold:opts.bold||false,verticalAlignment:"middle",paragraphAlignment:opts.align||"left"}; return s;
}
function base(title, subtitle="") {
  const slide = deck.slides.add(); slide.background.fill = pale;
  const bar = slide.shapes.add({geometry:"rect",position:{left:0,top:0,width:1280,height:22},fill:navy,line:{style:"solid",fill:navy,width:0}});
  box(slide, title, 72, 48, 1140, 58, 32, {bold:true,color:navy});
  if (subtitle) box(slide, subtitle, 74, 110, 1110, 34, 17, {color:muted});
  return slide;
}
function bullets(slide, items, top=165) { items.forEach((x,i)=>box(slide, `• ${x}`, 92, top+i*72, 1050, 58, 20, {color:ink})); }
function footer(slide, n){ box(slide, `Project 08   |   ${n}/11`, 1000, 680, 200, 20, 11, {color:muted,align:"right"}); }

let s = deck.slides.add(); s.background.fill=navy; box(s,"Project 08",88,120,600,70,42,{bold:true,color:"#FFFFFF"}); box(s,"Ước lượng nguy cơ trễ hạn thanh toán thẻ tín dụng",88,204,760,60,28,{color:"#FFFFFF"}); box(s,"Báo cáo bàn giao | [BỔ SUNG tên thành viên] | 08/10/2026",90,580,680,28,16,{color:"#D7E8F0"});

s=base("Bối cảnh và mục tiêu","Hỗ trợ học tập cho quy trình nhắc thanh toán, không quyết định cấp tín dụng"); bullets(s,["Target: default_payment_next_month theo bộ dữ liệu UCI", "Câu hỏi: ưu tiên cảnh báo với trade-off chi phí giả định", "Không suy diễn nguyên nhân cá nhân hoặc đưa ra quyết định bất lợi"]); footer(s,2);

s=base("Dữ liệu và thời điểm dự đoán","Default of Credit Card Clients từ UCI, 30.000 bản ghi, 25 cột"); bullets(s,["Lịch sử 6 tháng: PAY_*, BILL_AMT*, PAY_AMT*", "ID chỉ cố định split, không là đặc trưng; target không đi vào pipeline", "CSV Kaggle chỉ dùng đối chiếu nội dung, không thay nguồn UCI"]); footer(s,3);

s=base("Chống leakage","Cùng split cho toàn bộ thí nghiệm và test bị cô lập"); bullets(s,["Stratified 60/20/20, random_state=42; EDA chỉ dùng train", "Imputation, scaling, one-hot nằm trong Pipeline và fit trong train/fold", "Không oversample trước split; không dùng test để chọn C, model hay threshold"]); footer(s,4);

s=base("Baseline và lựa chọn mô hình","Logistic Regression, C chọn bằng Stratified 5-fold CV trên train"); bullets(s,["Baseline luôn không-default đặt mốc tối thiểu", "Unweighted và class_weight=balanced cùng C=1.0", "Không gọi chênh AP ~0.0004 là vượt trội rõ rệt; chọn unweighted theo chi phí validation và Brier"]); footer(s,5);

s=base("Bốn thí nghiệm bắt buộc","Accuracy không đủ khi lớp default ít"); bullets(s,["So sánh accuracy, AP và recall default", "Reliability diagram và Brier cho xác suất gốc", "Ngưỡng 0.5, 0.1667 và validation minimum; audit SEX, EDUCATION, MARRIAGE"]); footer(s,6);

s=base("Ngưỡng 0.150 và chi phí giả định","Quy ước FP=1, FN=5, TP=TN=0; không phải chi phí thực ngân hàng"); bullets(s,["Ngưỡng lý thuyết: 1 / (1 + 5) = 0.1667", "Validation unweighted @ 0.150: cost 3405, 0.5675/khách, recall 0.7483", "Hạ ngưỡng tăng recall nhưng tăng cảnh báo nhầm và làm accuracy giảm"]); footer(s,7);

s=base("Kết quả test sau freeze","Đánh giá duy nhất sau khi pipeline, C, calibration và threshold được khóa"); bullets(s,["Accuracy 0.6452 | Precision 0.3542 | Recall 0.7340 | F1 0.4778", "AP 0.5254 | ROC-AUC 0.7591 | Brier 0.1388", "TN 2897 | FP 1776 | FN 353 | TP 974 | Cost 3541 (0.5902/khách)"]); footer(s,8);

s=base("Audit và giới hạn","Không kết luận công bằng từ một chỉ số hoặc từ nhóm mẫu nhỏ"); bullets(s,["SEX mã 1: recall 0.7861, FPR 0.4318; mã 2: recall 0.6958, FPR 0.3464", "EDUCATION 0, 4, 5, 6 và MARRIAGE 0, 3 có nhóm nhỏ hoặc ít default", "Mã chưa rõ nghĩa vẫn là nhóm riêng; audit không chứng minh quan hệ nhân quả"]); footer(s,9);

s=base("Sản phẩm web và API","Pipeline phục vụ được nạp một lần khi khởi động"); bullets(s,["POST /api/risk-score nhận 23 đặc trưng, từ chối ID/target và dữ liệu không hợp lệ", "Trả xác suất, threshold 0.150, nhóm cảnh báo và model version", "Ba màn hình: Giới thiệu, Mô phỏng, Dashboard; thanh trượt chỉ minh họa validation"]); footer(s,10);

s=base("Demo và kết luận","Demo 5-7 phút trong tổng thời lượng 12-15 phút"); bullets(s,["Demo: dữ liệu → leakage → dashboard → mô phỏng → API → giới hạn", "Chỉ phục vụ học tập và hỗ trợ nhắc thanh toán", "Không tuning lại từ test; tái lập theo README và deliverables/reproducibility.md"]); footer(s,11);

const pptx=await PresentationFile.exportPptx(deck); await pptx.save(path.join(out,"Project_08_trinh_bay_draft.pptx"));

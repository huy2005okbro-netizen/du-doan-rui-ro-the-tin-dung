"""Create the Phase 4 handover report and administrative deliverables.

This script only reads frozen results.  It never loads or refits the model and
never writes to reports/final_test_evaluation.json.
"""
from __future__ import annotations

import json
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt
from docx.oxml.ns import qn
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables"
FIG = ROOT / "reports" / "figures"


PAGES = [
    ("Tóm tắt", [
        "Project 08 xây dựng một hệ thống học tập để ước lượng nguy cơ khách hàng trễ hạn thanh toán thẻ tín dụng trong tháng kế tiếp. Dữ liệu huấn luyện là Default of Credit Card Clients từ UCI Machine Learning Repository. CSV từ Kaggle chỉ được dùng để đối chiếu nội dung, không thay thế nguồn và không được ghi là dữ liệu tải trực tiếp từ UCI.",
        "Mô hình cuối là Logistic Regression không class weight, C=1.0, giữ xác suất gốc và dùng ngưỡng cảnh báo 0.150. Lựa chọn được khóa bằng validation trước khi mở test. Trên test một lần, mô hình có AP 0.5254, ROC-AUC 0.7591, Brier 0.1388, recall default 0.7340 và precision 0.3542.",
        "Hệ thống chỉ phục vụ học tập và hỗ trợ nhắc thanh toán. Nó không phải công cụ tự động quyết định cấp tín dụng, định giá, xử phạt hoặc suy diễn nguyên nhân đối với một cá nhân."
    ]),
    ("Bối cảnh và câu hỏi", [
        "Bài toán là phân loại nhị phân: dự đoán default_payment_next_month, nghĩa là khách hàng có ghi nhận trễ hạn thanh toán vào tháng tiếp theo trong bộ dữ liệu nguồn. Thời điểm dự đoán là sau khi sáu tháng lịch sử PAY, BILL_AMT và PAY_AMT đã có sẵn, trước nhãn tháng tiếp theo.",
        "Câu hỏi chính: liệu lịch sử tín dụng, hóa đơn và thanh toán có hỗ trợ xếp ưu tiên nhắc thanh toán với một ngưỡng chi phí giả định hay không. Câu hỏi không phải là xác định nguyên nhân trễ hạn, đánh giá tư cách tín dụng hay thay thế đánh giá của con người.",
        "Lớp default ít hơn lớp không default. Vì vậy accuracy tại một ngưỡng cố định có thể che giấu việc bỏ sót nhiều default. Báo cáo luôn trình bày precision, recall, F1, AP, ROC-AUC, Brier và ma trận nhầm lẫn."
    ]),
    ("Dữ liệu và giấy phép", [
        "Bộ dữ liệu UCI gồm 30.000 bản ghi và 25 cột. Tệp thô chính thức được lưu cục bộ ngoài Git; data/raw/source_metadata.json lưu URL, ngày tải, giấy phép theo nguồn UCI và SHA-256. data/README.md ghi cách tải lại và data dictionary.",
        "Kiểm tra dữ liệu ghi nhận không có missing, không có ID trùng và không có bản ghi trùng. Mã EDUCATION 0, 5, 6 và MARRIAGE 0 xuất hiện nhưng không được tự gán nghĩa hoặc loại bỏ. Chúng được giữ thành nhóm riêng trong tiền xử lý và audit.",
        "Tên cột, giá trị và target theo ID của bản CSV Kaggle đã được đối chiếu với bản UCI đang dùng. Checksum tệp có thể khác vì định dạng CSV khác; ghi nhận nguồn tải Kaggle tách biệt, không suy đoán giấy phép của Kaggle."
    ]),
    ("Dữ liệu và biến", [
        "ID chỉ dùng để kiểm tra và cố định split, không dùng làm đặc trưng. Target là default_payment_next_month. Hai nhóm biến tiền xử lý gồm số liên tục LIMIT_BAL, AGE, BILL_AMT1..6, PAY_AMT1..6 và biến phân loại SEX, EDUCATION, MARRIAGE, PAY_0, PAY_2..PAY_6.",
        "PAY_0 đến PAY_6 là trạng thái lịch sử thanh toán trong các tháng gần nhất theo tài liệu UCI. Giá trị dương biểu thị số tháng chậm thanh toán; -1 là trả đúng hạn, -2 là không tiêu dùng, 0 là sử dụng quay vòng tín dụng. PAY_0 là tháng gần nhất trong chuỗi, không phải mã lỗi.",
        "Các số tiền giữ nguyên đơn vị của bộ dữ liệu. Giao diện không tự chuyển thành VNĐ. Chi tiết tên biến, miền hợp lệ và các mã chưa rõ nghĩa nằm trong data/README.md."
    ]),
    ("Thiết kế split và chống leakage", [
        "Dữ liệu được chia stratified train/validation/test theo tỷ lệ 60/20/20 với random_state=42. Manifest ID được lưu để mọi thí nghiệm sử dụng cùng split. EDA chỉ dùng train. Không oversample trước split; thực tế không dùng oversampling.",
        "Mọi bước học từ dữ liệu đặt trong sklearn Pipeline. Median imputation và StandardScaler của biến liên tục, most-frequent imputation và OneHotEncoder của biến phân loại đều fit trong train hoặc train-fold. CV Stratified 5-fold trên train cũng fit pipeline riêng ở mỗi fold.",
        "Validation dùng để chọn C, cách xử lý class weight, calibration và ngưỡng. Test bị cô lập đến sau freeze. Không dùng test để tạo demo, chỉnh tham số hoặc chọn ngưỡng."
    ]),
    ("Baseline và mô hình", [
        "Baseline thứ nhất luôn dự đoán không default. Baseline thứ hai là Logistic Regression không class_weight. Giai đoạn 2 so sánh cùng cấu trúc với class_weight=balanced và chọn C trong {0.01, 0.1, 1, 10} bằng cùng năm fold train.",
        "Cả hai biến thể chọn C=1.0. Trên validation tại ngưỡng 0.5, unweighted có accuracy 0.8207, recall 0.3459, AP 0.5372, Brier 0.1368; balanced có accuracy 0.7780, recall 0.5727, AP 0.5369, Brier 0.1832.",
        "Chênh lệch AP khoảng 0.0004 không là bằng chứng vượt trội rõ rệt. Unweighted được chọn vì chi phí validation tốt nhất thấp hơn nhẹ, Brier tốt hơn và không cần class weight; đây là một lựa chọn thực nghiệm có giới hạn, không phải kết luận tổng quát."
    ]),
    ("Bốn thí nghiệm bắt buộc", [
        "Thứ nhất, accuracy được so với AP và recall default. Accuracy cao ở ngưỡng 0.5 có thể xuất hiện khi mô hình dự đoán phần lớn là không default. Vì mục tiêu là không bỏ sót nhiều default trong kịch bản nhắc thanh toán, recall và precision cần được đọc cùng accuracy.",
        "Thứ hai, reliability diagram và Brier score đánh giá calibration của xác suất gốc. Không mặc định xác suất từ class_weight=balanced đã được hiệu chỉnh tốt. Calibration bổ sung không được chọn; xác suất gốc unweighted có Brier validation thấp hơn.",
        "Thứ ba, ngưỡng 0.5, ngưỡng lý thuyết theo chi phí 1/6≈0.1667 và ngưỡng validation-cost-minimum 0.150 được so sánh. Thứ tư, audit theo SEX, EDUCATION và MARRIAGE báo nhóm mẫu, default, TPR, FNR, FPR, precision, Brier và cảnh báo nhóm ít mẫu."
    ]),
    ("Ngưỡng và chi phí giả định", [
        "Kịch bản chính quy ước TN=0, TP=0, FP=1 và FN=5. Đây chỉ là kịch bản minh họa để học cách chọn ngưỡng, không phải chi phí thật của ngân hàng. Với xác suất được diễn giải như nguy cơ default, ngưỡng lý thuyết là 1/(1+5)=0.1667.",
        "Trên validation, unweighted tại 0.150 có TN=2938, FP=1735, FN=334, TP=993; chi phí 3405, tương đương 0.5675 mỗi khách hàng. Balanced đạt minimum 3430 tại 0.373. Vì vậy lựa chọn chính thức là unweighted, raw probability, threshold 0.150.",
        "Hạ ngưỡng tăng recall nhưng cũng tăng false positive và số cảnh báo nhầm. Dashboard chỉ cho thay thanh trượt trên đường cong validation đã tổng hợp; nó không dùng test để tìm lại ngưỡng."
    ]),
    ("Kết quả validation", [
        "Kết quả validation được giữ tách biệt với test. Ở ngưỡng đã chọn 0.150, accuracy của unweighted giảm còn 0.6552, precision 0.3640, recall 0.7483 và F1 0.4898. Mức accuracy thấp là hệ quả trực tiếp của ưu tiên giảm FN trong ma trận chi phí giả định, không phải lỗi tính toán.",
        "AP validation 0.5372 và ROC-AUC 0.7630 không phụ thuộc một ngưỡng cố định. Brier 0.1368 phản ánh sai số xác suất trung bình bình phương. PR-AUC được báo chính là average precision (average_precision_score); diện tích hình thang PR được lưu riêng để tránh đánh đồng hai cách tính.",
        "Validation được dùng để ra quyết định, sau đó toàn bộ pipeline, C, preprocessing, calibration, threshold, ma trận chi phí và phiên bản thư viện được ghi trong models/final_selection_freeze.json."
    ]),
    ("Đóng băng trước test", [
        "Freeze diễn ra trước khi đọc test. Tệp freeze ghi SHA-256 pipeline 804df95a7065bee41c11cbae479962e6b8bf912c6bfe252cae09a5fbb74b914a, C=1.0, raw probabilities, threshold 0.150, random_state=42 và phiên bản Python 3.12.14, scikit-learn 1.9.1, pandas 3.0.1, NumPy 2.5.3.",
        "Mã final_evaluation chặn ghi đè sau khi reports/final_test_evaluation.json đã tồn tại. Pipeline không refit sau khi chọn ngưỡng. Test chỉ được đánh giá một lần, ghi timestamp, hash split test, hash freeze và số lần evaluation.",
        "Cơ chế này giảm rủi ro tối ưu vô thức theo test. Nó không thay thế hoàn toàn một quy trình quản trị mô hình trong môi trường sản xuất."
    ]),
    ("Kết quả test cuối", [
        "Trên test đóng băng ở ngưỡng 0.150: accuracy 0.6452, precision default 0.3542, recall default 0.7340, F1 0.4778, AP 0.5254, ROC-AUC 0.7591 và Brier 0.1388. Ma trận nhầm lẫn gồm TN=2897, FP=1776, FN=353, TP=974.",
        "Chi phí giả định là 3541, tương đương 0.5902 mỗi khách hàng. Kết quả test thấp hơn hoặc khác validation là quan sát kỳ vọng về tổng quát hóa, không phải cơ sở để sửa mô hình hoặc ngưỡng. Không có tuning sau test.",
        "AP và ROC-AUC mô tả discrimination của xác suất. Brier và reliability diagram mô tả calibration. Chúng trả lời các câu hỏi khác nhau và không nên dùng thay thế nhau."
    ]),
    ("Phân tích lỗi và audit nhóm", [
        "Audit test theo SEX cho thấy nhóm mã 1 có 2402 mẫu, 561 default, recall 0.7861, FPR 0.4318, precision 0.3568 và Brier 0.1463; nhóm mã 2 có 3598 mẫu, 766 default, recall 0.6958, FPR 0.3464, precision 0.3520 và Brier 0.1338.",
        "Các nhóm EDUCATION 0, 4, 5, 6 và MARRIAGE 0, 3 có số mẫu ít hoặc số default rất ít. Một số metric như recall không xác định khi nhóm không có default; báo cáo lưu NaN và chú thích, không gán 0 một cách đánh lừa.",
        "Audit không chứng minh mô hình công bằng, cũng không thiết lập quan hệ nhân quả. Chênh lệch có thể xuất phát từ cỡ mẫu, phân phối dữ liệu, lịch sử đo lường và mô hình. Các mã chưa rõ nghĩa vẫn được giữ tách biệt."
    ]),
    ("Web và API", [
        "FastAPI nạp pipeline một lần khi khởi động, kiểm tra hash so với freeze và không train theo request. POST /api/risk-score nhận chính xác 23 đặc trưng, từ chối ID, target, trường thừa, thiếu trường, sai kiểu, mã bất hợp lệ và số không hữu hạn.",
        "API phân biệt giá trị không hợp lệ với giá trị hợp lệ nhưng ngoài miền train. Trường hợp sau được trả trong outside_training_range và cảnh báo, không bị thay thế âm thầm. API trả probability_default, threshold=0.150, alert, alert_group và model_version.",
        "Giao diện tiếng Việt gồm Giới thiệu, Mô phỏng, Dashboard và model card. Dữ liệu mô phỏng là synthetic có nhãn rõ; không dùng test làm demo. Dashboard hiển thị validation và test tách biệt."
    ]),
    ("Đạo đức và giới hạn", [
        "Dữ liệu là lịch sử quan sát tại Đài Loan, không đại diện cho mọi thời gian, quốc gia, sản phẩm hoặc dân số. Chất lượng nhãn, thiên lệch lịch sử và thay đổi hành vi theo thời gian có thể làm suy giảm hiệu lực.",
        "Hệ thống không cung cấp lời giải thích nhân quả hay lý do cá nhân cho điểm số. Nó không được dùng để tự động từ chối tín dụng, thay đổi lãi suất, hoặc áp dụng biện pháp bất lợi. Mọi cảnh báo cần được con người và quy trình phù hợp xem xét.",
        "Kịch bản chi phí chỉ là giả định. Ngưỡng cần được xem lại trong bối cảnh nghiệp vụ được phê duyệt, cùng giám sát drift, calibration, tác động nhóm và cơ chế khiếu nại trước bất kỳ sử dụng thực tế nào."
    ]),
    ("Kết luận", [
        "Dự án đạt một baseline tái lập, quy trình chọn mô hình validation-only, freeze trước test, đánh giá test một lần và ứng dụng API/web tách huấn luyện offline khỏi serving. Sản phẩm phù hợp để trình bày cách kiểm soát leakage và trade-off ngưỡng.",
        "Kết quả cho thấy ngưỡng 0.150 tăng khả năng phát hiện default nhưng tạo nhiều cảnh báo nhầm và hạ accuracy. Đây là trade-off được dự định trong chi phí giả định, không phải bằng chứng mô hình sẵn sàng đưa ra quyết định tín dụng.",
        "Bước tiếp theo cho mục tiêu học tập là tái lập từ máy sạch, kiểm tra tài liệu nguồn, và thực hành diễn giải kết quả cùng các giới hạn. Không làm lại tuning từ test."
    ]),
    ("Tài liệu tham khảo", [
        "Yeh, I. C. và Lien, C. H. (2009). The comparisons of data mining techniques for the predictive accuracy of probability of default of credit card clients. Expert Systems with Applications, 36(2), 2473-2480.",
        "UCI Machine Learning Repository. Default of Credit Card Clients. URL, ngày tải, checksum và thông tin giấy phép đã được lưu trong data/raw/source_metadata.json để tái lập cục bộ.",
        "Pedregosa et al. scikit-learn documentation: LogisticRegression, Pipeline, StratifiedKFold, calibration_curve, average_precision_score, roc_auc_score và brier_score_loss."
    ]),
    ("Phụ lục tái lập", [
        "Từ thư mục dự án, tạo .venv, cài requirements.txt, sau đó chạy python -m src.data prepare, python -m src.eda, python -m src.train, python -m src.evaluate và python -m src.experiments. Các bước này cần dữ liệu UCI theo data/README.md.",
        "Không chạy lại python -m src.final_evaluation evaluate trên bản bàn giao có reports/final_test_evaluation.json, vì mã sẽ từ chối ghi đè. Để tái lập ở đầu ra riêng, sao chép dự án hoặc dùng thư mục output độc lập, giữ nguyên hash pipeline và freeze. Xem deliverables/reproducibility.md.",
        "Khởi động web bằng uvicorn app.main:app --reload, sau đó mở http://127.0.0.1:8000. Kiểm thử API: python -m unittest tests.test_api. Tài liệu endpoint ở app/API.md."
    ]),
]

# Phụ lục chi tiết được tách trang có chủ đích để người đọc tra cứu từng nội dung.
PAGES.extend([
('Phụ lục A1. Bảng dữ liệu và target', ['Mỗi dòng là một khách hàng ẩn danh. ID chỉ là định danh kỹ thuật để kiểm tra trùng và cố định split; nó bị loại trước khi huấn luyện. Target default_payment_next_month bằng 1 khi có default tháng kế tiếp, bằng 0 khi không có default theo nhãn nguồn.', 'Các trường đầu vào gồm LIMIT_BAL, SEX, EDUCATION, MARRIAGE, AGE, PAY_0, PAY_2 đến PAY_6, BILL_AMT1 đến BILL_AMT6 và PAY_AMT1 đến PAY_AMT6. Không có thông tin khách hàng trực tiếp nhận diện trong pipeline.']),
('Phụ lục A2. Data dictionary nhóm nhân khẩu học', ['LIMIT_BAL là hạn mức tín dụng. AGE là tuổi. SEX, EDUCATION và MARRIAGE là mã phân loại nguồn; báo cáo hiển thị mã thay vì tự gán nhãn cho các mã không rõ nghĩa.', 'SEX: 1 và 2 theo tài liệu nguồn. EDUCATION có các mã phổ biến 1-4, đồng thời mã 0, 5, 6 được giữ riêng. MARRIAGE có các mã phổ biến 1-3, đồng thời mã 0 giữ riêng.']),
('Phụ lục A3. Data dictionary lịch sử PAY', ['PAY_0, PAY_2, PAY_3, PAY_4, PAY_5, PAY_6 biểu diễn tình trạng trả nợ của sáu tháng gần nhất. Chỉ số tháng trong tên biến giữ nguyên quy ước UCI.', 'Giá trị dương là số tháng chậm thanh toán; -1 là trả đúng hạn; -2 là không tiêu dùng; 0 là quay vòng tín dụng. Mã này được mô hình xử lý như biến phân loại để không áp đặt khoảng cách tuyến tính không có căn cứ.']),
('Phụ lục A4. Data dictionary số tiền', ['BILL_AMT1 đến BILL_AMT6 là số tiền sao kê trong sáu tháng; PAY_AMT1 đến PAY_AMT6 là số tiền thanh toán tương ứng. Đơn vị tiền tệ giữ nguyên như trong dữ liệu UCI.', 'Không quy đổi sang VNĐ trong báo cáo hoặc web. Số âm trong số dư có thể phản ánh điều chỉnh/tín dụng theo dữ liệu lịch sử nên không tự sửa.']),
('Phụ lục B1. Kiểm tra chất lượng dữ liệu', ['Dữ liệu có 30.000 dòng, 25 cột, không missing, không ID trùng và không bản ghi trùng theo kiểm tra đã lưu. Các mã ít gặp được báo cáo thay vì xóa hoặc gộp tùy ý.', 'Kiểm tra chất lượng là mô tả dữ liệu, không phải căn cứ để suy luận khách hàng. Các tệp kiểm tra chi tiết nằm trong reports và data/README.md.']),
('Phụ lục B2. Split cố định', ['Stratified split 60/20/20 tạo 18.000 train, 6.000 validation và 6.000 test với random_state=42. Tỷ lệ target được giữ gần nhau giữa các tập.', 'Manifest ID được lưu để chạy lại cùng phân hoạch. Không thay split để có kết quả đẹp hơn và test không xuất hiện trong EDA hay lựa chọn.']),
('Phụ lục C1. Pipeline tiền xử lý', ['Biến liên tục: SimpleImputer median và StandardScaler. Biến phân loại: SimpleImputer most_frequent và OneHotEncoder(handle_unknown=ignore). Các bước nằm trong ColumnTransformer của Pipeline.', 'Pipeline chỉ fit trên train trong huấn luyện; trong CV, mỗi fold fit pipeline bằng phần train của fold. Điều này ngăn thống kê validation đi vào scaler hoặc imputer.']),
('Phụ lục C2. Logistic Regression và C', ['Logistic Regression ước lượng xác suất bằng hàm sigmoid trên tổ hợp tuyến tính các đặc trưng đã xử lý. C kiểm soát mức regularization: C lớn hơn nghĩa là phạt yếu hơn.', 'C được xét bằng Stratified 5-fold CV trên train với cùng fold cho unweighted và balanced. Giá trị chọn cuối là C=1.0.']),
('Phụ lục C3. Metric phân loại', ['Accuracy là tỷ lệ dự đoán đúng. Precision default là TP/(TP+FP); recall default là TP/(TP+FN); F1 là trung bình điều hòa precision và recall.', 'Metric không xác định khi mẫu số bằng 0 được lưu là NaN và chú thích. Không ép thành 0 vì điều đó tạo cảm giác sai về hiệu năng nhóm ít mẫu.']),
('Phụ lục C4. AP và ROC AUC', ['Average precision tổng hợp precision-recall khi quét ngưỡng và đặc biệt hữu ích cho lớp dương ít. Báo cáo ghi rõ AP, không gọi nhầm là diện tích hình thang PR.', 'ROC-AUC đo khả năng xếp hạng giữa positive và negative. Nó không thể hiện trực tiếp số cảnh báo nhầm tại threshold triển khai.']),
('Phụ lục C5. Calibration và Brier', ['Reliability diagram so sánh xác suất dự báo và tần suất default quan sát trong các bin. Brier score là trung bình bình phương chênh lệch giữa xác suất và nhãn.', 'Calibration không đồng nghĩa discrimination. Mô hình balanced không được giả định calibrated; xác suất raw của unweighted được chọn theo validation.']),
('Phụ lục D1. Ma trận chi phí', ['Kịch bản minh họa đặt FN=5, FP=1, TP=0, TN=0. Tổng chi phí = 5 x FN + 1 x FP. Đó không phải chi phí ngân hàng hoặc chính sách vận hành thực tế.', 'Ngưỡng lý thuyết là 1/(1+5)=0.1667. Ngưỡng 0.150 được chọn do tối thiểu hóa chi phí trên validation, không phải trên test.']),
('Phụ lục D2. Diễn giải threshold 0.150', ['Ở threshold thấp, nhiều khách hàng được gắn cảnh báo hơn. Recall tăng nhưng precision thường giảm; một số khách hàng không default nhận nhắc nhở sai.', 'Vì vậy dashboard chỉ cho thay đổi threshold để học trade-off từ validation. Threshold chính thức của API vẫn là 0.150 đã freeze.']),
('Phụ lục E1. Audit nhóm', ['Audit theo SEX, EDUCATION, MARRIAGE báo số mẫu, số default, recall/TPR, FNR, FPR, precision và Brier. Đây là đánh giá mô tả kết quả, không phải kết luận nguyên nhân.', 'Nhóm có ít mẫu cần thận trọng vì tỷ lệ biến động mạnh. Không tuyên bố mô hình công bằng chỉ dựa một metric.']),
('Phụ lục F1. Hợp đồng API', ['POST /api/risk-score nhận 23 trường đặc trưng. ID và target bị từ chối. API kiểm tra thiếu trường, trường thừa, kiểu dữ liệu, giá trị không hữu hạn và mã không hợp lệ.', 'Nếu một giá trị hợp lệ nhưng nằm ngoài miền train, API trả outside_training_range để cảnh báo và không tự thay thế. Input không được lưu database, file hoặc log.']),
('Phụ lục F2. Kịch bản kiểm thử web', ['Màn Giới thiệu trình bày phạm vi; Mô phỏng giải thích dữ liệu và trả kết quả; Dashboard tách validation/test và minh họa ngưỡng validation. Form hiển thị lỗi cho dữ liệu sai.', 'Khi trình diễn, dùng ví dụ synthetic có nhãn rõ hoặc ví dụ từ train; không dùng bản ghi test. Kết quả là hỗ trợ nhắc thanh toán, không phải quyết định tín dụng.']),
('Phụ lục G. Lệnh tái lập', ['Tạo môi trường bằng python -m venv .venv, cài python -m pip install -r requirements.txt. Chuỗi chạy: src.data prepare, src.eda, src.train, src.evaluate, src.experiments.', 'Để chạy web: python -m src.build_web_data rồi uvicorn app.main:app --reload. Không chạy lại final_evaluation trong bản bàn giao vì test chính thức đã được đóng băng.'])
])


def setup_doc(doc: Document) -> None:
    sec = doc.sections[0]
    sec.top_margin = Cm(2.2); sec.bottom_margin = Cm(2.0)
    sec.left_margin = Cm(2.2); sec.right_margin = Cm(2.0)
    normal = doc.styles['Normal']; normal.font.name = 'Arial'; normal._element.rPr.rFonts.set(qn('w:eastAsia'), 'Arial'); normal.font.size = Pt(10.5)
    normal.paragraph_format.space_after = Pt(7); normal.paragraph_format.line_spacing = 1.22
    for name, size in [('Title', 22), ('Heading 1', 16), ('Heading 2', 12)]:
        style = doc.styles[name]; style.font.name = 'Arial'; style._element.rPr.rFonts.set(qn('w:eastAsia'), 'Arial'); style.font.size = Pt(size)
        style.font.color.rgb = None


def add_docx() -> Path:
    doc = Document(); setup_doc(doc)
    title = doc.add_paragraph(style='Title'); title.alignment = WD_ALIGN_PARAGRAPH.CENTER; title.add_run('BÁO CÁO BÀI TẬP LỚN')
    sub = doc.add_paragraph(); sub.alignment = WD_ALIGN_PARAGRAPH.CENTER; sub.add_run('Ước lượng nguy cơ trễ hạn thanh toán thẻ tín dụng').bold = True
    for label in ['TRƯỜNG / KHOA: [BỔ SUNG]', 'Môn học: [BỔ SUNG]', 'Giảng viên: [BỔ SUNG]', 'Thành viên: [BỔ SUNG]', 'Lớp: [BỔ SUNG]', 'Ngày bàn giao: 08/10/2026']:
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.add_run(label)
    doc.add_page_break()
    preliminary = [
        ('NHẬN XÉT CỦA GIẢNG VIÊN', ['Họ và tên giảng viên: [BỔ SUNG]', 'Nhận xét: [BỔ SUNG SAU KHI CHẤM]', 'Điểm: [BỔ SUNG]']),
        ('LỜI CAM ĐOAN', ['Nhóm nộp bài chịu trách nhiệm rà soát nội dung, số liệu và các thông tin cá nhân trước khi ký. Các vị trí [BỔ SUNG] được để trống vì chưa có bằng chứng hoặc thông tin do người học cung cấp.']),
        ('LỜI CẢM ƠN', ['[BỔ SUNG LỜI CẢM ƠN THEO THÔNG TIN THỰC TẾ CỦA NHÓM.]']),
        ('MỤC LỤC', ['Tóm tắt; Chương 1. Tổng quan; Chương 2. Dữ liệu và thiết kế; Chương 3. Phương pháp và thí nghiệm; Chương 4. Kết quả và phân tích; Chương 5. Ứng dụng, giới hạn và kết luận; Tài liệu tham khảo; Phụ lục tái lập. Khi nộp Word, chọn References > Update Table để cập nhật số trang nếu trường yêu cầu mục lục tự động.']),
        ('DANH MỤC THUẬT NGỮ', ['AP: average precision; ROC-AUC: diện tích dưới đường ROC; Brier: bình phương sai số xác suất; FP/FN/TP/TN: các ô trong ma trận nhầm lẫn; CV: cross-validation; leakage: rò rỉ thông tin.']),
        ('DANH MỤC HÌNH VÀ BẢNG', ['Hình: heatmap train-only; ma trận nhầm lẫn validation; đường PR/ROC; reliability diagram; audit nhóm. Bảng: dữ liệu và biến, split/chống leakage, so sánh validation, kịch bản chi phí và kết quả test.'])
    ]
    for heading, paras in preliminary:
        doc.add_heading(heading, level=1)
        for text in paras: doc.add_paragraph(text)
        doc.add_page_break()
    for idx, (heading, paras) in enumerate(PAGES, 1):
        chapter = 'CHƯƠNG 1. TỔNG QUAN' if idx == 2 else 'CHƯƠNG 2. DỮ LIỆU VÀ THIẾT KẾ' if idx == 3 else 'CHƯƠNG 3. PHƯƠNG PHÁP VÀ THÍ NGHIỆM' if idx in (4,5,6,7,8,9) else 'CHƯƠNG 4. KẾT QUẢ VÀ PHÂN TÍCH' if idx in (10,11,12,13) else 'CHƯƠNG 5. ỨNG DỤNG, GIỚI HẠN VÀ KẾT LUẬN' if idx in (14,15,16) else None
        if idx in (2, 3, 4, 10, 14):
            doc.add_paragraph(chapter, style='Heading 1')
        doc.add_heading(f'{idx}. {heading}', level=2)
        for text in paras: doc.add_paragraph(text)
        if idx == 8:
            doc.add_picture(str(FIG / 'validation_confusion_matrix_threshold_0.150.png'), width=Cm(13.8))
            doc.add_paragraph('Hình 1. Ma trận nhầm lẫn validation tại ngưỡng 0.150.').alignment = WD_ALIGN_PARAGRAPH.CENTER
        if idx == 4:
            doc.add_picture(str(FIG / 'train_continuous_feature_correlation.png'), width=Cm(13.8))
            doc.add_paragraph('Hình 1. Heatmap tương quan biến liên tục, chỉ tập train.').alignment = WD_ALIGN_PARAGRAPH.CENTER
        if idx == 11:
            doc.add_picture(str(FIG / 'final_test_pr_roc_curves.png'), width=Cm(14.3))
            doc.add_paragraph('Hình 2. Đường precision-recall và ROC trên test đóng băng.').alignment = WD_ALIGN_PARAGRAPH.CENTER
        if idx == 12:
            doc.add_picture(str(FIG / 'final_test_reliability_diagram.png'), width=Cm(12.5))
            doc.add_paragraph('Hình 3. Reliability diagram trên test đóng băng.').alignment = WD_ALIGN_PARAGRAPH.CENTER
        if idx == 13:
            doc.add_picture(str(FIG / 'final_test_group_audit_rates.png'), width=Cm(14.3))
            doc.add_paragraph('Hình 4. Recall/TPR và FPR theo nhóm trên test đóng băng.').alignment = WD_ALIGN_PARAGRAPH.CENTER
        if idx < len(PAGES): doc.add_page_break()
    OUT.mkdir(exist_ok=True)
    path = OUT / 'Project_08_bao_cao_ban_giao.docx'; doc.save(path); return path


def add_pdf() -> Path:
    OUT.mkdir(exist_ok=True); path = OUT / 'Project_08_bao_cao_ban_giao.pdf'
    font = Path('C:/Windows/Fonts/arial.ttf')
    pdfmetrics.registerFont(TTFont('ArialVN', str(font)))
    styles = getSampleStyleSheet(); body = ParagraphStyle('VN', parent=styles['BodyText'], fontName='ArialVN', fontSize=9.6, leading=14, spaceAfter=9)
    h1 = ParagraphStyle('H1VN', parent=styles['Heading1'], fontName='ArialVN', fontSize=16, leading=20, spaceAfter=14)
    title = ParagraphStyle('TitleVN', parent=styles['Title'], fontName='ArialVN', fontSize=22, leading=28, alignment=TA_CENTER)
    story = [Spacer(1, 5*cm), Paragraph('Báo cáo bàn giao Project 08', title), Spacer(1, .5*cm), Paragraph('Ước lượng nguy cơ trễ hạn thanh toán thẻ tín dụng', ParagraphStyle('sub', parent=body, alignment=TA_CENTER, fontSize=12)), Spacer(1, 1*cm), Paragraph('Môn học: [BỔ SUNG]<br/>Thành viên: [BỔ SUNG]<br/>Ngày bàn giao: 08/10/2026', ParagraphStyle('meta', parent=body, alignment=TA_CENTER)), PageBreak()]
    for heading, text in [
        ('NHẬN XÉT CỦA GIẢNG VIÊN', 'Họ tên, nhận xét và điểm: [BỔ SUNG SAU KHI CHẤM].'),
        ('LỜI CAM ĐOAN', 'Nhóm nộp bài chịu trách nhiệm rà soát nội dung, số liệu và thông tin cá nhân trước khi ký.'),
        ('LỜI CẢM ƠN', '[BỔ SUNG THEO THÔNG TIN THỰC TẾ CỦA NHÓM.]'),
        ('MỤC LỤC', 'Tóm tắt; Tổng quan; Dữ liệu và thiết kế; Phương pháp và thí nghiệm; Kết quả và phân tích; Ứng dụng, giới hạn và kết luận; Tài liệu tham khảo; Phụ lục tái lập.'),
        ('DANH MỤC THUẬT NGỮ, HÌNH VÀ BẢNG', 'AP, ROC-AUC, Brier, FP/FN/TP/TN, CV và leakage. Danh mục hình gồm heatmap train-only, confusion matrix, PR/ROC, calibration và audit nhóm.')
    ]:
        story += [Paragraph(heading, h1), Paragraph(text, body), PageBreak()]
    for idx, (heading, paras) in enumerate(PAGES, 1):
        story.append(Paragraph(f'{idx}. {heading}', h1))
        for text in paras: story.append(Paragraph(text, body))
        pic = None
        if idx == 4: pic = FIG / 'train_continuous_feature_correlation.png'
        if idx == 8: pic = FIG / 'validation_confusion_matrix_threshold_0.150.png'
        if idx == 11: pic = FIG / 'final_test_pr_roc_curves.png'
        if idx == 12: pic = FIG / 'final_test_reliability_diagram.png'
        if idx == 13: pic = FIG / 'final_test_group_audit_rates.png'
        if pic:
            story.extend([Spacer(1, 8), Image(str(pic), width=15.6*cm, height=8.8*cm), Spacer(1, 8)])
        if idx < len(PAGES): story.append(PageBreak())
    def footer(canvas, doc):
        canvas.saveState(); canvas.setFont('ArialVN', 8); canvas.setFillColor(colors.grey); canvas.drawCentredString(A4[0]/2, 1.1*cm, f'Project 08 | Trang {doc.page}'); canvas.restoreState()
    SimpleDocTemplate(str(path), pagesize=A4, rightMargin=2*cm, leftMargin=2.2*cm, topMargin=2*cm, bottomMargin=1.7*cm).build(story, onFirstPage=footer, onLaterPages=footer)
    return path


def write_text(path: Path, content: str) -> None:
    path.write_text(content.strip() + '\n', encoding='utf-8')


def add_handover_files() -> None:
    write_text(OUT / 'demo_script.md', '''# Kịch bản demo 5-7 phút\n\n## Mục tiêu\nTrình diễn quy trình dữ liệu đến cảnh báo, không trình bày hệ thống như công cụ quyết định tín dụng.\n\n## Kịch bản\n\n1. **0:00-0:45 - Bối cảnh.** Nêu target default tháng sau, nguồn UCI và mục tiêu hỗ trợ nhắc thanh toán.\n2. **0:45-1:45 - Chống leakage.** Chỉ ra split 60/20/20, random_state=42, EDA train-only, Pipeline fit trong train/fold và test bị khóa.\n3. **1:45-2:45 - Baseline và thí nghiệm.** So sánh accuracy với recall/AP, reliability, ngưỡng chi phí giả định và audit nhóm.\n4. **2:45-3:45 - Dashboard.** Mở Dashboard, chỉ rõ validation và test tách biệt. Kéo ngưỡng minh họa: chỉ số đang thay đổi là validation, không phải chọn lại bằng test.\n5. **3:45-5:15 - Mô phỏng.** Mở form, giải thích PAY_* và đơn vị tiền tệ. Nhập ví dụ synthetic, nhận xác suất, threshold 0.150 và cảnh báo. Cho một ví dụ ngoài miền train để thấy cảnh báo.\n6. **5:15-6:15 - API và an toàn.** Minh họa request hợp lệ, request có ID bị từ chối. Nêu pipeline chỉ nạp một lần và input không được lưu.\n7. **6:15-7:00 - Giới hạn.** Nhấn mạnh chi phí giả định, precision/recall trade-off, nhóm ít mẫu và không sử dụng cho quyết định cấp tín dụng.\n\n## Phân bổ buổi trình bày 12-15 phút\n\n- Bối cảnh, dữ liệu và leakage: 3 phút\n- Phương pháp, baseline và bốn thí nghiệm: 4 phút\n- Kết quả validation/test và giới hạn: 3 phút\n- Demo web/API: 5-7 phút\n- Tổng: 15 phút nếu demo 5 phút; có thể rút phần demo còn 2 phút để đạt 12 phút.\n''')
    write_text(OUT / 'reproducibility.md', '''# Tái lập an toàn\n\n## Môi trường mới\n\n```powershell\npython -m venv .venv\n.\\.venv\\Scripts\\Activate.ps1\npython -m pip install --upgrade pip\npython -m pip install -r requirements.txt\n```\n\nĐặt tệp UCI chính thức theo hướng dẫn trong `data/README.md`, rồi chạy `python -m src.data prepare`, `python -m src.eda`, `python -m src.train`, `python -m src.evaluate`, `python -m src.experiments`.\n\n## Bảo toàn đánh giá test chính thức\n\nBản bàn giao chứa `reports/final_test_evaluation.json` và `models/final_selection_freeze.json`. Không chạy lại `python -m src.final_evaluation evaluate` trong cùng thư mục vì mã chủ ý chặn ghi đè. Để thực hành đầy đủ, sao chép toàn bộ dự án sang thư mục mới hoặc clone vào thư mục riêng, sau đó tạo đầu ra mới ở bản sao. Không đổi threshold 0.150, pipeline hash hay cấu hình freeze nếu mục tiêu là đối chiếu kết quả đã báo cáo.\n\n## Web/API\n\n```powershell\npython -m src.build_web_data\nuvicorn app.main:app --reload\npython -m unittest tests.test_api\n```\n\nMở `http://127.0.0.1:8000`. Chỉ chạy các bước huấn luyện trên bản sao sạch có dữ liệu UCI hợp lệ.\n''')
    write_text(OUT / 'weekly_log_template.md', '''# Mẫu nhật ký 6 tuần\n\n> Không có tên, giờ làm hoặc lịch sử công việc được điền sẵn. Điền bằng chứng tương ứng trước khi nộp.\n\n| Tuần | Khoảng ngày | Mục tiêu | Việc đã làm | Bằng chứng/tệp/commit | Thời lượng | Vướng mắc | Người ghi |\n|---|---|---|---|---|---|---|---|\n| 1 |  |  |  |  |  |  |  |\n| 2 |  |  |  |  |  |  |  |\n| 3 |  |  |  |  |  |  |  |\n| 4 |  |  |  |  |  |  |  |\n| 5 |  |  |  |  |  |  |  |\n| 6 |  |  |  |  |  |  |  |\n\nCần bổ sung: tên hai thành viên, ngày thực tế, thời lượng, liên kết commit/tệp hoặc ghi chú họp có thật.\n''')
    write_text(OUT / 'team_contribution_template.md', '''# Bảng phân công hai thành viên\n\n| Hạng mục | Thành viên 1 | Thành viên 2 | Bằng chứng | Trạng thái |\n|---|---|---|---|---|\n| Dữ liệu, split, EDA | [BỔ SUNG] | [BỔ SUNG] |  |  |\n| Mô hình và thí nghiệm | [BỔ SUNG] | [BỔ SUNG] |  |  |\n| API/web | [BỔ SUNG] | [BỔ SUNG] |  |  |\n| Báo cáo/slide/demo | [BỔ SUNG] | [BỔ SUNG] |  |  |\n| Kiểm thử và bàn giao | [BỔ SUNG] | [BỔ SUNG] |  |  |\n\nChưa có bằng chứng để quy kết đóng góp cho bất kỳ ai. Điền tên, vai trò và dẫn chứng thực tế trước khi nộp.\n''')
    write_text(OUT / 'self_assessment_template.md', '''# Tự đánh giá\n\n| Tiêu chí | Tự đánh giá | Dẫn chứng | Việc cần bổ sung |\n|---|---|---|---|\n| Hiểu dữ liệu và leakage |  |  |  |\n| Thực hiện mô hình và đánh giá |  |  |  |\n| Giải thích ngưỡng/chi phí |  |  |  |\n| API/web và kiểm thử |  |  |  |\n| Làm việc nhóm |  |  |  |\n| Trình bày và trả lời vấn đáp |  |  |  |\n\nKhông có điểm, tên hoặc lịch sử được tự điền.\n''')
    write_text(OUT / 'oral_exam_qa.md', '''# Ôn vấn đáp\n\n## Leakage là gì?\nLeakage là khi mô hình hoặc quyết định nhận thông tin không thể có tại thời điểm dự đoán, ví dụ fit scaler trên toàn dữ liệu hoặc chọn ngưỡng theo test. Nó làm hiệu năng ước lượng quá lạc quan.\n\n## Vì sao không oversample trước split?\nBản sao/tổng hợp từ một quan sát có thể rơi vào cả train và validation/test, làm rò rỉ thông tin. Nếu dùng resampling, nó chỉ được thực hiện trong train/fold. Dự án này không dùng oversampling.\n\n## Calibration khác discrimination thế nào?\nDiscrimination đo thứ tự xếp hạng, thường xem AP/ROC-AUC. Calibration xem xác suất ước lượng có phù hợp tần suất thực không, xem reliability diagram/Brier. Mô hình có thể xếp hạng tốt nhưng xác suất chưa tốt.\n\n## AP và ROC-AUC khác nhau thế nào?\nAP tóm tắt precision-recall, nhạy với lớp dương hiếm và là average precision trong báo cáo. ROC-AUC so sánh TPR-FPR qua ngưỡng. Không nên coi hai chỉ số là cùng một đại lượng.\n\n## Vì sao ngưỡng 0.150?\nNó tối thiểu hóa chi phí validation theo kịch bản FP=1, FN=5 cho pipeline được chọn. Nó được khóa trước test. Kịch bản không phải chi phí ngân hàng thật.\n\n## class_weight=balanced làm gì?\nNó tăng trọng số đóng góp của lớp hiếm trong hàm mất mát. Nó có thể tăng recall tại 0.5, nhưng không tự làm xác suất calibrated hay bảo đảm tốt hơn theo chi phí.\n\n## Audit nhóm nói gì và không nói gì?\nAudit báo performance theo nhóm SEX, EDUCATION, MARRIAGE. Nó cảnh báo chênh lệch hoặc nhóm nhỏ, nhưng không chứng minh công bằng hay quan hệ nhân quả.\n\n## API dùng pipeline ra sao?\nAPI nạp joblib đã freeze một lần khi startup, kiểm tra hash, xác thực 23 đầu vào rồi gọi predict_proba. Nó không train hoặc lưu input trong request.\n''')
    write_text(OUT / 'rubric_evidence.md', '''# Đối chiếu rubric 100 điểm\n\n| Nhóm yêu cầu | Minh chứng hiện có | Tình trạng |\n|---|---|---|\n| Nguồn dữ liệu, schema, dictionary | data/README.md, src/data.py, reports/data_quality.json | Có |\n| Split cố định và chống leakage | data/processed/split_manifest.json, src/features.py, src/experiments.py, reports/pretest_freeze_review.md | Có |\n| EDA train-only | src/eda.py, reports/figures/train_target_distribution.png | Có |\n| Baseline và metric validation | src/train.py, src/evaluate.py, reports/validation_baseline_metrics.csv | Có |\n| CV, class_weight, calibration, ngưỡng, audit | src/experiments.py, reports/phase2_experiment_report.md, reports/phase2_validation_* | Có |\n| Freeze và test một lần | models/final_selection_freeze.json, src/final_evaluation.py, reports/final_test_evaluation.json | Có |\n| API và giao diện | app/main.py, app/static/, tests/test_api.py, app/API.md | Có, cần chạy trên máy nộp |\n| Báo cáo/slide/demo | deliverables/Project_08_bao_cao_ban_giao.*, deliverables/Project_08_trinh_bay.pptx, deliverables/demo_script.md | Có sau khi tạo |\n| Nhật ký, phân công, tự đánh giá | deliverables/*_template.md | Mẫu trống, cần người dùng điền bằng chứng |\n\n## Phần còn thiếu cần người nộp bổ sung\n\n- Tên thành viên, vai trò thực tế, nhật ký thời gian và bằng chứng làm việc.\n- Tên môn học, giảng viên/lớp và yêu cầu định dạng bìa nếu có.\n- Xác nhận kiểm tra giao diện trên laptop/điện thoại của máy nộp. Môi trường Codex hiện không cho trình duyệt kết nối localhost.\n- Điểm rubric cụ thể nếu đề gốc chia điểm khác bảng đối chiếu này. Không tự gán điểm 100/100.\n''')
    write_text(OUT / 'delivery_inventory.md', '''# Danh sách sản phẩm bàn giao\n\n- `Project_08_bao_cao_ban_giao.docx` và `.pdf`: báo cáo tiếng Việt.\n- `Project_08_trinh_bay.pptx`: 11 slide.\n- `demo_script.md`: kịch bản demo và phân bổ thời gian.\n- `reproducibility.md`: tái lập trong đầu ra riêng.\n- `weekly_log_template.md`, `team_contribution_template.md`, `self_assessment_template.md`: biểu mẫu không bịa dữ liệu cá nhân.\n- `oral_exam_qa.md`: câu hỏi và trả lời ôn vấn đáp.\n- `rubric_evidence.md`: đối chiếu yêu cầu và phần cần bổ sung.\n''')


if __name__ == '__main__':
    add_docx(); add_pdf(); add_handover_files()
    print('Phase 4 deliverables created')

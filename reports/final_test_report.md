# Đánh giá test cuối cùng

Pipeline đã đóng băng trước test: SHA-256 `804df95a7065bee41c11cbae479962e6b8bf912c6bfe252cae09a5fbb74b914a`. Module từ chối chạy lại hoặc ghi đè kết quả test.

## Kết quả test

| threshold | accuracy | precision_default | recall_default | f1_default | pr_auc_average_precision | pr_auc_trapezoidal | roc_auc | brier_score | tn | fp | fn | tp | total_assumed_cost | assumed_cost_per_customer |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.1500 | 0.6452 | 0.3542 | 0.7340 | 0.4778 | 0.5254 | 0.5247 | 0.7591 | 0.1388 | 2897 | 1776 | 353 | 974 | 3541 | 0.5902 |

AP là `average_precision_score`; PR-AUC hình thang báo riêng. Chi phí là kịch bản giả định FP=1, FN=5, TP=TN=0; không phải chi phí ngân hàng. Model, calibration và threshold không thay đổi theo test.

## Audit nhóm trên test

| group_column | group_value | sample_count | default_count | recall_tpr | fnr | fpr | precision | brier_score | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SEX | 1 | 2402 | 561 | 0.7861 | 0.2139 | 0.4318 | 0.3568 | 0.1463 |  |
| SEX | 2 | 3598 | 766 | 0.6958 | 0.3042 | 0.3464 | 0.3520 | 0.1338 |  |
| EDUCATION | 0 | 2 | 0 | undefined | undefined | 0.0000 | undefined | 0.0029 | Small group; interpret with caution. |
| EDUCATION | 1 | 2130 | 405 | 0.7111 | 0.2889 | 0.3252 | 0.3392 | 0.1230 |  |
| EDUCATION | 2 | 2774 | 656 | 0.7652 | 0.2348 | 0.4268 | 0.3570 | 0.1431 |  |
| EDUCATION | 3 | 1014 | 261 | 0.6973 | 0.3027 | 0.4024 | 0.3753 | 0.1667 |  |
| EDUCATION | 4 | 26 | 1 | 1.0000 | 0.0000 | 0.1200 | 0.2500 | 0.0220 | Small group; interpret with caution. |
| EDUCATION | 5 | 45 | 3 | 0.3333 | 0.6667 | 0.0476 | 0.3333 | 0.0642 | Small group; interpret with caution. |
| EDUCATION | 6 | 9 | 1 | 0.0000 | 1.0000 | 0.3750 | 0.0000 | 0.1272 | Small group; interpret with caution. |
| MARRIAGE | 0 | 7 | 0 | undefined | undefined | 0.1429 | 0.0000 | 0.0349 | Small group; interpret with caution. |
| MARRIAGE | 1 | 2767 | 668 | 0.7485 | 0.2515 | 0.4116 | 0.3666 | 0.1458 |  |
| MARRIAGE | 2 | 3158 | 647 | 0.7172 | 0.2828 | 0.3457 | 0.3483 | 0.1326 |  |
| MARRIAGE | 3 | 68 | 12 | 0.8333 | 0.1667 | 0.7679 | 0.1887 | 0.1520 | Small group; interpret with caution. |

Nhóm ít mẫu hoặc metric không xác định cần được diễn giải thận trọng; audit không chứng minh công bằng hay nhân quả.

---
title: Thiết kế pipeline an toàn
sidebar_position: 2
---

# 6.1 · Tích hợp bảo mật trong CI/CD

Pipeline an toàn cần bảo vệ code, runner, artifact và credential xuyên suốt quá trình build/deploy. Tự động hóa test không thay thế quản lý quyền và review.

## Quy tắc thiết kế

| Kiểm soát | Cách áp dụng trong bài |
|---|---|
| Least privilege | Tách job build, kiểm thử và deploy; cấp quyền deploy theo project |
| Secrets | Không lưu token/password trong repo; cấu hình bằng CI/CD masked variables |
| Security gates | Kiểm thử, source scan, dependency audit chạy trước build/deploy |
| Runner | Dùng runner riêng có cập nhật; hạn chế quyền mạng và không chạy mã fork với secrets |
| Audit | Lưu log job, JUnit report, artifact và hash để đối chiếu |
| Branch control | Chỉ nhánh mặc định được kích hoạt job Pages |

## Các phương pháp kiểm thử

- **SAST:** phân tích mã nguồn tĩnh để phát hiện pattern nguy hiểm.
- **DAST:** gửi request vào ứng dụng đang chạy; ZAP baseline là lựa chọn passive scan cho môi trường lab.
- **SCA:** đối chiếu dependency với advisory đã công bố (`npm audit`).
- **Secret scanning:** dò token/credential bị commit nhầm (`gitleaks`).
- **IaC/config scanning:** rà soát Terraform, Kubernetes hoặc Dockerfile trước triển khai.

Trong bài này, security checks và dependency audit được đưa vào pipeline thực tế. DAST/container scanning được mô tả như phần mở rộng có điều kiện vì site Docusaurus được build thành file tĩnh và runner mặc định có thể không hỗ trợ Docker-in-Docker. Không ghi nhận chúng là đã chạy nếu runner chưa cấu hình.

## Quản lý secret

1. Lưu credential trong GitLab **Settings → CI/CD → Variables**.
2. Bật `Masked` và `Protected` cho biến dùng trong deploy.
3. Chỉ cấp biến protected cho nhánh/tag được bảo vệ.
4. Luân chuyển token nếu phát hiện đã commit nhầm; xóa khỏi lịch sử không làm token cũ an toàn trở lại.

## Xử lý finding

Security job trả mã khác 0 sẽ chặn các stage tiếp theo. Developer xác minh finding, cập nhật dependency hoặc sửa mã, rồi chạy pipeline lại. Nếu có ngoại lệ, ghi phạm vi, lý do, người phê duyệt và ngày hết hạn; không tắt gate toàn cục để che finding.

## Giới hạn

Static rules và secret scanners có thể có false positive hoặc bỏ sót. Dependency audit chỉ đối chiếu package đã khai báo. DAST cần ứng dụng đang chạy và kiểm thử chỉ trong hệ thống được cấp phép. Mỗi finding cần review theo ngữ cảnh và threat model.

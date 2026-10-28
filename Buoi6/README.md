# BUỔI 6 — BẢO MẬT VỚI DEVSECOPS

**Sinh viên:** Nguyễn Phúc Thịnh<br>
**MSSV:** 2387700066<br>
**Môn học:** Thực hành Lập trình An toàn Thông tin<br>
**Đề bài:** `lab-06.pdf`

Website tài liệu và pipeline CI/CD thực hành về DevSecOps. Nội dung bám theo đề: security gates, pipeline cơ bản, Docusaurus build artifact và GitLab Pages.

## Mục tiêu và sản phẩm

- Website Docusaurus có hướng dẫn tiếng Việt, giao diện responsive và bài học điều hướng được.
- Pipeline GitLab theo thứ tự `test → security → build → deploy`.
- Ví dụ job đầu tiên và pipeline bốn job ở `examples/`.
- Unit tests, kiểm tra policy cấu hình, dependency audit, Semgrep SAST và Gitleaks secret scan.
- Build artifact tĩnh, kèm manifest SHA-256 để kiểm tra tính toàn vẹn.
- 20 ảnh chụp trực tiếp từ CMD, gắn với output thực tế của lệnh tương ứng.

Dependency audit đã được dùng để xử lý các advisory nghiêm trọng/cao ở dependency bắc cầu bằng override có phiên bản cụ thể. Gate hiện không còn finding High/Critical; npm vẫn báo 5 finding Low trong nhánh SVG optimizer. Báo cáo JSON được lưu trong `evidence/npm-audit.json` để theo dõi cập nhật upstream.

## Kiến trúc pipeline

```mermaid
flowchart LR
  A[Commit / Merge Request] --> B[Test]
  B --> C[Security gates]
  C --> D[Docusaurus build]
  D --> E[Artifact + SHA-256]
  E --> F{Nhánh mặc định?}
  F -->|Có| G[GitLab Pages]
  F -->|Không| H[Artifact để review]
```

Job bảo mật không đặt `allow_failure`; finding làm pipeline dừng trước build/deploy. Job Pages chỉ chạy trên nhánh mặc định. GitHub Actions cũng chạy test, security, audit và build khi có thay đổi trong Buoi6; workflow đó tạo kiểm tra repo, không thay thế GitLab Pages.

## Chạy cục bộ trên Windows

Yêu cầu Node.js 22 trở lên. Mở CMD/PowerShell tại `Buoi6`:

```powershell
npm ci
npm run verify
npm run serve
```

Website preview chạy tại `http://localhost:3000/THLTANTT_2387700066_NPT/`.

## Chạy GitLab CI từ repository môn học

Do cấu hình nằm tại `Buoi6/.gitlab-ci.yml` trong monorepo, nếu GitLab project dùng cả repository, đặt **Settings → CI/CD → General pipelines → CI/CD configuration file** thành `Buoi6/.gitlab-ci.yml`. Nếu project chỉ chứa source của Buoi6, đặt file này thành `.gitlab-ci.yml` ở root.

Runner cần hỗ trợ image Node.js và network tới npm registry. Bật GitLab Pages cho project để job `pages` publish artifact. Chưa khai báo secret hoặc deploy credential trong source. Các bước DAST/container scan cần ứng dụng chạy được và runner Docker riêng; chúng được mô tả trong tài liệu mở rộng, không giả định đã chạy trong pipeline này.

## Chạy lại các kiểm tra

Từ thư mục `Buoi6`:

```powershell
npm ci
npm run verify
.\scripts\capture-evidence.ps1
```

`npm run checksums` ghi manifest tại `reports/build-sha256.json`. Script ảnh gọi lệnh bằng CMD, lưu output và chụp màn hình desktop thực bằng `CopyFromScreen` vào `static/evidence/`.

## 20 ảnh minh chứng CMD

Ảnh được chụp khi các lệnh chạy trong CMD. Log text tương ứng nằm tại `evidence/logs/`; SHA-256 của 20 ảnh được lưu tại [`evidence/sha256.json`](evidence/sha256.json). Bấm ảnh để mở bản đầy đủ.

<details>
<summary>Mở bộ 20 ảnh minh chứng</summary>

| # | Minh chứng | # | Minh chứng |
|---:|---|---:|---|
| 01 | ![Node.js](static/evidence/01-cmd.png)<br>Phiên bản Node.js | 02 | ![npm](static/evidence/02-cmd.png)<br>Phiên bản npm |
| 03 | ![Git](static/evidence/03-cmd.png)<br>Phiên bản Git | 04 | ![Package](static/evidence/04-cmd.png)<br>Scripts và yêu cầu runtime |
| 05 | ![Pipeline đầu tiên](static/evidence/05-cmd.png)<br>Ví dụ job đầu tiên | 06 | ![Pipeline cơ bản](static/evidence/06-cmd.png)<br>Pipeline bốn job |
| 07 | ![Pipeline tests](static/evidence/07-cmd.png)<br>Kiểm tra cấu trúc pipeline | 08 | ![Content tests](static/evidence/08-cmd.png)<br>Kiểm tra tài liệu |
| 09 | ![Unit tests](static/evidence/09-cmd.png)<br>Toàn bộ unit tests | 10 | ![Security](static/evidence/10-cmd.png)<br>Security policy gate |
| 11 | ![YAML](static/evidence/11-cmd.png)<br>Parse YAML CI | 12 | ![Audit](static/evidence/12-cmd.png)<br>npm dependency audit |
| 13 | ![Build](static/evidence/13-cmd.png)<br>Docusaurus production build | 14 | ![Build files](static/evidence/14-cmd.png)<br>File website đã tạo |
| 15 | ![SHA256](static/evidence/15-cmd.png)<br>Manifest SHA-256 | 16 | ![HTTP](static/evidence/16-cmd.png)<br>HTTP preview cục bộ |
| 17 | ![Manifest](static/evidence/17-cmd.png)<br>Chi tiết manifest | 18 | ![Deploy rule](static/evidence/18-cmd.png)<br>Điều kiện deploy nhánh mặc định |
| 19 | ![Responsive](static/evidence/19-cmd.png)<br>Breakpoint responsive CSS | 20 | ![Git diff](static/evidence/20-cmd.png)<br>Whitespace và trạng thái Git |

</details>

## Phạm vi và giới hạn

- Ảnh CMD và log chứng minh lệnh đã chạy trên máy cá nhân; không chứng minh GitLab runner, GitLab Pages hoặc production đã chạy.
- npm audit cần truy cập registry/advisory database và có thể thất bại nếu dependency xuất hiện advisory mới. Không tắt gate để che finding.
- Semgrep/Gitleaks trên GitLab chạy bằng scanner image. Các static checks có thể false positive hoặc bỏ sót và cần review.
- DAST chỉ được thực hiện trên ứng dụng lab được cấp phép; ZAP baseline không thay thế pentest.
- MFA, protected branches, runner isolation và bảo vệ CI/CD variables phải được cấu hình trong tài khoản/project tương ứng.

## Tài liệu

- [Tổng quan bài thực hành](docs/intro.md)
- [Thiết kế pipeline an toàn](docs/secure-pipeline.md)
- [Thực hành GitLab CI/CD](docs/gitlab-cicd.md)
- [Pipeline nhiều giai đoạn](docs/complex-pipeline.md)
- [Kết quả và minh chứng](docs/results.md)
- [Tài liệu tham khảo](docs/references.md)

Tham khảo cách sắp xếp phần đối chiếu yêu cầu, pipeline, kết quả và minh chứng tại [BUOI6 của Mikmankkk](https://github.com/Mikmankkk/TH_LTANTT_2387700042/tree/main/BUOI6); nội dung, mã nguồn, giao diện và ảnh minh chứng ở đây được làm riêng cho Nguyễn Phúc Thịnh.

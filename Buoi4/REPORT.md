# Báo cáo Lab 04 — Bảo mật Web App và API

**Nguyễn Phúc Thịnh — MSSV 2387700066**
Ngày thực hành: 13/10/2026. Nguồn yêu cầu: `lab-04.pdf`, mục 4.2 WebVulnScanner và 4.4 JWTSecure. Mã mẫu trong PDF được đọc cả phần văn bản và các ảnh code; không chỉ dựa trên phần trích xuất văn bản.

## 1. Mục tiêu và kiến thức

Thực hành phát hiện các rủi ro XSS, SQL Injection, CSRF, SSRF; kiểm tra chữ ký/claim JWT, thử khóa yếu do lab tạo, xây dựng OAuth client và quản lý vòng đời token. Sản phẩm gồm mã nguồn, CLI, Web UI, test và bằng chứng chạy thực tế.

XSS phát sinh khi dữ liệu không tin cậy được trình duyệt hiểu như mã. Bài kiểm tra reflected XSS bằng payload có script và SVG; đối chứng dùng Jinja autoescape. Output encoding cần đúng ngữ cảnh; CSP là lớp bảo vệ bổ sung. [OWASP XSS Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html).

SQLi phát sinh khi ghép đầu vào vào cú pháp SQL. Fixture tạo DB SQLite trong bộ nhớ với hai hàng dữ liệu giả. True/false probe và lỗi SQL được so với baseline; bản khắc phục dùng bind parameter. [OWASP SQL Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html).

CSRF liên quan yêu cầu thay đổi trạng thái với quyền xác thực được trình duyệt tự gửi. Bài phân tích form và thực hiện POST không token để kiểm tra server; không đồng nhất việc không thấy token với khai thác cross-site hoàn chỉnh. SSRF liên quan server truy cập đích do đầu vào điều khiển; bài xác nhận qua marker của một dịch vụ nội bộ tự dựng.

JWT được mã hóa biểu diễn Base64URL, **không mặc nhiên mã hóa bí mật payload**. Chữ ký bảo vệ tính toàn vẹn, còn ứng dụng phải kiểm tra thuật toán, issuer, audience, thời gian và loại token. Gateway khóa HS256 trong cấu hình thay vì tin `alg` do token đưa ra. [RFC 8725](https://www.rfc-editor.org/rfc/rfc8725.html).

OAuth 2.0 phục vụ ủy quyền. Client của bài dùng Authorization Code với state và PKCE S256, hạn chế replay callback; không triển khai Implicit hoặc password grant. Đây là OAuth client và provider fixture, không phải hệ thống OIDC đầy đủ. [RFC 9700](https://www.rfc-editor.org/rfc/rfc9700.html).

## 2. Đối chiếu yêu cầu đề

| Yêu cầu | Hiện thực | Bằng chứng |
|---|---|---|
| Folder web-vuln-scanner với scanners/report/tests/ui/main | Đúng cấu trúc; thêm engine và policy HTTP | [Mã scanner](web-vuln-scanner/) |
| XSSScanner với payload chuẩn hóa | Hai payload, giữ query cũ, thử từng tham số và q | [Báo cáo XSS/CSRF](screenshots/09-web-xss-csrf.png) |
| SQLInjectionTester | Static indicator theo đề; bổ sung true/false/error probe | [SQLi](screenshots/10-web-sql-injection.png) |
| CSRFDetector | Phân tích từng form POST, token có giá trị; không kết luận từ trang không có form | [Test CSRF](web-vuln-scanner/tests/test_csrf.py) |
| SSRFTester | Phân tích host/IP chính xác, IPv6/link-local; proof HTTP nội bộ | [SSRF](screenshots/11-web-ssrf.png) |
| ReportGenerator | Flatten list/dict, bỏ kết quả CSRF đã protected, risk/desc/remediation/độ xác nhận | [JSON](evidence/scanner-report.json) |
| unittest, main.py, web UI | 25 test, CLI và form chọn scanner chạy thật | [CMD scanner](screenshots/02-cmd-scanner-unittest.png) |
| Folder jwt-security-tools theo đề | Đủ 5 module, tests, main, pytest.ini, requirements | [Mã JWT](jwt-security-tools/) |
| JWTValidator | Chữ ký, thuật toán, claim bắt buộc, thời gian, issuer/audience/type | [Test validator](jwt-security-tools/tests/test_validator.py) |
| JWTCracker | Offline HS256, wordlist có giới hạn; token lab tự tạo | [Test cracker](jwt-security-tools/tests/test_cracker.py) |
| OAuthClient | Authorization Code, state dùng một lần, PKCE S256, timeout | [Test OAuth](jwt-security-tools/tests/test_oauth_client.py) |
| TokenManager | Issue, rotate, revoke, SQLite hash, transaction chống race | [Test manager](jwt-security-tools/tests/test_token_manager.py) |
| APIGateway và curl trong CMD | /protected, /refresh, /revoke; bearer token; HTTP 200/401 | [CMD curl](screenshots/06-cmd-curl-auth-csrf.png) |
| Rate limiting / race / logging nêu phần mở đầu | 60 request/phút, atomic refresh, audit không chứa token | [Audit](evidence/gateway-audit.jsonl) |
| Lưu access/refresh token và loại dữ liệu nhạy cảm trước commit | Chỉ lưu runtime bị ignore; ảnh curl dùng config file | [.gitignore](.gitignore) |
| Ảnh thao tác như Buoi3 | 15 ảnh thật, 7 CMD, Chrome UI và desktop | [Manifest](evidence/screenshot-manifest.json) |

## 3. Những điểm điều chỉnh so với mã minh họa PDF

Mã mẫu trong đề kiểm tra SQLi/SSRF chủ yếu bằng chuỗi trong URL; bản thực hành giữ giao diện `scan(url)` và ghi rõ đó là indicator, đồng thời thêm HTTP probe. CSRF lấy HTML thực từ URL thay vì dùng một form cố định. XSS dùng query được urlencode đúng, không nối thêm dấu `?` sai khi URL đã có query. Lỗi mạng/redirect được ghi vào `errors`; report không đánh dấu complete khi có scanner lỗi.

Report loại bỏ kết quả CSRF protected thay vì hiển thị như một lỗ hổng. UI escape mọi dữ liệu scanner và dùng CSRF token/CSP. Các payload SQL phá hủy như `DROP TABLE` trong ví dụ không được gửi.

JWT dùng khóa ngẫu nhiên thay cho secret hard-coded trong PDF; kiểm tra claim bắt buộc, tách access/refresh và thêm refresh rotation/revocation. OAuth thêm state, PKCE và timeout. Cổng được tách để toàn bộ bài chạy đồng thời.

## 4. Kết quả quan sát

| Kịch bản | Kết quả |
|---|---|
| XSS /page | Hai payload phản chiếu; browser xác nhận alert có message `1` |
| XSS /safe | Không có alert; payload hiển thị dạng text escaped |
| SQLi /items | Baseline 1 hàng, true 2 hàng, false 0 hàng; quote tạo lỗi SQLite |
| SQLi /safe-items | 0 phát hiện với probe đã dùng |
| CSRF /change, POST không token | HTTP 200; fixture tăng bộ đếm lab |
| CSRF /safe-change, POST không token | HTTP 403 |
| CSRF form scanner UI | POST không token bị 403; report payload không được thực thi |
| SSRF /fetch | Phản hồi chứa LAB04-INTERNAL-PROOF-2387700066 |
| SSRF /safe-fetch | 0 phát hiện; internal URL bị chặn |
| JWT access hợp lệ | HTTP 200, user 2387700066 |
| JWT thiếu/sai chữ ký/hết hạn/refresh dùng thay access | HTTP 401 |
| Refresh lần đầu | HTTP 200, nhận cặp token mới |
| Refresh dùng lại / bị thu hồi | HTTP 401 |
| 8 request refresh đồng thời | Chính xác 1 thành công |
| OAuth code + state + PKCE | Nhận token; callback dùng lại bị từ chối |
| Crack token yếu tự tạo | Tìm đúng ứng viên trong wordlist lab |
| Rate limit (Flask test client) | Request thứ 3 bị 429 khi cấu hình limit=2 |
| URL ngoài phạm vi | Bị chặn trước khi gửi HTTP |

Tất cả kết quả HTTP trong [integration.json](evidence/integration.json) được lấy từ dịch vụ thực. Kết quả trình duyệt nằm trong [browser-checks.json](evidence/browser-checks.json). Rate limit được kiểm tra qua test client; không tuyên bố đó là phép đo tải production.

## 5. Kiểm thử và tính tái lập

**25 unittest scanner và 35 pytest JWT đạt**. Các test gồm URL policy/redirect, giữ query XSS, Content-Type, CSRF từng form, report flattening, claim JWT bất hợp lệ, alg=none, wrong scheme/type, refresh replay/race/persistence, audit không rò token, OAuth state/PKCE/replay và wordlist limit.

[validation.json](evidence/validation.json), [output unittest](evidence/scanner-unittest.txt), [output pytest](evidence/jwt-pytest.txt) và [JUnit XML](evidence/jwt-tests.xml) lưu kết quả chạy. Bandit quét mã ứng dụng/runner, bỏ thư mục test; suppression SQLi chủ đích và scheme Bearer được ghi tại dòng code. Hai warning PyJWT chỉ xuất hiện ở test dùng khóa yếu có chủ đích.

Chuỗi tái hiện: cài dependency → `run_lab.py serve` → `run_lab.py demo` → `tools/validate.py` → xem UI hoặc `tools/capture_all.py` để chạy và chụp toàn bộ. Chi tiết lệnh, cổng và ảnh nằm trong [README](README.md).

## 6. Phạm vi đánh giá

Bài xác minh reflected XSS, boolean/error SQLi trên SQLite, form CSRF, SSRF marker và Authorization Code + PKCE cục bộ. Chưa xác minh stored/DOM XSS, time-based/second-order SQLi, DBMS khác, blind/OOB SSRF, cloud thật, provider OAuth ngoài hoặc OIDC. Access token không bị thu hồi tức thì khi revoke refresh. Gateway, audit và rate limit phục vụ lab một máy. Khóa/token runtime không đưa vào repo.

Các giới hạn được nêu để bằng chứng khớp với thao tác đã chạy, không gán khả năng chưa triển khai cho sản phẩm.

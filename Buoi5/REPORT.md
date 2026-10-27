# Báo cáo Buổi 5 — SAST + DAST

**Sinh viên:** Nguyễn Phúc Thịnh · **MSSV:** 2387700066
**Đề bài:** `lab-05.pdf`, phần 5.1, 5.2, 5.3, 5.4.

## Phạm vi thực hiện

SAST dùng Python AST để phát hiện `eval`, `exec`, lệnh subprocess với `shell=True`, `os.system` và một mẫu SQL interpolation. Luật được cấu hình JSON, có bật/tắt, validation, quality metrics, CLI với exit status và SARIF 2.1.0. DAST gồm runtime event monitor, `tracemalloc`, network metadata giới hạn demo, rule cảnh báo, sandbox allow-list có timeout và API Flask loopback.

## Kết quả

- Mẫu SAST cố ý nguy hiểm: 3 phát hiện (`PY-SQL-FSTRING`, `PY-EVAL`, `PY-SHELL`). Mẫu an toàn: 0 phát hiện.
- SARIF parse thành công, version 2.1.0, chứa 3 results.
- Unit tests SAST: 8 PASS. Unit tests DAST: 6 PASS. Tổng: 14 PASS, 0 FAIL, 0 SKIP.
- HTTP thật tới `127.0.0.1:5055`: health 200; status 200; demo event 201; alerts có một warning; input limit sai 400.
- Sandbox snippet allow-list kết thúc return code 0 và temp directory được dọn.

## Ranh giới kỹ thuật

SAST là rule matching AST với phân tích biến SQL nội suy tối thiểu, không phải taint analysis. DAST chỉ instrument demo trong tiến trình, không hook hệ điều hành hoặc bắt payload mạng. Tracing memory không chứng minh leak/overflow. Sandbox dùng subprocess, working directory tạm và timeout nhưng cùng OS identity, nên không an toàn để chạy mã độc.

## Artifact

- SARIF: [`../evidence/report.sarif`](../evidence/report.sarif)
- HTTP smoke result: [`../evidence/api-smoke.json`](../evidence/api-smoke.json)
- Hướng dẫn, endpoint, test và ảnh: [`../README.md`](../README.md)

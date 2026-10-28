---
title: Pipeline nhiều giai đoạn
sidebar_position: 4
---

# Pipeline nhiều giai đoạn

Pipeline được tách thành bốn stage nhằm làm rõ thứ tự và failure boundary.

| Stage | Job | Kết quả |
|---|---|---|
| `test` | `unit-tests` | Node test report, chặn pipeline khi lỗi |
| `security` | `security-check`, `dependency-audit`, `semgrep`, `secret-scan` | Chặn khi scanner báo finding theo policy |
| `build` | `build-job` | Static site cùng manifest SHA-256 |
| `deploy` | `pages` | Publish artifact từ nhánh mặc định |

```mermaid
flowchart TD
  subgraph test
    T[Unit tests]
  end
  subgraph security
    S1[Security policy tests]
    S2[Dependency audit]
    S3[Semgrep SAST]
    S4[Gitleaks]
  end
  subgraph build
    B[Docusaurus production build]
    H[SHA-256 manifest]
  end
  subgraph deploy
    P[GitLab Pages]
  end
  T --> S1 & S2 & S3 & S4
  S1 & S2 & S3 & S4 --> B --> H --> P
```

Semgrep và Gitleaks chạy bằng image scanner riêng, không cài công cụ đó vào site dependencies. Pipeline GitHub bổ sung build/test như kiểm tra repo, nhưng không tự tuyên bố đã xuất bản GitLab Pages.

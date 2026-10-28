---
title: Kết quả và minh chứng
sidebar_position: 5
---

# Kết quả kiểm tra và ảnh minh chứng

## Kết quả kiểm tra

Các lệnh cục bộ và kết quả thực tế được lưu trong `evidence/`. DAST và GitLab Pages là các bước cần project/runner riêng; chỉ ghi trạng thái sau khi chúng thực sự chạy.

Dependency audit đã phát hiện advisory nghiêm trọng/cao trong các package bắc cầu ban đầu. Lockfile được cập nhật với các override đã ghim (`serialize-javascript`, `tinypool`, `uuid`); lần kiểm tra gần nhất không còn finding High/Critical, còn 5 finding Low trong chuỗi SVG optimizer. Script audit giữ ngưỡng chặn High trở lên và lưu JSON đầy đủ tại `evidence/npm-audit.json` để theo dõi các Low.

| Kiểm tra | Cách tái tạo |
|---|---|
| Unit tests | `npm test` |
| Security policy | `npm run security` |
| Dependency audit | `npm run audit` |
| Build static site | `npm run build` |
| Hash artifact | `npm run checksums` |

## 20 ảnh CMD

Ảnh là các lần chụp thật từ cửa sổ CMD Windows sau khi lệnh tương ứng chạy. Mỗi ảnh có log lệnh và thời điểm trong `evidence/`. Dùng `scripts/capture-evidence.ps1` để chụp lại sau khi chạy lại kiểm tra.

import EvidenceGallery from '@site/src/components/EvidenceGallery';

<EvidenceGallery />

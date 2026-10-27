# Buá»•i 5 â€” PhÃ¢n tÃ­ch vÃ  kiá»ƒm thá»­ báº£o máº­t (SAST + DAST)

**Sinh viÃªn:** Nguyá»…n PhÃºc Thá»‹nh Â· **MSSV:** 2387700066
**Äá» bÃ i:** `C:\Users\PThinkk\Downloads\lab-05.pdf`, má»¥c 5.1â€“5.4.

BÃ i nÃ y xÃ¢y dá»±ng bá»™ quÃ©t SAST Python dá»±a trÃªn AST, xuáº¥t SARIF 2.1.0; vÃ  má»™t ná»n táº£ng DAST demo quan sÃ¡t sá»± kiá»‡n trong tiáº¿n trÃ¬nh, bá»™ nhá»› Python, metadata máº¡ng, cáº£nh bÃ¡o theo rule, sandbox giá»›i háº¡n vÃ  Flask API chá»‰ trÃªn loopback.

## MÃ´i trÆ°á»ng vÃ  cÃ i Ä‘áº·t

ÄÃ£ thá»±c thi trÃªn Windows vá»›i Python 3.11.9, pip 24.0, Git 2.55.0.windows.5; Flask 3.1.3. CÃ¡c dependency cáº§n duy nháº¥t lÃ  Flask. Táº¡o venv táº¡i `Buoi5/.venv` (khÃ´ng Ä‘Æ°a vÃ o Git):

```powershell
cd Buoi5
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

## Cáº¥u trÃºc

```text
Buoi5/
â”œâ”€â”€ sast-tool/                 # AST analyzer, rule JSON, CLI, SARIF, tests vÃ  vÃ­ dá»¥
â”œâ”€â”€ dast-tool/                 # Runtime/memory/network, behavior, sandbox, Flask, tests
â”œâ”€â”€ screenshots/               # áº¢nh báº±ng chá»©ng render tá»« output lá»‡nh/API tháº­t Ä‘Ã£ lÆ°u
â”œâ”€â”€ evidence/                  # SARIF vÃ  káº¿t quáº£ HTTP thá»±c táº¿
â”œâ”€â”€ README.md
â””â”€â”€ REPORT.md
```

## SAST

Cháº¡y tá»« thÆ° má»¥c `Buoi5`:

```powershell
Push-Location sast-tool
..\.venv\Scripts\python.exe -X utf8 -m sast_tool.main examples\vulnerable_01.py --sarif ..\evidence\report.sarif --quality
..\.venv\Scripts\python.exe -X utf8 -m sast_tool.main examples\safe_example.py
Pop-Location
```

Rule engine Ä‘á»c schema JSON version 1 á»Ÿ `sast-tool/rules/default_rules.json`; má»—i rule cÃ³ thá»ƒ báº­t/táº¯t vÃ  khai bÃ¡o severity, mÃ´ táº£, tÃªn hÃ m. Analyzer khÃ´ng import hay cháº¡y file. Luáº­t demo phÃ¡t hiá»‡n `eval`, `exec`, `os.system`, subprocess cÃ³ `shell=True`, vÃ  truy váº¥n SQL truyá»n f-string/chuá»—i ná»™i suy vÃ o `execute`. Vá»›i SQL, há»— trá»£ gÃ¡n trá»±c tiáº¿p má»™t biáº¿n tá»« f-string/biá»ƒu thá»©c ná»‘i chuá»—i trÆ°á»›c khi gá»i execute; Ä‘Ã¢y khÃ´ng pháº£i phÃ¢n tÃ­ch dataflow tá»•ng quÃ¡t, khÃ´ng theo dÃµi alias/nhÃ¡nh/hÃ m. CÃ³ thá»ƒ cÃ³ false positive/negative.

Quality checker bÃ¡o complexity = 1 + sá»‘ node nhÃ¡nh (if, loop, conditional expression, handler, comprehension, match); chiá»u dÃ i tÃ­nh cáº£ dÃ²ng khai bÃ¡o Ä‘áº¿n cuá»‘i thÃ¢n hÃ m; nested depth lÃ  sá»‘ cáº¥u trÃºc Ä‘iá»u khiá»ƒn lá»“ng tá»‘i Ä‘a; dependency count Ä‘áº¿m tÃªn module import duy nháº¥t; smell density = findings Ã— 100 / sá»‘ dÃ²ng nguá»“n. ÄÃ¢y lÃ  heuristic Ä‘á»ƒ Ä‘á»‹nh hÆ°á»›ng review, khÃ´ng pháº£i Ä‘iá»ƒm báº£o máº­t chuáº©n hÃ³a.

Exit code CLI: 0 khÃ´ng phÃ¡t hiá»‡n, 1 cÃ³ phÃ¡t hiá»‡n, 2 lá»—i cáº¥u hÃ¬nh/I/O. SARIF náº±m á»Ÿ [`evidence/report.sarif`](evidence/report.sarif), JSON parse Ä‘Æ°á»£c, phiÃªn báº£n 2.1.0, cÃ³ rule, severity, message, file vÃ  line. Má»Ÿ báº±ng SARIF Viewer hoáº·c trÃ¬nh soáº¡n tháº£o JSON.

### Káº¿t quáº£ vÃ  áº£nh SAST

![MÃ´i trÆ°á»ng Python vÃ  PDF Ä‘á» bÃ i](screenshots/01-environment.png)

áº¢nh tá»•ng há»£p xÃ¡c nháº­n Python 3.11.9, pip, Git vÃ  PDF Ä‘á» bÃ i cÃ³ trÃªn mÃ¡y.

![Cáº¥u trÃºc thÆ° má»¥c dá»± Ã¡n](screenshots/02-project-structure.png)

Cáº¥u trÃºc thá»±c táº¿ gá»“m cÃ¡c package SAST vÃ  DAST, test, rule vÃ  vÃ­ dá»¥.

File cá»‘ Ã½ nguy hiá»ƒm Ä‘Æ°á»£c quÃ©t (khÃ´ng cháº¡y) cÃ³ 3 cáº£nh bÃ¡o: `PY-SQL-FSTRING`, `PY-EVAL`, `PY-SHELL`; file an toÃ n cÃ³ 0 phÃ¡t hiá»‡n.

![QuÃ©t máº«u cÃ³ eval, SQL ná»™i suy vÃ  shell=True](screenshots/03-sast-vulnerabilities.png)

áº¢nh nÃ y lÃ  bÃ¡o cÃ¡o áº£nh Ä‘Æ°á»£c render tá»« stdout lá»‡nh SAST Ä‘Ã£ cháº¡y; output gá»‘c Ä‘Æ°á»£c lÆ°u trong `evidence/sast-vulnerable.txt`.

![QuÃ©t file an toÃ n](screenshots/04-sast-safe.png)

Quan sÃ¡t káº¿t quáº£ 0 phÃ¡t hiá»‡n; output lá»‡nh gá»‘c trong `evidence/sast-safe.txt`.

![SARIF Ä‘Ã£ xuáº¥t vÃ  xÃ¡c minh](screenshots/05-sarif-verified.png)

SARIF Ä‘Ã£ Ä‘Æ°á»£c náº¡p láº¡i báº±ng JSON parser vÃ  xÃ¡c nháº­n 3 result; dá»¯ liá»‡u Ä‘áº§y Ä‘á»§ táº¡i `evidence/report.sarif`.

## DAST

Cháº¡y demo tá»•ng há»£p an toÃ n:

```powershell
Push-Location dast-tool
..\.venv\Scripts\python.exe -X utf8 main.py
Pop-Location
```

RuntimeMonitor ghi timestamp UTC vÃ  metadata cÃ³ giá»›i háº¡n bá»™ Ä‘á»‡m. MemoryAnalyzer Ä‘o traced Python allocations qua `tracemalloc`; tÄƒng bá»™ nhá»› chá»‰ lÃ  tÃ­n hiá»‡u nghi váº¥n, khÃ´ng chá»©ng minh leak vÃ  khÃ´ng thá»ƒ phÃ¡t hiá»‡n buffer overflow cáº¥p native. NetworkTrafficAnalyzer ghi metadata demo/loopback vÃ  khÃ´ng báº¯t payload hoáº·c sniff lÆ°u lÆ°á»£ng há»‡ thá»‘ng; khÃ´ng cáº§n quyá»n báº¯t gÃ³i. Behavior checker Ã¡p dá»¥ng rule trÃªn cÃ¡c sá»± kiá»‡n demo. VirtualSandbox chá»‰ cho cháº¡y ba snippet cá»‘ Ä‘á»‹nh, cÃ³ timeout, stdout giá»›i háº¡n, working directory táº¡m Ä‘Æ°á»£c dá»n; subprocess váº«n cháº¡y cÃ¹ng user/OS identity, khÃ´ng cÃ³ cÃ´ láº­p syscall, filesystem hay network nhÆ° container/VM.

Khá»Ÿi Ä‘á»™ng API:

```powershell
Push-Location dast-tool
..\.venv\Scripts\python.exe -X utf8 app.py
# Ctrl+C Ä‘á»ƒ dá»«ng
```

Máº·c Ä‘á»‹nh bind `127.0.0.1:5055`, debug táº¯t. Endpoint:

| Method | Path | Chá»©c nÄƒng |
|---|---|---|
| GET | `/api/health` | TÃ¬nh tráº¡ng service vÃ  monitor |
| GET | `/api/status` | Snapshot memory vÃ  metadata máº¡ng |
| GET | `/api/events?limit=100` | Sá»± kiá»‡n gáº§n nháº¥t; `limit` tá»« 1 Ä‘áº¿n 200 |
| GET | `/api/alerts` | Cáº£nh bÃ¡o theo rule |
| POST | `/api/demo/event` | ThÃªm sá»± kiá»‡n demo allow-list |

VÃ­ dá»¥ PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:5055/api/health
Invoke-RestMethod http://127.0.0.1:5055/api/status
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5055/api/demo/event `
  -ContentType 'application/json' -Body '{"type":"command.shell"}'
Invoke-RestMethod http://127.0.0.1:5055/api/alerts
```

Endpoint demo chá»‰ nháº­n `process.spawn`, `command.shell`, `demo.normal`, khÃ´ng thá»±c thi lá»‡nh. JSON sai hoáº·c giá»›i háº¡n sai nháº­n HTTP 400. á»¨ng dá»¥ng khÃ´ng cÃ³ API cháº¡y Python/shell hay Ä‘á»c/ghi file.

![Demo runtime vÃ  sandbox](screenshots/07-dast-runtime-demo.png)

Output demo thá»±c táº¿ gá»“m process event, cáº£nh bÃ¡o vÃ  sandbox káº¿t thÃºc thÃ nh cÃ´ng; JSON gá»‘c á»Ÿ `evidence/dast-demo.json`.

![Flask API loopback vÃ  endpoint thá»±c táº¿](screenshots/09-api-smoke.png)

Flask Ä‘Æ°á»£c khá»Ÿi Ä‘á»™ng thá»±c táº¿; health tráº£ 200/status ok, POST demo tráº£ 201, cáº£nh bÃ¡o Ä‘Æ°á»£c táº¡o, `limit=999` tráº£ 400. Output API Ä‘Ã£ lÆ°u táº¡i `evidence/api-smoke.json`.

## Kiá»ƒm thá»­

```powershell
Push-Location sast-tool
..\.venv\Scripts\python.exe -X utf8 -m unittest discover -s tests -v
Pop-Location
Push-Location dast-tool
..\.venv\Scripts\python.exe -X utf8 -m unittest discover -s tests -v
Pop-Location
```

Káº¿t quáº£ thá»±c táº¿: SAST **8/8 PASS**, DAST **6/6 PASS**, tá»•ng **14 PASS, 0 FAIL, 0 SKIP**. Test API dÃ¹ng Flask test client; kiá»ƒm tra endpoint qua server loopback riÃªng Ä‘Æ°á»£c thá»±c hiá»‡n bá»• sung báº±ng HTTP tháº­t. áº¢nh test Ä‘Æ°á»£c render tá»« output test Ä‘Ã£ cháº¡y vÃ  lÆ°u, khÃ´ng pháº£i áº£nh chá»¥p cá»­a sá»• desktop.

![Unit tests SAST: 8 passed](screenshots/06-sast-tests.png)

![Unit tests DAST: 6 passed](screenshots/10-dast-tests.png)

![Tá»•ng há»£p tÃ­ch há»£p: 14 passed, SARIF vÃ  API Ä‘Ã£ xÃ¡c minh](screenshots/11-integration-summary.png)

## SAST vÃ  DAST

SAST Ä‘á»c cáº¥u trÃºc mÃ£ nguá»“n mÃ  khÃ´ng cháº¡y chÆ°Æ¡ng trÃ¬nh, phÃ¹ há»£p phÃ¡t hiá»‡n sá»›m máº«u nguy hiá»ƒm. DAST quan sÃ¡t tráº¡ng thÃ¡i/hÃ nh vi á»©ng dá»¥ng Ä‘ang cháº¡y trong demo; nÃ³ chá»‰ tháº¥y cÃ¡c sá»± kiá»‡n Ä‘Ã£ instrument, khÃ´ng pháº£i monitor toÃ n há»‡ Ä‘iá»u hÃ nh. Hai cÃ¡ch kiá»ƒm thá»­ bá»• trá»£ nhau.

## Giá»›i háº¡n vÃ  lÆ°u Ã½

- ÄÃ¢y lÃ  cÃ´ng cá»¥ há»c táº­p, khÃ´ng thay tháº¿ Bandit, Semgrep, CodeQL, fuzzing hay kiá»ƒm thá»­ chuyÃªn sÃ¢u.
- AST rules khÃ´ng thá»±c hiá»‡n taint analysis hay phÃ¢n tÃ­ch liÃªn thá»§ tá»¥c.
- Theo dÃµi network chá»‰ láº¥y metadata Ä‘Ã£ khai bÃ¡o trong demo, khÃ´ng báº¯t gÃ³i.
- Sandbox subprocess khÃ´ng pháº£i biÃªn cÃ´ láº­p an toÃ n Ä‘á»ƒ cháº¡y pháº§n má»m Ä‘á»™c háº¡i; chá»‰ dÃ¹ng snippet allow-list cÃ³ trong mÃ£.
- Flask development server chá»‰ phá»¥c vá»¥ local lab, khÃ´ng triá»ƒn khai production.
- KhÃ´ng cháº¡y `examples/vulnerable_01.py`; chá»‰ Ä‘Æ°a file cho analyzer.

## Danh má»¥c áº£nh minh chá»©ng

áº¢nh PNG trong thÆ° má»¥c nÃ y lÃ  báº£n render tá»« stdout/output lá»‡nh hoáº·c HTTP response tháº­t Ä‘Ã£ lÆ°u kÃ¨m; Ä‘Ã¢y khÃ´ng pháº£i screenshot giao diá»‡n desktop. ÄÃ£ má»Ÿ kiá»ƒm tra tá»«ng PNG vÃ  Ä‘á»‘i chiáº¿u file output nguá»“n.

| áº¢nh | Ná»™i dung | Tráº¡ng thÃ¡i |
|---|---|---|
| `01-environment.png` | Python/dependency vÃ  PDF Ä‘á» bÃ i | VERIFIED |
| `02-project-structure.png` | Cáº¥u trÃºc package, test, rules | VERIFIED |
| `03-sast-vulnerabilities.png` | Ba rule SAST trÃªn máº«u khÃ´ng an toÃ n | VERIFIED |
| `04-sast-safe.png` | Máº«u an toÃ n, 0 findings | VERIFIED |
| `05-sarif-verified.png` | SARIF 2.1.0 vÃ  3 results | VERIFIED |
| `06-sast-tests.png` | 8 unit tests SAST | VERIFIED |
| `07-dast-runtime-demo.png` | Runtime event, alert, sandbox demo | VERIFIED |
| `09-api-smoke.png` | HTTP loopback, status/alert vÃ  validation | VERIFIED |
| `10-dast-tests.png` | 6 unit tests DAST | VERIFIED |
| `11-integration-summary.png` | Káº¿t quáº£ tá»•ng há»£p vÃ  sá»‘ tests | VERIFIED |

## Nháº­n xÃ©t vÃ  káº¿t luáº­n

ÄÃ£ triá»ƒn khai cÃ¡c thÃ nh pháº§n trá»ng tÃ¢m trong Ä‘á», xÃ¡c minh Ä‘Æ°á»£c phÃ¡t hiá»‡n SAST, káº¿t quáº£ SARIF, hÃ nh vi demo DAST vÃ  Flask API loopback. Má»i test Ä‘Ã£ cháº¡y Ä‘áº¡t. CÃ¡c giá»›i háº¡n phÃ¢n tÃ­ch luá»“ng dá»¯ liá»‡u, giÃ¡m sÃ¡t há»‡ thá»‘ng vÃ  cÃ´ láº­p sandbox Ä‘Æ°á»£c giá»¯ rÃµ trong bÃ¡o cÃ¡o Ä‘á»ƒ khÃ´ng nháº§m prototype há»c táº­p vá»›i cÃ´ng cá»¥ production.

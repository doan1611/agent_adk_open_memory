# Memory Agent — Lưu trữ & tìm kiếm issue (OpenMemory + Gauss + Google ADK)

Hệ thống giúp **ghi nhớ** và **tìm kiếm** thông tin issue (ví dụ defect PLM) bằng **OpenMemory**, xử lý ngôn ngữ tự nhiên qua **Gauss** tích hợp **Google ADK** (`google.adk.agents`). Gauss không hỗ trợ tool calling native; model phản hồi theo JSON `tool_calls` và được parse trong `models/gauss_model.py` + `tools/parser.py`.

## Yêu cầu

- Python 3.10+ (khuyến nghị 3.11)
- Tài khoản / endpoint **Gauss** hợp lệ
- **OpenMemory** cấu hình đúng (package `openmemory-py`); kho nhớ nên **persistent** nếu bạn chạy nhiều process (server + CLI)

## Cài đặt

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux / macOS

pip install -r requirements.txt
```

## Biến môi trường (Gauss)

| Biến | Mô tả |
|------|--------|
| `GAUSS_ENDPOINT_URL` | URL gốc API Gauss (bắt buộc) |
| `GAUSS_CLIENT_KEY` | Client key (bắt buộc) |
| `GAUSS_TOKEN` | Token (bắt buộc) |
| `GAUSS_USER_EMAIL` | Email user (tùy chọn, gửi kèm header) |
| `GAUSS_MODEL_ID` | ID model (tùy chọn, có default trong code) |

Thiếu một trong các biến bắt buộc sẽ lỗi khi khởi tạo `GaussModel`.

## Chạy ứng dụng

### Chế độ mặc định: HTTP + theo dõi thư mục `inbox`

```bash
python main.py
```

- **HTTP API** lắng nghe `0.0.0.0` cổng **8081** (máy khác trong LAN truy cập `http://<IP-máy-chủ>:8081`).
- **Watcher** quét thư mục `./inbox` mỗi **1800 giây (30 phút)**.

Tùy chỉnh:

```bash
python main.py --host 0.0.0.0 --port 9000 --poll-interval 1800
```

### Ingest một file JSON (CLI)

```bash
python main.py --ingest path/to/issue.json
```

Có thể chạy **song song** với `python main.py` ở terminal khác (không tranh cổng). Đảm bảo OpenMemory dùng chung một kho lưu trữ giữa các process.

### Tìm kiếm (CLI)

```bash
python main.py --search "Bluetooth ANR"
```

## HTTP API

| Phương thức | Đường dẫn | Mô tả |
|-------------|-----------|--------|
| `POST` | `/ingest` | Body JSON issue; bắt buộc có `defectCode` (string). Server ghi `inbox/<defectCode>.json` rồi chạy orchestrator → ingest. |
| `GET` | `/search?q=...` | Tìm kiếm; orchestrator → query agent → `search_memory`. |

**Ví dụ ingest:**

```bash
curl -X POST http://localhost:8081/ingest ^
  -H "Content-Type: application/json" ^
  -d "{\"defectCode\":\"P250217-03238\",\"title\":\"...\",\"contentSummary\":\"...\",\"category\":\"S/W\",\"cause\":\"...\",\"countermeasure\":\"...\"}"
```

**Ví dụ search:**

```bash
curl "http://localhost:8081/search?q=Bluetooth+ANR"
```

## Định dạng issue (JSON)

Tên file khuyến nghị: `<defectCode>.json` (ví dụ `P250217-03238.json`).

```json
{
  "defectCode": "P250217-03238",
  "title": "Tiêu đề issue",
  "contentSummary": "Tóm tắt ngắn",
  "category": "S/W",
  "cause": "Nguyên nhân",
  "countermeasure": "Biện pháp"
}
```

Tool `store_memory` đọc file `./inbox/<defectCode>.json`, gắn metadata (summary, tags, importance), đưa vào OpenMemory với tag `plm_case`, cập nhật `processed.json`, rồi **xóa** file trong `inbox` sau khi lưu thành công.

## Cấu trúc thư mục chính

```
agents/          # ingest_agent, query_agent, orchestrator, prompts, runner_util
models/          # gauss_model.py (BaseLlm + parse tool_calls)
server/          # aiohttp: /ingest, /search
tools/           # memory_tools (OpenMemory), parser.py, tool_call_handler.py
watcher/         # quét inbox định kỳ
inbox/           # file JSON chờ ingest
processed.json   # lịch sử file đã xử lý
main.py          # entry point
```

## Chạy chỉ HTTP server (tùy chọn)

```bash
python -m server.http_server
```

Mặc định cổng **8081** (xem `server/http_server.py`).

## Kiểm thử

Xem `TESTING.md` và các file `test_*.py` trong repo. Một số test cần Gauss / OpenMemory thật hoặc server đang chạy.

## Tham khảo thêm

- `reference/agent.py`, `reference/agent_gauss.py` — ví dụ multi-agent / Gauss
- `reference/HOW_TOOL_CALL_WORKS.md` — ý tưởng parse `tool_calls` từ text
- `project_plan.md` — kế hoạch triển khai chi tiết

## Ghi chú

- Log gọi Gauss có thể được ghi vào thư mục `logs/` (theo `gauss_model.py`).
- Nếu ingest qua API hoặc CLI, luôn cần **`defectCode`** hợp lệ để tạo đúng file trong `inbox` trước khi agent gọi `store_memory`.

# Project Plan: Hệ Thống Lưu Trữ Và Tìm Kiếm Issue

## Tổng Quan
Hệ thống cho phép lưu trữ và tìm kiếm thông tin về các issue đã xử lý, sử dụng OpenMemory để lưu trữ và Gauss model để xử lý thông tin.

## Thông Tin Về Issue
Issue sẽ là một file JSON với định dạng như sau:

**Tên file:** P250217-03238.json

**Nội dung:**
```json
{
  "defectCode": "P250217-03238",
  "title": "[REP][YB1] [A346N] BluetoothAgent(com.sec.android.app.bluetoothagent,35.15) / Application not responding[ACT][3rdAppAuto]",
  "contentSummary": "Not merge ISehBluetooth\r\n=> Can not use ISehBluetooth HIDL or AIDL, BluetoothAgent not work",
  "category": "S/W",
  "cause": "Not merge ISehBluetooth\r\n=> Can not use ISehBluetooth HIDL or AIDL, BluetoothAgent not work",
  "countermeasure": "Merge ISehBluetooth AIDL"
}
```

## Các Step Triển Khai

### Step 1: Thiết Lập Cấu Trúc Project
- Tạo thư mục project với cấu trúc:
  ```
  project/
  ├── agents/
  │   ├── __init__.py
  │   ├── ingest_agent.py
  │   ├── query_agent.py
  │   └── orchestrator.py
  ├── models/
  │   ├── __init__.py
  │   └── gauss_model.py
  ├── tools/
  │   ├── __init__.py
  │   ├── memory_tools.py
  │   └── parser.py
  ├── server/
  │   ├── __init__.py
  │   └── http_server.py
  ├── watcher/
  │   ├── __init__.py
  │   └── file_watcher.py
  ├── inbox/
  ├── main.py
  ├── processed.json
  └── requirements.txt
  ```
- Tạo file `requirements.txt` với các dependencies cần thiết
- Tạo file `__init__.py` cho các package
- Tạo file `processed.json` rỗng

### Step 2: Tích Hợp Gauss Model
- Copy file `gauss_model.py` vào thư mục `models/`
- Tạo file config để lưu trữ các thông số environment cho Gauss model
- Tạo test script đơn giản để kiểm tra kết nối với Gauss model

### Step 3: Xây Dựng Tool System
- Tạo file `memory_tools.py` trong thư mục `tools/`
- Triển khai các function:
  - `store_memory`: Lưu thông tin issue vào OpenMemory
  - `search_memory`: Tìm kiếm thông tin trong OpenMemory
- Tạo file `parser.py` để xử lý tool calls từ Gauss model

### Step 4: Xử Lý Tool Call Từ Gauss Model
- Tạo file `tool_call_handler.py` trong thư mục `tools/`
- Tạo file `prompts.py` trong thư mục `agents/` để chứa các prompt định dạng tool calling:
  - Định dạng JSON yêu cầu cho tool calls
  - Cung cấp các ví dụ cụ thể cho từng loại tool call
- Triển khai hàm `extract_tool_calls` để trích xuất tool calls từ phản hồi văn bản của Gauss bằng kỹ thuật đếm dấu ngoặc:
  - Tìm key "tool_calls" trong phản hồi
  - Sử dụng bracket counting để xác định vị trí bắt đầu và kết thúc của danh sách tool calls
  - Parse JSON và trích xuất các tool calls
- Triển khai hàm `handle_tool_calling` để xử lý tool calls:
  - Parse phản hồi từ Gauss model để tìm tool calls theo định dạng JSON
  - Chuyển đổi tool calls sang định dạng mà ADK có thể xử lý
  - Xử lý các công cụ được gọi và trả kết quả về cho Gauss model
- Tích hợp với hệ thống agent để đảm bảo các tool calls được xử lý đúng cách

### Step 5: Xây Dựng Agent System
- Tạo file `ingest_agent.py` trong thư mục `agents/`:
  - Xử lý thông tin issue từ file JSON
  - Gọi `store_memory` tool để lưu thông tin
- Tạo file `query_agent.py` trong thư mục `agents/`:
  - Xử lý yêu cầu tìm kiếm
  - Gọi `search_memory` tool để tìm thông tin
- Tạo file `orchestrator.py` trong thư mục `agents/`:
  - Điều phối các yêu cầu đến agent phù hợp

### Step 6: Triển Khai File Watcher
- Tạo file `file_watcher.py` trong thư mục `watcher/`
- Triển khai logic kiểm tra thư mục `./inbox` mỗi 30 phút
- Xử lý file JSON mới và gọi ingest agent
- Ghi thông tin vào `processed.json` và xóa file

### Step 7: Xây Dựng HTTP Server
- Tạo file `http_server.py` trong thư mục `server/`
- Triển khai API endpoints:
  - `POST /ingest`: Nhận thông tin issue mới từ client
  - `GET /search`: Tìm kiếm issue theo query
- Kết nối với agent system để xử lý các yêu cầu

### Step 8: Tạo Main Application
- Tạo file `main.py` để khởi động toàn bộ hệ thống
- Khởi tạo các thành phần:
  - Agent system
  - HTTP server
  - File watcher
- Bắt đầu các tiến trình đồng thời

### Step 9: Testing & Validation
- Tạo test data với vài file issue mẫu trong thư mục `./inbox`
- Kiểm tra file watcher có hoạt động đúng không
- Kiểm tra ingest agent có lưu thông tin vào OpenMemory không
- Kiểm tra query agent có tìm kiếm được thông tin không
- Kiểm tra HTTP API có phản hồi đúng không

### Step 10: Documentation
- Viết README.md hướng dẫn cách cài đặt và chạy hệ thống
- Document các API endpoints
- Hướng dẫn cách thêm issue mới và tìm kiếm
# memory_agent

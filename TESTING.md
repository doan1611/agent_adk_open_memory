# Hướng dẫn chạy các test cho hệ thống Issue Tracking

## 1. Chuẩn bị môi trường

Trước khi chạy test, cần đảm bảo đã cài đặt đầy đủ các dependencies:

```bash
# Tạo virtual environment
python3 -m venv venv

# Kích hoạt virtual environment
source venv/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt

# Cài đặt langchain
pip install langchain
```

## 2. Chạy tất cả các test cùng lúc

Để chạy tất cả các test trong một lần:

```bash
# Kích hoạt virtual environment
source venv/bin/activate

# Chạy tất cả test
python run_tests.py
```

Lệnh này sẽ chạy tuần tự các test:
- tool_call_handler.py
- memory_tools.py
- file_watcher.py
- HTTP server tests (bỏ qua, cần chạy thủ công)

## 3. Chạy từng test riêng lẻ

### 3.1. Test tool_call_handler

```bash
# Kích hoạt virtual environment
source venv/bin/activate

# Chạy test tool_call_handler
python test_tool_call_handler.py
```

Test này kiểm tra:
- Hàm `extract_tool_calls` với các trường hợp: tool call hợp lệ, nhiều tool calls, không có tool calls
- Hàm `handle_tool_calling` với các trường hợp: tool call hợp lệ, không có tool calls

### 3.2. Test memory_tools

```bash
# Kích hoạt virtual environment
source venv/bin/activate

# Chạy test memory_tools
python test_memory_tools.py
```

Test này kiểm tra:
- Hàm `store_memory`: Lưu thông tin issue vào OpenMemory
- Hàm `search_memory`: Tìm kiếm thông tin trong OpenMemory

### 3.3. Test file_watcher

```bash
# Kích hoạt virtual environment
source venv/bin/activate

# Chạy test file_watcher
python test_file_watcher.py
```

Test này kiểm tra:
- Chức năng theo dõi thư mục inbox
- Xử lý file issue khi có file mới
- Gọi Gauss model để xử lý và lưu thông tin vào OpenMemory

### 3.4. Test HTTP server

```bash
# Terminal 1: Khởi động server
source venv/bin/activate
python main.py

# Terminal 2: Chạy test HTTP server
source venv/bin/activate
python test_http_server.py
```

Test này kiểm tra:
- Endpoint `POST /ingest`: Thêm issue mới
- Endpoint `GET /search`: Tìm kiếm issue

## 4. Kiểm tra kết quả

### 4.1. File processed.json

Sau khi chạy test, kiểm tra file `processed.json` để xem danh sách các file đã được xử lý:

```bash
cat processed.json
```

### 4.2. File log

Kiểm tra thư mục `logs` để xem log của các lần gọi API đến Gauss model:

```bash
ls -la logs/
cat logs/gauss_api_call_*.json
```

## 5. Các file test mẫu

Hệ thống cung cấp các file test mẫu:
- `test_issue.json`: File issue mẫu để test
- `inbox/P250217-03238.json`: File issue thực tế để test

## 6. Môi trường và cấu hình

### 6.1. Biến môi trường

Cần thiết lập các biến môi trường cho Gauss model:
- `GAUSS_MODEL_ID`: ID của model Gauss
- `GAUSS_ENDPOINT_URL`: URL endpoint của Gauss API
- `GAUSS_CLIENT_KEY`: Client key để xác thực
- `GAUSS_TOKEN`: Token để xác thực

Ví dụ:
```bash
export GAUSS_MODEL_ID="0198f11e-ceab-71c3-8fb1-d077d6331843"
export GAUSS_ENDPOINT_URL="https://your-gauss-endpoint.com"
export GAUSS_CLIENT_KEY="your-client-key"
export GAUSS_TOKEN="your-token"
```

### 6.2. Cấu trúc thư mục

Hệ thống sử dụng các thư mục:
- `inbox/`: Thư mục chứa các file issue cần xử lý
- `logs/`: Thư mục chứa log của các lần gọi API
- `venv/`: Virtual environment (được tạo khi chạy test)

## 7. Xử lý lỗi

### 7.1. Lỗi import

Nếu gặp lỗi import, kiểm tra:
- Đã kích hoạt virtual environment chưa: `source venv/bin/activate`
- Đã cài đặt đủ dependencies chưa: `pip install -r requirements.txt`

### 7.2. Lỗi kết nối Gauss model

Nếu gặp lỗi kết nối đến Gauss model:
- Kiểm tra các biến môi trường đã được thiết lập đúng chưa
- Kiểm tra endpoint URL có đúng không
- Kiểm tra client key và token có hợp lệ không

### 7.3. Lỗi file processed.json

Nếu file `processed.json` không được cập nhật:
- Kiểm tra quyền ghi file
- Kiểm tra hàm `store_memory` có được gọi đúng cách không
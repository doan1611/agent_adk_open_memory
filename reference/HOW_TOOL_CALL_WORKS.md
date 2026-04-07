# Cách Hệ Thống Xử Lý Tool Call Phản Hồi Từ Gauss

## Tổng Quan

Dự án sử dụng một proxy server để chuyển đổi giữa OpenAI API format và Samsung Custom LLM API format, cho phép hệ thống sử dụng Gauss LLM với khả năng tool calling mặc dù API gốc của Gauss có thể không hỗ trợ trực tiếp function calling theo chuẩn OpenAI.

## Quy Trình Xử Lý Tool Call

### 1. Định Dạng Yêu Cầu Tool Call

LLM được hướng dẫn trả về tool calls theo định dạng JSON cụ thể trong prompt (`ai/prompts.py`):

```json
{
  "tool_calls": [
    {
      "name": "tool_name",
      "parameters": {
        "param1": "value1",
        "param2": "value2"
      }
    }
  ]
}
```

Định dạng này được mô tả chi tiết trong biến `FUNCTION_CALLING_INSTRUCTIONS` trong file `ai/prompts.py`:

```python
FUNCTION_CALLING_INSTRUCTIONS = """
<tool_calling_format>
When you need to use tools, you MUST respond with a JSON object containing a "tool_calls" array. This is the ONLY accepted format.

Required Format:
{{
  "tool_calls": [
    {{
      "name": "tool_name",
      "parameters": {{
        "param1": "value1",
        "param2": "value2"
      }}
    }}
  ]
}}

Available tools:
{tool_descriptions}

Examples:
- To read a section:
{{
  "tool_calls": [
    {{
      "name": "tool_read_section",
      "parameters": {{
        "target_section_index": "1",
        "grep_command": "grep -E com.example.android"
      }}
    }}
  ]
}}

- To read multiple sections:
{{
  "tool_calls": [
    {{
      "name": "tool_read_section",
      "parameters": {{
        "target_section_index": "1",
        "grep_command": "grep -E com.example.android"
      }}
    }},
    {{
      "name": "tool_read_section", 
      "parameters": {{
        "target_section_index": "2",
        "grep_command": "grep -E com.example.android"
      }}
    }}
  ]
}}

- To query database:
{{
  "tool_calls": [
    {{
      "name": "tool_query_db",
      "parameters": {{
        "query": "system error pattern"
      }}
    }}
  ]
}}

CRITICAL: 
- ONLY this JSON format is accepted
- Any other format will be automatically rejected
- DO NOT explain your tool calling plan verbally
- Your entire response must be ONLY the JSON object
</tool_calling_format>
"""
```

Các công cụ hiện có trong hệ thống:

1. **`tool_read_section`**: Đọc và lọc nội dung từ một section cụ thể trong dumpstate
   - `target_section_index`: Chỉ số của section cần đọc
   - `grep_command`: Lệnh grep tùy chọn để lọc nội dung

2. **`tool_read_event_logs`**: Đọc và lọc log sự kiện
   - `target_section_index`: Chỉ số của section log cần đọc
   - `filter_text`: Văn bản lọc tùy chọn
   - `start_time`: Thời gian bắt đầu lọc (định dạng MM-DD HH:MM:SS)
   - `end_time`: Thời gian kết thúc lọc (định dạng MM-DD HH:MM:SS)
   - `uid`: UID để lọc log
   - `pid`: PID để lọc log

3. **`tool_query_db`**: Truy vấn cơ sở kiến thức nội bộ của Samsung
   - `query`: Truy vấn tìm kiếm, có thể là từ khóa hoặc đoạn log cụ thể

Các công cụ này được định nghĩa trong file `ai/tools.py` với các tham số và mô tả chi tiết.

### 2. Phân Tích Phản Hồi Từ Gauss

Proxy sử dụng hàm `extract_tool_calls` trong `proxy/samsung_llm_proxy.py` để trích xuất tool calls từ phản hồi văn bản của LLM bằng kỹ thuật đếm dấu ngoặc:

```python
def extract_tool_calls(text):
    """
    Extract all tool_calls JSON from text using bracket counting approach
    This replaces regex-based parsing which struggles with nested brackets
    """
    all_calls = []
    search_start = 0
    
    while True:
        # 1. Find the next "tool_calls" key
        key_index = text.find('"tool_calls"', search_start)
        if key_index == -1:
            break # No more tool calls found
            
        # 2. Find the start of the list '['
        list_start = text.find('[', key_index)
        if list_start == -1:
            break

        # 3. Bracket Counting to find the end of this list
        balance = 0
        list_end = -1
        
        for i in range(list_start, len(text)):
            if text[i] == '[':
                balance += 1
            elif text[i] == ']':
                balance -= 1
            
            if balance == 0:
                list_end = i + 1
                break
        
        # 4. Extract and Parse
        if list_end != -1:
            json_str = text[list_start:list_end]
            try:
                # Parse the list (e.g., [call1, call2])
                repaired_json = repair_json(json_str)
                parsed_list = json.loads(repaired_json)
                
                # Add all items found in this list to our master list
                if isinstance(parsed_list, list):
                    all_calls.extend(parsed_list)
            except:
                pass # Skip malformed blocks
            
            # Update search position to continue after this block
            search_start = list_end
        else:
            # If brackets didn't close, skip past this key
            search_start = list_start + 1

    return all_calls if all_calls else None
```

### 3. Chuyển Đổi Sang Định Dạng OpenAI

Proxy sử dụng hàm `handle_function_calling` để chuyển đổi tool calls sang định dạng chuẩn của OpenAI:

```python
def handle_function_calling(openai_request, model_response):
    """Handle function calling by parsing JSON response and converting to function calls"""
    
    # Check if the request includes tools/functions
    if 'tools' not in openai_request:
        return model_response
    
    tools = openai_request.get('tools', [])
    if not tools:
        return model_response
    
    # Try to extract function calls from the model response
    response_text = model_response.get('content', '')
    
    # Extract response text from OpenAI format
    if 'choices' in model_response and model_response['choices']:
        message = model_response['choices'][0].get('message', {})
        response_text = message.get('content', '')
    
    # Enhanced JSON parsing to handle tool calls embedded in text
    tool_calls = []
    
    try:
        # Use the new bracket counting approach to extract tool_calls
        tool_calls_list = extract_tool_calls(response_text)
        
        if tool_calls_list and isinstance(tool_calls_list, list):
            for tool_call in tool_calls_list:
                    # Handle different tool call formats
                    if isinstance(tool_call, dict) and 'name' in tool_call and 'parameters' in tool_call:
                        func_name = tool_call['name']
                        parameters = tool_call['parameters']
                        
                        # Find matching tool
                        matching_tool = None
                        for tool in tools:
                            if tool.get('function', {}).get('name') == func_name:
                                matching_tool = tool
                                break
                        
                        if matching_tool:
                            tool_calls.append({
                                "id": f"call_{func_name}_{len(tool_calls)}",
                                "type": "function",
                                "function": {
                                    "name": func_name,
                                    "arguments": json.dumps(parameters)
                                }
                            })
                
    except Exception as e:
        log_debug(f"error while parsing LLM's output {e}")
    
    # If we found tool calls, convert the response to OpenAI format
    if tool_calls:
        # Remove duplicates by function name and arguments
        seen_calls = set()
        unique_tool_calls = []
        for tool_call in tool_calls:
            func_name = tool_call['function']['name']
            func_args = tool_call['function']['arguments']
            call_signature = f"{func_name}:{func_args}"
            
            if call_signature not in seen_calls:
                seen_calls.add(call_signature)
                unique_tool_calls.append(tool_call)
        
        tool_calls = unique_tool_calls

        # Extract any non-tool-call content to preserve it
        non_tool_content = response_text
        for tool_call in tool_calls:
            func_name = tool_call['function']['name']
            # Remove the tool call JSON from the content
            non_tool_content = re.sub(
                rf'\{{[^{{}}]*"name"\s*:\s*"{re.escape(func_name)}"[^{{}}]*\}}',
                '',
                non_tool_content,
                flags=re.DOTALL
            )
        
        # Clean up the remaining content
        non_tool_content = re.sub(r'\s+', ' ', non_tool_content).strip()
        if not non_tool_content or non_tool_content.lower() in ['none', 'null', '']:
            non_tool_content = None
        
        return {
            "id": model_response.get('id', 'chatcmpl-samsung'),
            "object": "chat.completion",
            "created": model_response.get('created', 0),
            "model": model_response.get('model', 'samsung-custom-llm'),
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": non_tool_content,
                    "tool_calls": tool_calls
                },
                "finish_reason": "tool_calls"
            }],
            "usage": model_response.get('usage', {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            })
        }
    
    return model_response
```

### 4. Tích Hợp Với LangChain

Định dạng OpenAI tương thích với LangChain agent, cho phép agent tự động thực hiện các công cụ. Kết quả công cụ được gửi lại cho LLM trong vòng lặp tiếp theo.

## Lợi Ích Của Cách Tiếp Cận Này

1. **Tương thích với các hệ thống hiện có**: Sử dụng định dạng OpenAI cho phép tích hợp dễ dàng với các thư viện như LangChain
2. **Linh hoạt**: Có thể sử dụng bất kỳ LLM nào thông qua proxy
3. **Bảo mật**: Proxy có thể xử lý các tác vụ như lọc nội dung, giới hạn truy cập
4. **Dễ bảo trì**: Logic xử lý tool calling được tập trung trong proxy

## Các Thành Phần Chính

1. **`ai/prompts.py`**: Chứa hướng dẫn định dạng tool calling cho LLM
2. **`proxy/samsung_llm_proxy.py`**: Proxy server xử lý chuyển đổi giữa các định dạng API
3. **`ai/gauss_llm.py`**: Implementation trực tiếp của Gauss LLM (không đi qua proxy)
4. **`ai/gauss_model.py`**: Implementation sử dụng proxy thông qua LangChain ChatOpenAI
5. **`ai/main.py`**: Workflow chính sử dụng LangGraph và các agent

## Kết Luận

Cách tiếp cận này cho phép hệ thống sử dụng Gauss LLM với khả năng tool calling mặc dù API gốc của Gauss có thể không hỗ trợ trực tiếp function calling theo chuẩn OpenAI. Proxy server đóng vai trò trung gian chuyển đổi giữa các định dạng, đảm bảo tương thích với các hệ thống hiện có như LangChain.
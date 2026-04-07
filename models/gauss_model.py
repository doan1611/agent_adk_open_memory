"""
Gauss Model Integration for ADK

This module provides a custom model class that integrates Gauss AI service
with the ADK framework following the BaseLlm interface.
"""

import os
import json
import logging
from typing import AsyncGenerator, List, Dict, Any, Optional
from aiohttp import ClientSession, ClientTimeout

# ADK imports
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types

from tools.parser import first_function_call_from_text, strip_json_code_fence

logger = logging.getLogger(__name__)

class GaussModel(BaseLlm):
    """
    Gauss Model integration for ADK framework.
    
    This class wraps the Gauss AI service API calls and provides
    an ADK-compatible model interface by implementing the BaseLlm interface.
    """
    
    def __init__(
        self,
        model_id: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        client_key: Optional[str] = None,
        token: Optional[str] = None,
        user_email: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Gauss model with configuration.
        
        Args:
            model_id: Gauss model ID (defaults to environment GAUSS_MODEL_ID)
            endpoint_url: Gauss API endpoint (defaults to environment GAUSS_ENDPOINT_URL)
            client_key: Client key for authentication (defaults to environment GAUSS_CLIENT_KEY)
            token: API token for authentication (defaults to environment GAUSS_TOKEN)
            user_email: User email for the request (defaults to environment GAUSS_USER_EMAIL)
            **kwargs: Additional arguments passed to BaseLlm
        """
        # Set model name for BaseLlm
        _model_id = model_id or os.getenv("GAUSS_MODEL_ID", "0198f11e-ceab-71c3-8fb1-d077d6331843")
        model_name = f"gauss/{_model_id}"
        super().__init__(model=model_name, **kwargs)
        
        # Configuration from parameters or environment variables (set after super().__init__())
        self._model_id = _model_id
        self._endpoint_url = endpoint_url or os.getenv("GAUSS_ENDPOINT_URL", "")
        self._client_key = client_key or os.getenv("GAUSS_CLIENT_KEY", "")
        self._token = token or os.getenv("GAUSS_TOKEN", "")
        self._user_email = user_email or os.getenv("GAUSS_USER_EMAIL", "")
        self._timeout = ClientTimeout(total=300)
        
        # Validate required configuration
        self._validate_configuration()
        
        logger.info(f"GaussModel initialized with model_id: {self._model_id}")
    
    def _validate_configuration(self) -> None:
        """Validate that all required configuration is present."""
        if not self._endpoint_url:
            raise ValueError("GAUSS_ENDPOINT_URL must be set (environment variable or parameter)")
        if not self._client_key:
            raise ValueError("GAUSS_CLIENT_KEY must be set (environment variable or parameter)")
        if not self._token:
            raise ValueError("GAUSS_TOKEN must be set (environment variable or parameter)")
    
    @classmethod
    def supported_models(cls) -> list[str]:
        """Returns a list of supported models in regex for LlmRegistry."""
        return [r"gauss/.*"]
    
    async def generate_content_async(
        self, 
        llm_request: LlmRequest, 
        stream: bool = False,
        system_instruction: str = ""
    ) -> AsyncGenerator[LlmResponse, None]:
        """
        Generate content using Gauss model với tool calling support.
        
        Args:
            llm_request: LlmRequest containing the request data
            stream: bool indicating whether to stream the response (not supported by Gauss)
            system_instruction: System instruction for the model
            
        Yields:
            LlmResponse with the model's response
            
        Raises:
            Exception: If API call fails
        """
        try:
            # Extract text content from the request
            messages = self._extract_messages_from_request(llm_request)
            
            # Extract system instruction
            system_prompt = system_instruction
            if not system_prompt:
                if hasattr(llm_request, 'system_instruction') and llm_request.system_instruction:
                    system_prompt = llm_request.system_instruction
                elif llm_request.config and hasattr(llm_request.config, 'system_instruction') and llm_request.config.system_instruction:
                    system_prompt = llm_request.config.system_instruction
            
            # Extract generation parameters
            generation_config = self._extract_generation_config(llm_request)
            
            # Call Gauss API
            response_text = await self._call_gauss_api(messages, system_prompt, generation_config)
            
            # Parse response để detect và xử lý tool calls
            response_content = self._parse_tool_calls_to_adk_format(response_text)
            
            llm_response = LlmResponse(
                content=response_content,
                partial=False,
                model_version=self.model,
                finish_reason=types.FinishReason.STOP
            )
            
            yield llm_response
            
        except Exception as e:
            logger.error(f"Error generating content with Gauss model: {e}")
            # Create error response
            error_response = LlmResponse(
                error_code=types.FinishReason.OTHER,
                error_message=str(e),
                finish_reason=types.FinishReason.OTHER
            )
            yield error_response
    
    def _extract_messages_from_request(self, llm_request: LlmRequest) -> List[str]:
        """
        Extract messages from LlmRequest.
        
        Args:
            llm_request: LlmRequest containing the content
            
        Returns:
            List of message strings
        """
        messages = []
        if llm_request.contents:
            for content in llm_request.contents:
                if content.parts:
                    for part in content.parts:
                        if hasattr(part, 'text') and part.text:
                            messages.append(part.text)
        return messages
    
    def _extract_generation_config(self, llm_request: LlmRequest) -> Dict[str, Any]:
        """
        Extract generation configuration from LlmRequest.
        
        Args:
            llm_request: LlmRequest containing configuration
            
        Returns:
            Dictionary with generation parameters
        """
        config = {
            "max_new_tokens": 2024,
            "return_full_text": False,
            "seed": None,
            "top_k": 14,
            "top_p": 0.94,
            "temperature": 0.4,
            "repetition_penalty": 1.04
        }
        
        if llm_request.config:
            config_dict = llm_request.config.model_dump(exclude_none=True)
            # Map ADK config parameters to Gauss parameters
            param_mapping = {
                "temperature": "temperature",
                "top_p": "top_p",
                "top_k": "top_k",
                "max_output_tokens": "max_new_tokens",
            }
            for adk_key, gauss_key in param_mapping.items():
                if adk_key in config_dict:
                    config[gauss_key] = config_dict[adk_key]
            
            # Handle repetition penalty
            if "presence_penalty" in config_dict:
                config["repetition_penalty"] = 1.0 + config_dict["presence_penalty"]
        
        return config
    
    async def _call_gauss_api(
        self,
        messages: List[str],
        system_prompt: str,
        generation_config: Dict[str, Any]
    ) -> str:
        """
        Make API call to Gauss service.
        
        Args:
            messages: List of message strings to send
            system_prompt: System prompt for the model
            generation_config: Generation configuration parameters
            
        Returns:
            Response text from Gauss model
            
        Raises:
            Exception: If API call fails
        """
        if not self._endpoint_url or not self._client_key or not self._token:
            raise ValueError("Gauss configuration is incomplete")
            
        url = f"{self._endpoint_url}/openapi/chat/v1/messages"
        
        headers = {
            "x-fabrix-client": self._client_key,
            "x-openapi-token": self._token,
            "x-generative-ai-user-email": self._user_email,
            "Content-Type": "application/json"
        }
        
        # Simplify payload format cho Gauss model
        payload = {
            "modelIds": [self._model_id],
            "contents": messages,
            "isStream": False,
            "llmConfig": generation_config
        }
        
        # Chỉ thêm systemPrompt nếu không empty
        if system_prompt and system_prompt.strip():
            payload["systemPrompt"] = system_prompt.strip()
        
        # Print raw data sent to LLM
        print(f"\n=== RAW DATA SENT TO LLM ===")
        print(f"Messages: {messages}")
        print(f"System Prompt: {system_prompt}")
        print(f"Generation Config: {generation_config}")
        print(f"Full Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        print(f"============================\n")
        
        # Log request
        from datetime import datetime
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "request": {
                "url": url,
                "headers": {k: v for k, v in headers.items() if k not in ["x-fabrix-client", "x-openapi-token", "x-generative-ai-user-email"]},
                "payload": payload
            }
        }
        
        try:
            async with ClientSession(timeout=self._timeout) as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        # Log response
                        log_data["response"] = result
                        self._log_api_call(log_data)
                        # Return raw response for parsing
                        return json.dumps(result)
                    else:
                        error_text = await response.text()
                        # Log error response
                        log_data["error_response"] = {
                            "status": response.status,
                            "error_text": error_text
                        }
                        self._log_api_call(log_data)
                        logger.error(f"Gauss API error {response.status}: {error_text}")
                        raise Exception(f"Gauss API returned status {response.status}: {error_text}")
        except Exception as e:
            # Log exception
            log_data["exception"] = str(e)
            self._log_api_call(log_data)
            logger.error(f"Gauss API exception: {e}")
            raise Exception(f"Gauss API call failed: {str(e)}")
    
    def _log_api_call(self, log_data: dict):
        """Log API call request and response to file."""
        try:
            from datetime import datetime
            import os
            
            # Create logs directory if not exists
            log_dir = "logs"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            # Write to file with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = f"{log_dir}/gauss_api_call_{timestamp}.json"
            
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"API call logged to: {log_file}")
        except Exception as e:
            logger.error(f"Failed to log API call: {e}")
    
    def _parse_tool_calls_to_adk_format(self, response_text: str) -> types.Content:
        """
        Parse response text và convert tool calls sang format ADK.
        """
        print(f"Parsing tool calls from response: {response_text}")

        def _part_from_call(name: str, parameters: dict) -> types.Content:
            function_call_part = types.Part.from_function_call(
                name=name,
                args=parameters,
            )
            print(f"Created function call part: {function_call_part}")
            return types.Content(role="model", parts=[function_call_part])

        try:
            # Parse response JSON từ API call
            response_data = json.loads(response_text)
            print(f"Parsed response data: {response_data}")

            # Extract content from response
            content_str = ""
            if isinstance(response_data, dict) and "content" in response_data:
                content_str = response_data.get("content", "")
                print(f"Extracted content string: {content_str}")

                if content_str:
                    fenced = strip_json_code_fence(content_str)
                    tc = first_function_call_from_text(fenced)
                    if tc:
                        return _part_from_call(tc["name"], tc["parameters"])

                    try:
                        content_data = json.loads(fenced)
                        print(f"Parsed content data: {content_data}")

                        if isinstance(content_data, dict):
                            if "name" in content_data and "parameters" in content_data:
                                return _part_from_call(
                                    content_data.get("name", ""),
                                    content_data.get("parameters", {}),
                                )

                            if "tool_calls" in content_data and isinstance(
                                content_data["tool_calls"], list
                            ):
                                tool_calls = content_data["tool_calls"]
                                if tool_calls:
                                    first_call = tool_calls[0]
                                    return _part_from_call(
                                        first_call.get("name", ""),
                                        first_call.get("parameters", {}),
                                    )

                    except json.JSONDecodeError as e:
                        print(f"Content is not JSON, treating as text: {e}")
                        tc2 = first_function_call_from_text(content_str)
                        if tc2:
                            return _part_from_call(tc2["name"], tc2["parameters"])
            
            # Nếu là function call format trực tiếp với name và arguments
            if isinstance(response_data, dict) and "name" in response_data and "arguments" in response_data:
                function_name = response_data.get("name", "")
                arguments = response_data.get("arguments", {})
                
                # Convert sang function call part mà ADK có thể execute
                function_call_part = types.Part.from_function_call(
                    name=function_name,
                    args=arguments
                )
                print(f"Created function call part: {function_call_part}")
                return types.Content(role="model", parts=[function_call_part])
                
            # Nếu là tool call format mới với agent_name và task
            elif isinstance(response_data, dict) and "agent_name" in response_data and "task" in response_data:
                agent_name = response_data.get("agent_name", "")
                task = response_data.get("task", "")
                data = response_data.get("data", {})
                
                if agent_name == "ingest_agent" and task == "store_information" and data:
                    # Convert sang store_memory function call với data thực tế
                    function_call_part = types.Part.from_function_call(
                        name="store_memory",
                        args={
                            "name_of_issue": data.get("defectCode", "unknown_issue"),
                            "summary": data.get("contentSummary", "")[:200],
                            "entities_tags": ["defect", "issue", data.get("category", "").lower()],
                            "importance": 0.8
                        }
                    )
                    print(f"Created function call part: {function_call_part}")
                    return types.Content(role="model", parts=[function_call_part])
                    
            # Nếu là nested tool call format với agent và request  
            elif isinstance(response_data, dict) and "agent" in response_data and "request" in response_data:
                # Extract actual tool call từ response
                request_data = response_data.get("request", {})
                if request_data and isinstance(request_data, dict):
                    # Extract issue name từ request text nếu có
                    issue_name = "unknown_issue"
                    summary = request_data.get("contentSummary", "")
                    
                    # Tạo function call part cho store_memory với arguments phù hợp
                    function_call_part = types.Part.from_function_call(
                        name="store_memory",
                        args={
                            "name_of_issue": issue_name,
                            "summary": summary[:200],  # Giới hạn độ dài summary
                            "entities_tags": ["defect", "issue"],
                            "importance": 0.8
                        }
                    )
                    print(f"Created function call part: {function_call_part}")
                    return types.Content(role="model", parts=[function_call_part])
                    
        except (json.JSONDecodeError, Exception) as e:
            logger.debug(f"Error parsing tool calls: {e}")
            print(f"Error parsing tool calls: {e}")

        tc_any = first_function_call_from_text(response_text)
        if tc_any:
            return _part_from_call(tc_any["name"], tc_any["parameters"])

        # Default: return như text response
        # If we have content_str from earlier, use that, otherwise use full response
        content_to_return = ""
        try:
            response_data = json.loads(response_text)
            if isinstance(response_data, dict) and "content" in response_data:
                content_to_return = response_data.get("content", response_text)
            else:
                content_to_return = response_text
        except:
            content_to_return = response_text
            
        print(f"Returning text response: {content_to_return}")
        return types.Content(
            role="model", 
            parts=[types.Part.from_text(text=content_to_return)]
        )

# Convenience function to create Gauss model
def create_gauss_model(**kwargs) -> GaussModel:
    """
    Create a Gauss model instance.
    
    Args:
        **kwargs: Arguments to pass to GaussModel constructor
        
    Returns:
        GaussModel instance
    """
    return GaussModel(**kwargs)
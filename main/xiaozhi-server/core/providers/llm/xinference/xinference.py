from config.logger import setup_logging
from openai import OpenAI
import json
from core.providers.llm.base import LLMProviderBase

TAG = __name__
logger = setup_logging()


class LLMProvider(LLMProviderBase):
    def __init__(self, config):
        self.model_name = config.get("model_name")
        self.base_url = config.get("base_url", "http://localhost:9997")
        # Initialize OpenAI client with Xinference base URL
        # 如果没有v1，增加v1
        if not self.base_url.endswith("/v1"):
            self.base_url = f"{self.base_url}/v1"

        logger.bind(tag=TAG).info(
            f"Initializing Xinference LLM provider with model: {self.model_name}, base_url: {self.base_url}"
        )

        try:
            self.client = OpenAI(
                base_url=self.base_url,
                api_key="xinference",  # Xinference has a similar setup to Ollama where it doesn't need an actual key
            )
            logger.bind(tag=TAG).info("Xinference client initialized successfully")
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error initializing Xinference client: {e}")
            raise

    def response(self, session_id, dialogue, **kwargs):
        try:
            logger.bind(tag=TAG).info(f"开始Xinference请求 - 模型: {self.model_name}, 会话ID: {session_id}")
            logger.bind(tag=TAG).debug(f"对话长度: {len(dialogue)}, 参数: {kwargs}")
            
            responses = self.client.chat.completions.create(
                model=self.model_name, messages=dialogue, stream=True
            )
            
            logger.bind(tag=TAG).info("Xinference流式响应开始")
            is_active = True
            chunk_count = 0
            
            for chunk in responses:
                chunk_count += 1
                try:
                    delta = (
                        chunk.choices[0].delta
                        if getattr(chunk, "choices", None)
                        else None
                    )
                    content = delta.content if hasattr(delta, "content") else ""
                    
                    if chunk_count % 10 == 0:  # 每10个chunk记录一次日志
                        logger.bind(tag=TAG).debug(f"Xinference已处理 {chunk_count} 个chunk, content长度: {len(content) if content else 0}")
                    
                    if content:
                        if "<think>" in content:
                            is_active = False
                            logger.bind(tag=TAG).debug("检测到<think>标签，暂停输出")
                            content = content.split("<think>")[0]
                        if "</think>" in content:
                            is_active = True
                            logger.bind(tag=TAG).debug("检测到</think>标签，恢复输出")
                            content = content.split("</think>")[-1]
                        if is_active:
                            yield content
                except Exception as e:
                    logger.bind(tag=TAG).error(f"处理Xinference chunk {chunk_count} 时出错: {e}")
                    logger.bind(tag=TAG).error(f"Chunk错误类型: {type(e).__name__}")

        except Exception as e:
            logger.bind(tag=TAG).error(f"Xinference响应生成错误: {e}")
            logger.bind(tag=TAG).error(f"错误类型: {type(e).__name__}")
            logger.bind(tag=TAG).error(f"错误详情: {str(e)}")
            logger.bind(tag=TAG).error(f"会话ID: {session_id}, 模型: {self.model_name}")
            try:
                error_msg = str(e)
                # 确保错误消息是UTF-8编码
                if isinstance(error_msg, bytes):
                    error_msg = error_msg.decode('utf-8', errors='replace')
                    logger.bind(tag=TAG).debug(f"错误消息已从bytes解码: {error_msg}")
                yield f"【Xinference服务响应异常: {error_msg}】"
            except (UnicodeEncodeError, UnicodeDecodeError) as encode_error:
                logger.bind(tag=TAG).error(f"编码错误: {encode_error}")
                # 如果编码失败，使用英文错误信息
                yield "【Xinference service response error】"

    def response_with_functions(self, session_id, dialogue, functions=None):
        try:
            logger.bind(tag=TAG).info(f"开始Xinference函数调用请求 - 模型: {self.model_name}, 会话ID: {session_id}")
            logger.bind(tag=TAG).debug(f"对话长度: {len(dialogue)}, 函数数量: {len(functions) if functions else 0}")
            if functions:
                function_names = [f.get('function', {}).get('name', 'unknown') for f in functions]
                logger.bind(tag=TAG).debug(f"可用函数: {function_names}")

            stream = self.client.chat.completions.create(
                model=self.model_name,
                messages=dialogue,
                stream=True,
                tools=functions,
            )
            
            logger.bind(tag=TAG).info("Xinference函数调用流式响应开始")
            chunk_count = 0

            for chunk in stream:
                chunk_count += 1
                try:
                    delta = chunk.choices[0].delta
                    content = delta.content
                    tool_calls = delta.tool_calls
                    
                    if chunk_count % 10 == 0:  # 每10个chunk记录一次日志
                        logger.bind(tag=TAG).debug(f"Xinference函数调用已处理 {chunk_count} 个chunk, content长度: {len(content) if content else 0}, tool_calls: {bool(tool_calls)}")

                    if content:
                        yield content, tool_calls
                    elif tool_calls:
                        yield None, tool_calls
                except Exception as chunk_error:
                    logger.bind(tag=TAG).error(f"处理Xinference函数调用chunk {chunk_count} 时出错: {chunk_error}")
                    logger.bind(tag=TAG).error(f"Chunk错误类型: {type(chunk_error).__name__}")
                    raise

        except Exception as e:
            logger.bind(tag=TAG).error(f"Xinference函数调用错误: {e}")
            logger.bind(tag=TAG).error(f"错误类型: {type(e).__name__}")
            logger.bind(tag=TAG).error(f"错误详情: {str(e)}")
            logger.bind(tag=TAG).error(f"会话ID: {session_id}, 模型: {self.model_name}")
            try:
                error_msg = str(e)
                # 确保错误消息是UTF-8编码
                if isinstance(error_msg, bytes):
                    error_msg = error_msg.decode('utf-8', errors='replace')
                    logger.bind(tag=TAG).debug(f"函数调用错误消息已从bytes解码: {error_msg}")
                yield f"【Xinference服务响应异常: {error_msg}】", None
            except (UnicodeEncodeError, UnicodeDecodeError) as encode_error:
                logger.bind(tag=TAG).error(f"函数调用编码错误: {encode_error}")
                # 如果编码失败，使用英文错误信息
                yield "【Xinference service response error】", None

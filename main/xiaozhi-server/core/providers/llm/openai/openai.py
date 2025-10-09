import httpx
import openai
from openai.types import CompletionUsage
from config.logger import setup_logging
from core.utils.util import check_model_key
from core.providers.llm.base import LLMProviderBase

TAG = __name__
logger = setup_logging()


class LLMProvider(LLMProviderBase):
    def __init__(self, config):
        self.model_name = config.get("model_name")
        self.api_key = config.get("api_key")
        if "base_url" in config:
            self.base_url = config.get("base_url")
        else:
            self.base_url = config.get("url")
        # 增加timeout的配置项，单位为秒
        timeout = config.get("timeout", 300)
        self.timeout = int(timeout) if timeout else 300

        param_defaults = {
            "max_tokens": (500, int),
            "temperature": (0.7, lambda x: round(float(x), 1)),
            "top_p": (1.0, lambda x: round(float(x), 1)),
            "frequency_penalty": (0, lambda x: round(float(x), 1)),
        }

        for param, (default, converter) in param_defaults.items():
            value = config.get(param)
            try:
                setattr(
                    self,
                    param,
                    converter(value) if value not in (None, "") else default,
                )
            except (ValueError, TypeError):
                setattr(self, param, default)

        logger.debug(
            f"意图识别参数初始化: {self.temperature}, {self.max_tokens}, {self.top_p}, {self.frequency_penalty}"
        )

        model_key_msg = check_model_key("LLM", self.api_key)
        if model_key_msg:
            logger.bind(tag=TAG).error(model_key_msg)
        self.client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=httpx.Timeout(self.timeout))

    def response(self, session_id, dialogue, **kwargs):
        logger.info(f'OpenAI LLMProvider.response called, session_id={session_id}, dialogue={dialogue}, kwargs={kwargs}')
        logger.info(f'[LLM调试] 当前OpenAI LLM地址: {self.base_url}')
        try:
            logger.bind(tag=TAG).info(f"开始OpenAI请求 - 模型: {self.model_name}, 会话ID: {session_id}")
            logger.bind(tag=TAG).debug(f"对话长度: {len(dialogue)}, 参数: {kwargs}")
            
            responses = self.client.chat.completions.create(
                model=self.model_name,
                messages=dialogue,
                user=session_id,  # 🔥 同样通过user参数传递设备ID
                stream=True,
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                temperature=kwargs.get("temperature", self.temperature),
                top_p=kwargs.get("top_p", self.top_p),
                frequency_penalty=kwargs.get(
                    "frequency_penalty", self.frequency_penalty
                ),
            )
            
            logger.bind(tag=TAG).info("OpenAI流式响应开始")

            is_active = True
            chunk_count = 0
            for chunk in responses:
                chunk_count += 1
                try:
                    # 检查是否存在有效的choice且content不为空
                    delta = (
                        chunk.choices[0].delta
                        if getattr(chunk, "choices", None)
                        else None
                    )
                    content = delta.content if hasattr(delta, "content") else ""
                    
                    if chunk_count % 10 == 0:  # 每10个chunk记录一次日志
                        logger.bind(tag=TAG).debug(f"已处理 {chunk_count} 个chunk, 当前content长度: {len(content) if content else 0}")
                        
                except IndexError:
                    content = ""
                    logger.bind(tag=TAG).warning(f"Chunk {chunk_count} 索引错误")
                    
                if content:
                    # 处理标签跨多个chunk的情况
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
            logger.bind(tag=TAG).error(f"OpenAI响应生成错误: {e}")
            logger.bind(tag=TAG).error(f"错误类型: {type(e).__name__}")
            logger.bind(tag=TAG).error(f"错误详情: {str(e)}")
            try:
                error_msg = str(e)
                # 确保错误消息是UTF-8编码
                if isinstance(error_msg, bytes):
                    error_msg = error_msg.decode('utf-8', errors='replace')
                    logger.bind(tag=TAG).debug(f"错误消息已从bytes解码: {error_msg}")
                yield f"【OpenAI服务响应异常: {error_msg}】"
            except (UnicodeEncodeError, UnicodeDecodeError) as encode_error:
                logger.bind(tag=TAG).error(f"编码错误: {encode_error}")
                # 如果编码失败，使用英文错误信息
                yield "【OpenAI service response error】"

    def response_with_functions(self, session_id, dialogue, functions=None):
        logger.info(f'OpenAI LLMProvider.response_with_functions called, session_id={session_id}, dialogue={dialogue}, functions={functions}')
        logger.info(f'[LLM调试] 当前OpenAI LLM地址: {self.base_url}')
        try:
            logger.bind(tag=TAG).info(f"开始OpenAI函数调用请求 - 模型: {self.model_name}, 会话ID: {session_id}")
            logger.bind(tag=TAG).debug(f"对话长度: {len(dialogue)}, 函数数量: {len(functions) if functions else 0}")
            if functions:
                function_names = [f.get('function', {}).get('name', 'unknown') for f in functions]
                logger.bind(tag=TAG).debug(f"可用函数: {function_names}")
            
            stream = self.client.chat.completions.create(
                model=self.model_name,
                messages=dialogue,
                user=session_id,  # 🔥 同样通过user参数传递设备ID
                stream=True,
                tools=functions
            )
            
            logger.bind(tag=TAG).info("OpenAI函数调用流式响应开始")

            chunk_count = 0
            for chunk in stream:
                chunk_count += 1
                try:
                    # 检查是否存在有效的choice且content不为空
                    if getattr(chunk, "choices", None):
                        content = chunk.choices[0].delta.content
                        tool_calls = chunk.choices[0].delta.tool_calls

                        # logger.info(f"[OpenAI监控] chunk: {content}")
                        # logger.info(f"[OpenAI监控] content: {content}, tool_calls: {tool_calls}")
                        
                        
                        # 检查content的编码
                        if content is not None:
                            logger.bind(tag=TAG).debug(f"Content类型: {type(content)}, 长度: {len(content)}")
                            if isinstance(content, str):
                                try:
                                    # 测试编码
                                    content.encode('ascii')
                                    logger.bind(tag=TAG).debug("Content可以ASCII编码")
                                except UnicodeEncodeError:
                                    logger.bind(tag=TAG).debug("Content包含非ASCII字符，需要UTF-8编码")
                        
                        if chunk_count % 10 == 0:  # 每10个chunk记录一次日志
                            logger.bind(tag=TAG).debug(f"函数调用已处理 {chunk_count} 个chunk, content长度: {len(content) if content else 0}, tool_calls: {bool(tool_calls)}")
                        
                        yield content, tool_calls
                    # 存在 CompletionUsage 消息时，生成 Token 消耗 log
                    elif isinstance(getattr(chunk, "usage", None), CompletionUsage):
                        usage_info = getattr(chunk, "usage", None)
                        logger.bind(tag=TAG).info(
                            f"Token 消耗：输入 {getattr(usage_info, 'prompt_tokens', '未知')}，"
                            f"输出 {getattr(usage_info, 'completion_tokens', '未知')}，"
                            f"共计 {getattr(usage_info, 'total_tokens', '未知')}"
                        )
                except Exception as chunk_error:
                    logger.bind(tag=TAG).error(f"处理chunk {chunk_count} 时出错: {chunk_error}")
                    logger.bind(tag=TAG).error(f"Chunk错误类型: {type(chunk_error).__name__}")
                    raise

        except Exception as e:
            logger.bind(tag=TAG).error(f"OpenAI函数调用流式响应错误: {e}")
            logger.bind(tag=TAG).error(f"错误类型: {type(e).__name__}")
            logger.bind(tag=TAG).error(f"错误详情: {str(e)}")
            logger.bind(tag=TAG).error(f"会话ID: {session_id}, 模型: {self.model_name}")
            try:
                error_msg = str(e)
                # 确保错误消息是UTF-8编码
                if isinstance(error_msg, bytes):
                    error_msg = error_msg.decode('utf-8', errors='replace')
                    logger.bind(tag=TAG).debug(f"函数调用错误消息已从bytes解码: {error_msg}")
                yield f"【OpenAI服务响应异常: {error_msg}】", None
            except (UnicodeEncodeError, UnicodeDecodeError) as encode_error:
                logger.bind(tag=TAG).error(f"函数调用编码错误: {encode_error}")
                # 如果编码失败，使用英文错误信息
                yield "【OpenAI service response error】", None

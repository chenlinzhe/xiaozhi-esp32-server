from config.logger import setup_logging
from openai import OpenAI
import json
from core.providers.llm.base import LLMProviderBase

TAG = __name__
logger = setup_logging()


class LLMProvider(LLMProviderBase):
    def __init__(self, config):
        self.model_name = config.get("model_name")
        self.base_url = config.get("base_url", "http://localhost:11434")
        # Initialize OpenAI client with Ollama base URL
        # 如果没有v1，增加v1
        if not self.base_url.endswith("/v1"):
            self.base_url = f"{self.base_url}/v1"

        self.client = OpenAI(
            base_url=self.base_url,
            api_key="ollama",  # Ollama doesn't need an API key but OpenAI client requires one
        )

        # 检查是否是qwen3模型
        self.is_qwen3 = self.model_name and self.model_name.lower().startswith("qwen3")

    def response(self, session_id, dialogue, **kwargs):
        try:
            # 如果是qwen3模型，在用户最后一条消息中添加/no_think指令
            if self.is_qwen3:
                # 复制对话列表，避免修改原始对话
                dialogue_copy = dialogue.copy()

                # 找到最后一条用户消息
                for i in range(len(dialogue_copy) - 1, -1, -1):
                    if dialogue_copy[i]["role"] == "user":
                        # 在用户消息前添加/no_think指令
                        dialogue_copy[i]["content"] = (
                            "/no_think " + dialogue_copy[i]["content"]
                        )
                        logger.bind(tag=TAG).debug(f"为qwen3模型添加/no_think指令")
                        break

                # 使用修改后的对话
                dialogue = dialogue_copy

            logger.bind(tag=TAG).info(f"开始Ollama请求 - 模型: {self.model_name}, 会话ID: {session_id}")
            logger.bind(tag=TAG).debug(f"对话长度: {len(dialogue)}")
            
            responses = self.client.chat.completions.create(
                model=self.model_name, messages=dialogue, stream=True
            )
            
            logger.bind(tag=TAG).info("Ollama流式响应开始")
            is_active = True
            # 用于处理跨chunk的标签
            buffer = ""

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
                        logger.bind(tag=TAG).debug(f"Ollama已处理 {chunk_count} 个chunk, 当前content长度: {len(content) if content else 0}, buffer长度: {len(buffer)}")

                    if content:
                        # 将内容添加到缓冲区
                        buffer += content

                        # 处理缓冲区中的标签
                        while "<think>" in buffer and "</think>" in buffer:
                            # 找到完整的<think></think>标签并移除
                            pre = buffer.split("<think>", 1)[0]
                            post = buffer.split("</think>", 1)[1]
                            buffer = pre + post
                            logger.bind(tag=TAG).debug("移除完整的<think></think>标签")

                        # 处理只有开始标签的情况
                        if "<think>" in buffer:
                            is_active = False
                            buffer = buffer.split("<think>", 1)[0]
                            logger.bind(tag=TAG).debug("检测到<think>标签，暂停输出")

                        # 处理只有结束标签的情况
                        if "</think>" in buffer:
                            is_active = True
                            buffer = buffer.split("</think>", 1)[1]
                            logger.bind(tag=TAG).debug("检测到</think>标签，恢复输出")

                        # 如果当前处于活动状态且缓冲区有内容，则输出
                        if is_active and buffer:
                            yield buffer
                            buffer = ""  # 清空缓冲区

                except Exception as e:
                    logger.bind(tag=TAG).error(f"Ollama处理chunk {chunk_count} 时出错: {e}")
                    logger.bind(tag=TAG).error(f"错误类型: {type(e).__name__}")

        except Exception as e:
            logger.bind(tag=TAG).error(f"Ollama响应生成错误: {e}")
            logger.bind(tag=TAG).error(f"错误类型: {type(e).__name__}")
            logger.bind(tag=TAG).error(f"错误详情: {str(e)}")
            logger.bind(tag=TAG).error(f"会话ID: {session_id}, 模型: {self.model_name}")
            try:
                error_msg = str(e)
                # 确保错误消息是UTF-8编码
                if isinstance(error_msg, bytes):
                    error_msg = error_msg.decode('utf-8', errors='replace')
                    logger.bind(tag=TAG).debug(f"错误消息已从bytes解码: {error_msg}")
                yield f"【Ollama服务响应异常: {error_msg}】"
            except (UnicodeEncodeError, UnicodeDecodeError) as encode_error:
                logger.bind(tag=TAG).error(f"编码错误: {encode_error}")
                # 如果编码失败，使用英文错误信息
                yield "【Ollama service response error】"

    def response_with_functions(self, session_id, dialogue, functions=None):
        try:
            # 如果是qwen3模型，在用户最后一条消息中添加/no_think指令
            if self.is_qwen3:
                # 复制对话列表，避免修改原始对话
                dialogue_copy = dialogue.copy()

                # 找到最后一条用户消息
                for i in range(len(dialogue_copy) - 1, -1, -1):
                    if dialogue_copy[i]["role"] == "user":
                        # 在用户消息前添加/no_think指令
                        dialogue_copy[i]["content"] = (
                            "/no_think " + dialogue_copy[i]["content"]
                        )
                        logger.bind(tag=TAG).debug(f"为qwen3模型添加/no_think指令")
                        break

                # 使用修改后的对话
                dialogue = dialogue_copy

            logger.bind(tag=TAG).info(f"开始Ollama函数调用请求 - 模型: {self.model_name}, 会话ID: {session_id}")
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
            
            logger.bind(tag=TAG).info("Ollama函数调用流式响应开始")
            is_active = True
            buffer = ""
            chunk_count = 0

            for chunk in stream:
                chunk_count += 1
                try:
                    delta = (
                        chunk.choices[0].delta
                        if getattr(chunk, "choices", None)
                        else None
                    )
                    content = delta.content if hasattr(delta, "content") else None
                    tool_calls = (
                        delta.tool_calls if hasattr(delta, "tool_calls") else None
                    )

                    if chunk_count % 10 == 0:  # 每10个chunk记录一次日志
                        logger.bind(tag=TAG).debug(f"Ollama函数调用已处理 {chunk_count} 个chunk, content长度: {len(content) if content else 0}, tool_calls: {bool(tool_calls)}, buffer长度: {len(buffer)}")

                    # 如果是工具调用，直接传递
                    if tool_calls:
                        logger.bind(tag=TAG).debug("检测到工具调用")
                        yield None, tool_calls
                        continue

                    # 处理文本内容
                    if content:
                        # 将内容添加到缓冲区
                        buffer += content

                        # 处理缓冲区中的标签
                        while "<think>" in buffer and "</think>" in buffer:
                            # 找到完整的<think></think>标签并移除
                            pre = buffer.split("<think>", 1)[0]
                            post = buffer.split("</think>", 1)[1]
                            buffer = pre + post
                            logger.bind(tag=TAG).debug("移除完整的<think></think>标签")

                        # 处理只有开始标签的情况
                        if "<think>" in buffer:
                            is_active = False
                            buffer = buffer.split("<think>", 1)[0]
                            logger.bind(tag=TAG).debug("检测到<think>标签，暂停输出")

                        # 处理只有结束标签的情况
                        if "</think>" in buffer:
                            is_active = True
                            buffer = buffer.split("</think>", 1)[1]
                            logger.bind(tag=TAG).debug("检测到</think>标签，恢复输出")

                        # 如果当前处于活动状态且缓冲区有内容，则输出
                        if is_active and buffer:
                            yield buffer, None
                            buffer = ""  # 清空缓冲区
                except Exception as e:
                    logger.bind(tag=TAG).error(f"处理Ollama函数调用chunk {chunk_count} 时出错: {e}")
                    logger.bind(tag=TAG).error(f"Chunk错误类型: {type(e).__name__}")
                    continue

        except Exception as e:
            logger.bind(tag=TAG).error(f"Ollama函数调用错误: {e}")
            logger.bind(tag=TAG).error(f"错误类型: {type(e).__name__}")
            logger.bind(tag=TAG).error(f"错误详情: {str(e)}")
            logger.bind(tag=TAG).error(f"会话ID: {session_id}, 模型: {self.model_name}")
            try:
                error_msg = str(e)
                # 确保错误消息是UTF-8编码
                if isinstance(error_msg, bytes):
                    error_msg = error_msg.decode('utf-8', errors='replace')
                    logger.bind(tag=TAG).debug(f"函数调用错误消息已从bytes解码: {error_msg}")
                yield f"【Ollama服务响应异常: {error_msg}】", None
            except (UnicodeEncodeError, UnicodeDecodeError) as encode_error:
                logger.bind(tag=TAG).error(f"函数调用编码错误: {encode_error}")
                # 如果编码失败，使用英文错误信息
                yield "【Ollama service response error】", None

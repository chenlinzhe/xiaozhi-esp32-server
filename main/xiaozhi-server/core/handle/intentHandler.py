import json
import uuid
import asyncio
from core.utils.dialogue import Message
from core.providers.tts.dto.dto import ContentType
from core.handle.helloHandle import checkWakeupWords
from plugins_func.register import Action, ActionResponse
from core.handle.sendAudioHandle import send_stt_message
from core.utils.util import remove_punctuation_and_length
from core.providers.tts.dto.dto import TTSMessageDTO, SentenceType

TAG = __name__


async def handle_user_intent(conn, text):
    # 预处理输入文本，处理可能的JSON格式
    try:
        if text.strip().startswith('{') and text.strip().endswith('}'):
            parsed_data = json.loads(text)
            if isinstance(parsed_data, dict) and "content" in parsed_data:
                text = parsed_data["content"]  # 提取content用于意图分析
                conn.current_speaker = parsed_data.get("speaker")  # 保留说话人信息
    except (json.JSONDecodeError, TypeError):
        pass

    # 检查是否有明确的退出命令
    _, filtered_text = remove_punctuation_and_length(text)
    if await check_direct_exit(conn, filtered_text):
        return True


    # 检查是否是唤醒词
    if await checkWakeupWords(conn, filtered_text):
        return True





    # 新增：手工处理音量调节（支持绝对值和相对调节）  
    import re

    # speak_txt(conn,"手工处理音量调节（支持绝对值和相对调节）")

    # 先检查是否包含音量相关关键词  
    if any(keyword in text for keyword in ['音量', '声音', '大声', '小声']):  
        volume = None  
        is_relative = False  


        # speak_txt(conn,"手工处理音量调节（支持绝对值和相对调节）")

          
        # 1. 检查相对调节  
        if any(word in text for word in ['调大', '调高', '大声', '增大', '提高']):  
            is_relative = True  
            volume_delta = 10  
        elif any(word in text for word in ['调小', '调低','小声', '减小', '降低']):  
            is_relative = True  
            volume_delta = -10  
        else:  
            # 2. 尝试提取绝对数值 - 使用更简单的正则  
            # 直接提取文本中的所有数字  
            numbers = re.findall(r'\d+', text)  
              
            if numbers:  
                # 取第一个数字作为音量值  
                volume = int(numbers[0])  
                # 确保音量在0-100范围内  
                volume = max(0, min(100, volume)) 

                if volume < 60:
                    volume = 60

                conn.logger.bind(tag=TAG).info(f"提取到音量数值-----------------: {volume}")  
            else:
                pass


        # speak_txt(conn,"测试点2测试点2测试点2测试点2测试点2")
          
        # 处理相对调节:需要先获取当前音量  
        if is_relative:  
            if hasattr(conn, 'mcp_client') and conn.mcp_client:  
                try:  
                    get_status_data = {  
                        "name": "self_get_device_status",  
                        "id": str(uuid.uuid4().hex),  
                        "arguments": json.dumps({})  
                    }  
                      
                    status_result = await conn.func_handler.handle_llm_function_call(  
                        conn, get_status_data  
                    )  
                      
                    # 解析返回的设备状态,提取当前音量  
                    if status_result and status_result.result:  
                        status_data = json.loads(status_result.result)  
                        current_volume = status_data.get('audio_speaker', {}).get('volume', 50)  
                          
                        # 计算新音量,确保在0-100范围内  
                        volume = max(0, min(100, current_volume + volume_delta))  
                        conn.logger.bind(tag=TAG).info(  
                            f"相对调节: 当前音量{current_volume} → 目标音量{volume}"  
                        )  
                except Exception as e:  
                    conn.logger.bind(tag=TAG).error(f"获取当前音量失败: {e}")  
                    # 失败时使用默认基准值  
                    volume = max(0, min(100, 50 + volume_delta)) 

        # speak_txt(conn,"第3测试点第3测试点第3测试点第3测试点") 
          
        # 执行音量设置  
        if volume is not None and hasattr(conn, 'mcp_client') and conn.mcp_client:  
            function_call_data = {  
                "name": "self_audio_speaker_set_volume",  
                "id": str(uuid.uuid4().hex),  
                "arguments": json.dumps({"volume": volume})  
            }  
            
            conn.logger.bind(tag=TAG).info(f"已进入硬编码、调节音量,音量值: {volume}")  
            
            # 定义处理函数  
            def process_volume_adjustment():  
                # 初始化必要状态  
                if not hasattr(conn, 'sentence_id') or not conn.sentence_id:  
                    conn.sentence_id = str(uuid.uuid4().hex)  
                conn.llm_finish_task = True  
                
                # 执行工具调用  
                result = asyncio.run_coroutine_threadsafe(  
                    conn.func_handler.handle_llm_function_call(conn, function_call_data),  
                    conn.loop  
                ).result()  
                
                # 处理结果  
                if result.action == Action.RESPONSE:  
                    speak_txt(conn, result.response)  
                elif result.action == Action.REQLLM:  
                    speak_txt(conn, f"已将音量设置为{volume}")
            
            # 将函数执行放在线程池中  
            conn.executor.submit(process_volume_adjustment)  
            return True




    if conn.intent_type == "function_call":
        # 使用支持function calling的聊天方法,不再进行意图分析
        return False
    # 使用LLM进行意图分析
    intent_result = await analyze_intent_with_llm(conn, text)
    if not intent_result:
        return False
    # 会话开始时生成sentence_id
    conn.sentence_id = str(uuid.uuid4().hex)
    # 处理各种意图
    return await process_intent_result(conn, intent_result, text)


async def check_direct_exit(conn, text):
    """检查是否有明确的退出命令"""
    _, text = remove_punctuation_and_length(text)
    cmd_exit = conn.cmd_exit
    for cmd in cmd_exit:
        if text == cmd:
            conn.logger.bind(tag=TAG).info(f"识别到明确的退出命令: {text}")
            await send_stt_message(conn, text)
            await conn.close()
            return True
    return False


async def analyze_intent_with_llm(conn, text):
    """使用LLM分析用户意图"""
    if not hasattr(conn, "intent") or not conn.intent:
        conn.logger.bind(tag=TAG).warning("意图识别服务未初始化")
        return None

    # 对话历史记录
    dialogue = conn.dialogue
    try:
        intent_result = await conn.intent.detect_intent(conn, dialogue.dialogue, text)
        return intent_result
    except Exception as e:
        conn.logger.bind(tag=TAG).error(f"意图识别失败: {str(e)}")

    return None


async def process_intent_result(conn, intent_result, original_text):
    """处理意图识别结果"""
    try:
        # 尝试将结果解析为JSON
        intent_data = json.loads(intent_result)

        # 检查是否有function_call
        if "function_call" in intent_data:
            # 直接从意图识别获取了function_call
            conn.logger.bind(tag=TAG).debug(
                f"检测到function_call格式的意图结果: {intent_data['function_call']['name']}"
            )
            function_name = intent_data["function_call"]["name"]
            if function_name == "continue_chat":
                return False

            if function_name == "result_for_context":
                await send_stt_message(conn, original_text)
                conn.client_abort = False
                
                def process_context_result():
                    conn.dialogue.put(Message(role="user", content=original_text))
                    
                    from core.utils.current_time import get_current_time_info

                    current_time, today_date, today_weekday, lunar_date = get_current_time_info()
                    
                    # 构建带上下文的基础提示
                    context_prompt = f"""当前时间：{current_time}
                                        今天日期：{today_date} ({today_weekday})
                                        今天农历：{lunar_date}

                                        请根据以上信息回答用户的问题：{original_text}"""
                    
                    response = conn.intent.replyResult(context_prompt, original_text)
                    speak_txt(conn, response)
                
                conn.executor.submit(process_context_result)
                return True

            function_args = {}
            if "arguments" in intent_data["function_call"]:
                function_args = intent_data["function_call"]["arguments"]
                if function_args is None:
                    function_args = {}
            # 确保参数是字符串格式的JSON
            if isinstance(function_args, dict):
                function_args = json.dumps(function_args)

            function_call_data = {
                "name": function_name,
                "id": str(uuid.uuid4().hex),
                "arguments": function_args,
            }

            await send_stt_message(conn, original_text)
            conn.client_abort = False

            # 使用executor执行函数调用和结果处理
            def process_function_call():
                conn.dialogue.put(Message(role="user", content=original_text))

                # 使用统一工具处理器处理所有工具调用
                try:
                    result = asyncio.run_coroutine_threadsafe(
                        conn.func_handler.handle_llm_function_call(
                            conn, function_call_data
                        ),
                        conn.loop,
                    ).result()
                except Exception as e:
                    conn.logger.bind(tag=TAG).error(f"工具调用失败: {e}")
                    result = ActionResponse(
                        action=Action.ERROR, result=str(e), response=str(e)
                    )

                if result:
                    if result.action == Action.RESPONSE:  # 直接回复前端
                        text = result.response
                        if text is not None:
                            speak_txt(conn, text)
                    elif result.action == Action.REQLLM:  # 调用函数后再请求llm生成回复
                        text = result.result
                        conn.dialogue.put(Message(role="tool", content=text))
                        llm_result = conn.intent.replyResult(text, original_text)
                        if llm_result is None:
                            llm_result = text
                        speak_txt(conn, llm_result)
                    elif (
                        result.action == Action.NOTFOUND
                        or result.action == Action.ERROR
                    ):
                        text = result.result
                        if text is not None:
                            speak_txt(conn, text)
                    elif function_name != "play_music":
                        # For backward compatibility with original code
                        # 获取当前最新的文本索引
                        text = result.response
                        if text is None:
                            text = result.result
                        if text is not None:
                            speak_txt(conn, text)

            # 将函数执行放在线程池中
            conn.executor.submit(process_function_call)
            return True
        return False
    except json.JSONDecodeError as e:
        conn.logger.bind(tag=TAG).error(f"处理意图结果时出错: {e}")
        return False


def speak_txt(conn, text):
    conn.tts.tts_text_queue.put(
        TTSMessageDTO(
            sentence_id=conn.sentence_id,
            sentence_type=SentenceType.FIRST,
            content_type=ContentType.ACTION,
        )
    )
    conn.tts.tts_one_sentence(conn, ContentType.TEXT, content_detail=text)
    conn.tts.tts_text_queue.put(
        TTSMessageDTO(
            sentence_id=conn.sentence_id,
            sentence_type=SentenceType.LAST,
            content_type=ContentType.ACTION,
        )
    )
    conn.dialogue.put(Message(role="assistant", content=text))

import json
import asyncio
import uuid
from core.handle.sendAudioHandle import send_stt_message
from core.handle.helloHandle import checkWakeupWords
from core.utils.util import remove_punctuation_and_length
from core.providers.tts.dto.dto import ContentType
from core.utils.dialogue import Message
from plugins_func.register import Action, ActionResponse
from core.providers.tts.dto.dto import TTSMessageDTO, SentenceType
from core.scenario.scenario_manager import scenario_trigger
from core.scenario.dialogue_executor import DialogueStepExecutor

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
    filtered_text = remove_punctuation_and_length(text)[1]
    if await check_direct_exit(conn, filtered_text):
        return True
    # 检查是否是唤醒词
    if await checkWakeupWords(conn, filtered_text):
        return True

    # 检查场景触发 - 优先使用新的教学系统
    if not hasattr(conn, 'scenario_executor') or not conn.scenario_executor:
        triggered_scenario = scenario_trigger.detect_trigger(text, "voice")
        if triggered_scenario:
            # 🔥 关键修复：优先使用新的教学系统处理场景触发
            user_id = conn.device_id if conn.device_id else conn.session_id
            if hasattr(conn, 'teaching_handler') and conn.teaching_handler:
                # 使用新的教学系统处理场景触发
                result = await conn.teaching_handler.chat_status_manager.handle_user_input(user_id, text, conn.child_name or "小朋友")
                if result and result.get("success"):
                    conn.logger.bind(tag=TAG).info(f"✅ 使用新教学系统处理场景触发: {triggered_scenario['id']}")
                    
                    # 🔥 关键修复：调用teaching_handler处理结果
                    action = result.get("action")
                    if action in ["next_step", "retry", "perfect_match_next", "partial_match_next", "no_match_next", "start_teaching", "mode_switch"]:
                        conn.logger.bind(tag=TAG).info(f"🔥 调用teaching_handler处理action: {action}")
                        handled = await conn.teaching_handler.handle_chat_mode(text)
                        if handled:
                            conn.logger.bind(tag=TAG).info(f"✅ teaching_handler成功处理action: {action}")
                        else:
                            conn.logger.bind(tag=TAG).warning(f"⚠️ teaching_handler未处理action: {action}")
                    
                    return True
                else:
                    conn.logger.bind(tag=TAG).warning(f"⚠️ 新教学系统处理失败，回退到旧系统: {triggered_scenario['id']}")
            
            # 回退到旧的场景执行器系统
            await start_scenario_dialogue(conn, triggered_scenario['id'])
            return True

    # 如果正在执行场景对话，优先处理场景逻辑
    if hasattr(conn, 'scenario_executor') and conn.scenario_executor:
        return await handle_scenario_dialogue(conn, text)

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


async def start_scenario_dialogue(conn, scenario_id):
    """启动场景对话"""
    try:
        # 创建场景执行器
        executor = DialogueStepExecutor(scenario_id, conn.child_name)
        success = await executor.initialize()
        
        if not success:
            conn.logger.bind(tag=TAG).error(f"初始化场景执行器失败: {scenario_id}")
            return
        
        conn.scenario_executor = executor
        conn.logger.bind(tag=TAG).info(f"启动场景对话: {scenario_id}")
        
        # 🔥 关键修复：启动场景对话时自动切换到教学模式
        user_id = conn.device_id if conn.device_id else conn.session_id
        if hasattr(conn, 'teaching_handler') and conn.teaching_handler:
            # 使用teaching_handler切换到教学模式
            success = conn.teaching_handler.chat_status_manager.set_user_chat_status(user_id, "teaching_mode")
            if success:
                conn.logger.bind(tag=TAG).info(f"✅ 场景触发成功，已切换到教学模式: {user_id}")
            else:
                conn.logger.bind(tag=TAG).error(f"❌ 切换到教学模式失败: {user_id}")
        
        # 获取第一个步骤
        if executor.steps:
            first_step = executor.get_current_step()
            if first_step:
                ai_message = first_step.get('aiMessage', '').replace("**{childName}**", conn.child_name or "小朋友")
                speak_txt(conn, ai_message)
        
    except Exception as e:
        conn.logger.bind(tag=TAG).error(f"启动场景对话失败: {e}")


async def handle_scenario_dialogue(conn, text):
    """处理场景对话"""
    try:
        if not hasattr(conn, 'scenario_executor') or not conn.scenario_executor:
            return False
        
        executor = conn.scenario_executor
        result = executor.execute_current_step(text)
        
        if result['type'] == 'complete':
            # 场景完成
            speak_txt(conn, result['message'])
            
            # 🔥 关键修复：场景完成时切换到自由模式
            user_id = conn.device_id if conn.device_id else conn.session_id
            if hasattr(conn, 'teaching_handler') and conn.teaching_handler:
                success = conn.teaching_handler.chat_status_manager.set_user_chat_status(user_id, "free_mode")
                if success:
                    conn.logger.bind(tag=TAG).info(f"✅ 场景完成，已切换到自由模式: {user_id}")
                else:
                    conn.logger.bind(tag=TAG).error(f"❌ 切换到自由模式失败: {user_id}")
            
            # 保存学习记录
            if hasattr(conn, 'scenario_executor') and conn.scenario_executor:
                try:
                    record_id = await conn.scenario_executor.end_session()
                    if record_id:
                        conn.logger.bind(tag=TAG).info(f"学习记录已保存: {record_id}")
                except Exception as e:
                    conn.logger.bind(tag=TAG).error(f"保存学习记录失败: {e}")
            
            conn.scenario_executor = None
            return True
        elif result['type'] == 'next':
            # 进入下一步
            speak_txt(conn, result['message'])
            return True
        elif result['type'] == 'retry':
            # 重试当前步骤
            speak_txt(conn, result['message'])
            return True
        elif result['type'] == 'alternative':
            # 提供替代方案
            speak_txt(conn, result['message'])
            # 如果有手势提示，可以在这里处理
            if result.get('gesture'):
                conn.logger.bind(tag=TAG).info(f"手势提示: {result['gesture']}")
            return True
        else:
            return False
            
    except Exception as e:
        conn.logger.bind(tag=TAG).error(f"处理场景对话失败: {e}")
        return False

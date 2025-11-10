from core.handle.sendAudioHandle import send_stt_message
from core.handle.intentHandler import handle_user_intent
from core.utils.output_counter import check_device_output_limit
from core.handle.abortHandle import handleAbortMessage
import time
import asyncio
import json
from core.handle.sendAudioHandle import SentenceType
from core.utils.util import audio_to_data

TAG = __name__


async def handleAudioMessage(conn, audio):
    # 当前片段是否有人说话
    have_voice = conn.vad.is_vad(conn, audio)
    # 如果设备刚刚被唤醒，短暂忽略VAD检测
    # 但是教学模式中需要保持语音监听，所以检查是否在教学模式中
    if have_voice and hasattr(conn, "just_woken_up") and conn.just_woken_up:
        # 检查是否在教学模式中，如果是教学模式，不忽略VAD检测
        is_teaching_mode = False
        try:
            # 检查Redis中的聊天状态
            if hasattr(conn, 'device_id') and conn.device_id:
                from core.utils.redis_client import redis_client
                user_id = conn.device_id
                current_status = redis_client.get_user_chat_status(user_id)
                is_teaching_mode = (current_status == "teaching_mode")
        except Exception as e:
            conn.logger.bind(tag=TAG).debug(f"检查教学模式状态失败: {e}")
        
        if not is_teaching_mode:
            have_voice = False
            # 设置一个短暂延迟后恢复VAD检测
            conn.asr_audio.clear()
            if not hasattr(conn, "vad_resume_task") or conn.vad_resume_task.done():
                conn.vad_resume_task = asyncio.create_task(resume_vad_detection(conn))
            return

    if have_voice:
        if conn.client_is_speaking and conn.allow_interrupt:  # 添加 allow_interrupt 检查  
            await handleAbortMessage(conn)
            
    # 设备长时间空闲检测，用于say goodbye
    await no_voice_close_connect(conn, have_voice)
    # 接收音频
    await conn.asr.receive_audio(conn, audio, have_voice)


async def resume_vad_detection(conn):
    # 等待2秒后恢复VAD检测
    await asyncio.sleep(1)
    conn.just_woken_up = False


async def startToChat(conn, text):
    # 检查输入是否是JSON格式（包含说话人信息）
    speaker_name = None
    actual_text = text
    
    try:
        # 尝试解析JSON格式的输入
        if text.strip().startswith('{') and text.strip().endswith('}'):
            data = json.loads(text)
            if 'speaker' in data and 'content' in data:
                speaker_name = data['speaker']
                actual_text = data['content']
                conn.logger.bind(tag=TAG).info(f"解析到说话人信息: {speaker_name}")
                
                # 直接使用JSON格式的文本，不解析
                actual_text = text
    except (json.JSONDecodeError, KeyError):
        # 如果解析失败，继续使用原始文本
        pass
    
    # 保存说话人信息到连接对象
    if speaker_name:
        conn.current_speaker = speaker_name
    else:
        conn.current_speaker = None

    # 检查是否需要绑定设备
    if conn.need_bind:
        # 如果设备已经激活，清除绑定标志
        if not conn.bind_code:
            conn.need_bind = False
            conn.logger.bind(tag=TAG).info("设备已激活，清除绑定标志")
        else:
            await check_bind_device(conn)
            return

    # 如果当日的输出字数大于限定的字数
    if conn.max_output_size > 0:
        if check_device_output_limit(
            conn.headers.get("device-id"), conn.max_output_size
        ):
            await max_out_size(conn)
            return
    if conn.client_is_speaking:
        await handleAbortMessage(conn)

    # 🔥 新增：检测用户姓名并自动存储
    name_detected = await detect_and_store_user_name(conn, actual_text)
    if name_detected:
        # 如果检测到姓名并已存储，继续正常流程
        pass

    # 首先进行意图分析，使用实际文本内容
    intent_handled = await handle_user_intent(conn, actual_text)

    if intent_handled:
        # 如果意图已被处理，不再进行聊天
        return

    # 意图未被处理，继续常规聊天流程，使用实际文本内容
    await send_stt_message(conn, actual_text)
    conn.executor.submit(conn.chat, actual_text)


async def no_voice_close_connect(conn, have_voice):
    if have_voice:
        conn.last_activity_time = time.time() * 1000
        return
    # 只有在已经初始化过时间戳的情况下才进行超时检查
    if conn.last_activity_time > 0.0:
        no_voice_time = time.time() * 1000 - conn.last_activity_time
        close_connection_no_voice_time = int(
            conn.config.get("close_connection_no_voice_time", 120)
        )
        if (
            not conn.close_after_chat
            and no_voice_time > 1000 * close_connection_no_voice_time
        ):
            conn.close_after_chat = True
            conn.client_abort = False
            end_prompt = conn.config.get("end_prompt", {})
            if end_prompt and end_prompt.get("enable", True) is False:
                conn.logger.bind(tag=TAG).info("结束对话，无需发送结束提示语")
                await conn.close()
                return
            prompt = end_prompt.get("prompt")
            if not prompt:
                prompt = "请你以```时间过得真快```未来头，用富有感情、依依不舍的话来结束这场对话吧！字数不超过30个字"
            await startToChat(conn, prompt)


async def max_out_size(conn):
    text = "不好意思，我现在有点事情要忙，明天这个时候我们再聊，约好了哦！明天不见不散，拜拜！"
    await send_stt_message(conn, text)
    file_path = "config/assets/max_output_size.wav"
    opus_packets, _ = audio_to_data(file_path)
    conn.tts.tts_audio_queue.put((SentenceType.LAST, opus_packets, text))
    conn.close_after_chat = True


async def check_bind_device(conn):
    if conn.bind_code:
        # 确保bind_code是6位数字
        if len(conn.bind_code) != 6:
            conn.logger.bind(tag=TAG).error(f"无效的绑定码格式: {conn.bind_code}")
            text = "绑定码格式错误，请检查配置。"
            await send_stt_message(conn, text)
            return

        text = f"请登录控制面板，输入{conn.bind_code}，绑定设备。"
        await send_stt_message(conn, text)

        # 播放提示音
        music_path = "config/assets/bind_code.wav"
        opus_packets, _ = audio_to_data(music_path)
        conn.tts.tts_audio_queue.put((SentenceType.FIRST, opus_packets, text))

        # 逐个播放数字
        for i in range(6):  # 确保只播放6位数字
            try:
                digit = conn.bind_code[i]
                num_path = f"config/assets/bind_code/{digit}.wav"
                num_packets, _ = audio_to_data(num_path)
                conn.tts.tts_audio_queue.put((SentenceType.MIDDLE, num_packets, None))
            except Exception as e:
                conn.logger.bind(tag=TAG).error(f"播放数字音频失败: {e}")
                continue
        conn.tts.tts_audio_queue.put((SentenceType.LAST, [], None))
    else:
        text = f"没有找到该设备的版本信息，请正确配置 OTA地址，然后重新编译固件。"
        await send_stt_message(conn, text)
        music_path = "config/assets/bind_not_found.wav"
        opus_packets, _ = audio_to_data(music_path)
        conn.tts.tts_audio_queue.put((SentenceType.LAST, opus_packets, text))


async def detect_and_store_user_name(conn, text):
    """
    检测用户输入中的姓名并自动存储
    
    Args:
        conn: 连接对象
        text: 用户输入的文本
        
    Returns:
        bool: 是否检测到并存储了姓名
    """
    try:
        # 检查是否有设备ID
        if not conn.device_id:
            return False
            
        # 检查用户是否已经有姓名
        from core.providers.user.user_info_manager import UserInfoManager
        user_manager = UserInfoManager(conn.config)
        has_name = user_manager.has_user_name(conn.device_id)
        
        if has_name:
            user_info = user_manager.get_user_info(conn.device_id)
            if user_info is None:
                conn.logger.bind(tag=TAG).error("❌ get_user_info 返回 None，可能 token 失效，使用默认姓名")
                conn.child_name = "小朋友"
                if hasattr(conn, 'teaching_handler') and conn.teaching_handler:
                    conn.teaching_handler.child_name = conn.child_name
                return False  # 或 True，根据需要
            conn.child_name = user_info.get("userName", "小朋友")
            if hasattr(conn, 'teaching_handler') and conn.teaching_handler:
                conn.teaching_handler.child_name = conn.child_name
            return True
            
        # 使用extract_name函数检测姓名
        from core.providers.user.user_info_manager import extract_name
        detected_name = extract_name(text)
        
        if detected_name:
            conn.logger.bind(tag=TAG).info(f"🔍 检测到用户姓名: {detected_name}")
            
            # 验证姓名有效性（过滤无效输入）
            if is_valid_name(detected_name):
                # 存储姓名到数据库
                success = user_manager.update_user_name(conn.device_id, detected_name)
                
                if success:
                    # 更新连接对象中的姓名
                    conn.child_name = detected_name
                    if hasattr(conn, 'teaching_handler') and conn.teaching_handler:
                        conn.teaching_handler.child_name = detected_name
                    
                    conn.logger.bind(tag=TAG).info(f"✅ 成功存储用户姓名: {detected_name}")
                    
                    # 发送确认消息
                    confirmation_message = f"好的，{detected_name}！很高兴认识你！"
                    await send_stt_message(conn, confirmation_message)
                    
                    return True
                else:
                    conn.logger.bind(tag=TAG).error(f"❌ 存储用户姓名失败: {detected_name}")
            else:
                conn.logger.bind(tag=TAG).info(f"⚠️ 检测到无效姓名，忽略: {detected_name}")
        
        return False
        
    except Exception as e:
        conn.logger.bind(tag=TAG).error(f"❌ 检测用户姓名失败: {e}")
        import traceback
        conn.logger.bind(tag=TAG).error(f"异常堆栈: {traceback.format_exc()}")
        return False


def is_valid_name(name):
    """
    验证姓名是否有效
    
    Args:
        name: 检测到的姓名
        
    Returns:
        bool: 姓名是否有效
    """
    if not name or not isinstance(name, str):
        return False
        
    # 去除首尾空格
    name = name.strip()
    
    # 检查长度（1-10个字符）
    if len(name) < 1 or len(name) > 10:
        return False
        
    # 检查是否包含无效字符（只允许中文、英文字母、数字）
    import re
    if not re.match(r'^[\u4e00-\u9fa5a-zA-Z0-9]+$', name):
        return False
        
    # 过滤常见的无效输入
    invalid_names = ['我', '你', '他', '她', '它', '这个', '那个', '什么', '怎么', '为什么', '哪里', '什么时候']
    if name.lower() in [n.lower() for n in invalid_names]:
        return False
        
    return True

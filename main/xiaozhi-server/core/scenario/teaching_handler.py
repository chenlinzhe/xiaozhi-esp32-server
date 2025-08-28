"""
场景教学处理器
负责处理场景教学相关的功能，包括聊天模式切换、教学会话管理、超时检查等
"""

import asyncio
import time
import uuid
import threading
import json
from typing import Dict, Any, Optional, List
from core.scenario.chat_status_manager import ChatStatusManager
from core.providers.tts.dto.dto import ContentType, TTSMessageDTO, SentenceType
from core.utils.dialogue import Message
from config.logger import setup_logging

TAG = __name__


class TeachingHandler:
    """场景教学处理器"""
    
    def __init__(self, connection):
        """
        初始化教学处理器
        
        Args:
            connection: ConnectionHandler实例
        """
        self.connection = connection
        self.logger = setup_logging()
        self.chat_status_manager = ChatStatusManager()
        self.child_name = "小朋友"
        
    def set_child_name(self, child_name: str):
        """设置儿童姓名"""
        self.child_name = child_name
        
    def handle_chat_mode(self, query: str) -> Optional[bool]:
        """
        处理聊天模式切换和教学模式逻辑
        
        Args:
            query: 用户输入的查询文本
            
        Returns:
            bool: 如果处理了特殊逻辑返回True，否则返回None继续正常流程
        """
        try:
            self.logger.bind(tag=TAG).info(f"处理聊天模式切换和教学模式逻辑")
            
            # 使用设备ID作为用户ID，如果没有则使用session_id
            user_id = self.connection.device_id if self.connection.device_id else self.connection.session_id
            
            # 检查当前聊天状态
            current_status = self.chat_status_manager.get_user_chat_status(user_id)
            self.logger.bind(tag=TAG).info(f"用户 {user_id} 当前聊天状态: {current_status}")
            
            # 异步处理用户输入
            future = asyncio.run_coroutine_threadsafe(
                self.chat_status_manager.handle_user_input(user_id, query, self.child_name),
                self.connection.loop
            )
            result = future.result()
            
            self.logger.bind(tag=TAG).info(f"聊天模式处理结果: {result}")
            
            if result and result.get("success"):
                action = result.get("action")
                ai_message = result.get("ai_message", "")
                
                if action == "mode_switch":
                    # 模式切换，直接返回AI消息
                    self.logger.bind(tag=TAG).info(f"开始处理模式切换: {result.get('mode')}")
                    self.logger.bind(tag=TAG).info(f"AI消息内容: {ai_message}")
                    
                    # 确保TTS已准备就绪
                    if not self._ensure_tts_ready():
                        self.logger.bind(tag=TAG).error("TTS未准备就绪，无法进行教学模式切换")
                        return True  # 返回True避免继续处理
                    
                    # 发送TTS消息
                    self._send_tts_message(ai_message)
                    self.connection.dialogue.put(Message(role="assistant", content=ai_message))
                    self.logger.bind(tag=TAG).info(f"聊天模式切换完成: {result.get('mode')}")
                    

                    
                    # 如果切换到教学模式，启动等待超时检查
                    if result.get('mode') == 'teaching_mode':
                        wait_time = result.get("wait_time", 20)
                        self.logger.bind(tag=TAG).info(f"教学模式，等待时间: {wait_time}")
                        self._start_teaching_timeout_check(user_id, wait_time)
                    
                    return True
                    
                elif action == "start_teaching":
                    # 开始教学模式
                    # 确保TTS已准备就绪
                    if not self._ensure_tts_ready():
                        self.logger.bind(tag=TAG).error("TTS未准备就绪，无法开始教学模式")
                        return True
                    
                    self._send_tts_message(ai_message)
                    self.connection.dialogue.put(Message(role="assistant", content=ai_message))
                    self.logger.bind(tag=TAG).info(f"开始教学模式: {result.get('scenario_name')}")
                    
                    # 启动等待超时检查
                    self._start_teaching_timeout_check(user_id, result.get("timeoutSeconds", 20))
                    return True
                    
                elif action == "next_step" or action == "retry":
                    # 教学步骤处理
                    # 首先发送评估反馈
                    evaluation = result.get("evaluation", {})
                    feedback = evaluation.get("feedback", "")
                    if feedback:
                        self.logger.bind(tag=TAG).info(f"发送评估反馈: {feedback}")
                        self._send_tts_message(feedback)
                        self.connection.dialogue.put(Message(role="assistant", content=feedback))
                        
                        # 等待一小段时间再发送下一步消息
                        time.sleep(1)
                    
                    # 然后发送下一步的AI消息
                    self._send_tts_message(ai_message)
                    self.connection.dialogue.put(Message(role="assistant", content=ai_message))
                    self.logger.bind(tag=TAG).info(f"教学步骤: {action}")
                    
                    # 重新启动等待超时检查
                    self._start_teaching_timeout_check(user_id, result.get("timeoutSeconds", 20))
                    return True
                    
                elif action == "completed":
                    # 教学完成，切换到自由模式
                    # 首先发送评估反馈
                    evaluation = result.get("evaluation", {})
                    feedback = evaluation.get("feedback", "")
                    if feedback:
                        self.logger.bind(tag=TAG).info(f"发送最终评估反馈: {feedback}")
                        self._send_tts_message(feedback)
                        self.connection.dialogue.put(Message(role="assistant", content=feedback))
                        
                        # 等待一小段时间再发送完成消息
                        time.sleep(1)
                    
                    # 然后发送完成消息
                    self._send_tts_message(ai_message)
                    self.connection.dialogue.put(Message(role="assistant", content=ai_message))
                    self.logger.bind(tag=TAG).info(f"教学完成，最终得分: {result.get('final_score')}")
                    
                    return True
                    
                elif action == "free_chat":
                    # 自由聊天模式，发送简单回复后继续正常流程
                    self._send_tts_message(ai_message)
                    self.connection.dialogue.put(Message(role="assistant", content=ai_message))
                    self.logger.bind(tag=TAG).info("自由聊天模式")
                    # 不返回True，让流程继续到正常的LLM处理
                    return None
                    
                elif action == "warning_reminder":
                    # 警告提示
                    self._send_tts_message(ai_message)
                    self.connection.dialogue.put(Message(role="assistant", content=ai_message))
                    self.logger.bind(tag=TAG).info("发出警告提示")
                    
                    return True
                    
                elif action == "final_reminder":
                    # 最终提醒
                    self._send_tts_message(ai_message)
                    self.connection.dialogue.put(Message(role="assistant", content=ai_message))
                    self.logger.bind(tag=TAG).info("发出最终提醒")
                    
                    return True
                    
                elif action == "timeout_response":
                    # 超时自动回复
                    self._send_tts_message(ai_message)
                    self.connection.dialogue.put(Message(role="assistant", content=ai_message))
                    self.logger.bind(tag=TAG).info("教学超时自动回复")
                    
                    return True
            
            # 如果没有特殊处理，返回None继续正常流程
            self.logger.bind(tag=TAG).info(f"聊天模式处理完成，返回None继续正常流程")
            return None
            
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"处理聊天模式失败: {e}")
            return None

    def _send_tts_message(self, message: str):
        """
        发送TTS消息
        
        Args:
            message: 要发送的消息文本
        """
        if not message:
            self.logger.bind(tag=TAG).warning("TTS消息为空，跳过发送")
            return
            
        # 检查TTS是否可用
        if not self.connection.tts:
            self.logger.bind(tag=TAG).error("TTS实例不存在，无法发送消息")
            return
            
        try:
            # 使用简化的TTS发送方式
            self.connection.tts.tts_one_sentence(
                self.connection, 
                ContentType.TEXT, 
                content_detail=message
            )
            self.logger.bind(tag=TAG).info(f"TTS消息已发送: {message[:50]}...")
            
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"发送TTS消息失败: {e}")

    def _ensure_tts_ready(self):
        """
        确保TTS实例已完全初始化并准备就绪
        
        Returns:
            bool: TTS是否准备就绪
        """
        # 由于TTS在连接建立时就已初始化，这里只需要简单检查
        if not self.connection.tts:
            self.logger.bind(tag=TAG).error("TTS实例不存在")
            return False
        
        # 检查TTS线程是否正常运行
        try:
            if (hasattr(self.connection.tts, 'tts_priority_thread') and 
                self.connection.tts.tts_priority_thread.is_alive()):
                self.logger.bind(tag=TAG).info("TTS已准备就绪")
                return True
            else:
                self.logger.bind(tag=TAG).error("TTS文本处理线程未运行")
                return False
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"检查TTS状态时出错: {e}")
            return False


    def _start_teaching_timeout_check(self, user_id: str, wait_time: int):
        """
        启动教学超时检查 - 优化版本，支持渐进式提示
        
        Args:
            user_id: 用户ID
            wait_time: 等待时间（秒）
        """
        # 如果wait_time为0，不启动超时检查
        if wait_time <= 0:
            self.logger.bind(tag=TAG).info("不启动超时检查（立即开始）")
            return
            
        self.logger.bind(tag=TAG).info(f"启动渐进式超时检查，总等待时间: {wait_time}秒")
        
        async def progressive_timeout_check():
            """渐进式超时检查"""
            try:
                # 获取超时配置
                progressive_config = self.chat_status_manager.PROGRESSIVE_TIMEOUT_CONFIG
                warning_timeout = wait_time * progressive_config.get("warning_timeout", 0.7)
                final_timeout = wait_time * progressive_config.get("final_timeout", 0.9)
                
                self.logger.bind(tag=TAG).info(f"警告时间点: {warning_timeout}秒")
                self.logger.bind(tag=TAG).info(f"最终提醒时间点: {final_timeout}秒")
                
                # 检查警告提示
                if progressive_config.get("enabled", False):
                    await asyncio.sleep(warning_timeout)
                    result = await self.chat_status_manager.check_teaching_timeout(user_id)
                    if result and result.get("success") and result.get("action") == "warning_reminder":
                        ai_message = result.get("ai_message", "")
                        self._send_tts_message(ai_message)
                        self.connection.dialogue.put(Message(role="assistant", content=ai_message))
                        self.logger.bind(tag=TAG).info("发出警告提示")
                    
                    # 检查最终提醒
                    remaining_time = final_timeout - warning_timeout
                    if remaining_time > 0:
                        await asyncio.sleep(remaining_time)
                        result = await self.chat_status_manager.check_teaching_timeout(user_id)
                        if result and result.get("success") and result.get("action") == "final_reminder":
                            ai_message = result.get("ai_message", "")
                            self._send_tts_message(ai_message)
                            self.connection.dialogue.put(Message(role="assistant", content=ai_message))
                            self.logger.bind(tag=TAG).info("发出最终提醒")
                
                # 最终超时检查
                remaining_time = wait_time - final_timeout
                if remaining_time > 0:
                    await asyncio.sleep(remaining_time)
                
                result = await self.chat_status_manager.check_teaching_timeout(user_id)
                if result and result.get("success") and result.get("action") == "timeout_response":
                    ai_message = result.get("ai_message", "")
                    self._send_tts_message(ai_message)
                    self.connection.dialogue.put(Message(role="assistant", content=ai_message))
                    self.logger.bind(tag=TAG).info("教学超时，发送替代提示")
                    
            except Exception as e:
                self.logger.bind(tag=TAG).error(f"渐进式超时检查失败: {e}")
        
        # 在事件循环中执行超时检查
        try:
            asyncio.create_task(progressive_timeout_check())
        except RuntimeError as e:
            if "no running event loop" in str(e):
                # 如果没有运行的事件循环，使用run_coroutine_threadsafe
                asyncio.run_coroutine_threadsafe(progressive_timeout_check(), self.connection.loop)
            else:
                raise

    async def cleanup(self):
        """清理教学处理器资源"""
        try:
            if hasattr(self, "chat_status_manager") and self.chat_status_manager:
                user_id = self.connection.device_id if self.connection.device_id else self.connection.session_id
                self.chat_status_manager.redis_client.delete_session_data(f"teaching_{user_id}")
                self.logger.bind(tag=TAG).info(f"清理用户 {user_id} 的聊天会话数据")
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"清理教学处理器资源失败: {e}")

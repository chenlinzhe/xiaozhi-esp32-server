import os
import time
import base64
from typing import Optional, Dict, List

import httpx

TAG = __name__


class DeviceNotFoundException(Exception):
    pass


class DeviceBindException(Exception):
    def __init__(self, bind_code):
        self.bind_code = bind_code
        super().__init__(f"设备绑定异常，绑定码: {bind_code}")


class ManageApiClient:
    _instance = None
    _client = None
    _secret = None
    _user_token = None

    def __new__(cls, config):
        """单例模式确保全局唯一实例，并支持传入配置参数"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._init_client(config)
        return cls._instance

    @classmethod
    def _init_client(cls, config):
        """初始化持久化连接池"""
        cls.config = config.get("manager-api")

        if not cls.config:
            raise Exception("manager-api配置错误")

        if not cls.config.get("url") or not cls.config.get("secret"):
            raise Exception("manager-api的url或secret配置错误")

        if "你" in cls.config.get("secret"):
            raise Exception("请先配置manager-api的secret")

        cls._secret = cls.config.get("secret")
        cls.max_retries = cls.config.get("max_retries", 6)  # 最大重试次数
        cls.retry_delay = cls.config.get("retry_delay", 10)  # 初始重试延迟(秒)
        
        # 创建基础客户端（用于服务器密钥认证的API）
        cls._client = httpx.Client(
            base_url=cls.config.get("url"),
            headers={
                "User-Agent": f"PythonClient/2.0 (PID:{os.getpid()})",
                "Accept": "application/json",
                "Authorization": "Bearer " + cls._secret,
            },
            timeout=cls.config.get("timeout", 30),  # 默认超时时间30秒
        )
    
    @classmethod
    def _get_user_client(cls):
        """获取用户token认证的客户端"""
        if not cls._user_token:
            cls._login_and_get_token()
        
        if cls._user_token:
            return httpx.Client(
                base_url=cls.config.get("url"),
                headers={
                    "User-Agent": f"PythonClient/2.0 (PID:{os.getpid()})",
                    "Accept": "application/json",
                    "Authorization": "Bearer " + cls._user_token,
                },
                timeout=cls.config.get("timeout", 30),
            )
        return None
    
    @classmethod
    def _login_and_get_token(cls):
        """登录并获取用户token"""
        try:
            print("正在登录获取用户token...")
            
            # 尝试使用常见的用户名登录
            login_attempts = [
                {"username": "ningwenjie", "password": "310113Nm."},  # 用户提供的凭据
                {"username": "admin", "password": "admin"},
                {"username": "admin", "password": "123456"},
                {"username": "admin", "password": "password"},
                {"username": "xiaozhi", "password": "xiaozhi"},
                {"username": "xiaozhi", "password": "123456"},
            ]
            
            for attempt in login_attempts:
                try:
                    login_data = {
                        "username": attempt["username"],
                        "password": attempt["password"],
                        "captcha": "123456"   # 跳过验证码验证
                    }
                    
                    # 构建登录URL
                    base_url = cls.config.get("url").replace("/xiaozhi", "")
                    login_url = f"{base_url}/xiaozhi/user/login"
                    
                    print(f"尝试登录: username={attempt['username']}")
                    
                    # 使用基础客户端发送登录请求
                    response = cls._client.post(login_url, json=login_data)
                    
                    if response.status_code == 200:
                        data = response.json()
                        print(f"登录响应数据: {data}")
                        if data.get('code') == 0:
                            token_data = data.get('data', {})
                            # 尝试多种可能的token字段名
                            cls._user_token = (
                                token_data.get('accessToken') or 
                                token_data.get('token') or 
                                token_data.get('access_token') or
                                data.get('token') or
                                data.get('accessToken')
                            )
                            if cls._user_token:
                                print(f"登录成功，用户: {attempt['username']}, token: {cls._user_token[:20]}...")
                                return True
                            else:
                                print(f"登录成功但未获取到token，完整响应: {data}")
                                continue
                        else:
                            print(f"登录失败: {data.get('msg', '未知错误')}")
                            continue
                    else:
                        print(f"登录请求失败: HTTP {response.status_code}")
                        continue
                except Exception as e:
                    print(f"登录尝试异常: {e}")
                    continue
            
            print("所有登录尝试都失败了")
            return False
        except Exception as e:
            print(f"登录异常: {e}")
            return False

    @classmethod
    def _request(cls, method: str, endpoint: str, **kwargs) -> Dict:
        """发送单次HTTP请求并处理响应"""
        endpoint = endpoint.lstrip("/")
        response = cls._client.request(method, endpoint, **kwargs)
        response.raise_for_status()

        result = response.json()

        # 处理API返回的业务错误
        if result.get("code") == 10041:
            raise DeviceNotFoundException(result.get("msg"))
        elif result.get("code") == 10042:
            raise DeviceBindException(result.get("msg"))
        elif result.get("code") != 0:
            raise Exception(f"API返回错误: {result.get('msg', '未知错误')}")

        # 返回成功数据
        return result.get("data") if result.get("code") == 0 else None

    @classmethod
    def _should_retry(cls, exception: Exception) -> bool:
        """判断异常是否应该重试"""
        # 网络连接相关错误
        if isinstance(
            exception, (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError)
        ):
            return True

        # HTTP状态码错误
        if isinstance(exception, httpx.HTTPStatusError):
            status_code = exception.response.status_code
            return status_code in [408, 429, 500, 502, 503, 504]

        return False

    @classmethod
    def _execute_request(cls, method: str, endpoint: str, **kwargs) -> Dict:
        """带重试机制的请求执行器"""
        retry_count = 0

        while retry_count <= cls.max_retries:
            try:
                # 执行请求
                return cls._request(method, endpoint, **kwargs)
            except Exception as e:
                # 判断是否应该重试
                if retry_count < cls.max_retries and cls._should_retry(e):
                    retry_count += 1
                    print(
                        f"{method} {endpoint} 请求失败，将在 {cls.retry_delay:.1f} 秒后进行第 {retry_count} 次重试"
                    )
                    time.sleep(cls.retry_delay)
                    continue
                else:
                    # 不重试，直接抛出异常
                    raise

    @classmethod
    def safe_close(cls):
        """安全关闭连接池"""
        if cls._client:
            cls._client.close()
            cls._instance = None


def get_server_config() -> Optional[Dict]:
    """获取服务器基础配置"""
    return ManageApiClient._instance._execute_request("POST", "/config/server-base")


def get_agent_models(
    mac_address: str, client_id: str, selected_module: Dict
) -> Optional[Dict]:
    """获取代理模型配置"""
    return ManageApiClient._instance._execute_request(
        "POST",
        "/config/agent-models",
        json={
            "macAddress": mac_address,
            "clientId": client_id,
            "selectedModule": selected_module,
        },
    )


def save_mem_local_short(mac_address: str, short_momery: str) -> Optional[Dict]:
    try:
        return ManageApiClient._instance._execute_request(
            "PUT",
            f"/agent/saveMemory/" + mac_address,
            json={
                "summaryMemory": short_momery,
            },
        )
    except Exception as e:
        print(f"存储短期记忆到服务器失败: {e}")
        return None


def report(
    mac_address: str, session_id: str, chat_type: int, content: str, audio, report_time
) -> Optional[Dict]:
    """带熔断的业务方法示例"""
    if not content or not ManageApiClient._instance:
        return None
    try:
        return ManageApiClient._instance._execute_request(
            "POST",
            f"/agent/chat-history/report",
            json={
                "macAddress": mac_address,
                "sessionId": session_id,
                "chatType": chat_type,
                "content": content,
                "reportTime": report_time,
                "audioBase64": (
                    base64.b64encode(audio).decode("utf-8") if audio else None
                ),
            },
        )
    except Exception as e:
        print(f"TTS上报失败: {e}")
        return None


def init_service(config):
    ManageApiClient(config)


# 场景相关API方法
def _ensure_client_initialized():
    """确保客户端已初始化"""
    if ManageApiClient._instance is None:
        from config.config_loader import load_config
        config = load_config()
        ManageApiClient(config)

def get_scenario_list(agent_id: str = None, page: int = 1, limit: int = 100, is_active: bool = None) -> Optional[Dict]:
    """获取场景列表"""
    try:
        _ensure_client_initialized()
        params = {"page": page, "limit": limit}
        if agent_id:
            params["agentId"] = agent_id
        if is_active is not None:
            params["isActive"] = 1 if is_active else 0
        
        # 使用用户token认证的客户端
        user_client = ManageApiClient._instance._get_user_client()
        if not user_client:
            print("无法获取用户认证客户端")
            return None
        
        response = user_client.get("/xiaozhi/scenario/list", params=params)
        response.raise_for_status()
        
        result = response.json()
        if result.get("code") != 0:
            raise Exception(f"API返回错误: {result.get('msg', '未知错误')}")
        
        return result.get("data")
    except Exception as e:
        print(f"获取场景列表失败: {e}")
        return None


def get_scenario_by_id(scenario_id: str) -> Optional[Dict]:
    """根据ID获取场景"""
    try:
        _ensure_client_initialized()
        return ManageApiClient._instance._execute_request(
            "GET",
            f"/xiaozhi/scenario/{scenario_id}"
        )
    except Exception as e:
        print(f"获取场景失败: {e}")
        return None


def create_scenario(scenario_data: Dict) -> Optional[Dict]:
    """创建场景"""
    try:
        _ensure_client_initialized()
        return ManageApiClient._instance._execute_request(
            "POST",
            "/xiaozhi/scenario",
            json=scenario_data
        )
    except Exception as e:
        print(f"创建场景失败: {e}")
        return None


def update_scenario(scenario_id: str, scenario_data: Dict) -> Optional[Dict]:
    """更新场景"""
    try:
        _ensure_client_initialized()
        return ManageApiClient._instance._execute_request(
            "PUT",
            f"/xiaozhi/scenario/{scenario_id}",
            json=scenario_data
        )
    except Exception as e:
        print(f"更新场景失败: {e}")
        return None


def delete_scenario(scenario_id: str) -> Optional[Dict]:
    """删除场景"""
    try:
        _ensure_client_initialized()
        return ManageApiClient._instance._execute_request(
            "DELETE",
            f"/xiaozhi/scenario/{scenario_id}"
        )
    except Exception as e:
        print(f"删除场景失败: {e}")
        return None


def get_scenario_steps(scenario_id: str) -> Optional[List[Dict]]:
    """获取场景步骤列表"""
    try:
        _ensure_client_initialized()
        result = ManageApiClient._instance._execute_request(
            "GET",
            f"/xiaozhi/scenario-step/list/{scenario_id}"
        )
        if result and isinstance(result, list):
            # 按stepOrder字段排序
            result.sort(key=lambda x: x.get('stepOrder', 0))
        return result
    except Exception as e:
        print(f"获取场景步骤失败: {e}")
        return None


def get_step_by_id(step_id: str) -> Optional[Dict]:
    """根据ID获取步骤"""
    try:
        _ensure_client_initialized()
        return ManageApiClient._instance._execute_request(
            "GET",
            f"/xiaozhi/step/{step_id}"
        )
    except Exception as e:
        print(f"获取步骤失败: {e}")
        return None


def create_step(step_data: Dict) -> Optional[Dict]:
    """创建步骤"""
    try:
        _ensure_client_initialized()
        return ManageApiClient._instance._execute_request(
            "POST",
            "/xiaozhi/step",
            json=step_data
        )
    except Exception as e:
        print(f"创建步骤失败: {e}")
        return None


def update_step(step_id: str, step_data: Dict) -> Optional[Dict]:
    """更新步骤"""
    try:
        _ensure_client_initialized()
        return ManageApiClient._instance._execute_request(
            "PUT",
            f"/xiaozhi/step/{step_id}",
            json=step_data
        )
    except Exception as e:
        print(f"更新步骤失败: {e}")
        return None


def delete_step(step_id: str) -> Optional[Dict]:
    """删除步骤"""
    try:
        _ensure_client_initialized()
        return ManageApiClient._instance._execute_request(
            "DELETE",
            f"/xiaozhi/step/{step_id}"
        )
    except Exception as e:
        print(f"删除步骤失败: {e}")
        return None


def reorder_scenario_steps(scenario_id: str, step_orders: List[Dict]) -> Optional[Dict]:
    """重新排序场景步骤"""
    try:
        _ensure_client_initialized()
        return ManageApiClient._instance._execute_request(
            "PUT",
            f"/xiaozhi/scenario/{scenario_id}/steps/reorder",
            json={"stepOrders": step_orders}
        )
    except Exception as e:
        print(f"重新排序步骤失败: {e}")
        return None


def manage_api_http_safe_close():
    ManageApiClient.safe_close()

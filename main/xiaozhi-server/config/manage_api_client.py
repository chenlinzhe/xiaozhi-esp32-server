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
        # NOTE(goody): 2025/4/16 http相关资源统一管理，后续可以增加线程池或者超时
        # 后续也可以统一配置apiToken之类的走通用的Auth
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


def manage_api_http_safe_close():
    ManageApiClient.safe_close()






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
        print(f"=== get_scenario_list 调试 ===")
        print(f"参数: agent_id={agent_id}, page={page}, limit={limit}, is_active={is_active}")

        _ensure_client_initialized()
        print("客户端已初始化")

        params = {"page": page, "limit": limit}
        if agent_id:
            params["agentId"] = agent_id
        if is_active is not None:
            params["isActive"] = 1 if is_active else 0

        print(f"请求参数: {params}")

        # 场景API使用密钥认证
        response = ManageApiClient._instance._execute_request(
            "GET",
            "/scenario/list",
            params=params
        )
        print(f"响应数据: {response}")

        if response is None:
            print(f"API请求失败或返回None")
            # 返回空列表而不是None，避免后续处理出错
            return {"list": [], "total": 0}

        return response
    except Exception as e:
        print(f"获取场景列表失败: {e}")
        import traceback
        traceback.print_exc()
        # 返回空列表而不是None，避免后续处理出错
        return {"list": [], "total": 0}


def get_scenario_by_id(scenario_id: str) -> Optional[Dict]:
    """根据ID获取场景"""
    try:
        print(f"=== get_scenario_by_id 调试 ===")
        print(f"场景ID: {scenario_id}")

        _ensure_client_initialized()
        print("客户端已初始化")

        result = ManageApiClient._instance._execute_request(
            "GET",
            f"/scenario/{scenario_id}"
        )
        print(f"API请求结果: {result}")

        if result is None:
            print("API返回None，场景不存在或认证失败")
            return None

        print(f"场景数据详情:")
        print(f"  - 场景ID: {result.get('id', 'N/A')}")
        print(f"  - 场景名称: {result.get('scenarioName', 'N/A')}")
        print(f"  - 是否活跃: {result.get('isActive', 'N/A')}")
        print(f"  - 代理ID: {result.get('agentId', 'N/A')}")
        return result
    except Exception as e:
        print(f"获取场景失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_scenario(scenario_data: Dict) -> Optional[Dict]:
    """创建场景"""
    try:
        _ensure_client_initialized()
        return ManageApiClient._instance._execute_request(
            "POST",
            "/scenario",
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
            f"/scenario/{scenario_id}",
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
            f"/scenario/{scenario_id}"
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
            f"/scenario-step/list/{scenario_id}"
        )
        if result:
            steps = result if isinstance(result, list) else result.get("data", [])
            if isinstance(steps, list):
                # 按stepOrder字段排序
                steps.sort(key=lambda x: x.get('stepOrder', 0))
            return steps
        return None
    except Exception as e:
        print(f"获取场景步骤失败: {e}")
        return None


def get_step_by_id(step_id: str) -> Optional[Dict]:
    """根据ID获取步骤"""
    try:
        _ensure_client_initialized()
        return ManageApiClient._instance._execute_request(
            "GET",
            f"/step/{step_id}"
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
            "/step",
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
            f"/step/{step_id}",
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
            f"/step/{step_id}"
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
            f"/scenario/{scenario_id}/steps/reorder",
            json={"stepOrders": step_orders}
        )
    except Exception as e:
        print(f"重新排序步骤失败: {e}")
        return None


def batch_save_scenario_steps(scenario_id: str, steps: List[Dict]) -> Optional[Dict]:
    """批量保存场景步骤"""
    try:
        _ensure_client_initialized()
        return ManageApiClient._instance._execute_request(
            "POST",
            f"/scenario-step/batch-save/{scenario_id}",
            json=steps
        )
    except Exception as e:
        print(f"批量保存场景步骤失败: {e}")
        return None


def delete_scenario_step(step_id: str) -> Optional[Dict]:
    """删除场景步骤"""
    try:
        _ensure_client_initialized()
        return ManageApiClient._instance._execute_request(
            "DELETE",
            f"/scenario-step/{step_id}"
        )
    except Exception as e:
        print(f"删除场景步骤失败: {e}")
        return None


def count_scenario_steps(scenario_id: str) -> Optional[int]:
    """获取场景步骤数量"""
    try:
        _ensure_client_initialized()
        result = ManageApiClient._instance._execute_request(
            "GET",
            f"/scenario-step/count/{scenario_id}"
        )
        return result if isinstance(result, int) else None
    except Exception as e:
        print(f"获取场景步骤数量失败: {e}")
        return None


# 步骤模板相关API
def get_step_templates() -> Optional[List[Dict]]:
    """获取步骤模板列表"""
    try:
        _ensure_client_initialized()
        return ManageApiClient._instance._execute_request(
            "GET",
            "/step-template/list"
        )
    except Exception as e:
        print(f"获取步骤模板列表失败: {e}")
        return None


def get_step_template_by_id(template_id: str) -> Optional[Dict]:
    """根据ID获取步骤模板"""
    try:
        _ensure_client_initialized()
        return ManageApiClient._instance._execute_request(
            "GET",
            f"/step-template/{template_id}"
        )
    except Exception as e:
        print(f"获取步骤模板失败: {e}")
        return None


def create_step_template(template_data: Dict) -> Optional[Dict]:
    """创建步骤模板"""
    try:
        _ensure_client_initialized()
        return ManageApiClient._instance._execute_request(
            "POST",
            "/step-template",
            json=template_data
        )
    except Exception as e:
        print(f"创建步骤模板失败: {e}")
        return None


def update_step_template(template_id: str, template_data: Dict) -> Optional[Dict]:
    """更新步骤模板"""
    try:
        _ensure_client_initialized()
        return ManageApiClient._instance._execute_request(
            "PUT",
            f"/step-template/{template_id}",
            json=template_data
        )
    except Exception as e:
        print(f"更新步骤模板失败: {e}")
        return None


def delete_step_template(template_id: str) -> Optional[Dict]:
    """删除步骤模板"""
    try:
        _ensure_client_initialized()
        return ManageApiClient._instance._execute_request(
            "DELETE",
            f"/step-template/{template_id}"
        )
    except Exception as e:
        print(f"删除步骤模板失败: {e}")
        return None


def get_step_templates_by_type(template_type: str) -> Optional[List[Dict]]:
    """根据类型获取步骤模板列表"""
    try:
        _ensure_client_initialized()
        return ManageApiClient._instance._execute_request(
            "GET",
            f"/step-template/type/{template_type}"
        )
    except Exception as e:
        print(f"根据类型获取步骤模板失败: {e}")
        return None


def get_default_step_templates() -> Optional[List[Dict]]:
    """获取默认步骤模板列表"""
    try:
        _ensure_client_initialized()
        return ManageApiClient._instance._execute_request(
            "GET",
            "/step-template/default"
        )
    except Exception as e:
        print(f"获取默认步骤模板失败: {e}")
        return None


def get_default_step_template_by_type(template_type: str) -> Optional[Dict]:
    """根据类型获取默认步骤模板"""
    try:
        _ensure_client_initialized()
        return ManageApiClient._instance._execute_request(
            "GET",
            f"/step-template/default/{template_type}"
        )
    except Exception as e:
        print(f"根据类型获取默认步骤模板失败: {e}")
        return None


# 儿童学习记录相关API
def get_learning_records(params: Dict = None) -> Optional[Dict]:
    """获取学习记录列表"""
    try:
        _ensure_client_initialized()
        return ManageApiClient._instance._execute_request(
            "GET",
            "/child-learning-record/list",
            params=params or {}
        )
    except Exception as e:
        print(f"获取学习记录列表失败: {e}")
        return None


def get_learning_record_by_id(record_id: str) -> Optional[Dict]:
    """根据ID获取学习记录"""
    try:
        _ensure_client_initialized()
        return ManageApiClient._instance._execute_request(
            "GET",
            f"/child-learning-record/{record_id}"
        )
    except Exception as e:
        print(f"获取学习记录失败: {e}")
        return None


def create_learning_record(record_data: Dict) -> Optional[Dict]:
    """创建学习记录"""
    try:
        _ensure_client_initialized()
        return ManageApiClient._instance._execute_request(
            "POST",
            "/child-learning-record",
            json=record_data
        )
    except Exception as e:
        print(f"创建学习记录失败: {e}")
        return None


def update_learning_record(record_id: str, record_data: Dict) -> Optional[Dict]:
    """更新学习记录"""
    try:
        _ensure_client_initialized()
        return ManageApiClient._instance._execute_request(
            "PUT",
            f"/child-learning-record/{record_id}",
            json=record_data
        )
    except Exception as e:
        print(f"更新学习记录失败: {e}")
        return None


def delete_learning_record(record_id: str) -> Optional[Dict]:
    """删除学习记录"""
    try:
        _ensure_client_initialized()
        return ManageApiClient._instance._execute_request(
            "DELETE",
            f"/child-learning-record/{record_id}"
        )
    except Exception as e:
        print(f"删除学习记录失败: {e}")
        return None


# 步骤消息列表相关API
def get_step_messages(step_id: str) -> Optional[List[Dict]]:
    """获取步骤消息列表"""
    try:
        _ensure_client_initialized()
        result = ManageApiClient._instance._execute_request(
            "GET",
            f"/step-message/list/{step_id}"
        )
        if result:
            messages = result if isinstance(result, list) else result.get("data", [])
            if isinstance(messages, list):
                # 按messageOrder字段排序
                messages.sort(key=lambda x: x.get('messageOrder', 0))
            return messages
        return None
    except Exception as e:
        print(f"获取步骤消息列表失败: {e}")
        return None


def batch_save_step_messages(step_id: str, messages: List[Dict]) -> Optional[Dict]:
    """批量保存步骤消息"""
    try:
        _ensure_client_initialized()
        return ManageApiClient._instance._execute_request(
            "POST",
            f"/step-message/batch-save/{step_id}",
            json=messages
        )
    except Exception as e:
        print(f"批量保存步骤消息失败: {e}")
        return None


def delete_step_messages(step_id: str) -> Optional[Dict]:
    """删除步骤的所有消息"""
    try:
        _ensure_client_initialized()
        return ManageApiClient._instance._execute_request(
            "DELETE",
            f"/step-message/step/{step_id}"
        )
    except Exception as e:
        print(f"删除步骤消息失败: {e}")
        return None


def count_step_messages(step_id: str) -> Optional[int]:
    """获取步骤消息数量"""
    try:
        _ensure_client_initialized()
        result = ManageApiClient._instance._execute_request(
            "GET",
            f"/step-message/count/{step_id}"
        )
        if result:
            return result.get("data", 0) if isinstance(result, dict) else result
        return 0
    except Exception as e:
        print(f"获取步骤消息数量失败: {e}")
        return 0


def get_learning_records_by_agent(agent_id: str) -> Optional[List[Dict]]:
    """根据智能体ID获取学习记录"""
    try:
        _ensure_client_initialized()
        return ManageApiClient._instance._execute_request(
            "GET",
            f"/child-learning-record/agent/{agent_id}"
        )
    except Exception as e:
        print(f"根据智能体ID获取学习记录失败: {e}")
        return None


def get_learning_records_by_scenario(scenario_id: str) -> Optional[List[Dict]]:
    """根据场景ID获取学习记录"""
    try:
        _ensure_client_initialized()
        return ManageApiClient._instance._execute_request(
            "GET",
            f"/child-learning-record/scenario/{scenario_id}"
        )
    except Exception as e:
        print(f"根据场景ID获取学习记录失败: {e}")
        return None


def get_learning_records_by_child(child_name: str) -> Optional[List[Dict]]:
    """根据儿童姓名获取学习记录"""
    try:
        _ensure_client_initialized()
        return ManageApiClient._instance._execute_request(
            "GET",
            f"/child-learning-record/child/{child_name}"
        )
    except Exception as e:
        print(f"根据儿童姓名获取学习记录失败: {e}")
        return None


def get_learning_statistics(agent_id: str, child_name: str) -> Optional[Dict]:
    """获取学习统计信息"""
    try:
        _ensure_client_initialized()
        return ManageApiClient._instance._execute_request(
            "GET",
            "/child-learning-record/statistics",
            params={"agentId": agent_id, "childName": child_name}
        )
    except Exception as e:
        print(f"获取学习统计信息失败: {e}")
        return None


def manage_api_http_safe_close():
    ManageApiClient.safe_close()
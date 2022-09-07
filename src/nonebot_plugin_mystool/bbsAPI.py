"""
### 米游社其他API
"""
import traceback
from typing import Dict, List, Literal, NewType, Tuple, Union

import httpx
import nonebot
import tenacity
from nonebot.log import logger

from .config import mysTool_config as conf
from .data import UserAccount
from .utils import (Subscribe, check_DS, check_login, custom_attempt_times,
                    generateDeviceID, generateDS, logger)

URL_ACTION_TICKET = "https://api-takumi.mihoyo.com/auth/api/getActionTicketBySToken?action_type=game_role&stoken={stoken}&uid={bbs_uid}"
URL_GAME_RECORD = "https://api-takumi-record.mihoyo.com/game_record/card/wapi/getGameRecordCard?uid={}"
URL_GAME_LIST = "https://bbs-api.mihoyo.com/apihub/api/getGameList"
URL_MYB = "https://api-takumi.mihoyo.com/common/homutreasure/v1/web/user/point?app_id=1&point_sn=myb"
URL_DEVICE_LOGIN = "https://bbs-api.mihoyo.com/apihub/api/deviceLogin"
URL_DEVICE_SAVE = "https://bbs-api.mihoyo.com/apihub/api/saveDevice"
URL_GENSHIN_STATUS_WIDGET = "https://api-takumi-record.mihoyo.com/game_record/app/card/api/getWidgetData?game_id=2"

HEADERS_ACTION_TICKET = {
    "Host": "api-takumi.mihoyo.com",
    "x-rpc-device_model": conf.device.X_RPC_DEVICE_MODEL_MOBILE,
    "User-Agent": conf.device.USER_AGENT_OTHER,
    "Referer": "https://webstatic.mihoyo.com/",
    "x-rpc-device_name": conf.device.X_RPC_DEVICE_NAME_MOBILE,
    "Origin": "https://webstatic.mihoyo.com",
    "Content-Length": "66",
    "Connection": "keep-alive",
    "x-rpc-channel": conf.device.X_RPC_CHANNEL,
    "x-rpc-app_version": conf.device.X_RPC_APP_VERSION,
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "DS": None,
    "x-rpc-device_id": None,
    "x-rpc-client_type": "5",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json;charset=utf-8",
    "Accept-Encoding": "gzip, deflate, br",
    "x-rpc-sys_version": conf.device.X_RPC_SYS_VERSION,
    "x-rpc-platform": conf.device.X_RPC_PLATFORM
}
HEADERS_GAME_RECORD = {
    "Host": "api-takumi-record.mihoyo.com",
    "Origin": "https://webstatic.mihoyo.com",
    "Connection": "keep-alive",
    "Accept": "application/json, text/plain, */*",
    "User-Agent": conf.device.USER_AGENT_MOBILE,
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "Referer": "https://webstatic.mihoyo.com/",
    "Accept-Encoding": "gzip, deflate, br"
}
HEADERS_GAME_LIST = {
    "Host": "bbs-api.mihoyo.com",
    "DS": None,
    "Accept": "*/*",
    "x-rpc-device_id": generateDeviceID(),
    "x-rpc-client_type": "1",
    "x-rpc-channel": conf.device.X_RPC_CHANNEL,
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "x-rpc-sys_version": conf.device.X_RPC_SYS_VERSION,
    "Referer": "https://app.mihoyo.com",
    "x-rpc-device_name": conf.device.X_RPC_DEVICE_NAME_MOBILE,
    "x-rpc-app_version": conf.device.X_RPC_APP_VERSION,
    "User-Agent": conf.device.USER_AGENT_OTHER,
    "Connection": "keep-alive",
    "x-rpc-device_model": conf.device.X_RPC_DEVICE_MODEL_MOBILE
}
HEADERS_MYB = {
    "Host": "api-takumi.mihoyo.com",
    "Origin": "https://webstatic.mihoyo.com",
    "Connection": "keep-alive",
    "Accept": "application/json, text/plain, */*",
    "User-Agent": conf.device.USER_AGENT_MOBILE,
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "Referer": "https://webstatic.mihoyo.com/",
    "Accept-Encoding": "gzip, deflate, br"
}
HEADERS_DEVICE = {
    "DS": None,
    "x-rpc-client_type": "2",
    "x-rpc-app_version": conf.device.X_RPC_APP_VERSION,
    "x-rpc-sys_version": conf.device.X_RPC_SYS_VERSION_ANDROID,
    "x-rpc-channel": conf.device.X_RPC_CHANNEL_ANDROID,
    "x-rpc-device_id": None,
    "x-rpc-device_name": conf.device.X_RPC_DEVICE_NAME_ANDROID,
    "x-rpc-device_model": conf.device.X_RPC_DEVICE_MODEL_ANDROID,
    "Referer": "https://app.mihoyo.com",
    "Content-Type": "application/json; charset=UTF-8",
    "Host": "bbs-api.mihoyo.com",
    "Connection": "Keep-Alive",
    "Accept-Encoding": "gzip",
    "User-Agent": conf.device.USER_AGENT_ANDROID_OTHER
}
HEADERS_GENSHIN_STATUS_WIDGET = {
    "Host": "api-takumi-record.mihoyo.com",
    "DS": None,
    "Accept": "*/*",
    "x-rpc-device_id": None,
    "x-rpc-client_type": "1",
    "x-rpc-channel": "appstore",
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "x-rpc-device_model": conf.device.X_RPC_DEVICE_MODEL_MOBILE,
    "Referer": "https://app.mihoyo.com",
    "x-rpc-device_name": conf.device.X_RPC_DEVICE_NAME_MOBILE,
    "x-rpc-app_version": conf.device.X_RPC_APP_VERSION,
    "User-Agent": conf.device.USER_AGENT_WIDGET,
    "Connection": "keep-alive",
    "x-rpc-sys_version": conf.device.X_RPC_SYS_VERSION
}


class BaseData:
    def __init__(self, data_dict: dict, error_info: str = "初始化对象: dict数据不正确") -> None:
        self.dict = data_dict
        try:
            for func in dir(self):
                if func.startswith("__"):
                    continue
                getattr(self, func)
        except KeyError or TypeError:
            logger.error(f"{conf.LOG_HEAD}{error_info}")
            logger.debug(f"{conf.LOG_HEAD}{traceback.format_exc()}")


class GameRecord(BaseData):
    """
    用户游戏数据
    """

    def __init__(self, gameRecord_dict: dict) -> None:
        BaseData.__init__(self, gameRecord_dict, "用户游戏数据 - 初始化对象: dict数据不正确")

    @property
    def regionName(self) -> str:
        """
        服务器区名
        """
        return self.dict["region_name"]

    @property
    def gameID(self) -> str:
        """
        游戏ID
        """
        return self.dict["game_id"]

    @property
    def level(self) -> str:
        """
        用户游戏等级
        """
        return self.dict["level"]

    @property
    def region(self) -> str:
        """
        服务器区号
        """
        return self.dict["region"]

    @property
    def uid(self) -> str:
        """
        用户游戏UID
        """
        return self.dict["game_role_id"]

    @property
    def nickname(self) -> str:
        """
        用户游戏昵称
        """
        return self.dict["nickname"]


class GameInfo(BaseData):
    """
    游戏信息数据
    """
    Abbr = NewType("Abbr", str)
    Full_Name = NewType("Full_Name", str)
    ABBR_TO_ID: Dict[int, Tuple[Abbr, Full_Name]] = {}
    '''
    游戏ID(gameID)与缩写和全称的对应关系
    >>> {游戏ID, (缩写, 全称)}
    '''

    def __init__(self, gameInfo_dict: dict) -> None:
        BaseData.__init__(self, gameInfo_dict, "游戏信息数据 - 初始化对象: dict数据不正确")

    @property
    def gameID(self) -> int:
        """
        游戏ID
        """
        return self.dict["id"]

    @property
    def appIcon(self) -> str:
        """
        游戏App图标链接(大)
        """
        return self.dict["app_icon"]

    @property
    def opName(self) -> str:
        """
        游戏代号(英文数字, 例如hk4e)
        """
        return self.dict["op_name"]

    @property
    def enName(self) -> str:
        """
        游戏代号2(英文数字, 例如ys)
        """
        return self.dict["en_name"]

    @property
    def miniIcon(self) -> str:
        """
        游戏图标链接(圆形, 小)
        """
        return self.dict["icon"]

    @property
    def name(self) -> str:
        """
        游戏名称
        """
        return self.dict["name"]


class GenshinStatus:
    """
    原神实时便笺数据
    """

    def __init__(self) -> None:
        self.name = None
        '''游戏昵称'''
        self.gameUID = None
        '''游戏UID'''
        self.region = None
        '''游戏区服(如 "cn_gf01")'''
        self.level = None
        '''游戏等级'''
        self.resin = None
        '''当前树脂数量'''
        self.expedition = None
        '''探索派遣 `(进行中, 最多派遣数)`'''
        self.task = None
        '''每日委托完成数'''
        self.coin = None
        '''洞天财瓮 `(未收取, 最多可容纳宝钱数)`'''

    def fromWidget(self, widget_dict):
        self.dict = widget_dict

        try:
            self.name: str = widget_dict["nickname"]
            self.gameUID: str = widget_dict["game_role_id"]
            self.region: str = widget_dict["region"]
            self.level: int = widget_dict["level"]

            for status in widget_dict["data"]:
                data: Tuple[int, int] = tuple(
                    [int(value) for value in status["value"].split("/")])
                if status["name"] == "原粹树脂":
                    self.resin = data[0]
                elif status["name"] == "探索派遣":
                    self.expedition = data
                elif status["name"] == "每日委托进度":
                    self.task = data[0]
                elif status["name"] == "洞天财瓮":
                    self.coin = data
        except KeyError or TypeError:
            logger.error(f"{conf.LOG_HEAD}原神实时便笺数据 - 从小组件请求初始化对象: dict数据不正确")
            logger.debug(f"{conf.LOG_HEAD}{traceback.format_exc()}")

    def fromBBS(self, bbs_dict):
        ...


async def get_action_ticket(account: UserAccount, retry: bool = True) -> Union[str, Literal[-1, -2, -3]]:
    """
    获取ActionTicket，返回str

    参数:
        `account`: 用户账户数据
        `retry`: 是否允许重试

    - 若返回 `-1` 说明用户登录失效
    - 若返回 `-2` 说明服务器没有正确返回
    - 若返回 `-3` 说明请求失败
    """
    headers = HEADERS_ACTION_TICKET.copy()
    headers["DS"] = generateDS()
    index = 0
    try:
        async for attempt in tenacity.AsyncRetrying(stop=custom_attempt_times(retry), reraise=True, wait=tenacity.wait_fixed(conf.SLEEP_TIME_RETRY)):
            with attempt:
                async with httpx.AsyncClient() as client:
                    res = await client.get(URL_ACTION_TICKET.format(stoken=account.cookie["stoken"], bbs_uid=account.bbsUID), headers=headers, cookies=account.cookie, timeout=conf.TIME_OUT)
                if not check_login(res.text):
                    logger.info(conf.LOG_HEAD +
                                "获取ActionTicket - 用户 {} 登录失效".format(account.phone))
                    logger.debug(conf.LOG_HEAD + "网络请求返回: {}".format(res.text))
                    return -1
                if not check_DS(res.text):
                    logger.info(conf.LOG_HEAD +
                                "获取ActionTicket - DS无效，正在在线获取salt以重新生成...")
                    sub = Subscribe()
                    conf.SALT_IOS = await sub.get(
                        ("Config", "SALT_IOS"), index)
                    conf.device.USER_AGENT_MOBILE = await sub.get(
                        ("DeviceConfig", "USER_AGENT_MOBILE"), index)
                    headers["User-Agent"] = conf.device.USER_AGENT_MOBILE
                    index += 1
                    headers["DS"] = generateDS()
                return res.json()["data"]["ticket"]
    except KeyError:
        logger.error(conf.LOG_HEAD + "获取ActionTicket - 服务器没有正确返回")
        logger.debug(conf.LOG_HEAD + "网络请求返回: {}".format(res.text))
        logger.debug(conf.LOG_HEAD + traceback.format_exc())
        return -2
    except Exception:
        logger.error(conf.LOG_HEAD + "获取ActionTicket - 请求失败")
        logger.debug(conf.LOG_HEAD + traceback.format_exc())
        return -3


async def get_game_record(account: UserAccount, retry: bool = True) -> Union[List[GameRecord], Literal[-1, -2, -3]]:
    """
    获取用户绑定的游戏账户信息，返回一个GameRecord对象的列表

    参数:
        `account`: 用户账户数据
        `retry`: 是否允许重试

    - 若返回 `-1` 说明用户登录失效
    - 若返回 `-2` 说明服务器没有正确返回
    - 若返回 `-3` 说明请求失败
    """
    record_list = []
    try:
        async for attempt in tenacity.AsyncRetrying(stop=custom_attempt_times(retry), reraise=True, wait=tenacity.wait_fixed(conf.SLEEP_TIME_RETRY)):
            with attempt:
                async with httpx.AsyncClient() as client:
                    res = await client.get(URL_GAME_RECORD.format(account.bbsUID), headers=HEADERS_GAME_RECORD, cookies=account.cookie, timeout=conf.TIME_OUT)
                if not check_login(res.text):
                    logger.info(conf.LOG_HEAD +
                                "获取用户游戏数据 - 用户 {} 登录失效".format(account.phone))
                    logger.debug(conf.LOG_HEAD + "网络请求返回: {}".format(res.text))
                    return -1
                for record in res.json()["data"]["list"]:
                    record_list.append(GameRecord(record))
                return record_list
    except KeyError:
        logger.error(conf.LOG_HEAD + "获取用户游戏数据 - 服务器没有正确返回")
        logger.debug(conf.LOG_HEAD + "网络请求返回: {}".format(res.text))
        logger.debug(conf.LOG_HEAD + traceback.format_exc())
        return -2
    except Exception:
        logger.error(conf.LOG_HEAD + "获取用户游戏数据 - 请求失败")
        logger.debug(conf.LOG_HEAD + traceback.format_exc())
        return -3


async def get_game_list(retry: bool = True) -> Union[List[GameInfo], None]:
    """
    获取米哈游游戏的详细信息，若返回`None`说明获取失败

    参数:
        `retry`: 是否允许重试
    """
    headers = HEADERS_GAME_LIST.copy()
    headers["DS"] = generateDS()
    info_list = []
    try:
        async for attempt in tenacity.AsyncRetrying(stop=custom_attempt_times(retry), reraise=True, wait=tenacity.wait_fixed(conf.SLEEP_TIME_RETRY)):
            with attempt:
                async with httpx.AsyncClient() as client:
                    res = await client.get(URL_GAME_LIST, headers=headers, timeout=conf.TIME_OUT)
                for info in res.json()["data"]["list"]:
                    info_list.append(GameInfo(info))
                return info_list
    except KeyError:
        logger.error(conf.LOG_HEAD + "获取游戏信息 - 服务器没有正确返回")
        logger.debug(conf.LOG_HEAD + "网络请求返回: {}".format(res.text))
        logger.debug(conf.LOG_HEAD + traceback.format_exc())
    except Exception:
        logger.error(conf.LOG_HEAD + "获取游戏信息 - 请求失败")
        logger.debug(conf.LOG_HEAD + traceback.format_exc())


async def get_user_myb(account: UserAccount, retry: bool = True) -> Union[int, Literal[-1, -2, -3]]:
    """
    获取用户当前米游币数量

    参数:
        `account`: 用户账户数据
        `retry`: 是否允许重试

    - 若返回 `-1` 说明用户登录失效
    - 若返回 `-2` 说明服务器没有正确返回
    - 若返回 `-3` 说明请求失败
    """
    try:
        async for attempt in tenacity.AsyncRetrying(stop=custom_attempt_times(retry), reraise=True, wait=tenacity.wait_fixed(conf.SLEEP_TIME_RETRY)):
            with attempt:
                async with httpx.AsyncClient() as client:
                    res = await client.get(URL_MYB, headers=HEADERS_MYB, cookies=account.cookie, timeout=conf.TIME_OUT)
                if not check_login(res.text):
                    logger.info(conf.LOG_HEAD +
                                "获取用户米游币 - 用户 {} 登录失效".format(account.phone))
                    logger.debug(conf.LOG_HEAD + "网络请求返回: {}".format(res.text))
                    return -1
                return int(res.json()["data"]["points"])
    except KeyError or ValueError:
        logger.error(conf.LOG_HEAD + "获取用户米游币 - 服务器没有正确返回")
        logger.debug(conf.LOG_HEAD + "网络请求返回: {}".format(res.text))
        logger.debug(conf.LOG_HEAD + traceback.format_exc())
        return -2
    except Exception:
        logger.error(conf.LOG_HEAD + "获取用户米游币 - 请求失败")
        logger.debug(conf.LOG_HEAD + traceback.format_exc())
        return -3


async def device_login(account: UserAccount, retry: bool = True) -> Literal[1, -1, -2, -3]:
    """
    设备登录(deviceLogin)(适用于安卓设备)

    参数:
        `account`: 用户账户数据
        `retry`: 是否允许重试

    - 若返回 `1` 说明成功
    - 若返回 `-1` 说明用户登录失效
    - 若返回 `-2` 说明服务器没有正确返回
    - 若返回 `-3` 说明请求失败
    """
    data = {
        "app_version": conf.device.X_RPC_APP_VERSION,
        "device_id": account.deviceID_2,
        "device_name": conf.device.X_RPC_DEVICE_NAME_ANDROID,
        "os_version": "30",
        "platform": "Android",
        "registration_id": "1a0018970a5c00e814d"
    }
    headers = HEADERS_DEVICE.copy()
    headers["DS"] = generateDS(data)
    headers["x-rpc-device_id"] = account.deviceID_2
    try:
        async for attempt in tenacity.AsyncRetrying(stop=custom_attempt_times(retry), reraise=True, wait=tenacity.wait_fixed(conf.SLEEP_TIME_RETRY)):
            with attempt:
                async with httpx.AsyncClient() as client:
                    res = await client.post(URL_DEVICE_LOGIN, headers=headers, json=data, cookies=account.cookie, timeout=conf.TIME_OUT)
                if not check_login(res.text):
                    logger.info(conf.LOG_HEAD +
                                "设备登录 - 用户 {} 登录失效".format(account.phone))
                    logger.debug(conf.LOG_HEAD + "网络请求返回: {}".format(res.text))
                    return -1
                if res.json()["message"] != "OK":
                    raise ValueError
                else:
                    return 1
    except KeyError or ValueError:
        logger.error(conf.LOG_HEAD + "设备登录 - 服务器没有正确返回")
        logger.debug(conf.LOG_HEAD + "网络请求返回: {}".format(res.text))
        logger.debug(conf.LOG_HEAD + traceback.format_exc())
        return -2
    except Exception:
        logger.error(conf.LOG_HEAD + "设备登录 - 请求失败")
        logger.debug(conf.LOG_HEAD + traceback.format_exc())
        return -3


async def device_save(account: UserAccount, retry: bool = True) -> Literal[1, -1, -2, -3]:
    """
    设备保存(saveDevice)(适用于安卓设备)

    参数:
        `account`: 用户账户数据
        `retry`: 是否允许重试

    - 若返回 `1` 说明成功
    - 若返回 `-1` 说明用户登录失效
    - 若返回 `-2` 说明服务器没有正确返回
    - 若返回 `-3` 说明请求失败
    """
    data = {
        "app_version": conf.device.X_RPC_APP_VERSION,
        "device_id": account.deviceID_2,
        "device_name": conf.device.X_RPC_DEVICE_NAME_ANDROID,
        "os_version": "30",
        "platform": "Android",
        "registration_id": "1a0018970a5c00e814d"
    }
    headers = HEADERS_DEVICE.copy()
    headers["DS"] = generateDS(data)
    headers["x-rpc-device_id"] = account.deviceID_2
    try:
        async for attempt in tenacity.AsyncRetrying(stop=custom_attempt_times(retry), reraise=True, wait=tenacity.wait_fixed(conf.SLEEP_TIME_RETRY)):
            with attempt:
                async with httpx.AsyncClient() as client:
                    res = await client.post(URL_DEVICE_SAVE, headers=headers, json=data, cookies=account.cookie, timeout=conf.TIME_OUT)
                if not check_login(res.text):
                    logger.info(conf.LOG_HEAD +
                                "设备保存 - 用户 {} 登录失效".format(account.phone))
                    logger.debug(conf.LOG_HEAD + "网络请求返回: {}".format(res.text))
                    return -1
                if res.json()["message"] != "OK":
                    raise ValueError
                else:
                    return 1
    except KeyError or ValueError:
        logger.error(conf.LOG_HEAD + "设备保存 - 服务器没有正确返回")
        logger.debug(conf.LOG_HEAD + "网络请求返回: {}".format(res.text))
        logger.debug(conf.LOG_HEAD + traceback.format_exc())
        return -2
    except Exception:
        logger.error(conf.LOG_HEAD + "设备保存 - 请求失败")
        logger.debug(conf.LOG_HEAD + traceback.format_exc())
        return -3


async def genshin_status_widget(account: UserAccount, retry: bool = True):
    """
    获取原神实时便笺
    """
    headers = HEADERS_GENSHIN_STATUS_WIDGET.copy()
    headers["DS"] = generateDS()
    headers["x-rpc-device_id"] = account.deviceID
    try:
        index = 0
        async for attempt in tenacity.AsyncRetrying(stop=custom_attempt_times(retry), reraise=True, wait=tenacity.wait_fixed(conf.SLEEP_TIME_RETRY)):
            with attempt:
                async with httpx.AsyncClient() as client:
                    res = await client.get(URL_GENSHIN_STATUS_WIDGET, headers=headers, cookies=account.cookie, timeout=conf.TIME_OUT)
                if not check_login(res.text):
                    logger.info(conf.LOG_HEAD +
                                "原神实时便笺 - 用户 {} 登录失效".format(account.phone))
                    logger.debug(conf.LOG_HEAD + "网络请求返回: {}".format(res.text))
                    return -1
                if not check_DS(res.text):
                    logger.info(conf.LOG_HEAD +
                                "原神实时便笺 - DS无效，正在在线获取salt以重新生成...")
                    conf.SALT_IOS = await Subscribe().get(
                        ("Config", "SALT_IOS"), index)
                    index += 1
                    headers["DS"] = generateDS()
                if res.json()["message"] != "OK":
                    raise ValueError
                else:
                    return 1
    except KeyError or ValueError:
        logger.error(conf.LOG_HEAD + "原神实时便笺 - 服务器没有正确返回")
        logger.debug(conf.LOG_HEAD + "网络请求返回: {}".format(res.text))
        logger.debug(conf.LOG_HEAD + traceback.format_exc())
        return -2
    except Exception:
        logger.error(conf.LOG_HEAD + "原神实时便笺 - 请求失败")
        logger.debug(conf.LOG_HEAD + traceback.format_exc())
        return -3


driver = nonebot.get_driver()


@driver.on_startup
async def set_game_list():
    """
    设置游戏ID(gameID)与缩写和全称的对应关系
    """
    game_list = await get_game_list()
    if game_list is None:
        return
    for game in game_list:
        if game.name == "原神":
            GameInfo.ABBR_TO_ID.setdefault(game.gameID, ("ys", game.name))
        elif game.name == "崩坏3":
            GameInfo.ABBR_TO_ID.setdefault(game.gameID, ("bh3", game.name))
        elif game.name == "崩坏学园2":
            GameInfo.ABBR_TO_ID.setdefault(game.gameID, ("bh2", game.name))
        elif game.name == "未定事件簿":
            GameInfo.ABBR_TO_ID.setdefault(game.gameID, ("wd", game.name))
        elif game.name == "大别野":
            GameInfo.ABBR_TO_ID.setdefault(game.gameID, ("bbs", game.name))
        elif game.name == "崩坏：星穹铁道":
            GameInfo.ABBR_TO_ID.setdefault(game.gameID, ("xq", game.name))
        elif game.name == "绝区零":
            GameInfo.ABBR_TO_ID.setdefault(game.gameID, ("jql", game.name))

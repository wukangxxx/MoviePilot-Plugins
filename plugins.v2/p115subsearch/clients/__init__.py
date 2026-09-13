"""
客户端模块
包含115网盘、PanSou、Nullbr、癫影（Dian115）等客户端
"""
from .p115 import P115ClientManager
from .pansou import PanSouClient
from .nullbr import NullbrClient
from .hdhive import HDHiveOpenAPIClient, HDHiveOpenAPIError
from .kdocs import KDocsClient, KDocsError
from .dian115 import Dian115Client, Dian115Error

__all__ = [
    "P115ClientManager",
    "PanSouClient",
    "NullbrClient",
    "HDHiveOpenAPIClient",
    "HDHiveOpenAPIError",
    "KDocsClient",
    "KDocsError",
    "Dian115Client",
    "Dian115Error"
]

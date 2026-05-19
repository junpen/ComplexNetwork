"""
达梦数据库（DM）连接管理器模块。

本模块定义了 DMConnectionManager 类，提供对达梦数据库的统一连接管理，
采用单例模式确保全局共享同一数据库连接。

主要功能：
- 单例模式管理数据库连接，避免重复创建连接
- 自动连接检测与断线重连机制
- 支持查询（execute_query）、更新（execute_update）、批量执行（execute_many）
- 表存在性检查（支持 DBA_TABLES 和 USER_TABLES 两种视图）
- 连接参数从 config 模块的 DM_DATABASE 配置中读取
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# 尝试导入达梦数据库 Python 驱动，若未安装则标记为不可用
try:
    import dmPython
    DM_AVAILABLE = True
except ImportError:
    DM_AVAILABLE = False
    logger.warning("dmPython未安装，数据库功能不可用。请执行: pip install dmPython")

# 从配置文件导入数据库连接参数
from config import DM_DATABASE


class DMConnectionManager:
    """
    达梦数据库连接管理器（单例模式）。

    确保整个应用生命周期中只存在一个数据库连接实例。
    提供 SQL 查询、更新、批量执行等数据库操作方法，
    并内置断线自动重连机制。

    使用方式：
        # 获取全局单例实例
        from src.database.dm_manager import db
        rows = db.execute_query("SELECT * FROM MY_TABLE")

    类属性：
        _instance: 单例实例
        _connection: 底层数据库连接对象
    """

    _instance: Optional["DMConnectionManager"] = None
    _connection = None

    def __new__(cls):
        """
        单例模式实现：确保只创建一个 DMConnectionManager 实例。

        Returns:
            DMConnectionManager 的唯一实例
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def is_available(self) -> bool:
        """
        检查达梦数据库驱动是否可用。

        Returns:
            True 表示 dmPython 已安装且可用，False 表示不可用
        """
        return DM_AVAILABLE

    def connect(self, host: str = None, port: int = None,
                user: str = None, password: str = None):
        """
        建立达梦数据库连接。

        连接参数优先使用传入的参数，若未指定则从 config 模块的 DM_DATABASE 配置中读取。
        若已有连接存在，会先关闭旧连接再建立新连接。

        Args:
            host: 数据库主机地址，若为 None 则使用配置文件中的值
            port: 数据库端口号，若为 None 则使用配置文件中的值
            user: 数据库用户名，若为 None 则使用配置文件中的值
            password: 数据库密码，若为 None 则使用配置文件中的值

        Returns:
            数据库连接对象

        Raises:
            RuntimeError: dmPython 未安装时抛出
        """
        if not DM_AVAILABLE:
            raise RuntimeError("dmPython未安装，无法连接达梦数据库")

        # 合并参数：优先使用传入值，否则使用配置文件中的默认值
        cfg = {
            "host": host or DM_DATABASE["host"],
            "port": port or DM_DATABASE["port"],
            "user": user or DM_DATABASE["user"],
            "password": password or DM_DATABASE["password"],
        }

        # 关闭已有连接，防止连接泄漏
        if self._connection is not None:
            try:
                self._connection.close()
            except Exception:
                pass

        logger.info(f"正在连接DM数据库 {cfg['user']}@{cfg['host']}:{cfg['port']}")
        self._connection = dmPython.connect(
            user=cfg["user"],
            password=cfg["password"],
            server=cfg["host"],
            port=cfg["port"],
        )
        logger.info("DM数据库连接成功")
        return self._connection

    def get_connection(self):
        """
        获取有效的数据库连接。

        实现了断线自动重连机制：
        1. 若连接尚未建立，自动调用 connect() 创建连接
        2. 若连接已建立但已断开（通过执行 SELECT 1 FROM DUAL 探测），
           则自动重新连接

        Returns:
            有效的数据库连接对象
        """
        if self._connection is None:
            # 首次获取连接，自动建立
            self.connect()
        try:
            # 心跳检测：执行简单查询判断连接是否仍然有效
            cursor = self._connection.cursor()
            cursor.execute("SELECT 1 FROM DUAL")
            cursor.close()
        except Exception:
            # 连接已断开，自动重连
            logger.info("数据库连接已断开，尝试重连...")
            self._connection = None
            self.connect()
        return self._connection

    def execute_query(self, sql: str, params: tuple = None):
        """
        执行 SQL 查询并返回结果列表。

        查询结果会自动转换为字典列表格式，每行数据为一个字典（列名 -> 值）。
        对于包含 LOB/CLOB 类型的大字段，会自动调用 read() 方法读取内容。

        Args:
            sql: SQL 查询语句
            params: 查询参数元组，用于参数化查询，默认为 None

        Returns:
            查询结果列表，每个元素为 {列名: 值} 形式的字典
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # 执行参数化或非参数化查询
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            # 提取列名信息
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            # 将每行数据转换为字典格式
            result = []
            for row in rows:
                row_dict = {}
                for i, col in enumerate(columns):
                    val = row[i]
                    # 处理 LOB/CLOB 等大字段类型：通过 read() 方法读取完整内容
                    if hasattr(val, "read"):
                        val = val.read()
                    row_dict[col] = val
                result.append(row_dict)
            return result
        finally:
            # 确保游标始终被关闭，防止资源泄漏
            cursor.close()

    def execute_update(self, sql: str, params: tuple = None):
        """
        执行 SQL 更新操作（INSERT/UPDATE/DELETE）。

        执行成功后自动提交事务，失败时自动回滚。

        Args:
            sql: SQL 更新语句
            params: 更新参数元组，用于参数化操作，默认为 None

        Returns:
            受影响的行数

        Raises:
            Exception: 执行失败时抛出异常（已自动回滚）
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            # 成功后提交事务
            conn.commit()
            return cursor.rowcount
        except Exception as e:
            # 失败时回滚事务
            conn.rollback()
            raise e
        finally:
            cursor.close()

    def execute_many(self, sql: str, params_list: list):
        """
        批量执行 SQL 操作。

        使用相同的 SQL 模板，依次执行多组参数。
        所有操作在同一个事务中执行，全部成功才提交，任一失败则全部回滚。

        Args:
            sql: SQL 语句模板（包含占位符）
            params_list: 参数列表，每个元素为一组参数元组

        Returns:
            成功执行的参数组数

        Raises:
            Exception: 任一操作失败时抛出异常（已自动回滚全部操作）
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # 逐条执行参数化 SQL
            for params in params_list:
                cursor.execute(sql, params)
            # 全部执行成功后统一提交
            conn.commit()
            return len(params_list)
        except Exception as e:
            # 任一失败则回滚全部操作
            conn.rollback()
            raise e
        finally:
            cursor.close()

    def table_exists(self, table_name: str) -> bool:
        """
        检查指定名称的表是否存在于数据库中。

        采用两阶段检查策略：
        1. 首先尝试通过 DBA_TABLES 视图查询（需要 DBA 权限）
        2. 若失败则回退到 USER_TABLES 视图查询（仅查当前用户的表）

        Args:
            table_name: 要检查的表名（不区分大小写）

        Returns:
            True 表示表存在，False 表示表不存在或查询失败
        """
        # 第一阶段：通过 DBA_TABLES 视图查询（需要 DBA 权限）
        sql = ("SELECT COUNT(*) AS CNT FROM DBA_TABLES "
               "WHERE OWNER = :1 AND TABLE_NAME = :2")
        try:
            result = self.execute_query(sql, (DM_DATABASE["schema"], table_name.upper()))
            return result[0]["CNT"] > 0 if result else False
        except Exception:
            # DBA 权限不足，回退到 USER_TABLES 视图
            try:
                sql2 = ("SELECT COUNT(*) AS CNT FROM USER_TABLES "
                         "WHERE TABLE_NAME = :1")
                result = self.execute_query(sql2, (table_name.upper(),))
                return result[0]["CNT"] > 0 if result else False
            except Exception:
                return False

    def close(self):
        """
        关闭数据库连接并释放资源。

        安全关闭连接，忽略关闭过程中可能出现的异常。
        """
        if self._connection:
            try:
                self._connection.close()
            except Exception:
                pass
            self._connection = None

    def __del__(self):
        """
        析构函数：在对象被垃圾回收时自动关闭数据库连接。

        确保即使未显式调用 close()，也能在对象销毁时释放连接资源。
        """
        self.close()


# 全局单例实例，供其他模块直接导入使用
# 用法：from src.database.dm_manager import db
db = DMConnectionManager()

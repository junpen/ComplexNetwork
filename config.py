"""
全局配置文件
============

本模块定义了多源异构文书流转分析模型的所有全局配置项，包括：
  - 数据库连接参数（DM达梦数据库）
  - 默认数据源类型
  - 分析模块的配置参数
"""

# 文件默认编码格式
DEFAULT_ENCODING = "utf-8"

# DM达梦数据库连接配置
DM_DATABASE = {
    "host": "localhost",        # 数据库服务器地址
    "port": 5236,               # 数据库端口号（达梦数据库默认端口）
    "user": "SYSDBA",           # 数据库用户名（SYSDBA为达梦默认管理员账户）
    "password": "ADmin12345",   # 数据库密码
    "schema": "NETWORKX",       # 数据库模式（Schema）名称
}

# 默认数据源类型："database" 表示从DM达梦数据库加载，其他值则从文件加载
DATA_SOURCE = "database"

# 分析模块配置参数
ANALYSIS_CONFIG = {
    "default_top_n": 10,                                              # 默认返回排名前N的节点数量
    "random_seed": 42,                                                # 随机种子，确保分析结果可复现
    "simulation_iterations": 500,                                     # 攻击模拟的默认迭代次数
    "attack_strategies": ["random", "degree", "betweenness", "pagerank"],  # 支持的攻击策略列表
}

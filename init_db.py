#!/usr/bin/env python3
"""
DM达梦数据库初始化脚本
======================

本模块用于初始化DM达梦数据库，为多源异构文书流转分析模型创建所需的数据库结构。
主要执行以下操作：
  1. 创建 NETWORKX 模式（Schema），如果不存在则新建
  2. 创建 NETWORK_EDGES 边表，存储网络中的边（关系）数据
  3. 导入军事文电示例数据，用于演示和测试

设计说明：
  - 仅创建 NETWORK_EDGES 边表，不创建独立的节点表
  - 节点由 SOURCE_NODE + TARGET_NODE 字段自动提取并去重
  - 支持通过命令行参数控制是否重建（--drop）和数据库连接信息

依赖：
  - dmPython：达梦数据库Python驱动，需通过 pip install dmPython 安装
"""

import sys
import os

# 将当前脚本所在目录加入系统路径，确保可以正确引用本地配置模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import DM_DATABASE

# 边表建表SQL语句
# 字段说明：
#   EDGE_ID      - 边ID，自增主键
#   SOURCE_NODE  - 源节点名称（如"指挥员_刘司令员"）
#   TARGET_NODE  - 目标节点，支持顿号分隔的多个节点（如"部队_步兵第1团、部队_装甲第2营"）
#   EDGE_TYPE    - 边类型（如"指挥"、"协作"、"传输至"等）
#   WEIGHT       - 边权重，默认1.0
#   ATTRIBUTES   - 扩展属性，JSON格式存储（CLOB大字段类型）
#   SOURCE_TYPE  - 数据来源类型标识，默认'database'
#   RECEIVE_TIME - 接收/记录时间戳
CREATE_EDGES_TABLE = """
CREATE TABLE "{schema}"."NETWORK_EDGES" (
    EDGE_ID      INT IDENTITY(1,1) NOT NULL,
    SOURCE_NODE  VARCHAR(128)  NOT NULL,
    TARGET_NODE  VARCHAR(1024) NOT NULL,
    EDGE_TYPE    VARCHAR(64)   NOT NULL,
    WEIGHT       DECIMAL(10,2) DEFAULT 1.0,
    ATTRIBUTES   CLOB,
    SOURCE_TYPE  VARCHAR(64)   DEFAULT 'database',
    RECEIVE_TIME TIMESTAMP     DEFAULT NULL,
    PRIMARY KEY (EDGE_ID)
)
"""

# 删除旧表的SQL语句列表
# 包含三个历史表（NETWORK_NODES、NETWORK_METADATA、NETWORK_EDGES）
# 用于在需要完全重建数据库时清理旧数据
DROP_TABLES_SQL = [
    'DROP TABLE "{schema}"."NETWORK_NODES" CASCADE',
    'DROP TABLE "{schema}"."NETWORK_METADATA" CASCADE',
    'DROP TABLE "{schema}"."NETWORK_EDGES" CASCADE',
]

# 示例边数据列表
# 每条记录格式为：(源节点, 目标节点, 边类型, 权重, 扩展属性JSON, 数据来源, 时间)
# 数据描述了一个军事指挥网络的层级关系、通信关系和行动参与关系
SAMPLE_EDGES = [
    # ===== 指挥员之间的协作关系 =====
    ("指挥员_刘司令员", "指挥员_王副司令", "协作", 8.0, "{}", "军事数据库", "2025-06-01 08:00:00"),
    ("指挥员_刘司令员", "指挥员_张参谋长", "协作", 9.0, "{}", "军事数据库", "2025-06-01 08:15:00"),
    # ===== 指挥员对部队的指挥关系 =====
    ("指挥员_刘司令员", "部队_步兵第1团", "指挥", 10.0, "{}", "军事数据库", "2025-06-01 09:00:00"),
    ("指挥员_王副司令", "部队_装甲第2营", "指挥", 8.0, "{}", "军事数据库", "2025-06-01 09:30:00"),
    ("指挥员_张参谋长", "部队_炮兵第3连", "指挥", 5.0, "{}", "军事数据库", "2025-06-01 10:00:00"),
    ("指挥员_张参谋长", "部队_工兵连", "指挥", 3.0, "{}", "军事数据库", "2025-06-01 10:20:00"),
    # ===== 部队之间的隶属关系 =====
    ("部队_步兵第1团", "部队_装甲第2营、部队_炮兵第3连", "隶属", 5.0, "{}", "军事数据库", "2025-06-01 11:00:00"),
    # ===== 部队对武器装备的部署关系 =====
    ("部队_装甲第2营", "武器_ZTZ99坦克连", "部署", 6.0, "{}", "军事数据库", "2025-06-02 08:00:00"),
    ("部队_炮兵第3连", "武器_PLZ05榴弹炮", "部署", 6.0, "{}", "军事数据库", "2025-06-02 08:30:00"),
    ("部队_侦察排", "武器_无人机侦察连", "部署", 4.0, "{}", "军事数据库", "2025-06-02 09:00:00"),
    # ===== 部队对阵地/设施的驻扎关系 =====
    ("部队_步兵第1团", "阵地_302高地", "驻扎于", 5.0, "{}", "军事数据库", "2025-06-02 10:00:00"),
    ("部队_工兵连", "阵地_青龙江渡口", "驻扎于", 3.0, "{}", "军事数据库", "2025-06-02 10:30:00"),
    ("部队_炮兵第3连", "阵地_北山阵地", "驻扎于", 2.0, "{}", "军事数据库", "2025-06-02 11:00:00"),
    ("设施_一号通信站", "指挥员_刘司令员", "驻扎于", 2.0, "{}", "军事数据库", "2025-06-02 14:00:00"),
    ("设施_后勤补给点A", "阵地_北山阵地", "驻扎于", 2.0, "{}", "军事数据库", "2025-06-02 14:30:00"),
    # ===== 行动的参与者关系 =====
    ("行动_利剑行动", "指挥员_刘司令员、部队_步兵第1团、部队_装甲第2营", "参与", 5.0, "{}", "军事数据库", "2025-06-03 08:00:00"),
    ("行动_利剑行动", "部队_炮兵第3连", "参与", 3.0, "{}", "军事数据库", "2025-06-03 08:30:00"),
    ("行动_渡口保障", "部队_工兵连、部队_侦察排", "参与", 3.0, "{}", "军事数据库", "2025-06-03 09:00:00"),
    # ===== 命令的下达与传输关系 =====
    ("命令_作战命令001", "行动_利剑行动", "下令", 5.0, "{}", "军事数据库", "2025-06-03 07:00:00"),
    ("命令_作战命令001", "指挥员_刘司令员", "传输至", 5.0, "{}", "军事数据库", "2025-06-03 07:05:00"),
    ("命令_联合作战令", "各战区、指挥员_刘司令员", "下令", 9.0, "{}", "军事数据库", "2025-06-04 06:00:00"),
    ("命令_联合作战令", "指挥员_刘司令员", "传输至", 8.0, "{}", "军事数据库", "2025-06-04 06:10:00"),
    # ===== 战区对部队的指挥关系 =====
    ("中部战区", "部队_步兵第1团、部队_装甲第2营", "指挥", 7.0, "{}", "军事数据库", "2025-06-04 08:00:00"),
    ("北部战区", "部队_炮兵第3连", "指挥", 6.0, "{}", "军事数据库", "2025-06-04 08:30:00"),
    ("东部战区", "部队_工兵连、部队_侦察排", "指挥", 5.0, "{}", "军事数据库", "2025-06-04 09:00:00"),
    # ===== 文电传输记录 =====
    ("传输_密电015", "指挥员_张参谋长", "传输至", 4.0, "{}", "军事数据库", "2025-06-05 10:00:00"),
    ("指挥员_刘司令员", "传输_密电015", "传输至", 4.0, "{}", "军事数据库", "2025-06-05 09:50:00"),
    ("传输_报告028", "指挥员_刘司令员", "传输至", 3.0, "{}", "军事数据库", "2025-06-05 14:00:00"),
    ("传输_报告028", "指挥员_张参谋长", "接收自", 3.0, "{}", "军事数据库", "2025-06-05 14:10:00"),
    # ===== 部队向上级的汇报关系 =====
    ("部队_装甲第2营", "指挥员_王副司令", "汇报", 5.0, "{}", "军事数据库", "2025-06-05 16:00:00"),
    ("部队_步兵第1团", "指挥员_刘司令员", "汇报", 6.0, "{}", "军事数据库", "2025-06-05 16:20:00"),
    ("部队_炮兵第3连", "指挥员_张参谋长", "汇报", 4.0, "{}", "军事数据库", "2025-06-05 16:40:00"),
    ("部队_侦察排", "指挥员_张参谋长", "汇报", 3.0, "{}", "军事数据库", "2025-06-05 17:00:00"),
    # ===== 武器对阵地的部署及其他关联关系 =====
    ("武器_ZTZ99坦克连", "阵地_302高地", "驻扎于", 2.0, "{}", "军事数据库", "2025-06-06 08:00:00"),
    ("阵地_302高地", "命令_作战命令001", "关联命令", 2.0, "{}", "军事数据库", "2025-06-06 09:00:00"),
    ("行动_利剑行动", "命令_作战命令001", "关联命令", 3.0, "{}", "军事数据库", "2025-06-06 10:00:00"),
    ("行动_全域联演", "各战区、部队_步兵第1团", "参与", 7.0, "{}", "军事数据库", "2025-06-07 08:00:00"),
]


def init_database(drop_existing=False):
    """执行数据库初始化流程。

    主要步骤：
      1. 连接DM达梦数据库
      2. 创建Schema（如果不存在）
      3. 创建NETWORK_EDGES边表（如果不存在）
      4. 导入示例边数据

    Args:
        drop_existing: 是否删除旧表并重建，默认为False
    """
    import dmPython

    # 从配置文件读取数据库连接参数
    schema = DM_DATABASE["schema"]
    user = DM_DATABASE["user"]
    password = DM_DATABASE["password"]
    host = DM_DATABASE["host"]
    port = DM_DATABASE["port"]

    # 第一步：连接数据库
    print(f"[1/3] 连接DM数据库 {user}@{host}:{port}...")
    conn = dmPython.connect(user=user, password=password, server=host, port=port)
    cursor = conn.cursor()
    print("      连接成功")

    # 第二步：创建Schema和表
    print(f"[2/3] 创建模式 {schema}...")
    try:
        # 尝试创建Schema，如果已存在则跳过
        cursor.execute(f'CREATE SCHEMA "{schema}" AUTHORIZATION "{user}"')
        conn.commit()
        print(f"      模式 {schema} 创建成功")
    except Exception as e:
        conn.rollback()
        if "already exists" in str(e).lower() or "已存在" in str(e):
            print(f"      模式 {schema} 已存在，跳过")
        else:
            print(f"      创建模式警告: {e}")

    # 如果指定了drop_existing参数，先删除所有旧表
    if drop_existing:
        for sql in DROP_TABLES_SQL:
            try:
                cursor.execute(sql.format(schema=schema))
                conn.commit()
            except Exception:
                conn.rollback()
        print("      旧表已删除")

    # 创建NETWORK_EDGES边表
    try:
        cursor.execute(CREATE_EDGES_TABLE.format(schema=schema))
        conn.commit()
        print("      表 NETWORK_EDGES 创建成功")
    except Exception as e:
        conn.rollback()
        if "already exists" in str(e).lower() or "已存在" in str(e):
            print("      表 NETWORK_EDGES 已存在，跳过")
        else:
            print(f"      创建表警告: {e}")

    # 第三步：逐条插入示例边数据
    print("[3/3] 导入示例边数据...")
    edge_count = 0
    for edge in SAMPLE_EDGES:
        try:
            # 使用参数化查询防止SQL注入
            cursor.execute(
                f'INSERT INTO "{schema}"."NETWORK_EDGES" '
                f'(SOURCE_NODE, TARGET_NODE, EDGE_TYPE, WEIGHT, ATTRIBUTES, SOURCE_TYPE, RECEIVE_TIME) '
                f'VALUES (:1, :2, :3, :4, :5, :6, :7)',
                edge
            )
            edge_count += 1
        except Exception as e:
            print(f"      插入边 {edge[0]}->{edge[1]} 警告: {e}")
    conn.commit()
    print(f"      插入 {edge_count} 条边")

    # 从边数据中自动提取所有唯一节点（用于统计报告）
    all_nodes = set()
    for edge in SAMPLE_EDGES:
        # 添加源节点
        all_nodes.add(edge[0])
        # 解析目标节点：支持顿号（、）分隔的多个节点
        for tgt in edge[1].split("\u3001"):
            t = tgt.strip()
            # 特殊处理："各战区"展开为五大战区节点
            if t == "各战区":
                for tz in ["中部战区", "北部战区", "东部战区", "南部战区", "西部战区"]:
                    all_nodes.add(tz)
            else:
                all_nodes.add(t)
    print(f"      从边表自动提取 {len(all_nodes)} 个唯一节点")

    # 关闭数据库连接
    cursor.close()
    conn.close()
    print(f"\n初始化完成! 边表 {edge_count} 条 / 自动提取 {len(all_nodes)} 节点")


if __name__ == "__main__":
    # 命令行入口，支持以下参数：
    #   --drop       删除旧表并重建
    #   --host       指定数据库主机地址（覆盖配置文件）
    #   --port       指定数据库端口号（覆盖配置文件）
    import argparse
    parser = argparse.ArgumentParser(description="DM数据库初始化(仅边表)")
    parser.add_argument("--drop", action="store_true", help="删除旧表并重建")
    parser.add_argument("--host", default=None, help="数据库主机")
    parser.add_argument("--port", type=int, default=None, help="数据库端口")
    args = parser.parse_args()

    # 命令行参数覆盖配置文件中的默认值
    if args.host:
        DM_DATABASE["host"] = args.host
    if args.port:
        DM_DATABASE["port"] = args.port

    # 执行数据库初始化
    init_database(drop_existing=args.drop)

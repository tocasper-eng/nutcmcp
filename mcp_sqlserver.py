"""
SQL Server MCP Server
連線資訊: 163.17.141.61,8000 / casper
"""
import json
import pyodbc
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# 連線設定
CONN_STR = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=163.17.141.61,8000;"
    "UID=casper;"
    "PWD=CasChrAliJimJam;"
    "TrustServerCertificate=yes;"
)

def get_conn():
    return pyodbc.connect(CONN_STR, timeout=10)

server = Server("sqlserver-nutc")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="query",
            description="執行 SELECT 查詢，回傳結果（唯讀）",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql":    {"type": "string", "description": "SELECT 語句"},
                    "db":     {"type": "string", "description": "資料庫名稱（可省略）"},
                },
                "required": ["sql"],
            },
        ),
        Tool(
            name="execute",
            description="執行 DDL / DML 語句（INSERT、UPDATE、DELETE、CREATE 等）",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql":    {"type": "string", "description": "SQL 語句"},
                    "db":     {"type": "string", "description": "資料庫名稱（可省略）"},
                },
                "required": ["sql"],
            },
        ),
        Tool(
            name="list_databases",
            description="列出所有資料庫",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="list_tables",
            description="列出指定資料庫的所有資料表",
            inputSchema={
                "type": "object",
                "properties": {
                    "db": {"type": "string", "description": "資料庫名稱"},
                },
                "required": ["db"],
            },
        ),
        Tool(
            name="list_procedures",
            description="列出指定資料庫的所有 Stored Procedure（含是否加密）",
            inputSchema={
                "type": "object",
                "properties": {
                    "db": {"type": "string", "description": "資料庫名稱"},
                },
                "required": ["db"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        conn = get_conn()
        cursor = conn.cursor()

        if name == "list_databases":
            cursor.execute("SELECT name FROM sys.databases WHERE database_id > 4 ORDER BY name")
            rows = [r[0] for r in cursor.fetchall()]
            return [TextContent(type="text", text="\n".join(rows))]

        db = arguments.get("db", "")
        if db:
            cursor.execute(f"USE [{db}]")

        if name == "query":
            cursor.execute(arguments["sql"])
            cols = [c[0] for c in cursor.description]
            rows = cursor.fetchall()
            result = [dict(zip(cols, row)) for row in rows]
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2, default=str))]

        elif name == "execute":
            cursor.execute(arguments["sql"])
            conn.commit()
            return [TextContent(type="text", text=f"執行成功，影響 {cursor.rowcount} 筆資料")]

        elif name == "list_tables":
            cursor.execute("""
                SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE
                FROM INFORMATION_SCHEMA.TABLES
                ORDER BY TABLE_SCHEMA, TABLE_NAME
            """)
            cols = ["結構描述", "資料表", "類型"]
            rows = [dict(zip(cols, r)) for r in cursor.fetchall()]
            return [TextContent(type="text", text=json.dumps(rows, ensure_ascii=False, indent=2))]

        elif name == "list_procedures":
            cursor.execute("""
                SELECT
                    SCHEMA_NAME(o.schema_id) AS [結構描述],
                    o.name AS [SP名稱],
                    CASE WHEN m.definition IS NULL THEN '已加密' ELSE '未加密' END AS [狀態],
                    o.create_date, o.modify_date
                FROM sys.objects o
                JOIN sys.sql_modules m ON o.object_id = m.object_id
                WHERE o.type = 'P'
                ORDER BY SCHEMA_NAME(o.schema_id), o.name
            """)
            cols = [c[0] for c in cursor.description]
            rows = [dict(zip(cols, r)) for r in cursor.fetchall()]
            return [TextContent(type="text", text=json.dumps(rows, ensure_ascii=False, indent=2, default=str))]

    except Exception as e:
        return [TextContent(type="text", text=f"錯誤：{e}")]
    finally:
        try:
            conn.close()
        except:
            pass

    return [TextContent(type="text", text="未知工具")]


if __name__ == "__main__":
    import asyncio
    asyncio.run(stdio_server(server).run())

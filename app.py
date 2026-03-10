import os
import json
import anthropic
from flask import Flask, render_template, request, jsonify
import pymssql

app = Flask(__name__)

DB_CONFIG = {
    "server": os.environ.get("DB_SERVER", "163.17.141.61"),
    "port": int(os.environ.get("DB_PORT", 8000)),
    "user": os.environ.get("DB_USER", "casper"),
    "password": os.environ.get("DB_PASSWORD", "CasChrAliJimJam"),
    "database": os.environ.get("DB_NAME", "casper"),
    "charset": "CP950",
}

SYSTEM_PROMPT = """你是一個 SQL Server 資料庫助手，幫助使用者查詢以下資料庫的資料。

## 資料庫說明
- Server: 163.17.141.61,8000
- 主要資料庫: casper

## 重要資料表對照

| 業務名稱 | 資料表 | 說明 |
|---------|--------|------|
| 銷售訂單 | soh | 訂單主檔，sodate=日期，soamount=金額，custno=客戶 |
| 銷售明細 | sod | 訂單明細，連結 soh |
| 銀行帳戶/存款 | nban | 銀行帳戶主檔 |
| 應收帳款 | ledb | accino='117002' |
| 總帳明細 | leda | 各科目交易明細 |
| 採購訂單 | poh | 採購主檔 |
| 採購明細 | pod | 採購明細 |
| 進貨單 | RPORD6E | 進貨記錄，pudate=日期 |
| 會計科目 | acci | 科目代號與名稱 |
| 客戶資料 | cust | 客戶主檔 |
| 員工資料 | empl | 員工主檔 |

## 日期格式
資料庫日期格式為 YYYYMMDD（字串），例如今天 2026-03-10 = '20260310'

請用繁體中文回答，並盡量以清楚易懂的方式呈現查詢結果。
只執行 SELECT 查詢，不可執行任何修改資料的操作。"""

TOOLS = [
    {
        "name": "query",
        "description": "執行 SELECT SQL 查詢並回傳結果",
        "input_schema": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "要執行的 SELECT SQL 語句",
                }
            },
            "required": ["sql"],
        },
    },
    {
        "name": "list_tables",
        "description": "列出資料庫中所有的資料表名稱",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "list_databases",
        "description": "列出伺服器上所有資料庫",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
]


def get_conn():
    return pymssql.connect(**DB_CONFIG)


def run_tool(tool_name, tool_input):
    try:
        conn = get_conn()
        cur = conn.cursor(as_dict=True)
        if tool_name == "query":
            sql = tool_input["sql"]
            if not sql.strip().upper().startswith("SELECT"):
                return {"error": "只允許執行 SELECT 查詢"}
            cur.execute(sql)
            rows = cur.fetchall()
            conn.close()
            return {"rows": rows, "count": len(rows)}
        elif tool_name == "list_tables":
            cur.execute(
                "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE' ORDER BY TABLE_NAME"
            )
            rows = cur.fetchall()
            conn.close()
            return {"tables": [r["TABLE_NAME"] for r in rows]}
        elif tool_name == "list_databases":
            cur.execute("SELECT name FROM sys.databases ORDER BY name")
            rows = cur.fetchall()
            conn.close()
            return {"databases": [r["name"] for r in rows]}
        else:
            conn.close()
            return {"error": f"未知工具: {tool_name}"}
    except Exception as e:
        return {"error": str(e)}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "訊息不能為空"}), 400

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return jsonify({"error": "未設定 ANTHROPIC_API_KEY"}), 500

    client = anthropic.Anthropic(api_key=api_key)
    messages = [{"role": "user", "content": user_message}]

    try:
        while True:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )

            # Add assistant response to message history
            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                # Extract final text answer
                answer = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        answer += block.text
                return jsonify({"answer": answer})

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = run_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result, ensure_ascii=False, default=str),
                        })

                messages.append({"role": "user", "content": tool_results})
            else:
                # Unexpected stop reason
                break

        return jsonify({"answer": "無法取得回應"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

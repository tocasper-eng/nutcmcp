import os
from flask import Flask, render_template, request
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


def get_conn():
    return pymssql.connect(**DB_CONFIG)


@app.route("/")
def index():
    keyword = request.args.get("q", "")
    rows = []
    error = None
    try:
        conn = get_conn()
        cur = conn.cursor(as_dict=True)
        if keyword:
            cur.execute(
                "SELECT accino, accinm, di, amt FROM dbo.acci WHERE accinm LIKE %s OR accino LIKE %s ORDER BY accino",
                (f"%{keyword}%", f"%{keyword}%"),
            )
        else:
            cur.execute(
                "SELECT accino, accinm, di, amt FROM dbo.acci ORDER BY accino"
            )
        rows = cur.fetchall()
        conn.close()
    except Exception as e:
        error = str(e)
    return render_template("index.html", rows=rows, keyword=keyword, error=error)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

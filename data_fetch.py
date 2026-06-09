import urllib.request
import urllib.parse
import json
import re
import time
import csv
from datetime import datetime
from pathlib import Path

CSV_FILE = Path(__file__).parent / "A股总市值每日记录.csv"

def fetch_json(url, params, referer):
    full_url = url + "?" + urllib.parse.urlencode(params)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
        "Accept": "application/json,text/plain,*/*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": referer,
        "Connection": "close",
    }

    req = urllib.request.Request(full_url, headers=headers)

    for _ in range(3):
        try:
            text = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", errors="ignore").strip()

            if not text.startswith("{") and not text.startswith("["):
                m = re.search(r"\((.*)\)", text)
                if m:
                    text = m.group(1)

            return json.loads(text)

        except Exception as e:
            print("请求失败，重试：", e)
            time.sleep(1)

    raise RuntimeError("连续3次请求失败：" + full_url)


def num(x):
    if x in [None, "-", ""]:
        return 0.0
    return float(str(x).replace(",", "").strip())


def get_sse():
    data = fetch_json(
        "https://query.sse.com.cn/commonQuery.do",
        {
            "jsonCallBack": "",
            "isPagination": "false",
            "sqlId": "COMMON_SSE_SJ_SCGM_C",
            "_": int(datetime.now().timestamp() * 1000),
        },
        "https://www.sse.com.cn/market/stockdata/statistic/"
    )

    rows = data["result"]

    stock_total = None
    kcb_total = None
    trade_date = None

    for r in rows:
        name = str(r.get("PRODUCT_NAME", "")).strip()

        if name == "股票":
            stock_total = r.get("TOTAL_VALUE")
            trade_date = r.get("TRADE_DATE")

        if name == "科创板":
            kcb_total = r.get("TOTAL_VALUE")

    if stock_total is None or kcb_total is None:
        print("上交所返回数据：")
        print(rows)
        raise RuntimeError("没有识别出上交所总市值字段")

    return {
        "交易日期": trade_date,
        "上证总市值_亿元": num(stock_total),
        "科创板总市值_亿元": num(kcb_total),
    }


def get_szse():
    data = fetch_json(
        "https://www.szse.cn/api/report/ShowReport/data",
        {
            "SHOWTYPE": "JSON",
            "CATALOGID": "1803_sczm",
            "loading": "first",
            "random": str(time.time()),
        },
        "https://www.szse.cn/market/overview/index.html"
    )

    if isinstance(data, list):
        rows = data[0].get("data", [])
    elif isinstance(data, dict):
        rows = data.get("data", [])
    else:
        rows = []

    stock_total = None
    cyb_total = None

    for r in rows:
        name = str(r.get("lbmc", ""))
        name = name.replace("&nbsp;", "").strip()

        if name == "股票":
            stock_total = r.get("sjzz")

        if "创业板" in name:
            cyb_total = r.get("sjzz")

    if stock_total is None or cyb_total is None:
        print("深交所返回数据：")
        print(rows)
        raise RuntimeError("没有识别出深交所总市值字段")

    return {
        "深证总市值_亿元": num(stock_total),
        "创业板总市值_亿元": num(cyb_total),
    }


def save_csv(row):
    headers = [
        "抓取时间",
        "交易日期",
        "上证总市值_亿元",
        "深证总市值_亿元",
        "创业板总市值_亿元",
        "科创板总市值_亿元",
    ]

    old_rows = []

    if CSV_FILE.exists():
        with open(CSV_FILE, "r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            old_rows = list(reader)

    old_rows = [
        r for r in old_rows
        if str(r.get("交易日期", "")) != str(row["交易日期"])
    ]

    old_rows.append(row)

    old_rows.sort(key=lambda x: str(x.get("交易日期", "")))

    with open(CSV_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(old_rows)


def main():
    print("开始抓上交所数据")
    sse = get_sse()
    print("上交所成功：", sse)

    print("开始抓深交所数据")
    szse = get_szse()
    print("深交所成功：", szse)


    row = {
        "抓取时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "交易日期": sse["交易日期"],
        "上证总市值_亿元": sse["上证总市值_亿元"],
        "深证总市值_亿元": szse["深证总市值_亿元"],
        "创业板总市值_亿元": szse["创业板总市值_亿元"],
        "科创板总市值_亿元": sse["科创板总市值_亿元"],
    }

    save_csv(row)

    print("保存成功：", CSV_FILE.resolve())
    print(row)


if __name__ == "__main__":
    main()
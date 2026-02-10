import argparse
import csv
import json
import statistics
import time
import urllib.error
import urllib.request
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Deque, List, Optional

YAHOO_QUOTE_URL = "https://query1.finance.yahoo.com/v7/finance/quote?symbols=MSFT"
STOOQ_QUOTE_URL = "https://stooq.com/q/l/?s=msft.us&i=1"


@dataclass
class Quote:
    symbol: str
    price: float
    change: float
    change_percent: float
    market_time: int

    @property
    def market_datetime(self) -> datetime:
        return datetime.fromtimestamp(self.market_time)


class YahooQuoteClient:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def _fetch_from_yahoo(self) -> Quote:
        req = urllib.request.Request(
            YAHOO_QUOTE_URL,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))

        results = payload.get("quoteResponse", {}).get("result", [])
        if not results:
            raise RuntimeError("Yahoo 未获取到 MSFT 行情数据")

        row = results[0]
        return Quote(
            symbol=row.get("symbol", "MSFT"),
            price=float(row.get("regularMarketPrice", 0.0)),
            change=float(row.get("regularMarketChange", 0.0)),
            change_percent=float(row.get("regularMarketChangePercent", 0.0)),
            market_time=int(row.get("regularMarketTime", int(time.time()))),
        )

    def _fetch_from_stooq(self) -> Quote:
        req = urllib.request.Request(
            STOOQ_QUOTE_URL,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            raw = resp.read().decode("utf-8").strip()

        parts = raw.split(",")
        if len(parts) < 8:
            raise RuntimeError(f"Stooq 返回格式异常: {raw}")

        symbol, date_str, time_str, _open, high, low, close, _volume = parts[:8]
        market_dt = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
        close_price = float(close)
        day_mid = (float(high) + float(low)) / 2
        change = close_price - day_mid
        change_percent = (change / day_mid * 100) if day_mid else 0.0

        return Quote(
            symbol=symbol.replace(".US", ""),
            price=close_price,
            change=change,
            change_percent=change_percent,
            market_time=int(market_dt.timestamp()),
        )

    def fetch_msft_quote(self) -> Quote:
        try:
            return self._fetch_from_yahoo()
        except Exception:
            # Yahoo 在部分环境会返回 401，这里自动切换到 Stooq。
            try:
                return self._fetch_from_stooq()
            except urllib.error.URLError as exc:
                raise RuntimeError(f"网络请求失败: {exc}") from exc


class RealtimeAnalyzer:
    def __init__(self, window: int = 20):
        self.prices: Deque[float] = deque(maxlen=max(window, 20))

    def update(self, price: float) -> None:
        self.prices.append(price)

    def sma(self, period: int) -> Optional[float]:
        if len(self.prices) < period:
            return None
        values = list(self.prices)[-period:]
        return statistics.fmean(values)

    def ema(self, period: int) -> Optional[float]:
        if len(self.prices) < period:
            return None
        values = list(self.prices)[-period:]
        multiplier = 2 / (period + 1)
        ema_value = values[0]
        for p in values[1:]:
            ema_value = (p - ema_value) * multiplier + ema_value
        return ema_value

    def rsi(self, period: int = 14) -> Optional[float]:
        if len(self.prices) < period + 1:
            return None
        closes = list(self.prices)[-(period + 1) :]
        gains: List[float] = []
        losses: List[float] = []
        for i in range(1, len(closes)):
            diff = closes[i] - closes[i - 1]
            if diff >= 0:
                gains.append(diff)
                losses.append(0.0)
            else:
                gains.append(0.0)
                losses.append(-diff)

        avg_gain = statistics.fmean(gains)
        avg_loss = statistics.fmean(losses)
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))


def print_snapshot(quote: Quote, analyzer: RealtimeAnalyzer) -> None:
    sma_5 = analyzer.sma(5)
    sma_20 = analyzer.sma(20)
    ema_12 = analyzer.ema(12)
    rsi_14 = analyzer.rsi(14)

    print(
        f"[{quote.market_datetime.strftime('%Y-%m-%d %H:%M:%S')}] "
        f"{quote.symbol} 价格: {quote.price:.2f} USD | "
        f"涨跌: {quote.change:+.2f} ({quote.change_percent:+.2f}%)"
    )
    print(
        "  指标 -> "
        f"SMA5: {sma_5:.2f} " if sma_5 is not None else "  指标 -> SMA5: N/A ",
        f"SMA20: {sma_20:.2f} " if sma_20 is not None else "SMA20: N/A ",
        f"EMA12: {ema_12:.2f} " if ema_12 is not None else "EMA12: N/A ",
        f"RSI14: {rsi_14:.2f}" if rsi_14 is not None else "RSI14: N/A",
        sep="",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="微软 MSFT 实时行情分析工具")
    parser.add_argument("--interval", type=int, default=5, help="刷新间隔（秒），默认 5")
    parser.add_argument("--samples", type=int, default=120, help="采样次数，默认 120")
    parser.add_argument("--csv", type=Path, help="可选：将数据输出到 CSV 文件")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    client = YahooQuoteClient()
    analyzer = RealtimeAnalyzer(window=max(args.samples, 20))

    writer = None
    csv_file = None
    if args.csv:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        csv_file = args.csv.open("w", newline="", encoding="utf-8")
        writer = csv.writer(csv_file)
        writer.writerow(["time", "symbol", "price", "change", "change_percent", "sma5", "sma20", "ema12", "rsi14"])

    print("开始实时获取微软（MSFT）股票数据，按 Ctrl+C 停止。")

    try:
        for _ in range(args.samples):
            quote = client.fetch_msft_quote()
            analyzer.update(quote.price)
            print_snapshot(quote, analyzer)

            if writer:
                writer.writerow(
                    [
                        quote.market_datetime.isoformat(),
                        quote.symbol,
                        f"{quote.price:.4f}",
                        f"{quote.change:.4f}",
                        f"{quote.change_percent:.4f}",
                        f"{analyzer.sma(5):.4f}" if analyzer.sma(5) is not None else "",
                        f"{analyzer.sma(20):.4f}" if analyzer.sma(20) is not None else "",
                        f"{analyzer.ema(12):.4f}" if analyzer.ema(12) is not None else "",
                        f"{analyzer.rsi(14):.4f}" if analyzer.rsi(14) is not None else "",
                    ]
                )

            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n已停止采样。")
    finally:
        if csv_file:
            csv_file.close()


if __name__ == "__main__":
    main()

# CCmaker
import os
import pandas as pd
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ———————— تنظیمات ————————
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")  # ⚠️ از متغیر محیطی می‌خواند
if not TELEGRAM_TOKEN:
    raise ValueError("❌ متغیر محیطی TELEGRAM_TOKEN تنظیم نشده است!")

SYMBOL = "BTCUSDT"
INTERVAL = "15"
LIMIT = 210

async def get_signal():
    try:
        url = "https://api.bybit.com/v5/market/kline"  # فاصله انتهایی حذف شد
        params = {"category": "linear", "symbol": SYMBOL, "interval": INTERVAL, "limit": LIMIT}
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if data.get("retCode") != 0:
            return "❌ خطا در دریافت داده از Bybit."

        candles = data["result"]["list"]
        candles.reverse()

        df = pd.DataFrame(candles, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'
        ])
        df = df.astype({'close': float, 'high': float, 'low': float, 'volume': float})

        df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
        df['ema200'] = df['close'].ewm(span=200, adjust=False).mean()

        low_min = df['low'].rolling(14).min()
        high_max = df['high'].rolling(14).max()
        df['stoch_k'] = 100 * (df['close'] - low_min) / (high_max - low_min)
        df['stoch_d'] = df['stoch_k'].rolling(3).mean()
        df['vol_ma20'] = df['volume'].rolling(20).mean()

        last = df.iloc[-1]
        prev = df.iloc[-2]

        sl_pct = 0.009
        tp_pct = 0.018
        leverage = 5

        uptrend = last['ema50'] > last['ema200']
        downtrend = last['ema50'] < last['ema200']

        if uptrend and prev['stoch_d'] < 20 and last['stoch_d'] >= 20:
            entry = last['close']
            sl = entry * (1 - sl_pct)
            tp = entry * (1 + tp_pct)
            trend_bonus = min((last['ema50'] - last['ema200']) / last['ema200'] * 1000, 30)
            mom_bonus = min((last['stoch_d'] - prev['stoch_d']) * 2, 20)
            vol_bonus = 5 if last['volume'] > last['vol_ma20'] else 0
            strength = min(50 + trend_bonus + mom_bonus + vol_bonus, 100)

            msg = (
                "🟢 <b>سیگنال خرید (BUY)</b>\n\n"
                f"📍 نقطه ورود: {entry:,.2f} USDT\n"
                f"🛑 حد ضرر (SL): {sl:,.2f} USDT\n"
                f"🎯 حد سود (TP): {tp:,.2f} USDT\n"
                f"⚡ اهرم پیشنهادی: {leverage}x\n"
                f"📈 قدرت سیگنال: {strength:.1f}%"
            )
            return msg

        elif downtrend and prev['stoch_d'] > 80 and last['stoch_d'] <= 80:
            entry = last['close']
            sl = entry * (1 + sl_pct)
            tp = entry * (1 - tp_pct)
            trend_bonus = min((last['ema200'] - last['ema50']) / last['ema200'] * 1000, 30)
            mom_bonus = min((prev['stoch_d'] - last['stoch_d']) * 2, 20)
            vol_bonus = 5 if last['volume'] > last['vol_ma20'] else 0
            strength = min(50 + trend_bonus + mom_bonus + vol_bonus, 100)

            msg = (
                "🔴 <b>سیگنال فروش (SELL)</b>\n\n"
                f"📍 نقطه ورود: {entry:,.2f} USDT\n"
                f"🛑 حد ضرر (SL): {sl:,.2f} USDT\n"
                f"🎯 حد سود (TP): {tp:,.2f} USDT\n"
                f"⚡ اهرم پیشنهادی: {leverage}x\n"
                f"📈 قدرت سیگنال: {strength:.1f}%"
            )
            return msg

        else:
            return "⏸️ هیچ سیگنالی در تایم‌فریم ۱۵ دقیقه‌ای یافت نشد."

    except Exception as e:
        return f"❌ خطا: {str(e)}"

# ———————— هندلر دستور /signal ————————
async def signal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "در حال دریافت سیگنال... ⏳"
    await update.message.reply_text(msg)
    signal_msg = await get_signal()
    await update.message.reply_text(signal_msg, parse_mode="HTML")

# ———————— راه‌اندازی ربات ————————
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("signal", signal_command))
    print("ربات در حال اجراست...")
    app.run_polling()

if __name__ == "__main__":
    main()

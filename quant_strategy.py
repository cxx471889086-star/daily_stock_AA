"""
双均线 + 量价共振策略
买入：5日均线上穿20日均线 + 成交量放大1.5倍 + 收盘价站上20日均线
卖出：5日均线下穿20日均线 或 浮亏超过5%
"""
import pandas as pd
import numpy as np

class QuantStrategy:
    def __init__(self, ma_fast=5, ma_slow=20, volume_ratio=1.5, stop_loss=0.05):
        self.ma_fast = ma_fast
        self.ma_slow = ma_slow
        self.volume_ratio = volume_ratio
        self.stop_loss = stop_loss
    
    def calc_indicators(self, df):
        """计算技术指标"""
        df['ma5'] = df['close'].rolling(self.ma_fast).mean()
        df['ma20'] = df['close'].rolling(self.ma_slow).mean()
        df['vol_ma5'] = df['volume'].rolling(5).mean()
        df['rsi'] = self._calc_rsi(df['close'], 14)
        return df
    
    def _calc_rsi(self, prices, period=14):
        """计算RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def should_buy(self, df):
        """判断买入信号"""
        if len(df) < self.ma_slow + 1:
            return False, "数据不足"
        
        current = df.iloc[-1]
        prev = df.iloc[-2]
        
        # 金叉
        golden_cross = (current['ma5'] > current['ma20']) and (prev['ma5'] <= prev['ma20'])
        # 放量
        volume_ok = current['volume'] > current['vol_ma5'] * self.volume_ratio
        # 站稳20日线
        above_ma20 = current['close'] > current['ma20']
        # RSI不超买
        rsi_ok = 50 <= current['rsi'] <= 75
        
        signals = {
            '金叉': golden_cross,
            '放量': volume_ok,
            '站稳20日线': above_ma20,
            'RSI合理': rsi_ok
        }
        
        if all(signals.values()):
            return True, "全部信号触发"
        return False, f"未触发: {[k for k, v in signals.items() if not v]}"
    
    def should_sell(self, df, entry_price):
        """判断卖出信号"""
        current = df.iloc[-1]
        prev = df.iloc[-2]
        
        # 止损
        loss_pct = (current['close'] - entry_price) / entry_price
        stop_loss_hit = loss_pct < -self.stop_loss
        
        # 死叉
        death_cross = (current['ma5'] < current['ma20']) and (prev['ma5'] >= prev['ma20'])
        
        if stop_loss_hit:
            return True, f"止损 (浮亏{loss_pct*100:.2f}%)"
        if death_cross:
            return True, "死叉信号"
        return False, "继续持有"

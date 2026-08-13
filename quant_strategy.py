name: 每日量化分析

on:
  schedule:
    - cron: '0 1 * * 1-5'
  workflow_dispatch:

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - name: 拉取代码
        uses: actions/checkout@v4

      - name: 设置 Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: 安装依赖
        run: |
          pip install pandas yfinance requests

      - name: 读取自选股
        env:
          STOCK_LIST: ${{ secrets.STOCK_LIST }}
        run: |
          echo "当前自选股: $STOCK_LIST"

      - name: 推送到飞书
        env:
          FEISHU_WEBHOOK: ${{ secrets.FEISHU_WEBHOOK_URL }}
        run: |
          curl -X POST "$FEISHU_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d '{"msg_type":"text","content":{"text":"每日量化分析 - 策略就绪"}}'

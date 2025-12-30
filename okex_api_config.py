"""
OKEx API 配置文件
包含 API 密钥和基本配置
"""

# OKEx API 凭据
OKEX_API_KEY = "77465009-2c87-443c-83c8-08b35c7f14b2"
OKEX_SECRET_KEY = "11647B2578630D28501D41C748B3D809"
OKEX_PASSPHRASE = "Tencent@123"

# API 端点
OKEX_REST_URL = "https://www.okx.com"
OKEX_WS_PUBLIC_URL = "wss://ws.okx.com:8443/ws/v5/public"
OKEX_WS_PRIVATE_URL = "wss://ws.okx.com:8443/ws/v5/private"

# 配置
SIMULATED = False  # False = 实盘, True = 模拟盘

print("✅ OKEx API 配置文件已创建")

# BowlWanpi 全局代理配置
# 让所有网络请求都通过 Mihomo 代理

# HTTP/HTTPS 代理
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890

# SOCKS5 代理（部分工具使用）
export ALL_PROXY=socks5://127.0.0.1:7890
export all_proxy=socks5://127.0.0.1:7890

# 不代理的地址（本地地址）
export no_proxy=localhost,127.0.0.1,::1
export NO_PROXY=localhost,127.0.0.1,::1

# Git 代理配置
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890

echo "✅ 代理已配置: http://127.0.0.1:7890"
echo "🧪 测试: curl -I http://www.google.com"

# 添加到 ~/.bashrc（永久生效）
if ! grep -q "http_proxy=127.0.0.1:7890" ~/.bashrc 2>/dev/null; then
    echo "" >> ~/.bashrc
    echo "# BowlWanpi 代理配置" >> ~/.bashrc
    echo "export http_proxy=http://127.0.0.1:7890" >> ~/.bashrc
    echo "export https_proxy=http://127.0.0.1:7890" >> ~/.bashrc
    echo "export HTTP_PROXY=http://127.0.0.1:7890" >> ~/.bashrc
    echo "export HTTPS_PROXY=http://127.0.0.1:7890" >> ~/.bashrc
    echo "✅ 已添加到 ~/.bashrc（永久生效）"
fi

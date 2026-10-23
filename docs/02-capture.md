# 02 · 抓包：在电脑上复刻小程序的请求

> 目标：拿到「小程序 → 博联云」的请求头和一次完整的控制请求。

## 为什么在电脑上抓，而不是手机

- 电脑版微信同样能打开小程序，而且**系统代理一行命令就能设**
- 手机需要改 Wi-Fi 代理 + 装描述文件 + 信任证书，步骤多且容易出错
- 电脑上抓到的流量可以直接用脚本分析

## 1. 安装 mitmproxy

```bash
# macOS
brew install mitmproxy
# 或
pipx install mitmproxy
```

启动（监听 8080，允许非本机连接）：

```bash
mitmdump --listen-host 0.0.0.0 --listen-port 8080 \
  --set block_global=false -w ~/flows.mitm
```

## 2. 设置系统代理

**macOS**：系统设置 → 网络 → 当前网络 → 详细信息 → 代理 → 网页代理 / 安全网页代理
都填 `127.0.0.1`、端口 `8080`。

或命令行：

```bash
networksetup -setwebproxy "Wi-Fi" 127.0.0.1 8080
networksetup -setsecurewebproxy "Wi-Fi" 127.0.0.1 8080
```

## 3. 信任 mitmproxy 证书

浏览器访问 `http://mitm.it`，下载 Apple 证书并安装；然后在
「钥匙串访问 → 系统/登录 → mitmproxy → 信任 → 始终信任」。

> 只抓自己的设备与账号，抓完务必删除（见 07 篇）。

## 4. 操作小程序

打开电脑版微信 → 「全屋智控」→ 依次做：

1. 开一盏灯、关一盏灯
2. 空调：调温度、切模式、调风速
3. 窗帘：开、停、关
4. 触发一个场景（可选）

每步之间停 1–2 秒，方便区分请求。

## 5. 找到关键请求

停止 mitmproxy，用脚本扫描 flows 文件：

```python
from mitmproxy import io, http

with open("flows.mitm", "rb") as f:
    for flow in io.FlowReader(f).stream():
        if not isinstance(flow, http.HTTPFlow):
            continue
        if "houseproxy" in flow.request.path:
            print(flow.request.method, flow.request.pretty_url)
```

你会看到类似：

```
POST https://app-service-chn-xxxxxxxx.ibroadlink.com/appfront/v1/houseproxy/v1/dueros
```

这条就是控制入口。

## 6. 提取会话（session.json）

从**任意一条**成功请求里取出：

- 请求头：`loginsession`、`userid`、`familyid`、`licenseid`、`activationcode`、`companyid`
- 请求体：`payload.cookie`

写成：

```json
{
  "url": "https://app-service-chn-xxxxxxxx.ibroadlink.com/appfront/v1/houseproxy/v1/dueros",
  "headers": {
    "loginsession": "<会话>",
    "userid": "<用户ID>",
    "familyid": "<家庭ID>",
    "licenseid": "<授权ID>",
    "activationcode": "<固定授权码>",
    "companyid": "<厂商ID>",
    "Content-Type": "application/json"
  },
  "cookie": "<设备 cookie（Base64）>"
}
```

> `datatrace` 是埋点，可以丢弃；`messageid` 每次随机。

## 7. 提取设备清单（devices.json）

从 `DiscoverAppliancesRequest` 的响应里导出 `discoveredAppliances` 数组，
这就是全屋设备清单（含每个设备的 `additionalApplianceDetails`）。

**不要手改这份文件**：`applianceId` 和 `additionalApplianceDetails` 必须成对出现。

## 8. 收尾（很重要）

```bash
# 关闭系统代理
networksetup -setwebproxystate "Wi-Fi" off
networksetup -setsecurewebproxystate "Wi-Fi" off
# 删除抓包文件
rm ~/flows.mitm
```

再手动删除钥匙串里的 mitmproxy 证书。详见 [07-privacy.md](07-privacy.md)。

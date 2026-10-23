# 07 · 隐私、安全与合规

## 1. 哪些东西绝对不能公开

| 文件 / 数据 | 为什么 |
|---|---|
| `session.json` | `loginsession` + 设备 cookie，等于整屋钥匙 |
| `devices.json` | 每个设备带 `aeskeyToken`，且能还原户型 |
| `flows.mitm` / `*.har` / `*.pcap` | 包含你账号的**全部** HTTPS 流量 |
| mitmproxy 根证书私钥 | 可以被用来中间人攻击 |

**判断标准**：能让你控制设备的东西，都不能出现在仓库、截图、聊天记录里。

## 2. 分享前自检

```bash
# 在仓库根目录执行，应该没有任何输出
grep -rniE "loginsession|aeskey|cookie|mitmproxy-ca" . \
  --exclude-dir=.git --exclude="*.example"
```

`.gitignore` 已经排除了 `session.json`、`devices.json`、`*.mitm`、`*.log`。

## 3. 抓完包必须做的清理

1. 关闭系统代理
2. 删除抓包文件（`flows.mitm` 等）
3. 删除 mitmproxy 证书：
   - macOS：钥匙串访问 → 搜索 `mitmproxy` → 删除；再到「证书信任设置」关掉
   - Windows：certmgr.msc → 受信任的根证书颁发机构 → 删除
4. 删除 mitmproxy 的 CA 私钥目录（默认 `~/.mitmproxy/`）

## 4. 权限建议

- `session.json` 权限设为 `600`（仅所有者可读）
- 不要把 HA 的 8123 端口直接映射到公网
- 需要远程访问时用 VPN / Cloudflare Tunnel / Nabu Casa，不要裸奔
- HA 长期令牌（long-lived token）用完即撤销

## 5. 合规提示

- 本方法仅适用于**你拥有或有权管理**的设备
- 请遵守博联、微信的服务条款；不要用于破解他人设备
- 抓包会经过你账号的全部流量，请自行评估风险
- 接口为厂商私有协议，可能随时变更，升级后失效属正常现象

## 6. 账号风险

- 频繁异常请求可能触发风控，建议控制轮询频率（20 秒以上）
- 不要把会话共享给他人，包括"帮忙调试"的场景
- 若发现设备行为异常，先在米家/全屋智控 App 里确认账号状态

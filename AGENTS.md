# AGENTS.md — 给 AI 助手的部署说明

> 本文件面向 AI 编码助手（Codex / Claude Code / DeepSeek Harness / Copilot 等）。
> 当用户让你「按这个仓库帮我部署」时，请严格按下面的流程执行。

## 0. 先判断适用性（必做）

先问用户这 5 个问题，**不要跳过**：

1. 网关标签是不是 `IC.IHG2`？
2. 控制用的小程序是不是「全屋智控」？
3. Home Assistant 是 Docker / HA OS / Core？装在什么机器上？
4. 有没有一台 7×24 开机的机器？
5. 有没有 iPhone/iPad（要不要接 Siri）？

如果 1、2 任一为「否」，提醒用户先看 `docs/01-hardware.md` 的自检清单，
并说明协议可能不同、需要以自己抓到的包为准。

## 1. 部署顺序（不要打乱）

```
docs/01-hardware.md   → 确认硬件与网络
docs/02-capture.md    → 抓包，产出 session.json + devices.json
docs/03-protocol.md   → 理解请求结构（排错时必读）
docs/04-home-assistant.md → 安装集成、按房间建条目
docs/05-homekit.md    → 桥接、命名、房间、摄氏
docs/06-pitfalls.md   → 出问题先查这里
docs/07-privacy.md    → 收尾清理
```

## 2. 安全红线（必须遵守）

- **绝不要让用户把 `session.json`、`cookie`、`aeskey`、`loginsession` 粘贴到聊天里。**
  让用户自己把文件放到 HA 的 `config/cloudthink_broadlink/` 目录，你只检查文件是否存在。
- 不要建议关闭防火墙、不要把 8123 暴露到公网。
- 不要执行 `rm -rf`、数据库删除、容器删除等破坏性命令，除非用户明确要求。
- 重启 HA 前必须提醒用户：正在运行的自动化会中断。
- 抓包完成后必须提醒：关闭系统代理、删除证书、删除 `flows.mitm`。

## 3. 你可以做的事

- 逐条解释协议字段，帮用户核对抓到的请求
- 帮用户写/改 `session.json` 的**结构**（值由用户自己填）
- 生成 HA 集成代码、修改 `selected_devices` 适配用户房间
- 解读 HA 日志、定位是会话过期、权限问题还是实体缺失
- 生成 HomeKit 筛选清单、命名建议、房间分配步骤

## 4. 你不能做的事

- 不能访问用户的局域网、HA 实例、NAS
- 不能替用户完成抓包（需要在本机装 mitmproxy、信任证书）
- 不能凭空编造接口或字段——**一切以 `docs/03-protocol.md` 和用户抓到的包为准**

## 5. 验收清单

部署完成后逐项确认：

- [ ] `session.json` 与 `devices.json` 已放到 `config/cloudthink_broadlink/`
- [ ] 每个目标房间都有配置条目，且状态为 `loaded`
- [ ] 灯能开关、空调能调温、窗帘能开合
- [ ] HomeKit 里能看到对应配件，Siri 能控制
- [ ] 日志里没有 `cloudthink_broadlink` 的报错
- [ ] 用户已知晓：会话会过期，需要重新抓包

## 6. 常见报错映射

| 报错/现象 | 先查 |
|---|---|
| 实体全部 `unavailable` | 会话过期 → `docs/06` 第 20 条 |
| 集成加载失败 | `devices.json` 缺失或格式错 |
| `ServiceNotSupported: climate.toggle` | 未声明 TURN_ON/OFF → `docs/04` 第 5 节 |
| 家庭 App 显示华氏 | iPhone 温度单位 → `docs/05` 第 4 节 |
| 窗帘位置不准 | 电机行程 10 秒 → `docs/06` 第 4 条 |

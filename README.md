# BroadLink IHG2 → Home Assistant → HomeKit

精装房预装的博联全屋智能（网关 `IC.IHG2`，微信小程序「全屋智控」）平时只能在小程序里控。这个仓库记录我怎么把它接到 Home Assistant，再桥到 Apple 家庭，用 Siri 和自动化。

不改网关固件、不拆机、不动强电。官方 HA `broadlink` 集成认不到这类工程机，所以要自己抓包、复刻云端接口。

## 原理

小程序不直连网关，而是打博联云上的 DuerOS ConnectedHome `houseproxy`。抓到会话头和设备清单后，HA 用同一套 HTTPS 请求就能控灯、窗帘、空调、新风等。

```
微信小程序 ──HTTPS──▶ 博联云 houseproxy ──▶ IHG2 ──▶ 设备
                            ▲
                     HA 自定义集成（复刻请求）
```

## 仓库里有什么

- `docs/`：从辨认硬件、mitmproxy 抓包、协议字段，到装 HA、接 HomeKit、踩坑和隐私清理
- `custom_components/cloudthink_broadlink/`：参考用的 HA 自定义集成（light / climate / cover 等）
- `examples/`：`session.json` / `devices.json` 示例（真凭证不要提交）
- `hacs.json`：方便用 HACS 装集成
- `AGENTS.md` / `llms.txt`：给 AI 助手带部署时用的流程和文档索引

## 怎么用

1. 确认网关是 `IC.IHG2`、小程序是「全屋智控」一类 → [docs/01-hardware.md](docs/01-hardware.md)
2. 电脑版微信 + mitmproxy 抓包（不必动手机）→ [docs/02-capture.md](docs/02-capture.md)
3. 对照协议和指令字典 → [docs/03-protocol.md](docs/03-protocol.md)
4. 装集成、放好 `session.json` / `devices.json` → [docs/04-home-assistant.md](docs/04-home-assistant.md)
5. HomeKit Bridge 命名、房间、摄氏度坑 → [docs/05-homekit.md](docs/05-homekit.md)

动手前建议先扫一眼 [docs/06-pitfalls.md](docs/06-pitfalls.md)。证书和抓包文件用完按 [docs/07-privacy.md](docs/07-privacy.md) 清掉。

### HACS

自定义存储库填本仓库地址，类别选 Integration，搜索 `CloudThink BroadLink` 下载后重启 HA。会话文件仍需自己放到配置目录。

## 实际效果（我这套房子）

大约 7 个房间、40 个左右可控设备进 HA；灯有亮度/色温，空调有温度/模式/风速，窗帘有位置；HomeKit 里约 27 个配件，Siri 能直接控。

## 注意

- 只用在自己的设备上；私有协议，厂家随时可能改。
- 会话会过期，过期就重新抓包。
- 抓包会经过账号相关 HTTPS 流量，做完务必删证书和抓包文件。

MIT — 详见 [LICENSE](LICENSE)。

---

## English

Guide and reference Home Assistant integration for a **developer-installed BroadLink IHG2** whole-home system (WeChat mini-program only) into **HA → Apple Home**. Capture desktop WeChat traffic to BroadLink’s DuerOS houseproxy, replay it from HA, then bridge to HomeKit. See `docs/` for steps. Use only on devices you own.

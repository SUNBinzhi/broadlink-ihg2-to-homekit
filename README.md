[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.4%2B-41BDF5.svg)](https://www.home-assistant.io/)
[![HomeKit](https://img.shields.io/badge/Apple-HomeKit-black.svg)](https://www.apple.com/home-app/)
[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
[![GitHub stars](https://img.shields.io/github/stars/SUNBinzhi/broadlink-ihg2-to-homekit?style=social)](https://github.com/SUNBinzhi/broadlink-ihg2-to-homekit/stargazers)

# 开发商预装博联（BroadLink / IHG2）全屋智能 → Home Assistant → Apple 家庭

> 把「只能通过微信小程序控制」的开发商预装博联全屋智能，接入 Home Assistant，再桥接到 Apple 家庭，实现 Siri 语音控制与自动化。

本仓库记录一套**已在真实住宅跑通**的完整方法：抓包 → 协议分析 → 自建 HA 集成 → HomeKit 桥接。
不修改网关固件、不拆机、不动强电。

---

## 这套方案适合谁

如果你家满足下面任意两条，这个仓库大概率能帮到你：

- 精装房 / 开发商预装的全屋智能，品牌是**博联（BroadLink）**，网关型号标注 **IC.IHG2**
- 控制入口只有一个微信小程序，通常叫「**全屋智控**」（或类似名字）
- 小程序里能看到灯、窗帘、空调、新风、场景，但**没有任何开放接口**
- 想接 Home Assistant / HomeKit，但官方集成（`broadlink`）完全识别不到这些设备
- 问过厂家，回复「不对个人开放接口」

> 同类方案（如某些涂鸦贴牌、其他工程网关）思路相通，但协议细节不同，请以自己抓到的包为准。

## 原理一句话

小程序不是直连网关，而是调用**博联云**上的一个「小度 DuerOS houseproxy」接口。
拿到会话头和设备清单后，任何能上网的设备都能复刻同样的请求 —— 于是 HA 就能控制全屋。

```
微信小程序 ──HTTPS──▶ 博联云 houseproxy ──▶ IHG2 中控 ──▶ 灯 / 窗帘 / 空调 / 新风
                            ▲
                            └── 我们的 HA 集成（复刻同样的请求）
```

## 你需要准备什么

| 用途 | 硬件 | 说明 |
|---|---|---|
| 抓包 | 一台电脑（macOS / Windows） | 装电脑版微信 + mitmproxy，**不碰手机** |
| 跑 HA | NAS / 小主机 / 树莓派（Docker） | 需要 7×24 开机 |
| 语音 | iPhone / iPad | 用「家庭」App |
| 远程控制（可选） | Apple TV 或 HomePod | 作为家庭中枢 |
| 调试（可选） | 一台安卓手机 | 抓 BLE 或调试小程序 |

## 五步走

1. **确认系统**：看网关标签是不是 `IC.IHG2`，小程序是不是「全屋智控」→ [docs/01-hardware.md](docs/01-hardware.md)
2. **抓包**：电脑版微信 + mitmproxy，导出会话与请求 → [docs/02-capture.md](docs/02-capture.md)
3. **读协议**：认清 DuerOS 请求结构和指令字典 → [docs/03-protocol.md](docs/03-protocol.md)
4. **写集成**：装进 HA，按房间建条目 → [docs/04-home-assistant.md](docs/04-home-assistant.md)
5. **接 Siri**：HomeKit Bridge + 命名/房间/摄氏 → [docs/05-homekit.md](docs/05-homekit.md)

踩过的坑都在 [docs/06-pitfalls.md](docs/06-pitfalls.md)，**建议动手前先看一遍**。

## 仓库结构

```
.
├── README.md
├── docs/
│   ├── 01-hardware.md       # 硬件与系统识别
│   ├── 02-capture.md        # 抓包完整步骤
│   ├── 03-protocol.md       # 协议与指令字典
│   ├── 04-home-assistant.md # HA 自定义集成
│   ├── 05-homekit.md        # HomeKit / Siri
│   ├── 06-pitfalls.md       # 踩坑记录
│   └── 07-privacy.md        # 隐私与合规
├── custom_components/
│   └── cloudthink_broadlink/  # 参考实现（Python）
├── examples/
│   ├── session.json.example
│   └── devices.json.example
└── .gitignore               # 已经排除 session.json 等敏感文件
```

## 效果

- 7 个房间、约 40 个可控设备进入 HA
- 灯支持开关 / 亮度 / 色温，空调支持开关 / 温度 / 模式 / 风速，窗帘支持位置
- HomeKit 里 27 个配件，Siri 可直接说「把主卧空调调到 26 度」「关闭客厅布帘」
- 全屋场景可以做成按钮或自动化

## 重要声明

- 本项目仅用于**自有设备**的接入与自动化，请遵守博联、微信的服务条款。
- 接口是厂商私有协议，**可能随时变更**；会话会过期，需要重新抓包。
- 抓包会经过你账号的全部 HTTPS 流量，**请务必在完成后删除证书和抓包文件**，详见 [docs/07-privacy.md](docs/07-privacy.md)。
- 按本文操作造成的一切后果由使用者自行承担。

## License

MIT

---

## English summary

A practical, end-to-end guide for integrating a **developer-installed BroadLink (IHG2) whole-home system** — which normally can only be controlled by a WeChat mini program — into **Home Assistant** and **Apple Home / HomeKit (Siri)**.

The mini program talks to BroadLink's cloud through a **DuerOS ConnectedHome houseproxy** endpoint. By capturing that traffic (mitmproxy on desktop WeChat) and replaying the same requests, you can build a custom Home Assistant integration without touching firmware or wiring.

What's inside:

- How to identify the same hardware (`IC.IHG2` gateway, "全屋智控" mini program)
- Step-by-step HTTPS capture on a desktop (no phone needed)
- The DuerOS protocol: headers, device cookie, request/response shapes
- Command dictionary for lights, climate, covers and state queries
- A reference Home Assistant custom integration (multi-room, dimming, color temp)
- HomeKit Bridge setup, naming, room assignment and the Celsius/Fahrenheit pitfall
- A 24-item pitfalls list and a privacy/cleanup checklist

**Keywords:** BroadLink, IHG2, CloudThink, home assistant, homekit, siri, custom integration, hacs, smart home, developer pre-installed, 精装房, 全屋智能, 博联, 微信小程序.

> Use only on devices you own. Private protocol, may change at any time.

# 04 · Home Assistant 集成

## 1. 为什么写自定义集成，而不是 MQTT

| 方案 | 优点 | 缺点 |
|---|---|---|
| **自定义集成** | 实体原生、状态由协调器统一管理、可按房间配置 | 要写 Python |
| MQTT 桥接 | 与语言无关 | 需要额外 broker，实体是"影子"，配置分散 |
| RESTful / command_line | 最快 | 做不了气候/窗帘这类复杂实体 |

本仓库提供的是**自定义集成**参考实现（`custom_components/cloudthink_broadlink/`）。

## 2. 集成结构

```
custom_components/cloudthink_broadlink/
├── __init__.py        # 配置入口、协调器、设备筛选
├── api.py             # 调云端接口（同步 requests/urllib）
├── config_flow.py     # 选房间 → 选灯光 → 创建条目
├── const.py
├── entity.py          # 公共属性 / 状态读取
├── light.py           # 灯（含亮度、色温映射）
├── climate.py         # 空调
├── cover.py           # 窗帘
├── switch.py          # 新风等
├── sensor.py          # 环境传感器
├── manifest.json
├── strings.json
└── translations/
```

### 核心设计

1. **一个房间一个配置条目**，`entry.data = {"room": "主卧", "light": "主卧的灯"}`
2. **统一协调器**：`DataUpdateCoordinator` 每 20 秒轮询一次，控制后立即回读
3. **设备筛选**：按 `roomName` 取该房间的空调 / 窗帘 / 新风 / 传感器 + 一个灯组
4. **灯的策略**：优先用虚拟灯组；没有灯组时，把该房间所有灯都接进来

## 3. 请求实现要点

```python
def call(self, name, device, extra=None, namespace="DuerOS.ConnectedHome.Control"):
    session = json.loads(self.session_path.read_text())   # 每次重读，换会话不用重启
    payload = {
        "cookie": session["cookie"],
        "appliance": {
            "additionalApplianceDetails": device["additionalApplianceDetails"],
            "applianceId": device["applianceId"],
        },
        "applianceId": device["applianceId"],
    }
    if extra:
        payload.update(extra)
    body = {
        "header": {
            "messageId": f"wxmini_{random.randrange(10**9, 10**10)}",
            "name": name,
            "namespace": namespace,
            "payloadVersion": "1",
        },
        "payload": payload,
    }
    ...
```

> 状态查询建议用 `ReportStateRequest` + `Query` namespace（小程序原始用法）。

## 4. 灯：色温映射

云端给的是 **0–100 的百分比**，不是开尔文：

```python
MIN_KELVIN, MAX_KELVIN = 2700, 6500

def pct_to_kelvin(pct):
    return round(MIN_KELVIN + max(0, min(100, pct)) / 100 * (MAX_KELVIN - MIN_KELVIN))

def kelvin_to_pct(k):
    k = max(MIN_KELVIN, min(MAX_KELVIN, k))
    return round((k - MIN_KELVIN) / (MAX_KELVIN - MIN_KELVIN) * 100)
```

灯实体只声明 `ColorMode.COLOR_TEMP`，亮度 `0-255` 与云端 `0-100` 互转。

## 5. 空调：加上"一键开关"

HA 的 `climate.toggle` 需要实体声明 `TURN_ON` / `TURN_OFF` 特性，否则会报
`ServiceNotSupported`。所以：

```python
_attr_supported_features = (
    ClimateEntityFeature.TARGET_TEMPERATURE
    | ClimateEntityFeature.FAN_MODE
    | ClimateEntityFeature.TURN_ON
    | ClimateEntityFeature.TURN_OFF
)

async def async_turn_on(self):
    await self.coordinator.command(self.device, "TurnOnRequest")

async def async_turn_off(self):
    await self.coordinator.command(self.device, "TurnOffRequest")
```

这样 HomeKit 里的电源按钮、HA 里的 `climate.toggle` 才能用。

## 6. 部署步骤

1. 把 `custom_components/cloudthink_broadlink/` 复制到 HA 配置目录的 `custom_components/`
2. 新建 `config/cloudthink_broadlink/`，放入：
   - `session.json`（见 02 篇）
   - `devices.json`（全量设备清单）
3. **重启 HA**（Python 模块必须重启才生效）
4. 设置 → 设备与服务 → 添加集成 → `CloudThink BroadLink`
5. 选择房间 → 选择灯光（默认"自动"）→ 提交
6. 每个房间重复一次

## 7. 文件权限

```bash
chmod 600 config/cloudthink_broadlink/session.json
```

> 注意：部分 NAS（如极空间）的 SMB 挂载会忽略 chmod，需要在 NAS 的文件管理器里设置。

## 8. 更新与会话过期

- **换会话**：只替换 `session.json`，不需要重启 HA（代码每次请求都会重读）
- **改设备清单**：替换 `devices.json` 后重新加载条目
- **改代码**：必须重启 HA

## 9. 与小米等其它生态共存

如果家里还有小米设备，建议：

- 小米设备用**官方 Xiaomi Home** 集成（支持中枢网关本地推送）
- 博联设备用本项目
- 两者在 HA 里统一编排，再一起桥接到 HomeKit

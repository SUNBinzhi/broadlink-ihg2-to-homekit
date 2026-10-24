# 03 · 协议与指令字典

> 本项目的核心：把小程序用的这套「小度 DuerOS ConnectedHome」接口读懂。

## 1. 接口

```
POST https://app-service-chn-<你的实例>.ibroadlink.com/appfront/v1/houseproxy/v1/dueros
Content-Type: application/json
```

实例域名每个人都有差异，以抓包结果为准。

## 2. 请求头（鉴权）

| 头 | 说明 |
|---|---|
| `loginsession` | 登录会话，**最关键**，会过期 |
| `userid` | 用户 ID |
| `familyid` | 家庭 ID |
| `licenseid` | 授权 ID |
| `activationcode` | 固定授权码 |
| `companyid` | 厂商 ID |
| `Referer` | 小程序来源，可保留 |
| `xweb_xhr` | `1` |

`datatrace` 是埋点，可省略；`messageid` 仅回显。

## 3. 设备 cookie

请求体里的 `cookie` 是 Base64 的 JSON：

```json
{"device":{"aeskey":"<16字节hex>","id":1,
 "did":"<设备ID>","pid":"<产品ID>","mac":"<MAC>"}}
```

这个 cookie 对所有子设备通用，换设备时不需要改。

## 4. 请求结构

```json
{
  "header": {
    "messageId": "wxmini_123456",
    "name": "TurnOnRequest",
    "namespace": "DuerOS.ConnectedHome.Control",
    "payloadVersion": "1"
  },
  "payload": {
    "cookie": "<Base64 设备 cookie>",
    "appliance": {
      "additionalApplianceDetails": { "...": "取自设备清单，原样带回" },
      "applianceId": "<设备 ID>"
    },
    "applianceId": "<设备 ID>"
  }
}
```

> `additionalApplianceDetails` 必须与清单里那条设备记录**完全一致**，不能自己拼。

## 5. 指令字典

### 灯 / 开关 / 灯组

| 功能 | header.name | payload 附加 |
|---|---|---|
| 开 | `TurnOnRequest` | 无 |
| 关 | `TurnOffRequest` | 无 |
| 亮度 | `SetBrightnessPercentageRequest` | `{"brightness":{"value":0-100}}` |
| 色温 | `SetColorTemperatureRequest` | `{"colorTemperatureInKelvin":0-100}` |

> ⚠️ **字段名有坑**：`colorTemperatureInKelvin` 实际是 **0–100 的百分比**，不是开尔文。
> 接 HA 时需要自己映射到 2700–6500K。

### 空调

| 功能 | header.name | payload 附加 |
|---|---|---|
| 开 / 关 | `TurnOnRequest` / `TurnOffRequest` | 无 |
| 温度 | `SetTemperatureRequest` | `{"targetTemperature":{"value":16-30,"scale":"CELSIUS"}}` |
| 模式 | `SetModeRequest` | `{"mode":{"deviceType":"AIR_CONDITION","value":"COOL"}}` |
| 风速 | `SetFanSpeedRequest` | `{"fanSpeed":{"value":1-4}}` |

模式取值：`COOL` 制冷、`HEAT` 制热、`FAN` 送风、`DEHUMIDIFICATION` 除湿、`AUTO` 自动。

风速取值：`1` 自动、`2` 低、`3` 中、`4` 高（与微信小程序显示一致）。

### 窗帘 / 窗纱

| 功能 | header.name | payload 附加 |
|---|---|---|
| 开 | `TurnOnRequest` | `{"DeltaValue":{"value":100}}` |
| 关 | `TurnOffRequest` | `{"DeltaValue":{"value":0}}` |
| 任意位置 | `TurnOnRequest` | `{"DeltaValue":{"value":0-100}}` |

> 窗帘**没有** `position` 字段，位置就是 `DeltaValue`。电机走完全程约 10 秒。

### 查询

| 功能 | header.name | namespace |
|---|---|---|
| 查单设备 | `ReportStateRequest` | `DuerOS.ConnectedHome.Query` |
| 全屋发现 | `DiscoverAppliancesRequest` | `DuerOS.ConnectedHome.Discovery` |

返回的 `payload.attributes` 是键值数组：

| 字段 | 含义 |
|---|---|
| `turnOnState` | `ON` / `OFF` |
| `targetTemperature` / `temperature` | 空调目标温度 / 室温 |
| `mode` / `fanSpeed` | 空调模式 / 风速 |
| `brightness` | 亮度 0–100 |
| `colorTemperatureInKelvin` | 色温 0–100（百分比） |
| `degree` | 窗帘位置 0–100 |

## 6. 实测性能

| 指标 | 实测 |
|---|---|
| 单条指令往返 | 约 240 ms |
| 云端吞吐 | 约 5.5 条/秒 |
| 22 路灯并发 | 约 4 秒 |
| 窗帘全程 | 约 10 秒 |

吞吐上限来自**网关侧串行处理**，提高并发收益有限。批量控制 20 路以上时，
UI 应做「乐观更新」，不要等云端回执。

## 7. 设备类型速查

| `applianceTypes` | 含义 | 可做 |
|---|---|---|
| `LIGHT` | 灯 / 灯组 | 开关、亮度、色温 |
| `SWITCH` | 开关 / 面板背光 | 开关 |
| `AIR_CONDITION` | 空调 | 开关、温度、模式、风速 |
| `CURTAIN` / `CURT_SIMP` | 窗帘 / 窗纱 | 开关、位置 |
| `AIR_FRESHER` | 新风 | 开关 |
| `SCENE_PANEL` | 情景面板按键 | 未验证 |
| `ENVIRONMENT_SENSOR` | 环境监测 | 只读 |
| `GATEWAY` | 网关 | 只读 |
| `SMART_SCREEN` | 智慧屏 | 只读 |
| `DEHUMIDIFIER` | 除湿机 | 开关；湿度/温度/目标湿度只读 |

## 8. 命名规律

- 虚拟灯组（会客组、回家组等）的 `applianceId` 通常以网关 ID 开头，后接 `00003faa`
- 真实子设备通常以 `00000000000000000000` 开头
- 同名设备很多（「窗帘」「筒灯」），**必须以 `applianceId` 区分**

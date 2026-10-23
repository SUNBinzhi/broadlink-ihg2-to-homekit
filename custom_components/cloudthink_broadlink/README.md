# cloudthink_broadlink

参考实现：把博联云端 houseproxy 接口封装成 Home Assistant 集成。

## 安装

1. 复制本目录到 HA 的 `config/custom_components/cloudthink_broadlink/`
2. 在 `config/cloudthink_broadlink/` 放入：
   - `session.json`（见根目录 `examples/session.json.example`）
   - `devices.json`（见根目录 `examples/devices.json.example`）
3. 重启 Home Assistant
4. 设置 → 设备与服务 → 添加集成 → `CloudThink BroadLink`
5. 选择房间 → 选择灯光

## 说明

- 每个房间创建一个配置条目
- 灯优先使用虚拟灯组；没有灯组时接入该房间所有灯
- 状态轮询 20 秒，控制后立即回读
- `session.json` 可热替换，不需要重启

## 注意

本实现针对作者自家的设备结构做了适配（例如灯组命名），
你家如果没有同名设备，请在向导里手动选择灯光，或修改
`__init__.py` 里的 `pick_lights()`。

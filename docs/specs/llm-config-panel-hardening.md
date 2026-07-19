# LLM 配置页短期硬化说明

本文记录 LLM 配置页在 2026-07 的短期修复范围。目标是减少“测试成功但进游戏失败”、本地模型误报、旧密钥被带到新服务商、以及默认模型漂移导致的一键填充不可用。

## 背景

LLM 配置页承担三个职责：

1. 展示当前保存的 LLM profile，但不回传 API Key。
2. 允许用户通过 preset 快速填写 Base URL、模型名和 API 格式。
3. 在保存前测试连通性，并让新开局初始化使用同一套语义。

现有风险集中在“测试链路”和“运行时链路”判定不完全一致：页面测试只验证常规模型，初始化会验证常规模型和快速模型；页面允许 Ollama 空 key，后端原先又按所有服务都必须有 API Key 处理。另一个安全风险是切换 Base URL 时旧密钥可能被静默沿用到新 endpoint。

## 短期目标

1. 配置完整性判断统一：本地 OpenAI-compatible endpoint 可不填 API Key，远端和 Anthropic 仍要求 API Key。
2. “测试连通性并保存”必须覆盖常规模型和快速模型；两个模型完全相同时只测一次。
3. 切换到本地 endpoint 或切换 credential scope 时，如果用户没有输入新 key，则保存时清除旧 key，避免旧云端 key 被带到新 endpoint。
4. `max_concurrent_requests` 在后端 schema 层约束到 `1..50`。
5. 保存和测试前对 Base URL、模型名、模式、API 格式和 API Key 做首尾空白裁剪。
6. LLM 测试请求使用更长前端 timeout，覆盖本地模型首次加载。
7. 默认 preset 保持在前端内置，但用测试锁定关键模型名，降低误拼或退回旧模型的风险。

## 非目标

1. 本轮不把 preset 下沉到后端或外置 JSON。
2. 本轮不引入 provider registry、模型价格表或自动在线更新。
3. 本轮不改变 secrets 的持久化文件结构，仍由 `SettingsService` 保存到 `secrets.json`。
4. 本轮不做全语言文案补全；日常 i18n 仍按 Phase 1 优先维护 `zh-CN`。

## 设计

### 配置完整性

统一函数位于 `src/utils/llm/validation.py`：

- `is_local_llm_endpoint(base_url)`：识别 `localhost`、`127.0.0.1`、`::1`、`0.0.0.0`。
- `llm_requires_api_key(base_url, api_format)`：Anthropic 始终需要 key；OpenAI-compatible 只有远端 endpoint 需要 key。
- `is_llm_runtime_configured(profile, api_key)`：供状态接口和运行时状态判断复用。

### 连通性测试

新增 profile 级连通性 helper：

1. 先检查 Base URL、常规模型、快速模型和 key 要求。
2. 构造 normal config 进行测试。
3. 如果 fast 模型与 normal 模型不同，则构造 fast config 再测一次。
4. 返回错误时保留“智能模型 / 快速模型”前缀，让用户知道哪个槽位失败。

`/api/settings/llm/test` 和兼容层测试入口都应走同一 helper，避免页面测试与初始化阶段继续分叉。

### 旧密钥清理

前端不读取真实 key，因此只能按保存前状态做安全判断：

1. 记录当前已保存 profile 的 Base URL credential scope。
2. 保存时如果存在已保存 key、用户没有输入新 key、当前 Base URL scope 与原 scope 不同，则设置 `clear_api_key=true`。
3. 保存到本地 OpenAI-compatible endpoint 且用户没有输入新 key 时，也设置 `clear_api_key=true`。

后端仍以 `clear_api_key` 为最终真源，清除后响应中的 `has_api_key=false`。

### 输入约束

后端 schema 对 `max_concurrent_requests` 使用 `ge=1, le=50`。`SettingsService` 在测试和保存链路统一裁剪首尾空白。

### 前端超时

`llmApi.testConnection()` 使用 150 秒 timeout，匹配本地模型首次加载和后端 120 秒请求窗口。

## 验证

短期测试覆盖：

1. 本地 Ollama 空 key 状态为 configured。
2. 远端 OpenAI-compatible 空 key 状态为未配置。
3. 本地 Ollama 空 key 初始化检查会继续进入真实连通性测试。
4. 页面测试接口会测试 normal 和 fast 两个模型。
5. normal 和 fast 相同时只测试一次。
6. 保存时 trim LLM profile 字段。
7. 非法并发数被 schema 拒绝。
8. 前端切换本地或新 Base URL 且没有输入新 key 时发送 `clear_api_key=true`。
9. 前端 LLM 测试使用长 timeout。
10. 关键 preset 模型名由前端单元测试锁定。

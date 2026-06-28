# Item Icon Generation Spec

## 背景

物品详情、角色装备、区域商店和后续自定义内容需要稳定的像素风图标。头像系统已经独立存在，本方案只覆盖非头像的物品类资产。

首批范围：

- 兵器：`static/game_configs/weapon.csv`
- 丹药：`static/game_configs/elixir.csv`
- 辅助装备：`static/game_configs/auxiliary.csv`
- 功法：`static/game_configs/technique.csv`
- 外挂：`static/game_configs/goldfinger.csv`

生态资源范围：

- 材料：`static/game_configs/material.csv`
- 动物：`static/game_configs/animal.csv`
- 植物：`static/game_configs/plant.csv`
- 矿脉：`static/game_configs/lode.csv`
- 阵盘/阵法道具：如果未来从纯数值配置变成可携带物品，应并入物品图标系统
- 秘境/区域/宗门不纳入本系统；它们属于地图或面板视觉资产，不应和物品图标混用

## 目标

1. 批量生成可审查、可复现的像素风物品图标。
2. 支持 3x3 或 4x4 contact sheet 大图生成，再切分成单图。
3. 生成阶段使用纯色背景，后处理转透明 PNG。
4. 前端通过稳定 key 显示图标，并支持兜底图像。
5. API key 只允许来自环境变量或被 gitignore 的 `.env` 文件，不得进入 git。

## 非目标

1. 不为 avatar 生成头像。
2. 不在前端直接调用 fal、Tabcode 或 OpenAI 图像 API。
3. 不把原始大图、中间切图和密钥打进发布包。

## 工具结构

当前工具目录为 `tools/item_icons/`：

- `config.py`：Tabcode/OpenAI-compatible 配置读取。
- `client.py`：Tabcode/OpenAI-compatible 图片调用。
- `utils/fal_client.py`：fal queue 图片调用、轮询、下载。
- `build_manifest.py`：从 CSV 生成待打图 manifest。
- `prompts.py`：contact sheet prompt 构造。
- `postprocess.py`：切图、绿幕 alpha、像素化。
- `generate_preview_sheet.py`：只生成一张 3x3 预览大图并处理小图，用于人工验收。

密钥约定：

- Tabcode：`ITEM_ICON_API_KEY`
- fal：`FAL_KEY` 或 `ITEM_ICON_FAL_KEY`
- 本地 `.env` 必须被 `tools/item_icons/.gitignore` 忽略。

## Provider 策略

### Tabcode

Tabcode 是 OpenAI Images API 兼容接口：

- Base URL：`https://api2.tabcode.cc/openai/draw/v1`
- Endpoint：`/images/generations`
- Model：`gpt-image-2`
- Response：`data[0].b64_json`

### fal

fal 使用队列 API：

- Submit：`POST https://queue.fal.run/{model}`
- Auth：`Authorization: Key <FAL_KEY>`
- 默认 model：`openai/gpt-image-2`
- 输入：`prompt`、`image_size`、`quality`、`num_images`、`output_format`
- 输出：`images[0].url`

fal 生成的 URL 需要立即下载到本地，因为远端媒体 URL 有保留期限。

## 生成批次

正式批量生成前先跑一张预览：

```powershell
$env:ITEM_ICON_FAL_KEY="..."
python -m tools.item_icons.generate_preview_sheet
```

预览通过后再批量：

1. `python -m tools.item_icons.build_manifest`
2. 按类别、视觉相似度和抽象程度分组。
3. 具体物品优先 4x4；抽象物品优先 3x3。
4. 每批保存 prompt、provider、model、request_id、远端 URL 和本地输出路径。
5. 人工抽查后发布到 `web/src/assets/icons/items/`。

## 后处理

1. 原始大图保存到 `raw/`。
2. 按固定 rows/columns 切到 `split/`。
3. 将 `#ff00ff` 背景转 alpha，保存到 `alpha/`。后处理不能只按精确颜色抠图，必须支持边缘采样、背景连通域删除和小噪点连通域清理。
4. 统一像素化到 128x128 PNG，保存到 `pixel/`。
5. 发布前检查：
   - PNG 尺寸统一。
   - 四角透明。
   - 主体非空。
   - 文件名和 manifest key 对齐。

## 前端接入设计

建议新增：

- `web/src/assets/icons/items/*.png`
- `web/src/utils/itemIcons.ts`

解析顺序：

1. `item.icon_key` 精确命中。
2. 使用 `item.icon_category + item.id` 推断。
3. 使用类型/分类 fallback。
4. 使用 `fallback_unknown`。

展示位置：

- `EntityRow.vue`：名称左侧固定 24-28px 图标。
- `EntityDetailCard.vue`：标题区固定 48-64px 图标。

后端 DTO 可后续补充可选字段：

- `icon_key`
- `icon_category`

第一版也可以前端推断，等自定义内容链路稳定后再由后端显式提供。

## 范围判断

除了用户列出的兵器、丹药、辅助装备、功法、外挂，我建议把“材料”也纳入第二批。材料会在角色详情、掉落、采集、商店和事件奖励里出现，而且名称辨识度高，图标收益明显。

暂不建议纳入：

- 角色/avatar：已有头像。
- 宗门/地区/秘境：属于地图或组织视觉系统，不是物品。
- 情绪、资质、种族、道统：更适合标签或小型符号，不适合和物品图标混入同一批生成。

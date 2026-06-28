# Item Icon Generation

这个目录用于批量生成物品图标，目标覆盖：

- `weapon`：兵器
- `elixir`：丹药
- `auxiliary`：辅助装备
- `technique`：功法
- `goldfinger`：外挂
- `material`：其他材料

## Secrets

真实 key 放在 `tools/item_icons/.env`，该文件已由本目录 `.gitignore` 忽略。

```env
ITEM_ICON_API_KEY=sk-user-...
ITEM_ICON_API_BASE_URL=https://api2.tabcode.cc/openai/draw/v1
ITEM_ICON_API_MODEL=gpt-image-2
ITEM_ICON_API_SIZE=1024x1024
```

也可以通过同名环境变量注入，避免落盘。

## Connectivity

```powershell
$env:ITEM_ICON_API_KEY="sk-user-..."
python -m tools.item_icons.ping_api
```

成功后会写入 `tools/item_icons/connectivity.png` 和 `connectivity.json`。这些验证产物不会进 git。

## Manifest

```powershell
python -m tools.item_icons.build_manifest
```

脚本从 `static/game_configs/*.csv` 生成待打图清单，输出到 `manifest.generated.json`，该文件默认忽略。

## Postprocess

```powershell
python -m tools.item_icons.postprocess split raw/sheet.png split --columns 4 --rows 4 --prefix weapon_batch_001
python -m tools.item_icons.postprocess clean split/weapon_batch_001_01.png processed/weapon_1001.alpha.png
python -m tools.item_icons.postprocess pixelate processed/weapon_1001.alpha.png processed/weapon_1001.png
```

后续正式流水线建议：

1. 从 manifest 按 category 和视觉相似度分批，每批 9 或 16 个物品。
2. 用 `prompts.build_contact_sheet_prompt()` 生成 3x3 或 4x4 大图。
3. 切图、抠掉 `#ff00ff` 背景、像素化到统一尺寸。
4. 人工或脚本检查空白率、透明角、尺寸和文件名。
5. 发布到 `web/src/assets/icons/items/`，再生成前端映射文件。

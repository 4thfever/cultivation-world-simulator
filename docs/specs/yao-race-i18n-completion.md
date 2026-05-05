# 妖族与种族系统 i18n 补全 Spec

本文档记录妖族/种族系统近期新增文本的多语言补全范围、建议翻译、实施步骤与验收方式。

生成时间：2026-05-05

## 1. 背景

近期已加入妖族与种族相关功能：

1. 角色种族字段：人族、狐族、狼族、鸟族、蛇族、龟族。
2. 妖族种族描述与 effect。
3. 妖族动作与文本：吃凡人、休息、妖族采摘/狩猎文本等。
4. 角色详情面板 stats grid 新增“种族”字段，并可点击打开二阶详情。

开发阶段优先落了简体中文与必要占位，当前需要进入一次局部 i18n 补全，把本批新增文本翻译到所有启用语言。

当前启用语言以 `static/locales/registry.json` 为准：

1. `zh-CN`
2. `zh-TW`
3. `en-US`
4. `vi-VN`
5. `ja-JP`

## 2. 本次目标

本次目标是补齐“妖族与种族系统”新增 i18n 内容，不扩大到全项目翻译质量评审。

完成后应满足：

1. `python tools/i18n/generate_missing_report.py` 不再报告本批新增 key/msgid 缺失。
2. 前端 `game.info_panel.avatar.stats.race` 在所有启用语言中存在且翻译合理。
3. 后端 `RACE_*` 配置文本在所有启用语言中存在且翻译合理。
4. 修改 `.po` 源文件后重新构建 `.mo`。
5. 相关 i18n 测试通过。

## 3. 当前缺口报告

已运行：

```powershell
python tools/i18n/generate_missing_report.py
```

生成报告：

`i18n_missing_report.md`

当前报告显示缺口集中在两类。

### 3.1 前端缺口

缺失 key：

`info_panel.avatar.stats.race`

缺失文件：

1. `web/src/locales/zh-TW/game.json`
2. `web/src/locales/vi-VN/game.json`
3. `web/src/locales/ja-JP/game.json`

`en-US` 已存在。

### 3.2 后端配置文本缺口

缺失 msgid 文件：

1. `static/locales/zh-TW/game_configs_modules/race.po`
2. `static/locales/vi-VN/game_configs_modules/race.po`
3. `static/locales/ja-JP/game_configs_modules/race.po`

缺失 msgid：

1. `RACE_HUMAN_NAME`
2. `RACE_HUMAN_DESC`
3. `RACE_FOX_NAME`
4. `RACE_FOX_DESC`
5. `RACE_WOLF_NAME`
6. `RACE_WOLF_DESC`
7. `RACE_BIRD_NAME`
8. `RACE_BIRD_DESC`
9. `RACE_SNAKE_NAME`
10. `RACE_SNAKE_DESC`
11. `RACE_TURTLE_NAME`
12. `RACE_TURTLE_DESC`

`en-US` 已存在。

## 4. 文件范围

### 4.1 前端源文件

需要补：

1. `web/src/locales/zh-TW/game.json`
2. `web/src/locales/vi-VN/game.json`
3. `web/src/locales/ja-JP/game.json`

参考已存在文件：

1. `web/src/locales/zh-CN/game.json`
2. `web/src/locales/en-US/game.json`

### 4.2 后端 i18n 源文件

需要补：

1. `static/locales/zh-TW/game_configs_modules/race.po`
2. `static/locales/vi-VN/game_configs_modules/race.po`
3. `static/locales/ja-JP/game_configs_modules/race.po`

参考已存在文件：

1. `static/locales/zh-CN/game_configs_modules/race.po`
2. `static/locales/en-US/game_configs_modules/race.po`

### 4.3 构建产物

修改 `.po` 源文件后运行：

```powershell
python tools/i18n/build_mo.py
```

该命令会更新：

1. `static/locales/<lang>/LC_MESSAGES/messages.po`
2. `static/locales/<lang>/LC_MESSAGES/messages.mo`
3. `static/locales/<lang>/LC_MESSAGES/game_configs.po`
4. `static/locales/<lang>/LC_MESSAGES/game_configs.mo`

这些是构建产物，不应手动直接编辑。

## 5. 建议翻译

以下翻译是实现时建议采用的初稿，可在落地时微调，但应保持修仙语境清晰。

### 5.1 前端 stats label

| key | zh-CN | zh-TW | en-US | vi-VN | ja-JP |
|---|---|---|---|---|---|
| `game.info_panel.avatar.stats.race` | 种族 | 種族 | Race | Chủng tộc | 種族 |

### 5.2 种族名称

| msgid | zh-CN | zh-TW | en-US | vi-VN | ja-JP |
|---|---|---|---|---|---|
| `RACE_HUMAN_NAME` | 人族 | 人族 | Human | Nhân tộc | 人族 |
| `RACE_FOX_NAME` | 狐族 | 狐族 | Fox Yao | Hồ tộc | 狐族 |
| `RACE_WOLF_NAME` | 狼族 | 狼族 | Wolf Yao | Lang tộc | 狼族 |
| `RACE_BIRD_NAME` | 鸟族 | 鳥族 | Bird Yao | Điểu tộc | 鳥族 |
| `RACE_SNAKE_NAME` | 蛇族 | 蛇族 | Snake Yao | Xà tộc | 蛇族 |
| `RACE_TURTLE_NAME` | 龟族 | 龜族 | Turtle Yao | Quy tộc | 亀族 |

说明：

1. 英文使用 `Fox Yao` 而不是 `Fox Clan`，保留修仙语境中的“妖”概念。
2. 越南语使用汉越风格 `Nhân tộc / Hồ tộc / Lang tộc`，与修仙题材更贴近。
3. 日文使用 `人族 / 狐族 / 狼族 / 鳥族 / 蛇族 / 亀族`，简洁且符合题材。

### 5.3 种族描述

中文源文以 `static/locales/zh-CN/game_configs_modules/race.po` 为准。当前语义如下：

1. 人族：你是一个普通的人类。
2. 狐族：灵慧狡黠，善于观察灵植与人心。
3. 狼族：凶悍合群，擅长狩猎与搏杀。
4. 鸟族：身形轻捷，天生善于远行迁徙。
5. 蛇族：冷静狠毒，擅长潜伏与杀机。
6. 龟族：寿元悠长，最懂得休养生息。

建议翻译：

| msgid | zh-TW |
|---|---|
| `RACE_HUMAN_DESC` | 你是一個普通的人類 |
| `RACE_FOX_DESC` | 狐族靈慧狡黠，善於觀察靈植與人心。 |
| `RACE_WOLF_DESC` | 狼族凶悍合群，擅長狩獵與搏殺。 |
| `RACE_BIRD_DESC` | 鳥族身形輕捷，天生善於遠行遷徙。 |
| `RACE_SNAKE_DESC` | 蛇族冷靜狠毒，擅長潛伏與殺機。 |
| `RACE_TURTLE_DESC` | 龜族壽元悠長，最懂得休養生息。 |

| msgid | en-US |
|---|---|
| `RACE_HUMAN_DESC` | You are an ordinary human. |
| `RACE_FOX_DESC` | Fox yao are clever and perceptive, skilled at reading both spirit plants and people. |
| `RACE_WOLF_DESC` | Wolf yao are fierce and pack-minded, naturally gifted at hunting and close combat. |
| `RACE_BIRD_DESC` | Bird yao are light and swift, born for travel and migration. |
| `RACE_SNAKE_DESC` | Snake yao are calm and venomous, adept at lurking and striking with killing intent. |
| `RACE_TURTLE_DESC` | Turtle yao are long-lived and patient, masters of rest and recuperation. |

| msgid | vi-VN |
|---|---|
| `RACE_HUMAN_DESC` | Bạn là một con người bình thường. |
| `RACE_FOX_DESC` | Hồ tộc thông tuệ và giảo hoạt, giỏi quan sát linh thực lẫn lòng người. |
| `RACE_WOLF_DESC` | Lang tộc hung hãn và trọng bầy đàn, sở trường săn bắt và cận chiến. |
| `RACE_BIRD_DESC` | Điểu tộc nhẹ nhàng nhanh nhẹn, bẩm sinh giỏi đi xa và di cư. |
| `RACE_SNAKE_DESC` | Xà tộc lạnh tĩnh và hiểm độc, giỏi ẩn nấp và ra đòn sát cơ. |
| `RACE_TURTLE_DESC` | Quy tộc thọ nguyên dài lâu, tinh thông nghỉ ngơi và điều dưỡng. |

| msgid | ja-JP |
|---|---|
| `RACE_HUMAN_DESC` | あなたは普通の人間です。 |
| `RACE_FOX_DESC` | 狐族は聡く狡猾で、霊植と人心を見抜くことに長けている。 |
| `RACE_WOLF_DESC` | 狼族は獰猛で群れを重んじ、狩りと接近戦を得意とする。 |
| `RACE_BIRD_DESC` | 鳥族は身軽で素早く、遠行と渡りに生まれつき長けている。 |
| `RACE_SNAKE_DESC` | 蛇族は冷静で毒気を帯び、潜伏と殺機の一撃を得意とする。 |
| `RACE_TURTLE_DESC` | 亀族は長寿で辛抱強く、休息と養生を極めている。 |

## 6. 实施步骤

1. 打开 `i18n_missing_report.md`，确认缺口仍与本 spec 一致。
2. 在 `web/src/locales/zh-TW/game.json`、`vi-VN/game.json`、`ja-JP/game.json` 的 `game.info_panel.avatar.stats` 下补 `race`。
3. 在 `static/locales/zh-TW/game_configs_modules/race.po`、`vi-VN/game_configs_modules/race.po`、`ja-JP/game_configs_modules/race.po` 补齐 12 个 `RACE_*` msgid。
4. 如发现 `en-US` 中仍是中文占位，应顺手替换为本 spec 中英文译文。
5. 运行 `python tools/i18n/build_mo.py`。
6. 重新运行 `python tools/i18n/generate_missing_report.py`，确认本批缺口清零。
7. 运行测试。

## 7. 验收命令

建议先跑局部命令：

```powershell
python tools/i18n/generate_missing_report.py
python tools/i18n/build_mo.py
pytest tests/test_frontend_locales.py tests/test_backend_locales.py tests/test_i18n_integrity.py tests/test_i18n_modules.py -q
cd web
npm run test -- AvatarDetail --run
npm run type-check
```

最终回归：

```powershell
pytest
cd web
npm run test -- --run
npm run type-check
```

验收标准：

1. 缺失报告中不再出现 `info_panel.avatar.stats.race`。
2. 缺失报告中不再出现 `RACE_*` msgid。
3. 角色详情面板中“种族”在所有语言下都有 label。
4. 点击“种族”二阶面板时，种族名称、描述、效果说明均能显示对应语言文本。

## 8. 非目标

本 spec 不处理以下内容：

1. 妖族动作文本的翻译质量总审。
2. persona、world info、effect 文案的全语言润色。
3. 新语言接入。
4. i18n 工具链重构。
5. 机器翻译或外部翻译服务接入。

这些可以后续作为更大的 Phase 2 i18n 工作包处理。

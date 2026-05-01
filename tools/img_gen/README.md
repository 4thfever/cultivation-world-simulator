# 图片生成工具

本目录是本地资产生成工具集，当前只使用 Tabcode 的 OpenAI-compatible 图像接口。
接口配置、prompt 数据、生成脚本和后处理脚本都放在 `tools/img_gen/` 下。

图像生成设计原则见 [DESIGN.md](./DESIGN.md)。

## 初始化

先创建本地 env 文件：

```powershell
Copy-Item tools/img_gen/tabcode.env.example tools/img_gen/tabcode.env
```

然后在 `tools/img_gen/tabcode.env` 中填写：

```env
TABCODE_API_KEY=你的 key
```

`tabcode.env` 已被 `.gitignore` 忽略，不要提交真实 key。同名系统环境变量会覆盖
`tabcode.env` 中的值。

需要运行这些工具时，先安装本目录的工具依赖：

```powershell
pip install -r tools/img_gen/requirements.txt
```

## 任务入口

| 任务 | 运行文件 | 常用命令 | 默认输出 |
|---|---|---|---|
| 测试 Tabcode 生图是否可用 | `generate_preview.py` | `python tools/img_gen/generate_preview.py --open` | `tools/img_gen/tmp/preview/` |
| 生成人族女性头像 | `generate_avatars.py` | `python tools/img_gen/generate_avatars.py --gender female` | `tools/img_gen/tmp/avatars/female/` |
| 生成人族男性头像 | `generate_avatars.py` | `python tools/img_gen/generate_avatars.py --gender male` | `tools/img_gen/tmp/avatars/male/` |
| 生成人族部分头像 | `generate_avatars.py` | `python tools/img_gen/generate_avatars.py --gender female --limit 2 --realm qi_refining --realm golden_core` | `tools/img_gen/tmp/avatars/female/` |
| 生成妖族头像 | `generate_yaoguai_avatars.py` | `python tools/img_gen/generate_yaoguai_avatars.py` | `tools/img_gen/tmp/yaoguai_avatars/` |
| 生成妖族部分头像 | `generate_yaoguai_avatars.py` | `python tools/img_gen/generate_yaoguai_avatars.py --species fox --gender female --limit 1` | `tools/img_gen/tmp/yaoguai_avatars/` |
| 生成宗门图 | `generate_sects.py` | `python tools/img_gen/generate_sects.py` | `tools/img_gen/tmp/sects/` |
| 生成地图 tile 图 | `generate_tiles.py` | `python tools/img_gen/generate_tiles.py plain forest mountain` | `tools/img_gen/tmp/tiles/` |
| 后处理人族头像 | `postprocess_avatars.py` | `python tools/img_gen/postprocess_avatars.py --input-dir tools/img_gen/tmp/avatars/female --output-dir tools/img_gen/tmp/processed_avatars/female` | 指定的 `--output-dir` |
| 后处理妖族头像 | `postprocess_yaoguai_avatars.py` | `python tools/img_gen/postprocess_yaoguai_avatars.py` | `tools/img_gen/tmp/processed_yaoguai_avatars/` |
| 后处理宗门图 | `postprocess_sects.py` | `python tools/img_gen/postprocess_sects.py` | `tools/img_gen/tmp/processed_sects/` |

## 人族头像

人族头像 prompt 在 `prompts_avatars.py` 中维护。

每个性别当前有 48 个外貌描述，每个外貌会展开为 4 个境界：

```text
qi_refining   练气
foundation    筑基
golden_core   金丹
nascent_soul  元婴
```

默认完整生成量：

```text
48 个外貌 * 4 个境界 * 2 个性别 = 384 张
```

文件名会保留性别、外貌 index 和境界：

```text
tools/img_gen/tmp/avatars/female/female_001_qi_refining.png
tools/img_gen/tmp/avatars/female/female_001_foundation.png
tools/img_gen/tmp/avatars/female/female_001_golden_core.png
tools/img_gen/tmp/avatars/female/female_001_nascent_soul.png
```

同目录会写出 `manifest.json`，记录每张图的性别、外貌 index、境界英文 slug、境界中文名和完整 prompt。

## 妖族头像

妖族头像 prompt 在 `prompts_yaoguai_avatars.py` 中维护。

当前包含 5 个种族：

```text
fox     狐
wolf    狼
bird    鸟
snake   蛇
turtle  龟
```

每个种族 3 个外貌，每个外貌 4 个境界，男女各一套：

```text
5 个种族 * 3 个外貌 * 4 个境界 * 2 个性别 = 120 张
```

文件按种族和性别分目录：

```text
tools/img_gen/tmp/yaoguai_avatars/fox/female/fox_female_01_qi_refining.png
tools/img_gen/tmp/yaoguai_avatars/fox/female/fox_female_01_foundation.png
tools/img_gen/tmp/yaoguai_avatars/fox/female/fox_female_01_golden_core.png
tools/img_gen/tmp/yaoguai_avatars/fox/female/fox_female_01_nascent_soul.png
```

同样会写出 `manifest.json`，记录种族、性别、外貌 index、境界和完整 prompt。

## 后处理

头像后处理会裁边、抠纯白背景并缩放到默认 `512x512`。人族头像默认保留原文件名，
因此处理后仍然能看出 `gender_index_realm`。

```powershell
python tools/img_gen/postprocess_avatars.py --input-dir tools/img_gen/tmp/avatars/female --output-dir tools/img_gen/tmp/processed_avatars/female
python tools/img_gen/postprocess_avatars.py --input-dir tools/img_gen/tmp/avatars/male --output-dir tools/img_gen/tmp/processed_avatars/male
```

妖族头像后处理会递归处理种族和性别目录，并保留相同目录结构：

```powershell
python tools/img_gen/postprocess_yaoguai_avatars.py
```

宗门图只裁边和缩放，不抠白底：

```powershell
python tools/img_gen/postprocess_sects.py
```

## 维护提示

1. 真实 key 只放 `tools/img_gen/tabcode.env` 或系统环境变量。
2. 新增头像 prompt 时，注意人族男女数量一致。
3. 境界差异应尽量体现在原有可见特征的强弱、精致度和气质上，不要给所有角色套同一种灵纹或光效。
4. 背景相关约束应保持纯白、干净、无阴影、无渐变，方便后续抠图。

# 图片生成工具

本目录是本地资产生成工具集，当前使用 OpenAI-compatible 图像接口。
接口配置、prompt 数据、生成脚本和后处理脚本都放在 `tools/img_gen/` 下。

图像生成设计原则见 [DESIGN.md](./DESIGN.md)。

## 初始化

先创建本地 env 文件：

```powershell
Copy-Item tools/img_gen/image_api.env.example tools/img_gen/image_api.env
```

然后在 `tools/img_gen/image_api.env` 中填写：

```env
IMAGE_API_KEY=你的 key
```

`image_api.env` 已被 `.gitignore` 忽略，不要提交真实 key。同名系统环境变量会覆盖
`image_api.env` 中的值。

需要运行这些工具时，先安装本目录的工具依赖：

```powershell
pip install -r tools/img_gen/requirements.txt
```

## 任务入口

| 任务 | 运行文件 | 常用命令 | 默认输出 |
|---|---|---|---|
| 测试图像 API 是否可用 | `generate_preview.py` | `python tools/img_gen/generate_preview.py --open` | `tools/img_gen/tmp/preview/` |
| 第 1 段：生成人族女性练气基准头像 | `generate_avatars.py` | `python tools/img_gen/generate_avatars.py --gender female` | `tools/img_gen/tmp/avatars/female/` |
| 第 1 段：生成人族男性练气基准头像 | `generate_avatars.py` | `python tools/img_gen/generate_avatars.py --gender male` | `tools/img_gen/tmp/avatars/male/` |
| 第 2 段：由人族练气图编辑后三境界 | `edit_avatar_realms.py` | `python tools/img_gen/edit_avatar_realms.py --gender female` | 默认写回输入目录 |
| 第 1 段：生成妖族练气基准头像 | `generate_yaoguai_avatars.py` | `python tools/img_gen/generate_yaoguai_avatars.py` | `tools/img_gen/tmp/yaoguai_avatars/` |
| 第 2 段：由妖族练气图编辑后三境界 | `edit_yaoguai_avatar_realms.py` | `python tools/img_gen/edit_yaoguai_avatar_realms.py` | 默认写回输入目录 |
| 生成宗门图 | `generate_sects.py` | `python tools/img_gen/generate_sects.py` | `tools/img_gen/tmp/sects/` |
| 生成地图 tile 图 | `generate_tiles.py` | `python tools/img_gen/generate_tiles.py plain forest mountain` | `tools/img_gen/tmp/tiles/` |
| 后处理人族头像 | `postprocess_avatars.py` | `python tools/img_gen/postprocess_avatars.py --input-dir tools/img_gen/tmp/avatars/female --output-dir tools/img_gen/tmp/processed_avatars/female` | 指定的 `--output-dir` |
| 后处理妖族头像 | `postprocess_yaoguai_avatars.py` | `python tools/img_gen/postprocess_yaoguai_avatars.py` | `tools/img_gen/tmp/processed_yaoguai_avatars/` |
| 发布头像到游戏 assets | `publish_avatar_assets.py` | `python tools/img_gen/publish_avatar_assets.py --use-processed` | `assets/avatars/` 与 `assets/yao/` |
| 后处理宗门图 | `postprocess_sects.py` | `python tools/img_gen/postprocess_sects.py` | `tools/img_gen/tmp/processed_sects/` |

所有生成和编辑脚本默认遇到已存在的目标文件会跳过，避免重复扣费。需要重跑时加
`--overwrite`。

## 人族头像

人族头像 prompt 在 `prompts_avatars.py` 中维护。

当前流程分两段：

1. 文生图生成练气基准头像。
2. 用练气图作为输入图，通过图片编辑接口生成筑基、金丹、元婴。

每个性别当前有 48 个外貌描述。完整跑完后：

```text
48 个外貌 * 4 个境界 * 2 个性别 = 384 张
```

先生成练气：

```powershell
python tools/img_gen/generate_avatars.py --gender female
python tools/img_gen/generate_avatars.py --gender male
```

再从练气图编辑后三境界：

```powershell
python tools/img_gen/edit_avatar_realms.py --gender female
python tools/img_gen/edit_avatar_realms.py --gender male
```

只试跑少量图：

```powershell
python tools/img_gen/generate_avatars.py --gender female --limit 2
python tools/img_gen/edit_avatar_realms.py --gender female --limit 2 --realm golden_core
```

文件名会保留性别、外貌 index 和境界：

```text
tools/img_gen/tmp/avatars/female/female_001_qi_refining.png
tools/img_gen/tmp/avatars/female/female_001_foundation.png
tools/img_gen/tmp/avatars/female/female_001_golden_core.png
tools/img_gen/tmp/avatars/female/female_001_nascent_soul.png
```

`manifest.json` 记录练气文生图任务。`realm_edit_manifest.json` 记录图片编辑任务，
包括源图、目标境界和完整 prompt。

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

每个种族 9 个外貌，每个外貌 4 个境界，男女各一套。完整跑完后：

```text
5 个种族 * 9 个外貌 * 4 个境界 * 2 个性别 = 360 张
```

先生成练气：

```powershell
python tools/img_gen/generate_yaoguai_avatars.py
```

再从练气图编辑后三境界：

```powershell
python tools/img_gen/edit_yaoguai_avatar_realms.py
```

如果已经生成过前 3 个外貌，直接运行以上命令即可；脚本默认会跳过已存在文件，只补齐新增的 4-9 号外貌。不要加 `--overwrite`，否则会重新生成旧图并重新扣费。

只试跑狐族女性第一个外貌：

```powershell
python tools/img_gen/generate_yaoguai_avatars.py --species fox --gender female --limit 1
python tools/img_gen/edit_yaoguai_avatar_realms.py --species fox --gender female --limit 1
```

文件按种族和性别分目录：

```text
tools/img_gen/tmp/yaoguai_avatars/fox/female/fox_female_01_qi_refining.png
tools/img_gen/tmp/yaoguai_avatars/fox/female/fox_female_01_foundation.png
tools/img_gen/tmp/yaoguai_avatars/fox/female/fox_female_01_golden_core.png
tools/img_gen/tmp/yaoguai_avatars/fox/female/fox_female_01_nascent_soul.png
```

同样会写出 `manifest.json` 和 `realm_edit_manifest.json`。

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

1. 真实 key 只放 `tools/img_gen/image_api.env` 或系统环境变量。
2. 新增头像 prompt 时，注意人族男女数量一致。
3. 练气图是后三境界编辑的源图，不要随意删除。
4. 境界差异应尽量体现在原有可见特征的强弱、精致度和气质上，不要给所有角色套同一种灵纹或光效。
5. 背景相关约束应保持纯白、干净、无阴影、无渐变，方便后续抠图。
6. 图生图编辑时，必须保持输入图的像素风格、低细节程度和 Q 版二次元漫画风，禁止把头像改成写实、高清插画、厚涂或过度精细风格。
7. 图生图编辑时，还要保护角色识别特征：脸型、五官比例、肤色倾向、发型、发色、瞳色、瞳孔形状、表情基调、原有面部标记、主要饰物、主体大小、头肩占比和纯白背景。
8. 妖族图生图编辑还要额外保护种族特征的位置和基本形状，例如狐耳、狼耳、耳羽、竖瞳、鳞纹、龟甲纹、脸颊纹样等。

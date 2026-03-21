---
description: 小故事（Story Event）系统规范
globs: src/classes/story_event_service.py, src/classes/action/**/*.py, src/classes/mutual_action/**/*.py, src/classes/gathering/**/*.py, src/systems/battle.py, src/systems/fortune.py, static/config.yml, tests/**/*.py
---

# 小故事系统规范 (Story Event System)

本规范定义“小故事”在本项目中的统一生成方式。目标是避免在各处直接散落 `StoryTeller.tell_story()` 调用，保持概率入口清晰、类型一致、前后端语义稳定。

## 1. 统一入口

* 所有新的“小故事”生成逻辑，必须统一通过 `src/classes/story_event_service.py`。
* Action / MutualAction / Gathering / System 负责生成“事实事件”和整理故事输入，不直接决定故事文本事件的构造细节。
* 除 `StoryEventService` 外，业务代码应避免直接 new `Event(..., is_story=True)`。

## 2. 触发时机

* 小故事是“结果事件”的可选扩展层。
* 推荐顺序：
  1. 先结算数值与状态。
  2. 生成基础结果事件（`is_major=True/False`）。
  3. 再调用 `StoryEventService.maybe_create_story(...)` 或 `maybe_create_gathering_story(...)`。
* 若未命中概率，则直接跳过，不补占位事件，不在前端事件栏显示空故事。

## 3. 类型与概率

* 非 Gathering 小故事必须使用 `StoryEventKind` 分类，不要在各业务文件里手写一套新概率字段。
* 概率单一真相源为 `static/config.yml -> game.story.probabilities`。
* `gathering` 类型固定为 `100%`，不得在业务代码中重复加概率判断。

## 4. 事件语义

* 事实性结果事件：
  * 继续按原业务语义设置 `is_major=True/False`。
* LLM 展开的故事正文：
  * 统一使用 `is_story=True`。
  * 不再把长篇故事正文记为 `is_major=True`。
* `is_story=True` 事件仍会进入事件栏与分页接口，但不应当作为长期记忆事实去替代基础结果事件。

## 5. 新增故事入口时的选择原则

* 高频、重复、缺少戏剧性的动作，默认不要直接加故事。
* 更适合接入低概率故事的入口包括：
  * 明显的双人社交结果（送礼、传道、交谈、茶会、下棋）
  * 有结果性的 crafting / progression（炼丹、铸造、御兽、兵器成长）
  * 高叙事张力的大事件（战斗、表白、双修、结拜、突破、闭关）

## 6. 测试要求

* 调整或新增小故事逻辑时，必须补测试。
* 测试应显式控制 `StoryEventService.should_trigger(...)`，不要默认依赖真实随机数。
* Gathering 相关测试应验证其故事事件为 `is_story=True`，且路径不受概率影响。

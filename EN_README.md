<!-- Language / 语言 -->
<h3 align="center">
  <a href="README.md">🇨🇳 中文</a> · <a href="EN_README.md">🇺🇸 English</a>
</h3>
<p align="center">— ✦ —</p>

# Cultivation World Simulator

![GitHub stars](https://img.shields.io/github/stars/4thfever/cultivation-world-simulator?style=social)
[![Bilibili](https://img.shields.io/badge/Bilibili-Watch_Video-FB7299?logo=bilibili)](https://space.bilibili.com/527346837)
![QQ Group](https://img.shields.io/badge/QQ%20Group-1071821688-deepskyblue?logo=tencent-qq&logoColor=white)

![Last Commit](https://img.shields.io/github/last-commit/4thfever/cultivation-world-simulator)
![Commit Activity](https://img.shields.io/github/commit-activity/y/4thfever/cultivation-world-simulator)
![Repo Size](https://img.shields.io/github/repo-size/4thfever/cultivation-world-simulator)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

![Status](https://img.shields.io/badge/Status-Alpha-tomato)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)
![Genre: Xianxia](https://img.shields.io/badge/Genre-Xianxia-red)
![Powered by LLM](https://img.shields.io/badge/Powered%20by-LLM-0077B5)
![AI Agent](https://img.shields.io/badge/AI-Agent-orange)
![OpenAI Compatible](https://img.shields.io/badge/OpenAI%20API-Compatible-412991)

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi&logoColor=white)
![Vue](https://img.shields.io/badge/Vue.js-3.x-4FC08D?style=flat&logo=vuedotjs&logoColor=white)
![TypeScript](https://img.shields.io/badge/typescript-%23007ACC.svg?style=flat&logo=typescript&logoColor=white)
![Vite](https://img.shields.io/badge/vite-%23646CFF.svg?style=flat&logo=vite&logoColor=white)
![PixiJS](https://img.shields.io/badge/PixiJS-E72264?style=flat&logo=pixijs&logoColor=white)

<p align="center">
  <img src="assets/screenshot.gif" alt="Game Demo" width="100%">
</p>

> **An AI-driven cultivation world simulator that aims to create a truly living, immersive xianxia world.**

## 📖 Introduction

This is an **AI-driven open-world cultivation simulator**.

Unlike traditional RPGs where you play a specific character, here **you play as the "Heavenly Dao" (God)**.
You don't need to personally fight monsters or level up. Instead, you observe all living beings from a god's perspective. In an open world woven together by rules and AI, you witness the rise and fall of sects and the emergence of prodigies. You can quietly watch the world change, or bring down tribulations and alter minds, subtly intervening in the world's progress.

### ✨ Core Highlights

- 👁️ **Play as "Heavenly Dao" (God Perspective)**: You are not a cultivator, but the **Heavenly Dao** controlling the world's rules. Observe the myriad forms of life and experience their joys and sorrows.
- 🤖 **Fully AI-Driven**: Every NPC is independently driven by LLMs, with unique personalities, memories, relationships, and behavioral logic. They make decisions based on the current situation, have love and hate, form factions, and even defy the heavens to change their fate.
- 🌏 **Rules as the Cornerstone**: The world runs on a rigorous numerical system including spiritual roots, realms, cultivation methods, and lifespans. AI imagination is constrained within a reasonable cultivation logic framework, ensuring the world is authentic and credible.
- 🦋 **Emergent Storytelling**: Even the developer doesn't know what will happen next. There is no preset script, only world evolution woven from countless causes and effects. Sect wars, righteous vs. demonic conflicts, the fall of geniuses—all are deduced autonomously by the world's logic.

<table border="0">
  <tr>
    <td width="33%" valign="top">
      <h4 align="center">Character Panel</h4>
      <img src="assets/角色.png" width="100%" />
      <br/><br/>
      <h4 align="center">Personality Traits</h4>
      <img src="assets/特质.png" width="100%" />
    </td>
    <td width="33%" valign="top">
      <h4 align="center">Sect System</h4>
      <img src="assets/宗门.png" width="100%" />
      <br/><br/>
      <h4 align="center">Life Experiences</h4>
      <img src="assets/经历.png" width="100%" />
    </td>
    <td width="33%" valign="top">
      <h4 align="center">Independent Thinking</h4>
      <img src="assets/思考.png" width="100%" />
      <br/><br/>
      <h4 align="center">Short/Long Term Goals</h4>
      <img src="assets/目标.png" width="100%" />
      <br/><br/>
      <h4 align="center">Nicknames</h4>
      <img src="assets/绰号.png" width="100%" />
    </td>
  </tr>
</table>

### Why make this?
The worlds in cultivation novels are fascinating, but readers can only ever observe a corner of them.

Cultivation games are either completely scripted or rely on simple state machines designed by humans, often resulting in forced and unintelligent behaviors.

With the advent of Large Language Models, the goal of making "every character alive" seems reachable.

I hope to create a pure, joyful, direct, and living sense of immersion in a cultivation world. Not a pure marketing tool for some game company, nor pure research like "Stanford Town", but an actual world that provides players with real immersion.

## Contact

If you have any questions or suggestions, feel free to open an Issue or Pull Request.  
You're also welcome to leave a message on my [Bilibili account](https://space.bilibili.com/527346837)!  
You can also join the QQ group for discussion: 1071821688. Verification answer is my Bilibili nickname.  

## Development Progress

### 🏗️ Foundation
- ✅ World map basics, time, event system
- ✅ Diverse terrain types (plain, mountain, forest, desert, water, etc.)
- ✅ Web-based frontend interface
- ✅ Simulation framework
- ✅ Configuration files
- ✅ Standalone release (packaged exe)
- ✅ Menu bar & Save & Load
- ✅ Flexible custom LLM interface

### 🗺️ World System
- ✅ Basic tile mechanics
- ✅ Normal, cultivate, city, sect regions
- ✅ Same-tile NPC interactions
- ✅ Qi distribution and yields
- ✅ World event

### 👤 Character System
- ✅ Core attributes
- ✅ Cultivation realms
- ✅ Spiritual roots
- ✅ Basic movement actions
- ✅ Trait & Personality
- ✅ Breakthrough system
- ✅ Relationships
- ✅ Interaction range
- ✅ Effect system: buffs/debuffs
- ✅ Techniques
- ✅ Combat equipment & auxiliary equipment
- ✅ Short/Long term memory
- ✅ Character's short and long term objectives, supporting player active setting
- ✅ Avatar nicknames
- [ ] Character compatibility
- [ ] Life Skills
  - ✅ Forging
  - [ ] Alchemy
  - [ ] Planting
  - [ ] Taming
  - [ ] Evolving skills
- [ ] Mortals
- [ ] Prodigies (stronger abilities and AI)

### 🏛️ Organizations
- [ ] Sect system
  - ✅ Settings, techniques, healing, base, styles
  - ✅ Special sect actions: Hehuan Sect (dual cultivation), Hundred Beasts Sect (beast taming)
  - ✅ Sect tiers
  - [ ] Sect will AI
  - [ ] Sect tasks
- [ ] Clans
- [ ] Court/Empire (TBD)
- [ ] Inter-organization relations

### ⚡ Action System
- ✅ Basic movement
- ✅ Action execution framework
- ✅ Defined actions (rule-complete)
- ✅ Long-duration actions and settlement
  - ✅ Multi-month actions (cultivate, breakthrough, play, etc.)
  - ✅ Auto-settlement upon completion
- ✅ Multiplayer actions: initiator + responder flow
- ✅ LLM actions that affect relationships
- ✅ Systematic action registration and runtime logic

### 🎭 Event System
- ✅ Heaven-earth Qi fluctuations
- [ ] World-scale events:
  - [ ] Auctions
  - [ ] Secret realm exploration
  - [ ] Martial tournaments
  - [ ] Sect grand competition
- [ ] Sudden events
  - [ ] Treasure/cave emergence
- [ ] Natural events:
  - [ ] Natural disasters
  - [ ] Beast tides

### ⚔️ Combat
- ✅ Advantages and counters
- ✅ Win-rate estimation system

### 🎒 Items
- ✅ Basic items and spirit stones
- ✅ Trading mechanics

### 🌿 Ecology
- ✅ Animals and plants
- ✅ Hunting, gathering, materials
- [ ] Beasts/monsters

### 🤖 AI Enhancements
- ✅ LLM interface integration
- ✅ Character AI (rules AI + LLM AI)
- ✅ Coroutine decision making, async, multithreaded speedups
- ✅ Long-term planning and goal-driven behavior
- ✅ Reactive responses to external stimuli
- ✅ LLM-driven NPC dialogue, thinking, interaction
- ✅ LLM-generated micro-stories
- ✅ Use different models (max/flash) per task needs
- ✅ Micro-theaters
  - ✅ Battle micro-theaters
  - ✅ Dialogue micro-theaters
  - ✅ Multiple writing styles
- ✅ One-off choices (e.g., switch techniques or not)

### 🏛️ World Lore
- ✅ Inject basic world knowledge
- [ ] Dynamic worldview generation
- [ ] Dynamic history generation

### Specials
- ✅ Fortuitous encounters
- ✅ Tribulations & Heart devils
- [ ] Possession & Rebirth
- [ ] Opportunities & Karma
- [ ] Divination & Prophecy
- [ ] Male appearance female traits & Female appearance male traits
- [ ] Character Secrets & Two-faced
- [ ] Ascension to Upper Realm
- [ ] Formations
- [ ] Paths/Daos
- [ ] World Secrets & World Laws (Flexible customization)
- [ ] Gu Refining
- [ ] World-ending Crisis
- [ ] Become a Legend of Later Ages

### 🔭 Long-term
- [ ] ECS parallel toolkit
- [ ] Novelization/imagery/video for history and events
- [ ] Avatar calling MCP tools on their own

## Usage

### Run Steps
1. Clone the repo:
   ```bash
   git clone https://github.com/your-username/cultivation-world-simulator.git
   cd cultivation-world-simulator
   ```

2. Install dependencies:
   ```bash
   # Backend dependencies
   pip install -r requirements.txt
   
   # Frontend dependencies (Node.js environment required)
   cd web && npm install
   ```

3. Configure LLM:
   Edit `static/config.yml`:
   ```yaml
    llm:
      key: "your-api-key-here"        # your API key
      base_url: "https://api.xxx.com" # API base URL
      model_name: "model-name"        # main model name
      fast_model_name: "fast-model"   # fast model name
   ```
   Supports all API providers compatible with OpenAI interface format (e.g., Qwen, DeepSeek, SiliconFlow, OpenRouter, etc.)

   You can also configure LLM parameters directly in the frontend:
   
   <img src="assets/llm_config.png" alt="Frontend LLM Config" width="100%">

4. Run:
   ```bash
   # Start service (Recommended dev mode, automatically starts frontend)
   python src/server/main.py --dev
   ```
   The browser will automatically open the web frontend.


## Contributors
- Aku, for world design & discussion

## Acknowledgments
- Referenced some UI elements from ailifeengine
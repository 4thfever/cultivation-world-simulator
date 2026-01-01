<!-- Language / 语言 -->
<h3 align="center">
  <a href="README.md">🇨🇳 中文</a> · <a href="EN_README.md">🇺🇸 English</a>
</h3>
<p align="center">— ✦ —</p>

# Cultivation World Simulator

An AI-driven cultivation world simulator that aims to create a truly living, immersive xianxia world.

## Overview

Cultivation World Simulator combines traditional game-rule systems with large language models. By first establishing a complete ruleset for the cultivation world, it creates an autonomous, vibrant, immersive virtual world with emergent stories.

Core idea: **Build a credible rule-based world model first, then plug in AI to bring it to life.**

### Tech Stack

- **Frontend Rendering**: pygame (Web support in the future)
- **Simulation Engine**: custom event-driven simulator
- **World Model**: rule-based deterministic systems
- **AI Integration**: LLM-generated actions, decisions, micro-stories

## Background

I have been a long-time reader of xianxia novels, from classics to modern works. As a game AI practitioner, I believe today’s LLM capabilities are sufficient to support a xianxia-style world simulation.

However, LLM-only NPC decision/dialogue is not enough. A credible rule system must ground the world as the “world model”, and then AI makes it vivid.

I aim to create a pure, joyful, direct, living sense of immersion. Not a mere marketing demo, nor purely academic like “Stanford Town”, but a world that players can actually feel and inhabit.

If you like this project, consider starring it~ You can also watch intro videos for this project on my [Bilibili account](https://space.bilibili.com/527346837).

![Screenshot](assets/screenshot.gif)

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
- [ ] Dynamic worldview, map, history, sect, and notable figure generation

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
- [ ] Skill learning system:
  - [ ] Learnable skills
  - [ ] Life professions (alchemy, formations, planting, forging, etc.)
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
- [ ] Lore framework
- [ ] Worldbuilding
- [ ] Ancient history generation

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
   pip install -r requirements.txt
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

4. Run:
   Need to start both backend and frontend.
   
   ```bash
   # In project root
   python src/server/main.py
   ```
   The browser will automatically open the web frontend.


## Contributors
- Aku, for world design & discussion

## License

This project is licensed as specified in the [LICENSE](LICENSE) file.

## Acknowledgments
- Referenced some UI elements from ailifeengine

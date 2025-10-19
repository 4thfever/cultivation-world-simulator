<!-- Language / 语言 -->
<p align="center">
  <a href="README.md">🇨🇳 中文</a> · <a href="EN_README.md">🇺🇸 English</a>
</p>
<p align="center">— ✦ —</p>

# Cultivation World Simulator

An AI-augmented, rules-driven cultivation world simulator aimed at creating a truly living and immersive xianxia world.

## Overview

Cultivation World Simulator combines traditional deterministic rule systems with modern AI. It models terrains, characters, cultivation system, relationships, and more, to form an autonomous, vibrant virtual world.

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

If you like this project, consider starring it. You can also watch an intro video on my Bilibili: [`link`](https://space.bilibili.com/527346837).

![Screenshot](assets/screenshot.png)

## Development Progress

### 🏗️ Foundation
- ✅ World map basics
- ✅ Diverse terrain types (plain, mountain, forest, desert, water, etc.)
- ✅ Time system (year-month timestamps)
- ✅ Frontend UI (pygame)
- ✅ Simulation framework
- ✅ Project documentation (README)
- ✅ Config system
- [ ] Standalone release (packaged exe)
- [ ] Web frontend (later)
- [ ] ECS parallel toolkit (later)
- [ ] Player-configurable prompts (later)

### 🗺️ Tile System
- ✅ Basic tile mechanics
- ✅ Normal, cultivate, city, sect regions
- ✅ Same-tile NPC interactions
- ✅ Qi distribution and yields

### 👤 Character System
- ✅ Core attributes
- ✅ Cultivation realms
- ✅ Spiritual roots
- ✅ Basic movement actions
- ✅ Personality
- ✅ Breakthrough system
- ✅ Relationships
- ✅ Perception radius
- ✅ Buff system: buffs/debuffs
- ✅ Artifacts
- [ ] Special abilities
- [ ] Epithets/nicknames
- [ ] Combat-related
  - [ ] Attribute points allocation
  - [ ] Skill system (techniques)
  - [ ] Equipment system
- [ ] Skill learning
  - [ ] Learnable skills
  - [ ] Personal techniques (flexible integration)
  - [ ] Life professions (alchemy, formations, farming, forging, etc., with tailored prompts and info space)
- [ ] Mortals support
- [ ] Prodigies (stronger abilities and AI)

### 🏛️ Organizations
- [ ] Sect system
  - ✅ Settings, techniques, healing, base, styles
  - ✅ Special sect action: Hehuan Sect (dual cultivation)
  - [ ] sect will AI, tasks, recruiting
  - [ ] Sect tiers: different titles, abilities, actions
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
- [ ] Richer actions

### 🎭 Event System
- [ ] World-scale events:
  - [ ] Auctions
  - [ ] Secret realm exploration
  - [ ] Martial tournaments
- [ ] Sudden events
  - [ ] Treasure/cave emergence
  - [ ] Novelized/CG/film-style presentations
- [ ] Natural events:
  - [ ] Natural disasters
  - [ ] Beast tides

### ⚔️ Combat
- [ ] Combat design (roots influence skills and styles)
- [ ] Advantages and counters
- ✅ Win-rate estimation (simple)

### 🎒 Items
- ✅ Basic items and spirit stones
- [ ] Trading mechanics
- [ ] Economy system

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
- [ ] NPC observation space design
- [ ] One-off choices (e.g., switch techniques or not)
- [ ] Long-term memories / unforgettable memories

### 🏛️ World Lore
- [ ] Lore framework
- [ ] Worldbuilding
- [ ] Ancient history generation

### Specials
- ✅ Fortuitous encounters
- [ ] Paths/Daos
- [ ] Possession & Rebirth
- [ ] Formations
- [ ] Opportunities
- [ ] Tribulations & Heart devils
- [ ] Flexible world rules
- [ ] Divination & Omens
- [ ] Male-female traits inversion

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
     model_name: "gpt-3.5-turbo"  # or another model supported by LiteLLM
     key: "your-api-key-here"     # your API key
   ```
   See the LiteLLM docs: [`link`](https://docs.litellm.ai/docs/providers)

4. Run the simulator:
   ```bash
   python -m src.run.run
   ```

### Basic Operations
- A random map is generated at startup
- Observe characters moving and acting in the world
- Press ESC to quit

## Contributing

Contributions are welcome!

## License

This project is licensed as specified in [`LICENSE`](LICENSE).

## Contact

Open an issue or pull request if you have questions or suggestions.



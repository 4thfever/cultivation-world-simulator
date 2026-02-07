# Avatar Generation and Awakening System

## Overview

Refactored from a monolithic `new_avatar.py`, the avatar generation system is now split into two distinct modules to separate "World Initialization" from "Runtime Awakening".

## Architecture

### 1. Avatar Initialization (`src.sim.avatar_init`)
Responsible for creating avatars during **World Generation** or via **API requests**.
- **Role**: Handles mass population generation, sect assignment, and relationship mapping (parents/children/teachers) when the world is first created.
- **Key Components**:
  - `AvatarFactory`: Builds individual avatars.
  - `PopulationPlanner`: Plans the demographics of the initial world.
  - `MortalPlanner`: Plans mortal attributes.

### 2. Avatar Awakening (`src.sim.avatar_awake`)
Responsible for generating new cultivators during the **Game Simulation Loop**.
- **Role**: Handles the promotion of mortals to cultivators and the spontaneous appearance of rogue cultivators.
- **Location**: Invoked in `Simulator._phase_update_age_and_birth`.
- **Logic**:
  - **Bloodline Awakening**: Existing `Mortal` offspring (managed by `MortalManager`) have a chance to awaken spiritual roots upon reaching age 16.
  - **Wild Awakening**: Random "Wild" (Rogue) cultivators appear spontaneously based on world configuration.

### 3. Mortal Management (`src.sim.managers.mortal_manager`)
A centralized manager for non-cultivator humans in the world.
- **Purpose**: Previously, mortals were just transient objects or lost references. Now, `World.mortal_manager` tracks them.
- **Lifecycle**:
  - **Birth**: Registered upon birth from cultivator parents (`src.classes.birth`).
  - **Aging**: Checked annually for death (lifespan limit).
  - **Awakening**: Valid candidates (>= 16 years old) are queried for awakening checks.

## Awakening Mechanics

### Equipment & Stats
New awakened avatars use a simplified configuration compared to initial world generation:
- **Weapon**: One random weapon appropriate for their Realm (Qi Refinement).
- **Auxiliary**: None.
- **Technique**: Basic technique.
- **Resources**: Small amount of Spirit Stones.

### Localization
Event text for awakening uses modular PO files:
- `static/locales/<lang>/modules/avatar_awakening.po`

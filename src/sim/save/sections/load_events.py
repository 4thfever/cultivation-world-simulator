from __future__ import annotations

from .base import LoadContext


class EventsLoadSection:
    key = "events"

    def load(self, context: LoadContext) -> None:
        from src.classes.event import Event

        world = context.world
        db_event_count = world.event_manager.count()
        events_data = context.save_data.get("events", [])
        if db_event_count == 0 and len(events_data) > 0:
            print(f"Migrating {len(events_data)} events from JSON to SQLite...")
            for event_data in events_data:
                world.event_manager.add_event(Event.from_dict(event_data))
            print("Event migration completed")
        else:
            print(f"Loaded {db_event_count} events from SQLite")

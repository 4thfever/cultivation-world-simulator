from __future__ import annotations


def cooldown_action(cls: type) -> type:
    """
    冷却类装饰器：
    - 仅当类定义了 ACTION_CD_MONTHS 且 >0 时生效
    - 在 can_start 前置检查冷却；在 finish 后记录冷却开始月戳
    - 冷却记录存放于 avatar._action_cd_last_months[ClassName]
    - 同时在 DESC 中追加“（冷却：X月）”便于 UI 显示
    """

    cd = int(getattr(cls, "ACTION_CD_MONTHS", 0) or 0)
    if cd <= 0:
        return cls

    # 包装 can_start
    if hasattr(cls, "can_start"):
        original_can_start = cls.can_start

        def can_start(self, **params):  # type: ignore[no-redef]
            last_map = getattr(self.avatar, "_action_cd_last_months", {})
            last = last_map.get(self.__class__.__name__)
            if last is not None:
                elapsed = self.world.month_stamp - last
                if elapsed < cd:
                    remain = cd - elapsed
                    return False, f"冷却中，还需 {remain} 个月"
            return original_can_start(self, **params)

        cls.can_start = can_start  # type: ignore[assignment]

    # 包装 finish：调用原逻辑后记录冷却
    if hasattr(cls, "finish"):
        original_finish = cls.finish

        async def finish(self, **params):  # type: ignore[no-redef]
            # Must await original_finish first, then record cooldown.
            # This ensures cooldown is only recorded after finish() succeeds.
            events = await original_finish(self, **params)
            last_map = getattr(self.avatar, "_action_cd_last_months", None)
            if last_map is not None:
                last_map[self.__class__.__name__] = self.world.month_stamp
            return events

        cls.finish = finish  # type: ignore[assignment]
    return cls



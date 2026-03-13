import pytest
from unittest.mock import AsyncMock, Mock, patch

from src.systems.single_choice import (
    ChoiceSource,
    FallbackMode,
    FallbackPolicy,
    ItemDisposition,
    ItemExchangeKind,
    ItemExchangeRequest,
    RejectMode,
    SingleChoiceRequest,
    decide_single_choice,
    resolve_item_exchange,
)
from src.utils.config import CONFIG


class MockAvatar:
    def __init__(self):
        self.name = "TestAvatar"
        self.weapon = None
        self.auxiliary = None
        self.technique = None
        self.world = Mock()
        self.world.static_info = {}
        self.change_weapon = Mock()
        self.sell_weapon = Mock(return_value=100)
        self.consume_elixir = Mock()
        self.sell_elixir = Mock(return_value=50)

    def get_info(self, detailed=False):
        return {"name": self.name}


class MockItem:
    def __init__(self, name):
        self.name = name
        self.realm = Mock()
        self.realm.__str__ = Mock(return_value="TestRealm")

    def get_info(self, detailed=False):
        return f"Info({self.name})"


@pytest.mark.asyncio
async def test_decide_single_choice_accepts_valid_choice():
    avatar = MockAvatar()
    request = SingleChoiceRequest(
        task_name="single_choice",
        template_path=CONFIG.paths.templates / "single_choice.txt",
        avatar=avatar,
        situation="Context",
        options=[],
        fallback_policy=FallbackPolicy(FallbackMode.FIRST_OPTION),
    )
    request.options = [
        Mock(key="ACCEPT", title="Accept", description="Accept new item"),
        Mock(key="REJECT", title="Reject", description="Reject new item"),
    ]

    with patch(
        "src.systems.single_choice.engine.call_llm_with_task_name",
        new_callable=AsyncMock,
    ) as mock_llm:
        mock_llm.return_value = {"choice": "REJECT", "thinking": "keep old one"}
        decision = await decide_single_choice(request)

    assert decision.selected_key == "REJECT"
    assert decision.source == ChoiceSource.LLM
    assert decision.used_fallback is False


@pytest.mark.asyncio
async def test_decide_single_choice_falls_back_on_invalid_choice():
    avatar = MockAvatar()
    request = SingleChoiceRequest(
        task_name="single_choice",
        template_path=CONFIG.paths.templates / "single_choice.txt",
        avatar=avatar,
        situation="Context",
        options=[
            Mock(key="ACCEPT", title="Accept", description="Accept new item"),
            Mock(key="REJECT", title="Reject", description="Reject new item"),
        ],
        fallback_policy=FallbackPolicy(FallbackMode.PREFERRED_KEY, preferred_key="ACCEPT"),
    )

    with patch(
        "src.systems.single_choice.engine.call_llm_with_task_name",
        new_callable=AsyncMock,
    ) as mock_llm:
        mock_llm.return_value = {"choice": "UNKNOWN"}
        decision = await decide_single_choice(request)

    assert decision.selected_key == "ACCEPT"
    assert decision.source == ChoiceSource.FALLBACK
    assert decision.used_fallback is True


@pytest.mark.asyncio
async def test_weapon_auto_equip_without_llm():
    avatar = MockAvatar()
    new_weapon = MockItem("NewSword")

    with patch(
        "src.systems.single_choice.engine.call_llm_with_task_name",
        new_callable=AsyncMock,
    ) as mock_llm:
        outcome = await resolve_item_exchange(
            ItemExchangeRequest(
                avatar=avatar,
                new_item=new_weapon,
                kind=ItemExchangeKind.WEAPON,
                scene_intro="Context",
                reject_mode=RejectMode.ABANDON_NEW,
                auto_accept_when_empty=True,
            )
        )

    assert outcome.accepted is True
    assert outcome.action == ItemDisposition.AUTO_ACCEPTED
    assert "获得了TestRealm兵器『NewSword』并装备" in outcome.result_text
    avatar.change_weapon.assert_called_once_with(new_weapon)
    mock_llm.assert_not_called()


@pytest.mark.asyncio
async def test_weapon_swap_accept_sells_old():
    avatar = MockAvatar()
    old_weapon = MockItem("OldSword")
    new_weapon = MockItem("NewSword")
    avatar.weapon = old_weapon

    with patch(
        "src.systems.single_choice.engine.call_llm_with_task_name",
        new_callable=AsyncMock,
    ) as mock_llm:
        mock_llm.return_value = {"choice": "ACCEPT"}
        outcome = await resolve_item_exchange(
            ItemExchangeRequest(
                avatar=avatar,
                new_item=new_weapon,
                kind=ItemExchangeKind.WEAPON,
                scene_intro="Context",
                reject_mode=RejectMode.SELL_NEW,
                auto_accept_when_empty=False,
            )
        )

    assert outcome.accepted is True
    assert outcome.action == ItemDisposition.REPLACED_OLD
    assert "换上了TestRealm兵器『NewSword』" in outcome.result_text
    avatar.sell_weapon.assert_called_once_with(old_weapon)
    avatar.change_weapon.assert_called_once_with(new_weapon)
    mock_llm.assert_called_once()


@pytest.mark.asyncio
async def test_elixir_reject_sells_new():
    avatar = MockAvatar()
    new_elixir = MockItem("PowerPill")

    with patch(
        "src.systems.single_choice.engine.call_llm_with_task_name",
        new_callable=AsyncMock,
    ) as mock_llm:
        mock_llm.return_value = {"choice": "REJECT"}
        outcome = await resolve_item_exchange(
            ItemExchangeRequest(
                avatar=avatar,
                new_item=new_elixir,
                kind=ItemExchangeKind.ELIXIR,
                scene_intro="Context",
                reject_mode=RejectMode.SELL_NEW,
                auto_accept_when_empty=False,
            )
        )

    assert outcome.accepted is False
    assert outcome.action == ItemDisposition.SOLD_NEW
    assert "卖掉了新获得的PowerPill" in outcome.result_text
    avatar.sell_elixir.assert_called_once_with(new_elixir)
    avatar.consume_elixir.assert_not_called()

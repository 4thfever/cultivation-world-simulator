"""
Tests for src/classes/ai.py

This module tests the NPC AI decision-making system, including:
- LLM response parsing
- Emotion updates
- Batch avatar processing
- Edge cases

Testing Strategy:
    We do NOT call real LLM APIs in tests. Instead, we mock `call_llm_with_task_name`
    to simulate LLM responses. This approach:

    1. Avoids API call costs.
    2. Ensures deterministic test results (real LLM responses are unpredictable).
    3. Allows testing edge cases (invalid formats, empty responses, etc.).

    Example:
        with patch("src.classes.ai.call_llm_with_task_name", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "AvatarName": {
                    "action_name_params_pairs": [["cultivate", {"duration": 10}]],
                    "avatar_thinking": "...",
                    "current_emotion": "emotion_calm"
                }
            }
            results = await ai._decide(world, [avatar])

    What we're testing:
        - NOT whether the LLM answers correctly.
        - BUT whether ai.py correctly parses LLM responses and handles edge cases.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.classes.ai import AI, LLMAI, llm_ai
from src.classes.emotions import EmotionType
from src.classes.event import NULL_EVENT


class TestLLMAIDecide:
    """Tests for LLMAI._decide method."""

    @pytest.fixture
    def mock_world(self, base_world):
        """Create a world with mocked methods."""
        base_world.get_info = MagicMock(return_value="world info")
        base_world.get_observable_avatars = MagicMock(return_value=[])
        return base_world

    @pytest.fixture
    def test_avatar(self, dummy_avatar):
        """Create an avatar with mocked methods."""
        dummy_avatar.get_expanded_info = MagicMock(return_value="avatar info")
        dummy_avatar.emotion = EmotionType.CALM
        return dummy_avatar

    @pytest.mark.asyncio
    async def test_decide_with_valid_list_format(self, mock_world, test_avatar):
        """Test that LLM response with list format [name, params] is parsed correctly."""
        mock_response = {
            test_avatar.name: {
                "action_name_params_pairs": [
                    ["cultivate", {"duration": 10}],
                    ["move", {"target_x": 5, "target_y": 5}]
                ],
                "avatar_thinking": "I should cultivate to get stronger.",
                "short_term_objective": "Reach Foundation Establishment",
                "current_emotion": "emotion_calm"
            }
        }

        ai = LLMAI()
        with patch("src.classes.ai.call_llm_with_task_name", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response
            results = await ai._decide(mock_world, [test_avatar])

        assert test_avatar in results
        pairs, thinking, objective = results[test_avatar]
        
        assert len(pairs) == 2
        assert pairs[0] == ("cultivate", {"duration": 10})
        assert pairs[1] == ("move", {"target_x": 5, "target_y": 5})
        assert thinking == "I should cultivate to get stronger."
        assert objective == "Reach Foundation Establishment"

    @pytest.mark.asyncio
    async def test_decide_with_valid_dict_format(self, mock_world, test_avatar):
        """Test that LLM response with dict format {action_name, action_params} is parsed correctly."""
        mock_response = {
            test_avatar.name: {
                "action_name_params_pairs": [
                    {"action_name": "cultivate", "action_params": {"duration": 10}},
                    {"action_name": "rest", "action_params": {}}
                ],
                "avatar_thinking": "Time to rest after cultivation.",
                "short_term_objective": "Recover energy",
                "current_emotion": "emotion_tired"
            }
        }

        ai = LLMAI()
        with patch("src.classes.ai.call_llm_with_task_name", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response
            results = await ai._decide(mock_world, [test_avatar])

        assert test_avatar in results
        pairs, thinking, objective = results[test_avatar]
        
        assert len(pairs) == 2
        assert pairs[0] == ("cultivate", {"duration": 10})
        assert pairs[1] == ("rest", {})
        assert test_avatar.emotion == EmotionType.TIRED

    @pytest.mark.asyncio
    async def test_decide_with_null_params_converts_to_empty_dict(self, mock_world, test_avatar):
        """Test that null/None params are converted to empty dict."""
        mock_response = {
            test_avatar.name: {
                "action_name_params_pairs": [
                    ["cultivate", None],  # List format with null
                    {"action_name": "rest", "action_params": None}  # Dict format with null
                ],
                "avatar_thinking": "Just cultivating.",
                "short_term_objective": "Get stronger",
                "current_emotion": "emotion_calm"
            }
        }

        ai = LLMAI()
        with patch("src.classes.ai.call_llm_with_task_name", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response
            results = await ai._decide(mock_world, [test_avatar])

        assert test_avatar in results
        pairs, _, _ = results[test_avatar]
        
        # Both should have empty dict as params.
        assert pairs[0] == ("cultivate", {})
        assert pairs[1] == ("rest", {})

    @pytest.mark.asyncio
    async def test_decide_with_invalid_format_skips_pair(self, mock_world, test_avatar):
        """Test that invalid pair formats are skipped, valid ones kept."""
        mock_response = {
            test_avatar.name: {
                "action_name_params_pairs": [
                    ["cultivate", {"duration": 10}],  # Valid list format
                    "invalid_string",  # Invalid: not list/dict
                    ["only_one_element"],  # Invalid: list with 1 element
                    {"action_name": "move"},  # Invalid: missing action_params
                    {"wrong_key": "rest", "action_params": {}},  # Invalid: wrong key
                    {"action_name": "rest", "action_params": {}},  # Valid dict format
                ],
                "avatar_thinking": "Mixed formats.",
                "short_term_objective": "Test edge cases",
                "current_emotion": "emotion_calm"
            }
        }

        ai = LLMAI()
        with patch("src.classes.ai.call_llm_with_task_name", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response
            results = await ai._decide(mock_world, [test_avatar])

        assert test_avatar in results
        pairs, _, _ = results[test_avatar]
        
        # Only 2 valid pairs should be kept.
        assert len(pairs) == 2
        assert pairs[0] == ("cultivate", {"duration": 10})
        assert pairs[1] == ("rest", {})

    @pytest.mark.asyncio
    async def test_decide_with_empty_response_skips_avatar(self, mock_world, test_avatar):
        """Test that empty LLM response skips the avatar."""
        ai = LLMAI()
        with patch("src.classes.ai.call_llm_with_task_name", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {}  # Empty response
            results = await ai._decide(mock_world, [test_avatar])

        assert test_avatar not in results
        assert results == {}

    @pytest.mark.asyncio
    async def test_decide_with_none_response_skips_avatar(self, mock_world, test_avatar):
        """Test that None LLM response skips the avatar."""
        ai = LLMAI()
        with patch("src.classes.ai.call_llm_with_task_name", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = None  # None response
            results = await ai._decide(mock_world, [test_avatar])

        assert test_avatar not in results

    @pytest.mark.asyncio
    async def test_decide_with_missing_avatar_name_skips(self, mock_world, test_avatar):
        """Test that response without avatar name skips that avatar."""
        mock_response = {
            "OtherAvatar": {  # Different name than test_avatar.name
                "action_name_params_pairs": [["cultivate", {}]],
                "avatar_thinking": "Should not be used.",
                "short_term_objective": "Not for test avatar",
                "current_emotion": "emotion_calm"
            }
        }

        ai = LLMAI()
        with patch("src.classes.ai.call_llm_with_task_name", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response
            results = await ai._decide(mock_world, [test_avatar])

        assert test_avatar not in results

    @pytest.mark.asyncio
    async def test_decide_with_no_valid_pairs_skips_avatar(self, mock_world, test_avatar):
        """Test that avatar is skipped when all pairs are invalid."""
        mock_response = {
            test_avatar.name: {
                "action_name_params_pairs": [
                    "invalid",
                    123,
                    None,
                ],
                "avatar_thinking": "All invalid.",
                "short_term_objective": "Test",
                "current_emotion": "emotion_calm"
            }
        }

        ai = LLMAI()
        with patch("src.classes.ai.call_llm_with_task_name", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response
            results = await ai._decide(mock_world, [test_avatar])

        # Avatar should be skipped since no valid pairs.
        assert test_avatar not in results


class TestLLMAIEmotionUpdate:
    """Tests for emotion update logic in LLMAI._decide."""

    @pytest.fixture
    def mock_world(self, base_world):
        """Create a world with mocked methods."""
        base_world.get_info = MagicMock(return_value="world info")
        base_world.get_observable_avatars = MagicMock(return_value=[])
        return base_world

    @pytest.fixture
    def test_avatar(self, dummy_avatar):
        """Create an avatar with mocked methods."""
        dummy_avatar.get_expanded_info = MagicMock(return_value="avatar info")
        dummy_avatar.emotion = EmotionType.CALM
        return dummy_avatar

    @pytest.mark.asyncio
    async def test_decide_updates_emotion_with_valid_value(self, mock_world, test_avatar):
        """Test that valid emotion string updates avatar.emotion correctly."""
        emotions_to_test = [
            ("emotion_happy", EmotionType.HAPPY),
            ("emotion_angry", EmotionType.ANGRY),
            ("emotion_sad", EmotionType.SAD),
            ("emotion_fearful", EmotionType.FEARFUL),
            ("emotion_surprised", EmotionType.SURPRISED),
            ("emotion_anticipating", EmotionType.ANTICIPATING),
            ("emotion_disgusted", EmotionType.DISGUSTED),
            ("emotion_confused", EmotionType.CONFUSED),
            ("emotion_tired", EmotionType.TIRED),
        ]

        ai = LLMAI()
        for emotion_str, expected_emotion in emotions_to_test:
            test_avatar.emotion = EmotionType.CALM  # Reset
            
            mock_response = {
                test_avatar.name: {
                    "action_name_params_pairs": [["cultivate", {}]],
                    "avatar_thinking": "Testing emotion.",
                    "short_term_objective": "Test",
                    "current_emotion": emotion_str
                }
            }

            with patch("src.classes.ai.call_llm_with_task_name", new_callable=AsyncMock) as mock_llm:
                mock_llm.return_value = mock_response
                await ai._decide(mock_world, [test_avatar])

            assert test_avatar.emotion == expected_emotion, \
                f"Expected {expected_emotion} for '{emotion_str}', got {test_avatar.emotion}"

    @pytest.mark.asyncio
    async def test_decide_fallback_to_calm_on_invalid_emotion(self, mock_world, test_avatar):
        """Test that invalid emotion falls back to CALM."""
        test_avatar.emotion = EmotionType.HAPPY  # Set to non-CALM first
        
        mock_response = {
            test_avatar.name: {
                "action_name_params_pairs": [["cultivate", {}]],
                "avatar_thinking": "Testing emotion.",
                "short_term_objective": "Test",
                "current_emotion": "InvalidEmotion"  # Invalid value
            }
        }

        ai = LLMAI()
        with patch("src.classes.ai.call_llm_with_task_name", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response
            await ai._decide(mock_world, [test_avatar])

        assert test_avatar.emotion == EmotionType.CALM

    @pytest.mark.asyncio
    async def test_decide_fallback_to_calm_on_missing_emotion(self, mock_world, test_avatar):
        """Test that missing emotion field falls back to CALM (default '平静')."""
        test_avatar.emotion = EmotionType.HAPPY  # Set to non-CALM first
        
        mock_response = {
            test_avatar.name: {
                "action_name_params_pairs": [["cultivate", {}]],
                "avatar_thinking": "Testing emotion.",
                "short_term_objective": "Test"
                # No current_emotion field
            }
        }

        ai = LLMAI()
        with patch("src.classes.ai.call_llm_with_task_name", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response
            await ai._decide(mock_world, [test_avatar])

        # Default is "emotion_calm" which maps to CALM.
        assert test_avatar.emotion == EmotionType.CALM


class TestLLMAIBatchProcessing:
    """Tests for batch avatar processing in LLMAI._decide."""

    @pytest.fixture
    def mock_world(self, base_world):
        """Create a world with mocked methods."""
        base_world.get_info = MagicMock(return_value="world info")
        base_world.get_observable_avatars = MagicMock(return_value=[])
        return base_world

    @pytest.fixture
    def avatar_a(self, mock_world):
        """Create first test avatar."""
        from src.classes.core.avatar import Avatar, Gender
        from src.classes.age import Age
        from src.systems.cultivation import Realm
        from src.systems.time import Year, Month, create_month_stamp
        from src.classes.root import Root
        from src.classes.alignment import Alignment
        from src.utils.id_generator import get_avatar_id
        
        av = Avatar(
            world=mock_world,
            name="AvatarA",
            id=get_avatar_id(),
            birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
            age=Age(20, Realm.Qi_Refinement),
            gender=Gender.MALE,
            pos_x=0,
            pos_y=0,
            root=Root.GOLD,
            personas=[],
            alignment=Alignment.RIGHTEOUS
        )
        av.get_expanded_info = MagicMock(return_value="avatar a info")
        av.weapon = MagicMock()
        av.weapon.get_detailed_info.return_value = "Test Weapon"
        av.emotion = EmotionType.CALM
        return av

    @pytest.fixture
    def avatar_b(self, mock_world):
        """Create second test avatar."""
        from src.classes.core.avatar import Avatar, Gender
        from src.classes.age import Age
        from src.systems.cultivation import Realm
        from src.systems.time import Year, Month, create_month_stamp
        from src.classes.root import Root
        from src.classes.alignment import Alignment
        from src.utils.id_generator import get_avatar_id
        
        av = Avatar(
            world=mock_world,
            name="AvatarB",
            id=get_avatar_id(),
            birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
            age=Age(25, Realm.Foundation_Establishment),
            gender=Gender.FEMALE,
            pos_x=1,
            pos_y=1,
            root=Root.WATER,
            personas=[],
            alignment=Alignment.NEUTRAL
        )
        av.get_expanded_info = MagicMock(return_value="avatar b info")
        av.weapon = MagicMock()
        av.weapon.get_detailed_info.return_value = "Test Weapon B"
        av.emotion = EmotionType.CALM
        return av

    @pytest.mark.asyncio
    async def test_decide_multiple_avatars_concurrently(self, mock_world, avatar_a, avatar_b):
        """Test that multiple avatars are processed and each gets correct results."""
        call_count = 0
        
        async def mock_llm_side_effect(task_name, template_path, info):
            nonlocal call_count
            call_count += 1
            avatar_name = info["avatar_name"]
            
            if avatar_name == "AvatarA":
                return {
                    "AvatarA": {
                        "action_name_params_pairs": [["cultivate", {"duration": 10}]],
                        "avatar_thinking": "A is cultivating.",
                        "short_term_objective": "A's goal",
                        "current_emotion": "emotion_happy"
                    }
                }
            else:
                return {
                    "AvatarB": {
                        "action_name_params_pairs": [["move", {"target_x": 2, "target_y": 2}]],
                        "avatar_thinking": "B is moving.",
                        "short_term_objective": "B's goal",
                        "current_emotion": "emotion_angry"
                    }
                }

        ai = LLMAI()
        with patch("src.classes.ai.call_llm_with_task_name", new_callable=AsyncMock) as mock_llm:
            mock_llm.side_effect = mock_llm_side_effect
            results = await ai._decide(mock_world, [avatar_a, avatar_b])

        # Both avatars should have results.
        assert avatar_a in results
        assert avatar_b in results
        
        # LLM should be called twice (once per avatar).
        assert call_count == 2
        
        # Check avatar A's results.
        pairs_a, thinking_a, objective_a = results[avatar_a]
        assert pairs_a == [("cultivate", {"duration": 10})]
        assert thinking_a == "A is cultivating."
        assert avatar_a.emotion == EmotionType.HAPPY
        
        # Check avatar B's results.
        pairs_b, thinking_b, objective_b = results[avatar_b]
        assert pairs_b == [("move", {"target_x": 2, "target_y": 2})]
        assert thinking_b == "B is moving."
        assert avatar_b.emotion == EmotionType.ANGRY

    @pytest.mark.asyncio
    async def test_decide_with_empty_avatar_list(self, mock_world):
        """Test that empty avatar list returns empty results."""
        ai = LLMAI()
        with patch("src.classes.ai.call_llm_with_task_name", new_callable=AsyncMock) as mock_llm:
            results = await ai._decide(mock_world, [])

        assert results == {}
        mock_llm.assert_not_called()


class TestAIDecideWrapper:
    """Tests for AI.decide wrapper method."""

    @pytest.fixture
    def mock_world(self, base_world):
        """Create a world with mocked methods."""
        base_world.get_info = MagicMock(return_value="world info")
        base_world.get_observable_avatars = MagicMock(return_value=[])
        return base_world

    @pytest.fixture
    def test_avatar(self, dummy_avatar):
        """Create an avatar with mocked methods."""
        dummy_avatar.get_expanded_info = MagicMock(return_value="avatar info")
        dummy_avatar.emotion = EmotionType.CALM
        return dummy_avatar

    @pytest.mark.asyncio
    async def test_decide_returns_null_event(self, mock_world, test_avatar):
        """Test that AI.decide returns NULL_EVENT for each avatar."""
        mock_response = {
            test_avatar.name: {
                "action_name_params_pairs": [["cultivate", {}]],
                "avatar_thinking": "Testing.",
                "short_term_objective": "Test",
                "current_emotion": "emotion_calm"
            }
        }

        ai = LLMAI()
        with patch("src.classes.ai.call_llm_with_task_name", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response
            # Call decide (not _decide) to test the wrapper.
            results = await ai.decide(mock_world, [test_avatar])

        assert test_avatar in results
        pairs, thinking, objective, event = results[test_avatar]
        
        # Event should be NULL_EVENT.
        assert event is NULL_EVENT
        
        # Other fields should be preserved.
        assert pairs == [("cultivate", {})]
        assert thinking == "Testing."
        assert objective == "Test"


class TestLLMAIThinkingFieldVariants:
    """Tests for different thinking field names in LLM response."""

    @pytest.fixture
    def mock_world(self, base_world):
        """Create a world with mocked methods."""
        base_world.get_info = MagicMock(return_value="world info")
        base_world.get_observable_avatars = MagicMock(return_value=[])
        return base_world

    @pytest.fixture
    def test_avatar(self, dummy_avatar):
        """Create an avatar with mocked methods."""
        dummy_avatar.get_expanded_info = MagicMock(return_value="avatar info")
        dummy_avatar.emotion = EmotionType.CALM
        return dummy_avatar

    @pytest.mark.asyncio
    async def test_decide_with_thinking_field(self, mock_world, test_avatar):
        """Test that 'thinking' field is used as fallback for avatar_thinking."""
        mock_response = {
            test_avatar.name: {
                "action_name_params_pairs": [["cultivate", {}]],
                "thinking": "Using thinking field.",  # Not avatar_thinking
                "short_term_objective": "Test",
                "current_emotion": "emotion_calm"
            }
        }

        ai = LLMAI()
        with patch("src.classes.ai.call_llm_with_task_name", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response
            results = await ai._decide(mock_world, [test_avatar])

        assert test_avatar in results
        _, thinking, _ = results[test_avatar]
        assert thinking == "Using thinking field."

    @pytest.mark.asyncio
    async def test_decide_prefers_avatar_thinking_over_thinking(self, mock_world, test_avatar):
        """Test that 'avatar_thinking' takes precedence over 'thinking'."""
        mock_response = {
            test_avatar.name: {
                "action_name_params_pairs": [["cultivate", {}]],
                "avatar_thinking": "Preferred field.",
                "thinking": "Fallback field.",
                "short_term_objective": "Test",
                "current_emotion": "emotion_calm"
            }
        }

        ai = LLMAI()
        with patch("src.classes.ai.call_llm_with_task_name", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response
            results = await ai._decide(mock_world, [test_avatar])

        assert test_avatar in results
        _, thinking, _ = results[test_avatar]
        assert thinking == "Preferred field."

    @pytest.mark.asyncio
    async def test_decide_with_missing_optional_fields(self, mock_world, test_avatar):
        """Test that missing optional fields default to empty strings."""
        mock_response = {
            test_avatar.name: {
                "action_name_params_pairs": [["cultivate", {}]],
                # No avatar_thinking, thinking, or short_term_objective
                "current_emotion": "emotion_calm"
            }
        }

        ai = LLMAI()
        with patch("src.classes.ai.call_llm_with_task_name", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response
            results = await ai._decide(mock_world, [test_avatar])

        assert test_avatar in results
        _, thinking, objective = results[test_avatar]
        assert thinking == ""
        assert objective == ""


class TestLLMAIModuleLevelInstance:
    """Tests for the module-level llm_ai instance."""

    def test_llm_ai_is_llmai_instance(self):
        """Test that llm_ai is an instance of LLMAI."""
        assert isinstance(llm_ai, LLMAI)

    def test_llm_ai_is_ai_subclass(self):
        """Test that LLMAI is a subclass of AI."""
        assert issubclass(LLMAI, AI)

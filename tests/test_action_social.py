
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from src.classes.mutual_action.conversation import Conversation
from src.classes.action_runtime import ActionStatus
from src.classes.event import Event

class TestActionSocial:
    
    @pytest.fixture
    def target_avatar(self, dummy_avatar):
        target = MagicMock()
        target.name = "FriendDummy"
        target.id = "friend_id"
        target.get_info.return_value = "Target Info"
        target.get_planned_actions_str.return_value = "None"
        target.thinking = ""
        # 模拟 add_event
        target.events = []
        target.add_event = lambda e, to_sidebar=False: target.events.append(e)
        # 模拟修炼进度（用于关系判断）
        target.cultivation_progress.level = 10
        target.gender = dummy_avatar.gender # 同性
        target.get_relation.return_value = None
        
        return target

    @pytest.mark.asyncio
    @patch("src.classes.mutual_action.mutual_action.call_llm_with_task_name", new_callable=AsyncMock)
    async def test_conversation_flow(self, mock_llm, dummy_avatar, target_avatar):
        """测试对话流程：Step -> LLM -> Feedback"""
        
        # 1. 准备 Mock LLM 返回
        mock_response = {
            "FriendDummy": {
                "thinking": "He is nice.",
                "conversation_content": "Hello there!",
                "feedback": "Accept" # Conversation 其实不强制 feedback，主要是 content
            }
        }
        mock_llm.return_value = mock_response
        
        # 注入 World 查找
        dummy_avatar.world.avatar_manager.avatars = {target_avatar.name: target_avatar}
        
        # Mock 自己的 level (避免 dummy_avatar 中也是 Mock 导致无法比较)
        dummy_avatar.cultivation_progress.level = 10

        # 2. 初始化 Action
        action = Conversation(dummy_avatar, dummy_avatar.world)
        action._start_month_stamp = 100
        
        # 3. 第一次 Step: 应该触发 LLM 任务并返回 RUNNING
        res1 = action.step(target_avatar=target_avatar)
        assert res1.status == ActionStatus.RUNNING
        assert action._feedback_task is not None
        
        # 等待 Task 完成
        await action._feedback_task
        
        # 4. 第二次 Step: 消费结果
        res2 = action.step(target_avatar=target_avatar)
        assert res2.status == ActionStatus.COMPLETED
        
        # 5. 验证结果
        # 应该有一个包含对话内容的事件
        assert len(res2.events) >= 1
        content_event = res2.events[0]
        assert "Hello there!" in content_event.content
        assert dummy_avatar.id in content_event.related_avatars
        assert target_avatar.id in content_event.related_avatars
        
        # 验证 Target 思考被更新
        assert target_avatar.thinking == "He is nice."

    def test_conversation_no_target(self, dummy_avatar):
        action = Conversation(dummy_avatar, dummy_avatar.world)
        res = action.step(target_avatar=None)
        assert res.status == ActionStatus.FAILED


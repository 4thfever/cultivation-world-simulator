import { defineStore } from 'pinia';
import { computed, ref } from 'vue';

import { avatarApi } from '@/api';
import type { RoleplaySessionDTO } from '@/types/api';
import { logError } from '@/utils/appError';


function createInactiveSession(): RoleplaySessionDTO {
  return {
    controlled_avatar_id: null,
    status: 'inactive',
    pending_request: null,
    last_prompt_context: null,
    conversation_session: null,
    interaction_history: [],
  };
}


export const useRoleplayStore = defineStore('roleplay', () => {
  const session = ref<RoleplaySessionDTO>(createInactiveSession());
  const isLoading = ref(false);
  const isSubmitting = ref(false);
  const error = ref<string | null>(null);

  const hasActiveRoleplay = computed(() => !!session.value.controlled_avatar_id);

  async function fetchSession() {
    isLoading.value = true;
    error.value = null;
    try {
      session.value = await avatarApi.fetchRoleplaySession();
      return session.value;
    } catch (e) {
      logError('RoleplayStore fetch session', e);
      error.value = e instanceof Error ? e.message : '获取扮演状态失败';
      return session.value;
    } finally {
      isLoading.value = false;
    }
  }

  async function startRoleplay(avatarId: string) {
    isSubmitting.value = true;
    error.value = null;
    try {
      session.value = await avatarApi.startRoleplay(avatarId);
      return session.value;
    } catch (e) {
      logError('RoleplayStore start', e);
      error.value = e instanceof Error ? e.message : '开始扮演失败';
      throw e;
    } finally {
      isSubmitting.value = false;
    }
  }

  async function stopRoleplay(avatarId?: string) {
    isSubmitting.value = true;
    error.value = null;
    try {
      session.value = await avatarApi.stopRoleplay(avatarId);
      return session.value;
    } catch (e) {
      logError('RoleplayStore stop', e);
      error.value = e instanceof Error ? e.message : '退出扮演失败';
      throw e;
    } finally {
      isSubmitting.value = false;
    }
  }

  async function submitDecision(params: { avatar_id: string; request_id: string; command_text: string }) {
    isSubmitting.value = true;
    error.value = null;
    try {
      const result = await avatarApi.submitRoleplayDecision(params);
      await fetchSession();
      return result;
    } catch (e) {
      logError('RoleplayStore submit decision', e);
      error.value = e instanceof Error ? e.message : '提交扮演指令失败';
      throw e;
    } finally {
      isSubmitting.value = false;
    }
  }

  async function submitChoice(params: { avatar_id: string; request_id: string; selected_key: string }) {
    isSubmitting.value = true;
    error.value = null;
    try {
      const result = await avatarApi.submitRoleplayChoice(params);
      await fetchSession();
      return result;
    } catch (e) {
      logError('RoleplayStore submit choice', e);
      error.value = e instanceof Error ? e.message : '提交扮演选择失败';
      throw e;
    } finally {
      isSubmitting.value = false;
    }
  }

  async function sendConversation(params: { avatar_id: string; request_id: string; message: string }) {
    isSubmitting.value = true;
    error.value = null;
    try {
      const result = await avatarApi.sendRoleplayConversation(params);
      await fetchSession();
      return result;
    } catch (e) {
      logError('RoleplayStore send conversation', e);
      error.value = e instanceof Error ? e.message : '发送对话失败';
      throw e;
    } finally {
      isSubmitting.value = false;
    }
  }

  async function endConversation(params: { avatar_id: string; request_id: string }) {
    isSubmitting.value = true;
    error.value = null;
    try {
      const result = await avatarApi.endRoleplayConversation(params);
      await fetchSession();
      return result;
    } catch (e) {
      logError('RoleplayStore end conversation', e);
      error.value = e instanceof Error ? e.message : '结束对话失败';
      throw e;
    } finally {
      isSubmitting.value = false;
    }
  }

  function reset() {
    session.value = createInactiveSession();
    error.value = null;
    isLoading.value = false;
    isSubmitting.value = false;
  }

  return {
    session,
    isLoading,
    isSubmitting,
    error,
    hasActiveRoleplay,
    fetchSession,
    startRoleplay,
    stopRoleplay,
    submitDecision,
    submitChoice,
    sendConversation,
    endConversation,
    reset,
  };
});

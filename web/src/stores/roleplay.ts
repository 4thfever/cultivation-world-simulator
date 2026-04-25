import { defineStore } from 'pinia';
import { computed, ref } from 'vue';

import { avatarApi } from '@/api';
import i18n from '@/locales';
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
  const { t } = i18n.global;
  const session = ref<RoleplaySessionDTO>(createInactiveSession());
  const isLoading = ref(false);
  const isSubmitting = ref(false);
  const fetchError = ref<string | null>(null);
  const submitError = ref<string | null>(null);

  const hasActiveRoleplay = computed(() => !!session.value.controlled_avatar_id);
  const error = computed(() => submitError.value || fetchError.value);

  async function fetchSession() {
    isLoading.value = true;
    fetchError.value = null;
    try {
      session.value = await avatarApi.fetchRoleplaySession();
      return session.value;
    } catch (e) {
      logError('RoleplayStore fetch session', e);
      fetchError.value = e instanceof Error ? e.message : t('game.roleplay.errors.fetch_session');
      return session.value;
    } finally {
      isLoading.value = false;
    }
  }

  async function startRoleplay(avatarId: string) {
    isSubmitting.value = true;
    submitError.value = null;
    try {
      session.value = await avatarApi.startRoleplay(avatarId);
      return session.value;
    } catch (e) {
      logError('RoleplayStore start', e);
      submitError.value = e instanceof Error ? e.message : t('game.roleplay.errors.start');
      throw e;
    } finally {
      isSubmitting.value = false;
    }
  }

  async function stopRoleplay(avatarId?: string) {
    isSubmitting.value = true;
    submitError.value = null;
    try {
      session.value = await avatarApi.stopRoleplay(avatarId);
      return session.value;
    } catch (e) {
      logError('RoleplayStore stop', e);
      submitError.value = e instanceof Error ? e.message : t('game.roleplay.errors.stop');
      throw e;
    } finally {
      isSubmitting.value = false;
    }
  }

  async function submitDecision(params: { avatar_id: string; request_id: string; command_text: string }) {
    isSubmitting.value = true;
    submitError.value = null;
    try {
      const result = await avatarApi.submitRoleplayDecision(params);
      await fetchSession();
      return result;
    } catch (e) {
      logError('RoleplayStore submit decision', e);
      submitError.value = e instanceof Error ? e.message : t('game.roleplay.errors.submit_decision');
      throw e;
    } finally {
      isSubmitting.value = false;
    }
  }

  async function submitChoice(params: { avatar_id: string; request_id: string; selected_key: string }) {
    isSubmitting.value = true;
    submitError.value = null;
    try {
      const result = await avatarApi.submitRoleplayChoice(params);
      await fetchSession();
      return result;
    } catch (e) {
      logError('RoleplayStore submit choice', e);
      submitError.value = e instanceof Error ? e.message : t('game.roleplay.errors.submit_choice');
      throw e;
    } finally {
      isSubmitting.value = false;
    }
  }

  async function sendConversation(params: { avatar_id: string; request_id: string; message: string }) {
    isSubmitting.value = true;
    submitError.value = null;
    try {
      const result = await avatarApi.sendRoleplayConversation(params);
      await fetchSession();
      return result;
    } catch (e) {
      logError('RoleplayStore send conversation', e);
      submitError.value = e instanceof Error ? e.message : t('game.roleplay.errors.send_conversation');
      throw e;
    } finally {
      isSubmitting.value = false;
    }
  }

  async function endConversation(params: { avatar_id: string; request_id: string }) {
    isSubmitting.value = true;
    submitError.value = null;
    try {
      const result = await avatarApi.endRoleplayConversation(params);
      await fetchSession();
      return result;
    } catch (e) {
      logError('RoleplayStore end conversation', e);
      submitError.value = e instanceof Error ? e.message : t('game.roleplay.errors.end_conversation');
      throw e;
    } finally {
      isSubmitting.value = false;
    }
  }

  function reset() {
    session.value = createInactiveSession();
    fetchError.value = null;
    submitError.value = null;
    isLoading.value = false;
    isSubmitting.value = false;
  }

  return {
    session,
    isLoading,
    isSubmitting,
    error,
    fetchError,
    submitError,
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

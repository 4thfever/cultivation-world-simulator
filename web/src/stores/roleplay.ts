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
      error.value = e instanceof Error ? e.message : 'Failed to fetch roleplay session';
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
      error.value = e instanceof Error ? e.message : 'Failed to start roleplay';
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
      error.value = e instanceof Error ? e.message : 'Failed to stop roleplay';
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
      error.value = e instanceof Error ? e.message : 'Failed to submit roleplay decision';
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
      error.value = e instanceof Error ? e.message : 'Failed to submit roleplay choice';
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
    reset,
  };
});

/**
 * 智能问答状态管理 (Pinia Store)
 * 功能：管理问答会话状态，包括会话列表、当前会话、消息列表
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getConversations, createConversation, deleteConversation, getMessages, askQuestion } from '../api/qa'

export const useQAStore = defineStore('qa', () => {
  // ========== 状态 ==========
  const conversations = ref([])    // 会话列表
  const currentConv = ref(null)    // 当前选中的会话
  const messages = ref([])         // 当前会话的消息列表
  const sending = ref(false)       // 是否正在发送消息

  // ========== 方法 ==========

  /**
   * 加载会话列表
   */
  async function loadConversations() {
    const res = await getConversations()
    conversations.value = res.data
  }

  /**
   * 创建新会话
   * @param {string} title - 会话标题（默认 'New Conversation'）
   */
  async function newConversation(title) {
    const res = await createConversation({ title: title || 'New Conversation' })
    const conv = res.data
    await loadConversations()
    await selectConversation(conv)
    return conv
  }

  /**
   * 删除会话
   * @param {number} id - 会话ID
   */
  async function removeConversation(id) {
    await deleteConversation(id)
    // 如果删除的是当前会话，清空消息列表
    if (currentConv.value?.id === id) {
      currentConv.value = null
      messages.value = []
    }
    await loadConversations()
  }

  /**
   * 选择会话并加载消息
   * @param {object} conv - 会话对象
   */
  async function selectConversation(conv) {
    currentConv.value = conv
    const res = await getMessages(conv.id)
    messages.value = res.data
  }

  /**
   * 发送消息
   * @param {string} question - 用户问题
   * @param {string} modelName - 使用的模型名称
   * @returns {object} - 包含 answer, sources, kg_references 等
   */
  async function sendMessage(question, modelName) {
    sending.value = true
    try {
      const res = await askQuestion({
        conversation_id: currentConv.value?.id,
        question,
        model_name: modelName || undefined,
      })
      // 如果是新会话，更新当前会话并刷新会话列表
      if (!currentConv.value) {
        currentConv.value = { id: res.data.conversation_id }
        await loadConversations()
      }
      // 重新加载消息列表（包含新发送的消息和AI回答）
      const msgRes = await getMessages(res.data.conversation_id)
      messages.value = msgRes.data
      return res.data
    } finally {
      sending.value = false
    }
  }

  return { conversations, currentConv, messages, sending, loadConversations, newConversation, removeConversation, selectConversation, sendMessage }
})

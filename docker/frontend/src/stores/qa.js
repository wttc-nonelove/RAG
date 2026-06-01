import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getConversations, createConversation, deleteConversation, getMessages, askQuestion } from '../api/qa'

export const useQAStore = defineStore('qa', () => {
  const conversations = ref([])
  const currentConv = ref(null)
  const messages = ref([])
  const sending = ref(false)

  async function loadConversations() {
    const res = await getConversations()
    conversations.value = res.data
  }

  async function newConversation(title) {
    const res = await createConversation({ title: title || 'New Conversation' })
    const conv = res.data
    await loadConversations()
    await selectConversation(conv)
    return conv
  }

  async function removeConversation(id) {
    await deleteConversation(id)
    if (currentConv.value?.id === id) {
      currentConv.value = null
      messages.value = []
    }
    await loadConversations()
  }

  async function selectConversation(conv) {
    currentConv.value = conv
    const res = await getMessages(conv.id)
    messages.value = res.data
  }

  async function sendMessage(question, modelName) {
    sending.value = true
    try {
      const res = await askQuestion({
        conversation_id: currentConv.value?.id,
        question,
        model_name: modelName || undefined,
      })
      if (!currentConv.value) {
        currentConv.value = { id: res.data.conversation_id }
        await loadConversations()
      }
      const msgRes = await getMessages(res.data.conversation_id)
      messages.value = msgRes.data
      return res.data
    } finally {
      sending.value = false
    }
  }

  return { conversations, currentConv, messages, sending, loadConversations, newConversation, removeConversation, selectConversation, sendMessage }
})

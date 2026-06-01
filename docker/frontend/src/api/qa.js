import client from './client'

export const askQuestion = (data) => client.post('/qa/ask', data)
export const getConversations = () => client.get('/qa/conversations')
export const createConversation = (data) => client.post('/qa/conversations', data)
export const deleteConversation = (id) => client.delete(`/qa/conversations/${id}`)
export const getMessages = (convId) => client.get(`/qa/conversations/${convId}/messages`)
export const getModels = () => client.get('/qa/models')

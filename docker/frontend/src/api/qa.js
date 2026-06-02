/**
 * 智能问答 API 模块
 * 功能：封装所有与智能问答相关的 HTTP 请求
 */

import client from './client'

/** 提交问题，获取 RAG 回答 */
export const askQuestion = (data) => client.post('/qa/ask', data)

/** 获取当前用户的会话列表 */
export const getConversations = () => client.get('/qa/conversations')

/** 创建新会话 */
export const createConversation = (data) => client.post('/qa/conversations', data)

/** 删除会话 */
export const deleteConversation = (id) => client.delete(`/qa/conversations/${id}`)

/** 获取会话的消息历史 */
export const getMessages = (convId) => client.get(`/qa/conversations/${convId}/messages`)

/** 获取可用的模型列表 */
export const getModels = () => client.get('/qa/models')

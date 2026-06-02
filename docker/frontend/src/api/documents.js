/**
 * 知识库文档 API 模块
 * 功能：封装所有与文档管理相关的 HTTP 请求
 */

import client from './client'

/** 获取文档列表（分页、搜索、筛选） */
export const getDocuments = (params) => client.get('/documents', { params })

/** 获取文档统计数据（各类型、各状态数量） */
export const getDocumentStats = () => client.get('/documents/stats')

/** 上传新文档 */
export const uploadDocument = (formData) => client.post('/documents/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } })

/** 获取单个文档详情 */
export const getDocument = (id) => client.get(`/documents/${id}`)

/** 获取文档预览（分页文本内容） */
export const previewDocument = (id, params) => client.get(`/documents/${id}/preview`, { params })

/** 上传新版本覆盖旧文档 */
export const updateDocument = (id, formData) => client.post(`/documents/${id}/update`, formData, { headers: { 'Content-Type': 'multipart/form-data' } })

/** 删除文档（级联清理向量、图谱、文件） */
export const deleteDocument = (id) => client.delete(`/documents/${id}`)

/** 重新解析单个文档 */
export const reparseDocument = (id) => client.post(`/documents/${id}/reparse`)

/** 一键重新解析所有文档 */
export const reparseAllDocuments = () => client.post('/documents/reparse-all')

/** 一键删除所有文档 */
export const deleteAllDocuments = () => client.post('/documents/delete-all')

/** 批量删除文档 */
export const batchDeleteDocuments = (ids) => client.post('/documents/batch-delete', { ids })

/** 批量重新解析文档 */
export const batchReparseDocuments = (ids) => client.post('/documents/batch-reparse', { ids })

/** 清理知识图谱中的孤立实体 */
export const cleanupOrphanEntities = () => client.post('/documents/cleanup-orphans')

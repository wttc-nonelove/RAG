/**
 * 知识图谱 API 模块
 * 功能：封装所有与知识图谱管理相关的 HTTP 请求
 */

import client from './client'

/** 获取知识图谱全貌（所有节点和关系） */
export const getGraphOverview = () => client.get('/graph/overview')

/** 获取实体列表（分页） */
export const getEntities = (params) => client.get('/graph/entities', { params })

/** 创建新实体 */
export const createEntity = (data) => client.post('/graph/entities', data)

/** 更新实体信息 */
export const updateEntity = (id, data) => client.put(`/graph/entities/${id}`, data)

/** 删除实体及其所有关系 */
export const deleteEntity = (id) => client.delete(`/graph/entities/${id}`)

/** 获取实体的关联实体（邻居节点） */
export const getEntityNeighbors = (id) => client.get(`/graph/entities/${id}/neighbors`)

/** 搜索实体和关系 */
export const searchGraph = (q) => client.get('/graph/search', { params: { q } })

/** 按实体类型筛选 */
export const filterByType = (entityType) => client.get('/graph/filter', { params: { entity_type: entityType } })

/** 获取所有关系列表 */
export const getRelations = (limit) => client.get('/graph/relations', { params: { limit } })

/** 创建新关系 */
export const createRelation = (data) => client.post('/graph/relations', data)

/** 删除指定关系 */
export const deleteRelation = (source, relation, target) => client.delete('/graph/relations', { params: { source, relation, target } })

/** 手动触发文档的知识图谱抽取 */
export const extractDocument = (docId) => client.post(`/graph/extract/${docId}`)

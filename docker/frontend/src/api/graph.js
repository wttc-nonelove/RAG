import client from './client'

export const getGraphOverview = () => client.get('/graph/overview')
export const getEntities = (params) => client.get('/graph/entities', { params })
export const createEntity = (data) => client.post('/graph/entities', data)
export const updateEntity = (id, data) => client.put(`/graph/entities/${id}`, data)
export const deleteEntity = (id) => client.delete(`/graph/entities/${id}`)
export const getEntityNeighbors = (id) => client.get(`/graph/entities/${id}/neighbors`)
export const searchGraph = (q) => client.get('/graph/search', { params: { q } })
export const filterByType = (entityType) => client.get('/graph/filter', { params: { entity_type: entityType } })
export const getRelations = (limit) => client.get('/graph/relations', { params: { limit } })
export const createRelation = (data) => client.post('/graph/relations', data)
export const deleteRelation = (source, relation, target) => client.delete('/graph/relations', { params: { source, relation, target } })
export const extractDocument = (docId) => client.post(`/graph/extract/${docId}`)

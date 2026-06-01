import client from './client'

export const getGraphOverview = () => client.get('/graph/overview')
export const getEntities = (params) => client.get('/graph/entities', { params })
export const createEntity = (data) => client.post('/graph/entities', data)
export const deleteEntity = (id) => client.delete(`/graph/entities/${id}`)
export const searchGraph = (q) => client.get('/graph/search', { params: { q } })

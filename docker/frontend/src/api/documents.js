import client from './client'

export const getDocuments = (params) => client.get('/documents', { params })
export const getDocumentStats = () => client.get('/documents/stats')
export const uploadDocument = (formData) => client.post('/documents/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
export const getDocument = (id) => client.get(`/documents/${id}`)
export const previewDocument = (id, params) => client.get(`/documents/${id}/preview`, { params })
export const updateDocument = (id, formData) => client.post(`/documents/${id}/update`, formData, { headers: { 'Content-Type': 'multipart/form-data' } })
export const deleteDocument = (id) => client.delete(`/documents/${id}`)
export const reparseDocument = (id) => client.post(`/documents/${id}/reparse`)
export const reparseAllDocuments = () => client.post('/documents/reparse-all')

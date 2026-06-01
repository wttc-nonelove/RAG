import client from './client'

export const getAdminHistory = (params) => client.get('/history/admin', { params })
export const getMyHistory = (params) => client.get('/history/my', { params })
export const getMessage = (id) => client.get(`/history/${id}`)
export const getHistoryStats = () => client.get('/history/stats')

import client from './client'

export const getStats = () => client.get('/dashboard/stats')
export const getTrends = (params) => client.get('/dashboard/trends', { params })
export const getStorage = () => client.get('/dashboard/storage')
export const getSystemStatus = () => client.get('/dashboard/system-status')

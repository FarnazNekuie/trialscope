import axios from 'axios'
const client = axios.create({ baseURL: '/api', timeout: 15000 })
export const searchTrials = p => client.get('/trials', { params: p }).then(r => r.data)
export const getTrial = id => client.get(`/trials/${id}`).then(r => r.data)
export const getStatsByPhase = () => client.get('/stats/by-phase').then(r => r.data)
export const getStatsByStatus = () => client.get('/stats/by-status').then(r => r.data)
export const getStatsBySponsors = () => client.get('/stats/by-sponsor').then(r => r.data)
export const getTrends = () => client.get('/stats/trends').then(r => r.data)

import request from './request'

export function getJobList() {
  return request.get('/api/jobs/')
}

export function createJob(data) {
  return request.post('/api/jobs/', data)
}

export function updateJob(id, data) {
  return request.put(`/api/jobs/${id}`, data)
}

export function deleteJob(id) {
  return request.delete(`/api/jobs/${id}`)
}
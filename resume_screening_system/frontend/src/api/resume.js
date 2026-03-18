import request from './request'

export function uploadResume(formData) {
  return request.post('/api/resumes/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
}

export function getResumeList() {
  return request.get('/api/resumes/')
}

export function parseResume(id) {
  return request.post(`/api/resumes/${id}/parse`)
}

export function extractResume(id) {
  return request.get(`/api/resumes/${id}/extract`)
}

export function deleteResume(id) {
  return request.delete(`/api/resumes/${id}`)
}
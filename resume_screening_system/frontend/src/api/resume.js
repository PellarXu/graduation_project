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

export function getResumeDetail(id) {
  return request.get(`/api/resumes/${id}`)
}

export function parseResume(id) {
  return request.post(`/api/resumes/${id}/parse`)
}

export function analyzeResume(id) {
  return request.post(`/api/resumes/${id}/analyze`)
}

export function deleteResume(id) {
  return request.delete(`/api/resumes/${id}`)
}

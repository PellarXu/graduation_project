import request from './request'

export function getMatchResult(jobId, resumeIds = []) {
  return request.get(`/api/match/${jobId}`, {
    params: {
      resume_ids: resumeIds,
    },
    paramsSerializer: {
      indexes: null,
    },
  })
}
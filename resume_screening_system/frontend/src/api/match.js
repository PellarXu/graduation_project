import request from './request'

export function getMatchResult(jobId, resumeIds = []) {
  return request.post(`/api/match/jobs/${jobId}`, {
    resume_ids: resumeIds,
  })
}

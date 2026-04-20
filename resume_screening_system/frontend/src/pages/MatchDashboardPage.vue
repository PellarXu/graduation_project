<template>
  <div class="page-grid">
    <el-card class="panel-card">
      <template #header>
        <div>
          <div class="panel-title">匹配驾驶舱</div>
          <div class="panel-subtitle">从岗位权重、候选人排名、匹配解释和公平说明四个层次展示筛选结果。</div>
        </div>
      </template>

      <div class="filter-grid">
        <el-select v-model="selectedJobId" placeholder="请选择岗位" class="filter-control">
          <el-option
            v-for="job in jobList"
            :key="job.id"
            :label="`${job.job_name} / ${job.job_type}`"
            :value="job.id"
          />
        </el-select>

        <el-select
          v-model="selectedResumeIds"
          multiple
          collapse-tags
          collapse-tags-tooltip
          placeholder="请选择参与匹配的简历"
          class="filter-control"
        >
          <el-option
            v-for="resume in resumeList"
            :key="resume.id"
            :label="`${resume.file_name}（${resume.extract_status || '待分析'}）`"
            :value="resume.id"
          />
        </el-select>

        <el-button type="primary" class="match-button" @click="runMatch">开始匹配</el-button>
      </div>
    </el-card>

    <div class="metric-grid" v-if="matchResult">
      <div class="metric-card">
        <div class="metric-label">已选简历</div>
        <div class="metric-value">{{ matchResult.selected_resume_count }}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">可评分简历</div>
        <div class="metric-value">{{ matchResult.available_resume_count }}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">技能权重</div>
        <div class="metric-value">{{ formatWeight(matchResult.weights.skill_weight) }}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">经验权重</div>
        <div class="metric-value">{{ formatWeight(matchResult.weights.experience_weight) }}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">学历权重</div>
        <div class="metric-value">{{ formatWeight(matchResult.weights.degree_weight) }}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">专业权重</div>
        <div class="metric-value">{{ formatWeight(matchResult.weights.major_weight) }}</div>
      </div>
    </div>

    <el-row :gutter="20" v-if="matchResult">
      <el-col :span="12">
        <el-card class="panel-card">
          <template #header>
            <div>
              <div class="panel-title">候选人总分排名</div>
              <div class="panel-subtitle">基于岗位权重和结构化画像展示候选人综合评分。</div>
            </div>
          </template>
          <BaseChart :option="scoreBarOption" />
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card class="panel-card">
          <template #header>
            <div class="chart-header">
              <div>
                <div class="panel-title">候选人维度雷达图</div>
                <div class="panel-subtitle">默认展示当前高分候选人，也可切换查看四个维度的原始得分。</div>
              </div>
              <el-select
                v-if="candidateOptions.length"
                v-model="selectedCandidateId"
                placeholder="选择候选人"
                style="width: 220px"
              >
                <el-option
                  v-for="candidate in candidateOptions"
                  :key="candidate.resume_id"
                  :label="`${candidate.file_name} / ${candidate.total_score ?? '--'}分`"
                  :value="candidate.resume_id"
                />
              </el-select>
            </div>
          </template>
          <BaseChart :option="radarOption" />
        </el-card>
      </el-col>
    </el-row>

    <el-card class="panel-card" v-if="matchResult">
      <template #header>
        <div>
          <div class="panel-title">候选人匹配明细</div>
          <div class="panel-subtitle">点击表格可查看候选人的评分依据、命中证据、公平说明与脱敏画像。</div>
        </div>
      </template>

      <el-table
        :data="matchResult.results"
        border
        highlight-current-row
        style="width: 100%"
        :row-class-name="getRowClassName"
        @row-click="handleSelectCandidate"
      >
        <el-table-column prop="file_name" label="简历名称" min-width="220" />
        <el-table-column prop="analysis_status" label="分析状态" width="140" />
        <el-table-column prop="total_score" label="总分" width="120" />
        <el-table-column label="命中技能" min-width="220">
          <template #default="{ row }">
            {{ row.matched_skills?.length ? row.matched_skills.join('、') : '暂无' }}
          </template>
        </el-table-column>
        <el-table-column label="缺失技能" min-width="220">
          <template #default="{ row }">
            {{ row.missing_skills?.length ? row.missing_skills.join('、') : '暂无' }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card v-if="selectedCandidate" class="panel-card">
      <template #header>
        <div>
          <div class="panel-title">匹配解释</div>
          <div class="panel-subtitle">{{ selectedCandidate.file_name }}</div>
        </div>
      </template>

      <div class="summary-list">
        <div v-for="item in scoreSummary" :key="item" class="summary-item">{{ item }}</div>
      </div>

      <el-timeline class="explanation-timeline">
        <el-timeline-item v-for="item in selectedCandidate.final_explanations" :key="item" type="primary" hollow>
          {{ item }}
        </el-timeline-item>
      </el-timeline>

      <div class="dimension-grid">
        <div v-for="item in dimensionCards" :key="item.key" class="dimension-card">
          <div class="dimension-head">
            <div>
              <div class="dimension-title">{{ item.label }}</div>
              <div class="dimension-score">
                原始分 {{ item.rawScore }} / 加权分 {{ item.weightedScore }}
              </div>
            </div>
          </div>
          <div class="dimension-evidence-list">
            <div v-for="evidence in item.evidence" :key="evidence" class="dimension-evidence-item">{{ evidence }}</div>
          </div>
        </div>
      </div>
    </el-card>

    <el-card v-if="selectedCandidate" class="panel-card">
      <template #header>
        <div>
          <div class="panel-title">公平说明</div>
          <div class="panel-subtitle">明确哪些字段参与评分、哪些字段仅展示、哪些字段在评分前已脱敏。</div>
        </div>
      </template>

      <div class="fairness-list">
        <div v-for="note in selectedCandidate.fairness_notes || []" :key="note" class="fairness-item">{{ note }}</div>
      </div>
    </el-card>

    <el-card v-if="selectedCandidate" class="panel-card">
      <template #header>
        <div>
          <div class="panel-title">脱敏画像</div>
          <div class="panel-subtitle">主视图只保留适合人工复核的字段，避免将内部调试结构直接暴露到页面。</div>
        </div>
      </template>

      <ProfileFieldsBoard :profile="selectedCandidate.profile_masked || {}" />
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import BaseChart from '../components/BaseChart.vue'
import ProfileFieldsBoard from '../components/ProfileFieldsBoard.vue'
import { getJobList } from '../api/job'
import { getMatchResult } from '../api/match'
import { getResumeList } from '../api/resume'

const jobList = ref([])
const resumeList = ref([])
const selectedJobId = ref(null)
const selectedResumeIds = ref([])
const matchResult = ref(null)
const selectedCandidateId = ref(null)

const loadBaseData = async () => {
  ;[jobList.value, resumeList.value] = await Promise.all([getJobList(), getResumeList()])
}

const runMatch = async () => {
  if (!selectedJobId.value) {
    ElMessage.warning('请先选择一个岗位。')
    return
  }
  if (!selectedResumeIds.value.length) {
    ElMessage.warning('请至少选择一份简历。')
    return
  }

  try {
    matchResult.value = await getMatchResult(selectedJobId.value, selectedResumeIds.value)
    selectedCandidateId.value = matchResult.value.results?.[0]?.resume_id || null
    ElMessage.success('匹配完成。')
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '匹配失败。')
  }
}

const handleSelectCandidate = (row) => {
  selectedCandidateId.value = row.resume_id
}

const formatWeight = (value) => Number(value || 0).toFixed(2)

const candidateOptions = computed(() => matchResult.value?.results || [])

const selectedCandidate = computed(() => {
  const candidates = candidateOptions.value
  if (!candidates.length) {
    return null
  }
  return candidates.find((candidate) => candidate.resume_id === selectedCandidateId.value) || candidates[0]
})

const dimensionLabelMap = {
  skills: '技能',
  experience: '经验',
  degree: '学历',
  major: '专业',
}

const dimensionCards = computed(() => {
  const scores = selectedCandidate.value?.dimension_scores || {}
  return Object.entries(dimensionLabelMap).map(([key, label]) => ({
    key,
    label,
    rawScore: scores[key]?.raw_score ?? 0,
    weightedScore: scores[key]?.weighted_score ?? 0,
    evidence: scores[key]?.evidence || ['暂无评分证据。'],
  }))
})

const scoreSummary = computed(() => {
  if (!selectedCandidate.value || !matchResult.value) {
    return []
  }
  const total = selectedCandidate.value.total_score ?? '--'
  const weights = matchResult.value.weights || {}
  const strongest = [...dimensionCards.value].sort((a, b) => b.rawScore - a.rawScore)[0]
  const weakest = [...dimensionCards.value].sort((a, b) => a.rawScore - b.rawScore)[0]

  return [
    `当前总分为 ${total}，由技能、经验、学历、专业四个维度按岗位权重加权得到。`,
    `当前岗位权重为：技能 ${formatWeight(weights.skill_weight)}，经验 ${formatWeight(weights.experience_weight)}，学历 ${formatWeight(weights.degree_weight)}，专业 ${formatWeight(weights.major_weight)}。`,
    `当前最强项是 ${strongest?.label || '暂无'}，主要短板是 ${weakest?.label || '暂无'}。`,
    `命中技能：${selectedCandidate.value.matched_skills?.length ? selectedCandidate.value.matched_skills.join('、') : '暂无'}；缺失技能：${selectedCandidate.value.missing_skills?.length ? selectedCandidate.value.missing_skills.join('、') : '暂无'}。`,
  ]
})

const getRowClassName = ({ row }) => (row.resume_id === selectedCandidateId.value ? 'selected-candidate-row' : '')

const scoreBarOption = computed(() => {
  const results = matchResult.value?.results || []
  return {
    xAxis: {
      type: 'category',
      data: results.map((item) => item.file_name),
    },
    series: [
      {
        type: 'bar',
        data: results.map((item) => Number(item.total_score || 0)),
      },
    ],
  }
})

const radarOption = computed(() => {
  const candidate = selectedCandidate.value
  const scores = candidate?.dimension_scores || {}
  return {
    radar: {
      indicator: [
        { name: '技能', max: 100 },
        { name: '经验', max: 100 },
        { name: '学历', max: 100 },
        { name: '专业', max: 100 },
      ],
    },
    series: [
      {
        type: 'radar',
        data: [
          {
            value: [
              scores.skills?.raw_score || 0,
              scores.experience?.raw_score || 0,
              scores.degree?.raw_score || 0,
              scores.major?.raw_score || 0,
            ],
          },
        ],
      },
    ],
  }
})

onMounted(loadBaseData)
</script>

<style scoped>
.filter-grid {
  display: grid;
  grid-template-columns: minmax(240px, 1fr) minmax(280px, 1fr) 180px;
  gap: 20px;
  align-items: center;
}

.filter-control {
  width: 100%;
}

.match-button {
  width: 100%;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
}

.summary-list,
.fairness-list {
  display: grid;
  gap: 10px;
}

.summary-item,
.fairness-item {
  padding: 12px 14px;
  border-radius: 14px;
  background: #f8fbff;
  color: #30465e;
  line-height: 1.7;
}

.explanation-timeline {
  margin-top: 22px;
}

.dimension-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
  margin-top: 20px;
}

.dimension-card {
  padding: 18px;
  border-radius: 18px;
  background: linear-gradient(180deg, #ffffff 0%, #f6f8fb 100%);
  box-shadow: inset 0 0 0 1px rgba(24, 48, 75, 0.08);
}

.dimension-title {
  font-size: 15px;
  font-weight: 700;
  color: #18304b;
}

.dimension-score {
  margin-top: 6px;
  color: #6a7c8f;
}

.dimension-evidence-list {
  display: grid;
  gap: 10px;
  margin-top: 14px;
}

.dimension-evidence-item {
  padding: 10px 12px;
  border-radius: 14px;
  background: #fff;
  color: #30465e;
  line-height: 1.7;
  box-shadow: inset 0 0 0 1px rgba(24, 48, 75, 0.06);
}

:deep(.selected-candidate-row) {
  --el-table-tr-bg-color: #f9f1d9;
}
</style>

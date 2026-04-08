<template>
  <div class="page-grid">
    <el-card class="panel-card">
      <template #header>
        <div>
          <div class="panel-title">匹配驾驶舱</div>
          <div class="panel-subtitle">从岗位权重、候选人排名、匹配解释和公平说明四个层次展示筛选结果。</div>
        </div>
      </template>

      <el-row :gutter="20">
        <el-col :span="10">
          <el-select v-model="selectedJobId" placeholder="请选择岗位" style="width: 100%">
            <el-option
              v-for="job in jobList"
              :key="job.id"
              :label="`${job.job_name} / ${job.job_type}`"
              :value="job.id"
            />
          </el-select>
        </el-col>
        <el-col :span="10">
          <el-select
            v-model="selectedResumeIds"
            multiple
            collapse-tags
            collapse-tags-tooltip
            placeholder="请选择参与匹配的简历"
            style="width: 100%"
          >
            <el-option
              v-for="resume in resumeList"
              :key="resume.id"
              :label="`${resume.file_name}（${resume.extract_status || '待分析'}）`"
              :value="resume.id"
            />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-button type="primary" style="width: 100%" @click="runMatch">开始匹配</el-button>
        </el-col>
      </el-row>
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
                <div class="panel-subtitle">默认展示当前最高分候选人，也可手动切换查看四个维度的原始得分。</div>
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
          <div class="panel-subtitle">点击表格可查看候选人的解释文本、公平说明与脱敏画像。</div>
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

    <el-row :gutter="20" v-if="selectedCandidate">
      <el-col :span="12">
        <el-card class="panel-card">
          <template #header>
            <div>
              <div class="panel-title">匹配解释</div>
              <div class="panel-subtitle">{{ selectedCandidate.file_name }}</div>
            </div>
          </template>
          <el-timeline>
            <el-timeline-item
              v-for="item in selectedCandidate.final_explanations"
              :key="item"
              type="primary"
              hollow
            >
              {{ item }}
            </el-timeline-item>
          </el-timeline>
          <div class="section-title">公平说明</div>
          <el-tag
            v-for="note in selectedCandidate.fairness_notes"
            :key="note"
            class="tag-item"
            type="warning"
          >
            {{ note }}
          </el-tag>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card class="panel-card">
          <template #header>
            <div>
              <div class="panel-title">脱敏画像</div>
              <div class="panel-subtitle">用于人工复核时的展示数据</div>
            </div>
          </template>
          <pre class="json-panel">{{ JSON.stringify(selectedCandidate.profile_masked || {}, null, 2) }}</pre>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import BaseChart from '../components/BaseChart.vue'
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
    ElMessage.warning('请先选择一个岗位')
    return
  }
  if (!selectedResumeIds.value.length) {
    ElMessage.warning('请至少选择一份简历')
    return
  }

  try {
    matchResult.value = await getMatchResult(selectedJobId.value, selectedResumeIds.value)
    selectedCandidateId.value = matchResult.value.results?.[0]?.resume_id || null
    ElMessage.success('匹配完成')
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '匹配失败')
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
  return (
    candidates.find((candidate) => candidate.resume_id === selectedCandidateId.value) ||
    candidates[0] ||
    null
  )
})

const getRowClassName = ({ row }) => {
  return row.resume_id === selectedCandidateId.value ? 'selected-candidate-row' : ''
}

const scoreBarOption = computed(() => {
  const results = matchResult.value?.results || []
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 20, top: 40, bottom: 40 },
    xAxis: {
      type: 'category',
      data: results.map((item) => item.file_name),
      axisLabel: { interval: 0, rotate: 18 },
    },
    yAxis: { type: 'value', max: 100 },
    series: [
      {
        type: 'bar',
        data: results.map((item) => item.total_score || 0),
        itemStyle: {
          color: '#d49d2a',
          borderRadius: [10, 10, 0, 0],
        },
      },
    ],
  }
})

const radarOption = computed(() => {
  const candidate = selectedCandidate.value
  const scores = candidate?.dimension_scores || {}
  return {
    tooltip: {},
    radar: {
      radius: '64%',
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
            areaStyle: { color: 'rgba(212, 157, 42, 0.28)' },
            lineStyle: { color: '#18304b' },
          },
        ],
      },
    ],
  }
})

onMounted(loadBaseData)
</script>

<style scoped>
.tag-item {
  margin-right: 8px;
  margin-bottom: 8px;
}

.section-title {
  margin-top: 14px;
  margin-bottom: 12px;
  font-size: 15px;
  font-weight: 700;
  color: #18304b;
}

.json-panel {
  margin: 0;
  padding: 14px;
  min-height: 300px;
  border-radius: 18px;
  white-space: pre-wrap;
  word-break: break-word;
  background: #0f2134;
  color: #f8f2da;
  font-size: 13px;
  line-height: 1.7;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
}

:deep(.selected-candidate-row) {
  --el-table-tr-bg-color: #f9f1d9;
}
</style>

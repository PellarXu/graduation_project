<template>
  <div class="page-grid">
    <el-card class="panel-card model-card">
      <template #header>
        <div>
          <div class="panel-title">模型状态</div>
          <div class="panel-subtitle">展示当前接入模型的版本、指标与标签表现，并补充这些指标的含义。</div>
        </div>
      </template>

      <el-alert
        :title="modelStatus.ready ? '模型已就绪' : '模型未就绪'"
        :type="modelStatus.ready ? 'success' : 'warning'"
        :closable="false"
        :description="modelStatus.message || '尚未检测到训练后的推理资源。'"
      />

      <div class="metric-explain-grid">
        <div v-for="item in metricExplainList" :key="item.title" class="metric-explain-card">
          <div class="metric-explain-title">{{ item.title }}</div>
          <div class="metric-explain-text">{{ item.text }}</div>
        </div>
      </div>

      <el-descriptions :column="2" border class="metric-descriptions">
        <el-descriptions-item label="模型版本">{{ modelStatus.model_version || '-' }}</el-descriptions-item>
        <el-descriptions-item label="最近训练时间">{{ modelStatus.trained_at || '-' }}</el-descriptions-item>
        <el-descriptions-item label="整体 F1">{{ formatMetric(modelStatus.overall_f1) }}</el-descriptions-item>
        <el-descriptions-item label="宏平均 F1">{{ formatMetric(modelStatus.macro_f1) }}</el-descriptions-item>
        <el-descriptions-item label="论文达标">{{ modelStatus.paper_ready ? '是' : '否' }}</el-descriptions-item>
        <el-descriptions-item label="数据规模">
          train {{ modelStatus.dataset_size?.train || 0 }} / dev {{ modelStatus.dataset_size?.dev || 0 }} / test
          {{ modelStatus.dataset_size?.test || 0 }}
        </el-descriptions-item>
      </el-descriptions>

      <div class="analysis-section" v-if="Object.keys(modelStatus.per_label_metrics || {}).length">
        <div class="section-title">关键标签 F1</div>
        <el-tag
          v-for="label in keyMetricLabels"
          :key="label"
          class="tag-item"
          :type="metricTagType(modelStatus.per_label_metrics?.[label]?.f1)"
        >
          {{ label }}：{{ formatMetric(modelStatus.per_label_metrics?.[label]?.f1) }}
        </el-tag>
      </div>
    </el-card>

    <el-card class="panel-card">
      <template #header>
        <div>
          <div class="panel-title">简历上传与分析</div>
          <div class="panel-subtitle">支持简历上传、文本解析、结构化提取与脱敏画像展示。</div>
        </div>
      </template>

      <el-upload class="upload-area" drag :show-file-list="false" :http-request="handleUpload">
        <div class="upload-title">拖拽文件到这里，或点击上传简历</div>
        <div class="soft-tip">支持 pdf / docx / txt</div>
      </el-upload>

      <el-table
        :data="resumeList"
        border
        highlight-current-row
        style="width: 100%; margin-top: 20px"
        :row-class-name="getRowClassName"
      >
        <el-table-column prop="file_name" label="文件名称" min-width="240" />
        <el-table-column prop="file_type" label="文件类型" width="120" />
        <el-table-column prop="parse_status" label="解析状态" width="120" />
        <el-table-column prop="extract_status" label="分析状态" width="140" />
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleSelect(row.id)">查看</el-button>
            <el-button link type="success" @click="handleParse(row.id)">解析</el-button>
            <el-button link type="warning" @click="handleAnalyze(row.id)">分析</el-button>
            <el-button link type="danger" @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card v-if="detail" class="panel-card">
      <template #header>
        <div>
          <div class="panel-title">分析概览</div>
          <div class="panel-subtitle">{{ detail.file_name }}</div>
        </div>
      </template>

      <div class="overview-grid">
        <div class="overview-block">
          <div class="section-title">状态信息</div>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="解析状态">{{ detail.parse_status || '-' }}</el-descriptions-item>
            <el-descriptions-item label="分析状态">{{ detail.extract_status || '-' }}</el-descriptions-item>
            <el-descriptions-item label="模型版本">{{ detail.model_version || '待生成' }}</el-descriptions-item>
            <el-descriptions-item label="结果说明">{{ detail.message || '分析结果已更新。' }}</el-descriptions-item>
          </el-descriptions>
        </div>

        <div class="overview-block">
          <div class="section-title">敏感字段摘要</div>
          <div class="profile-tag-list">
            <el-tag
              v-for="field in detail.sensitive_summary?.masked_fields || []"
              :key="field"
              type="warning"
              class="tag-item"
            >
              {{ field }}
            </el-tag>
          </div>
          <div class="soft-tip overview-note">
            {{ detail.sensitive_summary?.note || '尚未生成敏感字段摘要。' }}
          </div>
        </div>
      </div>

      <div class="analysis-section">
        <div class="section-title">识别摘要</div>
        <div v-if="analysisSummary.length" class="summary-list">
          <div v-for="item in analysisSummary" :key="item" class="summary-item">{{ item }}</div>
        </div>
        <el-empty v-else description="暂无识别摘要" />
      </div>

      <el-collapse class="entity-collapse">
        <el-collapse-item title="识别到的实体与调试信息" name="entity-debug">
          <div class="profile-tag-list">
            <el-tag
              v-for="entity in detail.entity_result"
              :key="`${entity.label}-${entity.start}-${entity.end}-${entity.text}`"
              class="tag-item"
            >
              {{ entity.label }} / {{ entity.text }}
            </el-tag>
          </div>
          <el-empty v-if="!detail.entity_result?.length" description="暂无实体结果" />
        </el-collapse-item>
      </el-collapse>
    </el-card>

    <el-card class="panel-card" v-if="detail">
      <template #header>
        <div>
          <div class="panel-title">结构化画像</div>
          <div class="panel-subtitle">主视图改为字段卡片，避免右侧长 JSON 挤压页面。</div>
        </div>
      </template>

      <el-tabs v-model="profileTab">
        <el-tab-pane label="原始画像" name="raw">
          <ProfileFieldsBoard :profile="detail.profile_raw || {}" :show-raw-sections="true" />
        </el-tab-pane>
        <el-tab-pane label="脱敏复核画像" name="masked">
          <ProfileFieldsBoard :profile="detail.profile_masked || {}" />
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-card class="panel-card" v-if="detail">
      <template #header>
        <div>
          <div class="panel-title">文本预览</div>
          <div class="panel-subtitle">当前展示的是原始文本与清洗文本，便于核对解析效果。</div>
        </div>
      </template>

      <div class="text-preview-grid">
        <div>
          <div class="section-title">原始文本</div>
          <el-input :model-value="detail.raw_text || ''" type="textarea" :rows="12" readonly />
        </div>
        <div>
          <div class="section-title">清洗文本</div>
          <el-input :model-value="detail.clean_text || ''" type="textarea" :rows="12" readonly />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import ProfileFieldsBoard from '../components/ProfileFieldsBoard.vue'
import {
  analyzeResume,
  deleteResume,
  getModelStatus,
  getResumeDetail,
  getResumeList,
  parseResume,
  uploadResume,
} from '../api/resume'

const resumeList = ref([])
const detail = ref(null)
const selectedResumeId = ref(null)
const profileTab = ref('raw')
const modelStatus = ref({
  status: 'artifacts_missing',
  ready: false,
  message: '尚未检测到训练后的推理资源。',
  model_version: null,
  overall_f1: null,
  macro_f1: null,
  per_label_metrics: {},
  dataset_size: {},
  dataset_source_breakdown: {},
  paper_ready: false,
  trained_at: null,
})

const metricExplainList = [
  { title: '整体 F1', text: '把所有标签放在一起计算的综合识别效果，越接近 1 说明整体抽取越稳定。' },
  { title: '宏平均 F1', text: '先分别计算每个标签的 F1 再求平均，更能看出模型是否在某些标签上偏科。' },
  { title: '数据规模', text: 'train / dev / test 分别代表训练集、验证集、测试集的样本数。' },
]
const keyMetricLabels = ['NAME', 'PHONE', 'EMAIL', 'DEGREE', 'MAJOR', 'SCHOOL', 'SKILL', 'EXPERIENCE_YEARS']

const analysisSummary = computed(() => detail.value?.profile_raw?.analysis_summary || [])

const formatMetric = (value) => (typeof value === 'number' ? value.toFixed(4) : '-')

const metricTagType = (value) => {
  if (typeof value !== 'number') return 'info'
  if (value >= 0.8) return 'success'
  if (value >= 0.7) return 'warning'
  return 'danger'
}

const preserveScroll = async (task) => {
  const top = window.scrollY
  const left = window.scrollX
  const result = await task()
  await nextTick()
  window.scrollTo({ top, left, behavior: 'auto' })
  return result
}

const loadResumeList = async () => {
  resumeList.value = await getResumeList()
}

const loadModelStatus = async () => {
  modelStatus.value = await getModelStatus()
}

const refreshDetail = async (id) => {
  detail.value = await getResumeDetail(id)
  selectedResumeId.value = id
  return detail.value
}

const handleSelect = async (id) => {
  await preserveScroll(async () => {
    await refreshDetail(id)
  })
}

const handleUpload = async (option) => {
  const formData = new FormData()
  formData.append('file', option.file)
  try {
    await uploadResume(formData)
    ElMessage.success('简历上传成功。')
    await loadResumeList()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '简历上传失败。')
  }
}

const ensureParsedBeforeAnalyze = async (id) => {
  const currentDetail = detail.value?.id === id ? detail.value : await getResumeDetail(id)
  if (currentDetail.parse_status === '已完成' && currentDetail.clean_text) {
    return currentDetail
  }
  const parsed = await parseResume(id)
  if (parsed.parse_status !== '已完成') {
    throw new Error('简历解析失败，请先检查文件内容。')
  }
  return getResumeDetail(id)
}

const handleParse = async (id) => {
  try {
    await preserveScroll(async () => {
      const payload = await parseResume(id)
      await loadResumeList()
      if (payload.parse_status !== '已完成') {
        throw new Error('简历解析失败，请检查文件格式或内容。')
      }
      await refreshDetail(id)
    })
    ElMessage.success('简历解析完成。')
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '简历解析失败。')
  }
}

const handleAnalyze = async (id) => {
  try {
    const analysis = await preserveScroll(async () => {
      await ensureParsedBeforeAnalyze(id)
      const result = await analyzeResume(id)
      detail.value = result
      selectedResumeId.value = id
      await Promise.all([loadResumeList(), loadModelStatus()])
      return result
    })
    if (analysis.extract_status === '分析失败') {
      ElMessage.warning(analysis.message || '分析失败。')
    } else {
      ElMessage.success(analysis.message || '简历分析完成。')
    }
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '简历分析失败。')
  }
}

const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('删除后无法恢复，确定继续吗？', '删除简历', { type: 'warning' })
    await deleteResume(id)
    ElMessage.success('简历删除成功。')
    if (detail.value?.id === id) {
      detail.value = null
      selectedResumeId.value = null
    }
    await loadResumeList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error?.response?.data?.detail || '简历删除失败。')
    }
  }
}

const getRowClassName = ({ row }) => (row.id === selectedResumeId.value ? 'selected-resume-row' : '')

onMounted(async () => {
  await Promise.all([loadResumeList(), loadModelStatus()])
})
</script>

<style scoped>
.model-card {
  margin-bottom: 20px;
}

.upload-area {
  width: 100%;
}

.upload-title {
  font-size: 18px;
  font-weight: 700;
  color: #18304b;
}

.metric-explain-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
  margin-top: 16px;
}

.metric-explain-card {
  padding: 16px;
  border-radius: 18px;
  background: linear-gradient(180deg, #ffffff 0%, #f6f8fb 100%);
  box-shadow: inset 0 0 0 1px rgba(24, 48, 75, 0.08);
}

.metric-explain-title {
  font-size: 15px;
  font-weight: 700;
  color: #18304b;
}

.metric-explain-text {
  margin-top: 8px;
  color: #5a6d80;
  line-height: 1.7;
}

.metric-descriptions {
  margin-top: 16px;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 18px;
}

.overview-block {
  padding: 18px;
  border-radius: 18px;
  background: linear-gradient(180deg, #ffffff 0%, #f6f8fb 100%);
  box-shadow: inset 0 0 0 1px rgba(24, 48, 75, 0.08);
}

.overview-note {
  margin-top: 12px;
  line-height: 1.7;
}

.analysis-section + .analysis-section {
  margin-top: 24px;
}

.section-title {
  font-size: 15px;
  font-weight: 700;
  color: #18304b;
  margin-bottom: 12px;
}

.tag-item {
  margin-right: 8px;
  margin-bottom: 8px;
}

.profile-tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.summary-list {
  display: grid;
  gap: 10px;
}

.summary-item {
  padding: 12px 14px;
  border-radius: 14px;
  background: #f8fbff;
  color: #30465e;
  line-height: 1.7;
}

.entity-collapse {
  margin-top: 20px;
}

.text-preview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}

:deep(.selected-resume-row) {
  --el-table-tr-bg-color: #f9f1d9;
}
</style>

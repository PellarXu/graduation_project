<template>
  <div class="page-grid">
    <el-card class="panel-card">
      <template #header>
        <div>
          <div class="panel-title">岗位管理</div>
          <div class="panel-subtitle">每个岗位都必须单独配置技能、经验、学历、专业四项权重，且总和为 1。</div>
        </div>
      </template>

      <div class="toolbar">
        <el-button type="primary" @click="openCreateDialog">新增岗位</el-button>
        <el-button @click="loadJobList">刷新列表</el-button>
      </div>

      <el-table :data="jobList" border style="width: 100%">
        <el-table-column prop="job_name" label="岗位名称" min-width="170" />
        <el-table-column prop="job_type" label="岗位类型" width="130" />
        <el-table-column prop="degree_requirement" label="学历要求" width="120" />
        <el-table-column prop="major_requirement" label="专业要求" min-width="150" />
        <el-table-column prop="experience_requirement" label="经验要求" width="130" />
        <el-table-column prop="city" label="工作城市" width="120" />
        <el-table-column label="权重配置" min-width="260">
          <template #default="{ row }">
            <div class="weight-line">技能 {{ formatWeight(row.skill_weight) }}</div>
            <div class="weight-line">经验 {{ formatWeight(row.experience_weight) }}</div>
            <div class="weight-line">学历 {{ formatWeight(row.degree_weight) }}</div>
            <div class="weight-line">专业 {{ formatWeight(row.major_weight) }}</div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="190" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEditDialog(row)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="780px">
      <el-form label-width="110px" :model="form">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="岗位名称">
              <el-input v-model="form.job_name" placeholder="例如：新媒体运营专员" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="岗位类型">
              <el-input v-model="form.job_type" placeholder="例如：运营岗" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="学历要求">
              <el-input v-model="form.degree_requirement" placeholder="例如：本科" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="专业要求">
              <el-input v-model="form.major_requirement" placeholder="例如：广告学" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="经验要求">
              <el-input v-model="form.experience_requirement" placeholder="例如：2 年" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="工作城市">
              <el-input v-model="form.city" placeholder="例如：武汉" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="技能要求">
          <el-input
            v-model="form.skill_requirement"
            type="textarea"
            :rows="3"
            placeholder="例如：剪映, Photoshop, 公众号运营, 数据复盘"
          />
        </el-form-item>

        <el-form-item label="岗位描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="4"
            placeholder="填写岗位职责和招聘说明"
          />
        </el-form-item>

        <div class="weight-header">
          <div class="panel-title" style="font-size: 18px">岗位权重</div>
          <div class="soft-tip">四项权重之和必须等于 1。可先套用模板，再手动微调。</div>
        </div>

        <div class="template-actions">
          <el-button @click="applyWeightPreset('tech')">技术岗模板</el-button>
          <el-button @click="applyWeightPreset('operation')">运营岗模板</el-button>
          <el-button @click="applyWeightPreset('general')">通用模板</el-button>
        </div>

        <el-row :gutter="16">
          <el-col :span="6">
            <el-form-item label="技能权重" label-width="90px">
              <el-input-number v-model="form.skill_weight" :min="0" :max="1" :step="0.05" :precision="2" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="经验权重" label-width="90px">
              <el-input-number v-model="form.experience_weight" :min="0" :max="1" :step="0.05" :precision="2" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="学历权重" label-width="90px">
              <el-input-number v-model="form.degree_weight" :min="0" :max="1" :step="0.05" :precision="2" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="专业权重" label-width="90px">
              <el-input-number v-model="form.major_weight" :min="0" :max="1" :step="0.05" :precision="2" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-alert
          :title="`当前权重总和：${weightTotal}`"
          :type="isWeightTotalValid ? 'success' : 'warning'"
          :closable="false"
        />
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">保存岗位</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { createJob, deleteJob, getJobList, updateJob } from '../api/job'

const jobList = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const currentJobId = ref(null)

const defaultForm = () => ({
  job_name: '',
  job_type: '',
  degree_requirement: '',
  major_requirement: '',
  skill_requirement: '',
  experience_requirement: '',
  city: '',
  description: '',
  skill_weight: 0.35,
  experience_weight: 0.35,
  degree_weight: 0.15,
  major_weight: 0.15,
})

const form = ref(defaultForm())

const dialogTitle = computed(() => (isEdit.value ? '编辑岗位' : '新增岗位'))
const weightTotal = computed(() =>
  Number(
    (
      Number(form.value.skill_weight || 0) +
      Number(form.value.experience_weight || 0) +
      Number(form.value.degree_weight || 0) +
      Number(form.value.major_weight || 0)
    ).toFixed(2)
  )
)
const isWeightTotalValid = computed(() => Math.abs(weightTotal.value - 1) < 0.001)

const formatWeight = (value) => Number(value || 0).toFixed(2)

const loadJobList = async () => {
  jobList.value = await getJobList()
}

const resetForm = () => {
  form.value = defaultForm()
  currentJobId.value = null
}

const applyWeightPreset = (preset) => {
  const presets = {
    tech: { skill_weight: 0.45, experience_weight: 0.25, degree_weight: 0.15, major_weight: 0.15 },
    operation: { skill_weight: 0.35, experience_weight: 0.35, degree_weight: 0.15, major_weight: 0.15 },
    general: { skill_weight: 0.30, experience_weight: 0.30, degree_weight: 0.20, major_weight: 0.20 },
  }
  Object.assign(form.value, presets[preset])
}

const openCreateDialog = () => {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

const openEditDialog = (row) => {
  isEdit.value = true
  currentJobId.value = row.id
  form.value = {
    job_name: row.job_name,
    job_type: row.job_type,
    degree_requirement: row.degree_requirement || '',
    major_requirement: row.major_requirement || '',
    skill_requirement: row.skill_requirement || '',
    experience_requirement: row.experience_requirement || '',
    city: row.city || '',
    description: row.description || '',
    skill_weight: Number(row.skill_weight),
    experience_weight: Number(row.experience_weight),
    degree_weight: Number(row.degree_weight),
    major_weight: Number(row.major_weight),
  }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!isWeightTotalValid.value) {
    ElMessage.warning('四项权重之和必须等于 1')
    return
  }

  try {
    if (isEdit.value) {
      await updateJob(currentJobId.value, form.value)
      ElMessage.success('岗位更新成功')
    } else {
      await createJob(form.value)
      ElMessage.success('岗位创建成功')
    }
    dialogVisible.value = false
    await loadJobList()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '岗位保存失败')
  }
}

const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('删除后无法恢复，确定继续吗？', '删除岗位', {
      type: 'warning',
    })
    await deleteJob(id)
    ElMessage.success('岗位删除成功')
    await loadJobList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('岗位删除失败')
    }
  }
}

onMounted(loadJobList)
</script>

<style scoped>
.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 18px;
}

.weight-line {
  font-size: 13px;
  color: #43566b;
  line-height: 1.7;
}

.weight-header {
  margin-bottom: 12px;
}

.template-actions {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}
</style>

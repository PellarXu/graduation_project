<template>
  <div class="page-grid">
    <el-card class="panel-card">
      <template #header>
        <div>
          <div class="panel-title">简历上传与分析</div>
          <div class="panel-subtitle">当前阶段已接入最终版分析接口。若模型权重尚未训练，页面会明确提示“模型未就绪”。</div>
        </div>
      </template>

      <el-upload class="upload-area" drag :show-file-list="false" :http-request="handleUpload">
        <div class="upload-title">拖拽文件到这里，或点击上传简历</div>
        <div class="soft-tip">支持 pdf / docx / txt</div>
      </el-upload>

      <el-table :data="resumeList" border style="width: 100%; margin-top: 20px">
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

    <el-row :gutter="20" v-if="detail">
      <el-col :span="12">
        <el-card class="panel-card">
          <template #header>
            <div>
              <div class="panel-title">分析概览</div>
              <div class="panel-subtitle">{{ detail.file_name }}</div>
            </div>
          </template>

          <el-descriptions :column="1" border>
            <el-descriptions-item label="解析状态">{{ detail.parse_status || '-' }}</el-descriptions-item>
            <el-descriptions-item label="分析状态">{{ detail.extract_status || '-' }}</el-descriptions-item>
            <el-descriptions-item label="模型版本">{{ detail.model_version || '未加载' }}</el-descriptions-item>
            <el-descriptions-item label="结果来源">{{ detail.source_type }}</el-descriptions-item>
            <el-descriptions-item label="接口说明">{{ detail.message || '已就绪' }}</el-descriptions-item>
          </el-descriptions>

          <div class="analysis-section">
            <div class="section-title">敏感字段摘要</div>
            <el-tag
              v-for="field in detail.sensitive_summary?.masked_fields || []"
              :key="field"
              class="tag-item"
              type="warning"
            >
              {{ field }}
            </el-tag>
            <div class="soft-tip" style="margin-top: 10px">
              {{ detail.sensitive_summary?.note || '尚未生成敏感字段摘要。' }}
            </div>
          </div>

          <div class="analysis-section">
            <div class="section-title">识别到的实体</div>
            <el-empty v-if="!detail.entity_result?.length" description="暂无实体结果" />
            <el-tag
              v-for="entity in detail.entity_result"
              :key="`${entity.label}-${entity.start}-${entity.end}-${entity.text}`"
              class="tag-item"
            >
              {{ entity.label }} · {{ entity.text }}
            </el-tag>
          </div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card class="panel-card">
          <template #header>
            <div>
              <div class="panel-title">结构化画像</div>
              <div class="panel-subtitle">原始画像与脱敏画像对照展示</div>
            </div>
          </template>
          <div class="analysis-section">
            <div class="section-title">原始画像</div>
            <pre class="json-panel">{{ formatJson(detail.profile_raw) }}</pre>
          </div>
          <div class="analysis-section">
            <div class="section-title">脱敏画像</div>
            <pre class="json-panel">{{ formatJson(detail.profile_masked) }}</pre>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="panel-card" v-if="detail">
      <template #header>
        <div>
          <div class="panel-title">文本预览</div>
          <div class="panel-subtitle">当前展示的是解析后的原始文本和清洗文本</div>
        </div>
      </template>

      <el-row :gutter="20">
        <el-col :span="12">
          <div class="section-title">原始文本</div>
          <el-input :model-value="detail.raw_text || ''" type="textarea" :rows="12" readonly />
        </el-col>
        <el-col :span="12">
          <div class="section-title">清洗文本</div>
          <el-input :model-value="detail.clean_text || ''" type="textarea" :rows="12" readonly />
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { analyzeResume, deleteResume, getResumeDetail, getResumeList, parseResume, uploadResume } from '../api/resume'

const resumeList = ref([])
const detail = ref(null)

const loadResumeList = async () => {
  resumeList.value = await getResumeList()
}

const handleSelect = async (id) => {
  detail.value = await getResumeDetail(id)
}

const handleUpload = async (option) => {
  const formData = new FormData()
  formData.append('file', option.file)
  try {
    await uploadResume(formData)
    ElMessage.success('简历上传成功')
    await loadResumeList()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '简历上传失败')
  }
}

const handleParse = async (id) => {
  try {
    await parseResume(id)
    ElMessage.success('简历解析完成')
    await loadResumeList()
    if (detail.value?.id === id) {
      await handleSelect(id)
    }
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '简历解析失败')
  }
}

const handleAnalyze = async (id) => {
  try {
    detail.value = await analyzeResume(id)
    ElMessage.success(detail.value.message || '简历分析已执行')
    await loadResumeList()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '简历分析失败')
  }
}

const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('删除后无法恢复，确定继续吗？', '删除简历', { type: 'warning' })
    await deleteResume(id)
    ElMessage.success('简历删除成功')
    if (detail.value?.id === id) {
      detail.value = null
    }
    await loadResumeList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('简历删除失败')
    }
  }
}

const formatJson = (value) => JSON.stringify(value || {}, null, 2)

onMounted(loadResumeList)
</script>

<style scoped>
.upload-area {
  width: 100%;
}

.upload-title {
  font-size: 18px;
  font-weight: 700;
  color: #18304b;
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

.json-panel {
  margin: 0;
  padding: 14px;
  min-height: 220px;
  border-radius: 18px;
  white-space: pre-wrap;
  word-break: break-word;
  background: #0f2134;
  color: #f8f2da;
  font-size: 13px;
  line-height: 1.7;
}
</style>

<template>
  <div class="page-container">
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card class="card-block">
          <template #header>
            <div class="header-row">
              <span class="title">岗位管理</span>
              <div>
                <el-button type="success" @click="handleMatch" style="margin-right: 10px">
                  计算匹配结果
                </el-button>
                <el-button type="primary" @click="openCreateDialog">新增岗位</el-button>
              </div>
            </div>
          </template>

          <el-table :data="jobList" border style="width: 100%" @row-click="handleSelectJob">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="job_name" label="岗位名称" min-width="180" />
            <el-table-column prop="job_type" label="岗位类型" width="120" />
            <el-table-column prop="degree_requirement" label="学历要求" width="120" />
            <el-table-column prop="major_requirement" label="专业要求" min-width="160" />
            <el-table-column prop="skill_requirement" label="技能要求" min-width="220" />
            <el-table-column prop="experience_requirement" label="经验要求" width="120" />
            <el-table-column prop="city" label="城市" width="120" />
            <el-table-column prop="description" label="岗位描述" min-width="260" show-overflow-tooltip />
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="scope">
                <el-button type="primary" size="small" @click.stop="openEditDialog(scope.row)">
                  修改
                </el-button>
                <el-button type="danger" size="small" @click.stop="handleDelete(scope.row.id)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="tip-text" v-if="selectedJob">
            当前选中岗位：{{ selectedJob.job_name }}（ID: {{ selectedJob.id }}）
          </div>
        </el-card>
      </el-col>

      <el-col :span="24">
        <el-card class="card-block">
          <template #header>
            <div class="header-row">
              <span class="title">简历上传与解析</span>
            </div>
          </template>

          <el-upload
            class="upload-block"
            drag
            :show-file-list="false"
            :http-request="handleUpload"
          >
            <div class="upload-text">
              将简历文件拖到此处，或点击上传
            </div>
            <div class="upload-tip">
              支持 pdf / docx / txt
            </div>
          </el-upload>

          <div class="tip-text" style="margin-bottom: 10px;">
            请勾选要参与当前匹配计算的简历
          </div>

          <el-table
            :data="resumeList"
            border
            style="width: 100%; margin-top: 20px"
            @selection-change="handleResumeSelectionChange"
          >
            <el-table-column type="selection" width="55" />
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="file_name" label="文件名" min-width="220" />
            <el-table-column prop="file_type" label="文件类型" width="120" />
            <el-table-column prop="parse_status" label="状态" width="120" />
            <el-table-column prop="file_path" label="保存路径" min-width="260" />
            <el-table-column label="操作" width="260">
              <template #default="scope">
                <el-button type="success" size="small" @click="handleParse(scope.row.id)">
                  解析
                </el-button>
                <el-button type="primary" size="small" @click="handleExtract(scope.row.id)">
                  抽取
                </el-button>
                <el-button type="danger" size="small" @click="handleDeleteResume(scope.row.id)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="24" v-if="extractResult">
        <el-card class="card-block">
          <template #header>
            <div class="header-row">
              <span class="title">抽取结果展示</span>
            </div>
          </template>

          <el-descriptions border :column="2">
            <el-descriptions-item label="简历ID">
              {{ extractResult.id }}
            </el-descriptions-item>
            <el-descriptions-item label="文件名">
              {{ extractResult.file_name }}
            </el-descriptions-item>
            <el-descriptions-item label="手机号">
              {{ extractResult.phone || '未识别' }}
            </el-descriptions-item>
            <el-descriptions-item label="邮箱">
              {{ extractResult.email || '未识别' }}
            </el-descriptions-item>
            <el-descriptions-item label="学历">
              {{ extractResult.degree || '未识别' }}
            </el-descriptions-item>
            <el-descriptions-item label="专业">
              {{ extractResult.major || '未识别' }}
            </el-descriptions-item>
            <el-descriptions-item label="技能" :span="2">
              {{ extractResult.skills?.length ? extractResult.skills.join(', ') : '未识别' }}
            </el-descriptions-item>
          </el-descriptions>

          <div class="text-block">
            <div class="sub-title">原始文本</div>
            <el-input
              :model-value="extractResult.raw_text || ''"
              type="textarea"
              :rows="8"
              readonly
            />
          </div>

          <div class="text-block">
            <div class="sub-title">清洗后文本</div>
            <el-input
              :model-value="extractResult.clean_text || ''"
              type="textarea"
              :rows="8"
              readonly
            />
          </div>
        </el-card>
      </el-col>

      <el-col :span="24" v-if="matchResult">
        <el-card class="card-block">
          <template #header>
            <div class="header-row">
              <span class="title">匹配结果展示</span>
            </div>
          </template>

          <div class="tip-text">
            当前岗位：{{ matchResult.job_name }} / {{ matchResult.job_type }}
          </div>
          <div class="tip-text">
            当前权重：技能 {{ matchResult.skill_weight }} ，学历 {{ matchResult.degree_weight }} ，专业 {{ matchResult.major_weight }}
          </div>
          <div class="tip-text">
            本次参与匹配的简历数量：{{ matchResult.selected_resume_count }}
          </div>

          <el-table :data="matchResult.results" border style="width: 100%">
            <el-table-column prop="resume_id" label="简历ID" width="100" />
            <el-table-column prop="file_name" label="文件名" min-width="220" />
            <el-table-column prop="phone" label="手机号" min-width="140" />
            <el-table-column prop="email" label="邮箱" min-width="180" />
            <el-table-column prop="degree" label="学历" width="100" />
            <el-table-column prop="major" label="专业" min-width="160" />
            <el-table-column label="技能" min-width="220">
              <template #default="scope">
                {{ scope.row.skills?.length ? scope.row.skills.join(', ') : '无' }}
              </template>
            </el-table-column>
            <el-table-column prop="raw_skill_score" label="原始技能分" width="120" />
            <el-table-column prop="raw_degree_score" label="原始学历分" width="120" />
            <el-table-column prop="raw_major_score" label="原始专业分" width="120" />
            <el-table-column prop="skill_score" label="加权技能分" width="120" />
            <el-table-column prop="degree_score" label="加权学历分" width="120" />
            <el-table-column prop="major_score" label="加权专业分" width="120" />
            <el-table-column prop="total_score" label="总分" width="120" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '修改岗位' : '新增岗位'" width="700px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="岗位名称">
          <el-input v-model="form.job_name" placeholder="请输入岗位名称" />
        </el-form-item>

        <el-form-item label="岗位类型">
          <el-input v-model="form.job_type" placeholder="例如：技术岗" />
        </el-form-item>

        <el-form-item label="学历要求">
          <el-input v-model="form.degree_requirement" placeholder="例如：本科" />
        </el-form-item>

        <el-form-item label="专业要求">
          <el-input v-model="form.major_requirement" placeholder="例如：计算机类" />
        </el-form-item>

        <el-form-item label="技能要求">
          <el-input
            v-model="form.skill_requirement"
            type="textarea"
            :rows="3"
            placeholder="例如：Python, FastAPI, MySQL"
          />
        </el-form-item>

        <el-form-item label="经验要求">
          <el-input v-model="form.experience_requirement" placeholder="例如：1年" />
        </el-form-item>

        <el-form-item label="城市">
          <el-input v-model="form.city" placeholder="例如：武汉" />
        </el-form-item>

        <el-form-item label="岗位描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="4"
            placeholder="请输入岗位描述"
          />
        </el-form-item>

        <el-form-item label="权重模板ID">
          <el-input-number v-model="form.weight_template_id" :min="1" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">
          {{ isEdit ? '保存修改' : '确定新增' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getJobList, createJob, updateJob, deleteJob } from './api/job'
import { uploadResume, getResumeList, parseResume, extractResume, deleteResume } from './api/resume'
import { getMatchResult } from './api/match'

const jobList = ref([])
const resumeList = ref([])
const extractResult = ref(null)
const matchResult = ref(null)
const selectedJob = ref(null)
const selectedResumes = ref([])

const dialogVisible = ref(false)
const isEdit = ref(false)
const currentJobId = ref(null)

const form = ref({
  job_name: '',
  job_type: '',
  degree_requirement: '',
  major_requirement: '',
  skill_requirement: '',
  experience_requirement: '',
  city: '',
  description: '',
  weight_template_id: 1,
})

const resetForm = () => {
  form.value = {
    job_name: '',
    job_type: '',
    degree_requirement: '',
    major_requirement: '',
    skill_requirement: '',
    experience_requirement: '',
    city: '',
    description: '',
    weight_template_id: 1,
  }
  currentJobId.value = null
}

const loadJobList = async () => {
  try {
    jobList.value = await getJobList()
  } catch (error) {
    ElMessage.error('获取岗位列表失败')
    console.error(error)
  }
}

const loadResumeList = async () => {
  try {
    resumeList.value = await getResumeList()
  } catch (error) {
    ElMessage.error('获取简历列表失败')
    console.error(error)
  }
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
    job_name: row.job_name || '',
    job_type: row.job_type || '',
    degree_requirement: row.degree_requirement || '',
    major_requirement: row.major_requirement || '',
    skill_requirement: row.skill_requirement || '',
    experience_requirement: row.experience_requirement || '',
    city: row.city || '',
    description: row.description || '',
    weight_template_id: row.weight_template_id || 1,
  }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  try {
    if (isEdit.value) {
      await updateJob(currentJobId.value, form.value)
      ElMessage.success('修改岗位成功')
    } else {
      await createJob(form.value)
      ElMessage.success('新增岗位成功')
    }
    dialogVisible.value = false
    loadJobList()
  } catch (error) {
    ElMessage.error(isEdit.value ? '修改岗位失败' : '新增岗位失败')
    console.error(error)
  }
}

const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这个岗位吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteJob(id)
    ElMessage.success('删除成功')
    loadJobList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
      console.error(error)
    }
  }
}

const handleUpload = async (option) => {
  try {
    const formData = new FormData()
    formData.append('file', option.file)
    await uploadResume(formData)
    ElMessage.success('简历上传成功')
    loadResumeList()
  } catch (error) {
    ElMessage.error('简历上传失败')
    console.error(error)
  }
}

const handleParse = async (id) => {
  try {
    await parseResume(id)
    ElMessage.success('简历解析成功')
    loadResumeList()
  } catch (error) {
    ElMessage.error('简历解析失败')
    console.error(error)
  }
}

const handleExtract = async (id) => {
  try {
    extractResult.value = await extractResume(id)
    ElMessage.success('简历抽取成功')
  } catch (error) {
    ElMessage.error('简历抽取失败')
    console.error(error)
  }
}

const handleDeleteResume = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这份简历吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteResume(id)
    ElMessage.success('简历删除成功')
    loadResumeList()
    if (extractResult.value && extractResult.value.id === id) {
      extractResult.value = null
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('简历删除失败')
      console.error(error)
    }
  }
}

const handleSelectJob = (row) => {
  selectedJob.value = row
}

const handleResumeSelectionChange = (rows) => {
  selectedResumes.value = rows
}

const handleMatch = async () => {
  try {
    if (!selectedJob.value) {
      ElMessage.warning('请先点击选择一个岗位')
      return
    }

    if (!selectedResumes.value.length) {
      ElMessage.warning('请先勾选要参与匹配的简历')
      return
    }

    const resumeIds = selectedResumes.value.map(item => item.id)
    matchResult.value = await getMatchResult(selectedJob.value.id, resumeIds)
    ElMessage.success('匹配计算成功')
  } catch (error) {
    ElMessage.error('匹配计算失败')
    console.error(error)
  }
}

onMounted(() => {
  loadJobList()
  loadResumeList()
})
</script>

<style scoped>
.page-container {
  padding: 24px;
}

.card-block {
  margin-bottom: 20px;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 20px;
  font-weight: bold;
}

.upload-block {
  width: 100%;
}

.upload-text {
  font-size: 18px;
  margin-bottom: 8px;
}

.upload-tip {
  color: #909399;
  font-size: 14px;
}

.text-block {
  margin-top: 20px;
}

.sub-title {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 10px;
}

.tip-text {
  margin-top: 15px;
  color: #606266;
  font-size: 14px;
}
</style>
<template>
  <div class="profile-board">
    <el-empty v-if="!hasContent" description="暂无结构化画像" />

    <template v-else>
      <div class="profile-section-grid">
        <section v-for="section in sections" :key="section.title" class="profile-section-card">
          <div class="profile-section-title">{{ section.title }}</div>
          <div v-for="item in section.items" :key="item.label" class="profile-field-row">
            <div class="profile-field-label">{{ item.label }}</div>
            <div class="profile-field-value">{{ item.value }}</div>
          </div>
        </section>
      </div>

      <section v-if="skills.length" class="profile-section-card">
        <div class="profile-section-title">技能标签</div>
        <div class="profile-tag-list">
          <el-tag v-for="skill in skills" :key="skill" class="profile-tag" effect="plain">{{ skill }}</el-tag>
        </div>
      </section>

      <section v-if="analysisSummary.length" class="profile-section-card">
        <div class="profile-section-title">识别摘要</div>
        <div class="profile-summary-list">
          <div v-for="item in analysisSummary" :key="item" class="profile-summary-item">{{ item }}</div>
        </div>
      </section>

      <section v-if="scoringScope" class="profile-section-card">
        <div class="profile-section-title">评分边界</div>
        <div class="scope-group">
          <div class="scope-label">参与评分</div>
          <div class="profile-tag-list">
            <el-tag v-for="item in scoringScope.included || []" :key="`included-${item}`" type="success" class="profile-tag">
              {{ item }}
            </el-tag>
          </div>
        </div>
        <div class="scope-group" v-if="(scoringScope.display_only || []).length">
          <div class="scope-label">仅展示不计分</div>
          <div class="profile-tag-list">
            <el-tag v-for="item in scoringScope.display_only || []" :key="`display-${item}`" type="warning" class="profile-tag">
              {{ item }}
            </el-tag>
          </div>
        </div>
        <div class="scope-group" v-if="(scoringScope.masked || []).length">
          <div class="scope-label">已脱敏字段</div>
          <div class="profile-tag-list">
            <el-tag v-for="item in scoringScope.masked || []" :key="`masked-${item}`" type="info" class="profile-tag">
              {{ item }}
            </el-tag>
          </div>
        </div>
      </section>

      <el-collapse v-if="showRawSections && hasRawSections" class="profile-raw-collapse">
        <el-collapse-item title="原始结构数据" name="raw-structure">
          <pre class="json-panel">{{ JSON.stringify(profile.raw_sections || {}, null, 2) }}</pre>
        </el-collapse-item>
      </el-collapse>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  profile: {
    type: Object,
    default: () => ({}),
  },
  showRawSections: {
    type: Boolean,
    default: false,
  },
})

const pickValue = (...values) => values.find((value) => value !== null && value !== undefined && value !== '' && (!Array.isArray(value) || value.length))

const joinList = (value) => {
  if (Array.isArray(value)) {
    return value.length ? value.join('、') : ''
  }
  return value || ''
}

const basicInfo = computed(() => props.profile.basic_info || {})
const education = computed(() => props.profile.education || {})
const experience = computed(() => props.profile.experience || {})

const sections = computed(() => {
  const rawProfile = props.profile || {}
  const data = [
    {
      title: '基本信息',
      items: [
        { label: '姓名', value: pickValue(basicInfo.value.name, rawProfile.name) },
        { label: '性别', value: pickValue(basicInfo.value.gender, rawProfile.gender) },
        { label: '年龄', value: pickValue(basicInfo.value.age, rawProfile.age) },
        { label: '籍贯', value: pickValue(basicInfo.value.hometown, rawProfile.hometown) },
        { label: '电话', value: joinList(rawProfile.phones) },
        { label: '邮箱', value: joinList(rawProfile.emails) },
      ].filter((item) => item.value),
    },
    {
      title: '教育背景',
      items: [
        { label: '学历', value: joinList(pickValue(education.value.degrees, rawProfile.degrees)) },
        { label: '专业', value: joinList(pickValue(education.value.majors, rawProfile.majors)) },
        { label: '院校', value: joinList(pickValue(education.value.schools, rawProfile.schools)) },
      ].filter((item) => item.value),
    },
    {
      title: '岗位与经历',
      items: [
        { label: '工作年限', value: pickValue(experience.value.experience_years, rawProfile.experience_years) },
        { label: '岗位方向', value: joinList(pickValue(experience.value.titles, rawProfile.titles)) },
        { label: '相关组织', value: joinList(pickValue(experience.value.companies, rawProfile.companies)) },
        { label: '项目经历', value: joinList(pickValue(experience.value.projects, rawProfile.projects)) },
      ].filter((item) => item.value),
    },
  ]
  return data.filter((section) => section.items.length)
})

const skills = computed(() => props.profile.skills || [])
const analysisSummary = computed(() => props.profile.analysis_summary || [])
const scoringScope = computed(() => props.profile.scoring_scope || null)
const hasRawSections = computed(() => Object.keys(props.profile.raw_sections || {}).length > 0)
const hasContent = computed(
  () => sections.value.length || skills.value.length || analysisSummary.value.length || hasRawSections.value
)
</script>

<style scoped>
.profile-board {
  display: grid;
  gap: 16px;
}

.profile-section-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
}

.profile-section-card {
  padding: 18px;
  border-radius: 18px;
  background: linear-gradient(180deg, #ffffff 0%, #f6f8fb 100%);
  box-shadow: inset 0 0 0 1px rgba(24, 48, 75, 0.08);
}

.profile-section-title {
  margin-bottom: 12px;
  font-size: 15px;
  font-weight: 700;
  color: #18304b;
}

.profile-field-row + .profile-field-row {
  margin-top: 10px;
}

.profile-field-label {
  font-size: 12px;
  color: #7a8b9d;
}

.profile-field-value {
  margin-top: 4px;
  color: #18304b;
  line-height: 1.7;
  word-break: break-word;
}

.profile-tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.profile-tag {
  margin: 0;
}

.profile-summary-list {
  display: grid;
  gap: 10px;
}

.profile-summary-item {
  padding: 12px 14px;
  border-radius: 14px;
  background: #f8fbff;
  color: #30465e;
  line-height: 1.7;
}

.scope-group + .scope-group {
  margin-top: 14px;
}

.scope-label {
  margin-bottom: 8px;
  font-size: 13px;
  font-weight: 700;
  color: #6a7c8f;
}

.profile-raw-collapse {
  border-radius: 18px;
  overflow: hidden;
  background: #fff;
}

.json-panel {
  margin: 0;
  padding: 14px;
  min-height: 180px;
  border-radius: 18px;
  white-space: pre-wrap;
  word-break: break-word;
  background: #0f2134;
  color: #f8f2da;
  font-size: 13px;
  line-height: 1.7;
}
</style>

<template>
  <div class="process-container">
    <!-- 左侧:实时图谱展示区 -->
    <div class="left-panel">
      <div class="panel-header">
        <h2>实时图谱</h2>
      </div>
      <div class="graph-container">
        <div v-if="loading" class="loading-state">
          <div class="loading-spinner-large"></div>
          <p>加载图谱中...</p>
        </div>
        <div v-else-if="error" class="error-state">
          <p>{{ error }}</p>
        </div>
        <div v-else-if="graphData" class="graph-view">
          <!-- 图谱可视化将在这里实现 -->
          <div class="graph-placeholder">
            <p>图谱节点数: {{ graphData.node_count }}</p>
            <p>关系数: {{ graphData.edge_count }}</p>
          </div>
        </div>
        <div v-else class="empty-state">
          <p>暂无图谱数据</p>
        </div>
      </div>
    </div>

    <!-- 右侧:流程展示区 -->
    <div class="right-panel">
      <div class="panel-header">
        <h2>Step 1 - 现实种子构建</h2>
      </div>
      <div class="process-content">
        <!-- 流程步骤 -->
        <div class="steps">
          <div
            v-for="(step, index) in steps"
            :key="index"
            class="step-item"
            :class="{
              'active': currentStep === index,
              'completed': currentStep > index
            }"
          >
            <div class="step-indicator">
              <div class="step-number">{{ index + 1 }}</div>
            </div>
            <div class="step-content">
              <h3>{{ step.title }}</h3>
              <p>{{ step.description }}</p>
              <div v-if="step.status" class="step-status">
                {{ step.status }}
              </div>
            </div>
          </div>
        </div>

        <!-- 项目信息 -->
        <div v-if="projectData" class="project-info">
          <h3>项目信息</h3>
          <div class="info-item">
            <span class="label">项目名称:</span>
            <span class="value">{{ projectData.name }}</span>
          </div>
          <div class="info-item">
            <span class="label">项目ID:</span>
            <span class="value">{{ projectData.project_id }}</span>
          </div>
          <div class="info-item">
            <span class="label">状态:</span>
            <span class="value">{{ projectData.status }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { getProject, buildGraph, getTaskStatus, getGraphData } from '../api/graph'

const route = useRoute()
const projectId = route.params.projectId

// 状态
const loading = ref(true)
const error = ref('')
const projectData = ref(null)
const graphData = ref(null)
const currentStep = ref(0)

// 流程步骤
const steps = ref([
  {
    title: '文档分析',
    description: '正在分析上传的文档内容',
    status: ''
  },
  {
    title: '本体生成',
    description: '使用LLM生成知识图谱本体',
    status: ''
  },
  {
    title: '图谱构建',
    description: '基于本体构建知识图谱',
    status: ''
  },
  {
    title: '完成',
    description: '现实种子构建完成',
    status: ''
  }
])

// 轮询定时器
let pollTimer = null

// 加载项目数据
const loadProject = async () => {
  try {
    const response = await getProject(projectId)
    if (response.success) {
      projectData.value = response.data
      
      // 根据项目状态更新步骤
      updateStepsByProjectStatus(response.data.status)
      
      // 如果本体已生成,自动开始构建图谱
      if (response.data.status === 'ontology_generated' && !response.data.graph_id) {
        await startBuildGraph()
      }
      
      // 如果图谱正在构建,开始轮询任务状态
      if (response.data.status === 'graph_building' && response.data.graph_build_task_id) {
        startPollingTask(response.data.graph_build_task_id)
      }
      
      // 如果图谱已完成,加载图谱数据
      if (response.data.status === 'graph_completed' && response.data.graph_id) {
        await loadGraphData(response.data.graph_id)
      }
    }
  } catch (err) {
    console.error('Load project error:', err)
    error.value = '加载项目失败: ' + (err.message || '未知错误')
  } finally {
    loading.value = false
  }
}

// 根据项目状态更新步骤
const updateStepsByProjectStatus = (status) => {
  switch (status) {
    case 'created':
      currentStep.value = 0
      steps.value[0].status = '进行中...'
      break
    case 'ontology_generated':
      currentStep.value = 1
      steps.value[0].status = '已完成'
      steps.value[1].status = '已完成'
      break
    case 'graph_building':
      currentStep.value = 2
      steps.value[0].status = '已完成'
      steps.value[1].status = '已完成'
      steps.value[2].status = '进行中...'
      break
    case 'graph_completed':
      currentStep.value = 3
      steps.value[0].status = '已完成'
      steps.value[1].status = '已完成'
      steps.value[2].status = '已完成'
      steps.value[3].status = '已完成'
      break
    case 'failed':
      error.value = projectData.value?.error || '项目处理失败'
      break
  }
}

// 开始构建图谱
const startBuildGraph = async () => {
  try {
    const response = await buildGraph({
      project_id: projectId
    })
    
    if (response.success) {
      const taskId = response.data.task_id
      startPollingTask(taskId)
    }
  } catch (err) {
    console.error('Build graph error:', err)
    error.value = '启动图谱构建失败: ' + (err.message || '未知错误')
  }
}

// 开始轮询任务状态
const startPollingTask = (taskId) => {
  pollTimer = setInterval(async () => {
    try {
      const response = await getTaskStatus(taskId)
      if (response.success) {
        const task = response.data
        
        // 更新步骤状态
        if (task.status === 'processing') {
          steps.value[2].status = `${task.message} (${task.progress}%)`
        } else if (task.status === 'completed') {
          steps.value[2].status = '已完成'
          currentStep.value = 3
          
          // 停止轮询
          stopPolling()
          
          // 重新加载项目数据
          await loadProject()
        } else if (task.status === 'failed') {
          error.value = '图谱构建失败: ' + (task.error || '未知错误')
          stopPolling()
        }
      }
    } catch (err) {
      console.error('Poll task status error:', err)
    }
  }, 2000) // 每2秒轮询一次
}

// 停止轮询
const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

// 加载图谱数据
const loadGraphData = async (graphId) => {
  try {
    const response = await getGraphData(graphId)
    if (response.success) {
      graphData.value = response.data
    }
  } catch (err) {
    console.error('Load graph data error:', err)
  }
}

// 生命周期
onMounted(() => {
  loadProject()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.process-container {
  display: flex;
  height: 100vh;
  background-color: #ffffff;
}

/* 左侧面板 */
.left-panel {
  flex: 1;
  border-right: 1px solid #000000;
  display: flex;
  flex-direction: column;
}

/* 右侧面板 */
.right-panel {
  width: 400px;
  display: flex;
  flex-direction: column;
}

/* 面板标题 */
.panel-header {
  padding: 1.5rem;
  border-bottom: 1px solid #000000;
  background-color: #ffffff;
}

.panel-header h2 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 500;
  letter-spacing: 0.05em;
}

/* 图谱容器 */
.graph-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.loading-state,
.error-state,
.empty-state {
  text-align: center;
}

.loading-spinner-large {
  width: 48px;
  height: 48px;
  border: 3px solid #000000;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.graph-placeholder {
  text-align: center;
  padding: 2rem;
  border: 1px solid #000000;
}

/* 流程内容 */
.process-content {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
}

/* 步骤列表 */
.steps {
  margin-bottom: 2rem;
}

.step-item {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
  opacity: 0.4;
  transition: opacity 0.3s;
}

.step-item.active,
.step-item.completed {
  opacity: 1;
}

.step-indicator {
  flex-shrink: 0;
}

.step-number {
  width: 36px;
  height: 36px;
  border: 2px solid #000000;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 500;
  background-color: #ffffff;
  transition: all 0.3s;
}

.step-item.active .step-number {
  background-color: #000000;
  color: #ffffff;
}

.step-item.completed .step-number {
  background-color: #000000;
  color: #ffffff;
}

.step-content h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1rem;
  font-weight: 500;
}

.step-content p {
  margin: 0;
  font-size: 0.9rem;
  color: #666666;
}

.step-status {
  margin-top: 0.5rem;
  font-size: 0.85rem;
  color: #000000;
  font-weight: 500;
}

/* 项目信息 */
.project-info {
  margin-top: 2rem;
  padding: 1.5rem;
  border: 1px solid #000000;
}

.project-info h3 {
  margin: 0 0 1rem 0;
  font-size: 1rem;
  font-weight: 500;
}

.info-item {
  display: flex;
  margin-bottom: 0.75rem;
  font-size: 0.9rem;
}

.info-item .label {
  font-weight: 500;
  margin-right: 0.5rem;
  min-width: 80px;
}

.info-item .value {
  color: #666666;
  word-break: break-all;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .process-container {
    flex-direction: column;
  }
  
  .left-panel {
    border-right: none;
    border-bottom: 1px solid #000000;
    height: 50vh;
  }
  
  .right-panel {
    width: 100%;
    height: 50vh;
  }
}
</style>

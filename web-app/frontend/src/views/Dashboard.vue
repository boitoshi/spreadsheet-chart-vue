<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <h1>📊 投資ポートフォリオ ダッシュボード</h1>
      <p class="dashboard-subtitle">リアルタイムの資産状況と推移を確認できます</p>
    </div>
    
    <div class="dashboard-grid">
      <div class="dashboard-card main-portfolio">
        <PortfolioDashboard />
      </div>
      
      <div class="dashboard-card chart-card">
        <div class="card-header">
          <h3>💹 損益推移</h3>
        </div>
        <ProfitChart />
      </div>
      
      <div class="dashboard-card chart-card">
        <div class="card-header">
          <h3>📈 価格推移</h3>
        </div>
        <LineChart />
      </div>
      
      <div class="dashboard-card data-card">
        <div class="card-header">
          <h3>📋 データ一覧</h3>
        </div>
        <Spreadsheet />
      </div>
    </div>
    
    <div class="quick-actions">
      <router-link to="/input" class="action-button primary">
        <span class="button-icon">✏️</span>
        <span class="button-text">データ入力</span>
      </router-link>
      <router-link to="/report/2024-01" class="action-button secondary">
        <span class="button-icon">📋</span>
        <span class="button-text">月次レポート</span>
      </router-link>
    </div>
  </div>
</template>

<script>
import PortfolioDashboard from '../components/portfolio/PortfolioDashboard.vue'
import Spreadsheet from '../components/portfolio/Spreadsheet.vue'
import ProfitChart from '../components/charts/ProfitChart.vue'
import LineChart from '../components/charts/LineChart.vue'

export default {
  name: 'Dashboard',
  components: {
    PortfolioDashboard,
    Spreadsheet,
    ProfitChart,
    LineChart
  }
}
</script>

<style scoped>
.dashboard {
  padding: 0;
  max-width: 1600px;
  margin: 0 auto;
  min-height: calc(100vh - 120px);
}

.dashboard-header {
  text-align: center;
  margin-bottom: 2.5rem;
  padding: 2rem 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.dashboard-header h1 {
  font-size: 2.5rem;
  font-weight: 700;
  color: #333333;
  margin-bottom: 0.5rem;
}

.dashboard-subtitle {
  color: #64748b;
  font-size: 1.1rem;
  font-weight: 500;
  margin: 0;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: auto auto;
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.main-portfolio {
  grid-column: 1 / -1;
}

.dashboard-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border: 1px solid #e9ecef;
  overflow: hidden;
  position: relative;
}

.main-portfolio {
  background: #ffffff;
}

.card-header {
  padding: 1.5rem 1.5rem 0;
  border-bottom: 1px solid #f1f5f9;
  margin-bottom: 1rem;
}

.card-header h3 {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
  padding-bottom: 1rem;
}

.chart-card {
  min-height: 400px;
  display: flex;
  flex-direction: column;
}

.data-card {
  min-height: 300px;
}

.quick-actions {
  display: flex;
  justify-content: center;
  gap: 1rem;
  margin-top: 2rem;
  padding: 1rem;
}

.action-button {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 2rem;
  border-radius: 12px;
  text-decoration: none;
  font-weight: 600;
  font-size: 1rem;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  min-width: 160px;
  justify-content: center;
}

.action-button.primary {
  background: #2563eb;
  color: white;
}

.action-button.secondary {
  background: #7c3aed;
  color: white;
}

.action-button:hover {
  opacity: 0.9;
}

.button-icon {
  font-size: 1.25rem;
}

.button-text {
  font-weight: 600;
}

@media (max-width: 1024px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
  
  .main-portfolio {
    grid-column: 1;
  }
  
  .dashboard-header h1 {
    font-size: 2rem;
  }
}

@media (max-width: 768px) {
  .dashboard {
    padding: 0;
  }
  
  .dashboard-header {
    padding: 1.5rem 1rem;
    margin-bottom: 1.5rem;
  }
  
  .dashboard-header h1 {
    font-size: 1.75rem;
  }
  
  .dashboard-subtitle {
    font-size: 1rem;
  }
  
  .dashboard-grid {
    gap: 1rem;
    margin-bottom: 1.5rem;
  }
  
  .quick-actions {
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
  }
  
  .action-button {
    width: 100%;
    max-width: 280px;
  }
  
  .chart-card {
    min-height: 300px;
  }
}

@media (max-width: 480px) {
  .dashboard-header h1 {
    font-size: 1.5rem;
  }
  
  .card-header {
    padding: 1rem 1rem 0;
  }
  
  .card-header h3 {
    font-size: 1.1rem;
  }
}
</style>
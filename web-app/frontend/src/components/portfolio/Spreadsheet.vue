<template>
    <div class="spreadsheet-container">
      <h3>📋 データ詳細</h3>
      <div v-if="loading" class="loading">📈 データを取得中...</div>
      <div v-else-if="error" class="error">❌ {{ error }}</div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th v-for="(header, index) in headers" :key="index">{{ header }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, index) in dataRows" :key="index">
            <td v-for="(cell, cellIndex) in row" :key="cellIndex" 
                :class="{ 'profit': cellIndex === 5 && parseFloat(cell.replace(/[^\d.-]/g, '')) > 0,
                         'loss': cellIndex === 5 && parseFloat(cell.replace(/[^\d.-]/g, '')) < 0 }">
              {{ cell }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted, computed } from "vue";
  
  const spreadsheetData = ref([]);
  const loading = ref(true);
  const error = ref(null);
  
  // ヘッダーとデータ行を分離
  const headers = computed(() => spreadsheetData.value[0] || []);
  const dataRows = computed(() => spreadsheetData.value.slice(1) || []);
  
  const fetchData = async () => {
    try {
      // ダミーデータ（スプレッドシート形式）
      const dummyData = [
        ['銘柄', '数量', '取得価格', '現在価格', '評価額', '損益'],
        ['トヨタ自動車', '100株', '¥2,500', '¥2,800', '¥280,000', '+¥30,000'],
        ['ソフトバンク', '200株', '¥1,200', '¥1,150', '¥230,000', '-¥10,000'],
        ['任天堂', '50株', '¥5,600', '¥6,200', '¥310,000', '+¥30,000'],
        ['DeNA', '150株', '¥2,100', '¥2,350', '¥352,500', '+¥37,500'],
        ['KDDI', '80株', '¥3,800', '¥3,900', '¥312,000', '+¥8,000']
      ]
      
      // 実際のAPIを模擬した遅延
      await new Promise(resolve => setTimeout(resolve, 300))
      
      spreadsheetData.value = dummyData
    } catch (err) {
      error.value = "データ取得に失敗しました: " + err.message;
    } finally {
      loading.value = false;
    }
  };
  
  onMounted(() => {
    fetchData();
  });
  </script>
  
  <style scoped>
  .spreadsheet-container {
    padding: 1rem;
  }
  
  h3 {
    margin: 0 0 1rem 0;
    color: #333;
    font-weight: 600;
  }
  
  .loading, .error {
    text-align: center;
    padding: 2rem;
    font-size: 1.1rem;
  }
  
  .error {
    color: #dc3545;
  }
  
  .data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
  }
  
  .data-table th,
  .data-table td {
    padding: 0.75rem;
    text-align: left;
    border-bottom: 1px solid #e9ecef;
  }
  
  .data-table th {
    background-color: #f8f9fa;
    font-weight: 600;
    color: #495057;
  }
  
  .data-table tbody tr:hover {
    background-color: #f8f9fa;
  }
  
  .profit {
    color: #28a745;
    font-weight: 600;
  }
  
  .loss {
    color: #dc3545;
    font-weight: 600;
  }
  </style>

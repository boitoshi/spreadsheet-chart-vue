<template>
    <div>
      <h2>スプレッドシートデータ</h2>
      <div v-if="loading">データを取得中...</div>
      <div v-else-if="error">{{ error }}</div>
      <ul v-else>
        <li v-for="(row, index) in spreadsheetData" :key="index">
          {{ row.join(', ') }}
        </li>
      </ul>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted } from "vue";
  
  const spreadsheetData = ref([]);
  const loading = ref(true);
  const error = ref(null);
  
  const fetchData = async () => {
    try {
      // ダミーデータ（スプレッドシート形式）
      const dummyData = [
        ['銘柄', '数量', '取得価格', '現在価格', '評価額', '損益'],
        ['トヨタ自動車', '100', '2500', '2800', '280000', '30000'],
        ['ソフトバンク', '200', '1200', '1150', '230000', '-10000'],
        ['任天堂', '50', '5600', '6200', '310000', '30000'],
        ['DeNA', '150', '2100', '2350', '352500', '37500']
      ]
      
      // 実際のAPIを模擬した遅延
      await new Promise(resolve => setTimeout(resolve, 200))
      
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
  h2 {
    text-align: center;
  }
  </style>

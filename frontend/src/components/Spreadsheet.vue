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
  import axios from "axios";
  
  const spreadsheetData = ref([]);
  const loading = ref(true);
  const error = ref(null);
  
  const fetchData = async () => {
    try {
      const response = await axios.get("http://127.0.0.1:8000/get_data/");
      spreadsheetData.value = response.data.data; // DjangoのJSON形式に合わせて変更
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

import { ref } from 'vue';

export function useSpreadsheetData(startMonth = '2023-01', endMonth = '2023-12') {
  const data = ref([]);
  const error = ref(null);
  const loading = ref(false);

  const fetchData = async () => {
    loading.value = true;
    try {
      // ダミーデータ（月次推移データ）
      const dummyData = [
        { label: '2024-01-01', stock: 'トヨタ自動車', quantity: 100, purchase: 2500, value: 2600 },
        { label: '2024-01-01', stock: 'ソフトバンク', quantity: 200, purchase: 1200, value: 1180 },
        { label: '2024-01-01', stock: '任天堂', quantity: 50, purchase: 5600, value: 5800 },
        { label: '2024-01-01', stock: 'DeNA', quantity: 150, purchase: 2100, value: 2200 },
        
        { label: '2024-02-01', stock: 'トヨタ自動車', quantity: 100, purchase: 2500, value: 2700 },
        { label: '2024-02-01', stock: 'ソフトバンク', quantity: 200, purchase: 1200, value: 1150 },
        { label: '2024-02-01', stock: '任天堂', quantity: 50, purchase: 5600, value: 6000 },
        { label: '2024-02-01', stock: 'DeNA', quantity: 150, purchase: 2100, value: 2250 },
        
        { label: '2024-03-01', stock: 'トヨタ自動車', quantity: 100, purchase: 2500, value: 2800 },
        { label: '2024-03-01', stock: 'ソフトバンク', quantity: 200, purchase: 1200, value: 1150 },
        { label: '2024-03-01', stock: '任天堂', quantity: 50, purchase: 5600, value: 6200 },
        { label: '2024-03-01', stock: 'DeNA', quantity: 150, purchase: 2100, value: 2350 },
        
        { label: '2024-04-01', stock: 'トヨタ自動車', quantity: 100, purchase: 2500, value: 2750 },
        { label: '2024-04-01', stock: 'ソフトバンク', quantity: 200, purchase: 1200, value: 1200 },
        { label: '2024-04-01', stock: '任天堂', quantity: 50, purchase: 5600, value: 6100 },
        { label: '2024-04-01', stock: 'DeNA', quantity: 150, purchase: 2100, value: 2300 }
      ]
      
      // 実際のAPIを模擬した遅延
      await new Promise(resolve => setTimeout(resolve, 300))
      
      data.value = dummyData
    } catch (err) {
      error.value = err;
    } finally {
      loading.value = false;
    }
  };

  return { data, error, loading, fetchData };
}

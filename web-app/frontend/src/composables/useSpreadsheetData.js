import { ref } from 'vue';
import { apiService } from '../utils/api.js';

export function useSpreadsheetData(startMonth = '2023-01', endMonth = '2023-12') {
  const data = ref([]);
  const error = ref(null);
  const loading = ref(false);

  const fetchData = async () => {
    loading.value = true;
    try {
      const response = await apiService.getSpreadsheetData({
        startMonth,
        endMonth
      });
      
      data.value = response.data || [];
    } catch (err) {
      error.value = err;
    } finally {
      loading.value = false;
    }
  };

  return { data, error, loading, fetchData };
}

import { create } from 'zustand';

const useStore = create((set) => ({
  analysis: null,
  agreement: null,
  loading: true,
  error: null,
  activeStage: 0,

  setActiveStage: (stage) => set({ activeStage: stage }),

  fetchData: async () => {
    try {
      set({ loading: true, error: null });
      const [analysisRes, agreementRes] = await Promise.all([
        fetch('/analysis.json'),
        fetch('/final_agreement.json'),
      ]);
      if (!analysisRes.ok) throw new Error(`analysis.json: HTTP ${analysisRes.status}`);
      if (!agreementRes.ok) throw new Error(`final_agreement.json: HTTP ${agreementRes.status}`);
      const analysis = await analysisRes.json();
      const agreement = await agreementRes.json();
      set({ analysis, agreement, loading: false });
    } catch (err) {
      set({ error: err.message, loading: false });
    }
  },
}));

export default useStore;

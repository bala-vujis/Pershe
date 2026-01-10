import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const useStore = create(
  persist(
    (set) => ({
      user: null,
      token: null,
      setAuth: (user, token) => {
        localStorage.setItem('token', token);
        localStorage.setItem('user', JSON.stringify(user));
        set({ user, token });
      },
      logout: () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        set({ user: null, token: null });
      },
      // Project wizard state
      wizardStep: 1,
      wizardData: {},
      setWizardStep: (step) => set({ wizardStep: step }),
      setWizardData: (data) => set((state) => ({ wizardData: { ...state.wizardData, ...data } })),
      resetWizard: () => set({ wizardStep: 1, wizardData: {} }),
    }),
    {
      name: 'sheet-personalizer-storage',
      partialize: (state) => ({ user: state.user, token: state.token }),
    }
  )
);

export default useStore;

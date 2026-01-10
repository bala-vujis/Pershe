import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ChevronLeft, Check } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import Step1Connect from '@/components/wizard/Step1Connect';
import Step2SelectSheet from '@/components/wizard/Step2SelectSheet';
import Step3MapColumns from '@/components/wizard/Step3MapColumns';
import Step4ConfigurePrompts from '@/components/wizard/Step4ConfigurePrompts';
import Step5Run from '@/components/wizard/Step5Run';
import useStore from '@/store/useStore';

const NewProject = () => {
  const navigate = useNavigate();
  const { wizardStep, setWizardStep, resetWizard } = useStore();
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    return () => {
      if (wizardStep === 5) {
        resetWizard();
      }
    };
  }, []);

  const steps = [
    { number: 1, label: 'Connect' },
    { number: 2, label: 'Select Sheet' },
    { number: 3, label: 'Map Columns' },
    { number: 4, label: 'Configure' },
    { number: 5, label: 'Run' }
  ];

  return (
    <div className="min-h-screen bg-black">
      <div className="max-w-5xl mx-auto px-6 py-8">
        <div className="mb-8">
          <Button
            variant="ghost"
            onClick={() => navigate('/dashboard')}
            className="mb-6"
            data-testid="back-to-dashboard-btn"
          >
            <ChevronLeft className="w-4 h-4 mr-2" /> Back to Dashboard
          </Button>
          
          <h1 className="text-4xl font-outfit font-semibold mb-6">New Project</h1>
          
          <div className="flex items-center gap-2 mb-8" data-testid="wizard-stepper">
            {steps.map((step, idx) => (
              <div key={step.number} className="flex items-center">
                <div className="flex flex-col items-center gap-1">
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm ${
                      wizardStep > step.number
                        ? 'bg-emerald-500 text-black'
                        : wizardStep === step.number
                        ? 'bg-emerald-500 text-black shadow-[0_0_15px_rgba(16,185,129,0.5)]'
                        : 'bg-zinc-900 border border-zinc-800 text-zinc-500'
                    }`}
                    data-testid={`step-indicator-${step.number}`}
                  >
                    {wizardStep > step.number ? <Check className="w-5 h-5" /> : step.number}
                  </div>
                  <span className="text-xs text-zinc-500">{step.label}</span>
                </div>
                {idx < steps.length - 1 && (
                  <div className="h-[1px] w-16 bg-zinc-800 mx-2" />
                )}
              </div>
            ))}
          </div>
        </div>

        <motion.div
          key={wizardStep}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ duration: 0.3 }}
          className="bg-zinc-900/40 border border-white/10 rounded-2xl p-8"
        >
          {wizardStep === 1 && <Step1Connect onConnected={setIsConnected} />}
          {wizardStep === 2 && <Step2SelectSheet />}
          {wizardStep === 3 && <Step3MapColumns />}
          {wizardStep === 4 && <Step4ConfigurePrompts />}
          {wizardStep === 5 && <Step5Run />}
        </motion.div>
      </div>
    </div>
  );
};

export default NewProject;

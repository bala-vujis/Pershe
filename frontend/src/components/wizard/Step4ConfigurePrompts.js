import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import useStore from '@/store/useStore';

const Step4ConfigurePrompts = () => {
  const { setWizardStep, wizardData, setWizardData } = useStore();
  const [config, setConfig] = useState({
    summaryPreset: wizardData.summaryPreset || 'logistics',
    icebreakerPrompt: wizardData.icebreakerPrompt || `Hey {FirstName},\n\nI noticed [specific detail from {company_name}]. [Ask relevant question or make relevant observation].\n\nWorth a quick chat?`,
    model: wizardData.model || 'gpt-4o-mini'
  });

  const handleNext = () => {
    setWizardData(config);
    setWizardStep(5);
  };

  return (
    <div data-testid="step-4-configure-prompts">
      <h2 className="text-3xl font-outfit font-semibold mb-4">Configure Prompts</h2>
      <p className="text-zinc-400 mb-8">
        Customize how we analyze companies and generate icebreakers.
      </p>

      <div className="space-y-6">
        <div>
          <Label className="text-sm text-zinc-300 mb-2 block">AI Model</Label>
          <Select value={config.model} onValueChange={(v) => setConfig({...config, model: v})}>
            <SelectTrigger data-testid="model-select" className="bg-zinc-950/50 border-zinc-800 text-white">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-zinc-900 border-zinc-800">
              <SelectItem value="gpt-4o-mini" className="text-white">GPT-4o Mini (Recommended)</SelectItem>
              <SelectItem value="gpt-4o" className="text-white">GPT-4o (More Powerful)</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div>
          <Label className="text-sm text-zinc-300 mb-2 block">Summary Style Preset</Label>
          <Select value={config.summaryPreset} onValueChange={(v) => setConfig({...config, summaryPreset: v})}>
            <SelectTrigger data-testid="summary-preset-select" className="bg-zinc-950/50 border-zinc-800 text-white">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-zinc-900 border-zinc-800">
              <SelectItem value="logistics" className="text-white">Logistics (Services, Modes, Geographies)</SelectItem>
              <SelectItem value="industrial" className="text-white">Industrial (Products, Materials, Certifications)</SelectItem>
            </SelectContent>
          </Select>
          <p className="text-xs text-zinc-500 mt-2">
            Selects which facts to extract from company websites.
          </p>
        </div>

        <div>
          <Label className="text-sm text-zinc-300 mb-2 block">Icebreaker Prompt Template</Label>
          <Textarea
            value={config.icebreakerPrompt}
            onChange={(e) => setConfig({...config, icebreakerPrompt: e.target.value})}
            data-testid="icebreaker-prompt-textarea"
            rows={6}
            className="bg-zinc-950/50 border-zinc-800 text-white font-mono text-sm"
            placeholder="Use variables like {FirstName}, {company_name}, etc."
          />
          <p className="text-xs text-zinc-500 mt-2">
            Variables: {'{FirstName}'}, {'{company_name}'}, {'{title}'}
          </p>
        </div>

        <div className="bg-zinc-900/40 border border-emerald-500/20 rounded-lg p-4">
          <p className="text-sm text-zinc-300">
            <strong className="text-emerald-400">Tip:</strong> Run a preview on 3 rows first to test your prompts before processing the full list.
          </p>
        </div>

        <div className="flex gap-4">
          <Button
            variant="ghost"
            onClick={() => setWizardStep(3)}
            data-testid="step-4-back-btn"
          >
            Back
          </Button>
          <Button
            onClick={handleNext}
            data-testid="step-4-next-btn"
            className="bg-emerald-500 hover:bg-emerald-400 text-black font-medium"
          >
            Next: Run
          </Button>
        </div>
      </div>
    </div>
  );
};

export default Step4ConfigurePrompts;

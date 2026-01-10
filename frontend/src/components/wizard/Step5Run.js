import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Play, Sparkles } from 'lucide-react';
import { toast } from 'sonner';
import api from '@/utils/api';
import useStore from '@/store/useStore';

const Step5Run = () => {
  const navigate = useNavigate();
  const { wizardData, resetWizard } = useStore();
  const [loading, setLoading] = useState(false);

  const handleCreateAndRun = async (mode) => {
    setLoading(true);
    try {
      // Create project
      const projectPayload = {
        name: wizardData.projectName,
        spreadsheet_id: wizardData.spreadsheetId,
        sheet_name: wizardData.sheetName,
        header_row: 1
      };

      const fieldMappingPayload = {
        website_col: wizardData.websiteCol,
        first_name_col: wizardData.firstNameCol,
        company_col: wizardData.companyCol,
        email_col: wizardData.emailCol || null,
        title_col: wizardData.titleCol || null,
        description_col: wizardData.descriptionCol || null,
        output_mode: wizardData.outputMode,
        output_sheet_name: wizardData.outputSheetName || null
      };

      const promptConfigPayload = {
        summary_preset: wizardData.summaryPreset,
        icebreaker_prompt: wizardData.icebreakerPrompt,
        model: wizardData.model
      };

      const projectResponse = await api.post('/projects', {
        project: projectPayload,
        field_mapping: fieldMappingPayload,
        prompt_config: promptConfigPayload
      });

      const projectId = projectResponse.data.project_id;

      // Create run
      const runPayload = {
        project_id: projectId,
        mode: mode,
        max_rows: mode === 'preview' ? 3 : null
      };

      const runResponse = await api.post('/runs', runPayload);
      const runId = runResponse.data.run_id;

      toast.success(`${mode === 'preview' ? 'Preview' : 'Full'} run started!`);
      resetWizard();
      navigate(`/runs/${runId}`);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create run');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div data-testid="step-5-run">
      <h2 className="text-3xl font-outfit font-semibold mb-4">Ready to Run</h2>
      <p className="text-zinc-400 mb-8">
        You're all set! Choose how you want to process your leads.
      </p>

      <div className="space-y-6">
        <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-6">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-lg bg-emerald-500/20 flex items-center justify-center flex-shrink-0">
              <Sparkles className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <h3 className="text-lg font-outfit font-medium text-emerald-400 mb-2">Preview Mode (Recommended)</h3>
              <p className="text-sm text-zinc-300 mb-4">
                Test your configuration on the first 3 rows. This helps you verify everything works before processing your full list.
              </p>
              <ul className="text-sm text-zinc-400 space-y-1 mb-4">
                <li>• Processes 3 rows</li>
                <li>• Costs 3 credits</li>
                <li>• See results in ~30 seconds</li>
              </ul>
              <Button
                onClick={() => handleCreateAndRun('preview')}
                disabled={loading}
                data-testid="run-preview-btn"
                className="bg-emerald-500 hover:bg-emerald-400 text-black font-medium"
              >
                <Play className="w-4 h-4 mr-2" />
                {loading ? 'Starting...' : 'Run Preview'}
              </Button>
            </div>
          </div>
        </div>

        <div className="bg-zinc-900/40 border border-white/10 rounded-xl p-6">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-lg bg-zinc-800 flex items-center justify-center flex-shrink-0">
              <Play className="w-5 h-5 text-zinc-400" />
            </div>
            <div>
              <h3 className="text-lg font-outfit font-medium mb-2">Full Run</h3>
              <p className="text-sm text-zinc-400 mb-4">
                Process all rows in your sheet. Recommended after running a successful preview.
              </p>
              <ul className="text-sm text-zinc-500 space-y-1 mb-4">
                <li>• Processes all rows</li>
                <li>• 1 credit per row</li>
                <li>• Results written back to your sheet</li>
              </ul>
              <Button
                onClick={() => handleCreateAndRun('full')}
                disabled={loading}
                data-testid="run-full-btn"
                variant="secondary"
              >
                <Play className="w-4 h-4 mr-2" />
                {loading ? 'Starting...' : 'Run Full'}
              </Button>
            </div>
          </div>
        </div>

        <div className="flex gap-4">
          <Button
            variant="ghost"
            onClick={() => useStore.getState().setWizardStep(4)}
            disabled={loading}
            data-testid="step-5-back-btn"
          >
            Back
          </Button>
        </div>
      </div>
    </div>
  );
};

export default Step5Run;

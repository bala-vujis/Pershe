import { useState, useEffect } from 'react';
import { FileSpreadsheet, ChevronDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import api from '@/utils/api';
import useStore from '@/store/useStore';

const Step2SelectSheet = () => {
  const { setWizardStep, wizardData, setWizardData } = useStore();
  const [spreadsheets, setSpreadsheets] = useState([]);
  const [tabs, setTabs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingTabs, setLoadingTabs] = useState(false);
  const [projectName, setProjectName] = useState(wizardData.projectName || '');
  const [selectedSpreadsheet, setSelectedSpreadsheet] = useState(wizardData.spreadsheetId || '');
  const [selectedTab, setSelectedTab] = useState(wizardData.sheetName || '');

  useEffect(() => {
    fetchSpreadsheets();
  }, []);

  useEffect(() => {
    if (selectedSpreadsheet) {
      fetchTabs(selectedSpreadsheet);
    }
  }, [selectedSpreadsheet]);

  const fetchSpreadsheets = async () => {
    try {
      const response = await api.get('/sheets/spreadsheets');
      setSpreadsheets(response.data.spreadsheets || []);
    } catch (error) {
      toast.error('Failed to fetch spreadsheets');
    } finally {
      setLoading(false);
    }
  };

  const fetchTabs = async (spreadsheetId) => {
    setLoadingTabs(true);
    try {
      const response = await api.get(`/sheets/${spreadsheetId}/tabs`);
      setTabs(response.data.tabs || []);
    } catch (error) {
      toast.error('Failed to fetch sheet tabs');
    } finally {
      setLoadingTabs(false);
    }
  };

  const handleNext = () => {
    if (!projectName || !selectedSpreadsheet || !selectedTab) {
      toast.error('Please fill in all fields');
      return;
    }

    const selectedSheet = spreadsheets.find(s => s.id === selectedSpreadsheet);
    setWizardData({
      projectName,
      spreadsheetId: selectedSpreadsheet,
      spreadsheetName: selectedSheet?.name,
      sheetName: selectedTab
    });
    setWizardStep(3);
  };

  return (
    <div data-testid="step-2-select-sheet">
      <h2 className="text-3xl font-outfit font-semibold mb-4">Select Your Sheet</h2>
      <p className="text-zinc-400 mb-8">
        Choose the spreadsheet and sheet containing your leads.
      </p>

      {loading ? (
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-emerald-500"></div>
        </div>
      ) : (
        <div className="space-y-6">
          <div>
            <Label className="text-sm text-zinc-300 mb-2 block">Project Name</Label>
            <Input
              placeholder="e.g., Q1 Logistics Outreach"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              data-testid="project-name-input"
              className="bg-zinc-950/50 border-zinc-800 focus:border-emerald-500/50 text-white"
            />
          </div>

          <div>
            <Label className="text-sm text-zinc-300 mb-2 block">Spreadsheet</Label>
            <Select value={selectedSpreadsheet} onValueChange={setSelectedSpreadsheet}>
              <SelectTrigger data-testid="spreadsheet-select" className="bg-zinc-950/50 border-zinc-800 text-white">
                <SelectValue placeholder="Select a spreadsheet" />
              </SelectTrigger>
              <SelectContent className="bg-zinc-900 border-zinc-800">
                {spreadsheets.map((sheet) => (
                  <SelectItem key={sheet.id} value={sheet.id} className="text-white">
                    {sheet.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {selectedSpreadsheet && (
            <div>
              <Label className="text-sm text-zinc-300 mb-2 block">Sheet Tab</Label>
              <Select value={selectedTab} onValueChange={setSelectedTab}>
                <SelectTrigger data-testid="sheet-tab-select" className="bg-zinc-950/50 border-zinc-800 text-white">
                  <SelectValue placeholder="Select a sheet tab" />
                </SelectTrigger>
                <SelectContent className="bg-zinc-900 border-zinc-800">
                  {tabs.map((tab) => (
                    <SelectItem key={tab.name} value={tab.name} className="text-white">
                      {tab.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          <div className="flex gap-4">
            <Button
              variant="ghost"
              onClick={() => setWizardStep(1)}
              data-testid="step-2-back-btn"
            >
              Back
            </Button>
            <Button
              onClick={handleNext}
              data-testid="step-2-next-btn"
              className="bg-emerald-500 hover:bg-emerald-400 text-black font-medium"
            >
              Next: Map Columns
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Step2SelectSheet;

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
  const [startRow, setStartRow] = useState(wizardData.startRow || 2);
  const [endRow, setEndRow] = useState(wizardData.endRow || 100);

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

  const calculateEstimatedTime = () => {
    const rowCount = endRow - startRow + 1;
    // Each row takes ~10 seconds (scraping + LLM calls)
    const totalSeconds = rowCount * 10;
    const minutes = Math.ceil(totalSeconds / 60);
    return { rowCount, minutes };
  };

  const handleNext = () => {
    if (!projectName || !selectedSpreadsheet || !selectedTab) {
      toast.error('Please fill in all fields');
      return;
    }

    if (startRow < 2) {
      toast.error('Start row must be at least 2 (row 1 is headers)');
      return;
    }

    if (endRow < startRow) {
      toast.error('End row must be greater than start row');
      return;
    }

    const rowCount = endRow - startRow + 1;
    if (rowCount > 500) {
      toast.error('Maximum 500 rows per run. Please adjust your range.');
      return;
    }

    const selectedSheet = spreadsheets.find(s => s.id === selectedSpreadsheet);
    setWizardData({
      projectName,
      spreadsheetId: selectedSpreadsheet,
      spreadsheetName: selectedSheet?.name,
      sheetName: selectedTab,
      startRow,
      endRow
    });
    setWizardStep(3);
  };

  const estimate = calculateEstimatedTime();

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

          <div className="border-t border-white/10 pt-6">
            <h3 className="text-lg font-outfit font-medium mb-4">Row Range</h3>
            <p className="text-sm text-zinc-400 mb-4">Row 1 contains headers. Processing starts from row 2.</p>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-sm text-zinc-300 mb-2 block">Start Row</Label>
                <Input
                  type="number"
                  min="2"
                  value={startRow}
                  onChange={(e) => setStartRow(parseInt(e.target.value) || 2)}
                  data-testid="start-row-input"
                  className="bg-zinc-950/50 border-zinc-800 text-white"
                />
              </div>
              <div>
                <Label className="text-sm text-zinc-300 mb-2 block">End Row</Label>
                <Input
                  type="number"
                  min="2"
                  value={endRow}
                  onChange={(e) => setEndRow(parseInt(e.target.value) || 100)}
                  data-testid="end-row-input"
                  className="bg-zinc-950/50 border-zinc-800 text-white"
                />
              </div>
            </div>

            <div className="mt-4 p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-emerald-400">Estimated Processing</p>
                  <p className="text-xs text-zinc-400 mt-1">Based on {estimate.rowCount} rows</p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-emerald-400">~{estimate.minutes} min</p>
                  <p className="text-xs text-zinc-500">10 sec per row avg</p>
                </div>
              </div>
              <p className="text-xs text-zinc-500 mt-3">
                💡 Maximum: 500 rows per run • Preview mode: 3 rows only
              </p>
            </div>
          </div>

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
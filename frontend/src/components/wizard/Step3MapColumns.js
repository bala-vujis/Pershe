import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Input } from '@/components/ui/input';
import { toast } from 'sonner';
import api from '@/utils/api';
import useStore from '@/store/useStore';

const Step3MapColumns = () => {
  const { setWizardStep, wizardData, setWizardData } = useStore();
  const [headers, setHeaders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [mapping, setMapping] = useState({
    websiteCol: wizardData.websiteCol || '',
    firstNameCol: wizardData.firstNameCol || '',
    companyCol: wizardData.companyCol || '',
    emailCol: wizardData.emailCol || '',
    titleCol: wizardData.titleCol || '',
    descriptionCol: wizardData.descriptionCol || '',
    outputMode: wizardData.outputMode || 'same_sheet',
    outputSheetName: wizardData.outputSheetName || ''
  });

  useEffect(() => {
    fetchHeaders();
  }, []);

  const fetchHeaders = async () => {
    try {
      const response = await api.get(
        `/sheets/${wizardData.spreadsheetId}/values?sheet_name=${encodeURIComponent(wizardData.sheetName)}&range_notation=A1:Z1`
      );
      const values = response.data.values || [];
      if (values.length > 0) {
        setHeaders(values[0]);
        autoDetectColumns(values[0]);
      }
    } catch (error) {
      toast.error('Failed to fetch sheet headers');
    } finally {
      setLoading(false);
    }
  };

  const autoDetectColumns = (headers) => {
    const lowerHeaders = headers.map(h => h.toLowerCase());
    const newMapping = { ...mapping };

    // Auto-detect common column names
    const websiteIdx = lowerHeaders.findIndex(h => h.includes('website') || h.includes('url'));
    if (websiteIdx !== -1) newMapping.websiteCol = headers[websiteIdx];

    const firstNameIdx = lowerHeaders.findIndex(h => h.includes('first') || h.includes('firstname'));
    if (firstNameIdx !== -1) newMapping.firstNameCol = headers[firstNameIdx];

    const companyIdx = lowerHeaders.findIndex(h => h.includes('company') || h.includes('organization'));
    if (companyIdx !== -1) newMapping.companyCol = headers[companyIdx];

    const emailIdx = lowerHeaders.findIndex(h => h.includes('email'));
    if (emailIdx !== -1) newMapping.emailCol = headers[emailIdx];

    const titleIdx = lowerHeaders.findIndex(h => h.includes('title') || h.includes('position'));
    if (titleIdx !== -1) newMapping.titleCol = headers[titleIdx];

    const descIdx = lowerHeaders.findIndex(h => h.includes('description') || h.includes('notes'));
    if (descIdx !== -1) newMapping.descriptionCol = headers[descIdx];

    setMapping(newMapping);
  };

  const handleNext = () => {
    if (!mapping.websiteCol || !mapping.firstNameCol || !mapping.companyCol) {
      toast.error('Please map required fields: Website, First Name, and Company');
      return;
    }

    setWizardData(mapping);
    setWizardStep(4);
  };

  return (
    <div data-testid="step-3-map-columns">
      <h2 className="text-3xl font-outfit font-semibold mb-4">Map Columns</h2>
      <p className="text-zinc-400 mb-8">
        Tell us which columns contain your lead data.
      </p>

      {loading ? (
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-emerald-500"></div>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <Label className="text-sm text-zinc-300 mb-2 block">Website URL <span className="text-red-400">*</span></Label>
              <Select value={mapping.websiteCol} onValueChange={(v) => setMapping({...mapping, websiteCol: v})}>
                <SelectTrigger data-testid="website-col-select" className="bg-zinc-950/50 border-zinc-800 text-white">
                  <SelectValue placeholder="Select column" />
                </SelectTrigger>
                <SelectContent className="bg-zinc-900 border-zinc-800">
                  {headers.map((h) => (
                    <SelectItem key={h} value={h} className="text-white">{h}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label className="text-sm text-zinc-300 mb-2 block">First Name <span className="text-red-400">*</span></Label>
              <Select value={mapping.firstNameCol} onValueChange={(v) => setMapping({...mapping, firstNameCol: v})}>
                <SelectTrigger data-testid="firstname-col-select" className="bg-zinc-950/50 border-zinc-800 text-white">
                  <SelectValue placeholder="Select column" />
                </SelectTrigger>
                <SelectContent className="bg-zinc-900 border-zinc-800">
                  {headers.map((h) => (
                    <SelectItem key={h} value={h} className="text-white">{h}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label className="text-sm text-zinc-300 mb-2 block">Company Name <span className="text-red-400">*</span></Label>
              <Select value={mapping.companyCol} onValueChange={(v) => setMapping({...mapping, companyCol: v})}>
                <SelectTrigger data-testid="company-col-select" className="bg-zinc-950/50 border-zinc-800 text-white">
                  <SelectValue placeholder="Select column" />
                </SelectTrigger>
                <SelectContent className="bg-zinc-900 border-zinc-800">
                  {headers.map((h) => (
                    <SelectItem key={h} value={h} className="text-white">{h}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label className="text-sm text-zinc-300 mb-2 block">Email (Optional)</Label>
              <Select value={mapping.emailCol || "none"} onValueChange={(v) => setMapping({...mapping, emailCol: v === "none" ? "" : v})}>
                <SelectTrigger data-testid="email-col-select" className="bg-zinc-950/50 border-zinc-800 text-white">
                  <SelectValue placeholder="Select column" />
                </SelectTrigger>
                <SelectContent className="bg-zinc-900 border-zinc-800">
                  <SelectItem value="none" className="text-white">None</SelectItem>
                  {headers.map((h) => (
                    <SelectItem key={h} value={h} className="text-white">{h}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label className="text-sm text-zinc-300 mb-2 block">Title (Optional)</Label>
              <Select value={mapping.titleCol || "none"} onValueChange={(v) => setMapping({...mapping, titleCol: v === "none" ? "" : v})}>
                <SelectTrigger data-testid="title-col-select" className="bg-zinc-950/50 border-zinc-800 text-white">
                  <SelectValue placeholder="Select column" />
                </SelectTrigger>
                <SelectContent className="bg-zinc-900 border-zinc-800">
                  <SelectItem value="none" className="text-white">None</SelectItem>
                  {headers.map((h) => (
                    <SelectItem key={h} value={h} className="text-white">{h}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label className="text-sm text-zinc-300 mb-2 block">Description (Optional)</Label>
              <Select value={mapping.descriptionCol || "none"} onValueChange={(v) => setMapping({...mapping, descriptionCol: v === "none" ? "" : v})}>
                <SelectTrigger data-testid="description-col-select" className="bg-zinc-950/50 border-zinc-800 text-white">
                  <SelectValue placeholder="Select column" />
                </SelectTrigger>
                <SelectContent className="bg-zinc-900 border-zinc-800">
                  <SelectItem value="none" className="text-white">None</SelectItem>
                  {headers.map((h) => (
                    <SelectItem key={h} value={h} className="text-white">{h}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="border-t border-white/10 pt-6">
            <h3 className="text-lg font-outfit font-medium mb-4">Output Settings</h3>
            <div className="flex items-center gap-3 mb-4">
              <Switch
                checked={mapping.outputMode === 'same_sheet'}
                onCheckedChange={(checked) => setMapping({...mapping, outputMode: checked ? 'same_sheet' : 'new_sheet'})}
                data-testid="output-mode-switch"
              />
              <Label className="text-sm text-zinc-300">Write results to same sheet</Label>
            </div>
            {mapping.outputMode === 'new_sheet' && (
              <Input
                placeholder="Output sheet name"
                value={mapping.outputSheetName}
                onChange={(e) => setMapping({...mapping, outputSheetName: e.target.value})}
                data-testid="output-sheet-name-input"
                className="bg-zinc-950/50 border-zinc-800 text-white"
              />
            )}
          </div>

          <div className="flex gap-4">
            <Button
              variant="ghost"
              onClick={() => setWizardStep(2)}
              data-testid="step-3-back-btn"
            >
              Back
            </Button>
            <Button
              onClick={handleNext}
              data-testid="step-3-next-btn"
              className="bg-emerald-500 hover:bg-emerald-400 text-black font-medium"
            >
              Next: Configure Prompts
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Step3MapColumns;

import { useState, useEffect } from 'react';
import { CheckCircle, Link as LinkIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import api from '@/utils/api';
import useStore from '@/store/useStore';

const Step1Connect = ({ onConnected }) => {
  const { user, setWizardStep } = useStore();
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkConnection();
  }, []);

  const checkConnection = async () => {
    try {
      const response = await api.get('/oauth/google/status');
      setConnected(response.data.connected);
      onConnected(response.data.connected);
    } catch (error) {
      console.error('Failed to check connection');
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async () => {
    try {
      const response = await api.get(`/oauth/google/start?user_id=${user.id}`);
      window.location.href = response.data.auth_url;
    } catch (error) {
      toast.error('Failed to start Google OAuth');
    }
  };

  const handleNext = () => {
    setWizardStep(2);
  };

  return (
    <div data-testid="step-1-connect">
      <h2 className="text-3xl font-outfit font-semibold mb-4">Connect Google Sheets</h2>
      <p className="text-zinc-400 mb-8">
        We need access to your Google Sheets to read leads and write results.
      </p>

      {loading ? (
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-emerald-500"></div>
        </div>
      ) : connected ? (
        <div className="space-y-6">
          <div className="flex items-center gap-3 p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-lg" data-testid="connected-status">
            <CheckCircle className="w-5 h-5 text-emerald-400" />
            <div>
              <p className="text-sm font-medium text-emerald-400">Connected to Google</p>
              <p className="text-xs text-zinc-500">You're all set to access your sheets</p>
            </div>
          </div>
          <Button
            onClick={handleNext}
            data-testid="step-1-next-btn"
            className="bg-emerald-500 hover:bg-emerald-400 text-black font-medium"
          >
            Next: Select Sheet
          </Button>
        </div>
      ) : (
        <Button
          onClick={handleConnect}
          data-testid="connect-google-btn"
          className="bg-emerald-500 hover:bg-emerald-400 text-black font-medium"
        >
          <LinkIcon className="w-4 h-4 mr-2" />
          Connect Google Sheets
        </Button>
      )}
    </div>
  );
};

export default Step1Connect;

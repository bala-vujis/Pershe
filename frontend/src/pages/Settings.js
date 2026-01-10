import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ChevronLeft, Key, Trash2, Link as LinkIcon, Unlink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import api from '@/utils/api';

const Settings = () => {
  const navigate = useNavigate();
  const [apiKeys, setApiKeys] = useState([]);
  const [googleConnected, setGoogleConnected] = useState(false);
  const [newKeyValue, setNewKeyValue] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const [keysRes, googleRes] = await Promise.all([
        api.get('/settings/api-keys'),
        api.get('/oauth/google/status')
      ]);
      setApiKeys(keysRes.data.keys || []);
      setGoogleConnected(googleRes.data.connected);
    } catch (error) {
      toast.error('Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveApiKey = async () => {
    if (!newKeyValue.trim()) {
      toast.error('Please enter an API key');
      return;
    }

    try {
      await api.post('/settings/api-keys', {
        provider: 'openai',
        key: newKeyValue,
        nickname: 'OpenAI Key'
      });
      toast.success('API key saved successfully');
      setNewKeyValue('');
      fetchSettings();
    } catch (error) {
      toast.error('Failed to save API key');
    }
  };

  const handleDeleteApiKey = async (keyId) => {
    try {
      await api.delete(`/settings/api-keys/${keyId}`);
      toast.success('API key deleted');
      fetchSettings();
    } catch (error) {
      toast.error('Failed to delete API key');
    }
  };

  const handleConnectGoogle = async () => {
    try {
      const user = JSON.parse(localStorage.getItem('user'));
      const response = await api.get(`/oauth/google/start?user_id=${user.id}`);
      window.location.href = response.data.auth_url;
    } catch (error) {
      toast.error('Failed to start Google OAuth');
    }
  };

  const handleDisconnectGoogle = async () => {
    try {
      await api.delete('/oauth/google/disconnect');
      toast.success('Google account disconnected');
      setGoogleConnected(false);
    } catch (error) {
      toast.error('Failed to disconnect');
    }
  };

  return (
    <div className="min-h-screen bg-black">
      <div className="max-w-4xl mx-auto px-6 py-8">
        <Button
          variant="ghost"
          onClick={() => navigate('/dashboard')}
          className="mb-6"
          data-testid="back-to-dashboard-btn"
        >
          <ChevronLeft className="w-4 h-4 mr-2" /> Back to Dashboard
        </Button>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h1 className="text-4xl font-outfit font-semibold mb-2">Settings</h1>
          <p className="text-zinc-400 mb-8">Manage your integrations and API keys</p>

          {loading ? (
            <div className="flex justify-center py-20">
              <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-emerald-500"></div>
            </div>
          ) : (
            <div className="space-y-8">
              <section className="bg-zinc-900/40 border border-white/10 rounded-2xl p-6">
                <h2 className="text-2xl font-outfit font-medium mb-4 flex items-center gap-2">
                  <LinkIcon className="w-5 h-5 text-emerald-400" />
                  Google Sheets Connection
                </h2>
                <p className="text-sm text-zinc-400 mb-6">
                  {googleConnected
                    ? 'Your Google account is connected. You can access your spreadsheets.'
                    : 'Connect your Google account to access spreadsheets.'}
                </p>
                {googleConnected ? (
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2 px-4 py-2 bg-emerald-500/10 border border-emerald-500/30 rounded-lg" data-testid="google-connected-status">
                      <LinkIcon className="w-4 h-4 text-emerald-400" />
                      <span className="text-sm text-emerald-400 font-medium">Connected</span>
                    </div>
                    <Button
                      variant="ghost"
                      onClick={handleDisconnectGoogle}
                      data-testid="disconnect-google-btn"
                      className="text-red-400 hover:text-red-300"
                    >
                      <Unlink className="w-4 h-4 mr-2" /> Disconnect
                    </Button>
                  </div>
                ) : (
                  <Button
                    onClick={handleConnectGoogle}
                    data-testid="connect-google-btn"
                    className="bg-emerald-500 hover:bg-emerald-400 text-black font-medium"
                  >
                    <LinkIcon className="w-4 h-4 mr-2" /> Connect Google
                  </Button>
                )}
              </section>

              <section className="bg-zinc-900/40 border border-white/10 rounded-2xl p-6">
                <h2 className="text-2xl font-outfit font-medium mb-4 flex items-center gap-2">
                  <Key className="w-5 h-5 text-emerald-400" />
                  OpenAI API Key
                </h2>
                <p className="text-sm text-zinc-400 mb-6">
                  Add your OpenAI API key to use GPT models for generating summaries and icebreakers.
                </p>

                {apiKeys.length > 0 ? (
                  <div className="space-y-4">
                    {apiKeys.map((key) => (
                      <div
                        key={key.id}
                        className="flex items-center justify-between p-4 bg-zinc-950/50 border border-zinc-800 rounded-lg"
                        data-testid={`api-key-${key.id}`}
                      >
                        <div>
                          <p className="text-sm font-medium">{key.nickname}</p>
                          <p className="text-xs text-zinc-500">Added {new Date(key.created_at).toLocaleDateString()}</p>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteApiKey(key.id)}
                          data-testid={`delete-key-btn-${key.id}`}
                          className="text-red-400 hover:text-red-300"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    ))}
                    <div className="pt-4 border-t border-white/10">
                      <Label className="text-sm text-zinc-300 mb-2 block">Replace with new key</Label>
                      <div className="flex gap-3">
                        <Input
                          type="password"
                          placeholder="sk-..."
                          value={newKeyValue}
                          onChange={(e) => setNewKeyValue(e.target.value)}
                          data-testid="new-api-key-input"
                          className="bg-zinc-950/50 border-zinc-800 text-white"
                        />
                        <Button
                          onClick={handleSaveApiKey}
                          data-testid="save-api-key-btn"
                          className="bg-emerald-500 hover:bg-emerald-400 text-black font-medium"
                        >
                          Save
                        </Button>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div>
                    <Label className="text-sm text-zinc-300 mb-2 block">API Key</Label>
                    <div className="flex gap-3">
                      <Input
                        type="password"
                        placeholder="sk-..."
                        value={newKeyValue}
                        onChange={(e) => setNewKeyValue(e.target.value)}
                        data-testid="new-api-key-input"
                        className="bg-zinc-950/50 border-zinc-800 text-white"
                      />
                      <Button
                        onClick={handleSaveApiKey}
                        data-testid="save-api-key-btn"
                        className="bg-emerald-500 hover:bg-emerald-400 text-black font-medium"
                      >
                        Save
                      </Button>
                    </div>
                    <p className="text-xs text-zinc-500 mt-2">
                      Get your API key from{' '}
                      <a
                        href="https://platform.openai.com/api-keys"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-emerald-400 hover:underline"
                      >
                        OpenAI Dashboard
                      </a>
                    </p>
                  </div>
                )}
              </section>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
};

export default Settings;

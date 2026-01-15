import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ChevronLeft, RefreshCw, Download, CheckCircle, XCircle, Loader, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import api from '@/utils/api';

const RunDetail = () => {
  const { runId } = useParams();
  const navigate = useNavigate();
  const [run, setRun] = useState(null);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pollingInterval, setPollingInterval] = useState(null);

  useEffect(() => {
    fetchRun();
    const interval = setInterval(fetchRun, 3000); // Poll every 3 seconds
    setPollingInterval(interval);
    return () => clearInterval(interval);
  }, [runId]);

  const fetchRun = async () => {
    try {
      const response = await api.get(`/runs/${runId}`);
      setRun(response.data.run);
      setItems(response.data.items || []);
      
      // Stop polling if run is completed or failed
      if (response.data.run.status === 'completed' || response.data.run.status === 'failed') {
        if (pollingInterval) clearInterval(pollingInterval);
      }
    } catch (error) {
      toast.error('Failed to fetch run details');
    } finally {
      setLoading(false);
    }
  };

  const handleRetryFailed = async () => {
    try {
      await api.post(`/runs/${runId}/retry`);
      toast.success('Retrying failed rows...');
      fetchRun();
    } catch (error) {
      toast.error('Failed to retry');
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="w-4 h-4 text-emerald-400" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-400" />;
      case 'processing':
        return <Loader className="w-4 h-4 text-blue-400 animate-spin" />;
      default:
        return <AlertCircle className="w-4 h-4 text-zinc-500" />;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-emerald-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black">
      <div className="max-w-7xl mx-auto px-6 py-8">
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
          <div className="flex justify-between items-start mb-8">
            <div>
              <h1 className="text-4xl font-outfit font-semibold mb-2">Run Details</h1>
              <p className="text-zinc-400">Track progress and view results</p>
            </div>
            <div className="flex gap-3">
              {run?.status === 'completed' && run?.failed_rows > 0 && (
                <Button
                  onClick={handleRetryFailed}
                  data-testid="retry-failed-btn"
                  variant="secondary"
                >
                  <RefreshCw className="w-4 h-4 mr-2" /> Retry Failed
                </Button>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-zinc-900/40 border border-white/10 rounded-xl p-6" data-testid="status-card">
              <p className="text-sm text-zinc-500 mb-1">Status</p>
              <p className="text-2xl font-outfit font-semibold capitalize">
                <span className={`${
                  run?.status === 'completed' ? 'text-emerald-400' :
                  run?.status === 'running' ? 'text-blue-400' :
                  run?.status === 'failed' ? 'text-red-400' :
                  'text-zinc-400'
                }`}>
                  {run?.status}
                </span>
              </p>
            </div>

            <div className="bg-zinc-900/40 border border-white/10 rounded-xl p-6" data-testid="total-rows-card">
              <p className="text-sm text-zinc-500 mb-1">Total Rows</p>
              <p className="text-2xl font-outfit font-semibold">{run?.total_rows || 0}</p>
            </div>

            <div className="bg-zinc-900/40 border border-white/10 rounded-xl p-6" data-testid="success-rows-card">
              <p className="text-sm text-zinc-500 mb-1">Success</p>
              <p className="text-2xl font-outfit font-semibold text-emerald-400">{run?.success_rows || 0}</p>
            </div>

            <div className="bg-zinc-900/40 border border-white/10 rounded-xl p-6" data-testid="failed-rows-card">
              <p className="text-sm text-zinc-500 mb-1">Failed</p>
              <p className="text-2xl font-outfit font-semibold text-red-400">{run?.failed_rows || 0}</p>
            </div>
          </div>

          {run?.status === 'running' && (
            <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-6 mb-8">
              <div className="flex items-center gap-3">
                <Loader className="w-5 h-5 text-blue-400 animate-spin" />
                <div>
                  <p className="text-sm font-medium text-blue-400">Processing in progress...</p>
                  <p className="text-xs text-zinc-500">This may take a few minutes depending on the number of rows.</p>
                </div>
              </div>
            </div>
          )}
          {run?.status === 'failed' && run?.error_message && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-6 mb-8">
              <div className="flex items-center gap-3">
                <AlertCircle className="w-5 h-5 text-red-400" />
                <div>
                  <p className="text-sm font-medium text-red-400">Run Failed</p>
                  <p className="text-xs text-zinc-400">{run.error_message}</p>
                </div>
              </div>
            </div>
          )}

          <div className="bg-zinc-900/20 border border-white/5 rounded-xl overflow-hidden">
            <div className="p-6 border-b border-white/5">
              <h2 className="text-xl font-outfit font-medium">Row Results</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-zinc-900/50 border-b border-white/5">
                  <tr>
                    <th className="text-left p-4 text-xs font-medium text-zinc-400 uppercase tracking-wider">Row</th>
                    <th className="text-left p-4 text-xs font-medium text-zinc-400 uppercase tracking-wider">Company</th>
                    <th className="text-left p-4 text-xs font-medium text-zinc-400 uppercase tracking-wider">Website</th>
                    <th className="text-left p-4 text-xs font-medium text-zinc-400 uppercase tracking-wider">Status</th>
                    <th className="text-left p-4 text-xs font-medium text-zinc-400 uppercase tracking-wider">Icebreaker</th>
                    <th className="text-left p-4 text-xs font-medium text-zinc-400 uppercase tracking-wider">Error</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr key={item.id} className="border-b border-white/5 hover:bg-white/[0.02]" data-testid={`item-row-${item.id}`}>
                      <td className="p-4 text-sm text-zinc-300">{item.row_index}</td>
                      <td className="p-4 text-sm text-zinc-300">{item.input_data?.Company || item.input_data?.company_name || 'N/A'}</td>
                      <td className="p-4 text-sm text-zinc-500 truncate max-w-xs">{item.website_url || 'N/A'}</td>
                      <td className="p-4">
                        <div className="flex items-center gap-2">
                          {getStatusIcon(item.status)}
                          <span className="text-sm capitalize">{item.status}</span>
                        </div>
                      </td>
                      <td className="p-4 text-sm text-zinc-300 max-w-md truncate">
                        {item.output_icebreaker || '-'}
                      </td>
                      <td className="p-4 text-sm text-red-400 max-w-xs truncate">
                        {item.error_message || '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default RunDetail;

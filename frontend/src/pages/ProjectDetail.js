import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ChevronLeft, Play, Settings, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import api from '@/utils/api';

const ProjectDetail = () => {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProjectDetails();
  }, [projectId]);

  const fetchProjectDetails = async () => {
    try {
      const [projectRes, runsRes] = await Promise.all([
        api.get(`/projects/${projectId}`),
        api.get(`/runs?project_id=${projectId}`)
      ]);
      setProject(projectRes.data.project);
      setRuns(runsRes.data.runs || []);
    } catch (error) {
      toast.error('Failed to load project details');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-emerald-500"></div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center">
          <p className="text-zinc-400 mb-4">Project not found</p>
          <Button onClick={() => navigate('/dashboard')}>Back to Dashboard</Button>
        </div>
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
              <h1 className="text-4xl font-outfit font-semibold mb-2">{project.name}</h1>
              <p className="text-zinc-400">{project.spreadsheet_id} • {project.sheet_name}</p>
            </div>
            <div className="flex gap-3">
              <Button
                onClick={() => {
                  toast.info('Edit functionality coming soon');
                }}
                variant="secondary"
                data-testid="edit-project-btn"
              >
                <Settings className="w-4 h-4 mr-2" /> Settings
              </Button>
            </div>
          </div>

          <section>
            <h2 className="text-2xl font-outfit font-medium mb-4">Runs</h2>
            {runs.length === 0 ? (
              <div className="bg-zinc-900/20 border border-white/5 rounded-xl p-12 text-center" data-testid="empty-runs">
                <Play className="w-12 h-12 text-zinc-600 mx-auto mb-4" />
                <p className="text-zinc-400 mb-4">No runs yet for this project</p>
                <p className="text-sm text-zinc-500">This project was created but no runs have been started.</p>
              </div>
            ) : (
              <div className="bg-zinc-900/20 border border-white/5 rounded-xl overflow-hidden">
                <table className="w-full">
                  <thead className="bg-zinc-900/50 border-b border-white/5">
                    <tr>
                      <th className="text-left p-4 text-xs font-medium text-zinc-400 uppercase tracking-wider">Status</th>
                      <th className="text-left p-4 text-xs font-medium text-zinc-400 uppercase tracking-wider">Mode</th>
                      <th className="text-left p-4 text-xs font-medium text-zinc-400 uppercase tracking-wider">Progress</th>
                      <th className="text-left p-4 text-xs font-medium text-zinc-400 uppercase tracking-wider">Created</th>
                      <th className="text-left p-4 text-xs font-medium text-zinc-400 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {runs.map((run) => (
                      <tr key={run.id} className="border-b border-white/5 hover:bg-white/[0.02]" data-testid={`run-row-${run.id}`}>
                        <td className="p-4">
                          <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${
                            run.status === 'completed' ? 'bg-emerald-500/10 text-emerald-400' :
                            run.status === 'running' ? 'bg-blue-500/10 text-blue-400' :
                            run.status === 'failed' ? 'bg-red-500/10 text-red-400' :
                            'bg-zinc-500/10 text-zinc-400'
                          }`}>
                            {run.status}
                          </span>
                        </td>
                        <td className="p-4 text-sm text-zinc-300 capitalize">{run.mode}</td>
                        <td className="p-4 text-sm text-zinc-300">
                          {run.success_rows}/{run.total_rows} success
                        </td>
                        <td className="p-4 text-sm text-zinc-500">
                          {new Date(run.created_at).toLocaleDateString()}
                        </td>
                        <td className="p-4">
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => navigate(`/runs/${run.id}`)}
                            data-testid={`view-run-btn-${run.id}`}
                          >
                            View
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </motion.div>
      </div>
    </div>
  );
};

export default ProjectDetail;
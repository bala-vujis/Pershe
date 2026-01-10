import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Plus, Sparkles, Settings, LogOut, Coins, FileSpreadsheet, Play } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import api from '@/utils/api';
import useStore from '@/store/useStore';

const Dashboard = () => {
  const { user, logout } = useStore();
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [runs, setRuns] = useState([]);
  const [credits, setCredits] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [projectsRes, runsRes, creditsRes] = await Promise.all([
        api.get('/projects'),
        api.get('/runs'),
        api.get('/credits/balance')
      ]);
      setProjects(projectsRes.data.projects || []);
      setRuns(runsRes.data.runs || []);
      setCredits(creditsRes.data.balance || 0);
    } catch (error) {
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-black">
      <nav className="border-b border-white/10 px-6 py-4">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-emerald-500 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-black" />
            </div>
            <span className="font-outfit font-semibold text-xl">Sheet Personalizer</span>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-4 py-2 bg-zinc-900/60 border border-white/10 rounded-lg" data-testid="credits-display">
              <Coins className="w-4 h-4 text-emerald-400" />
              <span className="text-sm font-medium">{credits} credits</span>
            </div>
            <Button variant="ghost" size="sm" onClick={() => navigate('/settings')} data-testid="nav-settings-btn">
              <Settings className="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="sm" onClick={handleLogout} data-testid="nav-logout-btn">
              <LogOut className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="flex justify-between items-center mb-8">
            <div>
              <h1 className="text-4xl font-outfit font-semibold mb-2">Welcome back, {user?.name}</h1>
              <p className="text-zinc-400">Manage your lead personalization projects</p>
            </div>
            <Link to="/projects/new">
              <Button data-testid="new-project-btn" className="bg-emerald-500 hover:bg-emerald-400 text-black font-medium shadow-[0_0_20px_-5px_rgba(16,185,129,0.5)]">
                <Plus className="w-4 h-4 mr-2" /> New Project
              </Button>
            </Link>
          </div>

          {loading ? (
            <div className="flex justify-center py-20">
              <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-emerald-500"></div>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-8">
              <section>
                <h2 className="text-2xl font-outfit font-medium mb-4">Your Projects</h2>
                {projects.length === 0 ? (
                  <div className="bg-zinc-900/20 border border-white/5 rounded-xl p-12 text-center" data-testid="empty-projects">
                    <FileSpreadsheet className="w-12 h-12 text-zinc-600 mx-auto mb-4" />
                    <p className="text-zinc-400 mb-4">No projects yet</p>
                    <Link to="/projects/new">
                      <Button data-testid="create-first-project-btn" className="bg-emerald-500 hover:bg-emerald-400 text-black font-medium">
                        Create Your First Project
                      </Button>
                    </Link>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {projects.map((project) => (
                      <div
                        key={project.id}
                        className="bg-zinc-900/20 border border-white/5 rounded-xl p-6 hover:border-white/10 hover:bg-zinc-900/30 transition-all cursor-pointer"
                        onClick={() => navigate(`/projects/${project.id}`)}
                        data-testid={`project-card-${project.id}`}
                      >
                        <h3 className="text-lg font-outfit font-medium mb-2">{project.name}</h3>
                        <p className="text-sm text-zinc-500 mb-4">{project.sheet_name}</p>
                        <div className="text-xs text-zinc-600">
                          Created {new Date(project.created_at).toLocaleDateString()}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </section>

              <section>
                <h2 className="text-2xl font-outfit font-medium mb-4">Recent Runs</h2>
                {runs.length === 0 ? (
                  <div className="bg-zinc-900/20 border border-white/5 rounded-xl p-12 text-center" data-testid="empty-runs">
                    <Play className="w-12 h-12 text-zinc-600 mx-auto mb-4" />
                    <p className="text-zinc-400">No runs yet. Create a project to get started!</p>
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
                        {runs.slice(0, 10).map((run) => (
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
                                onClick={(e) => {
                                  e.stopPropagation();
                                  navigate(`/runs/${run.id}`);
                                }}
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
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
};

export default Dashboard;

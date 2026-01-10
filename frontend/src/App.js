import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'sonner';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Dashboard from './pages/Dashboard';
import NewProject from './pages/NewProject';
import ProjectDetail from './pages/ProjectDetail';
import RunDetail from './pages/RunDetail';
import Settings from './pages/Settings';
import useStore from './store/useStore';
import './App.css';

function PrivateRoute({ children }) {
  const { token } = useStore();
  return token ? children : <Navigate to="/login" />;
}

function App() {
  return (
    <div className="min-h-screen bg-black text-white">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route
            path="/dashboard"
            element={
              <PrivateRoute>
                <Dashboard />
              </PrivateRoute>
            }
          />
          <Route
            path="/projects/new"
            element={
              <PrivateRoute>
                <NewProject />
              </PrivateRoute>
            }
          />
          <Route
            path="/projects/:projectId"
            element={
              <PrivateRoute>
                <ProjectDetail />
              </PrivateRoute>
            }
          />
          <Route
            path="/runs/:runId"
            element={
              <PrivateRoute>
                <RunDetail />
              </PrivateRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <PrivateRoute>
                <Settings />
              </PrivateRoute>
            }
          />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" theme="dark" />
    </div>
  );
}

export default App;

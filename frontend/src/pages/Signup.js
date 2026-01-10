import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { motion } from 'framer-motion';
import { Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import api from '@/utils/api';
import useStore from '@/store/useStore';

const Signup = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { setAuth } = useStore();

  const handleSignup = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await api.post('/auth/signup', { name, email, password });
      const { access_token, user } = response.data;
      setAuth(user, access_token);
      toast.success('Account created! You have 50 free credits.');
      navigate('/dashboard');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Signup failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black flex items-center justify-center px-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="w-full max-w-md"
      >
        <Link to="/" className="flex items-center justify-center gap-2 mb-8">
          <div className="w-10 h-10 rounded-lg bg-emerald-500 flex items-center justify-center">
            <Sparkles className="w-6 h-6 text-black" />
          </div>
          <span className="font-outfit font-semibold text-2xl">Sheet Personalizer</span>
        </Link>

        <div className="bg-zinc-900/40 border border-white/10 rounded-2xl p-8 backdrop-blur-xl">
          <h2 className="text-3xl font-outfit font-semibold mb-2">Get Started Free</h2>
          <p className="text-zinc-400 mb-6">50 free credits • No credit card required</p>

          <form onSubmit={handleSignup} className="space-y-4">
            <div>
              <Label htmlFor="name" className="text-sm text-zinc-300 mb-2 block">Full Name</Label>
              <Input
                id="name"
                type="text"
                data-testid="signup-name-input"
                placeholder="John Doe"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="bg-zinc-950/50 border-zinc-800 focus:border-emerald-500/50 focus:ring-2 focus:ring-emerald-500/20 text-white"
              />
            </div>
            <div>
              <Label htmlFor="email" className="text-sm text-zinc-300 mb-2 block">Email</Label>
              <Input
                id="email"
                type="email"
                data-testid="signup-email-input"
                placeholder="you@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="bg-zinc-950/50 border-zinc-800 focus:border-emerald-500/50 focus:ring-2 focus:ring-emerald-500/20 text-white"
              />
            </div>
            <div>
              <Label htmlFor="password" className="text-sm text-zinc-300 mb-2 block">Password</Label>
              <Input
                id="password"
                type="password"
                data-testid="signup-password-input"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
                className="bg-zinc-950/50 border-zinc-800 focus:border-emerald-500/50 focus:ring-2 focus:ring-emerald-500/20 text-white"
              />
            </div>
            <Button
              type="submit"
              data-testid="signup-submit-btn"
              disabled={loading}
              className="w-full bg-emerald-500 hover:bg-emerald-400 text-black font-medium h-11 shadow-[0_0_20px_-5px_rgba(16,185,129,0.5)]"
            >
              {loading ? 'Creating account...' : 'Create Account'}
            </Button>
          </form>

          <p className="text-center text-sm text-zinc-500 mt-6">
            Already have an account?{' '}
            <Link to="/login" className="text-emerald-400 hover:text-emerald-300">
              Log in
            </Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
};

export default Signup;

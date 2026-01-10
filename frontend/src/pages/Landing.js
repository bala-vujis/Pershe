import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Sparkles, Zap, Shield, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';

const Landing = () => {
  return (
    <div className="min-h-screen bg-black relative overflow-hidden">
      <div className="hero-glow absolute inset-0 pointer-events-none" />
      
      <div className="relative z-10">
        <nav className="px-6 py-6 flex justify-between items-center max-w-7xl mx-auto">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-emerald-500 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-black" />
            </div>
            <span className="font-outfit font-semibold text-xl">Sheet Personalizer</span>
          </div>
          <div className="flex gap-4">
            <Link to="/login">
              <Button variant="ghost" data-testid="nav-login-btn">Login</Button>
            </Link>
            <Link to="/signup">
              <Button data-testid="nav-signup-btn" className="bg-emerald-500 hover:bg-emerald-400 text-black font-medium shadow-[0_0_20px_-5px_rgba(16,185,129,0.5)]">
                Get Started
              </Button>
            </Link>
          </div>
        </nav>

        <section className="px-6 py-20 md:py-32 max-w-5xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h1 className="text-5xl md:text-6xl font-outfit font-semibold tracking-tight mb-6">
              Turn Cold Leads Into
              <span className="block mt-2 bg-gradient-to-r from-emerald-400 to-emerald-600 bg-clip-text text-transparent">
                Warm Conversations
              </span>
            </h1>
            <p className="text-lg md:text-xl text-zinc-400 mb-8 max-w-2xl mx-auto leading-relaxed">
              Scrape company websites, generate AI-powered summaries, and create personalized icebreakers—all in your Google Sheet.
            </p>
            <div className="flex gap-4 justify-center">
              <Link to="/signup">
                <Button size="lg" data-testid="hero-get-started-btn" className="bg-emerald-500 hover:bg-emerald-400 text-black font-medium px-8 h-12 shadow-[0_0_25px_-5px_rgba(16,185,129,0.7)]">
                  Start Free Trial <ArrowRight className="ml-2 w-4 h-4" />
                </Button>
              </Link>
            </div>
            <p className="text-sm text-zinc-500 mt-4">50 free credits • No credit card required</p>
          </motion.div>
        </section>

        <section className="px-6 py-20 max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="grid grid-cols-1 md:grid-cols-3 gap-6"
          >
            <div className="bg-zinc-900/40 border border-white/10 rounded-2xl p-8 hover:bg-zinc-900/60 hover:border-emerald-500/30 transition-all duration-300" data-testid="feature-card-smart-scraping">
              <div className="w-12 h-12 rounded-lg bg-emerald-500/10 flex items-center justify-center mb-4">
                <Zap className="w-6 h-6 text-emerald-400" />
              </div>
              <h3 className="text-2xl font-outfit font-medium mb-3">Smart Scraping</h3>
              <p className="text-zinc-400 leading-relaxed">
                Automatically identifies and scrapes the most relevant pages from company websites using intelligent scoring.
              </p>
            </div>

            <div className="bg-zinc-900/40 border border-white/10 rounded-2xl p-8 hover:bg-zinc-900/60 hover:border-emerald-500/30 transition-all duration-300" data-testid="feature-card-ai-summaries">
              <div className="w-12 h-12 rounded-lg bg-emerald-500/10 flex items-center justify-center mb-4">
                <Sparkles className="w-6 h-6 text-emerald-400" />
              </div>
              <h3 className="text-2xl font-outfit font-medium mb-3">AI Summaries</h3>
              <p className="text-zinc-400 leading-relaxed">
                Extract ICP-relevant facts with preset prompts for Logistics, Industrial, or your custom business model.
              </p>
            </div>

            <div className="bg-zinc-900/40 border border-white/10 rounded-2xl p-8 hover:bg-zinc-900/60 hover:border-emerald-500/30 transition-all duration-300" data-testid="feature-card-personalized">
              <div className="w-12 h-12 rounded-lg bg-emerald-500/10 flex items-center justify-center mb-4">
                <Shield className="w-6 h-6 text-emerald-400" />
              </div>
              <h3 className="text-2xl font-outfit font-medium mb-3">Personalized at Scale</h3>
              <p className="text-zinc-400 leading-relaxed">
                Generate unique, believable icebreakers for each lead. Preview on 3 rows before processing hundreds.
              </p>
            </div>
          </motion.div>
        </section>

        <section className="px-6 py-20 text-center max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-4xl md:text-5xl font-outfit font-semibold mb-6">Ready to 10x Your Outreach?</h2>
            <p className="text-lg text-zinc-400 mb-8">
              Join sales teams using Sheet Personalizer to turn spreadsheets into revenue engines.
            </p>
            <Link to="/signup">
              <Button size="lg" data-testid="cta-start-now-btn" className="bg-emerald-500 hover:bg-emerald-400 text-black font-medium px-8 h-12 shadow-[0_0_25px_-5px_rgba(16,185,129,0.7)]">
                Start Now for Free
              </Button>
            </Link>
          </motion.div>
        </section>

        <footer className="border-t border-white/10 py-8 px-6 text-center text-sm text-zinc-500">
          <p>© 2025 Sheet Personalizer. Built for B2B sales teams.</p>
        </footer>
      </div>
    </div>
  );
};

export default Landing;

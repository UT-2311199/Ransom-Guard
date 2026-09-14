import React, { useState } from 'react';
import { useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Sidebar } from './Sidebar';
import { Navbar } from './Navbar';
import { ParticleBackground } from '../components/AnimatedBackground';
import { SystemHealthBar } from '../components/SystemHealthBar';

const PAGE_TITLES: Record<string, { title: string; subtitle: string }> = {
  '/': { title: 'Dashboard', subtitle: 'Real-time system security overview' },
  '/monitoring': { title: 'Live File Activity', subtitle: 'Real-time file system monitoring' },
  '/process-monitor': { title: 'Process Monitor', subtitle: 'Active process surveillance and management' },
  '/threat-detection': { title: 'Threat Detection', subtitle: 'ML-powered ransomware analysis' },
  '/threat-history': { title: 'Threat History', subtitle: 'Historical security incidents timeline' },
  '/analytics': { title: 'Analytics', subtitle: 'Security metrics and trend analysis' },
  '/reports': { title: 'Reports', subtitle: 'Generate and export security reports' },
  '/settings': { title: 'Settings', subtitle: 'System configuration and preferences' },
};

interface MainLayoutProps {
  children: React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();
  const sidebarWidth = collapsed ? 72 : 256;
  const pageInfo = PAGE_TITLES[location.pathname] || { title: 'RansomGuard', subtitle: '' };

  return (
    <div className="min-h-screen bg-slate-950 cyber-grid">
      <ParticleBackground />
      <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />
      <Navbar
        sidebarWidth={sidebarWidth}
        pageTitle={pageInfo.title}
        pageSubtitle={pageInfo.subtitle}
      />
      <motion.main
        className="min-h-screen pt-16 relative z-10"
        animate={{ paddingLeft: sidebarWidth }}
        transition={{ duration: 0.3, ease: 'easeInOut' }}
      >
        <motion.div
          key={location.pathname}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
          className="p-6 pb-16"
        >
          {children}
        </motion.div>
      </motion.main>
      <SystemHealthBar />
    </div>
  );
};

import React from 'react';
import { useAuth } from '../context/AuthContext';
import { CustomerDashboard } from './CustomerDashboard';
import { AgentDashboard } from './AgentDashboard';
import { AuthorityWorkbench } from './AuthorityWorkbench';

export const DashboardContainer: React.FC = () => {
  const { role } = useAuth();

  switch (role) {
    case 'INSURANCE_AGENT':
      return <AgentDashboard />;
    case 'APPROVAL_AUTHORITY':
      return <AuthorityWorkbench />;
    case 'CUSTOMER':
    default:
      return <CustomerDashboard />;
  }
};

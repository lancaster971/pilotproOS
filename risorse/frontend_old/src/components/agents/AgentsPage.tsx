/**
 * AI Agents Transparency Page
 * 
 * KILLER FEATURE: Mostra cosa stanno facendo gli AI agents in real-time
 * - Feed attività agents con business context
 * - Drill-down su ogni execution
 * - Quick actions per CRM/sistemi esterni
 */

import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Bot, Clock, CheckCircle, XCircle, ExternalLink, Mail, Eye, Zap, Settings, Send } from 'lucide-react';
import { tenantAPI } from '../../services/api';
import AgentDetailModal from './AgentDetailModal';

// Tipi per nuovo approccio basato su WORKFLOW
interface AgentWorkflow {
  id: string;
  name: string;
  status: 'active' | 'inactive';
  lastActivity: string | null;
  lastExecutionId: string | null;
  lastExecutionStatus: string;
  totalExecutions: number;
  hasDetailedData: boolean;
  updatedAt: string;
  type: 'ai-agent';
  preview?: {
    senderEmail?: string;
    subject?: string;
    classification?: string;
  };
}

const AgentsPage: React.FC = () => {
  const [selectedWorkflow, setSelectedWorkflow] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const tenantId = 'client_simulation_a'; // TODO: Get from auth context

  // Fetch AI agents workflows (NEW APPROACH)
  const { data: workflowsData, isLoading, error, refetch } = useQuery({
    queryKey: ['agents-workflows', tenantId],
    queryFn: async () => {
      const response = await fetch(`http://localhost:3001/api/tenant/${tenantId}/agents/workflows?limit=20`);
      if (!response.ok) throw new Error('Failed to fetch agents workflows');
      return response.json();
    },
    refetchInterval: 300000, // 🚀 POLLING SMART: Auto-refresh ogni 5 minuti per workflow activity
    staleTime: 0, // 🔥 SEMPRE FRESH: Nessuna cache stale
    refetchOnWindowFocus: true, // 👁️ REFRESH ON FOCUS: Quando torni alla pagina
  });

  const workflows: AgentWorkflow[] = workflowsData?.data || [];

  // Gestione apertura modal (ora per WORKFLOW non execution)
  const handleViewWorkflow = (workflowId: string) => {
    setSelectedWorkflow(workflowId);
    setIsModalOpen(true);
  };

  // Formattazione durata
  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}min`;
  };

  // Formattazione timestamp relativo
  const formatTimeAgo = (timestamp: string) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffMs = now.getTime() - time.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return `${Math.floor(diffMins / 1440)}d ago`;
  };

  // Icon per status
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success': return <CheckCircle className="w-5 h-5 text-green-400" />;
      case 'error': return <XCircle className="w-5 h-5 text-red-400" />;
      case 'running': return <Clock className="w-5 h-5 text-yellow-400 animate-spin" />;
      default: return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  // Color per workflow type
  const getWorkflowColor = (workflowName: string) => {
    if (workflowName.includes('CHATBOT')) return 'text-blue-400 bg-blue-400/10';
    if (workflowName.includes('AGENT')) return 'text-purple-400 bg-purple-400/10';
    if (workflowName.includes('AI')) return 'text-green-400 bg-green-400/10';
    return 'text-gray-400 bg-gray-400/10';
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-black p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-400"></div>
          <span className="ml-3 text-green-400">Loading AI Agents...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-black p-6">
        <div className="text-center text-red-400">
          <XCircle className="w-16 h-16 mx-auto mb-4" />
          <p>Failed to load AI Agents activity</p>
          <button 
            onClick={() => refetch()} 
            className="mt-4 px-4 py-2 bg-green-400 text-black rounded hover:bg-green-300 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <Bot className="w-8 h-8 text-green-400 mr-3" />
            <div>
              <h1 className="text-2xl font-bold text-white">AI Agents</h1>
              <p className="text-gray-400">Real-time transparency on your AI agents activity</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center text-sm text-gray-400">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse mr-2"></div>
              Live Feed
            </div>
            <button
              onClick={() => refetch()}
              className="px-4 py-2 bg-green-400 text-black rounded hover:bg-green-300 transition-colors"
            >
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Stats Cards - Workflow-based */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-gray-900 border border-green-400/20 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Active Agents</p>
              <p className="text-2xl font-bold text-white">{workflows.length}</p>
            </div>
            <Bot className="w-8 h-8 text-green-400" />
          </div>
        </div>
        
        <div className="bg-gray-900 border border-green-400/20 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">With Data</p>
              <p className="text-2xl font-bold text-green-400">
                {workflows.filter(w => w.hasDetailedData).length}
              </p>
            </div>
            <CheckCircle className="w-8 h-8 text-green-400" />
          </div>
        </div>

        <div className="bg-gray-900 border border-green-400/20 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Total Executions</p>
              <p className="text-2xl font-bold text-white">
                {workflows.reduce((sum, w) => sum + w.totalExecutions, 0)}
              </p>
            </div>
            <Clock className="w-8 h-8 text-yellow-400" />
          </div>
        </div>

        <div className="bg-gray-900 border border-green-400/20 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Recently Active</p>
              <p className="text-2xl font-bold text-white">
                {workflows.filter(w => w.lastActivity && new Date(w.lastActivity) > new Date(Date.now() - 24 * 60 * 60 * 1000)).length}
              </p>
            </div>
            <Bot className="w-8 h-8 text-blue-400" />
          </div>
        </div>
      </div>

      {/* Workflow Cards - NEW APPROACH */}
      <div className="bg-gray-900 border border-green-400/20 rounded-lg p-6">
        <h2 className="text-xl font-semibold text-white mb-6">AI Agent Workflows</h2>
        
        {workflows.length === 0 ? (
          <div className="text-center py-12">
            <Bot className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400">No AI agent workflows found</p>
            <p className="text-gray-500 text-sm mt-2">Active AI workflows will appear here</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {workflows.map((workflow) => (
              <div 
                key={workflow.id}
                className="bg-black border border-gray-800 rounded-lg p-5 hover:border-green-400/30 transition-all cursor-pointer"
                onClick={() => handleViewWorkflow(workflow.id)}
              >
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center mb-2">
                      <Bot className="w-5 h-5 text-green-400 mr-2" />
                      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${getWorkflowColor(workflow.name)}`}>
                        {workflow.name}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center">
                    {workflow.hasDetailedData ? (
                      <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" title="Has detailed execution data" />
                    ) : (
                      <div className="w-2 h-2 bg-gray-600 rounded-full" title="No execution data available" />
                    )}
                  </div>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <div className="text-gray-400 text-xs mb-1">Executions</div>
                    <div className="text-white text-lg font-semibold">{workflow.totalExecutions}</div>
                  </div>
                  <div>
                    <div className="text-gray-400 text-xs mb-1">Status</div>
                    <div className="flex items-center">
                      {workflow.lastExecutionStatus === 'success' && <CheckCircle className="w-4 h-4 text-green-400 mr-1" />}
                      {workflow.lastExecutionStatus === 'error' && <XCircle className="w-4 h-4 text-red-400 mr-1" />}
                      {!workflow.lastExecutionStatus && <Clock className="w-4 h-4 text-gray-400 mr-1" />}
                      <span className="text-white text-sm">{workflow.lastExecutionStatus || 'inactive'}</span>
                    </div>
                  </div>
                </div>

                {/* Business Context Preview */}
                {workflow.preview && (
                  <div className="mb-4 p-3 bg-gray-800/50 rounded border-l-2 border-green-400/50">
                    <div className="text-gray-400 text-xs mb-2">Latest Activity</div>
                    {workflow.preview.senderEmail && (
                      <div className="flex items-center mb-1">
                        <Mail className="w-3 h-3 text-blue-400 mr-2" />
                        <span className="text-blue-400 text-sm truncate">{workflow.preview.senderEmail}</span>
                      </div>
                    )}
                    {workflow.preview.subject && (
                      <div className="text-gray-300 text-sm truncate mb-1">"{workflow.preview.subject}"</div>
                    )}
                    {workflow.preview.classification && (
                      <div className="text-green-400 text-xs">{workflow.preview.classification}</div>
                    )}
                  </div>
                )}

                {/* Last Activity */}
                <div className="flex items-center justify-between text-xs text-gray-400">
                  <div>
                    {workflow.lastActivity ? formatTimeAgo(workflow.lastActivity) : 'No recent activity'}
                  </div>
                  <button className="text-green-400 hover:text-green-300 font-medium">
                    View Timeline →
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Workflow Timeline Modal */}
      {isModalOpen && selectedWorkflow && (
        <AgentDetailModal
          workflowId={selectedWorkflow}
          tenantId={tenantId}
          isOpen={isModalOpen}
          onClose={() => {
            setIsModalOpen(false);
            setSelectedWorkflow(null);
          }}
        />
      )}
    </div>
  );
};

export default AgentsPage;
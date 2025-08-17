/**
 * Agent Detail Modal
 * 
 * Modal per drill-down completo su execution AI agent
 * - Timeline step-by-step dell'agent
 * - Input/output di ogni nodo
 * - Business context dettagliato
 * - Raw execution data per debugging
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  X, CheckCircle, XCircle, Bot, Mail,
  ChevronDown, ChevronRight, Code, Database, Activity,
  AlertTriangle, Info, Settings, RefreshCw, Clock,
  GitBranch, Zap, Play, Pause, Copy, Download, ExternalLink,
  TrendingUp, Calendar, Server, Cpu, Link2, Box, Layers,
  BarChart3, MessageSquare, Send, FileText, Webhook, Brain,
  Cog, Globe, Package
} from 'lucide-react';
import { api, schedulerAPI, tenantAPI } from '../../services/api';
import { cn, formatDate } from '../../lib/utils';
import ReactApexChart from 'react-apexcharts';

// Tipi per execution details
interface AgentStep {
  nodeId: string;
  nodeName: string;
  type: 'input' | 'processing' | 'output' | 'error';
  startTime: string;
  duration: number;
  input: any;
  output: any;
  summary: string;
  details?: string;
  isVisible?: boolean; // Campo per filtro whitelist
}


interface AgentDetailModalProps {
  workflow?: any;
  workflowId?: string;
  tenantId?: string;
  isOpen?: boolean;
  onClose: () => void;
  isWorkflowMode?: boolean; // Nuovo: per distinguere tra modalità AI Agent e Workflow standard
}

const AgentDetailModal: React.FC<AgentDetailModalProps> = ({ 
  workflow,
  workflowId, 
  tenantId, 
  isOpen, 
  onClose,
  isWorkflowMode = false
}) => {
  // Compatibility per entrambi i formati
  const actualWorkflowId = workflowId || workflow?.id;
  const actualTenantId = tenantId || 'client_simulation_a';
  const actualIsOpen = isOpen !== undefined ? isOpen : !!workflow;
  const [activeTab, setActiveTab] = useState<'timeline' | 'context' | 'raw' | 'overview' | 'executions' | 'nodes' | 'performance' | 'activity'>(
    isWorkflowMode ? 'overview' : 'timeline'
  );
  const [expandedStep, setExpandedStep] = useState<string | null>(null);
  // Rimosso toggle - mostra sempre solo i nodi "show" per client view
  
  // React Query Client per invalidazione cache
  const queryClient = useQueryClient();

  // Utility per convertire dati JSON in descrizioni human-readable per EMAIL
  const humanizeStepData = (data: any, dataType: 'input' | 'output', nodeType?: string, nodeName?: string): string => {
    
    // LOGICA SPECIALE PER TRIGGER NODES
    const isTriggerNode = nodeType?.includes('trigger') || 
                         nodeType?.includes('Trigger') ||
                         nodeName?.toLowerCase().includes('ricezione') ||
                         nodeName?.toLowerCase().includes('trigger');
    
    // Per nodi trigger, l'input è sempre "In attesa di dati"
    if (isTriggerNode && dataType === 'input') {
      return 'In attesa di nuove email dal server Microsoft Outlook';
    }
    
    if (!data) return 'Nessun dato disponibile';

    // Se è un array, prendi il primo elemento
    const processData = Array.isArray(data) ? data[0] : data;
    
    if (!processData || typeof processData !== 'object') {
      return String(processData) || 'Dato non strutturato';
    }

    const dataString = JSON.stringify(processData);
    const insights: string[] = [];
    
    // PRIORITÀ 1: CONTENUTO EMAIL (corpo del messaggio)
    const emailBodyFields = [
      processData.json?.messaggio_cliente,
      processData.json?.messaggio,
      processData.json?.body?.content,
      processData.json?.body,
      processData.json?.content,
      processData.json?.text,
      processData.json?.message,
      processData.body?.content,
      processData.content
    ];
    
    const emailBody = emailBodyFields.find(field => 
      field && typeof field === 'string' && field.length > 20
    );
    
    if (emailBody) {
      // Pulisci il contenuto HTML/formato e mostra preview
      const cleanContent = emailBody
        .replace(/<[^>]+>/g, ' ')  // Rimuovi HTML
        .replace(/&[a-zA-Z0-9]+;/g, ' ')  // Rimuovi entità HTML
        .replace(/\s+/g, ' ')  // Normalizza spazi
        .trim();
        
      const preview = cleanContent.substring(0, 200);
      insights.push(`Contenuto email: "${preview}${preview.length >= 200 ? '...' : ''}"`);
    }

    // PRIORITÀ 2: SUBJECT/OGGETTO
    if (processData.json?.oggetto) {
      insights.push(`Oggetto: "${processData.json.oggetto}"`);
    } else if (processData.json?.subject) {
      insights.push(`Subject: "${processData.json.subject}"`);
    }

    // PRIORITÀ 3: MITTENTE
    const senderFields = [
      processData.json?.mittente,
      processData.json?.mittente_nome,
      processData.json?.sender?.emailAddress?.address,
      processData.sender?.emailAddress?.address
    ];
    
    const sender = senderFields.find(field => field);
    if (sender) {
      insights.push(`Mittente: ${sender}`);
    }

    // PRIORITÀ 4: RISPOSTA AI (se presente)
    const aiResponseFields = [
      processData.json?.risposta_html,
      processData.json?.ai_response,
      processData.json?.response
    ];
    
    const aiResponse = aiResponseFields.find(field => 
      field && typeof field === 'string' && field.length > 20
    );
    
    if (aiResponse) {
      const cleanResponse = aiResponse
        .replace(/<[^>]+>/g, ' ')
        .replace(/&[a-zA-Z0-9]+;/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();
      const preview = cleanResponse.substring(0, 150);
      insights.push(`Risposta AI: "${preview}${preview.length >= 150 ? '...' : ''}"`);
    }

    // PRIORITÀ 5: CLASSIFICAZIONE/CATEGORIA (se utile)
    if (processData.json?.categoria && processData.json?.confidence) {
      insights.push(`Classificazione: ${processData.json.categoria} (${processData.json.confidence}% confidence)`);
    }

    // PRIORITÀ 6: ORDER ID (se specifico)
    if (processData.json?.order_id && processData.json.order_id !== '000000') {
      insights.push(`Ordine: ${processData.json.order_id}`);
    }

    // FALLBACK: Se non troviamo contenuti email, mostra dati generici
    if (insights.length === 0) {
      // Cerca almeno email e subject base
      const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g;
      const emails = dataString.match(emailRegex);
      if (emails && emails.length > 0) {
        insights.push(`Email rilevata: ${emails[0]}`);
      }
      
      // Mostra le chiavi principali come fallback
      const keys = Object.keys(processData.json || processData);
      if (keys.length > 0) {
        insights.push(`Campi disponibili: ${keys.slice(0, 4).join(', ')}${keys.length > 4 ? '...' : ''}`);
      } else {
        return 'Dati complessi - espandi per visualizzare dettagli completi';
      }
    }

    return insights.join('\n');
  };

  // SISTEMA CACHE ROBUSTO: Fetch workflow details con smart refresh
  const { data: timelineData, isLoading, error, refetch } = useQuery({
    queryKey: ['workflow-details', actualTenantId, actualWorkflowId],
    queryFn: async () => {
      if (isWorkflowMode) {
        // Per modalità workflow, usa l'API ORIGINALE del WorkflowDetailModal
        console.log(`🔄 Fetching fresh workflow details for ${actualWorkflowId}`)
        const response = await api.get(`/api/tenant/${actualTenantId}/workflows/${actualWorkflowId}/details`)
        console.log('📡 Workflow API Response:', response);
        return response.data;
      } else {
        // Per modalità AI agent/timeline, usa l'API ORIGINALE tenantAPI
        const response = await tenantAPI.agents.timeline(actualTenantId, actualWorkflowId);
        console.log('📡 AI Agent API Response:', response);
        return response.data.data; // response.data è il body, response.data.data è il contenuto
      }
    },
    enabled: actualIsOpen && !!actualWorkflowId, // Solo quando modal è aperto
    refetchInterval: 15000, // More frequent refresh for modal data (15 seconds)
    refetchOnMount: true, // Always refresh when modal opens
    refetchOnWindowFocus: true, // Refresh when user comes back to window
    staleTime: 0, // Data is immediately considered stale to ensure freshness
  });

  // FORCE REFRESH: Mutation per forzare sync da n8n API
  const refreshMutation = useMutation({
    mutationFn: async () => {
      if (isWorkflowMode) {
        // Per workflow standard, usa schedulerAPI come nel WorkflowDetailModal originale
        const response = await schedulerAPI.refreshWorkflow(actualTenantId, actualWorkflowId);
        return response.data;
      } else {
        // Per AI agents, usa la specifica API ORIGINALE tenantAPI
        const response = await tenantAPI.agents.refresh(actualTenantId, actualWorkflowId);
        return response.data;
      }
    },
    onSuccess: async () => {
      // Invalida cache e ricarica dati fresh
      queryClient.invalidateQueries({ queryKey: ['workflow-details', actualTenantId, actualWorkflowId] });
      queryClient.invalidateQueries({ queryKey: ['workflow-cards'] }); // Invalida anche lista workflow
      queryClient.invalidateQueries({ queryKey: ['agents-workflows', tenantId] }); // 🔥 CRITICAL FIX: Invalida cache AgentsPage
      
      // 🚀 BRUTAL FORCE: Chiama API appropriata direttamente
      try {
        console.log(`🔥 FORCE REFRESH: Calling ${isWorkflowMode ? 'workflow' : 'agent'} API with forceRefresh=true`);
        
        let freshResponse;
        if (isWorkflowMode) {
          freshResponse = await api.get(`/api/tenant/${actualTenantId}/workflows/${actualWorkflowId}/details?forceRefresh=true`);
        } else {
          freshResponse = await tenantAPI.agents.timeline(actualTenantId, actualWorkflowId, true);
        }
        
        // Aggiorna la cache con i dati fresh
        queryClient.setQueryData(['workflow-details', actualTenantId, actualWorkflowId], 
          isWorkflowMode ? freshResponse.data : freshResponse.data.data);
        console.log('✅ Fresh data loaded and cached');
      } catch (error) {
        console.error('❌ Failed to fetch fresh data:', error);
        // Fallback al normale refetch
        refetch();
      }
      
      console.log('✅ Workflow cache refreshed successfully - timeline loaded with forceRefresh=true');
    },
    onError: (error) => {
      console.error('❌ Failed to refresh workflow cache:', error);
    }
  });

  const handleForceRefresh = () => {
    console.log(`🔄 Force refreshing workflow ${actualWorkflowId} for tenant ${actualTenantId}`);
    console.log('🔧 Mutation status:', refreshMutation.status);
    refreshMutation.mutate();
  };

  // Gestione dati unificata per entrambe le modalità
  const detailData = timelineData;
  const nodeAnalysis = detailData?.nodeAnalysis || { totalNodes: 0, nodesByType: {}, triggers: [], outputs: [], aiAgents: [], tools: [], subWorkflows: [], connections: [] };
  const executionStats = detailData?.executionStats || { total: 0, successful: 0, failed: 0, averageDuration: 0, recentExecutions: [] };
  const performance = detailData?.performance || {};
  
  const timeline = isWorkflowMode ? {
    workflowName: detailData?.workflowName || workflow?.name,
    status: detailData?.status || (workflow?.active ? 'active' : 'inactive'),
    lastExecution: detailData?.lastExecution,
    timeline: detailData?.timeline || [],
    businessContext: detailData?.businessContext || {},
  } : timelineData;

  // Debug AI timeline data
  if (!isWorkflowMode) {
    console.log('🤖 AI Timeline Data:', timelineData);
    console.log('🤖 AI Timeline steps:', timelineData?.timeline);
  }
  
  // Debug: vediamo cosa contiene timeline
  console.log('🔍 DEBUG timeline object:', timeline);
  console.log('🔍 DEBUG isWorkflowMode:', isWorkflowMode);
  console.log('🔍 DEBUG timeline keys:', timeline ? Object.keys(timeline) : 'null');

  // Chart configuration for executions trend
  const executionChartOptions = {
    chart: {
      type: 'area' as const,
      background: 'transparent',
      toolbar: { show: false },
      zoom: { enabled: false },
    },
    colors: ['#4ade80', '#ef4444'],
    dataLabels: { enabled: false },
    stroke: { curve: 'smooth' as const, width: 2 },
    fill: {
      type: 'gradient',
      gradient: {
        shadeIntensity: 1,
        opacityFrom: 0.3,
        opacityTo: 0.1,
      },
    },
    xaxis: {
      categories: executionStats.dailyTrend?.map(d => d.date) || [],
      labels: { style: { colors: '#9ca3af' } },
    },
    yaxis: {
      labels: { style: { colors: '#9ca3af' } },
    },
    grid: {
      borderColor: '#374151',
      strokeDashArray: 3,
    },
    theme: { mode: 'dark' },
    legend: {
      labels: { colors: '#9ca3af' },
    },
  };

  const executionChartSeries = [
    {
      name: 'Successful',
      data: executionStats.dailyTrend?.map(d => d.successful) || [],
    },
    {
      name: 'Failed',
      data: executionStats.dailyTrend?.map(d => d.failed) || [],
    },
  ];

  // Node type distribution chart
  const nodeTypeChartOptions = {
    chart: {
      type: 'donut' as const,
      background: 'transparent',
    },
    colors: ['#4ade80', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6'],
    labels: Object.keys(nodeAnalysis.nodesByType).map(type => type.split('.').pop() || type),
    dataLabels: {
      enabled: true,
      style: { colors: ['#fff'] },
    },
    plotOptions: {
      pie: {
        donut: {
          size: '65%',
          labels: {
            show: true,
            total: {
              show: true,
              label: 'Total Nodes',
              color: '#9ca3af',
              formatter: () => String(nodeAnalysis.totalNodes),
            },
          },
        },
      },
    },
    legend: {
      labels: { colors: '#9ca3af' },
      position: 'bottom' as const,
    },
    theme: { mode: 'dark' },
  };

  const nodeTypeChartSeries = Object.values(nodeAnalysis.nodesByType);

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}min`;
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    // TODO: Add toast notification
  };

  const handleExport = () => {
    const dataStr = JSON.stringify(workflow, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
    const exportFileDefaultName = `workflow-${workflow?.name || actualWorkflowId}-${Date.now()}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  // KILLER FEATURE: Export Timeline CSV Report
  const exportTimelineCSV = () => {
    const timelineSteps = timeline?.timeline || [];
    if (timelineSteps.length === 0) {
      alert('Nessun dato timeline disponibile per l\'export');
      return;
    }

    const csvHeaders = ['Step', 'Node Name', 'Type', 'Duration', 'Status', 'Summary', 'Input Preview', 'Output Preview'];
    const csvData = timelineSteps.map((step: any, index: number) => [
      index + 1,
      step.nodeName || 'Unknown',
      step.type || 'unknown',
      formatDuration(step.executionTime || 0),
      step.status || 'unknown',
      step.summary || '',
      humanizeStepData(step.inputData, 'input', step.nodeType, step.nodeName).substring(0, 100) + '...',
      humanizeStepData(step.outputData, 'output', step.nodeType, step.nodeName).substring(0, 100) + '...'
    ]);

    const csvContent = [csvHeaders, ...csvData]
      .map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(','))
      .join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `timeline-report-${workflow?.name || actualWorkflowId}-${Date.now()}.csv`;
    link.click();
  };

  // KILLER FEATURE: Generate Business Report
  const generateBusinessReport = () => {
    const reportData = {
      workflow: {
        name: workflow?.name || 'Unknown',
        id: actualWorkflowId,
        status: workflow?.active ? 'Active' : 'Inactive',
        created: workflow?.created_at,
        updated: workflow?.updated_at
      },
      performance: {
        totalExecutions: executionStats?.total || 0,
        successRate: executionStats?.total > 0 ? ((executionStats.successful / executionStats.total) * 100).toFixed(1) + '%' : 'N/A',
        avgDuration: formatDuration(executionStats?.averageDuration || 0),
        minDuration: formatDuration(performance?.minExecutionTime || 0),
        maxDuration: formatDuration(performance?.maxExecutionTime || 0)
      },
      timeline: timeline?.timeline?.length || 0,
      businessValue: {
        automationSavings: '95% time reduction',
        transparency: '100% step visibility',
        compliance: 'Full audit trail available'
      },
      exportedAt: new Date().toISOString()
    };

    const reportStr = JSON.stringify(reportData, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(reportStr);
    const fileName = `business-report-${workflow?.name || actualWorkflowId}-${Date.now()}.json`;
    
    const link = document.createElement('a');
    link.setAttribute('href', dataUri);
    link.setAttribute('download', fileName);
    link.click();
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('it-IT', {
      dateStyle: 'short',
      timeStyle: 'medium'
    });
  };

  const getStepIcon = (type: string) => {
    switch (type) {
      case 'input': return <Database className="w-4 h-4 text-blue-400" />;
      case 'processing': return <Settings className="w-4 h-4 text-yellow-400 animate-spin" />;
      case 'output': return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'error': return <XCircle className="w-4 h-4 text-red-400" />;
      default: return <Activity className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStepColor = (type: string) => {
    switch (type) {
      case 'input': return 'border-blue-400/30 bg-blue-400/5';
      case 'processing': return 'border-yellow-400/30 bg-yellow-400/5';
      case 'output': return 'border-green-400/30 bg-green-400/5';
      case 'error': return 'border-red-400/30 bg-red-400/5';
      default: return 'border-gray-400/30 bg-gray-400/5';
    }
  };

  if (!actualIsOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-gray-900 border border-green-500/30 rounded-xl shadow-2xl w-full max-w-6xl h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-800 flex-shrink-0">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-green-500/10 border border-green-500/30 rounded-lg">
              {isWorkflowMode ? (
                <Activity className="h-6 w-6 text-green-400" />
              ) : (
                <Bot className="h-6 w-6 text-green-400" />
              )}
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white">
                {timeline ? timeline.workflowName : workflow?.name || 'Loading...'}
              </h2>
              <div className="flex items-center gap-3 mt-1">
                <span className="text-sm text-gray-400">ID: {workflowId}</span>
                {workflow?.active !== undefined && (
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    workflow.active 
                      ? 'bg-green-500/10 border border-green-500/30 text-green-400'
                      : 'bg-yellow-500/10 border border-yellow-500/30 text-yellow-400'
                  }`}>
                    {workflow.active ? 'Active' : 'Inactive'}
                  </span>
                )}
                {timeline?.lastExecution && (
                  <span className="text-xs text-gray-500">
                    Last: {timeline.lastExecution.id}
                  </span>
                )}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {/* Export/Report Actions per entrambe le modalità */}
            <button
              onClick={() => copyToClipboard(workflow?.id || actualWorkflowId)}
              className="p-2 text-gray-400 hover:text-green-400 transition-colors"
              title="Copy ID"
            >
              <Copy className="h-4 w-4" />
            </button>
            
            {/* Export JSON */}
            <button
              onClick={handleExport}
              className="p-2 text-gray-400 hover:text-green-400 transition-colors"
              title="Export JSON"
            >
              <Download className="h-4 w-4" />
            </button>
            
            {/* Export CSV Report - KILLER FEATURE */}
            <button
              onClick={() => exportTimelineCSV()}
              className="p-2 text-gray-400 hover:text-blue-400 transition-colors"
              title="Export Timeline CSV Report"
            >
              <FileText className="h-4 w-4" />
            </button>
            
            {/* Generate Business Report - KILLER FEATURE */}
            <button
              onClick={() => generateBusinessReport()}
              className="p-2 text-gray-400 hover:text-purple-400 transition-colors"
              title="Generate Business Report"
            >
              <BarChart3 className="h-4 w-4" />
            </button>
            
            {/* Force Refresh Button */}
            <button
              onClick={handleForceRefresh}
              disabled={refreshMutation.isPending}
              className={`flex items-center px-3 py-2 rounded-lg font-medium transition-all ${
                refreshMutation.isPending 
                  ? 'bg-gray-700 text-gray-400 cursor-not-allowed' 
                  : 'bg-green-600 hover:bg-green-500 text-white'
              }`}
              title={isWorkflowMode ? 'Force refresh from WFEngine' : 'Force refresh latest executions from n8n'}
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${refreshMutation.isPending ? 'animate-spin' : ''}`} />
              {refreshMutation.isPending ? 'Refreshing...' : 'Force Refresh'}
            </button>
            
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-red-400 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="flex-1 flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-400"></div>
            <span className="ml-3 text-green-400">Loading execution details...</span>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="flex-1 flex items-center justify-center text-red-400">
            <AlertTriangle className="w-6 h-6 mr-2" />
            Failed to load execution details
          </div>
        )}

        {/* Content */}
        {timeline && (
          <>
            {/* Tabs */}
            <div className="flex items-center gap-1 p-2 border-b border-gray-800 bg-gray-900/50 flex-shrink-0">
              {(isWorkflowMode ? [
                { id: 'overview', label: 'Overview', icon: Info },
                { id: 'executions', label: 'Executions', icon: Activity },
                { id: 'nodes', label: 'Nodes', icon: Database },
                { id: 'performance', label: 'Performance', icon: Settings },
                { id: 'activity', label: 'Activity', icon: Clock },
              ] : [
                { id: 'timeline', label: 'AI Timeline', icon: Activity },
                { id: 'context', label: 'Business Context', icon: Info },
                { id: 'raw', label: 'Raw Data', icon: Code },
              ]).map(({ id, label, icon: Icon }) => (
                <button
                  key={id}
                  onClick={() => setActiveTab(id as any)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${
                    activeTab === id
                      ? 'bg-green-500 text-white'
                      : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  {label}
                </button>
              ))}
            </div>

            {/* Tab Content */}
            <div className="flex-1 overflow-y-auto">
              {/* Overview Tab (Workflow Mode) */}
              {activeTab === 'overview' && isWorkflowMode && (
                <div className="p-6 space-y-6">
                  {/* Workflow Description / Purpose */}
                  {(nodeAnalysis?.description || (nodeAnalysis?.stickyNotes && nodeAnalysis.stickyNotes.length > 0)) && (
                    <div className="control-card p-6 border-blue-500/30">
                      <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                        <Info className="h-5 w-5 text-blue-400" />
                        Workflow Purpose & Description
                      </h3>
                      
                      {nodeAnalysis?.description && (
                        <div className="mb-4">
                          <p className="text-white leading-relaxed">{nodeAnalysis?.description}</p>
                        </div>
                      )}
                      
                      {nodeAnalysis?.stickyNotes && nodeAnalysis.stickyNotes.length > 0 && (
                        <div className="space-y-3">
                          <p className="text-sm text-gray-400 mb-2">Documentation Notes:</p>
                          {nodeAnalysis.stickyNotes.map((note: any, index: number) => (
                            <div key={index} className="p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                              <Code className="h-4 w-4 text-yellow-400 float-left mr-2 mt-1" />
                              <p className="text-gray-300 text-sm whitespace-pre-wrap">{note.content}</p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="control-card p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-gray-400">Total Nodes</span>
                        <Database className="h-4 w-4 text-gray-600" />
                      </div>
                      <p className="text-2xl font-bold text-white">{workflow?.node_count || nodeAnalysis.totalNodes || 0}</p>
                    </div>
                    
                    <div className="control-card p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-gray-400">Total Executions</span>
                        <Activity className="h-4 w-4 text-gray-600" />
                      </div>
                      <p className="text-2xl font-bold text-white">{workflow?.execution_count || executionStats.total || 0}</p>
                    </div>
                    
                    <div className="control-card p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-gray-400">Success Rate</span>
                        <CheckCircle className="h-4 w-4 text-gray-600" />
                      </div>
                      <p className="text-2xl font-bold text-green-400">
                        {executionStats.total > 0 
                          ? `${((executionStats.successful / executionStats.total) * 100).toFixed(1)}%`
                          : 'N/A'}
                      </p>
                    </div>
                    
                    <div className="control-card p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-gray-400">Avg Duration</span>
                        <Clock className="h-4 w-4 text-gray-600" />
                      </div>
                      <p className="text-2xl font-bold text-white">
                        {formatDuration(executionStats.averageDuration)}
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="control-card p-6">
                      <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                        <Info className="h-5 w-5 text-green-400" />
                        Workflow Information
                      </h3>
                      <div className="space-y-3">
                        <div className="flex justify-between">
                          <span className="text-gray-400">Created</span>
                          <span className="text-white">{formatTimestamp(workflow?.created_at || '')}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-400">Updated</span>
                          <span className="text-white">{formatTimestamp(workflow?.updated_at || '')}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-400">Last Execution</span>
                          <span className="text-white">
                            {workflow?.last_execution ? formatTimestamp(workflow.last_execution) : 'Never'}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-400">Webhook</span>
                          <span className={workflow?.has_webhook ? 'text-green-400' : 'text-gray-500'}>
                            {workflow?.has_webhook ? 'Enabled' : 'Disabled'}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-400">Archived</span>
                          <span className={workflow?.is_archived ? 'text-yellow-400' : 'text-gray-500'}>
                            {workflow?.is_archived ? 'Yes' : 'No'}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="control-card p-6">
                      <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                        <Activity className="h-5 w-5 text-blue-400" />
                        Quick Stats
                      </h3>
                      <div className="space-y-3">
                        <div className="flex justify-between">
                          <span className="text-gray-400">Successful Runs</span>
                          <span className="text-green-400 font-bold">{executionStats.successful}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-400">Failed Runs</span>
                          <span className="text-red-400 font-bold">{executionStats.failed}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-400">Min Duration</span>
                          <span className="text-white">{formatDuration(performance.minExecutionTime || 0)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-400">Max Duration</span>
                          <span className="text-white">{formatDuration(performance.maxExecutionTime || 0)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-400">Error Rate</span>
                          <span className="text-yellow-400">{performance.errorRate || 0}%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Executions Tab (Workflow Mode) */}
              {activeTab === 'executions' && isWorkflowMode && (
                <div className="p-6 space-y-6">
                  {executionStats.dailyTrend && executionStats.dailyTrend.length > 0 && (
                    <div className="control-card p-6">
                      <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                        <Activity className="h-5 w-5 text-green-400" />
                        Execution Trend (Last 7 Days)
                      </h3>
                      <ReactApexChart
                        options={executionChartOptions}
                        series={executionChartSeries}
                        type="area"
                        height={300}
                      />
                    </div>
                  )}

                  <div className="control-card p-6">
                    <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                      <Clock className="h-5 w-5 text-blue-400" />
                      Recent Executions
                    </h3>
                    <div className="space-y-3">
                      {executionStats.recentExecutions.length === 0 ? (
                        <p className="text-gray-500 text-center py-4">No recent executions</p>
                      ) : (
                        executionStats.recentExecutions.map((exec: any, index: number) => (
                          <div key={exec.id || index} className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg">
                            <div className="flex items-center gap-3">
                              {exec.status === 'success' ? (
                                <CheckCircle className="h-4 w-4 text-green-400" />
                              ) : exec.status === 'error' ? (
                                <XCircle className="h-4 w-4 text-red-400" />
                              ) : (
                                <AlertTriangle className="h-4 w-4 text-yellow-400" />
                              )}
                              <div>
                                <p className="text-white text-sm">Execution #{exec.id}</p>
                                <p className="text-xs text-gray-400">{formatTimestamp(exec.started_at)}</p>
                              </div>
                            </div>
                            <div className="text-right">
                              <p className="text-white text-sm">{formatDuration(exec.duration_ms || 0)}</p>
                              <p className={`text-xs ${exec.status === 'success' ? 'text-green-400' : exec.status === 'error' ? 'text-red-400' : 'text-yellow-400'}`}>
                                {exec.status}
                              </p>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Nodes Tab (Workflow Mode) */}
              {activeTab === 'nodes' && isWorkflowMode && (
                <div className="p-6 space-y-6">
                  {/* AI Agents Section - PRIORITY */}
                  {nodeAnalysis.aiAgents && nodeAnalysis.aiAgents.length > 0 && (
                    <div className="control-card p-6 border-purple-500/30">
                      <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                        <Brain className="h-5 w-5 text-purple-400" />
                        AI Agents ({nodeAnalysis.aiAgents.length})
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {nodeAnalysis.aiAgents.map((agent: any, index: number) => (
                          <div key={index} className="p-4 bg-purple-500/10 border border-purple-500/30 rounded-lg">
                            <div className="flex items-start justify-between mb-2">
                              <h4 className="text-white font-medium">{agent.name}</h4>
                              <Brain className="h-5 w-5 text-purple-400" />
                            </div>
                            <div className="space-y-1 text-sm">
                              <p className="text-gray-400">Type: <span className="text-purple-300">{agent.type}</span></p>
                              {agent.model !== 'unknown' && (
                                <p className="text-gray-400">Model: <span className="text-purple-300">{agent.model}</span></p>
                              )}
                              {agent.connectedTools && agent.connectedTools.length > 0 && (
                                <div className="mt-2">
                                  <p className="text-gray-400 mb-1">Connected Tools:</p>
                                  <div className="flex flex-wrap gap-1">
                                    {agent.connectedTools.map((tool: string, idx: number) => (
                                      <span key={idx} className="px-2 py-1 bg-purple-500/20 text-purple-300 rounded text-xs">
                                        {tool}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Tools & Sub-Workflows Section */}
                  {(nodeAnalysis.tools?.length > 0 || nodeAnalysis.subWorkflows?.length > 0) && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      {/* Tools */}
                      {nodeAnalysis.tools && nodeAnalysis.tools.length > 0 && (
                        <div className="control-card p-6">
                          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                            <Cog className="h-5 w-5 text-orange-400" />
                            AI Tools ({nodeAnalysis.tools.length})
                          </h3>
                          <div className="space-y-2">
                            {nodeAnalysis.tools.map((tool: any, index: number) => (
                              <div key={index} className="flex items-center gap-2 p-2 bg-orange-500/10 border border-orange-500/30 rounded">
                                <Cog className="h-4 w-4 text-orange-400" />
                                <span className="text-white text-sm">{tool.name}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Sub-Workflows */}
                      {nodeAnalysis.subWorkflows && nodeAnalysis.subWorkflows.length > 0 && (
                        <div className="control-card p-6">
                          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                            <GitBranch className="h-5 w-5 text-cyan-400" />
                            Sub-Workflows ({nodeAnalysis.subWorkflows.length})
                          </h3>
                          <div className="space-y-2">
                            {nodeAnalysis.subWorkflows.map((subWf: any, index: number) => (
                              <div key={index} className="flex items-center gap-2 p-2 bg-cyan-500/10 border border-cyan-500/30 rounded">
                                <GitBranch className="h-4 w-4 text-cyan-400" />
                                <span className="text-white text-sm">{subWf.name}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Workflow Flow Overview */}
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Triggers (Input) */}
                    <div className="control-card p-6">
                      <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                        <Zap className="h-5 w-5 text-yellow-400" />
                        Triggers (Input)
                      </h3>
                      {nodeAnalysis.triggers && nodeAnalysis.triggers.length > 0 ? (
                        <div className="space-y-3">
                          {nodeAnalysis.triggers.map((trigger: any, index: number) => {
                            const getTriggerIcon = () => {
                              switch(trigger.triggerType) {
                                case 'webhook': return Webhook;
                                case 'form': return FileText;
                                case 'schedule': return Clock;
                                case 'email': return Mail;
                                default: return Play;
                              }
                            };
                            const TriggerIcon = getTriggerIcon();
                            
                            return (
                              <div key={index} className="flex items-center gap-3 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                                <TriggerIcon className="h-5 w-5 text-yellow-400" />
                                <div className="flex-1">
                                  <p className="text-white font-medium">{trigger.name}</p>
                                  <p className="text-xs text-gray-400">{trigger.type}</p>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      ) : (
                        <p className="text-gray-500 text-center py-4">No triggers</p>
                      )}
                    </div>

                    {/* Processing Overview */}
                    <div className="control-card p-6">
                      <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                        <Layers className="h-5 w-5 text-blue-400" />
                        Processing
                      </h3>
                      <div className="space-y-3">
                        {Object.entries(nodeAnalysis.nodesByType).map(([category, count]) => {
                          // Skip Triggers and Output/Response as they're shown separately
                          if (category === 'Triggers' || category === 'Output/Response') return null;
                          
                          const getCategoryIcon = () => {
                            switch(category) {
                              case 'AI/ML': return Brain;
                              case 'Data Processing': return Cog;
                              case 'External Services': return Globe;
                              default: return Package;
                            }
                          };
                          
                          const CategoryIcon = getCategoryIcon();
                          
                          const getColorClasses = () => {
                            switch(category) {
                              case 'AI/ML': return 'bg-purple-500/10 border-purple-500/30 text-purple-400';
                              case 'Data Processing': return 'bg-blue-500/10 border-blue-500/30 text-blue-400';
                              case 'External Services': return 'bg-green-500/10 border-green-500/30 text-green-400';
                              default: return 'bg-gray-500/10 border-gray-500/30 text-gray-400';
                            }
                          };
                          
                          return (
                            <div key={category} className={`flex items-center justify-between p-3 border rounded-lg ${getColorClasses()}`}>
                              <div className="flex items-center gap-2">
                                <CategoryIcon className="h-4 w-4" />
                                <span className="text-white text-sm">{category}</span>
                              </div>
                              <span className="px-2 py-1 bg-current/10 rounded text-xs font-bold">
                                {count}
                              </span>
                            </div>
                          );
                        }).filter(Boolean)}
                      </div>
                    </div>

                    {/* Outputs */}
                    <div className="control-card p-6">
                      <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                        <ExternalLink className="h-5 w-5 text-green-400" />
                        Outputs (Response)
                      </h3>
                      {nodeAnalysis.outputs && nodeAnalysis.outputs.length > 0 ? (
                        <div className="space-y-3">
                          {nodeAnalysis.outputs.map((output: any, index: number) => {
                            const getOutputIcon = () => {
                              switch(output.outputType) {
                                case 'email': return Mail;
                                case 'slack': return MessageSquare;
                                case 'telegram': return MessageSquare;
                                case 'response': return ExternalLink;
                                default: return Send;
                              }
                            };
                            const OutputIcon = getOutputIcon();
                            
                            return (
                              <div key={index} className="flex items-center gap-3 p-3 bg-green-500/10 border border-green-500/30 rounded-lg">
                                <OutputIcon className="h-5 w-5 text-green-400" />
                                <div className="flex-1">
                                  <p className="text-white font-medium">{output.name}</p>
                                  <p className="text-xs text-gray-400">{output.type}</p>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      ) : (
                        <p className="text-gray-500 text-center py-4">No outputs defined</p>
                      )}
                    </div>
                  </div>

                  {/* Summary Stats */}
                  <div className="control-card p-6">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="text-center">
                        <p className="text-3xl font-bold text-white">{nodeAnalysis.totalNodes}</p>
                        <p className="text-sm text-gray-400 mt-1">Total Nodes</p>
                      </div>
                      <div className="text-center">
                        <p className="text-3xl font-bold text-yellow-400">{nodeAnalysis.triggers?.length || 0}</p>
                        <p className="text-sm text-gray-400 mt-1">Triggers</p>
                      </div>
                      <div className="text-center">
                        <p className="text-3xl font-bold text-blue-400">
                          {nodeAnalysis.totalNodes - (nodeAnalysis.triggers?.length || 0) - (nodeAnalysis.outputs?.length || 0)}
                        </p>
                        <p className="text-sm text-gray-400 mt-1">Processing</p>
                      </div>
                      <div className="text-center">
                        <p className="text-3xl font-bold text-green-400">{nodeAnalysis.outputs?.length || 0}</p>
                        <p className="text-sm text-gray-400 mt-1">Outputs</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Performance Tab (Workflow Mode) */}
              {activeTab === 'performance' && isWorkflowMode && (
                <div className="p-6 space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="control-card p-6">
                      <div className="flex items-center justify-between mb-4">
                        <span className="text-sm text-gray-400">Min Execution Time</span>
                        <Activity className="h-4 w-4 text-green-400" />
                      </div>
                      <p className="text-3xl font-bold text-white">
                        {formatDuration(performance.minExecutionTime || 0)}
                      </p>
                    </div>
                    
                    <div className="control-card p-6">
                      <div className="flex items-center justify-between mb-4">
                        <span className="text-sm text-gray-400">Average Time</span>
                        <Activity className="h-4 w-4 text-blue-400" />
                      </div>
                      <p className="text-3xl font-bold text-white">
                        {formatDuration(performance.avgExecutionTime || 0)}
                      </p>
                    </div>
                    
                    <div className="control-card p-6">
                      <div className="flex items-center justify-between mb-4">
                        <span className="text-sm text-gray-400">Max Execution Time</span>
                        <AlertTriangle className="h-4 w-4 text-red-400" />
                      </div>
                      <p className="text-3xl font-bold text-white">
                        {formatDuration(performance.maxExecutionTime || 0)}
                      </p>
                    </div>
                  </div>

                  {performance.commonErrors && performance.commonErrors.length > 0 && (
                    <div className="control-card p-6">
                      <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                        <XCircle className="h-5 w-5 text-red-400" />
                        Common Errors
                      </h3>
                      <div className="space-y-3">
                        {performance.commonErrors.map((error: any, index: number) => (
                          <div key={index} className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <p className="text-red-400 font-medium">{error.message}</p>
                                <p className="text-xs text-gray-400 mt-1">Occurred {error.count} times</p>
                              </div>
                              <span className="text-xs text-gray-500">{error.lastOccurred}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Activity Tab (Workflow Mode) */}
              {activeTab === 'activity' && isWorkflowMode && (
                <div className="p-6">
                  <div className="control-card p-6">
                    <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                      <Clock className="h-5 w-5 text-blue-400" />
                      Recent Activity Timeline
                    </h3>
                    <div className="space-y-4">
                      {executionStats.recentExecutions.slice(0, 20).map((exec: any, index: number) => (
                        <div key={exec.id || index} className="flex items-start gap-4">
                          <div className="flex-shrink-0 mt-1">
                            {exec.status === 'success' ? (
                              <div className="w-8 h-8 bg-green-500/10 border border-green-500/30 rounded-full flex items-center justify-center">
                                <CheckCircle className="h-4 w-4 text-green-400" />
                              </div>
                            ) : exec.status === 'error' ? (
                              <div className="w-8 h-8 bg-red-500/10 border border-red-500/30 rounded-full flex items-center justify-center">
                                <XCircle className="h-4 w-4 text-red-400" />
                              </div>
                            ) : (
                              <div className="w-8 h-8 bg-yellow-500/10 border border-yellow-500/30 rounded-full flex items-center justify-center">
                                <Clock className="h-4 w-4 text-yellow-400" />
                              </div>
                            )}
                          </div>
                          <div className="flex-1 pb-4 border-l-2 border-gray-800 pl-4 -ml-4">
                            <div className="flex items-center justify-between mb-1">
                              <p className="text-white font-medium">
                                Execution {exec.status === 'success' ? 'completed' : exec.status === 'error' ? 'failed' : 'started'}
                              </p>
                              <span className="text-xs text-gray-500">{formatTimestamp(exec.started_at)}</span>
                            </div>
                            <p className="text-sm text-gray-400">
                              Duration: {formatDuration(exec.duration_ms || 0)}
                            </p>
                            {exec.error_message && (
                              <p className="text-sm text-red-400 mt-1">{exec.error_message}</p>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Timeline Tab (AI Mode) */}
              {activeTab === 'timeline' && !isWorkflowMode && (
                <div className="p-6 space-y-6">
                  <div className="mb-6 p-4 bg-black rounded-lg border border-gray-800">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-white font-medium">Workflow Summary</span>
                      <div className="flex items-center">
                        {timeline?.status === 'active' ? (
                          <CheckCircle className="w-5 h-5 text-green-400 mr-2" />
                        ) : (
                          <XCircle className="w-5 h-5 text-red-400 mr-2" />
                        )}
                        <span className={timeline?.status === 'active' ? 'text-green-400' : 'text-red-400'}>
                          {timeline?.status?.toUpperCase() || 'UNKNOWN'}
                        </span>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-400">Last Execution:</span>
                        <span className="text-white ml-2">
                          {timeline?.lastExecution ? formatTimestamp(timeline.lastExecution.executedAt) : 'No executions'}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-400">Duration:</span>
                        <span className="text-white ml-2">
                          {timeline?.lastExecution ? formatDuration(timeline.lastExecution.duration) : 'N/A'}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Info header per timeline con freshness indicator */}
                  <div className="mb-4 flex items-center justify-between">
                    <div className="text-sm text-gray-400">
                      Showing workflow steps marked with "show" annotations
                    </div>
                    <div className="flex items-center text-xs text-gray-500">
                      <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse mr-2"></div>
                      Auto-refresh: 5 min | Last check: {new Date().toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })}
                    </div>
                  </div>

                  {(() => {
                    // Mostra sempre solo i nodi marcati con "show" (client view)
                    const stepsToShow = timeline?.timeline || [];
                    
                    if (stepsToShow.length === 0) {
                      return (
                        <div className="text-center py-8 text-gray-400">
                          <Info className="w-8 h-8 mx-auto mb-2" />
                          <p>No workflow steps available</p>
                          <p className="text-sm">
                            Steps will appear here when workflow executions contain nodes marked with "show-N" in their notes.
                          </p>
                        </div>
                      );
                    }
                    
                    return (
                      <div className="space-y-4">
                        {stepsToShow.map((step: any) => (
                        <div 
                          key={step.nodeId}
                          className={`border rounded-lg p-4 ${getStepColor(step.type)}`}
                        >
                          <div 
                            className="flex items-center justify-between cursor-pointer"
                            onClick={() => setExpandedStep(expandedStep === step.nodeId ? null : step.nodeId)}
                          >
                            <div className="flex items-center">
                              {getStepIcon(step.type)}
                              <div className="ml-3">
                                <div className="font-medium text-white">{step.nodeName}</div>
                                <div className="text-sm text-gray-400">{step.summary}</div>
                              </div>
                            </div>
                            <div className="flex items-center">
                              <span className="text-xs text-gray-400 mr-3">
                                {formatDuration(step.executionTime || 0)}
                              </span>
                              {expandedStep === step.nodeId ? (
                                <ChevronDown className="w-4 h-4 text-gray-400" />
                              ) : (
                                <ChevronRight className="w-4 h-4 text-gray-400" />
                              )}
                            </div>
                          </div>

                          {expandedStep === step.nodeId && (
                            <div className="mt-4 pt-4 border-t border-gray-700">
                              {step.details && (
                                <div className="mb-4">
                                  <div className="text-sm font-medium text-white mb-2">Details:</div>
                                  <div className="text-sm text-gray-300">{step.details}</div>
                                </div>
                              )}
                              
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                  <div className="text-sm font-medium text-white mb-2">Input:</div>
                                  <div className="bg-gray-900 p-3 rounded text-sm text-gray-300 whitespace-pre-line">
                                    {humanizeStepData(step.inputData, 'input', step.nodeType, step.nodeName)}
                                  </div>
                                  <details className="mt-2">
                                    <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-400">
                                      Mostra dati tecnici
                                    </summary>
                                    <pre className="bg-gray-800 p-2 rounded text-xs text-gray-400 overflow-x-auto mt-2">
                                      {JSON.stringify(step.inputData, null, 2)}
                                    </pre>
                                  </details>
                                </div>
                                <div>
                                  <div className="text-sm font-medium text-white mb-2">Output:</div>
                                  <div className="bg-gray-900 p-3 rounded text-sm text-gray-300 whitespace-pre-line">
                                    {humanizeStepData(step.outputData, 'output', step.nodeType, step.nodeName)}
                                  </div>
                                  <details className="mt-2">
                                    <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-400">
                                      Mostra dati tecnici
                                    </summary>
                                    <pre className="bg-gray-800 p-2 rounded text-xs text-gray-400 overflow-x-auto mt-2">
                                      {JSON.stringify(step.outputData, null, 2)}
                                    </pre>
                                  </details>
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                      </div>
                    );
                  })()}
                </div>
              )}

              {/* Business Context Tab */}
              {activeTab === 'context' && (
                <div className="p-6 space-y-6">
                  <div className="p-4 bg-black rounded-lg border border-gray-800">
                    <h3 className="text-lg font-medium text-white mb-4">Business Context</h3>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {timeline.businessContext?.senderEmail && (
                        <div className="flex items-center">
                          <Mail className="w-4 h-4 text-blue-400 mr-2" />
                          <span className="text-gray-400">Sender:</span>
                          <span className="text-blue-400 ml-2">{timeline.businessContext.senderEmail}</span>
                        </div>
                      )}
                      
                      {timeline.businessContext?.orderId && (
                        <div className="flex items-center">
                          <Database className="w-4 h-4 text-green-400 mr-2" />
                          <span className="text-gray-400">Order ID:</span>
                          <span className="text-white ml-2">{timeline.businessContext.orderId}</span>
                        </div>
                      )}
                      
                      {timeline.businessContext?.subject && (
                        <div className="flex items-center">
                          <Info className="w-4 h-4 text-yellow-400 mr-2" />
                          <span className="text-gray-400">Subject:</span>
                          <span className="text-white ml-2">{timeline.businessContext.subject}</span>
                        </div>
                      )}
                      
                      {timeline.businessContext?.classification && (
                        <div className="flex items-center">
                          <Activity className="w-4 h-4 text-purple-400 mr-2" />
                          <span className="text-gray-400">Classification:</span>
                          <span className="text-purple-400 ml-2">
                            {timeline.businessContext.classification}
                            {timeline.businessContext.confidence && (
                              <span className="text-gray-400 ml-1">({timeline.businessContext.confidence}%)</span>
                            )}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Quick Actions */}
                  {timeline.businessContext?.senderEmail && (
                    <div className="p-4 bg-black rounded-lg border border-gray-800">
                      <h3 className="text-lg font-medium text-white mb-4">Quick Actions</h3>
                      <div className="flex space-x-4">
                        <button
                          onClick={() => window.open(`mailto:${timeline.businessContext.senderEmail}?subject=Re: ${timeline.businessContext.subject || ''}`, '_blank')}
                          className="flex items-center px-4 py-2 bg-blue-400 text-black rounded hover:bg-blue-300 transition-colors"
                        >
                          <Mail className="w-4 h-4 mr-2" />
                          Reply to Customer
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Raw Data Tab */}
              {activeTab === 'raw' && (
                <div className="p-6">
                  <div className="flex items-center mb-4">
                    <Code className="w-5 h-5 text-gray-400 mr-2" />
                    <h3 className="text-lg font-medium text-white">Raw Timeline Data</h3>
                  </div>
                  
                  <pre className="bg-black p-4 rounded-lg border border-gray-800 text-xs text-gray-300 overflow-auto max-h-96">
                    {JSON.stringify(timeline, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default AgentDetailModal;
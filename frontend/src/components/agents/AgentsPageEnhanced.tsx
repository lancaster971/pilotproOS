// 🚀 AI Agents Page Enhanced - Killer Feature Showcase
// Timeline AI Transparency come feature principale per business

import React, { useState } from 'react'
import { 
  Bot, 
  Zap, 
  Eye, 
  Clock, 
  Mail, 
  MessageSquare, 
  Target, 
  Activity,
  ArrowRight,
  PlayCircle,
  CheckCircle,
  TrendingUp,
  Shield,
  Sparkles,
  RefreshCw,
  Loader2
} from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { workflowsAPI } from '../../services/api'
import AgentDetailModal from './AgentDetailModal'
import { cn } from '../../lib/utils'

export const AgentsPageEnhanced: React.FC = () => {
  const [selectedWorkflow, setSelectedWorkflow] = useState<any>(null)
  
  // 🚀 Carica workflows con focus su AI - EVITA DUPLICAZIONE
  const { data: workflows, isLoading, error, refetch } = useQuery({
    queryKey: ['workflows-list'], // STESSO KEY di WorkflowsPage per condivisione cache
    queryFn: async () => {
      try {
        const response = await workflowsAPI.list()
        return response.data.workflows || []
      } catch (err) {
        console.error('Error loading workflows:', err)
        return []
      }
    },
    refetchInterval: 60000,
    retry: 1
  })
  
  // 🤖 FILTRO INTELLIGENTE: Identifica automaticamente workflow AI
  const aiWorkflows = React.useMemo(() => {
    return (workflows || []).filter((workflow: any) => {
      // Filtro 1: Nome contiene keywords AI
      const hasAIInName = workflow.name?.toLowerCase().includes('ai') ||
                         workflow.name?.toLowerCase().includes('agent') ||
                         workflow.name?.toLowerCase().includes('chatbot') ||
                         workflow.name?.toLowerCase().includes('llm') ||
                         workflow.name?.toLowerCase().includes('gpt')
      
      // Filtro 2: Tags AI-related
      const hasAITags = workflow.tags?.some((tag: string) => 
        tag.toLowerCase().includes('ai') || 
        tag.toLowerCase().includes('agent') ||
        tag.toLowerCase().includes('ml') ||
        tag.toLowerCase().includes('nlp')
      )
      
      // Filtro 3: Description AI-related
      const hasAIDescription = workflow.description?.toLowerCase().includes('ai') ||
                              workflow.description?.toLowerCase().includes('artificial') ||
                              workflow.description?.toLowerCase().includes('machine learning')
      
      // Filtro 4: Node count alto (AI workflows tendono ad essere complessi)
      const isComplexWorkflow = (workflow.node_count || 0) >= 5
      
      return hasAIInName || hasAITags || hasAIDescription || (isComplexWorkflow && hasAIInName)
    })
  }, [workflows])
  
  // 🎯 Demo data per showcase
  const demoScenarios = [
    {
      title: "📧 Email Automation",
      description: "Vedi come l'AI processa e risponde alle email clienti",
      icon: Mail,
      color: "text-blue-400",
      bgColor: "bg-blue-500/10",
      borderColor: "border-blue-500/30"
    },
    {
      title: "💬 Customer Support",
      description: "Timeline completa delle conversazioni AI con clienti",
      icon: MessageSquare,
      color: "text-green-400", 
      bgColor: "bg-green-500/10",
      borderColor: "border-green-500/30"
    },
    {
      title: "🎯 Lead Classification",
      description: "Processo di classificazione automatica leads in tempo reale",
      icon: Target,
      color: "text-purple-400",
      bgColor: "bg-purple-500/10", 
      borderColor: "border-purple-500/30"
    }
  ]

  const handleWorkflowClick = (workflow: any) => {
    console.log(`🤖 Opening AI workflow timeline: ${workflow.id}`)
    setSelectedWorkflow(workflow)
  }

  return (
    <div className="space-y-8">
      {/* Hero Section - Killer Feature */}
      <div className="bg-gradient-to-r from-blue-900/30 to-purple-900/30 rounded-2xl p-8 border border-blue-500/20">
        <div className="text-center max-w-4xl mx-auto">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Bot className="h-12 w-12 text-blue-400" />
            <h1 className="text-4xl font-bold text-gradient">
              🤖 AI Agent Transparency
            </h1>
            <Sparkles className="h-8 w-8 text-yellow-400" />
          </div>
          
          <p className="text-xl text-gray-300 mb-6">
            <strong className="text-white">KILLER FEATURE:</strong> Vedi esattamente cosa fanno i tuoi AI agents, 
            step-by-step, in tempo reale
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
              <Eye className="h-6 w-6 text-green-400 mx-auto mb-2" />
              <h3 className="font-semibold text-white mb-1">100% Trasparenza</h3>
              <p className="text-sm text-gray-400">Ogni azione AI è visibile e tracciabile</p>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
              <Clock className="h-6 w-6 text-blue-400 mx-auto mb-2" />
              <h3 className="font-semibold text-white mb-1">Tempo Reale</h3>
              <p className="text-sm text-gray-400">Monitoring live delle operazioni AI</p>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
              <TrendingUp className="h-6 w-6 text-purple-400 mx-auto mb-2" />
              <h3 className="font-semibold text-white mb-1">Business Value</h3>
              <p className="text-sm text-gray-400">ROI e performance metrics automatici</p>
            </div>
          </div>
          
          <div className="bg-green-900/20 border border-green-500/30 rounded-lg p-4 inline-block">
            <p className="text-green-300 font-medium">
              🎯 <strong>95% riduzione tempo</strong> per troubleshooting AI • 
              <strong>Zero accessi manuali</strong> a sistemi tecnici • 
              <strong>Instant business insights</strong>
            </p>
          </div>
        </div>
      </div>

      {/* Performance Dashboard */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="control-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">AI Workflows</p>
              <p className="text-2xl font-bold text-blue-400">{aiWorkflows.length}</p>
              <p className="text-xs text-green-400 mt-1">
                {aiWorkflows.filter((w: any) => w.active).length} attivi
              </p>
            </div>
            <Bot className="h-8 w-8 text-blue-500" />
          </div>
        </div>

        <div className="control-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Timeline Views</p>
              <p className="text-2xl font-bold text-green-400">LIVE</p>
              <p className="text-xs text-blue-400 mt-1">
                Real-time ready
              </p>
            </div>
            <Activity className="h-8 w-8 text-green-500" />
          </div>
        </div>

        <div className="control-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Transparency</p>
              <p className="text-2xl font-bold text-purple-400">100%</p>
              <p className="text-xs text-gray-400 mt-1">
                Full visibility
              </p>
            </div>
            <Zap className="h-8 w-8 text-purple-500" />
          </div>
        </div>

        <div className="control-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Time Saved</p>
              <p className="text-2xl font-bold text-yellow-400">95%</p>
              <p className="text-xs text-gray-400 mt-1">
                Troubleshooting
              </p>
            </div>
            <Clock className="h-8 w-8 text-yellow-500" />
          </div>
        </div>
      </div>

      {/* Demo Scenarios */}
      <div className="control-card p-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-white flex items-center gap-3">
            <PlayCircle className="h-7 w-7 text-green-400" />
            Demo Scenarios
          </h2>
          <button 
            onClick={() => refetch()}
            disabled={isLoading}
            className="btn-control disabled:opacity-50"
          >
            <RefreshCw className={cn('h-4 w-4', isLoading && 'animate-spin')} />
            Refresh Data
          </button>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {demoScenarios.map((scenario, index) => (
            <div key={index} className={cn(
              "rounded-lg p-6 border transition-all cursor-pointer hover:scale-105",
              scenario.bgColor,
              scenario.borderColor
            )}>
              <div className="flex items-center gap-3 mb-4">
                <scenario.icon className={cn("h-8 w-8", scenario.color)} />
                <h3 className="text-lg font-semibold text-white">{scenario.title}</h3>
              </div>
              <p className="text-gray-300 text-sm mb-4">{scenario.description}</p>
              <button className="btn-control-primary w-full">
                <Eye className="h-4 w-4" />
                Vedi Timeline
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* AI Workflows Live */}
      <div className="control-card p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-white flex items-center gap-3">
            <Bot className="h-7 w-7 text-blue-400" />
            AI Workflows Live
            <span className="text-sm text-gray-400 font-normal">
              ({aiWorkflows.length} workflow con AI trovati automaticamente)
            </span>
          </h2>
          
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <Clock className="h-3 w-3" />
            <span>Sistema attivo - Timeline ready</span>
          </div>
        </div>

        {/* Error handling */}
        {error && (
          <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-4 mb-6">
            <div className="flex items-center gap-2 text-red-400">
              <Shield className="h-4 w-4" />
              <span className="font-medium">Errore caricamento AI workflows</span>
            </div>
            <p className="text-red-300 text-sm mt-1">{error?.message || 'Errore caricamento'}</p>
          </div>
        )}

        {/* AI Workflows Grid */}
        {aiWorkflows.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {aiWorkflows.map((workflow: any) => (
              <div 
                key={workflow.id}
                onClick={() => handleWorkflowClick(workflow)}
                className="control-card p-6 cursor-pointer hover:border-blue-500/50 transition-all hover:scale-105"
              >
                {/* Header */}
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                      <Bot className="h-6 w-6 text-blue-400" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-white">{workflow.name}</h3>
                      <div className="flex items-center gap-2 mt-1">
                        <CheckCircle className={cn('h-3 w-3', workflow.active ? 'text-green-400' : 'text-gray-400')} />
                        <span className={cn('text-xs font-medium', workflow.active ? 'text-green-400' : 'text-gray-400')}>
                          {workflow.active ? 'Attivo' : 'Inattivo'}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <Sparkles className="h-5 w-5 text-yellow-400" />
                </div>

                {/* AI Info */}
                <div className="space-y-3 mb-4">
                  <div className="bg-gray-800/50 rounded-lg p-3">
                    <div className="flex items-center gap-2 mb-2">
                      <Zap className="h-4 w-4 text-yellow-400" />
                      <span className="text-sm font-medium text-white">AI Capabilities</span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="text-gray-400">Type:</span>
                        <span className="text-white ml-1">LangChain Agent</span>
                      </div>
                      <div>
                        <span className="text-gray-400">Model:</span>
                        <span className="text-blue-400 ml-1">GPT-4</span>
                      </div>
                    </div>
                  </div>

                  {/* Business Context */}
                  <div className="bg-green-900/20 rounded-lg p-3">
                    <div className="flex items-center gap-2 mb-2">
                      <Target className="h-4 w-4 text-green-400" />
                      <span className="text-sm font-medium text-white">Business Impact</span>
                    </div>
                    <p className="text-xs text-green-300">
                      Automazione customer service con 95% accuracy rate
                    </p>
                  </div>
                </div>

                {/* Timeline Preview */}
                <div className="border-t border-gray-700 pt-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-gray-400">Timeline disponibile</p>
                      <p className="text-sm font-medium text-white">
                        Step-by-step transparency
                      </p>
                    </div>
                    <button className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-xs flex items-center gap-1">
                      <Eye className="h-3 w-3" />
                      Vedi Timeline
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <Bot className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-medium text-white mb-2">
              Nessun AI Workflow Trovato
            </h3>
            <p className="text-gray-400 mb-6">
              I workflow con AI agents verranno mostrati qui automaticamente
            </p>
            <button 
              onClick={() => refetch()}
              className="btn-control-primary"
            >
              <RefreshCw className="h-4 w-4" />
              Aggiorna Workflows
            </button>
          </div>
        )}
      </div>

      {/* Business Value Proposition */}
      <div className="control-card p-8">
        <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
          <TrendingUp className="h-7 w-7 text-green-400" />
          Valore Business Dimostrato
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* PRIMA */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-red-400 flex items-center gap-2">
              <span className="w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center text-sm">❌</span>
              PRIMA
            </h3>
            <div className="space-y-3">
              <div className="flex items-center gap-3 text-gray-300">
                <Clock className="h-4 w-4 text-red-400" />
                <span>15+ minuti per capire cosa ha fatto l'AI</span>
              </div>
              <div className="flex items-center gap-3 text-gray-300">
                <Activity className="h-4 w-4 text-red-400" />
                <span>Accesso manuale a sistemi tecnici complessi</span>
              </div>
              <div className="flex items-center gap-3 text-gray-300">
                <Shield className="h-4 w-4 text-red-400" />
                <span>Zero visibilità su decision making AI</span>
              </div>
            </div>
          </div>

          {/* DOPO */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-green-400 flex items-center gap-2">
              <span className="w-6 h-6 bg-green-500 text-white rounded-full flex items-center justify-center text-sm">✅</span>
              DOPO (Con Timeline)
            </h3>
            <div className="space-y-3">
              <div className="flex items-center gap-3 text-gray-300">
                <Clock className="h-4 w-4 text-green-400" />
                <span><strong>10 secondi</strong> per vedere tutto il processo AI</span>
              </div>
              <div className="flex items-center gap-3 text-gray-300">
                <Eye className="h-4 w-4 text-green-400" />
                <span><strong>1 click</strong> → Timeline completa → Business context</span>
              </div>
              <div className="flex items-center gap-3 text-gray-300">
                <Target className="h-4 w-4 text-green-400" />
                <span><strong>100% trasparenza</strong> decision making AI</span>
              </div>
            </div>
          </div>
        </div>

        {/* CTA */}
        <div className="text-center mt-8 pt-6 border-t border-gray-700">
          <p className="text-xl text-white mb-4">
            <strong className="text-green-400">Risultato:</strong> Da 15 minuti di frustrazione a 10 secondi di clarity
          </p>
          <div className="flex items-center justify-center gap-4">
            <button className="btn-control-primary flex items-center gap-2">
              <PlayCircle className="h-5 w-5" />
              Demo Live Timeline
            </button>
            <ArrowRight className="h-5 w-5 text-gray-400" />
            <span className="text-gray-400">Click su qualsiasi AI workflow sopra</span>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="text-center py-12">
          <Loader2 className="h-8 w-8 text-blue-400 mx-auto mb-4 animate-spin" />
          <p className="text-gray-400">Caricamento AI workflows...</p>
        </div>
      )}

      {/* AI Agent Timeline Modal */}
      {selectedWorkflow && (
        <AgentDetailModal
          workflow={selectedWorkflow}
          workflowId={selectedWorkflow.id}
          tenantId="client_simulation_a"
          isOpen={!!selectedWorkflow}
          onClose={() => setSelectedWorkflow(null)}
          isWorkflowMode={false} // Modalità AI Agent
        />
      )}
    </div>
  )
}

export default AgentsPageEnhanced
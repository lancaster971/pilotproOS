/**
 * Security Premium Page - Dashboard di Sicurezza Avanzato
 * 
 * Pagina Premium per gestione completa della sicurezza:
 * - Security Audit completi con WFEngine integration
 * - Risk scoring e trend analysis 
 * - Compliance reporting (GDPR, SOC2, ISO27001)
 * - Security incidents tracking
 * - Real-time monitoring
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Shield, 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  TrendingUp, 
  TrendingDown,
  RefreshCw,
  Activity,
  Lock,
  Users,
  Database,
  FileText,
  BarChart3,
  Settings,
  Download,
  Bell,
  Play,
  X,
  ExternalLink
} from 'lucide-react';
import { useAuthStore } from '../../store/authStore';

// Interfaces per TypeScript
interface SecurityOverview {
  tenant_id: string;
  current_score: number;
  current_risk: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  total_issues: number;
  critical_issues: number;
  last_audit: string;
  previous_score?: number;
  open_incidents: number;
  pending_recommendations: number;
}

interface SecurityCategory {
  risk: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  score: number;
  issues: SecurityIssue[];
  summary: string;
}

interface SecurityIssue {
  title: string;
  description: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  recommendation: string;
  affectedItems: number;
}

interface SecurityAuditReport {
  overview: {
    securityScore: number;
    riskLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
    lastAuditDate: string;
    nextAuditDue: string;
    totalIssues: number;
    criticalIssues: number;
  };
  categories: {
    credentials: SecurityCategory;
    database: SecurityCategory;
    nodes: SecurityCategory;
    filesystem: SecurityCategory;
    instance: SecurityCategory;
    access: SecurityCategory;
  };
  recommendations: SecurityRecommendation[];
  complianceStatus: ComplianceStatus;
}

interface SecurityRecommendation {
  priority: 'HIGH' | 'MEDIUM' | 'LOW';
  category: string;
  title: string;
  description: string;
  effort: 'LOW' | 'MEDIUM' | 'HIGH';
  impact: 'LOW' | 'MEDIUM' | 'HIGH';
}

interface ComplianceStatus {
  gdpr: { compliant: boolean; score: number; issues: string[]; };
  soc2: { compliant: boolean; score: number; issues: string[]; };
  iso27001: { compliant: boolean; score: number; issues: string[]; };
}

const SecurityPremiumPage: React.FC = () => {
  // State management
  const [overview, setOverview] = useState<SecurityOverview[]>([]);
  const [auditReport, setAuditReport] = useState<SecurityAuditReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [auditLoading, setAuditLoading] = useState(false);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([
    'credentials', 'database', 'nodes', 'filesystem', 'instance'
  ]);
  const [activeTab, setActiveTab] = useState<'overview' | 'audit' | 'compliance' | 'incidents'>('overview');
  const [error, setError] = useState<string>('');
  const [selectedIssue, setSelectedIssue] = useState<SecurityIssue | null>(null);
  const [showIssueModal, setShowIssueModal] = useState(false);
  
  const { user } = useAuthStore();
  const tenantId = user?.tenantId || 'default_tenant';
  const navigate = useNavigate();

  // Fetch security overview
  const fetchSecurityOverview = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch('http://localhost:3001/api/security/overview');
      if (response.ok) {
        const data = await response.json();
        setOverview(data.data || []);
      } else {
        throw new Error('Failed to fetch security overview');
      }
    } catch (error) {
      console.error('❌ Errore caricamento security overview:', error);
      setError('Errore nel caricamento dei dati di sicurezza');
    } finally {
      setLoading(false);
    }
  };

  // Generate security audit
  const generateSecurityAudit = async () => {
    setAuditLoading(true);
    setError('');
    try {
      const categoriesParam = selectedCategories.join(',');
      const response = await fetch(
        `http://localhost:3001/api/tenant/${tenantId}/security/audit?categories=${categoriesParam}`, 
        { 
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        setAuditReport(data.data);
        // Refresh overview dopo audit
        fetchSecurityOverview();
      } else {
        const errorData = await response.json();
        setError(errorData.details || 'Security audit temporaneamente non disponibile');
        console.error('❌ Security audit failed:', errorData);
      }
    } catch (error) {
      console.error('❌ Errore security audit:', error);
      setError('Errore durante esecuzione audit. Riprova più tardi.');
    } finally {
      setAuditLoading(false);
    }
  };

  // Load data on component mount
  useEffect(() => {
    fetchSecurityOverview();
  }, []);

  // Helper functions
  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'LOW': return 'text-green-400 bg-green-400/10';
      case 'MEDIUM': return 'text-yellow-400 bg-yellow-400/10';
      case 'HIGH': return 'text-orange-400 bg-orange-400/10';
      case 'CRITICAL': return 'text-red-400 bg-red-400/10';
      default: return 'text-gray-400 bg-gray-400/10';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-400';
    if (score >= 70) return 'text-yellow-400';
    if (score >= 50) return 'text-orange-400';
    return 'text-red-400';
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'CRITICAL': return <AlertTriangle className="w-4 h-4 text-red-400" />;
      case 'HIGH': return <XCircle className="w-4 h-4 text-orange-400" />;
      case 'MEDIUM': return <AlertTriangle className="w-4 h-4 text-yellow-400" />;
      case 'LOW': return <CheckCircle className="w-4 h-4 text-green-400" />;
      default: return <Shield className="w-4 h-4 text-gray-400" />;
    }
  };

  // Handle issue click
  const handleIssueClick = (issue: SecurityIssue) => {
    setSelectedIssue(issue);
    setShowIssueModal(true);
  };

  const closeIssueModal = () => {
    setShowIssueModal(false);
    setSelectedIssue(null);
  };

  const navigateToWorkflow = (workflowName?: string) => {
    if (workflowName) {
      // Naviga alla pagina workflow con search parameter per il nome
      navigate(`/workflows?search=${encodeURIComponent(workflowName)}`);
    } else {
      // Naviga alla pagina workflow generica
      navigate('/workflows');
    }
    closeIssueModal();
  };

  // Current tenant overview data
  const currentTenantOverview = overview.find(o => o.tenant_id === tenantId);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Shield className="w-8 h-8 text-green-400" />
            Compliance & Security Audit
            <span className="text-xs px-2 py-1 bg-blue-500/20 text-blue-400 rounded-full font-medium">
              Powered by Revisia
            </span>
          </h1>
          <p className="text-gray-400 mt-1">
            Audit di conformità, risk assessment e reportistica GDPR/SOC2/ISO27001
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchSecurityOverview}
            disabled={loading}
            className="px-4 py-2 bg-gray-800 text-gray-300 rounded-lg hover:bg-gray-700 
                     disabled:opacity-50 flex items-center gap-2 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Aggiorna
          </button>
          <button
            onClick={generateSecurityAudit}
            disabled={auditLoading || selectedCategories.length === 0}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 
                     disabled:opacity-50 flex items-center gap-2 transition-colors"
          >
            <Play className={`w-4 h-4 ${auditLoading ? 'animate-pulse' : ''}`} />
            {auditLoading ? 'Eseguendo...' : 'Esegui Audit'}
          </button>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-4 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />
          <div>
            <h3 className="text-red-400 font-medium">Avviso</h3>
            <p className="text-red-300 text-sm">{error}</p>
          </div>
        </div>
      )}

      {/* Tabs Navigation */}
      <div className="border-b border-gray-800">
        <nav className="flex gap-6">
          {[
            { key: 'overview', label: 'Overview', icon: BarChart3 },
            { key: 'audit', label: 'Security Audit', icon: Shield },
            { key: 'compliance', label: 'Compliance', icon: FileText },
            { key: 'incidents', label: 'Incidents', icon: Bell }
          ].map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setActiveTab(key as any)}
              className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${
                activeTab === key
                  ? 'border-green-400 text-green-400'
                  : 'border-transparent text-gray-400 hover:text-gray-300'
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Security Score Cards */}
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Main Security Score */}
            <div className="lg:col-span-2 bg-black border border-gray-800 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-white">Security Score</h2>
                <Shield className="w-6 h-6 text-green-400" />
              </div>
              {currentTenantOverview ? (
                <>
                  <div className="flex items-end gap-2 mb-2">
                    <span className={`text-4xl font-bold ${getScoreColor(currentTenantOverview.current_score)}`}>
                      {currentTenantOverview.current_score}
                    </span>
                    <span className="text-gray-400 text-lg">/100</span>
                    {currentTenantOverview.previous_score && (
                      <div className="ml-2 flex items-center gap-1">
                        {currentTenantOverview.current_score > currentTenantOverview.previous_score ? (
                          <TrendingUp className="w-4 h-4 text-green-400" />
                        ) : (
                          <TrendingDown className="w-4 h-4 text-red-400" />
                        )}
                        <span className="text-sm text-gray-400">
                          {Math.abs(currentTenantOverview.current_score - currentTenantOverview.previous_score)}
                        </span>
                      </div>
                    )}
                  </div>
                  <div className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${getRiskColor(currentTenantOverview.current_risk)}`}>
                    {currentTenantOverview.current_risk} RISK
                  </div>
                </>
              ) : (
                <div className="text-center py-8">
                  <Shield className="w-12 h-12 text-gray-600 mx-auto mb-3" />
                  <p className="text-gray-400">Nessun audit disponibile</p>
                  <p className="text-gray-500 text-sm">Esegui il primo security audit per visualizzare il punteggio</p>
                </div>
              )}
            </div>

            {/* Issues Summary */}
            <div className="bg-black border border-gray-800 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">Issues</h3>
                <AlertTriangle className="w-5 h-5 text-yellow-400" />
              </div>
              {currentTenantOverview ? (
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Total</span>
                    <span className="text-white font-medium">{currentTenantOverview.total_issues}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Critical</span>
                    <span className="text-red-400 font-medium">{currentTenantOverview.critical_issues}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Open Incidents</span>
                    <span className="text-orange-400 font-medium">{currentTenantOverview.open_incidents}</span>
                  </div>
                </div>
              ) : (
                <p className="text-gray-500 text-center">No data</p>
              )}
            </div>

            {/* Recommendations */}
            <div className="bg-black border border-gray-800 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">Actions</h3>
                <Settings className="w-5 h-5 text-green-400" />
              </div>
              {currentTenantOverview ? (
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Pending</span>
                    <span className="text-blue-400 font-medium">{currentTenantOverview.pending_recommendations}</span>
                  </div>
                  <div className="pt-3 border-t border-gray-800">
                    <button 
                      onClick={() => setActiveTab('audit')}
                      className="w-full px-3 py-2 bg-green-600/20 text-green-400 rounded-lg hover:bg-green-600/30 transition-colors text-sm"
                    >
                      View Recommendations
                    </button>
                  </div>
                </div>
              ) : (
                <p className="text-gray-500 text-center">No data</p>
              )}
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-black border border-gray-800 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Quick Actions</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <button
                onClick={() => setActiveTab('audit')}
                className="p-4 bg-gray-900 hover:bg-gray-800 rounded-lg transition-colors text-left"
              >
                <Shield className="w-6 h-6 text-green-400 mb-2" />
                <h3 className="text-white font-medium">Run Security Audit</h3>
                <p className="text-gray-400 text-sm">Comprehensive security analysis</p>
              </button>
              
              <button
                onClick={() => setActiveTab('compliance')}
                className="p-4 bg-gray-900 hover:bg-gray-800 rounded-lg transition-colors text-left"
              >
                <FileText className="w-6 h-6 text-blue-400 mb-2" />
                <h3 className="text-white font-medium">Compliance Report</h3>
                <p className="text-gray-400 text-sm">GDPR, SOC2, ISO27001 status</p>
              </button>

              <button className="p-4 bg-gray-900 hover:bg-gray-800 rounded-lg transition-colors text-left">
                <Users className="w-6 h-6 text-purple-400 mb-2" />
                <h3 className="text-white font-medium">Access Review</h3>
                <p className="text-gray-400 text-sm">User permissions audit</p>
              </button>

              <button className="p-4 bg-gray-900 hover:bg-gray-800 rounded-lg transition-colors text-left">
                <Download className="w-6 h-6 text-yellow-400 mb-2" />
                <h3 className="text-white font-medium">Export Report</h3>
                <p className="text-gray-400 text-sm">Download security reports</p>
              </button>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'audit' && (
        <div className="space-y-6">
          {/* Audit Configuration */}
          <div className="bg-black border border-gray-800 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Security Audit Configuration</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Audit Categories
                </label>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                  {[
                    { key: 'credentials', label: 'Credentials', icon: Lock },
                    { key: 'database', label: 'Database', icon: Database },
                    { key: 'nodes', label: 'Nodes', icon: Activity },
                    { key: 'filesystem', label: 'Filesystem', icon: FileText },
                    { key: 'instance', label: 'Instance', icon: Shield }
                  ].map(({ key, label, icon: Icon }) => (
                    <label key={key} className="flex items-center gap-2 p-3 bg-gray-900 rounded-lg cursor-pointer hover:bg-gray-800">
                      <input
                        type="checkbox"
                        checked={selectedCategories.includes(key)}
                        onChange={(e) => {
                          console.log(`🔄 Categoria ${key} ${e.target.checked ? 'selezionata' : 'deselezionata'}`);
                          if (e.target.checked) {
                            const newCategories = [...selectedCategories, key];
                            console.log('🎯 Nuove categorie:', newCategories);
                            setSelectedCategories(newCategories);
                          } else {
                            const newCategories = selectedCategories.filter(c => c !== key);
                            console.log('🎯 Nuove categorie:', newCategories);
                            setSelectedCategories(newCategories);
                          }
                        }}
                        className="w-4 h-4 rounded border-2 border-gray-600 bg-gray-800 text-green-500 focus:ring-green-500 focus:border-green-500"
                      />
                      <Icon className="w-4 h-4 text-gray-400" />
                      <span className="text-sm text-gray-300">{label}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="flex justify-end">
                <button
                  onClick={generateSecurityAudit}
                  disabled={auditLoading || selectedCategories.length === 0}
                  className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 
                           disabled:opacity-50 flex items-center gap-2 transition-colors"
                >
                  <Shield className={`w-4 h-4 ${auditLoading ? 'animate-pulse' : ''}`} />
                  {auditLoading ? 'Eseguendo Audit...' : 'Esegui Security Audit'}
                </button>
              </div>
            </div>
          </div>

          {/* Audit Results */}
          {auditReport && (
            <div className="space-y-6">
              {/* Audit Overview */}
              <div className="bg-black border border-gray-800 rounded-lg p-6">
                <h2 className="text-lg font-semibold text-white mb-4">Audit Results</h2>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="text-center">
                    <div className={`text-3xl font-bold mb-1 ${getScoreColor(auditReport.overview.securityScore)}`}>
                      {auditReport.overview.securityScore}
                    </div>
                    <div className="text-gray-400 text-sm">Security Score</div>
                  </div>
                  
                  <div className="text-center">
                    <div className={`px-3 py-1 rounded-full text-sm font-medium inline-block ${getRiskColor(auditReport.overview.riskLevel)}`}>
                      {auditReport.overview.riskLevel} RISK
                    </div>
                    <div className="text-gray-400 text-sm mt-1">Risk Level</div>
                  </div>
                  
                  <div className="text-center">
                    <div className="text-3xl font-bold mb-1 text-red-400">
                      {auditReport.overview.criticalIssues}
                    </div>
                    <div className="text-gray-400 text-sm">Critical Issues</div>
                  </div>
                </div>
              </div>

              {/* Category Breakdown */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {Object.entries(auditReport.categories).map(([categoryName, category]) => (
                  <div key={categoryName} className="bg-black border border-gray-800 rounded-lg p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-white capitalize">{categoryName}</h3>
                      <div className={`px-2 py-1 rounded-full text-xs font-medium ${getRiskColor(category.risk)}`}>
                        {category.risk}
                      </div>
                    </div>
                    
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-gray-400">Score</span>
                        <span className={`font-medium ${getScoreColor(category.score)}`}>
                          {category.score}/100
                        </span>
                      </div>
                      
                      <div className="text-gray-300 text-sm">
                        {category.summary}
                      </div>
                      
                      {category.issues.length > 0 && (
                        <div className="space-y-2">
                          <div className="text-sm font-medium text-gray-300">Issues ({category.issues.length})</div>
                          {category.issues.slice(0, 2).map((issue, index) => (
                            <div 
                              key={index} 
                              className="flex items-start gap-2 p-2 bg-gray-900 rounded cursor-pointer hover:bg-gray-800 transition-colors border border-transparent hover:border-green-500/30"
                              onClick={() => handleIssueClick(issue)}
                            >
                              {getSeverityIcon(issue.severity)}
                              <div className="flex-1">
                                <div className="text-sm text-white font-medium hover:text-green-400 transition-colors">
                                  {issue.title}
                                </div>
                                <div className="text-xs text-gray-400">{issue.affectedItems} items affected</div>
                              </div>
                              <div className="text-xs text-green-400 opacity-0 hover:opacity-100 transition-opacity">
                                Click for details →
                              </div>
                            </div>
                          ))}
                          {category.issues.length > 2 && (
                            <div className="text-xs text-gray-500">
                              +{category.issues.length - 2} more issues
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {!auditReport && !auditLoading && (
            <div className="bg-black border border-gray-800 rounded-lg p-8 text-center">
              <Shield className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <h3 className="text-white text-lg font-medium mb-2">No Audit Results</h3>
              <p className="text-gray-400 mb-4">
                Configura le categorie di audit e clicca "Esegui Security Audit" per iniziare l'analisi di sicurezza.
              </p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'compliance' && (
        <div className="bg-black border border-gray-800 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Compliance Status</h2>
          {auditReport?.complianceStatus ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {Object.entries(auditReport.complianceStatus).map(([standard, status]) => (
                <div key={standard} className="bg-gray-900 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-white font-medium uppercase">{standard}</h3>
                    {status.compliant ? (
                      <CheckCircle className="w-5 h-5 text-green-400" />
                    ) : (
                      <XCircle className="w-5 h-5 text-red-400" />
                    )}
                  </div>
                  <div className={`text-2xl font-bold mb-2 ${getScoreColor(status.score)}`}>
                    {status.score}%
                  </div>
                  <div className={`text-xs px-2 py-1 rounded-full ${status.compliant ? 'bg-green-400/20 text-green-400' : 'bg-red-400/20 text-red-400'}`}>
                    {status.compliant ? 'Compliant' : 'Non-Compliant'}
                  </div>
                  {status.issues.length > 0 && (
                    <div className="mt-3 space-y-1">
                      <div className="text-xs text-gray-400">Issues:</div>
                      {status.issues.slice(0, 3).map((issue, index) => (
                        <div key={index} className="text-xs text-gray-300">• {issue}</div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <FileText className="w-12 h-12 text-gray-600 mx-auto mb-3" />
              <p className="text-gray-400">Nessun report di compliance disponibile</p>
              <p className="text-gray-500 text-sm">Esegui un security audit per generare i report</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'incidents' && (
        <div className="bg-black border border-gray-800 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Security Incidents</h2>
          <div className="text-center py-8">
            <Bell className="w-12 h-12 text-gray-600 mx-auto mb-3" />
            <p className="text-gray-400">Nessun incidente di sicurezza registrato</p>
            <p className="text-gray-500 text-sm">Gli incidenti vengono rilevati automaticamente durante gli audit</p>
          </div>
        </div>
      )}

      {/* Issue Details Modal */}
      {showIssueModal && selectedIssue && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-black border border-gray-800 rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="flex items-start justify-between p-6 border-b border-gray-800">
              <div className="flex items-start gap-3">
                {getSeverityIcon(selectedIssue.severity)}
                <div>
                  <h2 className="text-xl font-semibold text-white mb-2">{selectedIssue.title}</h2>
                  <div className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${
                    selectedIssue.severity === 'CRITICAL' ? 'bg-red-500/20 text-red-400' :
                    selectedIssue.severity === 'HIGH' ? 'bg-orange-500/20 text-orange-400' :
                    selectedIssue.severity === 'MEDIUM' ? 'bg-yellow-500/20 text-yellow-400' :
                    'bg-green-500/20 text-green-400'
                  }`}>
                    {selectedIssue.severity} SEVERITY
                  </div>
                </div>
              </div>
              <button 
                onClick={closeIssueModal}
                className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-gray-400" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 space-y-6">
              {/* Description */}
              <div>
                <h3 className="text-lg font-medium text-white mb-3">Description</h3>
                <p className="text-gray-300">{selectedIssue.description}</p>
              </div>

              {/* Location */}
              {selectedIssue.location && (
                <div>
                  <h3 className="text-lg font-medium text-white mb-3">Location</h3>
                  <div className="bg-gray-900 rounded-lg p-4">
                    <div className="flex items-center gap-2 text-sm">
                      <span className="text-gray-400 capitalize">{selectedIssue.location.type}:</span>
                      <span className="text-green-400 font-mono">{selectedIssue.location.name}</span>
                    </div>
                    {selectedIssue.location.id && (
                      <div className="flex items-center gap-2 text-sm mt-1">
                        <span className="text-gray-400">ID:</span>
                        <span className="text-gray-300 font-mono">{selectedIssue.location.id}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Recommendation */}
              <div>
                <h3 className="text-lg font-medium text-white mb-3">Recommended Actions</h3>
                <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-4">
                  <p className="text-blue-300">{selectedIssue.recommendation}</p>
                </div>
              </div>

              {/* Impact */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-900 rounded-lg p-4">
                  <h4 className="text-white font-medium mb-2">Affected Items</h4>
                  <div className="text-2xl font-bold text-red-400">{selectedIssue.affectedItems}</div>
                </div>
                <div className="bg-gray-900 rounded-lg p-4">
                  <h4 className="text-white font-medium mb-2">Priority</h4>
                  <div className={`text-2xl font-bold ${
                    selectedIssue.severity === 'CRITICAL' ? 'text-red-400' :
                    selectedIssue.severity === 'HIGH' ? 'text-orange-400' :
                    selectedIssue.severity === 'MEDIUM' ? 'text-yellow-400' :
                    'text-green-400'
                  }`}>
                    {selectedIssue.severity === 'CRITICAL' ? '🔥 URGENT' :
                     selectedIssue.severity === 'HIGH' ? '⚠️ HIGH' :
                     selectedIssue.severity === 'MEDIUM' ? '📋 MEDIUM' :
                     '✅ LOW'}
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3 pt-4 border-t border-gray-800">
                {selectedIssue.location?.type === 'workflow' && (
                  <button 
                    onClick={() => navigateToWorkflow(selectedIssue.location?.name)}
                    className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center gap-2"
                  >
                    <ExternalLink className="w-4 h-4" />
                    View Workflow
                  </button>
                )}
                {selectedIssue.location?.type === 'node' && (
                  <button 
                    onClick={() => navigateToWorkflow()}
                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
                  >
                    <ExternalLink className="w-4 h-4" />
                    View Workflows
                  </button>
                )}
                <button 
                  onClick={() => navigator.clipboard.writeText(JSON.stringify(selectedIssue, null, 2))}
                  className="flex-1 px-4 py-2 bg-gray-800 text-gray-300 rounded-lg hover:bg-gray-700 transition-colors flex items-center justify-center gap-2"
                >
                  <Download className="w-4 h-4" />
                  Copy Issue
                </button>
                <button 
                  onClick={closeIssueModal}
                  className="px-6 py-2 bg-gray-900 text-gray-400 rounded-lg hover:bg-gray-800 transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SecurityPremiumPage;
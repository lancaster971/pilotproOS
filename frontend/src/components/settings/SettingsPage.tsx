/**
 * Settings Page - Configurazione sistema per deployment remoto
 * 
 * Features:
 * - Configurazione connessione backend remoto
 * - Generazione e gestione API Keys
 * - Test connettività automatico
 * - Auto-discovery backend
 */

import React, { useState, useEffect } from 'react';
import { 
  Settings, 
  Server, 
  Key, 
  TestTube, 
  AlertCircle, 
  CheckCircle, 
  Loader2, 
  Plus, 
  Trash2, 
  RefreshCw,
  Copy,
  Eye,
  EyeOff,
  Power,
  RotateCcw,
  Activity,
  Terminal,
  Monitor,
  Clock,
  Database,
  Edit,
  Calendar,
  Shield,
  Lock
} from 'lucide-react';
import { settingsAPI, systemAPI } from '../../services/api';

interface ConnectionConfig {
  backendUrl: string;
  connectionTimeout: number;
  retryAttempts: number;
  features: Record<string, boolean>;
}

interface ApiKeyInfo {
  id: string;
  keyName: string;
  keyPrefix: string;
  keyType: string;
  permissions: string[];
  scopes: string[];
  expiresAt?: string;
  lastUsedAt?: string;
  usageCount: number;
  isActive: boolean;
  createdAt: string;
}

interface ConnectivityResult {
  success: boolean;
  responseTime?: number;
  error?: string;
}

interface ServiceStatus {
  name: string;
  status: 'running' | 'stopped' | 'unknown';
  pid?: number;
  port?: number;
  message?: string;
}

interface SystemStatus {
  overall: 'healthy' | 'degraded' | 'down';
  services: ServiceStatus[];
  lastCheck: string;
}

const SettingsPage: React.FC = () => {
  const [config, setConfig] = useState<ConnectionConfig>({
    backendUrl: 'http://localhost:3001',
    connectionTimeout: 5000,
    retryAttempts: 3,
    features: {}
  });
  
  const [apiKeys, setApiKeys] = useState<ApiKeyInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isTesting, setIsTesting] = useState(false);
  const [connectivityResult, setConnectivityResult] = useState<ConnectivityResult | null>(null);
  const [showNewKeyModal, setShowNewKeyModal] = useState(false);
  const [newKeyData, setNewKeyData] = useState({ name: '', type: 'frontend-read' });
  const [generatedKey, setGeneratedKey] = useState<string>('');
  const [showGeneratedKey, setShowGeneratedKey] = useState(false);
  const [showRenewModal, setShowRenewModal] = useState(false);
  const [renewKeyData, setRenewKeyData] = useState({ keyId: '', keyName: '', days: 30 });
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');
  
  // API Key Update state
  const [currentApiKey, setCurrentApiKey] = useState<string>('');
  const [newApiKey, setNewApiKey] = useState<string>('');
  const [adminPassword, setAdminPassword] = useState<string>('');
  const [isUpdatingKey, setIsUpdatingKey] = useState(false);
  
  // System Management state
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [isLoadingSystem, setIsLoadingSystem] = useState(false);
  const [isManagingService, setIsManagingService] = useState<string>('');

  useEffect(() => {
    loadSettings();
    loadSystemStatus();
    // Carica API key attuale da environment o localStorage
    const envApiKey = import.meta.env.VITE_API_KEY;
    const storedApiKey = localStorage.getItem('pilotpro_api_key');
    setCurrentApiKey(storedApiKey || envApiKey || '');
  }, []);

  const loadSettings = async () => {
    try {
      setIsLoading(true);
      const [configResponse, keysResponse] = await Promise.all([
        settingsAPI.getConnection(),
        settingsAPI.getApiKeys()
      ]);
      
      if (configResponse.data.success) {
        setConfig(configResponse.data.data);
      }
      
      if (keysResponse.data.success) {
        setApiKeys(keysResponse.data.data);
      }
    } catch (error: any) {
      setError(`Errore caricamento impostazioni: ${error.response?.data?.message || error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const testConnectivity = async (url?: string) => {
    setIsTesting(true);
    setConnectivityResult(null);
    
    try {
      const response = await settingsAPI.testConnection(
        url || config.backendUrl,
        config.connectionTimeout
      );
      
      setConnectivityResult(response.data.data);
    } catch (error: any) {
      setConnectivityResult({
        success: false,
        error: error.response?.data?.message || error.message
      });
    } finally {
      setIsTesting(false);
    }
  };

  const saveConnectionConfig = async () => {
    try {
      setError('');
      setSuccess('');
      
      const response = await settingsAPI.updateConnection(config);
      
      if (response.data.success) {
        setSuccess('Configurazione salvata con successo');
        setConfig(response.data.data);
        if (response.data.connectivity) {
          setConnectivityResult(response.data.connectivity);
        }
      }
    } catch (error: any) {
      setError(`Errore salvataggio: ${error.response?.data?.message || error.message}`);
    }
  };

  const generateApiKey = async () => {
    try {
      setError('');
      
      const response = await settingsAPI.generateApiKey({
        name: newKeyData.name,
        type: newKeyData.type,
        permissions: newKeyData.type === 'admin-full' ? ['*'] : ['read'],
        scopes: newKeyData.type === 'frontend-read' ? ['read'] : ['read', 'write']
      });
      
      if (response.data.success) {
        setGeneratedKey(response.data.data.apiKey);
        setShowGeneratedKey(true);
        setShowNewKeyModal(false);
        setNewKeyData({ name: '', type: 'frontend-read' });
        loadSettings(); // Ricarica lista
        setSuccess('API Key generata con successo');
      }
    } catch (error: any) {
      setError(`Errore generazione API Key: ${error.response?.data?.message || error.message}`);
    }
  };

  const revokeApiKey = async (keyId: string) => {
    try {
      await settingsAPI.revokeApiKey(keyId);
      loadSettings();
      setSuccess('API Key revocata con successo');
    } catch (error: any) {
      setError(`Errore revoca API Key: ${error.response?.data?.message || error.message}`);
    }
  };

  const renewApiKey = async () => {
    try {
      setError('');
      const expiresInSeconds = renewKeyData.days * 24 * 60 * 60; // Convert days to seconds
      
      const response = await settingsAPI.renewApiKey(renewKeyData.keyId, expiresInSeconds);
      
      if (response.data.success) {
        setSuccess(`API Key "${renewKeyData.keyName}" rinnovata per ${renewKeyData.days} giorni`);
        setShowRenewModal(false);
        setRenewKeyData({ keyId: '', keyName: '', days: 30 });
        loadSettings();
      }
    } catch (error: any) {
      setError(`Errore rinnovo API Key: ${error.response?.data?.message || error.message}`);
    }
  };

  const openRenewModal = (keyId: string, keyName: string) => {
    setRenewKeyData({ keyId, keyName, days: 30 });
    setShowRenewModal(true);
  };

  const updateApiKey = async () => {
    try {
      setIsUpdatingKey(true);
      setError('');
      
      // Validazione input
      if (!newApiKey.trim()) {
        setError('API Key richiesta');
        return;
      }
      
      if (!adminPassword.trim()) {
        setError('Password admin richiesta per autorizzazione');
        return;
      }

      // Chiamata backend per validazione e aggiornamento
      const updateResponse = await settingsAPI.updateClientApiKey(newApiKey, adminPassword);
      
      if (!updateResponse.data.success) {
        setError(`Aggiornamento fallito: ${updateResponse.data.message}`);
        return;
      }

      // Hot-swap locale (salva nuova API key)
      const oldApiKey = currentApiKey;
      localStorage.setItem('pilotpro_api_key', newApiKey);
      localStorage.setItem('pilotpro_api_key_updated_at', new Date().toISOString());
      localStorage.setItem('pilotpro_api_key_backup', oldApiKey); // Backup per rollback
      
      setCurrentApiKey(newApiKey);
      setSuccess('API Key aggiornata con successo! Sistema riconfigurato automaticamente.');
      
      // Reset form
      setNewApiKey('');
      setAdminPassword('');
      
      // Test finale con nuova key
      setTimeout(async () => {
        try {
          await loadSettings(); // Test che funzioni
        } catch (error) {
          // Rollback automatico se fallisce
          localStorage.setItem('pilotpro_api_key', oldApiKey);
          setCurrentApiKey(oldApiKey);
          setError('Rollback automatico: nuova API key non funziona');
        }
      }, 1000);
      
    } catch (error: any) {
      setError(`Errore aggiornamento API Key: ${error.response?.data?.message || error.message}`);
    } finally {
      setIsUpdatingKey(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setSuccess('Copiato negli appunti');
  };

  // System Management functions
  const loadSystemStatus = async () => {
    try {
      setIsLoadingSystem(true);
      const response = await systemAPI.getStatus();
      if (response.data.success) {
        setSystemStatus(response.data.data);
      }
    } catch (error: any) {
      console.error('Errore caricamento stato sistema:', error);
    } finally {
      setIsLoadingSystem(false);
    }
  };

  const manageService = async (action: 'start' | 'stop' | 'restart', service: string = 'all') => {
    try {
      setIsManagingService(`${action}-${service}`);
      setError('');
      
      let response;
      if (action === 'restart') {
        response = await systemAPI.restartSystem();
      } else if (action === 'start') {
        response = await systemAPI.startService(service as 'backend' | 'frontend' | 'all');
      } else {
        response = await systemAPI.stopService(service as 'backend' | 'frontend' | 'all');
      }
      
      if (response.data.success) {
        setSuccess(response.data.message);
        // Ricarica stato dopo azione
        setTimeout(() => {
          loadSystemStatus();
        }, action === 'restart' ? 5000 : 2000);
      }
    } catch (error: any) {
      setError(`Errore ${action} servizio: ${error.response?.data?.message || error.message}`);
    } finally {
      setIsManagingService('');
    }
  };

  const getServiceStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'text-green-400';
      case 'stopped': return 'text-red-400'; 
      case 'unknown': return 'text-yellow-400';
      default: return 'text-gray-400';
    }
  };

  const getServiceStatusBg = (status: string) => {
    switch (status) {
      case 'running': return 'bg-green-500/20 border-green-500';
      case 'stopped': return 'bg-red-500/20 border-red-500';
      case 'unknown': return 'bg-yellow-500/20 border-yellow-500';
      default: return 'bg-gray-500/20 border-gray-500';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('it-IT');
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-green-500" />
        <span className="ml-2 text-gray-300">Caricamento impostazioni...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center">
            <Settings className="mr-3 h-8 w-8 text-green-500" />
            Impostazioni Sistema
          </h1>
          <p className="text-gray-400 mt-1">
            Configura connessione backend remoto e gestisci API Keys
          </p>
        </div>
      </div>

      {/* Alerts */}
      {error && (
        <div className="bg-red-500/20 border border-red-500 rounded-lg p-4 flex items-center">
          <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
          <span className="text-red-300">{error}</span>
        </div>
      )}

      {success && (
        <div className="bg-green-500/20 border border-green-500 rounded-lg p-4 flex items-center">
          <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
          <span className="text-green-300">{success}</span>
        </div>
      )}

      {/* Connection Configuration */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
        <div className="flex items-center mb-4">
          <Server className="h-6 w-6 text-green-500 mr-2" />
          <h2 className="text-xl font-semibold text-white">Configurazione Connessione</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              URL Backend
            </label>
            <input
              type="url"
              value={config.backendUrl}
              onChange={(e) => setConfig({ ...config, backendUrl: e.target.value })}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-green-500"
              placeholder="http://localhost:3001"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Timeout (ms)
            </label>
            <input
              type="number"
              value={config.connectionTimeout}
              onChange={(e) => setConfig({ ...config, connectionTimeout: parseInt(e.target.value) || 5000 })}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-green-500"
              min="1000"
              max="30000"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Tentativi Retry
            </label>
            <input
              type="number"
              value={config.retryAttempts}
              onChange={(e) => setConfig({ ...config, retryAttempts: parseInt(e.target.value) || 3 })}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-green-500"
              min="0"
              max="10"
            />
          </div>
        </div>

        {/* Connectivity Test */}
        <div className="flex items-center space-x-4 mb-4">
          <button
            onClick={() => testConnectivity()}
            disabled={isTesting}
            className="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white rounded-lg transition-colors"
          >
            {isTesting ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <TestTube className="h-4 w-4 mr-2" />
            )}
            Test Connettività
          </button>

          <button
            onClick={saveConnectionConfig}
            className="flex items-center px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
          >
            <CheckCircle className="h-4 w-4 mr-2" />
            Salva Configurazione
          </button>
        </div>

        {/* Connectivity Result */}
        {connectivityResult && (
          <div className={`p-4 rounded-lg border ${
            connectivityResult.success 
              ? 'bg-green-500/20 border-green-500' 
              : 'bg-red-500/20 border-red-500'
          }`}>
            <div className="flex items-center">
              {connectivityResult.success ? (
                <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
              ) : (
                <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
              )}
              <span className={connectivityResult.success ? 'text-green-300' : 'text-red-300'}>
                {connectivityResult.success 
                  ? `Connessione riuscita (${connectivityResult.responseTime}ms)`
                  : `Connessione fallita: ${connectivityResult.error}`
                }
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Security API Key Update */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
        <div className="flex items-center mb-4">
          <Shield className="h-6 w-6 text-green-500 mr-2" />
          <h2 className="text-xl font-semibold text-white">Sicurezza API Key</h2>
        </div>

        <div className="mb-4 p-3 bg-yellow-500/20 border border-yellow-500 rounded-lg">
          <p className="text-yellow-300 text-sm">
            ⚠️ <strong>Per clienti con frontend remoto:</strong> Se la tua API key è compromessa, aggiornala qui senza accesso al codice
          </p>
        </div>

        {/* Current API Key */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-300 mb-2">
            API Key Attuale
          </label>
          <div className="flex items-center">
            <code className="bg-gray-900 rounded px-3 py-2 text-green-400 font-mono text-sm flex-1 mr-2">
              {currentApiKey ? `${currentApiKey.substring(0, 15)}***` : 'Nessuna API key configurata'}
            </code>
            {currentApiKey && (
              <button
                onClick={() => copyToClipboard(currentApiKey)}
                className="flex items-center px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm transition-colors"
              >
                <Copy className="h-3 w-3 mr-1" />
                Copia
              </button>
            )}
          </div>
          {currentApiKey && (
            <p className="text-xs text-gray-400 mt-1">
              Ultima modifica: {localStorage.getItem('pilotpro_api_key_updated_at') 
                ? new Date(localStorage.getItem('pilotpro_api_key_updated_at')!).toLocaleString('it-IT')
                : 'Non disponibile'
              }
            </p>
          )}
        </div>

        {/* Update API Key */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Nuova API Key
            </label>
            <input
              type="text"
              value={newApiKey}
              onChange={(e) => setNewApiKey(e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-green-500 font-mono text-sm"
              placeholder="fr_your_new_api_key_here..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Password SuperAdmin
            </label>
            <input
              type="password"
              value={adminPassword}
              onChange={(e) => setAdminPassword(e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-green-500"
              placeholder="Conferma con password admin"
            />
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <button
            onClick={updateApiKey}
            disabled={isUpdatingKey || !newApiKey.trim() || !adminPassword.trim()}
            className="flex items-center px-4 py-2 bg-orange-600 hover:bg-orange-700 disabled:bg-gray-600 text-white rounded-lg transition-colors"
          >
            {isUpdatingKey ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <Lock className="h-4 w-4 mr-2" />
            )}
            Aggiorna API Key
          </button>

          <div className="text-xs text-gray-400">
            <p>✅ Hot-swap automatico (nessun riavvio)</p>
            <p>✅ Rollback automatico se fallisce</p>
            <p>✅ Test connettività incluso</p>
          </div>
        </div>
      </div>

      {/* API Keys Management */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <Key className="h-6 w-6 text-green-500 mr-2" />
            <h2 className="text-xl font-semibold text-white">API Keys</h2>
          </div>
          <button
            onClick={() => setShowNewKeyModal(true)}
            className="flex items-center px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
          >
            <Plus className="h-4 w-4 mr-2" />
            Genera API Key
          </button>
        </div>

        {/* API Keys List */}
        <div className="space-y-2">
          {apiKeys.length === 0 ? (
            <p className="text-gray-400 text-center py-4">Nessuna API Key presente</p>
          ) : (
            apiKeys.map((key) => (
              <div key={key.id} className="bg-gray-700 rounded-lg p-3 border border-gray-600">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center mb-1">
                      <span className="font-medium text-white text-sm">{key.keyName}</span>
                      <span className={`ml-2 px-2 py-0.5 text-xs rounded-full ${
                        key.isActive ? 'bg-green-500/20 text-green-300' : 'bg-red-500/20 text-red-300'
                      }`}>
                        {key.isActive ? 'Attiva' : 'Revocata'}
                      </span>
                    </div>
                    <div className="text-xs text-gray-400 flex items-center space-x-4">
                      <span>Tipo: <span className="text-gray-300">{key.keyType}</span></span>
                      <span>Prefisso: <span className="font-mono text-gray-300">{key.keyPrefix}***</span></span>
                      <span>Utilizzi: <span className="text-gray-300">{key.usageCount}</span></span>
                    </div>
                  </div>
                  <div className="flex items-center space-x-1">
                    {key.isActive && (
                      <>
                        <button
                          onClick={() => openRenewModal(key.id, key.keyName)}
                          className="flex items-center px-2 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs transition-colors"
                        >
                          <Calendar className="h-3 w-3 mr-1" />
                          Rinnova
                        </button>
                        <button
                          onClick={() => revokeApiKey(key.id)}
                          className="flex items-center px-2 py-1 bg-red-600 hover:bg-red-700 text-white rounded text-xs transition-colors"
                        >
                          <Trash2 className="h-3 w-3 mr-1" />
                          Revoca
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* System Management */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <Activity className="h-6 w-6 text-green-500 mr-2" />
            <h2 className="text-xl font-semibold text-white">Gestione Servizi Sistema</h2>
          </div>
          <button
            onClick={loadSystemStatus}
            disabled={isLoadingSystem}
            className="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white rounded-lg transition-colors"
          >
            {isLoadingSystem ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <RefreshCw className="h-4 w-4 mr-2" />
            )}
            Aggiorna Stato
          </button>
        </div>

        {/* System Overview */}
        {systemStatus && (
          <div className={`p-3 rounded-lg border mb-3 ${
            systemStatus.overall === 'healthy' 
              ? 'bg-green-500/20 border-green-500' 
              : systemStatus.overall === 'degraded'
              ? 'bg-yellow-500/20 border-yellow-500'
              : 'bg-red-500/20 border-red-500'
          }`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <Activity className={`h-4 w-4 mr-2 ${
                  systemStatus.overall === 'healthy' ? 'text-green-400' : 
                  systemStatus.overall === 'degraded' ? 'text-yellow-400' : 'text-red-400'
                }`} />
                <span className="font-medium text-white text-sm">
                  Sistema: {systemStatus.overall === 'healthy' ? 'Sano' : 
                           systemStatus.overall === 'degraded' ? 'Degradato' : 'Non Funzionante'}
                </span>
              </div>
              <span className="text-xs text-gray-300">
                Ultimo check: {new Date(systemStatus.lastCheck).toLocaleTimeString('it-IT')}
              </span>
            </div>
          </div>
        )}

        {/* Services Status */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
          {systemStatus?.services.map((service) => (
            <div key={service.name} className={`p-3 rounded-lg border ${getServiceStatusBg(service.status)}`}>
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center">
                  {service.name === 'database' && <Database className="h-4 w-4 mr-2" />}
                  {service.name === 'backend' && <Server className="h-4 w-4 mr-2" />}
                  {service.name === 'frontend' && <Monitor className="h-4 w-4 mr-2" />}
                  {service.name === 'scheduler' && <Clock className="h-4 w-4 mr-2" />}
                  <span className="font-medium text-white capitalize text-sm">{service.name}</span>
                </div>
                <span className={`text-xs font-medium ${getServiceStatusColor(service.status)}`}>
                  {service.status === 'running' ? 'Attivo' : 
                   service.status === 'stopped' ? 'Fermo' : 'Sconosciuto'}
                </span>
              </div>
              <p className="text-xs text-gray-300">{service.message}</p>
              <div className="flex items-center space-x-3 text-xs text-gray-400 mt-1">
                {service.pid && <span>PID: {service.pid}</span>}
                {service.port && <span>Porta: {service.port}</span>}
              </div>
            </div>
          ))}
        </div>

        {/* Service Controls */}
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => manageService('start', 'all')}
            disabled={isManagingService.includes('start')}
            className="flex items-center px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white rounded-lg transition-colors"
          >
            {isManagingService === 'start-all' ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <Power className="h-4 w-4 mr-2" />
            )}
            Avvia Sistema
          </button>

          <button
            onClick={() => manageService('restart', 'all')}
            disabled={isManagingService.includes('restart')}
            className="flex items-center px-4 py-2 bg-yellow-600 hover:bg-yellow-700 disabled:bg-gray-600 text-white rounded-lg transition-colors"
          >
            {isManagingService === 'restart-all' ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <RotateCcw className="h-4 w-4 mr-2" />
            )}
            Riavvia Sistema
          </button>

          <button
            onClick={() => manageService('start', 'backend')}
            disabled={isManagingService.includes('backend')}
            className="flex items-center px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white rounded-lg transition-colors text-sm"
          >
            {isManagingService === 'start-backend' ? (
              <Loader2 className="h-3 w-3 animate-spin mr-2" />
            ) : (
              <Server className="h-3 w-3 mr-2" />
            )}
            Backend
          </button>

          <button
            onClick={() => manageService('start', 'frontend')}
            disabled={isManagingService.includes('frontend')}
            className="flex items-center px-3 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 text-white rounded-lg transition-colors text-sm"
          >
            {isManagingService === 'start-frontend' ? (
              <Loader2 className="h-3 w-3 animate-spin mr-2" />
            ) : (
              <Monitor className="h-3 w-3 mr-2" />
            )}
            Frontend
          </button>
        </div>

        {/* Quick Links */}
        {systemStatus?.overall === 'healthy' && (
          <div className="mt-4 p-4 bg-gray-700 rounded-lg">
            <h3 className="text-sm font-medium text-white mb-2">Accesso Rapido</h3>
            <div className="flex flex-wrap gap-2">
              <a
                href="http://localhost:5173"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center px-3 py-1 bg-green-600 hover:bg-green-700 text-white rounded text-sm transition-colors"
              >
                <Monitor className="h-3 w-3 mr-1" />
                Dashboard
              </a>
              <a
                href="http://localhost:3001/api-docs"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm transition-colors"
              >
                <Terminal className="h-3 w-3 mr-1" />
                API Docs
              </a>
              <a
                href="http://localhost:3001/health"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center px-3 py-1 bg-cyan-600 hover:bg-cyan-700 text-white rounded text-sm transition-colors"
              >
                <Activity className="h-3 w-3 mr-1" />
                Health Check
              </a>
            </div>
          </div>
        )}
      </div>

      {/* New API Key Modal */}
      {showNewKeyModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-white mb-4">Genera Nuova API Key</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Nome API Key
                </label>
                <input
                  type="text"
                  value={newKeyData.name}
                  onChange={(e) => setNewKeyData({ ...newKeyData, name: e.target.value })}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-green-500"
                  placeholder="Frontend Production Key"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Tipo API Key
                </label>
                <select
                  value={newKeyData.type}
                  onChange={(e) => setNewKeyData({ ...newKeyData, type: e.target.value })}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-green-500"
                >
                  <option value="frontend-read">Frontend Read-Only</option>
                  <option value="frontend-full">Frontend Full Access</option>
                  <option value="frontend-limited">Frontend Limited</option>
                  <option value="admin-full">Admin Full Access</option>
                </select>
              </div>
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowNewKeyModal(false)}
                className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
              >
                Annulla
              </button>
              <button
                onClick={generateApiKey}
                disabled={!newKeyData.name.trim()}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white rounded-lg transition-colors"
              >
                Genera
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Generated API Key Modal */}
      {showGeneratedKey && generatedKey && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 w-full max-w-lg">
            <h3 className="text-lg font-semibold text-white mb-4">API Key Generata</h3>
            
            <div className="bg-yellow-500/20 border border-yellow-500 rounded-lg p-4 mb-4">
              <p className="text-yellow-300 text-sm">
                ⚠️ Questa è l'unica volta che vedrai questa API key. Copiala e conservala in un luogo sicuro.
              </p>
            </div>

            <div className="bg-gray-900 rounded-lg p-4 mb-4">
              <div className="flex items-center justify-between">
                <code className="text-green-400 font-mono text-sm break-all flex-1 mr-2">
                  {generatedKey}
                </code>
                <button
                  onClick={() => copyToClipboard(generatedKey)}
                  className="flex items-center px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm transition-colors"
                >
                  <Copy className="h-3 w-3 mr-1" />
                  Copia
                </button>
              </div>
            </div>

            <div className="flex justify-end">
              <button
                onClick={() => {
                  setShowGeneratedKey(false);
                  setGeneratedKey('');
                }}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
              >
                Ho Copiato la Key
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Renew API Key Modal */}
      {showRenewModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-white mb-4">Rinnova API Key</h3>
            
            <div className="mb-4 p-3 bg-blue-500/20 border border-blue-500 rounded-lg">
              <p className="text-blue-300 text-sm">
                <strong>{renewKeyData.keyName}</strong>
              </p>
              <p className="text-blue-300/80 text-xs">
                Estendi la scadenza di questa API key
              </p>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Estendi per (giorni)
                </label>
                <select
                  value={renewKeyData.days}
                  onChange={(e) => setRenewKeyData({ ...renewKeyData, days: parseInt(e.target.value) })}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-green-500"
                >
                  <option value={1}>1 giorno</option>
                  <option value={7}>7 giorni</option>
                  <option value={30}>30 giorni</option>
                  <option value={90}>90 giorni</option>
                  <option value={365}>1 anno</option>
                </select>
              </div>
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowRenewModal(false)}
                className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
              >
                Annulla
              </button>
              <button
                onClick={renewApiKey}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
              >
                Rinnova
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SettingsPage;
// PilotProOS AI Business Chat - Conversational Interface for Business Processes
// Integrates with existing MCP server from PilotProMT
import React, { useState, useEffect, useRef } from 'react';
import { 
  MessageCircle, Send, Bot, User, BarChart, FileText, Zap, 
  TrendingUp, AlertCircle, CheckCircle, Clock, ArrowRight 
} from 'lucide-react';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { aiAgentAPI, formatters } from '../../services/pilotpros-api';

interface ChatMessage {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  visualData?: {
    charts?: Array<{
      type: string;
      title: string;
      data: any;
    }>;
    table?: {
      headers: string[];
      rows: any[][];
    };
    metrics?: Array<{
      label: string;
      value: string | number;
      trend?: 'up' | 'down' | 'stable';
    }>;
  };
  actionSuggestions?: string[];
  quickActions?: Array<{
    label: string;
    query: string;
  }>;
  timestamp: Date;
}

const AIBusinessChat: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [sessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Welcome message on first load
  useEffect(() => {
    setMessages([{
      id: 'welcome',
      type: 'assistant',
      content: '👋 **Ciao! Sono il tuo Assistente per i Processi Aziendali.**\n\nPosso aiutarti a gestire e monitorare i tuoi processi automatizzati attraverso conversazione naturale.\n\n**Esempi di cosa puoi chiedermi:**\n• "Mostra i processi attivi"\n• "Report di questa settimana"\n• "Quanti clienti abbiamo processato oggi?"\n• "Ci sono errori da controllare?"\n• "Come stanno andando le performance?"',
      quickActions: [
        { label: '📊 Stato Processi', query: 'Mostra lo stato dei miei processi aziendali' },
        { label: '📈 Report Settimanale', query: 'Crea un report delle performance di questa settimana' },
        { label: '⚠️ Controlla Errori', query: 'Ci sono errori o problemi da controllare?' },
        { label: '🎯 Analytics Business', query: 'Mostra le analisi business e metriche principali' }
      ],
      timestamp: new Date()
    }]);
  }, []);
  
  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  const sendMessage = async (query: string) => {
    if (!query.trim()) return;
    
    // Add user message
    const userMessage: ChatMessage = {
      id: `user_${Date.now()}`,
      type: 'user',
      content: query,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    
    try {
      // Call AI Agent API (integrates with MCP server)
      const startTime = Date.now();
      const aiResponse = await aiAgentAPI.sendChatMessage(query, {
        sessionId,
        userId: 'business-user',
        startTime
      });
      
      // Add AI response with rich content
      const assistantMessage: ChatMessage = {
        id: `assistant_${Date.now()}`,
        type: 'assistant',
        content: aiResponse.textResponse,
        visualData: aiResponse.visualData,
        actionSuggestions: aiResponse.actionSuggestions,
        quickActions: aiResponse.quickActions,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      
    } catch (error) {
      console.error('AI Agent error:', error);
      
      // Error handling with helpful fallback
      const errorMessage: ChatMessage = {
        id: `error_${Date.now()}`,
        type: 'system',
        content: '🚨 **Assistente temporaneamente non disponibile**\n\nProva con queste richieste base:\n• "Mostra processi attivi"\n• "Report settimanale"\n• "Stato sistema"',
        quickActions: [
          { label: '📊 Processi Attivi', query: 'Mostra i processi attivi' },
          { label: '📈 Report Base', query: 'Report settimanale' },
          { label: '🔍 Stato Sistema', query: 'Stato del sistema' }
        ],
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorMessage]);
    }
    
    setIsLoading(false);
  };
  
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(inputMessage);
    }
  };
  
  const handleQuickAction = (query: string) => {
    sendMessage(query);
  };
  
  return (
    <Card className={`ai-chat-container ${isExpanded ? 'h-96' : 'h-16'} transition-all duration-300 bg-black border-green-500`}>
      {/* Chat Header */}
      <div 
        className="chat-header flex items-center justify-between p-4 cursor-pointer hover:bg-gray-900 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center space-x-3">
          <div className="relative">
            <Bot className="w-6 h-6 text-green-500" />
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full animate-pulse" />
          </div>
          <div>
            <h3 className="font-semibold text-white">Assistente Processi Aziendali</h3>
            <p className="text-xs text-gray-400">
              {isLoading ? 'Sto pensando...' : 'Pronto ad aiutarti'}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-xs text-green-500 font-medium">AI Powered</span>
          <ArrowRight className={`w-4 h-4 text-gray-400 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
        </div>
      </div>
      
      {/* Chat Messages */}
      {isExpanded && (
        <>
          <div className="chat-messages flex-1 overflow-y-auto p-4 space-y-4 max-h-64">
            {messages.map((message) => (
              <ChatMessageComponent 
                key={message.id} 
                message={message}
                onQuickAction={handleQuickAction}
              />
            ))}
            
            {isLoading && (
              <div className="flex items-center space-x-3 p-3 bg-gray-900 rounded-lg">
                <Bot className="w-5 h-5 text-green-500" />
                <div className="typing-animation flex space-x-1">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
                <span className="text-gray-400 text-sm">Elaborando la tua richiesta...</span>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
          
          {/* Chat Input */}
          <div className="chat-input border-t border-gray-800 p-4">
            <div className="flex items-end space-x-3">
              <div className="flex-1">
                <textarea
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Chiedi qualcosa sui tuoi processi aziendali..."
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white placeholder-gray-400 resize-none focus:outline-none focus:border-green-500 transition-colors"
                  rows={1}
                  disabled={isLoading}
                />
              </div>
              <Button 
                onClick={() => sendMessage(inputMessage)}
                disabled={!inputMessage.trim() || isLoading}
                className="bg-green-600 hover:bg-green-700 text-white px-4 py-2"
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>
            
            {/* Example queries */}
            <div className="flex flex-wrap gap-2 mt-3">
              {[
                'Processi attivi',
                'Report oggi',
                'Errori recenti'
              ].map((example) => (
                <button
                  key={example}
                  onClick={() => setInputMessage(example)}
                  className="text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 px-2 py-1 rounded transition-colors"
                >
                  {example}
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </Card>
  );
};

// Individual message component
const ChatMessageComponent: React.FC<{
  message: ChatMessage;
  onQuickAction: (query: string) => void;
}> = ({ message, onQuickAction }) => {
  return (
    <div className={`message flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[80%] ${
        message.type === 'user' 
          ? 'bg-green-600 text-white rounded-l-lg rounded-tr-lg' 
          : 'bg-gray-900 text-white rounded-r-lg rounded-tl-lg border border-gray-700'
      } p-3`}>
        
        {/* Message header */}
        <div className="flex items-center space-x-2 mb-2">
          {message.type === 'user' ? (
            <User className="w-4 h-4" />
          ) : message.type === 'assistant' ? (
            <Bot className="w-4 h-4 text-green-500" />
          ) : (
            <AlertCircle className="w-4 h-4 text-yellow-500" />
          )}
          <span className="text-xs opacity-70">
            {message.timestamp.toLocaleTimeString('it-IT', { 
              hour: '2-digit', 
              minute: '2-digit' 
            })}
          </span>
        </div>
        
        {/* Message content */}
        <div className="message-text">
          {message.content.split('\n').map((line, i) => (
            <p key={i} className={`${line.startsWith('**') ? 'font-semibold' : ''} ${i > 0 ? 'mt-1' : ''}`}>
              {line.replace(/\*\*(.*?)\*\*/g, '$1')}
            </p>
          ))}
        </div>
        
        {/* Visual data (charts, tables, metrics) */}
        {message.visualData && (
          <div className="visual-data mt-4 space-y-3">
            {/* Metrics display */}
            {message.visualData.metrics && (
              <div className="metrics-grid grid grid-cols-2 gap-3">
                {message.visualData.metrics.map((metric, i) => (
                  <div key={i} className="bg-gray-800 p-2 rounded text-center">
                    <div className="text-lg font-bold text-white">{metric.value}</div>
                    <div className="text-xs text-gray-400">{metric.label}</div>
                    {metric.trend && (
                      <TrendingUp className={`w-3 h-3 inline-block ml-1 ${
                        metric.trend === 'up' ? 'text-green-500' : 
                        metric.trend === 'down' ? 'text-red-500' : 'text-gray-500'
                      }`} />
                    )}
                  </div>
                ))}
              </div>
            )}
            
            {/* Table display */}
            {message.visualData.table && (
              <div className="table-container bg-gray-800 rounded overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-gray-700">
                      {message.visualData.table.headers.map((header, i) => (
                        <th key={i} className="px-3 py-2 text-left text-xs font-semibold text-gray-300">
                          {header}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {message.visualData.table.rows.slice(0, 5).map((row, i) => (
                      <tr key={i} className="border-t border-gray-700">
                        {row.map((cell, j) => (
                          <td key={j} className="px-3 py-2 text-xs text-gray-300">
                            {cell}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
                {message.visualData.table.rows.length > 5 && (
                  <div className="p-2 text-center text-xs text-gray-500">
                    +{message.visualData.table.rows.length - 5} più righe
                  </div>
                )}
              </div>
            )}
          </div>
        )}
        
        {/* Quick action buttons */}
        {message.quickActions && (
          <div className="quick-actions mt-4 space-y-2">
            <p className="text-xs text-gray-400 mb-2">🎯 Azioni rapide:</p>
            <div className="flex flex-wrap gap-2">
              {message.quickActions.map((action, i) => (
                <Button
                  key={i}
                  onClick={() => onQuickAction(action.query)}
                  variant="outline"
                  size="sm"
                  className="text-xs bg-gray-800 border-gray-600 text-gray-300 hover:bg-gray-700 hover:border-green-500"
                >
                  {action.label}
                </Button>
              ))}
            </div>
          </div>
        )}
        
        {/* Action suggestions */}
        {message.actionSuggestions && (
          <div className="action-suggestions mt-4">
            <p className="text-xs text-gray-400 mb-2">💡 Altre domande utili:</p>
            <div className="space-y-1">
              {message.actionSuggestions.slice(0, 3).map((suggestion, i) => (
                <button
                  key={i}
                  onClick={() => onQuickAction(suggestion)}
                  className="block w-full text-left text-xs text-green-400 hover:text-green-300 hover:bg-gray-800 p-2 rounded transition-colors"
                >
                  "{suggestion}"
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Standalone AI Assistant Page
export const AIAssistantPage: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center space-x-3">
            <Bot className="w-8 h-8 text-green-500" />
            <span>Assistente IA Processi</span>
          </h1>
          <p className="text-gray-400 mt-2">
            Gestisci i tuoi processi aziendali attraverso conversazione naturale
          </p>
        </div>
        <div className="flex items-center space-x-2 text-sm">
          <CheckCircle className="w-4 h-4 text-green-500" />
          <span className="text-green-500">AI Online</span>
        </div>
      </div>
      
      {/* AI Chat Interface */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Chat */}
        <div className="lg:col-span-2">
          <AIBusinessChat />
        </div>
        
        {/* AI Assistant Info Panel */}
        <div className="space-y-4">
          <Card className="bg-black border-green-500 p-4">
            <h3 className="font-semibold text-white mb-3 flex items-center">
              <Zap className="w-4 h-4 text-green-500 mr-2" />
              Cosa posso fare per te
            </h3>
            <div className="space-y-2 text-sm text-gray-300">
              <div className="flex items-start space-x-2">
                <BarChart className="w-4 h-4 text-green-500 mt-0.5" />
                <span>Analizzare performance dei processi</span>
              </div>
              <div className="flex items-start space-x-2">
                <FileText className="w-4 h-4 text-green-500 mt-0.5" />
                <span>Generare report personalizzati</span>
              </div>
              <div className="flex items-start space-x-2">
                <AlertCircle className="w-4 h-4 text-green-500 mt-0.5" />
                <span>Identificare e risolvere problemi</span>
              </div>
              <div className="flex items-start space-x-2">
                <TrendingUp className="w-4 h-4 text-green-500 mt-0.5" />
                <span>Suggerire ottimizzazioni</span>
              </div>
            </div>
          </Card>
          
          <Card className="bg-black border-green-500 p-4">
            <h3 className="font-semibold text-white mb-3">🎯 Esempi di domande</h3>
            <div className="space-y-2 text-sm">
              {[
                "Mostra i processi più utilizzati",
                "Quanto tempo abbiamo risparmiato?",
                "Ci sono colli di bottiglia?",
                "Report performance del mese",
                "Suggerimenti per migliorare"
              ].map((example, i) => (
                <div key={i} className="text-gray-400 italic">
                  "{example}"
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default AIBusinessChat;
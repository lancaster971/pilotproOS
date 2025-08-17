// PilotProOS AI Assistant Page - Standalone AI conversational interface
import React from 'react';
import { Bot, Zap, BarChart, FileText, AlertCircle, TrendingUp, CheckCircle } from 'lucide-react';
import { Card } from '../ui/card';
import AIBusinessChat from './AIBusinessChat';

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
import React from 'react'

export const DatabasePage: React.FC = () => {
  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold text-white mb-6">🗄️ Database</h1>
      <div className="bg-gray-900 rounded-lg p-6 text-white">
        <h2 className="text-xl mb-4">Database Page</h2>
        <p className="text-green-400">✅ Database page caricata correttamente</p>
        <p className="text-yellow-400">🚧 Contenuto in fase di ripristino...</p>
      </div>
    </div>
  )
}
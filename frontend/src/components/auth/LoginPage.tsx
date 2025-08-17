import React, { useState } from 'react'
import { Navigate } from 'react-router-dom'
import { Button } from '../ui/button'
import { Input } from '../ui/input'
import { Label } from '../ui/label'
import { Card } from '../ui/card'
import { useToast } from '../../hooks/use-toast'
import { Eye, EyeOff, Loader2 } from 'lucide-react'
import BackToTopButton from './BackToTopButton'
import { useAuthStore } from '../../store/authStore'

// Costanti di testo
const LOGIN_TITLE = "Bentornato"
const LOGIN_DESCRIPTION = "Accedi per gestire i tuoi Ai Agent."
const BRAND_TITLE = "I primi Ai business Agent in Italia"
const BRAND_DESCRIPTION = "Trasformiamo il modo di lavorare delle aziende attraverso l'intelligenza artificiale. Benvenuto!"

export const LoginPage: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [formData, setFormData] = useState({
    email: 'admin@pilotpro.local',
    password: 'admin123',
  })
  const { toast } = useToast()
  const { login, isAuthenticated } = useAuthStore()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    setTimeout(async () => {
      setIsLoading(false)
      try {
        await login(formData.email, formData.password)
        toast({
          title: "Login effettuato con successo!",
          description: "Benvenuto in PilotPro Control Center",
        })
      } catch (error: any) {
        toast({
          title: "Errore di login",
          description: error.message || "Credenziali non valide",
          variant: "destructive",
        })
      }
    }, 1000)
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }

  return (
    <div className="min-h-screen">
      <div className="flex min-h-screen">
        {/* Left Side - Integrations Gradient with Brand Texts */}
        <div className="hidden lg:flex lg:w-1/2 relative bg-black overflow-hidden">
          {/* Same gradient as integrations section */}
          <div className="absolute inset-0 bg-gradient-to-br from-yellow-400/30 via-lime-400/25 to-green-400/30"></div>
          <div className="absolute inset-0 bg-gradient-to-tr from-green-400/20 via-transparent to-yellow-400/20"></div>
          
          <div className="relative z-10 flex flex-col justify-center items-center text-center px-12 w-full">
            <div className="max-w-2xl">
              {/* Logo PilotPro Testuale */}
              <div className="mb-8">
                <h2 className="text-3xl sm:text-4xl md:text-5xl font-light tracking-tight">
                  <span className="text-white">Pilot</span>
                  <span className="text-green-400">Pro</span>
                </h2>
              </div>
              
              <h1 className="text-4xl sm:text-5xl md:text-6xl text-white mb-6 tracking-tight leading-tight" style={{ fontWeight: '300' }}>
                {BRAND_TITLE}
              </h1>
              <p className="text-lg md:text-xl text-gray-300 leading-relaxed" style={{ fontWeight: '200' }}>
                {BRAND_DESCRIPTION}
              </p>
            </div>
          </div>
        </div>

        {/* Right Side - Black Background with Auth Form */}
        <div className="w-full lg:w-1/2 bg-black flex flex-col">
          <div className="flex-1 flex items-center justify-center px-8 py-12">
            <div className="w-full max-w-md">
              <Card className="bg-gray-900 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 border border-gray-700 p-6 text-left relative">
                <div>
                  <h3 className="text-lg md:text-xl text-white mb-4" style={{ fontWeight: '300' }}>
                    {LOGIN_TITLE}
                  </h3>
                  <p className="text-base text-gray-300 leading-relaxed mb-6" style={{ fontWeight: '200' }}>
                    {LOGIN_DESCRIPTION}
                  </p>
                  <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="email" className="text-sm text-gray-300" style={{ fontWeight: '300' }}>
                        Email
                      </Label>
                      <Input
                        id="email"
                        name="email"
                        type="email"
                        placeholder="inserisci la tua email"
                        value={formData.email}
                        onChange={handleInputChange}
                        required
                        className="bg-gray-800 border-gray-700 text-white placeholder-gray-500 focus:border-green-400 focus:ring-green-400"
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="password" className="text-sm text-gray-300" style={{ fontWeight: '300' }}>
                        Password
                      </Label>
                      <div className="relative">
                        <Input
                          id="password"
                          name="password"
                          type={showPassword ? "text" : "password"}
                          placeholder="inserisci la tua password"
                          value={formData.password}
                          onChange={handleInputChange}
                          required
                          className="bg-gray-800 border-gray-700 text-white placeholder-gray-500 focus:border-green-400 focus:ring-green-400 pr-10"
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-gray-700"
                          onClick={() => setShowPassword(!showPassword)}
                        >
                          {showPassword ? (
                            <EyeOff className="h-4 w-4 text-gray-400" />
                          ) : (
                            <Eye className="h-4 w-4 text-gray-400" />
                          )}
                        </Button>
                      </div>
                    </div>
                    
                    <Button 
                      type="submit" 
                      className="w-full bg-green-600 hover:bg-green-700 text-white rounded-lg shadow-lg"
                      disabled={isLoading}
                    >
                      {isLoading ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Accesso in corso...
                        </>
                      ) : (
                        "Accedi"
                      )}
                    </Button>
                  </form>
                  
                </div>
              </Card>
            </div>
          </div>
        </div>
      </div>
      <BackToTopButton />
    </div>
  )
}
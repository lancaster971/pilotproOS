import React, { useState } from 'react'
import { Navigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { Mail, Lock, Eye, EyeOff, AlertCircle, Loader2 } from 'lucide-react'
import { useAuthStore } from '../../store/authStore'
import { cn } from '../../lib/utils'
import toast from 'react-hot-toast'

const loginSchema = z.object({
  email: z.string().email('Email non valida'),
  password: z.string().min(6, 'Password deve essere almeno 6 caratteri'),
})

type LoginFormData = z.infer<typeof loginSchema>

export const LoginPage: React.FC = () => {
  const [showPassword, setShowPassword] = useState(false)
  const { login, isAuthenticated, isLoading, error } = useAuthStore()
  
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: 'admin@pilotpro.com',
      password: 'admin123',
    },
  })
  
  const onSubmit = async (data: LoginFormData) => {
    try {
      await login(data.email, data.password)
      toast.success('Login effettuato con successo!')
    } catch (error: any) {
      toast.error(error.message || 'Credenziali non valide')
    }
  }
  
  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }
  
  return (
    <div className="min-h-screen flex relative overflow-hidden">
      {/* Animated background */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary-600 via-secondary-600 to-primary-700">
        <div className="absolute inset-0 bg-black/20" />
        {/* Animated orbs */}
        <div className="absolute top-20 left-20 w-72 h-72 bg-primary-400 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-float" />
        <div className="absolute top-40 right-20 w-72 h-72 bg-secondary-400 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-float animation-delay-200" />
        <div className="absolute -bottom-20 left-40 w-72 h-72 bg-pink-400 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-float animation-delay-300" />
      </div>
      
      {/* Login form */}
      <div className="relative z-10 flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md animate-fade-in">
          {/* Logo and title */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-white/10 backdrop-blur-lg mb-4">
              <div className="animated-gradient w-14 h-14 rounded-xl flex items-center justify-center">
                <span className="text-white font-bold text-2xl">PP</span>
              </div>
            </div>
            <h1 className="text-3xl font-bold text-white mb-2">
              PilotPro Control Center
            </h1>
            <p className="text-white/70">
              Sistema Premium Multi-Tenant
            </p>
          </div>
          
          {/* Form card */}
          <div className="glass-card rounded-2xl p-8 backdrop-blur-2xl bg-white/10 border border-white/20">
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              {/* Email field */}
              <div>
                <label className="block text-sm font-medium text-white/90 mb-2">
                  Email
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-white/50" />
                  <input
                    {...register('email')}
                    type="email"
                    className={cn(
                      'w-full pl-10 pr-4 py-3 bg-white/10 border rounded-lg',
                      'text-white placeholder-white/50',
                      'focus:outline-none focus:ring-2 focus:ring-primary-400 focus:border-transparent',
                      'backdrop-blur-lg',
                      errors.email
                        ? 'border-red-400'
                        : 'border-white/20 hover:border-white/30'
                    )}
                    placeholder="admin@example.com"
                  />
                </div>
                {errors.email && (
                  <p className="mt-1 text-sm text-red-400 flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />
                    {errors.email.message}
                  </p>
                )}
              </div>
              
              {/* Password field */}
              <div>
                <label className="block text-sm font-medium text-white/90 mb-2">
                  Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-white/50" />
                  <input
                    {...register('password')}
                    type={showPassword ? 'text' : 'password'}
                    className={cn(
                      'w-full pl-10 pr-12 py-3 bg-white/10 border rounded-lg',
                      'text-white placeholder-white/50',
                      'focus:outline-none focus:ring-2 focus:ring-primary-400 focus:border-transparent',
                      'backdrop-blur-lg',
                      errors.password
                        ? 'border-red-400'
                        : 'border-white/20 hover:border-white/30'
                    )}
                    placeholder="••••••••"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-white/50 hover:text-white/70"
                  >
                    {showPassword ? (
                      <EyeOff className="h-5 w-5" />
                    ) : (
                      <Eye className="h-5 w-5" />
                    )}
                  </button>
                </div>
                {errors.password && (
                  <p className="mt-1 text-sm text-red-400 flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />
                    {errors.password.message}
                  </p>
                )}
              </div>
              
              {/* Remember me & Forgot password */}
              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    className="w-4 h-4 bg-white/10 border-white/20 rounded focus:ring-2 focus:ring-primary-400"
                  />
                  <span className="text-sm text-white/70">Ricordami</span>
                </label>
                <button
                  type="button"
                  className="text-sm text-white/70 hover:text-white transition-colors"
                >
                  Password dimenticata?
                </button>
              </div>
              
              {/* Error message */}
              {error && (
                <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                  <p className="text-sm text-red-400 flex items-center gap-2">
                    <AlertCircle className="h-4 w-4" />
                    {error}
                  </p>
                </div>
              )}
              
              {/* Submit button */}
              <button
                type="submit"
                disabled={isLoading}
                className={cn(
                  'w-full py-3 px-4 rounded-lg font-medium transition-all duration-200',
                  'bg-white text-primary-600 hover:bg-white/90',
                  'focus:outline-none focus:ring-2 focus:ring-white/50',
                  'disabled:opacity-50 disabled:cursor-not-allowed',
                  'transform hover:scale-[1.02] active:scale-[0.98]'
                )}
              >
                {isLoading ? (
                  <span className="flex items-center justify-center gap-2">
                    <Loader2 className="h-5 w-5 animate-spin" />
                    Accesso in corso...
                  </span>
                ) : (
                  'Accedi'
                )}
              </button>
            </form>
            
            {/* Demo credentials */}
            <div className="mt-6 p-4 rounded-lg bg-white/5 border border-white/10">
              <p className="text-xs text-white/60 mb-2">Credenziali Demo:</p>
              <div className="space-y-1">
                <p className="text-xs text-white/80">
                  <span className="font-mono">admin@pilotpro.com</span>
                </p>
                <p className="text-xs text-white/80">
                  <span className="font-mono">admin123</span>
                </p>
              </div>
            </div>
          </div>
          
          {/* Footer */}
          <div className="mt-8 text-center">
            <p className="text-sm text-white/50">
              © 2025 PilotPro Control Center • v1.0.0
            </p>
          </div>
        </div>
      </div>
      
      {/* Right side - Feature showcase */}
      <div className="hidden lg:flex lg:w-1/2 items-center justify-center p-12 relative">
        <div className="max-w-lg">
          <h2 className="text-4xl font-bold text-white mb-6">
            Gestione Completa dei tuoi Workflow
          </h2>
          <div className="space-y-4">
            {[
              'Multi-tenant architecture con isolamento completo',
              'Dashboard real-time con metriche avanzate',
              'Scheduler automatico per sincronizzazione',
              'Sistema di alert e monitoring integrato',
              'Backup automatico e disaster recovery',
              'API REST completa con documentazione Swagger',
            ].map((feature, index) => (
              <div
                key={index}
                className="flex items-start gap-3 animate-slide-up"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <div className="mt-1 w-5 h-5 rounded-full bg-white/20 flex items-center justify-center flex-shrink-0">
                  <div className="w-2 h-2 rounded-full bg-white" />
                </div>
                <p className="text-white/90">{feature}</p>
              </div>
            ))}
          </div>
          
          {/* Stats */}
          <div className="mt-12 grid grid-cols-3 gap-6">
            {[
              { value: '99.9%', label: 'Uptime' },
              { value: '10ms', label: 'Response' },
              { value: '24/7', label: 'Support' },
            ].map((stat, index) => (
              <div
                key={index}
                className="text-center animate-scale-in"
                style={{ animationDelay: `${600 + index * 100}ms` }}
              >
                <p className="text-3xl font-bold text-white">{stat.value}</p>
                <p className="text-sm text-white/60">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
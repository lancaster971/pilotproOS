"use client";

import React, { useState } from 'react';
import Link from 'next/link';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from './components/ui/card';
import { useToast } from './hooks/use-toast';
import { Eye, EyeOff, Loader2 } from 'lucide-react';
import Header from "./components/Header";
import BackToTopButton from "./components/BackToTopButton";

const LOGIN_TITLE = "Bentornato";
const LOGIN_DESCRIPTION = "Accedi per gestire i tuoi Ai Agent.";
const SIGNUP_TITLE = "Crea un Account";
const SIGNUP_DESCRIPTION = "Registrati per iniziare a trasformare la tua azienda con PilotPro.";
const BRAND_TITLE = "I primi Ai business Agent in Italia";
const BRAND_DESCRIPTION = "Trasformiamo il modo di lavorare delle aziende attraverso l'intelligenza artificiale. Benvenuto!";

const Auth = () => {
  const [isSignUp, setIsSignUp] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    setTimeout(() => {
      setIsLoading(false);
      if (isSignUp) {
        // Reindirizza a prenota-demo per la registrazione
        window.location.href = '/prenota-demo';
      } else {
        toast({
          title: "Funzionalità in arrivo",
          description: "Il sistema di login sarà disponibile presto. Per ora prenota una demo!",
        });
      }
    }, 1000);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  return (
    <div className="min-h-screen">
      <Header />
      
      <div className="flex min-h-screen pt-16">
        {/* Left Side - Integrations Gradient with Brand Texts */}
        <div className="hidden lg:flex lg:w-1/2 relative bg-black overflow-hidden">
          {/* Same gradient as integrations section */}
          <div className="absolute inset-0 bg-gradient-to-br from-yellow-400/30 via-lime-400/25 to-green-400/30"></div>
          <div className="absolute inset-0 bg-gradient-to-tr from-green-400/20 via-transparent to-yellow-400/20"></div>
          
          <div className="relative z-10 flex flex-col justify-center items-center text-center px-12 w-full">
            <div className="max-w-2xl">
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
                    {isSignUp ? SIGNUP_TITLE : LOGIN_TITLE}
                  </h3>
                  <p className="text-base text-gray-300 leading-relaxed mb-6" style={{ fontWeight: '200' }}>
                    {isSignUp ? SIGNUP_DESCRIPTION : LOGIN_DESCRIPTION}
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
                          placeholder={isSignUp ? "crea una password sicura" : "inserisci la tua password"}
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
                          {isSignUp ? "Creazione account..." : "Accesso in corso..."}
                        </>
                      ) : (
                        isSignUp ? "Crea Account" : "Accedi"
                      )}
                    </Button>
                  </form>
                  
                  <div className="flex flex-col space-y-4 mt-6">
                  <div className="text-center">
                    <span className="text-sm text-gray-400" style={{ fontWeight: '200' }}>
                      {isSignUp ? "Hai già un account?" : "Non hai un account?"}
                    </span>
                    {isSignUp ? (
                      <Button
                        variant="link"
                        className="p-0 ml-1 text-green-400"
                        onClick={() => setIsSignUp(!isSignUp)}
                      >
                        Accedi
                      </Button>
                    ) : (
                      <Link
                        href="/prenota-demo"
                        className="p-0 ml-1 text-green-400"
                      >
                        Registrati
                      </Link>
                    )}
                  </div>
                  
                  {isSignUp && (
                    <p className="text-xs text-gray-500 text-center" style={{ fontWeight: '200' }}>
                      Registrandoti accetti i nostri{' '}
                      <Link href="/terms-of-service" className="text-green-400 hover:text-green-300">
                        termini di servizio
                      </Link>{' '}
                      e la{' '}
                      <Link href="/privacy-policy" className="text-green-400 hover:text-green-300">
                        privacy policy
                      </Link>
                    </p>
                  )}
                  </div>
                </div>
              </Card>
            </div>
          </div>
        </div>
      </div>
      <BackToTopButton />
    </div>
  );
};

export default Auth;
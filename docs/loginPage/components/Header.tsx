"use client";

import { useState, useRef } from "react";
import { Menu, X, ChevronDown, Settings, Brain, Users, Zap, BarChart3, Shield, Calculator, HelpCircle, Phone, Lock, BookOpen, Cpu, FileText } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button } from "./ui/button";

const Header = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);
  const closeTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pathname = usePathname();

  // AI Products (colonna sinistra)
  const aiProducts = [
    { name: "Ai Agent", href: "/agent-template", icon: Brain, description: "Assistenti virtuali personalizzati" },
    { name: "PilotPro", href: "/pilotpro", icon: Cpu, description: "Sistema operativo Ai" },
    { name: "Sicurezza Enterprise", href: "/sicurezza", icon: Shield, description: "Protezione dati e compliance" }
  ];

  // Company Menu Items
  const companyItems = [
    { name: "Metodologia", href: "/metodologia", icon: Settings, description: "Come implementiamo il tuo AI Agent in 7 giorni" },
    { name: "FAQ", href: "/faq", icon: HelpCircle, description: "Domande frequenti" }
  ];

  // Resources Menu Items
  const resourcesItems = [
    { name: "Articoli", href: "/articoli", icon: FileText, description: "Approfondimenti e best practices" },
    { name: "Casi Studio", href: "/casi-studio", icon: BookOpen, description: "Storie di successo reali" }
  ];

  const scrollToSection = (elementId: string) => {
    if (pathname !== '/') {
      window.location.href = `/${elementId}`;
      return;
    }

    const element = document.querySelector(elementId);
    if (element) {
      const headerHeight = 80;
      const elementPosition = element.getBoundingClientRect().top + window.pageYOffset;
      const offsetPosition = elementPosition - headerHeight;
      const startPosition = window.pageYOffset;
      const distance = offsetPosition - startPosition;
      const duration = 1000;
      let start: number | null = null;

      const easeInOutCubic = (t: number): number => {
        return t < 0.5 ? 4 * t * t * t : (t - 1) * (2 * t - 2) * (2 * t - 2) + 1;
      };

      const animation = (currentTime: number) => {
        if (start === null) start = currentTime;
        const timeElapsed = currentTime - start;
        const run = easeInOutCubic(timeElapsed / duration) * distance;
        window.scrollTo(0, startPosition + run);
        if (timeElapsed < duration) requestAnimationFrame(animation);
      };

      requestAnimationFrame(animation);
    }
    setIsMenuOpen(false);
  };

  const isActive = (href: string) => {
    if (href === '/') return location.pathname === '/';
    return location.pathname === href;
  };

  const handleMouseEnter = (dropdownName: string) => {
    if (closeTimeoutRef.current) {
      clearTimeout(closeTimeoutRef.current);
      closeTimeoutRef.current = null;
    }
    setActiveDropdown(dropdownName);
  };

  const handleMouseLeave = () => {
    closeTimeoutRef.current = setTimeout(() => {
      setActiveDropdown(null);
    }, 300); // 300ms delay per evitare chiusure accidentali
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-black/5 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex items-center h-16">
          {/* Logo */}
          <div className="flex-shrink-0">
            <Link href="/" className="text-2xl text-white" style={{ fontWeight: '300' }}>
              Pilot<span className="text-green-400">Pro</span>
            </Link>
          </div>

          {/* Main Navigation - Centered */}
          <nav className="hidden lg:flex items-center justify-center flex-1 space-x-8">
            {/* Platform (AI Workforce) */}
            <div className="relative" onMouseEnter={() => handleMouseEnter('platform')} onMouseLeave={handleMouseLeave}>
              <button
                className="flex items-center space-x-1 text-white hover:text-green-400 transition-colors duration-200 py-2"
              >
                <span className="text-sm" style={{ fontWeight: '300' }}>Piattaforma</span>
                <ChevronDown className="w-4 h-4" />
              </button>

              {/* Platform Mega Menu */}
              {activeDropdown === 'platform' && (
                <div
                  className="absolute top-full left-0 mt-0 w-[600px] rounded-2xl shadow-2xl border border-gray-700 p-8 z-[60]"
                  style={{ transform: 'translateX(-20%)', backgroundColor: '#000000' }}
                >
                  <div className="grid grid-cols-2 gap-8">
                    {/* AI Companions Column */}
                    <div>
                      <h3 className="text-xs font-semibold text-gray-300 uppercase tracking-wider mb-4">
                        Ai AGENT
                      </h3>
                      <div className="space-y-3">
                        {aiProducts.map((product) => {
                          const IconComponent = product.icon;
                          return (
                            <Link
                              key={product.name}
                              href={product.href}
                              className="flex items-start space-x-3 p-2 rounded-lg hover:bg-gray-800/50 transition-colors duration-200 group"
                              onClick={() => setActiveDropdown(null)}
                            >
                              <div className="w-8 h-8 bg-green-500/20 rounded-lg flex items-center justify-center group-hover:bg-green-500/30 transition-colors duration-200 mt-0.5">
                                <IconComponent className="w-4 h-4 text-green-400" />
                              </div>
                              <div>
                                <div className="text-white group-hover:text-green-400 font-medium text-sm">
                                  {product.name}
                                </div>
                                <div className="text-xs text-gray-400 mt-0.5">
                                  {product.description}
                                </div>
                              </div>
                            </Link>
                          );
                        })}
                      </div>
                    </div>

                    {/* Promotional Section */}
                    <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl p-4 text-white self-start">
                      <div className="text-xs font-semibold uppercase tracking-wider mb-2 opacity-90">
                        DISPONIBILE ORA
                      </div>
                      <h3 className="text-lg font-semibold mb-3 leading-tight">
                        Calcola il tuo <span className="text-yellow-300">Risparmio</span>
                      </h3>
                      <Link
                        href="/calcola-risparmio"
                        className="bg-white/20 hover:bg-white/30 text-white px-3 py-1.5 rounded-lg text-xs font-medium transition-colors duration-200 mb-3 inline-block"
                        onClick={() => setActiveDropdown(null)}
                      >
                        Calcola Ora
                      </Link>
                      <div className="flex items-center space-x-1 text-xs">
                        <span>Scopri il risparmio</span>
                        <ChevronDown className="w-3 h-3 rotate-[-90deg]" />
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Company */}
            <div className="relative" onMouseEnter={() => handleMouseEnter('company')} onMouseLeave={handleMouseLeave}>
              <button
                className="flex items-center space-x-1 text-white hover:text-green-400 transition-colors duration-200 py-2"
              >
                <span className="text-sm" style={{ fontWeight: '300' }}>Company</span>
                <ChevronDown className="w-4 h-4" />
              </button>

              {activeDropdown === 'company' && (
                <div 
                  className="absolute top-full left-1/2 transform -translate-x-1/2 mt-0 w-80 rounded-xl shadow-xl border border-gray-700 p-4 z-[60]"
                  style={{ backgroundColor: '#000000' }}
                >
                  <div className="space-y-3">
                    {companyItems.map((item) => {
                      const IconComponent = item.icon;
                      return (
                        <Link
                          key={item.name}
                          href={item.href}
                          className="flex items-start space-x-3 p-2 rounded-lg hover:bg-gray-800/50 transition-colors duration-200 group"
                          onClick={() => setActiveDropdown(null)}
                        >
                          <div className="w-8 h-8 bg-green-500/20 rounded-lg flex items-center justify-center group-hover:bg-green-500/30 transition-colors duration-200 mt-0.5">
                            <IconComponent className="w-4 h-4 text-green-400" />
                          </div>
                          <div>
                            <div className="text-white group-hover:text-green-400 font-medium text-sm">
                              {item.name}
                            </div>
                            <div className="text-xs text-gray-400 mt-0.5">
                              {item.description}
                            </div>
                          </div>
                        </Link>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>

            {/* Risorse */}
            <div className="relative" onMouseEnter={() => handleMouseEnter('resources')} onMouseLeave={handleMouseLeave}>
              <button
                className="flex items-center space-x-1 text-white hover:text-green-400 transition-colors duration-200 py-2"
              >
                <span className="text-sm" style={{ fontWeight: '300' }}>Risorse</span>
                <ChevronDown className="w-4 h-4" />
              </button>

              {activeDropdown === 'resources' && (
                <div 
                  className="absolute top-full left-1/2 transform -translate-x-1/2 mt-0 w-80 rounded-xl shadow-xl border border-gray-700 p-4 z-[60]"
                  style={{ backgroundColor: '#000000' }}
                >
                  <div className="space-y-3">
                    {resourcesItems.map((item) => {
                      const IconComponent = item.icon;
                      return (
                        <Link
                          key={item.name}
                          href={item.href}
                          className="flex items-start space-x-3 p-2 rounded-lg hover:bg-gray-800/50 transition-colors duration-200 group"
                          onClick={() => setActiveDropdown(null)}
                        >
                          <div className="w-8 h-8 bg-green-500/20 rounded-lg flex items-center justify-center group-hover:bg-green-500/30 transition-colors duration-200 mt-0.5">
                            <IconComponent className="w-4 h-4 text-green-400" />
                          </div>
                          <div>
                            <div className="text-white group-hover:text-green-400 font-medium text-sm">
                              {item.name}
                            </div>
                            <div className="text-xs text-gray-400 mt-0.5">
                              {item.description}
                            </div>
                          </div>
                        </Link>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>

            {/* Enterprise */}
            <Link
              href="/sicurezza"
              className="text-white hover:text-green-400 transition-colors duration-200 text-sm py-2" 
              style={{ fontWeight: '300' }}
            >
              Enterprise
            </Link>

            {/* Chi siamo */}
            <Link
              href="/chi-siamo"
              className="text-white hover:text-green-400 transition-colors duration-200 text-sm py-2" 
              style={{ fontWeight: '300' }}
            >
              Chi siamo
            </Link>
          </nav>

          {/* Auth Section */}
          <div className="hidden lg:flex items-center space-x-4 flex-shrink-0">
            <div className="flex items-center space-x-3">
              <Button
                asChild
                className="!bg-white !text-black hover:!bg-gray-100 px-6 py-3 text-sm font-medium rounded-md transition-all duration-200 shadow-sm" 
                style={{ fontWeight: '300' }}
              >
                <Link href="/prenota-demo">
                  Richiedi accesso
                </Link>
              </Button>
              <Button
                asChild
                size="lg"
                className="!bg-gray-800 !text-white hover:!bg-gray-700 !border-0 px-6 py-3 text-sm font-medium rounded-md transition-all duration-200"
              >
                <Link href="/auth">
                  Accedi
                </Link>
              </Button>
            </div>
          </div>

          {/* Mobile Menu Button */}
          <div className="lg:hidden">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="text-white hover:text-green-400 transition-colors duration-200"
            >
              {isMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      {isMenuOpen && (
        <div className="lg:hidden border-t border-gray-700 shadow-lg" style={{ backgroundColor: '#000000' }}>
          <div className="px-6 py-4 space-y-4">
            <Link
              href="/pilotpro"
              className="block text-white hover:text-green-400 transition-colors duration-200 text-base py-2" 
              style={{ fontWeight: '300' }}
              onClick={() => setIsMenuOpen(false)}
            >
              Piattaforma
            </Link>
            <Link
              href="/casi-studio"
              className="block text-white hover:text-green-400 transition-colors duration-200 text-base py-2" 
              style={{ fontWeight: '300' }}
              onClick={() => setIsMenuOpen(false)}
            >
              Company
            </Link>
            <Link
              href="/sicurezza"
              className="block text-white hover:text-green-400 transition-colors duration-200 text-base py-2" 
              style={{ fontWeight: '300' }}
              onClick={() => setIsMenuOpen(false)}
            >
              Enterprise
            </Link>
            <Link
              href="/chi-siamo"
              className="block text-white hover:text-green-400 transition-colors duration-200 text-base py-2" 
              style={{ fontWeight: '300' }}
              onClick={() => setIsMenuOpen(false)}
            >
              Chi siamo
            </Link>
            
            {/* Mobile Risorse with submenu */}
            <div className="space-y-2">
              <div className="text-white text-base py-2" style={{ fontWeight: '300' }}>
                Risorse
              </div>
              <div className="pl-4 space-y-2">
                <Link
                  href="/articoli"
                  className="block text-gray-400 hover:text-green-400 transition-colors duration-200 text-sm py-1" 
                  style={{ fontWeight: '200' }}
                  onClick={() => setIsMenuOpen(false)}
                >
                  → Articoli
                </Link>
                <Link
                  href="/casi-studio"
                  className="block text-gray-400 hover:text-green-400 transition-colors duration-200 text-sm py-1" 
                  style={{ fontWeight: '200' }}
                  onClick={() => setIsMenuOpen(false)}
                >
                  → Casi Studio
                </Link>
              </div>
            </div>
            
            <div className="px-2 space-y-3">
              <Button
                asChild
                className="w-full !bg-white !text-black hover:!bg-gray-100 px-6 py-3 text-sm font-medium rounded-md transition-all duration-200 shadow-sm justify-center" 
                style={{ fontWeight: '300' }}
              >
                <Link href="/prenota-demo">
                  Richiedi accesso
                </Link>
              </Button>
              <Button
                asChild
                size="lg"
                className="w-full !bg-gray-800 !text-white hover:!bg-gray-700 !border-0 px-6 py-3 text-sm font-medium rounded-md transition-all duration-200 justify-center"
              >
                <Link href="/auth">
                  Accedi
                </Link>
              </Button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
};

export default Header;
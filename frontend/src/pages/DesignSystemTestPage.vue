<template>
  <div class="min-h-screen bg-background text-text p-6">
    <div class="max-w-6xl mx-auto">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-4xl font-bold text-text mb-2">
          🎨 PilotProOS Design System Test
        </h1>
        <p class="text-text-secondary">
          Testing the new CSS architecture with instant theme switching
        </p>
      </div>
      
      <!-- Theme Switcher -->
      <ThemeSwitcher />
      
      <!-- Component Showcase -->
      <div class="mt-8 space-y-8">
        <!-- Buttons Section -->
        <section class="control-card p-6">
          <h2 class="text-2xl font-bold text-text mb-4">Button Showcase</h2>
          <div class="flex flex-wrap gap-4">
            <div class="btn-control">
              <Settings class="w-4 h-4" />
              <span>Control Button</span>
            </div>
            <div class="btn-control-primary">
              <Check class="w-4 h-4" />
              <span>Primary Button</span>
            </div>
            <button class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-hover transition-colors">
              Tailwind Primary
            </button>
            <button class="px-4 py-2 bg-surface border border-border text-text rounded-lg hover:bg-surface-hover transition-colors">
              Surface Button
            </button>
          </div>
        </section>
        
        <!-- Cards Section -->
        <section>
          <h2 class="text-2xl font-bold text-text mb-4">Card Layouts</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div class="control-card p-6">
              <div class="flex items-center gap-3 mb-4">
                <div class="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                  <Check class="w-4 h-4 text-white" />
                </div>
                <div>
                  <h3 class="text-text font-semibold">Success Card</h3>
                  <p class="text-text-secondary text-sm">Using design system</p>
                </div>
              </div>
              <div class="status-success px-3 py-1 rounded-full text-xs inline-flex items-center gap-1 border">
                <div class="w-2 h-2 bg-success rounded-full"></div>
                Active Process
              </div>
            </div>
            
            <div class="control-card p-6">
              <div class="flex items-center gap-3 mb-4">
                <div class="w-8 h-8 bg-surface border border-border rounded-lg flex items-center justify-center">
                  <Settings class="w-4 h-4 text-text-muted" />
                </div>
                <div>
                  <h3 class="text-text font-semibold">Configuration</h3>
                  <p class="text-text-secondary text-sm">System settings</p>
                </div>
              </div>
              <div class="btn-control w-full justify-center">
                <span>Configure</span>
              </div>
            </div>
            
            <div class="control-card p-6">
              <h3 class="text-text font-semibold mb-3">Status Overview</h3>
              <div class="space-y-2">
                <div class="flex items-center justify-between">
                  <span class="text-text-secondary text-sm">Success</span>
                  <div class="status-success px-2 py-1 rounded text-xs border">24</div>
                </div>
                <div class="flex items-center justify-between">
                  <span class="text-text-secondary text-sm">Errors</span>
                  <div class="status-error px-2 py-1 rounded text-xs border">3</div>
                </div>
                <div class="flex items-center justify-between">
                  <span class="text-text-secondary text-sm">Running</span>
                  <div class="status-running px-2 py-1 rounded text-xs border">12</div>
                </div>
              </div>
            </div>
          </div>
        </section>
        
        <!-- Sidebar Preview -->
        <section class="control-card p-6">
          <h2 class="text-2xl font-bold text-text mb-4">Sidebar Elements Preview</h2>
          <div class="w-64 bg-background border-r border-border">
            <div class="p-4">
              <div class="sidebar-nav">
                <div class="sidebar-nav-item mb-2">
                  <div class="sidebar-nav-icon">
                    <Settings class="w-5 h-5" />
                  </div>
                  <div class="ml-3">
                    <div class="sidebar-nav-label">Dashboard</div>
                    <div class="sidebar-nav-description">Main overview</div>
                  </div>
                </div>
                
                <div class="sidebar-nav-item active mb-2">
                  <div class="sidebar-nav-icon">
                    <Check class="w-5 h-5" />
                  </div>
                  <div class="ml-3">
                    <div class="sidebar-nav-label">Processes</div>
                    <div class="sidebar-nav-description">Business workflows</div>
                  </div>
                  <div class="sidebar-active-indicator"></div>
                  <div class="ml-auto">
                    <div class="badge-new">New</div>
                  </div>
                </div>
                
                <div class="sidebar-nav-item mb-2">
                  <div class="sidebar-nav-icon">
                    <Palette class="w-5 h-5" />
                  </div>
                  <div class="ml-3">
                    <div class="sidebar-nav-label">AI Agents</div>
                    <div class="sidebar-nav-description">Intelligent automation</div>
                  </div>
                  <div class="ml-auto">
                    <div class="badge-ai">AI</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
        
        <!-- Typography Section -->
        <section class="control-card p-6">
          <h2 class="text-2xl font-bold text-text mb-4">Typography Scale</h2>
          <div class="space-y-4">
            <div class="text-6xl font-bold text-text">Heading 1</div>
            <div class="text-4xl font-bold text-text">Heading 2</div>
            <div class="text-2xl font-semibold text-text">Heading 3</div>
            <div class="text-xl font-medium text-text">Heading 4</div>
            <div class="text-lg text-text">Large Text</div>
            <div class="text-base text-text">Body Text</div>
            <div class="text-sm text-text-secondary">Secondary Text</div>
            <div class="text-xs text-text-muted">Muted Text</div>
            <div class="text-gradient text-2xl font-bold">Gradient Text Effect</div>
          </div>
        </section>
        
        <!-- Live CSS Variables -->
        <section class="control-card p-6">
          <h2 class="text-2xl font-bold text-text mb-4">Live CSS Variables</h2>
          <p class="text-text-secondary mb-4">
            These values update instantly when you change themes above.
          </p>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-sm font-mono">
            <div class="bg-surface border border-border rounded p-3">
              <div class="text-text-muted">--color-primary:</div>
              <div class="text-primary">{{ getCSSVariable('color-primary') }}</div>
            </div>
            <div class="bg-surface border border-border rounded p-3">
              <div class="text-text-muted">--color-background:</div>
              <div class="text-text">{{ getCSSVariable('color-background') }}</div>
            </div>
            <div class="bg-surface border border-border rounded p-3">
              <div class="text-text-muted">--color-surface:</div>
              <div class="text-text">{{ getCSSVariable('color-surface') }}</div>
            </div>
            <div class="bg-surface border border-border rounded p-3">
              <div class="text-text-muted">--color-border:</div>
              <div class="text-text">{{ getCSSVariable('color-border') }}</div>
            </div>
            <div class="bg-surface border border-border rounded p-3">
              <div class="text-text-muted">--success:</div>
              <div class="text-success">{{ getCSSVariable('success') }}</div>
            </div>
            <div class="bg-surface border border-border rounded p-3">
              <div class="text-text-muted">--error:</div>
              <div class="text-error">{{ getCSSVariable('error') }}</div>
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { getCSSVariable } from '../design-system'
import ThemeSwitcher from '../components/ThemeSwitcher.vue'
import { Settings, Check, Palette } from 'lucide-vue-next'
</script>

<style scoped>
/* All styles are handled by the design system! */
</style>
#!/usr/bin/env node
/**
 * PilotPro MCP Server - Main Entry Point
 * 
 * This file serves as the entry point for the PilotPro MCP Server,
 * which allows AI assistants to interact with PilotPro workflows through the MCP protocol.
 */

import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { loadEnvironmentVariables } from './config/environment.js';
import { configureServer } from './config/server.js';

// Load environment variables
loadEnvironmentVariables();

/**
 * Main function to start the PilotPro MCP Server
 */
async function main() {
  try {
    console.error('Starting PilotPro MCP Server...');

    // Create and configure the MCP server
    const server = await configureServer();

    // Set up error handling
    server.onerror = (error: unknown) => console.error('[MCP Error]', error);

    // Set up clean shutdown
    process.on('SIGINT', async () => {
      console.error('Shutting down PilotPro MCP Server...');
      await server.close();
      process.exit(0);
    });

    // Connect to the server transport (stdio)
    const transport = new StdioServerTransport();
    await server.connect(transport);

    console.error('PilotPro MCP Server running on stdio');
  } catch (error) {
    console.error('Failed to start PilotPro MCP Server:', error);
    process.exit(1);
  }
}

// Start the server
main().catch(console.error);

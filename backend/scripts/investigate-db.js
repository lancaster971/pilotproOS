#!/usr/bin/env node

/**
 * Database Structure Investigation
 * 
 * This script investigates the structure of the n8n database
 * to understand how workflow nodes are stored.
 */

import { Pool } from 'pg';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

// Database connection
const dbPool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: process.env.DB_PORT || 5432,
  database: process.env.DB_NAME || 'pilotpros_db',
  user: process.env.DB_USER || 'pilotpros_user',
  password: process.env.DB_PASSWORD || 'pilotpros_password',
});

async function main() {
  console.log('🔍 Database Structure Investigation');
  console.log('===================================\n');
  
  try {
    // Check table structure
    console.log('📋 Workflow Entity Table Structure:');
    const structureQuery = `
      SELECT column_name, data_type, is_nullable
      FROM information_schema.columns 
      WHERE table_name = 'workflow_entity' 
        AND table_schema = 'n8n' 
      ORDER BY ordinal_position;
    `;
    
    const structure = await dbPool.query(structureQuery);
    console.table(structure.rows);
    
    // Check sample workflow data
    console.log('\n📄 Sample Workflow Data:');
    const sampleQuery = `
      SELECT id, name, nodes, connections
      FROM n8n.workflow_entity 
      LIMIT 3;
    `;
    
    const samples = await dbPool.query(sampleQuery);
    
    for (const row of samples.rows) {
      console.log(`\n🔸 Workflow: ${row.name} (ID: ${row.id})`);
      console.log('Nodes structure:', typeof row.nodes);
      
      if (row.nodes) {
        try {
          const nodesData = typeof row.nodes === 'string' ? JSON.parse(row.nodes) : row.nodes;
          console.log('Nodes is array:', Array.isArray(nodesData));
          
          if (Array.isArray(nodesData)) {
            console.log(`Has ${nodesData.length} nodes:`);
            nodesData.slice(0, 3).forEach((node, idx) => {
              console.log(`  ${idx + 1}. ${node.name || 'Unnamed'} (${node.type || 'No type'})`);
            });
          } else {
            console.log('Nodes structure:', Object.keys(nodesData).slice(0, 5));
            const firstNodeKey = Object.keys(nodesData)[0];
            if (firstNodeKey) {
              const firstNode = nodesData[firstNodeKey];
              console.log(`First node type: ${firstNode.type || 'No type'}`);
            }
          }
        } catch (err) {
          console.log('Error parsing nodes:', err.message);
        }
      } else {
        console.log('No nodes data');
      }
    }
    
    // Check for node types
    console.log('\n🎯 Attempting to extract node types...');
    
    // Try different approaches
    const typeQueries = [
      // Approach 1: nodes as JSON object
      `SELECT id, name, 
        json_object_keys(nodes::json) as node_keys
      FROM n8n.workflow_entity 
      WHERE nodes IS NOT NULL 
      LIMIT 1`,
      
      // Approach 2: nodes as text
      `SELECT id, name, 
        substring(nodes from 1 for 200) as nodes_preview
      FROM n8n.workflow_entity 
      WHERE nodes IS NOT NULL 
      LIMIT 1`
    ];
    
    for (let i = 0; i < typeQueries.length; i++) {
      try {
        console.log(`\nApproach ${i + 1}:`);
        const result = await dbPool.query(typeQueries[i]);
        if (result.rows.length > 0) {
          console.log('Success! Result:', result.rows[0]);
        }
      } catch (error) {
        console.log(`Failed: ${error.message}`);
      }
    }
    
  } catch (error) {
    console.error('❌ Investigation failed:', error.message);
  } finally {
    await dbPool.end();
  }
}

main().catch(console.error);
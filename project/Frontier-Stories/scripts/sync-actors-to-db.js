/**
 * Sync Actors JSON to Database
 * Updates the metadata field in the database for all actors from actors.json
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import pg from 'pg';

const { Pool } = pg;
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Database connection - Docker PostgreSQL (port 5433 from host)
const DATABASE_URL = process.env.DATABASE_URL || 'postgresql://postgres:postgres@localhost:5433/frontier_stories';

console.log('');
console.log('═══════════════════════════════════════════════════════════════');
console.log('  Sync Actors to Database - Frontier Stories');
console.log('═══════════════════════════════════════════════════════════════');
console.log('');
console.log('Connecting to database:', DATABASE_URL.replace(/:[^:@]+@/, ':****@'));

const pool = new Pool({
  connectionString: DATABASE_URL,
});

async function syncActors() {
  console.log('Reading actors.json...');
  const actorsPath = path.join(__dirname, 'actors.json');
  const actorsData = JSON.parse(fs.readFileSync(actorsPath, 'utf8'));
  
  console.log(`Found ${actorsData.data.length} actors to sync`);
  
  let updated = 0;
  let notFound = 0;
  let errors = 0;
  
  for (const actor of actorsData.data) {
    try {
      // Update only the metadata field
      const result = await pool.query(
        `UPDATE public.actors 
         SET metadata = $1::jsonb, updated_at = NOW()
         WHERE id = $2
         RETURNING id, full_name`,
        [JSON.stringify(actor.metadata), actor.id]
      );
      
      if (result.rowCount > 0) {
        updated++;
        if (updated % 50 === 0) {
          console.log(`  Updated ${updated} actors...`);
        }
      } else {
        notFound++;
        console.log(`  Actor not found in DB: ${actor.full_name} (${actor.id})`);
      }
    } catch (error) {
      errors++;
      console.error(`  Error updating ${actor.full_name}:`, error.message);
    }
  }
  
  console.log('');
  console.log('═══════════════════════════════════════════');
  console.log('Sync Complete!');
  console.log(`  ✅ Updated: ${updated}`);
  console.log(`  ⚠️  Not found: ${notFound}`);
  console.log(`  ❌ Errors: ${errors}`);
  console.log('═══════════════════════════════════════════');
  
  await pool.end();
}

// Also create an insert-if-missing version
async function syncActorsFull() {
  console.log('Reading actors.json...');
  const actorsPath = path.join(__dirname, 'actors.json');
  const actorsData = JSON.parse(fs.readFileSync(actorsPath, 'utf8'));
  
  console.log(`Found ${actorsData.data.length} actors to sync (full upsert)`);
  
  let updated = 0;
  let inserted = 0;
  let errors = 0;
  
  for (const actor of actorsData.data) {
    try {
      // Try update first
      const updateResult = await pool.query(
        `UPDATE public.actors 
         SET metadata = $1::jsonb, 
             first_name = $2,
             last_name = $3,
             role = $4,
             era = $5,
             bio = $6,
             tags = $7::jsonb,
             updated_at = NOW()
         WHERE id = $8
         RETURNING id`,
        [
          JSON.stringify(actor.metadata),
          actor.first_name,
          actor.last_name,
          actor.role,
          actor.era,
          actor.bio,
          JSON.stringify(actor.tags || []),
          actor.id
        ]
      );
      
      if (updateResult.rowCount > 0) {
        updated++;
      } else {
        // Insert if not exists
        await pool.query(
          `INSERT INTO public.actors (id, first_name, middle_name, last_name, role, era, bio, 
            voice_id, voice_provider, voice_settings, tags, image_url, metadata, 
            created_at, updated_at, character_type, is_active)
           VALUES ($1::uuid, $2, $3, $4, $5, $6, $7, $8, $9, $10::jsonb, $11::jsonb, $12, $13::jsonb, 
                   $14::timestamptz, NOW(), $15, true)`,
          [
            actor.id,
            actor.first_name,
            actor.middle_name,
            actor.last_name,
            actor.role,
            actor.era,
            actor.bio,
            actor.voice_id,
            actor.voice_provider || 'elevenlabs',
            JSON.stringify(actor.voice_settings || {}),
            JSON.stringify(actor.tags || []),
            actor.image_url,
            JSON.stringify(actor.metadata),
            actor.created_at || new Date().toISOString(),
            actor.character_type || 'professional'
          ]
        );
        inserted++;
      }
      
      if ((updated + inserted) % 50 === 0) {
        console.log(`  Processed ${updated + inserted} actors...`);
      }
    } catch (error) {
      errors++;
      console.error(`  Error syncing ${actor.full_name}:`, error.message);
    }
  }
  
  console.log('');
  console.log('═══════════════════════════════════════════');
  console.log('Full Sync Complete!');
  console.log(`  ✅ Updated: ${updated}`);
  console.log(`  ➕ Inserted: ${inserted}`);
  console.log(`  ❌ Errors: ${errors}`);
  console.log('═══════════════════════════════════════════');
  
  await pool.end();
}

// Check command line args
const args = process.argv.slice(2);
if (args.includes('--full')) {
  syncActorsFull().catch(console.error);
} else {
  syncActors().catch(console.error);
}

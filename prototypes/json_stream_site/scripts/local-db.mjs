// Local-only SQLite D1 interface. Migrations are applied before serving, never in request handling.
import {DatabaseSync} from 'node:sqlite';
import {readFileSync,mkdirSync} from 'node:fs';
export function localDB(path=':memory:'){
 if(path!==':memory:')mkdirSync('work',{recursive:true});
 const sqlite=new DatabaseSync(path);
 const exists=sqlite.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name='lab_sessions'").get();
 if(!exists)sqlite.exec(readFileSync('drizzle/0000_dsb_lab.sql','utf8'));
 sqlite.exec(readFileSync('drizzle/0001_provider_cooldowns.sql','utf8'));
 sqlite.exec(readFileSync('drizzle/0002_provider_rotation.sql','utf8'));
 const prepare=sql=>({sql,values:[],bind(...values){this.values=values.map(v=>v instanceof ArrayBuffer?new Uint8Array(v):v);return this;},
  async first(){return sqlite.prepare(sql).get(...this.values)||null;},
  async run(){const r=sqlite.prepare(sql).run(...this.values);return {meta:{changes:Number(r.changes)}};},
  async all(){return {results:sqlite.prepare(sql).all(...this.values)};}});
 return {prepare,async batch(statements){sqlite.exec('BEGIN');try{
  const results=statements.map(s=>{const v=sqlite.prepare(s.sql).run(...s.values);return {meta:{changes:Number(v.changes)}};});sqlite.exec('COMMIT');return results;
 }catch(e){sqlite.exec('ROLLBACK');throw e;}},close(){sqlite.close();}};
}

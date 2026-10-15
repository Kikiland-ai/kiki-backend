import {readFile,readdir} from 'node:fs/promises';
import {existsSync} from 'node:fs';
import {deflateRawSync} from 'node:zlib';
const standalone=new URL('../adapter/',import.meta.url);
const source=existsSync(standalone)?standalone:new URL('../../screen_writing/shared_tab/',import.meta.url);
export const readAdapterAsset=name=>readFile(new URL(name,source),'utf8');
function crc32(bytes){let crc=0xffffffff;for(const byte of bytes){crc^=byte;for(let i=0;i<8;i++)crc=(crc>>>1)^((crc&1)?0xedb88320:0);}return (crc^0xffffffff)>>>0;}
export async function packAdapter(){
 const records=[],directory=[];let offset=0;
 for(const entry of (await readdir(source,{withFileTypes:true})).filter(v=>v.isFile()&&!v.name.endsWith('.md')).sort((a,b)=>a.name.localeCompare(b.name))){
  const bytes=await readFile(new URL(entry.name,source)),compressed=deflateRawSync(bytes),name=Buffer.from('kiki-simulink-adapter/'+entry.name),crc=crc32(bytes);
  const header=Buffer.alloc(30);header.writeUInt32LE(0x04034b50);header.writeUInt16LE(20,4);header.writeUInt16LE(8,8);header.writeUInt32LE(crc,14);header.writeUInt32LE(compressed.length,18);header.writeUInt32LE(bytes.length,22);header.writeUInt16LE(name.length,26);
  const central=Buffer.alloc(46);central.writeUInt32LE(0x02014b50);central.writeUInt16LE(20,4);central.writeUInt16LE(20,6);central.writeUInt16LE(8,10);central.writeUInt32LE(crc,16);central.writeUInt32LE(compressed.length,20);central.writeUInt32LE(bytes.length,24);central.writeUInt16LE(name.length,28);central.writeUInt32LE(offset,42);
  records.push(header,name,compressed);directory.push(central,name);offset+=header.length+name.length+compressed.length;
 }
 const central=Buffer.concat(directory),end=Buffer.alloc(22);end.writeUInt32LE(0x06054b50);end.writeUInt16LE(directory.length/2,8);end.writeUInt16LE(directory.length/2,10);end.writeUInt32LE(central.length,12);end.writeUInt32LE(offset,16);
 return Buffer.concat([...records,central,end]);
}

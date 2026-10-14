// Strict incremental JSON parsing. A provisional row is never checkpoint evidence.
function streamValue(text,start=0){
 let i=start,depth=0;const incomplete=()=>{throw Object.assign(Error('incomplete_json'),{incomplete:true});};
 const bad=()=>{throw Error('invalid_output');};
 function space(){while(i<text.length&&/[\t\r\n ]/.test(text[i]))i++;}
 function string(){const from=i++;let escaped=false;
  while(i<text.length){const ch=text[i++];if(escaped){escaped=false;continue;}if(ch==='\\'){escaped=true;continue;}if(ch==='"'){try{return JSON.parse(text.slice(from,i));}catch{bad();}}}
  incomplete();
 }
 function value(){space();if(i>=text.length)incomplete();if(++depth>32)bad();let result;const ch=text[i];
  if(ch==='"')result=string();
  else if(ch==='{'||ch==='['){const object=ch==='{',end=object?'}':']';result=object?Object.create(null):[];i++;space();
   if(i>=text.length)incomplete();if(text[i]===end){i++;depth--;return result;}
   while(true){space();let key;if(object){if(i>=text.length)incomplete();if(text[i]!== '"')bad();key=string();if(Object.hasOwn(result,key))bad();space();if(i>=text.length)incomplete();if(text[i++]!==':')bad();}
    const next=value();if(object)result[key]=next;else result.push(next);space();if(i>=text.length)incomplete();
    const delimiter=text[i++];if(delimiter===end)break;if(delimiter!==',')bad();space();if(i>=text.length)incomplete();if(text[i]===end)bad();
   }
  }else{const from=i;while(i<text.length&&!/[\t\r\n ,\]}]/.test(text[i]))i++;if(i===text.length)incomplete();try{result=JSON.parse(text.slice(from,i));}catch{bad();}if(typeof result==='number'&&!Number.isFinite(result))bad();}
  depth--;return result;
 }
 const result=value();return {value:result,end:i};
}
function streamStrictJSON(text){const parsed=streamValue(text+' ',0);if(text.slice(parsed.end).trim())throw Error('invalid_output');return parsed.value;}
class FindingParserJS{
 constructor(cp,actions){this.expected={criteria:new Set(cp.completion_criteria.map(c=>c.id)),action_findings:new Set(actions.map(a=>a.id))};this.seen={criteria:new Set(),action_findings:new Set()};this.completed=new Set();this.keys=new Set();this.text='';this.pos=0;this.state='start';this.field=null;this.closed=false;}
 feed(text){this.text+=text;if(this.text.length>262144)throw Error('invalid_output');return this.parse();}
 parse(){const events=[],bad=()=>{throw Error('invalid_output');};
  while(true){while(this.pos<this.text.length&&/[\t\r\n ]/.test(this.text[this.pos]))this.pos++;if(this.pos>=this.text.length)return events;
   const ch=this.text[this.pos];let parsed;
   const read=()=>{try{return streamValue(this.text,this.pos);}catch(e){if(e.incomplete)return null;throw e;}};
   if(this.state==='start'){if(ch!=='{')bad();this.pos++;this.state='key';}
   else if(this.state==='key'){parsed=read();if(!parsed)return events;const key=parsed.value;if(!['criteria','action_findings','uncertainties','summary'].includes(key)||this.keys.has(key))bad();this.keys.add(key);this.field=key;this.pos=parsed.end;this.state='colon';}
   else if(this.state==='colon'){if(ch!==':')bad();this.pos++;this.state=this.expected[this.field]?'array_start':'value';}
   else if(this.state==='array_start'){if(ch!=='[')bad();this.pos++;this.state='row_or_end';}
   else if(['row','row_or_end'].includes(this.state)){
    if(ch===']'&&this.state==='row_or_end'){this.finishArray();continue;}parsed=read();if(!parsed)return events;const row=parsed.value,idKey=this.field==='criteria'?'criterion_id':'action_id',id=row?.[idKey];
    if(!row||Object.keys(row).sort().join(',')!==[idKey,'status','evidence'].sort().join(',')||!this.expected[this.field].has(id)||this.seen[this.field].has(id)||!['match','mismatch','unknown'].includes(row.status)||typeof row.evidence!=='string'||row.evidence.length>180||(row.status!=='unknown'&&!row.evidence.trim()))bad();
    this.seen[this.field].add(id);this.pos=parsed.end;this.state='row_delim';events.push({type:'provisional_findings',field:this.field,finding:row});
   }else if(this.state==='row_delim'){if(ch===','){this.pos++;this.state='row';}else if(ch===']')this.finishArray();else bad();}
   else if(this.state==='value'){parsed=read();if(!parsed)return events;const value=parsed.value;
    if(this.field==='summary'&&(typeof value!=='string'||!value.trim()||value.length>220))bad();
    if(this.field==='uncertainties'&&(!Array.isArray(value)||value.length>3||value.some(x=>typeof x!=='string'||x.length>150)))bad();
    this.completed.add(this.field);this.pos=parsed.end;this.state='field_delim';
   }else if(this.state==='field_delim'){if(ch===','){this.pos++;this.state='key';}else if(ch==='}'){this.pos++;this.state='end';this.closed=true;}else bad();}
   else bad();
  }
 }
 finishArray(){if(this.seen[this.field].size!==this.expected[this.field].size)throw Error('invalid_output');this.completed.add(this.field);this.pos++;this.state='field_delim';}
 finish(){this.parse();if(!this.closed||this.text.slice(this.pos).trim()||this.keys.size!==4||!this.completed.has('action_findings'))throw Error('invalid_output');return streamStrictJSON(this.text);}
}
class SSEDecoderJS{
 constructor(){this.decoder=new TextDecoder('utf-8',{fatal:true});this.pending='';this.data=[];this.total=0;}
 feed(bytes){this.total+=bytes.length;if(this.total>2000000)throw Error('invalid_output');this.pending+=this.decoder.decode(bytes,{stream:true});const result=[];
  while(this.pending.includes('\n')){const end=this.pending.indexOf('\n'),line=this.pending.slice(0,end).replace(/\r$/,'');this.pending=this.pending.slice(end+1);
   if(!line){if(this.data.length)result.push(this.data.join('\n'));this.data=[];}else if(line.startsWith('data:'))this.data.push(line.slice(5).replace(/^ /,''));
   if(this.pending.length+this.data.join('\n').length>131072)throw Error('invalid_output');
  }return result;
 }
 finish(){this.pending+=this.decoder.decode();if(this.pending.trim()||this.data.length)throw Error('incomplete_output');}
}
export {FindingParserJS,SSEDecoderJS,streamStrictJSON};

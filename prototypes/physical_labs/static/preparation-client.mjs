/* Serialise student actions so quick apparatus clicks are never silently discarded. */
export class PreparationClient {
  constructor(api,onState=()=>{},id=()=>crypto.randomUUID()) { this.api=api;this.onState=onState;this.id=id;this.state=null;this.tail=Promise.resolve();this.pending=0; }
  use(state) { this.state=state; }
  event(kind,fields={}) {
    const session=this.state?.session_id,eventId=this.id();
    if(!session)return Promise.reject(Error('Start a preparation session first.'));
    this.pending++;
    const operation=this.tail.then(async()=>{
      if(this.state?.session_id!==session)throw Error('The active session changed. Please repeat your action.');
      const payload={event_id:eventId,revision:this.state.revision,kind,...fields};
      const next=await this.api(`/v1/physical-labs/sessions/${session}/events`,{method:'POST',body:JSON.stringify(payload)});
      this.state=next;await this.onState(next);return next;
    });
    this.tail=operation.catch(()=>{});
    return operation.finally(()=>{this.pending--;});
  }
}

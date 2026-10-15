export function verificationCadence({sameFrame,pendingSecondRead,evidenceExpiring,status},policy){
 if(!sameFrame||pendingSecondRead||evidenceExpiring)return policy.fast_interval_ms||3000;
 if(['failed','waiting_for_provider','checking'].includes(status))return policy.idle_interval_ms||12000;
 return null; // A stable, supported frame needs no new paid interpretation.
}

export function sameScreenContent(current,previous){
 const a=current.fingerprint,b=previous.fingerprint;
 if(a||b)return !!a&&!!b&&a.length===b.length&&!a.some((v,i)=>v!==null&&b[i]!==null&&Math.abs(v-b[i])>3);
 return current.hash===previous.hash;
}

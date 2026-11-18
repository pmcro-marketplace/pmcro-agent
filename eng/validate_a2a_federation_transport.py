#!/usr/bin/env python3
from __future__ import annotations
import json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/"contracts"/"a2a"/"federation-transport.json"
ROLE_CONTRACT=ROOT/"contracts"/"a2a"/"role-services.json"
ROLES=("orchestrator","planner","maker","checker","reflector")
SHA40=re.compile(r"^[0-9a-f]{40}$")
def req(c,m):
    if not c: raise ValueError(m)
def load(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def validate(manifest=None,contract=None):
    manifest=load(MANIFEST) if manifest is None else manifest
    contract=load(ROLE_CONTRACT) if contract is None else contract
    req(manifest.get("kind")=="PmcroA2AFederationTransportProof" and manifest.get("version")==1,"invalid kind/version")
    req(manifest.get("scope")=="a2a-transport","scope changed")
    req(manifest.get("provider_execution")=="NOT_INVOKED","provider execution must remain NOT_INVOKED")
    services=manifest.get("services",[])
    req(tuple(x.get("role") for x in services)==ROLES,"service membership/order changed")
    ports=set()
    for svc in services:
        role=svc["role"]
        sealed=contract["roles"][role]
        proof=sealed["proof"]
        req(svc.get("repository")==sealed.get("repository"),f"{role}: repo mismatch")
        req(svc.get("commit")==proof.get("commit"),f"{role}: commit mismatch")
        req(SHA40.fullmatch(svc.get("commit","")) is not None,f"{role}: invalid commit")
        req(svc.get("agent")==sealed.get("agent"),f"{role}: agent mismatch")
        req(isinstance(svc.get("port"),int) and 1024<=svc["port"]<=65535,f"{role}: bad port")
        req(svc["port"] not in ports,f"{role}: duplicate port")
        ports.add(svc["port"])
        h=svc.get("health",{})
        req(h.get("execution")=="NOT_INVOKED",f"{role}: execution claim")
        if role=="maker": req(h.get("mcp")=="NOT_CONNECTED","maker MCP must stay disconnected")
        if role=="checker": req(h.get("mutation")=="DISALLOWED","checker mutation must stay disallowed")
        if role=="reflector": req(h.get("next_cycle_dispatch") is False,"reflector dispatch must stay false")
    return {"status":"PASS","services":5,"ports":sorted(ports),"provider_execution":"NOT_INVOKED"}
def main():
    try:
        print(json.dumps(validate(),sort_keys=True)); return 0
    except Exception as exc:
        print(json.dumps({"status":"FAIL","error":str(exc)},sort_keys=True)); return 1
if __name__=="__main__": sys.exit(main())

# PMCR-O Agent

Canonical plugin: `pmcro`.
Human handle: `@pmcro-agent`.

## PMCR-O Agent marketplace

The authored [marketplace.yaml](marketplace.yaml) federates the existing
protocol, five role agents, Hook Agent and Marketplace Agent. Plugin identities
remain their original names; no role implementation is copied. Commit pins
resolve independently of a mutable branch. The existing root plugin manifests
remain the PMCR-O protocol package, not generated catalog projections.

| Agent | Plugin | Skill |
| --- | --- | --- |
| PMCR-O | pmcro | interpret, pmcro |
| Orchestrator | orchestrator | orchestrate |
| Planner | planner | plan |
| Maker | maker | make |
| Checker | checker | check |
| Reflector | reflector | reflect |
| Hook | hook | hook |
| Marketplace | marketplace | marketplace |

The reviewed Marketplace Agent currently provides the private trail
implementation. A separate `pmcro-trail` package is not registered unless a
real reviewed provider exists. Hook dispatch currently resolves lifecycle
contracts only; host lifecycle execution remains NOT_INVOKED.

## Automatic proof

Clone the seven external repositories from their declared GitHub origins
into one parent directory, including Marketplace Agent's
`pmcro/standalone-production` review branch. The current PMCR-O repository
must contain its pinned protocol commit.

```sh
python3 -I -B eng/validate_marketplace.py --providers-dir /absolute/providers
PMCRO_PROVIDERS_DIR=/absolute/providers python3 -B eng/test_marketplace.py
```

For persistent proof in an already registered, authorized private project,
append `--project-id example` to the validator. This uses the pinned
Marketplace Agent's write-once trail implementation and checks its seal after
reopening. Raw frames remain under the operator's private project registry,
not in this repository. POSIX owner-only permissions are required.

The GitHub proof workflow runs these checks with a disposable private project.
Catalog membership and source verification do not imply installation, real
role execution, host lifecycle invocation or independent approval.

## Executable five-phase proof host

The reviewed Cycle skill coordinator is distributed byte-for-byte as a pinned
dependency. The local host registers five narrowly scoped executable role
callbacks. Orchestrator admits the fixed federation-proof intent, Planner
specifies measurable criteria, Maker invokes the actual Marketplace Agent
validation capability via the coordinator's scoped resolver, Checker
independently rereads the sources and private provider receipt, and Reflector
records the actual verdict. Each invocation persists start and terminal
frames in the reviewed Trail implementation. The coordinator separately
checks the noun agent and cognitive verb grants; scope is fixed, not arbitrary
message code, and no next cycle starts automatically.

```sh
python3 -I -B eng/run_cycle.py --providers-dir /absolute/providers --project-id example --execute-proof
python3 -I -B eng/run_cycle.py --providers-dir /absolute/providers --project-id example --verify-trail RETURNED_UUID
PMCRO_PROVIDERS_DIR=/absolute/providers python3 -B eng/test_cycle_host.py
```

Execution is limited to a registered private proof project and the fixed
federation validator. A successful local cycle is **not** evidence of native
MAF, remote agent, model, or Hook Agent execution. Those remain uninvoked
until their real host adapters are available. GitHub's automatic proof runs
the same code and reopens the sealed seven-frame receipt in a fresh process.

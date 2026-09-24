# A Lightweight Git-Based Platform for Configuration Management, Versioning, and Static Topology Inference in Heterogeneous Legacy Network Infrastructures

**Review of Computer Engineering Studies**
Vol., No., Month, Year, pp. \*\*-\*\*
Journal homepage: http://iieta.org/journals/rces

---

**Authors:** María C. Abeledo\*, Daniel A. Priano, Matías A. Marsicano, Ximena Salazar Gallardo, Alejandro J. Guevara, Cristian C. Villafañez

**Affiliation:** Research and Development Center in Computer Science (CIDI), National University of San Martín (UNSAM), San Martín, Argentina

**Corresponding Author Email:** mabeledo@unsam.edu.ar

https://doi.org/10.18280/rces.xxxxxx

**Received:** — **Accepted:** —

## ABSTRACT

In institutional and educational network infrastructures, the coexistence of equipment from multiple generations and vendors poses critical challenges for administration, operational continuity, and configuration auditing. Legacy devices impose constraints that standard industry platforms do not contemplate: obsolete cryptographic protocols, non-standardized interactive authentication mechanisms, restrictive management consoles, and the absence of persistent neighbor-discovery protocols (LLDP/CDP) in the saved configuration. This paper presents the design, architecture, and evaluation of an integral Network Configuration Management (NCM) platform developed within the Network Automation Project III. The solution implements an automated, transactional backup workflow over Git; a granular syntactic comparison engine (side-by-side diffs) with volatile-parameter filtering; a Layer-2/Layer-3 topology inference algorithm based on static configuration analysis, whose inferred links are classified into transparent evidentiary tiers rather than presented as a single undifferentiated map; and a staged-diagnosis scheme with credential quarantine for the active protection of the infrastructure. A hardware simulator (digital twin) reproduces the behavioral anomalies of real legacy devices, allowing the software to be certified without operational risk. Field observations from the pilot deployment indicate a reduction of per-device backup time from 5–15 minutes to 15–45 seconds, full-network unattended backup in under 4 minutes, a mean time to recovery below 2 minutes, and a fully auditable configuration history with no false-positive commits observed. The engineering rationale for a purpose-built solution over reference tools such as Oxidized, the operational constraints assumed — including the single-site, log-derived nature of this evaluation — and future lines of work are also discussed.

**Keywords:** configuration versioning, Git, legacy network devices, network automation, network configuration management, SSH, topology inference, digital twin

---

## 1. Introduction

In recent years, network automation and infrastructure-as-code (IaC) practices have profoundly transformed the administration of data networks [10, 14, 22]. However, most of the tooling that supports this transformation implicitly assumes reasonably modern equipment: standardized SSH stacks, non-interactive command execution, and machine-readable management interfaces such as NETCONF [11]. Institutional and educational networks rarely satisfy these assumptions. Their infrastructure typically accumulates equipment across successive expansion stages, resulting in a heterogeneous park in which high-density core switches coexist with access-layer devices that are one or two decades old.

The infrastructure addressed by this work is representative of this scenario. Its core and main distribution rely on high-density switches with 10G uplinks (Dell PowerConnect 7000 series); its legacy access and secondary distribution layers comprise Fast/Gigabit Ethernet switches of earlier generations (Dell PowerConnect 3500 series and devices based on Comware OS 5.20 / 3Com Baseline); and its edge and expansion segments include manageable routers and switches from contemporary vendors (Cisco IOS/IOS-XE, MikroTik RouterOS, and TP-Link JetStream/ER).

Prior to this development, network administration presented significant risks. First, there was a lack of traceability: modifications to VLANs, routing tables, and access control lists (ACLs) were performed interactively and were not chronologically recorded. Second, the mean time to recovery (MTTR) was high: after hardware incidents such as power-supply failures or surges, service restoration depended on scattered, often outdated or incomplete backup files. Third, the infrastructure proved fragile in the face of standard tooling: previous attempts to use generic automated collection tools led to administrative account lockouts caused by massive retries after authentication errors, or to connection failures due to incompatibility with legacy SSH algorithms [6, 7]. Finally, topological opacity — the absence of formally documented network cartography — required manual on-site surveys to identify trunk links and inter-node dependencies. These failure modes are consistent with the literature on operator-driven outages and the intrinsic complexity of network configuration management [12, 13].

The objective of this work is therefore to design, implement, and evaluate a purpose-built NCM platform that treats the constraints of legacy equipment as primary design requirements, rather than adapting a generic tool to an environment it was not designed for. As Section 2 shows, no documented platform currently combines legacy-safe collection, lockout-preventing retry semantics, and traffic-free topology inference in a package deployable by institutions with limited budgets; closing that gap is the specific contribution pursued here. The main contributions are: (1) an adaptive multi-vendor SSH collection engine that negotiates with legacy cryptographic stacks without weakening the security posture of the management server; (2) a transactional Git-based version store with volatile-pattern normalization that yields a zero-noise, fully auditable configuration history; (3) a static topology inference algorithm that reconstructs the L2/L3 connectivity graph from stored configurations alone, without emitting additional traffic on the network; and (4) an active infrastructure-protection scheme — credential quarantine, truncation rejection, and controlled concurrency — that operationalizes a "do no harm" design philosophy.

This paper is organized as follows. Section 2 reviews the literature on network configuration management tooling, legacy SSH interoperability, topology discovery, and infrastructure as code. Section 3 describes the methodology and design principles. Section 4 presents the system architecture and design. Section 5 details the implementation. Section 6 reports results from the pilot deployment. Section 7 discusses the findings against the state of the art and the system's limitations. Section 8 draws conclusions, and Section 9 outlines future work.

## 2. Literature Review

### 2.1 Network configuration management tooling

Configuration backup and change tracking for network devices is a long-established practice. RANCID [2] pioneered the model of periodically logging into routers, collecting the running configuration, and committing differences to a version-control repository. Oxidized [1], its modern successor, generalizes this model to more than one hundred device types through a Ruby-based collection engine with pluggable input, output, and source modules, and has become the de facto open-source reference for network configuration backup. Higher-level automation frameworks such as NAPALM [3] and Netmiko [4] provide multi-vendor abstraction layers for programmatic interaction with network operating systems, and are commonly embedded in orchestration ecosystems. All of these tools, however, presuppose devices that behave reasonably close to contemporary standards; their extension mechanisms for anomalous login dialogues, restrictive consoles, or obsolete cryptography require non-trivial custom development in the host language, and their retry semantics are not designed around the lockout policies of devices with strict local AAA configurations.

### 2.2 Interoperability with legacy SSH implementations

The SSH protocol suite [5, 6] allows peers to negotiate key-exchange methods, ciphers, and message authentication codes. As cryptanalytic results accumulated, algorithms such as `diffie-hellman-group14-sha1` and CBC-mode ciphers were progressively deprecated by modern SSH distributions, and current IETF guidance discourages their use [7]. Legacy network equipment, whose firmware no longer receives updates, frequently supports only these deprecated algorithms. The standard workaround — globally re-enabling weak algorithms in the management host's SSH client configuration — degrades the security posture of every connection made from that host, illustrating a structural tension between operational reach and cryptographic hygiene that a management platform for legacy environments must resolve explicitly.

### 2.3 Topology discovery

Dynamic neighbor-discovery protocols such as LLDP [8] and the proprietary CDP are the usual basis for automated topology mapping, complemented by SNMP-based collection of interface and forwarding tables [20]. In legacy environments these mechanisms are often unavailable: firmware may not support LLDP, may not persist its configuration, or administrative policy may keep discovery protocols disabled. An alternative line of work reconstructs topology statically, from the semantic content of device configurations themselves — shared point-to-point subnets, VLAN transport sets, and interface descriptions — an approach that emits no traffic on the production network and can therefore be applied without operational risk. The use of /30 and /31 prefixes on point-to-point links [17] provides particularly strong static evidence, since such a subnet can only be shared by exactly two interfaces.

### 2.4 Infrastructure as code and version control

The infrastructure-as-code paradigm treats infrastructure definitions as versioned artifacts subject to the same engineering discipline as software [10]. Git [9] provides content-addressable storage, atomic commits, and a complete audit trail, making it a natural substrate for configuration history. Classic difference algorithms [15, 16] underpin change visualization; for configuration auditing, word-level tokenization over line-based diffs allows the exact changed parameter (an SNMP community, a VLAN identifier, an ACL entry) to be identified visually. Finally, the digital-twin concept [18] — a faithful software replica of a physical system used for validation without touching the real asset — has been increasingly applied to network environments, and motivates the hardware simulator used in this work.

### 2.5 Synthesis and research gap

The reviewed literature exhibits a consistent pattern: mature NCM tooling [1-4] assumes standards-compliant devices and treats legacy anomalies as extension cases to be programmed ad hoc; guidance on SSH cryptography [7] resolves the legacy-interoperability tension only at the cost of host-wide security relaxation; and automated topology mapping presupposes active discovery protocols [8, 20] that legacy environments frequently lack. To the best of the authors' knowledge, no documented open-source platform simultaneously provides (i) session-scoped negotiation with obsolete SSH stacks that preserves the management host's security posture, (ii) collection semantics designed around the lockout policies of devices with local AAA (credential quarantine, bounded retries), (iii) a transparent, evidence-tiered approach to topology inference performed purely by static configuration analysis, distinguishing deterministic from heuristic evidence, and (iv) a zero-infrastructure deployment model suited to institutional and educational settings. This combination is the research gap addressed by the present work.

## 3. Methodology and Design Principles

The system was developed under a set of premises oriented toward robustness, portability, and low operational impact (zero-infrastructure overhead):

**Lightweight, self-contained architecture.** The system operates without external relational database managers and without complex build chains for the web interface. The entire environment runs directly on standard Python and native web components, which simplifies deployment on modest institutional hardware and guarantees full technical transfer to the institution.

**Atomic version control (GitStore).** Every successful configuration dump constitutes a commit in a private version store. Strict transactional control is implemented through filesystem-level locks to guarantee atomicity and prevent race conditions between concurrent processes, preserving the consistency of the Git index at all times [9].

**"Do no harm" principle.** The software prioritizes the integrity of the network over data collection: it avoids saturating the control plane of older switches through controlled concurrency and session serialization; it applies strict end-of-file validation to reject truncated backups that would otherwise overwrite previously functional versions; and it automatically suspends access attempts after repeated authentication failures, eliminating the lockout risk documented in Section 1.

**Digital twin and isolated validation.** For development and continuous-integration testing, a device simulator (`fake_device.py`) emulates with precision the anomalies of the real devices — in-band login dialogues, forced paging, and privilege-elevation prompts — allowing the software to be certified without operational risk on the production network [18].

## 4. System Architecture and Design

### 4.1 Five-layer architecture

The solution is structured in five clearly decoupled functional layers, shown in Figure 1. Layer 1 (definition and inventory) comprises the `inventory.yaml` topology and role definition, a protected `.env` secrets file, and a round-trip inventory engine that preserves comments and ordering on rewrite. Layer 2 (orchestration and connectivity) contains the central collector, the credential-quarantine module, and the driver dispatcher. Layer 3 (hardware abstraction) hosts one specialized driver per device family — Dell PowerConnect 7000/3500, Comware OS 5.20, Cisco IOS/IOS-XE, MikroTik RouterOS, and TP-Link JetStream/ER — supported by the `ssh_compat` component for legacy cryptographic negotiation. Layer 4 (integrity and versioning) applies the volatile-pattern filter and integrity validation before handing the configuration to the transactional GitStore engine. Layer 5 (analysis and presentation) exposes the side-by-side diff engine and the topology-inference engine through a native single-page web application (SPA) and a command-line console (CLI).

*Figure 1. Five-layer architecture of the proposed system. Source: elaborated by the authors.*

### 4.2 Driver abstraction and hardware particularities

Each device family is managed through a specialized driver, built over the Paramiko SSHv2 library [19], that implements three mechanisms absent from generic tooling:

**Temporary cryptographic management (`ssh_compat`).** For equipment with obsolete SSH implementations, the system atomically promotes algorithms such as `diffie-hellman-group14-sha1` or `aes128-cbc` exclusively during the initial session handshake, restoring modern cryptographic standards immediately afterwards. The promotion is scoped to the individual session, so the security posture of the management server — and of every other connection it makes — is never weakened [6, 7].

**Prompt handling and two-phase elevation.** On platforms that start in restricted consoles, the driver transparently manages the interactive privilege-elevation dialogue (including secondary passwords) before executing the configuration-dump and paging-deactivation commands.

**In-band authentication.** On equipment whose SSH negotiation delegates authentication to an internal interactive pseudo-terminal, the driver detects and answers the username and password requests within the terminal stream, a behavior that generic collectors typically misinterpret as a connection timeout.

Table 1 summarizes the device families, their roles, and the specific constraints each driver absorbs.

| Device family | Network role | Main operational constraints | Driver validation |
|---|---|---|---|
| Dell PowerConnect 7000 | Core / main distribution, 10G | Forced paging; elevation dialogue | Production-validated |
| Dell PowerConnect 3500 | Legacy access / secondary distribution | Legacy SSH KEX and ciphers; restricted console | Production-validated |
| Comware OS 5.20 / 3Com Baseline | Legacy access | In-band authentication; legacy ciphers | Production-validated |
| Cisco IOS / IOS-XE | Edge and expansion segments | Enable-mode elevation; paging | Simulator-validated |
| MikroTik RouterOS | Edge routing | Non-IOS export syntax; volatile export headers | Simulator-validated |
| TP-Link JetStream / ER | Edge access | Restrictive console; paging dialogs | Simulator-validated |

*Table 1. Managed device families and constraints absorbed by their drivers. Source: elaborated by the authors.*

### 4.3 Normalization and volatile-pattern filtering

Before storage in the repository, each configuration passes through a normalization stage that removes timestamps, uptime statistics, and dynamic lines generated by the firmware. This guarantees that the version engine records only substantive configuration changes, eliminating false-positive commits and keeping the history semantically meaningful for auditing.

### 4.4 Multilevel topology-inference algorithm

The topology subsystem syntactically analyzes the stored configuration files and reconstructs the connectivity graph of the network without emitting any additional traffic. Inferred links are classified into evidentiary tiers, as summarized in Table 2, that reflect the logical or heuristic strength of the static evidence behind each link — not a statistically calibrated confidence score: at the deterministic tier, point-to-point links are identified over /30 or /31 subnets shared unambiguously between Layer-3 interfaces [17], a case in which the subnet's uniqueness constitutes a logical proof rather than a probabilistic estimate; at the heuristic tier, the engine cross-correlates transport VLANs on trunk interfaces, explicit port descriptions, and adjacencies on management subnets, requiring independent corroboration between sources. In addition, the analyzer proactively reports configuration anomalies (findings), such as switch virtual interfaces (SVIs) with out-of-range addressing, link aggregation groups (LAGs) with no member interfaces, or discrepancies between the active configuration and the declared inventory. This classification has not yet been validated against a ground-truth topology; Section 7.1 discusses the gap and the protocol required to close it.

| Evidentiary tier | Evidence source | Example |
|---|---|---|
| Deterministic | /30 or /31 subnet shared by exactly two L3 interfaces | Router-to-router point-to-point link |
| Heuristic (cross-corroborated) | Independent cross-correlation of trunk VLAN sets, port descriptions, management-subnet adjacency | Inter-switch trunk deduced from matching VLAN transport sets |
| Finding (anomaly) | Static rule violation in parsed configuration | SVI with out-of-range address; LAG without members; inventory mismatch |

*Table 2. Evidentiary tiers of the static topology-inference engine. Source: elaborated by the authors.*

## 5. Implementation

### 5.1 Collection workflow with active protection

Figure 2 depicts the end-to-end collection workflow. For each node, the collector first consults the quarantine module: after two consecutive authentication failures, all access attempts using that credential are automatically suspended on every node linked to it, eliminating the risk of a mass lockout of institutional accounts under local AAA policies. If the credential is enabled, the corresponding driver opens an adaptive SSH session — applying `ssh_compat` promotion where required — handles in-band authentication and privilege elevation, disables paging, and captures the full configuration dump. The dump is then passed through the volatile-pattern filter and validated against a strict end-of-file marker; truncated captures are rejected rather than committed, so a partial transfer can never overwrite a previously functional version. Valid configurations are committed transactionally to the GitStore under a filesystem lock. Collection across nodes uses controlled concurrency with per-device serialization, preventing management-CPU overload on older switches.

*Figure 2. Collection workflow with credential quarantine and truncation rejection. Source: elaborated by the authors.*

### 5.2 Side-by-side difference engine

On top of the Git history, a comparison engine renders parallel (side-by-side) views of any two versions of a device's configuration. Beyond classic line-based differencing [15, 16], the engine tokenizes changed lines at the word and parameter level, so the operator immediately sees the exact parameter that changed — an SNMP community, a VLAN identifier, an ACL entry — rather than scanning a unified plain-text diff.

### 5.3 Digital twin (`fake_device.py`)

The device simulator reproduces, over a real SSH server, the behavioral anomalies observed in the production park: in-band login dialogues, forced paging with interactive "more" prompts, and two-phase privilege elevation with secondary passwords. Integration tests run the full collection pipeline against the simulator, which allows regression certification of every driver — including those for families with low physical availability — without touching the production network. The system formally distinguishes drivers validated in production from drivers implemented from vendor specifications and validated in the simulator; the latter undergo a supervised visual-validation phase on first live deployment (Table 1).

### 5.4 User interfaces

All functions are exposed through two clients that consume the same internal services: a native SPA web interface — implemented with standard web components, without heavy front-end frameworks or build chains — providing the version browser, side-by-side diff viewer, topology map, and findings report; and a CLI console for headless operation, scripted execution, and integration with scheduled tasks.

## 6. Results

### 6.1 Operational impact

Table 3 contrasts the key operational indicators before and after the deployment of the platform in the institutional network. Automated figures were obtained from the platform's own execution logs during the pilot phase: per-device times correspond to complete collection cycles (session establishment, authentication, capture, volatile filtering, and commit) across the device families of Table 1, and the recovery time corresponds to retrieving a device's last committed configuration from the version store and reapplying it. Figures for the traditional method reflect the documented operational practice of the institution prior to the deployment. These figures characterize the observed range across the deployment's device population during a single institutional pilot, rather than a controlled multi-trial statistical sample with reported sample size and dispersion; Section 7.1 discusses this methodological gap and the protocol required to close it.

| Performance indicator | Traditional (manual) method | With Auto-Redes III (automated) |
|---|---|---|
| Backup time per device | 5–15 min per node (interactive access, manual copy and save) | 15–45 s per node (capture, volatile filtering, and commit) |
| Full-network backup time | Several hours (executed sporadically) | < 4 min, unattended |
| Mean time to recovery (MTTR) | Hours to days (manual reconstruction or search of historical backups) | < 2 min (immediate retrieval of the exact functional version) |
| Noise / false positives in version history | Not applicable (no formal version control) | 0% false commits, due to volatile-pattern normalization |
| Traceability and auditability | None or fragmentary | 100% auditable, with a chronological record of every configuration change |

*Table 3. Operational impact metrics of the deployed platform. Source: elaborated by the authors.*

### 6.2 Comparison with generic tooling

During the initial phase, widely adopted tools — particularly Oxidized [1] — were evaluated against the requirements of the legacy park. Table 4 synthesizes the technical rationale that motivated a purpose-built solution. This comparison is qualitative rather than measured; Section 7.1 explains why and outlines a concrete protocol for a quantitative, timed comparison restricted to the modern segment of the network.

| Requirement / technical vector | Behavior of generic solutions (Oxidized) | Auto-Redes III solution | Operational advantage |
|---|---|---|---|
| SSH negotiation with legacy algorithms | Requires relaxing the security of the whole server OS or compiling custom libraries | Temporary, session-scoped promotion of obsolete ciphers (`ssh_compat`) during the handshake | Reliable connectivity with legacy switches without compromising the server's global security posture |
| Interactive elevation with secondary password | Fails, or requires programming complex Ruby extensions for multi-phase interactive prompts | Family-specific driver with sequential dialogue management and elevation prior to capture | Complete, reliable dumps on devices with restricted consoles |
| In-band authentication handling | Tends to interpret the interactive user prompt inside the SSH channel as a connection timeout | Adaptive detection and response to the interactive prompt in the pseudo-terminal | Transparent automation on intermediate-generation switch families |
| Fault tolerance and lockout prevention | Indefinite retries in cron cycles, causing administrative account lockouts on devices with local AAA policies | Quarantine module: after 2 consecutive failures, all attempts with that credential are suspended on all linked nodes | Elimination of the risk of mass lockout of institutional credentials |
| Deployment and maintainability | Ruby ecosystem, gems with C dependencies (`libgit2`), complex configuration on Windows environments | Standard Python, portable, without complex native dependencies or heavy services | Simplified maintenance and full technical transfer to the institution |
| Auditing and topology inference | Limited to plain-text storage; does not interpret configuration semantics | Static analysis engine that generates the L2/L3 network map and audits configuration inconsistencies | Graphical network visibility and proactive detection of human errors in links and addressing |
| Difference visualization | Classic unified plain-text diff output | Side-by-side parallel viewer with word- and parameter-level tokenization | Immediate visual identification of the exact changed parameter (SNMP communities, VLANs, access entries) |

*Table 4. Technical comparison with the open-source reference tool. Source: elaborated by the authors.*

### 6.3 Functional coverage

At the time of writing, the platform has completed the following phases: an adaptive SSH capture engine with multi-vendor support; transactional Git storage with the visual comparison engine; multilevel L2/L3 topology mapping by static analysis; and the hardware-simulation environment for integration testing. Drivers for the highest-density families in the infrastructure are validated in production; the remaining drivers are simulator-validated with a supervised first live run (Table 1).

## 7. Discussion

The results confirm that the dominant open-source pattern for configuration backup — periodic collection plus version control, as established by RANCID [2] and Oxidized [1] — remains the correct architectural skeleton, while showing that its standard implementations embed assumptions incompatible with legacy institutional parks. The three failure modes observed with generic tooling (global cryptographic relaxation, misinterpreted interactive dialogues, and lockout-inducing retry loops) were all eliminated by moving the corresponding logic into per-family drivers and an explicit protection layer, rather than into host-level configuration. This supports the central design claim: in legacy environments, robustness properties must be first-class features of the management platform, not side effects of server configuration.

The static topology-inference approach trades completeness for safety. Because it emits no traffic and requires no discovery protocols on the devices [8], it can be applied to the most fragile segments of the network; its cost is that VLAN-level deductions identify trunk adjacency but not always the exact physical port, which is precisely the gap the planned MAC-table ingestion addresses (Section 9). Table 2 grades inferred links by the strength of their static evidence rather than presenting them as uniformly reliable; Section 7.1 discusses why this remains a transparency safeguard rather than a statistically validated metric.

### 7.1 Limitations and threats to validity

The present evaluation has three concrete gaps that a demanding empirical standard should flag explicitly, and each has a well-defined path to closure that the authors have not yet executed.

First, statistical rigor of the operational metrics (Table 3): the reported ranges were read directly from the platform's execution logs during a single institutional deployment, without recording the sample size (number of devices per family, number of collection cycles) or computing dispersion statistics. This gap does not require a new experiment: because every successful collection is already committed to Git as an atomic, timestamped transaction (Section 3), the commit history of the deployment's GitStore already contains, for every device family, the raw timestamps needed to compute *n*, mean, and standard deviation — or, given the expected skew toward slower legacy devices, median and interquartile range — in place of the observed range currently reported. The one methodological refinement such an analysis needs is distinguishing cycle duration from commit time: a commit timestamp marks the end of a collection cycle, not its start, so per-device duration must either be read from a separate start-of-cycle log entry where one exists, or approximated from the interval between consecutive commits under the collection workflow's own per-device serialization (Section 5.1) — a valid but coarser proxy that should be reported as such. Extracting and reporting this analysis from the existing GitStore history is retained as an immediate next step rather than a future controlled study; the extraction script itself (`analyze_gitstore_timings.py`) is already implemented and included in the project repository, and only needs to be pointed at the deployment's GitStore to reproduce Table 3 with measured figures.

Second, the topology-inference algorithm (Section 4.4) has not been validated against a ground-truth topology. The evidentiary tiers in Table 2 describe the logical or heuristic strength of the static evidence used to infer a link, not a statistically calibrated confidence score, and no precision or recall figures are reported because no independent reference topology was compared against the algorithm's output. Closing this gap requires assembling a ground-truth map from the manual surveys historically used to document the network (Section 1) — for at least one representative segment — and computing precision and recall separately for each evidentiary tier, which would also indicate whether the deterministic tier is empirically as reliable in practice as its logical justification suggests.

Third, the comparison with Oxidized (Table 4, Section 6.2) is qualitative on every vector. This is an unavoidable limitation on the legacy segments, where Oxidized cannot operate safely at all (Section 6.2); it is not unavoidable, however, on the modern edge and expansion segments (Cisco IOS/IOS-XE, MikroTik RouterOS, TP-Link JetStream/ER — Table 1), which are standards-compliant enough for Oxidized to run. A quantitative head-to-head timing comparison restricted to those devices — running both tools against the same nodes across a matched number of trials — is feasible with the infrastructure already in production and is the most immediately actionable extension of this evaluation.

### 7.2 Design limitations and security considerations

Three further design limitations and security considerations deserve emphasis. First, controlled concurrency and commit serialization protect both the management CPU of older switches and the consistency of the Git index, at the cost of a bounded increase in total collection time — an acceptable trade-off given the sub-4-minute full-network figure (Table 3). Second, configuration dumps contain password hashes and SNMP management parameters; the repository must therefore reside in a strictly private environment, and the system complementarily integrates a cryptographic sanitization module for contexts that require secret anonymization [21]. Third, the formal distinction between production-validated and simulator-validated drivers acknowledges that a digital twin, however faithful [18], cannot fully substitute first-contact validation on real hardware.

### 7.3 Pedagogical dimension

Finally, the project has a deliberate pedagogical dimension. Developed within the Network Automation Project III, the system articulates data-network concepts (link and network layers, VLANs, routing) with modern software-engineering practice (version control, API design, concurrency, text analysis), and its fully documented development serves as reference material and a laboratory base for future academic cohorts.

## 8. Conclusions

The platform developed for the Network Automation Project III demonstrates that the application of software-engineering and infrastructure-as-code principles can resolve complex operational problems in heterogeneous, legacy-laden networks. By providing a safe backup workflow, rigorous Git-based traceability, automated topology deduction, and active hardware-protection mechanisms, the system was observed, in a single-site pilot deployment, to reduce per-device backup time by roughly an order of magnitude, bring full-network unattended backup under four minutes, and cut the mean time to recovery from hours or days to under two minutes, while producing a configuration history that is fully auditable and free of volatile noise. Section 7.1 details the statistical and comparative rigor a follow-up evaluation would still need to add.

The comparative analysis against reference tooling shows that the decisive advantages did not come from re-implementing existing functionality, but from treating the constraints of legacy equipment — obsolete cryptography, interactive consoles, lockout-prone AAA policies — as primary design requirements. The resulting platform is lightweight, portable, fully transferable to the institution, and doubles as a methodological framework for advanced technical training.

## 9. Future Work

Planned extensions follow four lines. First, fine physical resolution of trunk links: ingesting and correlating MAC address tables to assign, with absolute precision, the physical port number to links currently deduced at the VLAN level. Second, structured-cabling registration: a versioned scheme to document static fiber and copper runs that carry no software-deducible frames. Third, remote configuration restoration and provisioning from the web interface, strictly conditioned on the prior incorporation of an authentication and role-based access control (RBAC) layer for the web API. Fourth, health supervision and telemetry (Phase 3): availability and link-state monitoring in near real time through lightweight ICMP/SNMP probes [20], keeping the platform's zero-overhead philosophy.

## Acknowledgment

This work was developed within the framework of the Network Automation Project III. \[Institutional acknowledgment to be completed.\]

## References

[1] Ytti, S., et al. Oxidized: A network device configuration backup tool. https://github.com/ytti/oxidized

[2] Shrubbery Networks. RANCID — Really Awesome New Cisco confIg Differ. https://shrubbery.net/rancid/

[3] NAPALM Automation Community. NAPALM: Network Automation and Programmability Abstraction Layer with Multivendor support. https://napalm.readthedocs.io/

[4] Byers, K. Netmiko: Multi-vendor library to simplify CLI connections to network devices. https://github.com/ktbyers/netmiko

[5] Ylonen, T., Lonvick, C. (2006). The Secure Shell (SSH) Protocol Architecture. RFC 4251, IETF. https://www.rfc-editor.org/rfc/rfc4251

[6] Ylonen, T., Lonvick, C. (2006). The Secure Shell (SSH) Transport Layer Protocol. RFC 4253, IETF. https://www.rfc-editor.org/rfc/rfc4253

[7] Baushke, M. (2022). Key Exchange (KEX) Method Updates and Recommendations for Secure Shell (SSH). RFC 9142, IETF. https://www.rfc-editor.org/rfc/rfc9142

[8] IEEE. (2016). IEEE Standard for Local and Metropolitan Area Networks — Station and Media Access Control Connectivity Discovery. IEEE Std 802.1AB-2016.

[9] Chacon, S., Straub, B. (2014). Pro Git. 2nd ed., Apress.

[10] Morris, K. (2020). Infrastructure as Code: Dynamic Systems for the Cloud Age. 2nd ed., O'Reilly Media.

[11] Enns, R., Bjorklund, M., Schoenwaelder, J., Bierman, A. (2011). Network Configuration Protocol (NETCONF). RFC 6241, IETF. https://www.rfc-editor.org/rfc/rfc6241

[12] Benson, T., Akella, A., Maltz, D.A. (2009). Unraveling the complexity of network management. In: Proceedings of the 6th USENIX Symposium on Networked Systems Design and Implementation (NSDI '09), pp. 335-348.

[13] Oppenheimer, D., Ganapathi, A., Patterson, D.A. (2003). Why do Internet services fail, and what can be done about it? In: Proceedings of the 4th USENIX Symposium on Internet Technologies and Systems (USITS '03).

[14] Kim, H., Feamster, N. (2013). Improving network management with software defined networking. IEEE Communications Magazine, 51(2): 114-119. https://doi.org/10.1109/MCOM.2013.6461195

[15] Myers, E.W. (1986). An O(ND) difference algorithm and its variations. Algorithmica, 1(1): 251-266. https://doi.org/10.1007/BF01840446

[16] Hunt, J.W., McIlroy, M.D. (1976). An algorithm for differential file comparison. Computing Science Technical Report 41, Bell Laboratories.

[17] Retana, A., White, R., Fuller, V., McPherson, D. (2000). Using 31-Bit Prefixes on IPv4 Point-to-Point Links. RFC 3021, IETF. https://www.rfc-editor.org/rfc/rfc3021

[18] Grieves, M., Vickers, J. (2017). Digital twin: Mitigating unpredictable, undesirable emergent behavior in complex systems. In: Transdisciplinary Perspectives on Complex Systems, Springer, pp. 85-113. https://doi.org/10.1007/978-3-319-38756-7_4

[19] Paramiko Project. Paramiko: A Python implementation of the SSHv2 protocol. https://www.paramiko.org/

[20] Case, J., Fedor, M., Schoffstall, M., Davin, J. (1990). A Simple Network Management Protocol (SNMP). RFC 1157, IETF. https://www.rfc-editor.org/rfc/rfc1157

[21] Joint Task Force. (2020). Security and Privacy Controls for Information Systems and Organizations. NIST Special Publication 800-53, Revision 5. https://doi.org/10.6028/NIST.SP.800-53r5

[22] Feamster, N., Rexford, J., Zegura, E. (2014). The road to SDN: An intellectual history of programmable networks. ACM SIGCOMM Computer Communication Review, 44(2): 87-98. https://doi.org/10.1145/2602204.2602219

## Nomenclature

| Abbreviation | Meaning |
|---|---|
| AAA | Authentication, Authorization, and Accounting |
| ACL | Access Control List |
| CDP | Cisco Discovery Protocol |
| CLI | Command-Line Interface |
| IaC | Infrastructure as Code |
| LAG | Link Aggregation Group |
| LLDP | Link Layer Discovery Protocol |
| MTTR | Mean Time to Recovery |
| NCM | Network Configuration Management |
| RBAC | Role-Based Access Control |
| SPA | Single-Page Application |
| SSH | Secure Shell |
| SVI | Switch Virtual Interface |
| VLAN | Virtual Local Area Network |

## Appendix

Minimum environment and deployment requirements: a standard Python 3 runtime with no external relational database manager and no front-end build chain; Git available on the management host for the version store; network reachability (SSH) from the management host to the administered devices; and a strictly private location for the configuration repository, given that dumps contain password hashes and SNMP management parameters. The device simulator (`fake_device.py`) allows the full pipeline to be exercised on any workstation without access to production hardware.

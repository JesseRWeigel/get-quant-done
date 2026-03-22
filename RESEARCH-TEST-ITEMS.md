# Research Test Items for Get-X-Done Systems

> Concrete research problems to test each domain's copilot on real work.
> These should be genuine, publishable research tasks — not toy problems.

---

## Get Math Done — Test Research Items

### GMD-T1: Chromatic Number Bounds for Random Graphs (Combinatorics)
**Problem**: Prove tighter bounds on the chromatic number of Erdős–Rényi random graphs G(n,p) in the regime p = c/n for c near the colorability threshold.
**Why good test**: Requires probabilistic method, second moment method, known literature to compare against (Achlioptas, Naor). Tests counterexample search, convergence verification, and special case checking (c=1, c=2).
**Expected difficulty**: Medium — extends known results with new technique.

### GMD-T2: Spectral Gap Estimates for Graph Laplacians (Spectral Theory)
**Problem**: Derive spectral gap estimates for normalized Laplacians of expander graph families, comparing algebraic and Cheeger-type bounds.
**Why good test**: Requires linear algebra + functional analysis protocols, convergence verification for eigenvalue computations, and comparison with known Ramanujan graph bounds.
**Expected difficulty**: Medium — computational + theoretical.

### GMD-T3: Fixed Point Theorems in Non-Archimedean Analysis (Analysis)
**Problem**: Extend Banach fixed point theorem to ultrametric spaces with relaxed contraction conditions. Characterize when unique fixed points exist.
**Why good test**: Tests base case verification, assumption tracking (which properties of the metric are actually used), and constructive witness (producing the fixed point).
**Expected difficulty**: Medium-hard.

### GMD-T4: Counting Lattice Points in Polytopes (Number Theory / Combinatorics)
**Problem**: Derive Ehrhart-type formulas for specific families of lattice polytopes (e.g., order polytopes of posets), connecting to combinatorial reciprocity.
**Why good test**: Tests algebra + combinatorics protocols, sign error detection (E001), and known identity matching (Ehrhart reciprocity).
**Expected difficulty**: Medium.

### GMD-T5: Homological Dimension of Monoid Algebras (Algebra)
**Problem**: Compute the global dimension of semigroup algebras for specific classes of commutative monoids, extending results of Nico and Kobayashi.
**Why good test**: Tests algebra protocols, category theory conventions, literature comparison with published computations.
**Expected difficulty**: Hard.

---

## Get Review Done — Test Research Items

### GRD-T1: Effectiveness of AI Tutoring in K-12 Mathematics Education
**Problem**: Systematic review and meta-analysis of randomized controlled trials examining AI-powered tutoring systems' effect on mathematics achievement in K-12 students.
**Why good test**: Active field with growing literature (2020-2026), well-defined PICO, multiple databases needed, moderate heterogeneity expected.
**Expected output**: PRISMA-compliant manuscript with forest plots, subgroup analysis by grade level and intervention type.

### GRD-T2: Mental Health Outcomes of Remote Work
**Problem**: Systematic review of longitudinal studies on the association between remote/hybrid work arrangements and mental health outcomes (depression, anxiety, burnout) in knowledge workers.
**Why good test**: High public interest, mixed evidence, needs careful study design classification (RCT vs cohort vs cross-sectional), publication bias likely.
**Expected difficulty**: Medium — large literature, complex quality assessment.

### GRD-T3: Efficacy of Psychedelic-Assisted Therapy for PTSD
**Problem**: Meta-analysis of clinical trials examining psilocybin and MDMA-assisted therapy for treatment-resistant PTSD.
**Why good test**: Rapidly evolving field (FDA breakthrough therapy designation), small but growing trial base, strong interest from regulators and clinicians.
**Expected difficulty**: Medium — fewer studies but high methodological rigor needed.

---

## Get Legal Done — Test Research Items

### GLD-T1: AI-Generated Content and Fair Use
**Problem**: Research memorandum analyzing whether training AI models on copyrighted works constitutes fair use under 17 U.S.C. § 107, synthesizing recent case law (Andersen v. Stability AI, Thomson Reuters v. Ross Intelligence, NYT v. OpenAI).
**Why good test**: Active, evolving area of law with multiple circuit-level cases. Tests citation verification heavily (many fake AI law citations circulate). Requires statutory analysis + case law synthesis.
**Expected output**: 20-30 page research memorandum with verified citations.

### GLD-T2: State Privacy Law Compliance Analysis
**Problem**: Comparative analysis of data privacy obligations under CCPA/CPRA, Virginia CDPA, Colorado Privacy Act, and Connecticut Data Privacy Act for a SaaS company processing consumer health data.
**Why good test**: Multi-jurisdictional statutory analysis, requires current statute versions, frequent amendments. Tests statutory currency verification.
**Expected difficulty**: Medium — statutory analysis with clear framework.

### GLD-T3: Employment Non-Compete Enforceability Post-FTC Rule
**Problem**: Brief analyzing enforceability of existing employee non-compete agreements following the FTC's 2024 non-compete ban rule, addressing constitutional challenges and state law interaction.
**Why good test**: Regulatory + constitutional + employment law intersection. Tests multiple protocols. Citation verification critical given rapidly changing law.
**Expected difficulty**: Hard — unsettled area with conflicting rulings.

---

## Get Quant Done — Test Research Items

### GQD-T1: Volatility Surface Dynamics Under Rough Volatility Models
**Problem**: Compare pricing accuracy of rough Bergomi, rough Heston, and classical Heston models for SPX options across strikes and maturities, using 2020-2025 market data.
**Why good test**: Requires option pricing protocols, convergence verification for Monte Carlo, comparison with market data, sensitivity analysis.
**Expected output**: Paper with calibration results, pricing error analysis, model comparison.

### GQD-T2: Machine Learning Alpha Signal Decay Analysis
**Problem**: Quantify the decay rate of common ML-based alpha signals (momentum, mean reversion, NLP sentiment) in US equities over 2015-2025, with proper out-of-sample testing.
**Why good test**: Tests backtesting integrity (no look-ahead bias), statistical significance (multiple testing correction), robustness checks.
**Expected difficulty**: Medium — empirical with strong methodology requirements.

### GQD-T3: Tail Risk Hedging Efficiency
**Problem**: Analyze cost-efficiency of tail risk hedging strategies (put spreads, VIX calls, variance swaps) across different market regimes, measured by conditional Sharpe ratios.
**Why good test**: Risk measure coherence, boundary conditions (deep OTM), distribution validity checks, and robustness across regimes.

---

## Get Engineering Done — Test Research Items

### GED-T1: Topology Optimization of Lattice Structures for Additive Manufacturing
**Problem**: Design minimum-weight lattice structures for a given loading condition using topology optimization with manufacturing constraints (minimum member size, overhang angle limits).
**Why good test**: FEA convergence, dimensional analysis, boundary conditions, comparison with analytical solutions for simple cases.

### GED-T2: Seismic Performance Assessment of CLT (Cross-Laminated Timber) Buildings
**Problem**: Nonlinear dynamic analysis of a 6-story CLT building under suite of ground motions, comparing performance against code-based design criteria (ASCE 7-22).
**Why good test**: Code compliance, convergence verification, material limits, comparison with steel/concrete benchmarks.

### GED-T3: Wind Load Analysis for Solar Panel Arrays
**Problem**: CFD + structural analysis of wind loads on ground-mounted solar panel arrays, with comparison to ASCE 7 component and cladding coefficients.
**Why good test**: Dimensional analysis, CFD convergence, code compliance, experimental data comparison.

---

## Get Chem Done — Test Research Items

### GCD-T1: Benchmarking DFT Functionals for Transition Metal Complexes
**Problem**: Systematic benchmark of 10+ DFT functionals for spin-state energetics of first-row transition metal complexes, comparing with CCSD(T) reference values.
**Why good test**: Basis set convergence, functional sensitivity, comparison with experimental and high-level computational data.

### GCD-T2: Binding Affinity Predictions for SARS-CoV-2 Protease Inhibitors
**Problem**: Molecular docking + MM-PBSA binding free energy calculations for a set of candidate protease inhibitors, validated against published IC50 data.
**Why good test**: Multiple computational protocols, thermodynamic consistency, experimental validation.

---

## Get Bio Done — Test Research Items

### GBD-T1: Differential Expression Analysis of Alzheimer's Disease Bulk RNA-seq
**Problem**: Re-analysis of public Alzheimer's disease bulk RNA-seq datasets (ROSMAP, Mayo) with updated pipeline (STAR + DESeq2), identifying consistently differentially expressed genes across cohorts.
**Why good test**: Pipeline reproducibility, batch effect correction, multiple testing, comparison with published results.

### GBD-T2: Single-Cell Atlas of Tumor Microenvironment
**Problem**: Integrate and annotate public scRNA-seq datasets from solid tumors to build a pan-cancer tumor microenvironment cell atlas.
**Why good test**: Normalization, batch correction across datasets, clustering validation, biological plausibility.

---

## Get Policy Done — Test Research Items

### GPAD-T1: Cost-Benefit Analysis of Universal Pre-K Programs
**Problem**: CBA of expanding universal pre-kindergarten to all 3- and 4-year-olds, including long-term benefits (educational attainment, earnings, reduced crime) discounted to present value.
**Why good test**: Discount rate sensitivity, baseline construction, distributional analysis, comparison with existing CBAs (Heckman, Barnett).

### GPAD-T2: Regulatory Impact of AI Disclosure Requirements
**Problem**: Regulatory impact assessment of proposed mandatory AI system disclosure requirements for high-risk applications, estimating compliance costs and expected reduction in AI-related harms.
**Why good test**: Novel policy area, limited precedent for comparison, requires multi-stakeholder analysis, uncertainty quantification.

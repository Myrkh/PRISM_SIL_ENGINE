# p4-p24 — Markdown transcription (from `docs/theory/p4-p24.pdf` pages 4–27)

> Source file: `docs/theory/p4-p24.pdf`.
> Scope: pages 4 to 27.
> This file is structured for readability and keeps tables in standard Markdown format.

## Page 4

@ SINTEF Reliability Data for Safety Equipment 45 4.6 a7 References PDS Data Handbook, 2021 Edition 4.4.34 Lifeboat Radio.... 4.4.35 PA Loudspeakers........ Subsea Equipment 4.5.1 Subsea Pressure Sensor 4.5.2 Subsea Temperature Sensor...... 4.5.3 Combined Subsea Pressure and Temperature Sensor .. 4.5.4 Subsea Flow Sensol 4.5.5 Subsea Sand Detectol 4.5.6 Master Control Station ... 4.5.7 Umbilical Hydraulic/Chemical Line 4.5.8 Umbilical Power/Signal Line....... 4.5.9 Subsea Solenoid Control Valves .... 4.5.10 Subsea Electronic Module 4.5.11 Subsea Manifold Isolation Valve 4.5.12 Subsea XT Valves PMV, PWV .. 4.5.13 Subsea XT Valves XOV. 4.5.14 Subsea XT Valves AMV... 4.5.15 Subsea XT Valves CIV, MIV. 4.5.16 Subsea Isolation Valves SSIV....... Downhole Well Completion Equipment 4.6.1 Downhole Safety Valves DHSV 4.6.2 Downhole Safety Valve TRSCSSV 4,6.3 Downhole Safety Valve - WRSCSSV 4.6.4 Annulus Subsurface Safety valve -~ TRSCASSV, type A.. 4.6.5 Annulus Subsurface Safety Valves TRSCASSV, type B 4.6.6 Wire Retrievable Chemical Injection Valves ~ WRCIV....... 4.6.7 Tubing Retrievable Chemical Injection Valves TRCIV 4.6.8 Gas Lift Valves - GLV. Drilling Equipment 4.7.1 Annular Preventer ... 4.7.2 Ram Preventer... 4.7.3 Choke and Kill Valv 4.7.4 Choke and Kill Line... 4.7.5 Hydraulic Connector.... 4.7.6 Multiplex Control System 4.7.7 Pilot Control System..... 4.7.8 Acoustic Backup Control System .......

## Page 5

Reliability Data for Safety Equipment G SINTEF PDS Data Handbook, 2021 Edition PREFACE SINTEF is proud to present this new 2021 edition of the PDS' data handbook. As compared to the 2013 edition of the PDS data handbook [1], the historical data basis has been greatly expanded and the detailing and assessment of the data have been significantly improved. The data have been subject to extensive quality assurance, where equipment experts and operational personnel have gone through and classified some thirty thousand maintenance notifications and work orders manually. As to our knowledge, this represents one of the broadest and best documented data bases for safety equipment, worldwide. The work has been carried out as part of the research project Automized process for follow-up of safety instrumented systems” (APOS) and has been funded by SINTEF, the Research Council of Norway, the APOS project members and the PDS forum participants. We would like to thank everyone who has provided us with quality assured reliability data, comments, and valuable input to this PDS data handbook. Trondheim, May 2021 PDS Forum Participants as per 2021 Petroleum Companies / Operators: Engineering Companies and Consultants: ® AkerBP * Aibel ® Altera Infrastructure ® Aker Solutions * ConocoPhillips Norge « DNV Norge * Equinor * ORS Consulting * Gassco * Proactima * Lundin Energy * Rosenberg WorleyParsons * Neptune Energy e Safetec Nordic * Norske Shell e TechnipFMC * OKEA ® Vysus Group * Repsol Norge ® VarEnergi Governmental Bodies (Observers): « Norwegian Maritime Directorate Control and Safety System Vendors: = Petroleum Safety Authority Norway ABB Emerson Honeywell Kongsherg Maritime Optronics Technology Origo Solutions Siemens Energy ! PDS is a Norwegian acronym for reliability of Safety Instrumented Systems. See also www.sintef.no/pds.

## Page 6

O SINTEF Reliability Data for Safety Equipment PDS Data Handbook, 2021 Edition 1 INTRODUCTION 1.1 Objective and Scope The use of realistic failure data is an essential part of any quantitative reliability analysis. It is also one of the most challenging parts and raises several questions concerning the suitability of the data, the assumptions underlying the data and the uncertainties related to the data, This handbook provides reliability data for safety equipment, including components of safety instrumented systems, subsea and drilling equipment and selected non-instrumented safety critical equipment such as valves, fire-fighting equipment, fire and gas dampers, fire doors, etc. Efforts have been made to document the presented data thoroughly, both in terms of applied data sources, underlying assumptions, and uncertainties in terms of confidence limits. Compared to the 2013 version, the main changes and improvements are: o Greatly expanded data basis, including comprehensive and more recent operational experience. e New equipment groups have been added, and more detailed failure rates, differentiating on attributes such as dimension, measuring principle, medium, etc., are given for selected sensors and final elements. e Updated common cause factors (B values) based on an extensive field study of some 12.000 maintenance notifications, as described in [3]. e Updated values for diagnostic coverage (DC) and random hardware fraction (RHF) based on operational experience, vendor certificates and discussions with equipment experts. « Improved data traceability and a more detailed assessment of failure rate uncertainty. In addition, failure rates, equipment boundaries including a definition of dangerous (or safety critical) failure, and other relevant information and parameters have been reviewed and updated for all components. This data handbook may also be used in conjunction with the PDS method handbook [2]%, which describes a practical approach for calculating the reliability of safety systems. 1.2 ThelEC 61508 and 61511 Standards The IEC 61508 and IEC 61511 standards, [4] and [5], present requirements to SIS for all relevant lifecycle phases, and have become leading standards for SIS specification, design, implementation, and operation. IEC 61508 is a generic standard common to several industries, whereas IEC 61511 has been developed especially for the process industry. The Norwegian Oil and Gas Association (NOROG) has also developed a guideline to support the use of [EC 61508 / 61511 in the Norwegian Petroleum Industry [6]. A fundamental concept in both IEC 61508 and [EC 61511 is the notion of risk reduction; the higher the risk reduction is required, the higher the SIL. It is therefore important to apply realistic failure data in the design calculations, since too optimistic failure rates may suggest a higher risk reduction than what is obtainable in operation. In other words, the predicted risk reduction, calculated for a safety function in the design phase, should to the degree possible reflect the actual risk reduction that is experienced in the operational phase, see also [6]. This is also emphasized in the second edition of IEC 61511-1 (sub clause 11.9.3) [4] which states that the applied reliability data shall be credible, traceable, documented and justified and shall be based on field feedback from similar devices used in a similar operating environment. It is therefore recommended [6] to use data based on actual historic field experience when performing reliability calculations. The PDS method handbook is currently under revision. A new version is planned to be issued early 2022.

## Page 7

Reliability Data for Safety Equipment O SINTEF PDS Data Handbook, 2021 Edition The reliability data in this PDS handbook represent collected experience from operation of safety equipment, mainly in the Norwegian oil and gas industry. As such, the PDS data and associated method are in line with the main principles advocated in the IEC standards, and the data presented in this handbook are on a format suitable for performing reliability calculations in line with the IEC standards. 1.3 Data Sources The most important data source for this handbook is extensive operational experience gathered from Norwegian offshore (and some onshore) oil and gas facilities during the last 10-15 years. Data from 54 different facilities and seven different operators, are represented. In fact, the total accumulated experience sums up to more than 3 billion operational hours for topside equipment and more than 750 million operational hours for subsea and well completion equipment. Note that these data have been subject to extensive quality assurance through the fact that equipment experts and operational personnel have gone through and classified thousands of maintenance notifications and work orders manually. As to our knowledge, this represents one of the broadest and best documented data bases for safety equipment, worldwide. Other data sources applied include: OREDA reliability data handbooks, subsea BOP data from Exprosoft, RNNP, manufacturer data and certificates, in addition to various data studies and expert judgements. Each of the data sources applied in this handbook are briefly discussed in Table 1.1. Table 1.1: Discussion of applied data sources Data source Description Relevance of data in present handbook Operational Experience data from operational The operational reviews represent the review data reviews on Norwegian offshore and most important data source in this onshore facilities. Equipment experts handbook, particularly due to the thorough from the operator, often together with failure classification, extensive personnel from a consultant (SINTEF or | population, and the fact that the data have other), have assessed failures been collected recently, i.e., during the last (notifications and work orders) 1015 years. The operational reviews are registered in maintenance databases and | the main data source for topside have classified each failure (typically equipment, and an important data source into categories DU, DD, S, non-critical). | for subsea and well completion equipment. WellMaster WellMaster RMS (Reliability WellMaster data is the main data source RMS, [13] Management System) is a world leading | for several subsea and well completion well and subsea equipment reliability equipment groups, including both topside database and analysis solution for oil and || and subsea located wells. As for the data gas operators. It is utilized through the from operational reviews, the WellMaster full well life cycle, from designing better | data have been subject to extensive quality wells and selecting better equipment, to || assurance and failure classification. risk assessment, well integrity analysis, and remaining life assessments. Subsea BOP | From 1983 to 2019, SINTEF and The latest study Subsea BOP Reliability, data, [14] Exprosoft have documented results from || Testing, and Well Kicks [15] was several detailed reliability studies of completed in October 2019. This study subsea blowout preventer (BOP) was based on experience from well systems. A total of nearly 1000 wells operations in Norwegian waters in the have been reviewed with respect to period 2016-2018. Most wells were subsea BOP reliability. drilled in water depths less than 500 meters.

## Page 8

@ SINTEF Reliability Data for Safety Equipment PDS Data Handbook, 2021 Edition Data source Description Relevance of data in present handbook The study Reliability of Deepwater Subsea BOP Systems and Well Kicks [16] was completed in 2012. The study was based on wells drilled in water-depths deeper than 600m in the period 2007 - 2010 in US GoM OCS (Outer Continental Shelf). These two studies, in addition to [17], [18] and Exprosoft expert judgements have been used as basis for the subsea BOP failure rates. Expert judgements Discussions and meetings with experts (operators and manufacturers) provide essential input to this handbook. This includes numerous virtual and physical meetings, PDS workshops, as well as extensive mail and telephone correspondence. Expert judgements have been important to enable data differentiation and to establish diagnostic coverage and proof test coverage values. Expert judgements have been particularly important to establish data for control logic since limited operational data have been available. OREDA reliability data handbooks, (9] OREDA is a project organisation whose main purpose is to collect and exchange reliability data among the participating companies, see www.oreda.com. The OREDA handbooks contain failure data (failure mode and failure severity) for a broad group of components within oil and gas production. OREDA has been applied as a data source for some subsea equipment groups, and as part of the input to estimate the distribution between dangerous and safe failures and RHF values. Manufacturer data/ equipment certificates Failure data, e.g., in the form of equipment certificates or assessment reports, prepared for specific products. The data can be based on component FMECA/FMEDA studies, laboratory testing, and in some cases also field experience. Manufacturer data have been particularly relevant for equipment with limited operational experience, such as control logic. Furthermore, equipment certificates’ have provided valuable input to diagnostic coverage values. RNNP, [20] Failure data from the RNNP project for selected safety critical equipment. The RNNP data comprise a high number of facilities on the Norwegian Continental Shelf. The RNNP data also include all components within the specified equipment groups, giving a very high overall operational time. RNNP data contain results from the period 2003— 2018. i RNNP data mainly include results from functional testing, implying that failures detected otherwise are normally not included. Therefore, the failure rates may be optimistic for equipment groups where failures are also detected between tests (e.g., for valves, fire doors, etc.). RNNP only includes selected equipment, and the degree of detailing is limited (e.g., all gas detectors are grouped together, and test intervals are not explicitly stated). Therefore, RNNP data have been applied as a data source only for selected equipment groups such as e.g., deluge valves and downhole safety valves. 3 See e.g., www.exida.com

## Page 9

Reliability Data for Safety Equipment G SINTEF PDS Data Handbook, 2021 Edition 1.4 Organisation of the Data Handbook In chapter 2, important reliability concepts are discussed and defined. Failure classification for safety equipment is presented together with the main reliability performance measures used in the IEC standards and in PDS. The reliability data are summarised in chapter 3. A split has been made between topside equipment, subsea and downhole well completion equipment, and drilling equipment. Chapter 3 also includes main considerations and assumptions behind the given parameter values. In chapter 4 all the detailed data dossiers with data sources and failure rate assessments are presented, including an explanation of the various data dossier fields. Finally, a list of references, i.., reports, standards, guidelines, and other relevant data sources and documents, is included. 1.5 List of abbreviations General terms CCF - Common cause failure cSsu - Critical safety unavailability D - Dangerous DC - Diagnostic coverage DD - Dangerous detected DU - Dangerous undetected ESD - Emergency shutdown FMECA - Failure modes, effects, and criticality analysis FMEDA - Failure modes, effects, and diagnostic analysis F&G - Fire and gas FTA - Fault tree analysis HC - Hydrocarbon HMI - Human machine interface IEC - International electro-technical commission IR - Infrared 1SO - International organization for standardization mA - Milliampere MoC - Management of change MooN - M-out-of-N MTTF - Mean time to failure MTTR - Mean time to restoration MUX - Multiplex NA - Not applicable NDE - Normally de-energised NE - Normally energised NOG/NOROG - Norwegian oil and gas association OREDA - Offshore reliability data PA - Public address PDS - Norwegian acronym for reliability of computer-based safety systems™ PFD - Probability of failure on demand PFH - Probability of failure per hour (or average frequency of failure per hour) PSD - Process shutdown PST - Partial stroke test PTC - Proof test coverage

## Page 10

O SINTEF Reliability Data for Safety Equipment PDS Data Handbook, 2021 Edition RBD - Reliability block diagram RH - Random hardware RHF - Random hardware fraction RNNP - Project on risk level in the Norwegian petroleum production S - Safe SFF - Safe failure fraction SIF - Safety instrumented function SIL - Safety integrity level SIS - Safety instrumented system SOLAS - Safety of life at sea TIF - Test independent failure uv - Ultraviolet Technical (equipment related) terms Al - Analogue input AMV - Annulus master valve ASV - Annulus safety valve BPCS - Basic process control system BOP - Blowout preventer CAP - Critical action panel CCR - Central control room CIESDV - Chemical injection emergency shutdown valve CcIv - Chemical injection valve CLU - Control logic unit CPU - Central processing unit DCP - Driller's control panel DHSV - Downhole safety valve DO - Digital output ESV - Emergency shutdown valve FOV - Fast opening valve GLESDV - Gas lift emergency shutdown valve GLV - Gas lift valve HART - Highway addressable remote transducer (protocol) HASCV - Hydraulically actuated safety check valve HIPPS - High integrity pressure protection system HXT - Horizontal X-mas tree LMRP - Lower marine riser package MCS - Master control station MIv - Methanol injection valve PLC - Programmable logic controller PMV - Production master valve PPS - Pressure protection system PSS - Programmable safety system PSV - Pressure relief valve PWV - Production wing valve Qsv - Quick closing shut-off valve SAS - Safety and automation system SCM - Subsea control module SEM - Subsea electronic module SPM - Side-pocket mandrel SSIv - Subsea isolation valve TCP - Toolpusher's control panel TRCIV - Tubing retrievable chemical injection valve

## Page 11

@ SINTEF TRSCSSV TRSCASSV ups WRCIV WRSCSSV XT Xov XV Reliability Data for Safety Equipment PDS Data Handbook, 2021 Edition Tubing retrievable surface-controlled subsurface valve Tubing retrievable surface-controlled annulus subsurface valve (also abbr. ASV) Uninterruptable power supply Wire retrievable chemical injection valve Wireline retrievable surface-controlled subsurface valve X-mas tree Crossover valve Production shutdown valve Failure mode abbreviations AIR BRD DOP ELP ELU ERO FTC FTR FTO FTR FTS HIO INL LAP Lce LOO NONC NOO PLU PRD SPO STP uUsT Abnormal instrument reading Breakdown Delayed operation External leakage process medium External leakage utility medium Erratic output Fail to close on demand Fail to function on demand Fail to open on demand Fail to regulate Fail to start on demand High output Internal leakage utility medium Leakage across packer Leakage in closed position Low output Non-critical No output Plugged/choked Premature disconnect Spurious operation Fail to stop on demand Spurious stop (unexpected stop)

## Page 12

Reliability Data for Safety Equipment G SINTEF PDS Data Handbook, 2021 Edition 2 RELIABILITY CONCEPTS  THE PDS METHOD The PDS method has been developed to enable safety and reliability engineers to perform reliability calculations in various phases of a project. This chapter presents some main characteristics of the PDS method, the failure classification scheme, and reliability performance measures. Please note that the objective is not to give a full and detailed presentation of the method, but to introduce the model taxonomy and some basic ideas. For a more comprehensive description of the PDS method and the detailed formulas, see the PDS method handbook, [2]. 2.1 The PDS Method For estimating SIS reliability, different calculation approaches can be applied, including analytical formulas, Boolean approaches like reliability block diagrams (RBD) and fault tree analysis (FTA), Markov modelling and Petri Nets (see IEC 61508-6, Annex B). The IEC standards do not mandate one specific approach or a set of formulas but leave it to the user to choose the most appropriate approach for quantifying the reliability of a given system or function. The PDS method includes a set of analytical formulas and concepts to quantify loss of safety [2], and together with the PDS data, it offers an effective and practical approach towards implementing the quantitative aspects of the IEC standards. In the following sections some main characteristics of the PDS method are briefly introduced, including important notation and classification schemes. 2.2 Notation and Definitions Table 2.1 presents some main parameters and performance measures used in the PDS method and in this data handbook. Table 2.1 Performance measures and reliability parameters Term | Description Acrie | Rate of critical failures. Critical failures include dangerous (D) failures which may cause loss of the ability to shut down production (or go to a safe state) when required, plus safe (S) failures which may cause loss of the ability to maintain production when safe (e.g., spurious trip failures). Hence: Acrie = Ap + Ag (see below). Ap | Rate of dangerous failures, including both undetected and detected failures. Ap = Apy + App (see below). Apy || Rate of dangerous undetected (DU) failures, i.e., dangerous failures undetected by automatic self-test (only revealed by a functional test or upon a planned or unplanned demand). Apu—ry| The rate of dangerous undetected failures (Apy), originating from random hardware failures. Rate of dangerous detected failures, i.e., dangerous failures detected upon occurrence by e.g. App self-diagnostics. s Rate of safe failures, i.e., failures that either cause a spurious operation of the equipment and/or maintain the equipment in a safe state.

## Page 13

TEF Reliability Data for Safety Equipment @sIN PDS Data Handbook, 2021 Edition Term | Description SFF | Safe failure fraction. SFF = 1  (Apy/Acrit) - 100%. The fraction of failures of a single component that result in simultaneous failure of both components of a redundant pair, due to a common failure cause. Cuoon | Modification factor for redundant configurations other than 1002 in the beta-factor model (e.g., 1003, 2003 and 2004 configurations). RHF | Random hardware fraction, i.e., the fraction of DU failures originating from random hardware failures (1  RHF will be the fraction originating from systematic failures). DC Diagnostic coverage, i.e., the fraction of dangerous failures detected by automatic diagnostic tests (i.e., internal self-diagnostic built into the equipment plus external diagnostic facilities). This fraction is computed using the rate of dangerous detected failures divided by the total rate of dangerous failures; DC = (App/Ap) - 100%. Note that the interval between automatic diagnostic tests, is often referred to as diagnostic test interval. PTC || Proof test coverage, i.e., the fraction of DU failures detected during functional proof testing. PFD | The probability of failure of a system or component to perform its specified safety function upon a demand. Note that the PFD is the average probability of failure on demand over a period of time, i.e., PFD,y as denoted in IEC 61508. However, due to simplicity PFD,yg is denoted as PFD in the PDS handbooks. Interval of proof test (time between proof tests of a component). 23 Failure Classification Schemes 2.3.1 Failure Classification by Mode In line with IEC 61508/615111, the PDS method considers both critical and non-critical failure modes. Dangerous, safe and non-critical failure modes are given the following interpretations  on a component level: Dangerous (D): The component does not operate upon a demand, e.g., sensor stuck upon demand or valve does not close on demand. The Dangerous failures are, depending on how they are revealed, further split into: o Dangerous Undetected (DU): Dangerous failures not detected automatically upon occurrence, i.e., revealed only by a functional test, or upon a planned or unplanned demand. o Dangerous Detected (DD): Dangerous failures detected automatically upon occurrence, e.g., by self-diagnostics or sensor comparison. Safe (S): Safe failures either cause a spurious operation of the equipment and/or maintain the equipment in a safe state. The safe failures are not dangerous with respect to the safety function of

## Page 14

Reliability Data for Safety Equipment @ SINTEF PDS Data Handbook, 2021 Edition the equipment itself but are often critical for production. Safe failures can be further split into safe detected (SD) and safe undetected (SU) failures (not further pursued in this handbook). e Non-critical (NONC): The main function(s) of the component are still intact, but performance may be reduced. Non-critical failures will cover all failures that are not dangerous (safety critical) nor safe/spurious (production critical). They may be further split into: o Degraded failures: Failures where the ability of the equipment to carry out the required safety function (or maintain production) has not ceased but is reduced, and which over time may develop into a dangerous (or a safe) failure. o No effect failure: Failures that have no direct effect on the equipment safety (or production) function. The Dangerous and Safe failures are considered critical in the sense that they may affect either of the two main functions of the component, i.e., (1) the ability to shut down on demand or (2) the ability to maintain production when safe. The safe failures are often revealed instantly upon occurrence. The dangerous failures are detected by built in self-diagnostic or sensor comparison (dangerous detected) or are dormant  and can only be detected upon testing or a true demand (dangerous undetected). 1t should also be noted that a given failure may be classified as either dangerous or safe depending on the intended application. E.g., loss of hydraulic supply to a valve actuator operating on-demand will be dangerous in an energise-to-trip application and safe in a de-energise-to-trip application. Hence, when performing reliability calculations, the assumptions underlying the applied failure data as well as the context in which the data shall be used must be carefully considered. Definitions of dangerous failure are included in the data dossiers in Chapter 4. 2.3.2 Failure Classification by Cause Failures can be categorised according to failure cause and the IEC standards differentiate between random hardware failure and systematic failure. PDS uses the same classification and suggests a somewhat more detailed breakdown, as indicated in Figure 2.1. RANDOM HARDWARE FAILURE = T Figure 2.1 Possible failure classification by cause of failure

## Page 15

Reliability Data for Safety Equipment @ SINTEF PDS Data Handbook, 2021 Edition Random hardware failures are failures occurring at a random time during operation, resulting from one or more degradation mechanisms. It is here assumed that the operating conditions are within the design envelope of the system. Systematic failures are in PDS defined as failures that can be related to a specific cause other than natural degradation. Systematic failures are due to errors made during specification, design, operation and maintenance phases of the lifecycle. Such failures can therefore normally be eliminated by a modification, either of the design or manufacturing process, the testing and operating procedures, the training of personnel or changes to procedures and/or work practices. The failure rates presented in this handbook are based on operational experience, and do not distinguish explicitly between failure causes. However, some values for the relative distributions between random hardware failures and systematic failures are suggested (RHF, see section 2.4.4 and section 3.7). For further discussion of suggested taxonomies for failure modes, detection methods, failure causes and equipment classification, reference is made to the APOS project [11]. 2.4 Reliability Parameters 2.4.1 The Beta (p) factor and Cmoon When quantifying the reliability of systems with redundancy / voted systems, ¢.g., duplicated, or triplicated systems, it is essential to distinguish between independent and dependent failures. Random hardware failures due to natural stressors are often assumed to be independent failures. However, all systematic failures, e.g., hardware inadequacies and maintenance errors, are dependent failures and can lead to simultaneous failure of more than one (redundant) component in the safety system, reducing the advantage of redundancy. Dependent or common cause failures are often accounted for by the 8 factor approach. The PDS method presents a 8 factor model that distinguishes between different types of redundancies by introducing f factors which depend on the configuration, i.e., B(MooN) = B - Cpygon. Here, Cpoon is a modification factor depending on the configuration, MooN. A similar concept is described in IEC 61508-6 (Table D.5). Values for Cyoqn are given in Table 3. For a more complete description of the extended § factor approach and the reasoning behind the Cpo0y values, see the 2013 PDS method handbook [2]. SINTEF's suggested values for the g factor for different equipment types are given in section 3.4. Table 2.2: Numerical values for configuration factor, Cyoonv M\ N N=2 N=3 N=4 N=5 N=6 M=1 | Cooz=10 | Cioo3 =05 | Cioos =03 | Croos =02 | Cio06 =015 M=2 2 Ca003 =20 | Coo04 = 1.1 | Cpo5 = 0.8 | Czo06 = 0.6 M=3 L 5 C3008 = 2.8 | C3005 = 1.6 | C3006 =12 M=4 - ¥ - Caoos = 3.6 | Cio0s =19 M=5 2 - = 4 Csaos = 4.5

## Page 16

Reliability Data for Safety Equipment G SINTEF PDS Data Handbook, 2021 Edition 2.4.2 Safe Failure Fraction (SFF) The Safe Failure Fraction as described in IEC 61508 is given by the ratio between dangerous detected failures plus safe failures and the total rate of critical failures, i.e., SFF = (App + 45)/(Ap + As). The SFF can also be estimated as: e SFF =1— (Apy/Acrir); or rather in percentage: SFF = [1  (Apy/Acrit)] - 100%. The SFF values presented in this handbook are based on reported failure mode distributions in operational reviews, as well as additional expert judgements by SINTEF and industry in workshops. Higher (or lower) SFFs than indicated in the tables will apply for specific equipment types, but should be documented, e.g., by FMEDA type of analyses. 2.4.3 Diagnostic coverage (DC) and proof test coverage (PTC) There are two main test methods available to detect dangerous SIS failures: e Automatic on-line diagnostic testing. * Manual proof testing, including activation of the SIS component. To perform PFD quantification, the effectiveness of these two methods needs to be known. * The effectiveness of the automatic diagnostic test is defined by the diagnostic coverage (DC). A distinction is often made between internal self-diagnostic built into the equipment and external diagnostic facilities implemented by the user (e.g., comparison of different instrument readings). Both properties are however captured by the DC. See section 3.5. * The effectiveness of manual proof testing is defined by the proof test coverage (PTC). Based on the extent and quality of the proof test, such as a complete functional test versus a partial test, the PTC will vary since a varying number of failure modes (and associated failure causes) can be revealed. Both the DC and PTC will affect the system availability, but they differ slightly in terms of their mathematical treatment in the PFD calculations: * DC defines the fraction of dangerous failures that are revealed by diagnostic on-line tests and is mathematically expressed as: DC = (App/Ap) - 100%. Since Apy + App = Ap, diagnostic coverage can also be expressed as: DC = (1  Apy/Ap) - 100%. The assumed value of DC will therefore affect the rate of DU failures (Apy) used in the PFD calculations. o The PTC defines the fraction of DU failures that is revealed during a proof test. This implies that the rate of DU failures (Apy) ifself is not directly affected. However, when the PTC is less than 100%, the PFD is affected since some DU failures are not revealed upon test but remain dormant until a test that completely restores the component's functionality (PTC = 100%) has been performed. This contributes to an increasing average PFD as illustrated in Figure 2.2, Here an incomplete test (with PTC less than 100%) is performed with interval 7 and this test reveals a certain fraction of the DU failures. At time T a complete functional test that also reveals the residual DU failures, is performed, and the system is assumed restored back to its original state.

## Page 17

Reliability Data for Safety Equipment @ SINTEF PDS Data Handbook, 2021 Editon PFD() Time dependent PFD Average PFD Figure 2.2 Time dependent PFD with PTC < 100% Mathematically, the above implies that the rate of dangerous undetected failures can now be split into: 1. Failures defected during normal proof testing: with rate PTC - Apy and proof test interval 7, and 2. Failures not detected during normal proof testing: with rate (1  PTC) * Apy and test interval™ T For a lool configuration the PFD is then given as: PFD1001 = PTC- (Apy - 5) + (1 = PTC) - (Apy - 3). For a more detailed discussion, reference is made to the PDS method handbook [2]. Proof tests as diagnostic tests  partial stroke testing Note that in theory, any proof test can be turned into a diagnostic test, but it requires that the frequency of this automated or on-line (i.e., during operation) proof test is sufficiently high. In [7] it is suggested that the frequency of the automated test should ar least be a factor 100 of the demand rate of the associated SIS. This factor is also discussed in IEC 61508-2 [4] (section 7.4.4.1) for high demand systems, as well as in an EXIDA white paper [9]. Note that for low demand systems, the diagnostic test frequency is normally only minutes or seconds (or even microseconds), i.e., a factor by far exceeding 100 times the demand rate. The latter implies that partial stroke testing of valves can normally not be accounted for as a diagnostic test due to too infrequent execution. Rather, a partial stroke test should be counted as a proof test with reduced test coverage as discussed above. See also section 3.6.3 for further discussion of test coverage for partial stroke testing. 2.4.4 Random Hardware Failure fraction (RHF) Failure rates based on analyses and/or provided by manufacturers often tend to exclude systematic failures related to installation, commissioning, or operation of the equipment. A mismatch between manufacturer / certificate data and operational data is therefore often observed. However, since systematic failures inevitably will occur, why not include these failures in predictive reliability analyses (see also discussion in section 1.2)? The approach taken in this handbook is to present reliability data based on historically observed and further classified failures. As a result, both random hardware failures and systematic failures will be included in the presented failure rates. To reflect this, the parameter RHF has been defined as the fraction of dangerous undetected failures (Apy) originating from random hardware failures (Apy-gp), i.., RHF = Apy—gu/Apy (i.e., 1  RHF becomes the fraction of systematic failures). Indicative values of the RHF factor, based on observed failure causes, are given in section 3.7, but will obviously depend heavily on facility specific conditions.

## Page 18 — Table 3.1

**Table 3.1: Failure rates (per 10⁶ hour), DC and SFF — Transmitters and switches**

| Component | λcrit | λS | λP | λDU | λDU70% | DC | SFF | Section |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Position switch | 1.9 | 0.7 | 1.2 | 1.1 | 1.3 | 5% | 41% | 4.2.1 |
| Aspirator system including flow switch etc. | 4.6 | 1.9 | 2.6 | 2.5 | 3.0 | 5% | 46% | 4.2.2 |
| Pressure transmitter | 1.95 | 0.58 | 1.36 | 0.48 | 0.52 | 65% | 75% | 4.2.3 (D) |
| Level transmitter | 10 | 4.2 | 6.3 | 1.90 | 2.5 | 70% | 82% | 4.2.4 (D) |
| Temperature transmitter | 0.7 | 0.3 | 0.4 | 0.1 | 0.2 | 70% | 82% | 4.2.5 (D) |
| Flow transmitter | 6.6 | 2.7 | 4.0 | 1.4 | 1.8 | 65% | 79% | 4.2.6 (D) |

`) See section 4.2.4 for a more thorough discussion of how failure rates vary with complexity of application.`

## Page 19 — Tables 3.2 and 3.3

**Table 3.2: Failure rates (per 10⁶ hour), DC and SFF — Detectors**

| Component | λcrit | λS | λP | λDU | λDU70% | DC | SFF | Section |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Catalytic point gas detector | 5.2 | 1.6 | 3.6 | 1.5 | 1.6 | 60% | 72% | 4.2.7 |
| IR point gas detector | 3.2 | 1.5 | 1.7 | 0.3 | 0.27 | 85% | 92% | 4.2.8 |
| Aspirated IR point gas detector system | 6.6 | 3.1 | 3.5 | 2.9 | 3.6 | 16% | 56% | 4.2.9 (D) |
| Line gas detector | 6.7 | 2.3 | 4.4 | 0.4 | 0.47 | 90% | 94% | 4.2.10 (D) |
| Electrochemical detector | 6.0 | 1.8 | 4.2 | 1.7 | 1.9 | 60% | 68% | 4.2.11 |
| Smoke detector | 2.0 | 1.2 | 0.8 | 0.16 | 0.17 | 80% | 92% | 4.2.12 (D) |
| Heat detector | 2.29 | 1.37 | 0.92 | 0.37 | 0.43 | 60% | 84% | 4.2.13 (D) |
| Flame detector | 3.53 | 2.12 | 1.41 | 0.35 | 0.37 | 75% | 90% | 4.2.14 |

**Table 3.3: Failure rates (per 10⁶ hour), DC and SFF — Manual push buttons and call points**

| Component | λcrit | λS | λP | λDU | λDU70% | DC | SFF | Section |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Manual pushbutton/call point (outdoor) | 0.35 | 0.11 | 0.23 | 0.19 | 0.53 | 20% | 46% | 4.2.15 (D) |
| CAP switch (indoor) | 0.21 | 0.07 | 0.14 | 0.11 | 0.20 | 20% | 46% | 4.2.16 |

## Page 20 — Table 3.4

**Table 3.4: Failure rates (per 10⁶ hour), DC and SFF — Control logic units**

Standard industrial PLC

| Component | λcrit | λS | λP | λDU | DC | SFF | Section |
|---|---:|---:|---:|---:|---:|---:|---|
| Analogue input (single) | 3.6 | 1.8 | 1.8 | 0.7 | 60% | 80% | 4.3.1.1 |
| CPU - logic solver (1oo1) | 17.5 | 8.8 | 8.8 | 3.5 | 60% | 80% | 4.3.1.2 |
| Digital output (single) | 3.6 | 1.8 | 1.8 | 0.7 | 60% | 80% | 4.3.1.3 |

Programmable safety system

| Component | λcrit | λS | λP | λDU | DC | SFF | Section |
|---|---:|---:|---:|---:|---:|---:|---|
| Analogue input (single) | 2.8 | 1.4 | 1.4 | 0.1 | 90% | 95% | 4.3.2.1 |
| CPU - logic solver (1oo1) | 5.4 | 2.7 | 2.7 | 0.3 | 90% | 95% | 4.3.2.2 |
| Digital output (single) | 3.20 | 1.60 | 1.60 | 0.16 | 90% | 95% | 4.3.2.3 |

Hardwired safety system

| Component | λcrit | λS | λP | λDU | DC | SFF | Section |
|---|---:|---:|---:|---:|---:|---:|---|
| Analogue input (single) | 0.44 | 0.40 | 0.04 | 0.04 | 0% | 91% | 4.3.3.1 |
| Logic (1oo1) | 0.33 | 0.30 | 0.03 | 0.03 | 0% | 91% | 4.3.3.2 |
| Digital output (single) | 0.44 | 0.40 | 0.04 | 0.04 | 0% | 91% | 4.3.3.3 |

Other control logic units

| Component | λcrit | λS | λP | λDU | DC | SFF | Section |
|---|---:|---:|---:|---:|---:|---:|---|
| Fire central including I/O | 13.2 | 6.6 | 6.6 | 0.7 | 90% | 95% | 4.3.4.1 |
| Intrinsic safety isolator (galvanic isolation) | 0.2 | 0.1 | 0.1 | 0.1 | 0% | 50% | 4.3.4.2 |

## Page 21 — Table 3.5

**Table 3.5: Failure rates (per 10⁶ hour), DC and SFF — Valves**

| Component | λcrit | λS | λP | λDU | λDU70% | DC | SFF | Section |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Topside ESV and XV (excl. solenoid/pilot) | 4.5 | 2.0 | 2.5 | 2.3 | 2.6 | 5% | 48% | 4.4.1 (D) |
| Topside ESV and XV - ball valves (excl. solenoid/pilot) | 4.0 | 1.8 | 2.2 | 2.1 | 2.2 | 5% | 48% | 4.4.1.1 |
| Topside ESV and XV - gate valves (excl. solenoid/pilot) | 6.4 | 2.9 | 3.5 | 3.3 | 3.6 | 5% | 48% | 4.4.1.2 |
| Riser ESV (excl. solenoid/pilot) | 3.6 | 1.6 | 2.0 | 1.9 | 2.6 | 5% | 48% | 4.4.2 |
| Topside XT valve - PMV and PWV (excl. solenoid/pilot) | 4.5 | 2.0 | 2.5 | 2.3 | 3.2 | 5% | 48% | 4.4.3 (D) |
| Topside XT valve - HASCV | 5.2 | 0.7 | 4.5 | 4.2 | 5.2 | 5% | 48%² | 4.4.4 |
| Topside XT valve - GLESDV (excl. solenoid/pilot) | 0.5 | 0.1 | 0.2 | 0.2 | 0.5 | 5% | 48%² | 4.4.5 |
| Topside XT valve ~ CIESDV (incl. solenoid/pilot) | 2.1 | 0.2 | 1.9 | 1.8 | 3.2 | 5% | 48%² | 4.4.6 |
| Topside HIPPS valve (excl. solenoid/pilot) | 1.2 | 0.7 | 0.5 | 0.5 | 0.9 | 5% | 57% | 4.4.7 |
| Blowdown valve (excl. solenoid/pilot) | 5.3 | 2.2 | 3.1 | 2.8 | 3.2 | 5% | 48% | 4.4.8 |
| Fast opening valve — FOV (in closed flare, excl. solenoid/pilot) | 11 | 4.1 | 6.6 | 6.3 | 7.6 | 5% | 41% | 4.4.9 |
| Solenoid or pilot valve | 0.8 | 0.5 | 0.3 | 0.3 | 0.34 | 5% | 62% | 4.4.10 |
| Process control valve (frequently operated, excl. solenoid/pilot) *¹ | 6.3 | 2.7 | 3.6 | 2.5 | 3.8 | 30% | 60% | 4.4.11 |
| Process control valve (shutdown service only, excl. solenoid/pilot) *¹ | - | - | - | 3.5 | 5.5 | 5% | 60% | 4.4.11 |
| Pressure relief valve — PSV | 2.8 | 0.9 | 1.9 | 1.9 | 2.2 | 0% | 33% | 4.4.12 |
| Deluge valve (incl. solenoid and pilot) | 2.2 | 0.8 | 1.4 | 1.4 | 2.0 | 0% | 37% | 4.4.13 |
| Fire water monitor valve (incl. solenoid/pilot) | 3.6 | 1.3 | 2.2 | 2.2 | 2.9 | 0% | 37% | 4.4.14 |
| Water mist valve (incl. solenoid/pilot) | 1.2 | 0.5 | 0.8 | 0.8 | 1.1 | 0% | 37% | 4.4.16 |
| Sprinkler valve (incl. solenoid/pilot) | 2.1 | 0.8 | 1.3 | 1.3 | 4.9 | 0% | 38% | 4.4.17 |
| Foam valve (incl. solenoid/pilot) | 6.5 | 2.4 | 4.1 | 4.1 | 5.2 | 0% | 37% | 4.4.18 |
| Ballast water valve (excl. solenoid/pilot) | 1.0 | 0.4 | 0.6 | 0.5 | 0.7 | 5% | 43% | 4.4.19 |

## Page 22 — Table 3.6

**Table 3.6: Failure rates (per 10⁶ hour), DC and SFF — Miscellaneous final elements**

| Component | λcrit | λS | λP | λDU | λDU70% | DC | SFF | Section |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Fire water pump system — diesel electric | 3.4 | 1.4 | 2.0 | 2.0 | 2.5 | 0% | 41% | 4.4.20 |
| Fire water pump system — diesel hydraulic | 2.5 | 1.0 | 1.5 | 1.5 | 1.9 | 0% | 40% | 4.4.21 |
| Fire water pump system — diesel mechanical | 2.9 | 1.2 | 1.7 | 1.7 | 2.1 | 0% | 41% | 4.4.22 |
| Fire and gas damper | 3.0 | 0.8 | 2.2 | 2.2 | 2.8 | 0% | 27% | 4.4.23 |
| Rupture disc | 0.9 | 0.1 | 0.8 | 0.8 | 0.9 | 0% | 11% | 4.4.24 |
| Circuit breaker | 0.9 | 0.4 | 0.5 | 0.5 | 0.6 | 0% | 44% | 4.4.25 |
| Relay, contactor | 0.5 | 0.2 | 0.3 | 0.3 | 0.4 | 0% | 40% | 4.4.26 |
| Fire door | 1.8 | 0.5 | 1.3 | 1.3 | 1.6 | 0% | 28% | 4.4.27 |
| Watertight door | 1.5 | 0.4 | 1.1 | 1.1 | 1.3 | 0% | 27% | 4.4.28 |
| Emergency generator | 1.4 | 0.5 | 0.9 | 0.9 | 1.1 | 0% | 36% | 4.4.29 |
| Lifeboat engines | 2.0 | 0.4 | 1.6 | 1.6 | 2.0 | 0% | 20% | 4.4.30 |
| UPS & Battery package | 0.8 | 0.2 | 0.6 | 0.6 | 0.8 | 0% | 25% | 4.4.31 |
| Emergency lights | 0.5 | 0.1 | 0.4 | 0.4 | 0.5 | 0% | 20% | 4.4.32 |
| Flashing beacon | 0.3 | 0.1 | 0.2 | 0.2 | 0.3 | 0% | 33% | 4.4.33 |
| Lifeboat radios | 1.2 | 0 | 1.2 | 1.2 | 1.5 | 0% | 0% | 4.4.34 |
| PA loudspeakers | 0.2 | 0 | 0.2 | 0.2 | 0.25 | 0% | 0% | 4.4.35 |

## Page 23 — Table 3.7

**Table 3.7: Failure rates (per 10⁶ hour), DC and SFF — Subsea input devices**

| Component | λcrit | λS | λP | λDU | λDU70% | DC | SFF | Section |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Subsea pressure sensor | 2.0 | 0.8 | 1.2 | 0.4 | 0.8 | 65% | 79% | 4.5.1 |
| Subsea temperature sensor | 1.0 | 0.4 | 0.6 | 0.2 | - | 65% | 79% | 4.5.2 |
| Combined subsea pressure and temperature sensor | 2.2 | 0.9 | 1.3 | 0.4 | 0.8 | 70% | 82% | 4.5.3 |
| Subsea flow sensor | 6.2 | 2.5 | 3.7 | 1.3 | 2.1 | 65% | 79% | 4.5.4 |
| Subsea sand detector | 9.5 | 3.8 | 5.7 | 2.0 | - | 65% | 79% | 4.5.5 |

## Page 24 — Tables 3.8, 3.9, 3.10

**Table 3.8: Failure rates (per 10⁶ hour), DC and SFF — Subsea control logic and umbilicals**

| Component | λcrit | λS | λP | λDU | λDU70% | DC | SFF | Section |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| MCS — Master control station (located topside) | 15 | 7.7 | 7.7 | 3.1 | - | 60% | 80% | 4.5.6 |
| Umbilical hydraulic/chemical line (per line) | 0.60 | 0.30 | 0.30 | 0.06 | - | 80% | 90% | 4.5.7 |
| Umbilical power/signal line (per line) | 0.55 | 0.28 | 0.28 | 0.06 | - | 80% | 90% | 4.5.8 |
| SEM — Subsea electronic module | 5.3 | 2.6 | 2.6 | 1.1 | 1.5 | 60% | 80% | 4.5.9 |
| Subsea solenoid control valve (in subsea control module) | 0.4 | 0.2 | 0.2 | 0.2 | - | 0% | 60% | 4.5.10 |

**Table 3.9: Failure rates (per 10⁶ hour) and DC — Subsea final elements**

| Component | λcrit | λS | λP | λDU | λDU70% | DC | Section |
|---|---:|---:|---:|---:|---:|---:|---|
| Subsea manifold isolation valve | 0.5 | 0.3 | 0.2 | 0.2 | - | 0% | 4.5.11 |
| Subsea XT valve ~ PMV, PWV | 0.9 | 0.3 | 0.6 | 0.6 | 0.7 | 0% | 4.5.12 (D) |
| Subsea XT valve - XOV | 0.13 | 0.05 | 0.08 | 0.08 | 0.14 | 0% | 4.5.13 (D) |
| Subsea XT valve - AMV | 0.16 | 0.04 | 0.12 | 0.12 | 0.19 | 0% | 4.5.14 |
| Subsea XT valve - CIV, MIV | 0.30 | 0.06 | 0.24 | 0.24 | 0.4 | 0% | 4.5.15 (D) |
| Subsea isolation valve — SSIV | 0.9 | 0.5 | 0.4 | 0.4 | - | 0% | 4.5.16 |

`"1 Same DC values as for corresponding topside equipment assumed.`

**Table 3.10: Failure rates (per 10⁶ hour) and DC — Downhole well completion valves**

| Component | λcrit | λS | λP | λDU | λDU70% | DC | Section |
|---|---:|---:|---:|---:|---:|---:|---|
| Downhole safety valve — DHSV | 19 | 11 | 7.5 | 7.25 | - | 0% | 4.6.1 (D) |
| Downhole safety valve — TRSCSSV | 4.4 | 0.4 | 4.0 | 2.0 | - | 0% | 4.6.2 (D) |
| Downhole safety valve — WRSCSSV | 1.9 | 0.4 | 1.5 | 1.5 | - | 0% | 4.6.3 (D) |
| Annulus subsurface safety valve — TRSCASSV, type A | 4.3 | 0.6 | 3.6 | 3.6 | 3.9 | 0% | 4.6.4 (D) |
| Annulus subsurface safety valve — TRSCASSV, type B | 4.7 | 0.8 | 3.9 | 3.9 | 4.4 | 0% | 4.6.5 |
| Wire retrievable chemical injection valve — WRCIV | 1.8 | 0.1 | 1.8 | 1.8 | 2.1 | 0% | 4.6.6 |
| Tubing retrievable chemical injection valve — TRCIV | 0.4 | 0.1 | 0.3 | 0.3 | 0.7 | 0% | 4.6.7 |
| Gas lift valve - GLV | 1.3 | 0.2 | 1.3 | 1.3 | 13.2 | 0% | 4.6.8 |

`') Same DC values as for corresponding topside equipment assumed.`


## Page 25

Reliability Data for Safety Equipment @ SINTEF PDS Data Handbook, 2021 Edition 3.3 Drilling Equipment Table 3.11 summarises the reliability input data for drilling equipment. Equipment boundaries and a more detailed discussion of the data sources and underlying assumptions are given in the detailed data dossiers in section 4.7. Data for estimating specific β values for drilling equipment have not been available and such values are therefore not given. As for subsea equipment, the values for SFF should be considered as indicative only since the underlying data for estimating this factor have been scarce. Higher (or lower) SFFs may apply for specific equipment types, and this should in such case be documented separately.

**Table 3.11: Failure rates (per 10⁶ hour), DC and SFF — Drilling equipment**

| Component | λcrit | λS | λP | λDU | DC | SFF | Section |
|---|---:|---:|---:|---:|---:|---:|---|
| Annular preventer | 4.5 | 3.5 | 9.8 | 9.8 | 0% | 80% | 4.7.1 |
| Ram preventer | 3.8 | 0.4 | 3.4 | 3.4 | 0% | 10% | 4.7.2 |
| Choke and kill valve | 0.9 | 0.2 | 0.8 | 0.8 | 0% | 20% | 4.7.3 |
| Choke and kill line | 2.4 | 2.0 | 2.2 | 2.2 | 0% | 10% | 4.7.4 (D) |
| Hydraulic connector | 4.1 | 1.0 | 3.1 | 3.1 | 0% | 25% | 4.7.5 (D) |
| Multiplex control system | 12.4 | 0 | 12.4 | 6.2 | 50% | 50% | 4.7.6 (D) |
| Pilot control system | 10.2 | 0 | 10.2 | 10.2 | 0% | 0% | 4.7.7 (D) |
| Acoustic backup control system | 3.7 | 0 | 3.7 | 3.7 | 0% | 0% | 4.7.8 (D) |

" Values for λDU70%, i.e., the upper 70% confidence limits of the dangerous undetected failure rates, have not been available for drilling equipment.

) Note that the failure rate represents the total amount of functions in the control system (with redundant control pods). As a rough assumption half of the total failure rate for all functions could be considered as the failure rate for one individual pod.

3.4 Generic β values

The generic β values in this handbook are based both on the values in the 2013 handbook and on a field study from 2015 of common cause failures (CCFs), conducted as a review of some 12.000 maintenance notifications [3]. Main deliverables from the study were: 1) Generic beta-factor values for main component groups of safety instrumented systems, and 2) CCF checklists for assessing possible CCF causes, and defences. These checklists may be used to determine installation specific beta-factor values for SIS. For more details and suggested checklists, reference is made to the report [3]. Also note that IEC 61508 (part 6, Appendix D) contains a checklist that can be used to arrive at installation and equipment specific β-values. This checklist describes measures that are considered efficient defences against common cause failures. Based on a scoring of each measure, estimated β values can be obtained for both input, logic, and final elements [4]. In Table 3.12, β values for (topside) input devices, control logic units and final elements are suggested. Specific β values for subsea and drilling equipment are not given. Rather, reference is made to comparable topside values.

## Page 26

**Table 3.12: Suggested β values for topside equipment**

| Component | β | Comment/source |
|---|---:|---|
| Process transmitters | 0.10 | Updated PDS/SINTEF estimates based on findings from operational reviews as documented in [3], former values and expert judgements. |
| Process switches | 0.10 | Note that field experience, [3], indicates even higher β values for process transmitters and detectors. |
| Fire and gas detectors | 0.10 | Note that field experience, [3], indicates even higher β values for process transmitters and detectors. |
| Pushbuttons and call points | 0.05 | — |
| Standard industrial PLCs | 0.07 | SINTEF estimates based on former PDS values and expert judgements. |
| Programmable safety systems | 0.05 | SINTEF estimates based on former PDS values and expert judgements. |
| Hardwired safety systems | 0.03 | SINTEF estimates based on former PDS values and expert judgements. |
| Topside shutdown valves | 0.08 | Updated SINTEF estimates based on former PDS values, findings from operational reviews, [3], and expert judgements. |
| Blowdown and fast opening valves | 0.08 | Updated SINTEF estimates based on former PDS values, findings from operational reviews, [3], and expert judgements. |
| Solenoid and pilot valves on same valve | 0.10 | Note that field experience, [3], indicates even higher β values for shutdown valves, blowdown valves, PSVs and dampers. |
| Solenoid and pilot valves on different valves | 0.07 | Note that field experience, [3], indicates even higher β values for shutdown valves, blowdown valves, PSVs and dampers. |
| Process control valves | 0.08 | — |
| Pressure relief valves, PSVs | 0.07 | — |
| Deluge valves | 0.08 | — |
| Fire and gas dampers | 0.12 | — |
| Circuit breakers / contactors / relays | 0.05 | — |

3.5 Determining Diagnostic Coverage (DC)

Two main aspects are important when assessing the actual diagnostic coverage:

1. The technical part of the diagnostic coverage built-in to or external to the equipment. This is sometimes referred to as the instrument DC and estimated values are presented in this handbook.
2. The operational/organisational part of the diagnostic coverage, i.e., having human machine interfaces (HMIs), procedures, work processes, competent and trained personnel, and resources to ensure that the diagnostic alarm is revealed and properly acted upon. This is sometimes referred to as diagnostic success. I.e., to credit the stated instrument DC, operational/organisational prerequisites must be in place.

Instrument DC values is further discussed in section 3.5.1 and 3.5.2, whereas diagnostic success is briefly discussed in section 3.5.3.

## Page 27

Reliability Data for Safety Equipment @ SINTEF PDS Data Handbook, 2021 Edition 3.5.1 Instrument DC in general — Relevant data sources Typical DC values suggested in equipment certificates and commercially available SIL tools vary between 70 - 95%. Whereas these values refer to self-diagnostic built into the equipment, and mainly applies for input devices such as transmitters and detectors, possible external diagnostic facilities are discussed in [6] and [7). In section 8.6.1 in NOROG guideline 070 [6] it is stated that, unless a more detailed analysis is performed: transmitter comparison alarm could be given a maximum credit of DC = 90%. In [7] it is further specified that to assume this diagnostic coverage, it requires monitoring of two analog signals for synchronism — and if they diverge by more than a given value (usually about 5%), an alarm or an appropriate actuator is triggered. Furthermore, "high signal dynamics" are required to achieve high diagnostic coverage, i.e., the signals concerned regularly cover major parts of the measuring range. If the signals concerned only cover parts of the measuring range [here "parts of" not further specified], only "medium signal dynamics" are obtained, and only a diagnostic coverage of DC = 70% should be claimed, [7]. Note that in Annex E of ISO 13489-1 [8], tables with examples of typical DC values and associated prerequisites are provided. Similarly, Annex A of IEC 61508-2 [4], gives slightly more detailed tables (Table A.2 - A.14). Both sources specify possible diagnostic measures and associated maximum achievable DC values in terms of low (60%), medium (90%) or high (99%). 3.5.2 Equipment specific (instrument) DC values During operational reviews, classification of both DU failures and DD failures have been performed, and the failure mode and causes (if known) have been documented. Consequently, based on observed λDU and λDD values, DC values can be obtained. For equipment with extensive operational experience (both with respect to aggregated operational time and experienced dangerous failures), the estimated DC values can be considered as quite realistic. However, for some equipment with limited aggregated operational time and few experienced failures, additional expert judgements together with DC values from e.g., equipment certificates have been applied to provide DC values. In this handbook, some typical (average) DC values have been suggested, giving the distribution between λDU and λDD. It must be strongly pointed out that instrument DC values will vary between equipment types and models and how the diagnostics are implemented in the specific application. The assumptions underlying the DC values suggested in this handbook are therefore highlighted whenever possible. If claiming a higher DC, this should be documented and justified (e.g., by a separate analysis). Below the specific instrument DC values are further discussed. Switches In general, process switches do not have any built-in self-diagnostics, except for some intelligent (SIL rated) process switches with self-test functions implemented (claiming up to 70% DC). Here, a DC of 10% for dangerous failures has been assumed due to line monitoring as well as observations from operational reviews (where several switch failures have been classified as DD). For proximity switches, a similar DC of 10% has also been assumed. Process Transmitters Assumed DC values are discussed for different types of process transmitters. This is based on implemented self-test in the transmitter, typically range checking and input filtering. If a higher coverage is claimed, e.g., due to automatic comparison between transmitters (discrepancy alarm with reference transmitter), this should be especially documented or verified.

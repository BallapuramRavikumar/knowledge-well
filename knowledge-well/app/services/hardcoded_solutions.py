from __future__ import annotations
from typing import List, Dict, Any, Tuple

# This data structure stores the predefined Q&A pairs provided by the user.
# The keys are normalized versions of the questions for easy lookup.
HARDCODED_SOLUTIONS = [
    {
        "question": "what is the best bonding temperature?",
        "solution": "The initial bonding phase in HB is performed at low or room temperature (RT). Hybrid bonding is described as a room temperature, low force process. The activated top dies are picked and placed on the activated coupons with a flip-chip bonder at room temperature, held together by van der Waals force. This initial phase is often referred to as tacking or low-temperature fusion bonding.",
        "sources": ["Overlay scaling error reduction for hybrid Die-To-Wafer bonding", "Annealing Effects in Sub-8 µm Pitch Die-to-Wafer"],
    },
    {
        "question": "what is the best queue time between bonding?",
        "solution": "Minimising the queue time (Q-time) is critical to preserving surface activation. Q-time is defined as the duration from plasma activation and deionized water (DIW) rinse to bonding. Extended Q-time causes water evaporation at the bonding interface, leading to insufficient water retention and weakened bond strength. Samples with a Q-time of 24 hours or more experienced detachment due to insufficient bonding strength, confirming that extended exposure is detrimental. Die handling procedures are enhanced, and queue times are minimized to maintain surface cleanliness.",
        "sources": ["Assessing Queue Time in D2W Hybrid Bonding Through Precise Bond Strength Measurements", "Hybrid Bonding with Fluidic Self Alignment: Process Optimization and Electrical Test Vehicle Fabrication"],
    },
    {
        "question": "Precision alignment control?",
        "solution": "The primary challenges or requirements for high-yield hybrid bonding are wafer warpage, planarity, cleanliness, and alignment accuracy. Alignment accuracy is the critical factor for tight bond pitches, with high-accuracy D2W bonders reducing placement errors to sub-micron levels. Wafer/Die warpage is a major concern as it impacts tacking and pre-bond yield. Hybrid bonding also requires optimal surface topography (planarity) and maintaining a clean bonding environment to avoid voids caused by particles.",
        "sources": ["A Review of Die-to-Die, Die-to-Substrate and Die-to-Wafer Heterogeneous Integration", "Overlay scaling error reduction for hybrid Die-To-Wafer bonding", "Direct Transfer Bonding Technology Enabling 50-nm Scale Accuracy for Die-to-Wafer 3D/Heterogeneous", "Annealing Effects in Sub-8 µm Pitch Die-to-Wafer", "Dielectric Stack Optimization for Die-level Warpage Reduction for Chip-to-Wafer Hybrid Bonding", "D2W Hybrid Bonding Challenges for HBM"],
    },
    {
        "question": "Particle control?",
        "solution": "Particle control is critical at several stages, including wafer saw, CMP, carrier/tape handling, bonding, and Si back grinding (Si BG). Wafer saw/dicing can cause particle contamination from chipping at die edges. CMP slurry residues or silicon-based etch residues can lead to contamination. Carrier/tape handling can introduce particles from insufficient cleaning. Particles introduced during the bonding stage itself can result in void formation, and protecting the bonding surface during Si BG is necessary to avoid contamination.",
        "sources": ["A Review of Die-to-Die, Die-to-Substrate and Die-to-Wafer Heterogeneous Integration", "Electrical Performance of CMP Process for Hybrid Bonding Application with Conventional / nt-Cu and Low Temperature SixNy / SixOy Dielectrics"],
    },
    {
        "question": "Particles come from where?",
        "solution": "Particles originate from specific sources such as wafer saw chipping (which creates Si dust residues), CMP slurry/residues, and carrier tape/adhesive residue. For instance, blade dicing can expose the bonding surface to Si dust, while CMP slurry residues can be identified by Energy Dispersive X-ray (EDX) analysis. Additionally, organic contamination or particles from conventional tapes can severely reduce bonding performance.",
        "sources": ["A novel Direct Transfer Bonding process with particle less tapes for Die to Wafer integration", "Electrical Performance of CMP Process for Hybrid Bonding Application with Conventional / nt-Cu and Low Temperature SixNy / SixOy Dielectrics"],
    },
    {
        "question": "Warpage control?",
        "solution": "The required tolerance for thin dies is generally tighter than 100 µm. Die-level warpage is a crucial element that affects bonding quality, with optimization programs aiming for warpage of less than 80 µm for 50 µm thick dies. A warpage level less than 70 µm has enabled successful tacking of thin chips, while high warpage can lead to corner delamination.",
        "sources": ["Process Development, Challenges, and Strategies for Void-Free Multi-Chip Stacking in Hybrid", "Dielectric Stack Optimization for Die-level Warpage Reduction for Chip-to-Wafer Hybrid Bonding"],
    },
    {
        "question": "what is Water absorption rate in Hybrid bonding?",
        "solution": "While a specific numerical absorption rate isn't typically cited, the consequences of water presence and loss are well-documented. Moisture ingress causes a hydrolysis reaction on siloxane bonds (SiO2 bonding), which can lead to delamination. In D2W bonding, water evaporation during extended queue time weakens the initial fusion bond. For self-assembly processes, a fluid is used for alignment, and experiments have shown it does not negatively impact electrical connections.",
        "sources": ["Bond Strength Measurement for Wafer-Level and Chip-Level Hybrid Bonding", "Assessing Queue Time in D2W Hybrid Bonding Through Precise Bond Strength Measurements", "Die-Level Transformation of 2D Shuttle Chips into 3D-IC for Advanced Rapid Prototyping using Meta Bonding", "Electrical performance of self-assembly applied to die-to-wafer hybrid bonding"],
    },
    {
        "question": "Cu bulge out issue?",
        "solution": "The Cu bulge-out issue is related to the dynamic process of thermal expansion during annealing. The Cu pad must be slightly recessed (dished) before bonding. During heat treatment, Cu expands due to its higher Coefficient of Thermal Expansion (CTE) compared to SiO2, causing it to protrude and make metallic contact with the opposing pad. Optimized designs require a balance, as excessive protrusion is detrimental, but some expansion is needed for joint formation.",
        "sources": ["Influence of Heat Treatment on the Quality of Die-to-Wafer Hybrid Bond Interconnects", "Direct Die-to-Wafer Hybrid Bonding Using Plasma Diced Dies and Bond Pad Pitch Scaling Down to 2 µm"],
    },
    {
        "question": "how to mitigate Cu Oxidation formation?",
        "solution": "Both pre-cleaning/activation and specific chemical treatments are used to manage oxidation. Plasma activation is necessary for pre-treatment of dielectric surfaces to enhance hydrophilicity. The initial bond interface uses surface activation followed by a DI water rinse. Wet cleaning with a citric acid rinse has shown improved Cu-Cu joint quality and less micro-voiding. The presence of Cu2O before bonding can aggregate into nodules and evolve into voids during annealing.",
        "sources": ["D2W Hybri2d Bonding Challenges for HBM", "Annealing Effects in Sub-8 µm Pitch Die-to-Wafer", "Demonstration of Low Temperature Cu-Cu Hybrid Bonding using A Novel Thin Polymer", "Electrical performance of self-assembly applied to die-to-wafer hybrid bonding"],
    },
    {
        "question": "DBI?",
        "solution": "DBI stands for Direct Bond Interconnect, a technology based on hybrid bonding principles. It's often used in comparisons with conventional stacks, as it utilizes Hybrid Bonding (HB) technology.",
        "sources": ["A Review of Die-to-Die, Die-to-Substrate and Die-to-Wafer Heterogeneous Integration"],
    },
    {
        "question": "Organic or Inorganic dielectric?",
        "solution": "Both organic and inorganic dielectric materials are used. Inorganic dielectrics like SiO2 and SiCN are conventional choices, with SiCN offering higher bonding strength. Organic materials like polymers are being developed for low-temperature hybrid bonding and inter-die gap fill processes.",
        "sources": ["SiCN CMP Integration for Hybrid Bonding", "Low-Temperature Nanocrystalline Cu/polymer Hybrid Bonding with Tailored CMP Process", "Digital Design of Inter-Die Gap Fill Dielectric Film Processing for C2W Hybrid Bonding using Finite Element Modelling"],
    },
    {
        "question": "what is the best Annealing temperature?",
        "solution": "The best annealing temperature is process-dependent, but the trend is moving lower. While traditional hybrid bonding uses temperatures between 350°C and 400°C, lower temperatures (200°C or less) are desired to prevent thermal damage to devices like DRAM. Strong metallurgical bonds have been formed as low as 180°C with optimized Cu microstructures.",
        "sources": ["Demonstration of Low Temperature Cu-Cu Hybrid Bonding using A Novel Thin Polymer", "Process Challenges in Thin Wafers Fabrication with Double Side Hybrid Bond Pads for Chip Stacking", "The Influence of Cu Microstructure on Thermal Budget in Hybrid Bonding", "Annealing Effects in Sub-8 µm Pitch Die-to-Wafer"],
    },
    {
        "question": "Challenges on Cu dishing height, surface hydrophilicity, hydroxyl density and adhesion.",
        "solution": "All listed elements are foundational parameters influencing HB yield and reliability. Cu dishing height must be controlled to less than 5nm. Plasma activation enhances surface hydrophilicity by introducing silanol groups (Si-O-H). Strong adhesion is crucial, with materials like SiCN offering higher bonding strength than SiO2.",
        "sources": ["SiCN CMP Integration for Hybrid Bonding", "A Review of Die-to-Die, Die-to-Substrate and Die-to-Wafer Heterogeneous Integration", "Dielectric Stack Optimization for Die-level Warpage Reduction for Chip-to-Wafer Hybrid Bonding", "Bond Wave Analysis of SiCN for Fine Pitch Hybrid Bonding"],
    },
    {
        "question": "Plasma dicing or Mechanical dicing",
        "solution": "Plasma dicing is preferred. It addresses critical issues like contamination and chipping inherent in mechanical dicing. Plasma dicing is a damage- and stress-free process that provides a well-defined die edge and clean sidewall, minimizing defects and particle generation. It is a more suitable alternative to conventional blade dicing for high-quality bonding processes.",
        "sources": ["A Review of Die-to-Die, Die-to-Substrate and Die-to-Wafer Heterogeneous Integration", "Direct Die-to-Wafer Hybrid Bonding Using Plasma Diced Dies and Bond Pad Pitch Scaling Down to 2 µm", "Scalability and Process Optimization in Hybrid Bonding with Fine-Pitch Interconnections", "Hybrid Bonding with Fluidic Self Alignment: Process Optimization and Electrical Test Vehicle Fabrication"],
    },
]

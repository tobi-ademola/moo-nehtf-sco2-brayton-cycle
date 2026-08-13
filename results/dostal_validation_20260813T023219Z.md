# sCO2 recompression cycle -- Dostal (2004) validation

| | |
|---|---|
| script | `scripts/validate_dostal.py` |
| run (UTC) | 20260813T023219Z |
| git commit | `f2fde9d-dirty` |
| PySAM | 7.1.1.post1 (bundled ssc 306) |
| CO2 properties | CoolProp 8.0.0, cross-checked against ssc |
| Dostal target eta | 51.27 % |

```
================================================================================================
DOSTAL 2004 HIGH-PERFORMANCE RECOMPRESSION -- CASE F (ADOPTED BASELINE)
  f_rc 0.4097, recuperators at 10.0 K approach, Dostal's own per-HX pressure loss.
  All three read from his published data; none fitted. See VALIDATION.md 2.3.4a.
================================================================================================
  turbine inlet        700.000 C   (target 700.0)
  compressor inlet      32.000 C   (target 32.0)
  P_comp_out           20.0000 MPa (target 20.00)
  P_comp_in             7.6923 MPa (target 7.6923)
  pressure ratio        2.6000     (target 2.60)
  recomp_frac          0.40970     (target 0.4097; Table 10.1 states 0.39 -- see 2.3.4a)
  eff_HTR / eff_LTR    0.97625 / 0.93095
  recup UA total        2306.6 kW/K
  m_dot_co2             92.233 kg/s   (m_dot_htf 75.362 kg/s, cp_htf 1.5332 kJ/kg-K)

  ETA_THERMAL          0.51289  = 51.29 %
  Dostal target        0.51270  = 51.27 %
  deviation              +0.02 percentage points  (+0.04 % relative)
  eta net less cooling 0.50776  (fan power 100.0 kW deducted)

STATE POINTS  (h, s from CoolProp CO2 at the ssc-solved T and P)
#   node            T[C]      P[kPa]   h[kJ/kg]  s[kJ/kg-K]   description
------------------------------------------------------------------------------------------------
0   MC_IN         32.000     7692.31    306.675     1.34780   main compressor inlet
1   MC_OUT        61.099    20000.00    327.256     1.35458   main compressor outlet
2   LTR_HP_OUT   159.407    19990.22    538.320     1.91508   LTR high-pressure outlet
3   MIXER_OUT    159.643    19990.22    538.690     1.91593   LTR-HP + recompressor merge
4   HTR_HP_OUT   531.256    19944.56   1011.945     2.71310   HTR high-pressure outlet = PHX inlet
5   TURB_IN      700.000    19814.56   1223.339     2.95286   turbine inlet
6   TURB_OUT     578.309     7929.22   1078.948     2.97185   turbine outlet = HTR low-pressure inlet
7   HTR_LP_OUT   169.583     7802.64    605.672     2.22055   HTR low-pressure outlet = LTR low-pressure inlet
8   LTR_LP_OUT    71.127     7704.93    481.081     1.90233   LTR low-pressure outlet = flow split point
9   RC_OUT       159.983    19990.22    539.223     1.91716   recompressor outlet
10  PC_IN            nan         nan        nan         nan   pre-compressor inlet   (partial-cooling only -> NaN here)
11  PC_OUT           nan         nan        nan         nan   pre-compressor outlet  (partial-cooling only -> NaN here)

property cross-check   max |h_ssc - h_CoolProp| = 1.04e-04 kJ/kg   max |s_ssc - s_CoolProp| = 2.50e-07 kJ/kg-K
mixer energy balance   h[3] = 538.6899   (1-f)h[2] + f*h[9] = 538.6899   err 1.35e-07 kJ/kg

ENTROPY GENERATION  (T0 = 299.15 K = ambient)
   MC   main compressor   Sgen  +0.36927 kW/K    Edest    110.47 kW
   RC   recompressor      Sgen  +0.56060 kW/K    Edest    167.70 kW
   TURB turbine           Sgen  +1.75155 kW/K    Edest    523.98 kW
   LTR  low-T recup       Sgen  +1.16569 kW/K    Edest    348.72 kW
   HTR  high-T recup      Sgen  +4.23072 kW/K    Edest   1265.62 kW
   MIX  mixer             Sgen  +0.00003 kW/K    Edest      0.01 kW
   COOL precooler         Sgen  +1.55023 kW/K    Edest    463.75 kW
   PHX  primary HX        Sgen  +0.59714 kW/K    Edest    178.63 kW
   TOTAL                  Sgen +10.22522 kW/K    Edest   3058.88 kW

power balance   W_turb 13317.63 - W_mc 1120.56 - W_rc 2197.06 = 10000.00 kW   (W_dot_net_des 10000.00, err 1.82e-12)
energy balance  q_PHX 19497.52 = W_net 10000.00 + q_cool 9495.57  -> err 1.944 kW


================================================================================================
LEGACY CASE A -- REGRESSION ANCHOR ONLY, NOT THE VALIDATION BASELINE
  equal recuperator effectiveness 0.950, lossless, f_rc 0.39. Agrees with Dostal on eta
  via two CANCELLING errors while its internal states are wrong by up to 5.4 %; kept
  because it reproduces bit-for-bit across machines, so it catches environment drift.
================================================================================================
  turbine inlet        700.000 C   (target 700.0)
  compressor inlet      32.000 C   (target 32.0)
  P_comp_out           20.0000 MPa (target 20.00)
  P_comp_in             7.6923 MPa (target 7.6923)
  pressure ratio        2.6000     (target 2.60)
  recomp_frac          0.39000     (target 0.4097; Table 10.1 states 0.39 -- see 2.3.4a)
  eff_HTR / eff_LTR    0.95000 / 0.95000
  recup UA total        1882.3 kW/K
  m_dot_co2             87.269 kg/s   (m_dot_htf 71.279 kg/s, cp_htf 1.5326 kJ/kg-K)

  ETA_THERMAL          0.51532  = 51.53 %
  Dostal target        0.51270  = 51.27 %
  deviation              +0.26 percentage points  (+0.51 % relative)
  eta net less cooling 0.51017  (fan power 100.0 kW deducted)

STATE POINTS  (h, s from CoolProp CO2 at the ssc-solved T and P)
#   node            T[C]      P[kPa]   h[kJ/kg]  s[kJ/kg-K]   description
------------------------------------------------------------------------------------------------
0   MC_IN         32.000     7692.31    306.675     1.34780   main compressor inlet
1   MC_OUT        61.099    20000.00    327.256     1.35458   main compressor outlet
2   LTR_HP_OUT   188.507    20000.00    581.645     2.01199   LTR high-pressure outlet
3   MIXER_OUT    177.887    20000.00    566.293     1.97834   LTR-HP + recompressor merge
4   HTR_HP_OUT   522.367    20000.00   1000.908     2.69876   HTR high-pressure outlet = PHX inlet
5   TURB_IN      700.000    20000.00   1223.271     2.95095   turbine inlet
6   TURB_OUT     573.364     7692.31   1073.150     2.97082   turbine outlet = HTR low-pressure inlet
7   HTR_LP_OUT   198.017     7692.31    638.539     2.29499   HTR low-pressure outlet = LTR low-pressure inlet
8   LTR_LP_OUT    72.493     7692.31    483.362     1.90917   LTR low-pressure outlet = flow split point
9   RC_OUT       161.969    20000.00    542.281     1.92413   recompressor outlet
10  PC_IN            nan         nan        nan         nan   pre-compressor inlet   (partial-cooling only -> NaN here)
11  PC_OUT           nan         nan        nan         nan   pre-compressor outlet  (partial-cooling only -> NaN here)

property cross-check   max |h_ssc - h_CoolProp| = 1.55e-04 kJ/kg   max |s_ssc - s_CoolProp| = 3.40e-07 kJ/kg-K
mixer energy balance   h[3] = 566.2928   (1-f)h[2] + f*h[9] = 566.2929   err 8.33e-05 kJ/kg

ENTROPY GENERATION  (T0 = 299.15 K = ambient)
   MC   main compressor   Sgen  +0.36106 kW/K    Edest    108.01 kW
   RC   recompressor      Sgen  +0.50937 kW/K    Edest    152.38 kW
   TURB turbine           Sgen  +1.73376 kW/K    Edest    518.66 kW
   LTR  low-T recup       Sgen  +1.32645 kW/K    Edest    396.81 kW
   HTR  high-T recup      Sgen  +3.89109 kW/K    Edest   1164.02 kW
   MIX  mixer             Sgen  +0.05394 kW/K    Edest     16.14 kW
   COOL precooler         Sgen  +1.55761 kW/K    Edest    465.96 kW
   PHX  primary HX        Sgen  +0.48074 kW/K    Edest    143.81 kW
   TOTAL                  Sgen  +9.91403 kW/K    Edest   2965.78 kW

power balance   W_turb 13100.92 - W_mc 1095.64 - W_rc 2005.28 = 10000.00 kW   (W_dot_net_des 10000.00, err 0.00e+00)
energy balance  q_PHX 19405.43 = W_net 10000.00 + q_cool 9405.78  -> err 0.354 kW

================================================================================================
RECUPERATOR EFFECTIVENESS SWEEP -- LEGACY case-A parameterisation (see docstring)
================================================================================================
   recup eff  eta_thermal  UA_tot [kW/K]  d vs Dostal
      0.9000      0.47594         1114.2       -3.68 pp
      0.9200      0.49163         1326.6       -2.11 pp
      0.9300      0.49951         1468.4       -1.32 pp
      0.9400      0.50745         1646.9       -0.52 pp
      0.9450      0.51140         1755.7       -0.13 pp
      0.9500      0.51532         1882.3       +0.26 pp
      0.9600      0.52306         2213.4       +1.04 pp
      0.9700      0.53057         2731.4       +1.79 pp

  -> eta = 51.27 % is reproduced at recuperator effectiveness ~ 0.9467

================================================================================================
VERDICT: converged at 7.69 MPa / 32.0 C compressor inlet.
  adopted case F : eta_thermal = 51.289 %  (+0.019 pp vs Dostal 51.27 %)
  legacy  case A : eta_thermal = 51.532 %  (+0.262 pp) -- anchor only
================================================================================================
```

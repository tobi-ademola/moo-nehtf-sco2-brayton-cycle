# sCO2 cycle -- node-by-node error vs Dostal (2004) Table 10.4

| | |
|---|---|
| script | `scripts/compare_dostal_nodes.py` |
| run (UTC) | 20260813T012414Z |
| git commit | `fad1a0e-dirty` |
| case | high-performance 700 C, base (lossless) |
| source table | Dostal 2004 Table 10.4, p.229 (conservative) |

```
========================================================================================================
DOSTAL 2004 TABLE 10.4 (HIGH-PERFORMANCE, 700 C) -- NODE-BY-NODE ERROR
========================================================================================================
  model: TIT 700.0 C, MC inlet 32.0 C, P_high 20.0 MPa, PR 2.60, f_rc 0.39,
         eta_mc 0.89 / eta_rc 0.89 / eta_t 0.90, recup effectiveness 0.95,
         zero pressure loss (so PR is exactly 2.60)
  h and s below are ssc's OWN values, not re-derived -- this is a
  PySAM-vs-Dostal comparison. (validate_dostal.py separately shows ssc
  agrees with CoolProp to 1.6e-04 kJ/kg in h, 3.4e-07 kJ/kg-K in s, and
  the two share a reference state: Dostal s1 = 1.3478 vs ssc 1.34780.)

  NOT compared here (no Dostal row; see VALIDATION.md 2.3.3a): LTR_HP_OUT, RC_OUT

pt   node        qty  unit             Dostal        PySAM    abs error    % error  flag
--------------------------------------------------------------------------------------------------------
1    MC_IN       T    C               32.0000      32.0000      +0.0000    +0.000 %  
1    MC_IN       P    kPa           7692.3100    7692.3077      -0.0023    -0.000 %  
1    MC_IN       h    kJ/kg          306.6700     306.6747      +0.0047    +0.002 %  
1    MC_IN       s    kJ/kg-K          1.3478       1.3478      -0.0000    -0.000 %  

2    MC_OUT      T    C               61.1000      61.0985      -0.0015    -0.000 %  
2    MC_OUT      P    kPa          20000.0000   20000.0000      +0.0000    +0.000 %  
2    MC_OUT      h    kJ/kg          327.2600     327.2563      -0.0037    -0.001 %  
2    MC_OUT      s    kJ/kg-K          1.3546       1.3546      -0.0000    -0.002 %  

3    MIXER_OUT   T    C              159.8800     177.8865     +18.0065    +4.158 %  
3    MIXER_OUT   P    kPa          19990.2200   20000.0000      +9.7800    +0.049 %  
3    MIXER_OUT   h    kJ/kg          539.0700     566.2928     +27.2228    +5.050 %  FLAG
3    MIXER_OUT   s    kJ/kg-K          1.9168       1.9783      +0.0615    +3.211 %  FLAG

4    HTR_HP_OUT  T    C              531.3300     522.3671      -8.9629    -1.114 %  
4    HTR_HP_OUT  P    kPa          19944.5600   20000.0000     +55.4400    +0.278 %  
4    HTR_HP_OUT  h    kJ/kg         1012.0300    1000.9077     -11.1223    -1.099 %  
4    HTR_HP_OUT  s    kJ/kg-K          2.7132       2.6988      -0.0144    -0.532 %  

5    TURB_IN     T    C              700.0000     700.0000      +0.0000    +0.000 %  
5    TURB_IN     P    kPa          19814.5600   20000.0000    +185.4400    +0.936 %  
5    TURB_IN     h    kJ/kg         1223.3400    1223.2714      -0.0686    -0.006 %  
5    TURB_IN     s    kJ/kg-K          2.9529       2.9510      -0.0019    -0.066 %  

6    TURB_OUT    T    C              578.3100     573.3637      -4.9463    -0.581 %  
6    TURB_OUT    P    kPa           7929.2200    7692.3077    -236.9123    -2.988 %  
6    TURB_OUT    h    kJ/kg         1078.9500    1073.1501      -5.7999    -0.538 %  
6    TURB_OUT    s    kJ/kg-K          2.9719       2.9708      -0.0011    -0.036 %  

7    HTR_LP_OUT  T    C              169.8500     198.0169     +28.1669    +6.358 %  
7    HTR_LP_OUT  P    kPa           7802.6400    7692.3077    -110.3323    -1.414 %  
7    HTR_LP_OUT  h    kJ/kg          605.9800     638.5392     +32.5592    +5.373 %  FLAG
7    HTR_LP_OUT  s    kJ/kg-K          2.2212       2.2950      +0.0738    +3.322 %  FLAG

8    LTR_LP_OUT  T    C               71.0500      72.4935      +1.4435    +0.419 %  
8    LTR_LP_OUT  P    kPa           7704.9300    7692.3077     -12.6223    -0.164 %  
8    LTR_LP_OUT  h    kJ/kg          480.9600     483.3621      +2.4021    +0.499 %  
8    LTR_LP_OUT  s    kJ/kg-K          1.9020       1.9092      +0.0072    +0.377 %  

========================================================================================================
SUMMARY
========================================================================================================

worst |% error| by quantity (across the 8 compared nodes):
   T    worst   +6.358 %  at HTR_LP_OUT  (pt 7)      RMS  2.727 %
   P    worst   -2.988 %  at TURB_OUT    (pt 6)      RMS  1.220 %
   h    worst   +5.373 %  at HTR_LP_OUT  (pt 7)      RMS  2.649 %
   s    worst   +3.322 %  at HTR_LP_OUT  (pt 7)      RMS  1.650 %

nodes flagged (|%err| > 2 % on h or s): 
   MIXER_OUT   (pt 3)  h  Dostal   539.0700  PySAM   566.2928    +5.050 %
   MIXER_OUT   (pt 3)  s  Dostal     1.9168  PySAM     1.9783    +3.211 %
   HTR_LP_OUT  (pt 7)  h  Dostal   605.9800  PySAM   638.5392    +5.373 %
   HTR_LP_OUT  (pt 7)  s  Dostal     2.2212  PySAM     2.2950    +3.322 %

eta_thermal   Dostal  51.27 %   PySAM  51.53 %   abs +0.262 pp   % error +0.511 %

========================================================================================================
MARKDOWN (paste into VALIDATION.md 2.3.4)
========================================================================================================
| Dostal pt | Node | Quantity | Dostal | PySAM | Abs error | % error | Flag |
|---|---|---|---|---|---|---|---|
| 1 | `MC_IN` | T (C) | 32.0000 | 32.0000 | +0.0000 | +0.000 % |  |
| 1 | `MC_IN` | P (kPa) | 7692.3100 | 7692.3077 | -0.0023 | -0.000 % |  |
| 1 | `MC_IN` | h (kJ/kg) | 306.6700 | 306.6747 | +0.0047 | +0.002 % |  |
| 1 | `MC_IN` | s (kJ/kg-K) | 1.3478 | 1.3478 | -0.0000 | -0.000 % |  |
| 2 | `MC_OUT` | T (C) | 61.1000 | 61.0985 | -0.0015 | -0.000 % |  |
| 2 | `MC_OUT` | P (kPa) | 20000.0000 | 20000.0000 | +0.0000 | +0.000 % |  |
| 2 | `MC_OUT` | h (kJ/kg) | 327.2600 | 327.2563 | -0.0037 | -0.001 % |  |
| 2 | `MC_OUT` | s (kJ/kg-K) | 1.3546 | 1.3546 | -0.0000 | -0.002 % |  |
| 3 | `MIXER_OUT` | T (C) | 159.8800 | 177.8865 | +18.0065 | +4.158 % |  |
| 3 | `MIXER_OUT` | P (kPa) | 19990.2200 | 20000.0000 | +9.7800 | +0.049 % |  |
| 3 | `MIXER_OUT` | h (kJ/kg) | 539.0700 | 566.2928 | +27.2228 | +5.050 % | **FLAG** |
| 3 | `MIXER_OUT` | s (kJ/kg-K) | 1.9168 | 1.9783 | +0.0615 | +3.211 % | **FLAG** |
| 4 | `HTR_HP_OUT` | T (C) | 531.3300 | 522.3671 | -8.9629 | -1.114 % |  |
| 4 | `HTR_HP_OUT` | P (kPa) | 19944.5600 | 20000.0000 | +55.4400 | +0.278 % |  |
| 4 | `HTR_HP_OUT` | h (kJ/kg) | 1012.0300 | 1000.9077 | -11.1223 | -1.099 % |  |
| 4 | `HTR_HP_OUT` | s (kJ/kg-K) | 2.7132 | 2.6988 | -0.0144 | -0.532 % |  |
| 5 | `TURB_IN` | T (C) | 700.0000 | 700.0000 | +0.0000 | +0.000 % |  |
| 5 | `TURB_IN` | P (kPa) | 19814.5600 | 20000.0000 | +185.4400 | +0.936 % |  |
| 5 | `TURB_IN` | h (kJ/kg) | 1223.3400 | 1223.2714 | -0.0686 | -0.006 % |  |
| 5 | `TURB_IN` | s (kJ/kg-K) | 2.9529 | 2.9510 | -0.0019 | -0.066 % |  |
| 6 | `TURB_OUT` | T (C) | 578.3100 | 573.3637 | -4.9463 | -0.581 % |  |
| 6 | `TURB_OUT` | P (kPa) | 7929.2200 | 7692.3077 | -236.9123 | -2.988 % |  |
| 6 | `TURB_OUT` | h (kJ/kg) | 1078.9500 | 1073.1501 | -5.7999 | -0.538 % |  |
| 6 | `TURB_OUT` | s (kJ/kg-K) | 2.9719 | 2.9708 | -0.0011 | -0.036 % |  |
| 7 | `HTR_LP_OUT` | T (C) | 169.8500 | 198.0169 | +28.1669 | +6.358 % |  |
| 7 | `HTR_LP_OUT` | P (kPa) | 7802.6400 | 7692.3077 | -110.3323 | -1.414 % |  |
| 7 | `HTR_LP_OUT` | h (kJ/kg) | 605.9800 | 638.5392 | +32.5592 | +5.373 % | **FLAG** |
| 7 | `HTR_LP_OUT` | s (kJ/kg-K) | 2.2212 | 2.2950 | +0.0738 | +3.322 % | **FLAG** |
| 8 | `LTR_LP_OUT` | T (C) | 71.0500 | 72.4935 | +1.4435 | +0.419 % |  |
| 8 | `LTR_LP_OUT` | P (kPa) | 7704.9300 | 7692.3077 | -12.6223 | -0.164 % |  |
| 8 | `LTR_LP_OUT` | h (kJ/kg) | 480.9600 | 483.3621 | +2.4021 | +0.499 % |  |
| 8 | `LTR_LP_OUT` | s (kJ/kg-K) | 1.9020 | 1.9092 | +0.0072 | +0.377 % |  |
```

# Is Dostal's state table self-consistent with his stated f?

| | |
|---|---|
| script | `scripts/check_dostal_table_consistency.py` |
| run (UTC) | 20260813T014726Z |
| git commit | `fad1a0e-dirty` |
| method | arithmetic on published values + CoolProp; NO model run |

```
====================================================================================================
High-Performance 700 C   (Table 10.4, Table 10.1 states f = 0.39)
====================================================================================================
   HTR balance   h4-h3 = 472.9600   h6-h7 = 472.9700   residual -0.0100 kJ/kg
      -> PASS: the HTR rows are internally consistent to 0.01 kJ/kg

   recompressor  h8s(20 MPa, s8) = 532.7177   ->  h_RC = 539.1148 kJ/kg  (eta_rc 0.89)

   at the STATED f = 0.39:
      LTR hot duty     h7-h8      = 125.0200 kJ/kg
      -> h[LTR_HP_OUT] = h2 + duty/(1-f) = 532.2108 kJ/kg
      -> h3 predicted  = 534.9034   tabulated 539.0700   residual -4.1666 kJ/kg (-0.773 %)

   solving the mixer for f:  f_implied = 0.4097   (Table 10.1 states 0.39, delta +0.0197)
      at f_implied:  h[LTR_HP_OUT] = 539.0389   h[RC_OUT] = 539.1148   difference -0.0758
      (a well-designed junction mixes streams of nearly EQUAL enthalpy, so a near-zero
       difference here is independent evidence that f_implied is the real design point)

   robustness -- what would it take for f = 0.39 to be right?
      the mixer would need h[RC_OUT] = 549.7985 kJ/kg
      which requires eta_rc = 0.7519   (Dostal states 0.89 conservative, 0.948 best)
      -> NOT PLAUSIBLE: no eta_rc Dostal states can rescue the stated f
      at eta_rc = 0.890 -> f_implied = 0.4097
      at eta_rc = 0.948 -> f_implied = 0.4167

   residual -4.1666 kJ/kg, f_implied - f_stated = +0.0197

====================================================================================================
Advanced 650 C (control)   (Table 10.3, Table 10.1 states f = 0.41)
====================================================================================================
   HTR balance   h4-h3 = 424.7700   h6-h7 = 424.7800   residual -0.0100 kJ/kg
      -> PASS: the HTR rows are internally consistent to 0.01 kJ/kg

   recompressor  h8s(20 MPa, s8) = 528.4833   ->  h_RC = 534.7760 kJ/kg  (eta_rc 0.89)

   at the STATED f = 0.41:
      LTR hot duty     h7-h8      = 123.4400 kJ/kg
      -> h[LTR_HP_OUT] = h2 + duty/(1-f) = 536.4803 kJ/kg
      -> h3 predicted  = 535.7816   tabulated 534.7300   residual +1.0516 kJ/kg (+0.197 %)

   solving the mixer for f:  f_implied = 0.4049   (Table 10.1 states 0.41, delta -0.0051)
      at f_implied:  h[LTR_HP_OUT] = 534.6987   h[RC_OUT] = 534.7760   difference -0.0773
      (a well-designed junction mixes streams of nearly EQUAL enthalpy, so a near-zero
       difference here is independent evidence that f_implied is the real design point)

   robustness -- what would it take for f = 0.41 to be right?
      the mixer would need h[RC_OUT] = 532.2112 kJ/kg
      which requires eta_rc = 0.9318   (Dostal states 0.89 conservative, 0.948 best)
      -> PLAUSIBLE: the finding is NOT robust, eta_rc could explain it
      at eta_rc = 0.890 -> f_implied = 0.4049
      at eta_rc = 0.948 -> f_implied = 0.4119

   residual +1.0516 kJ/kg, f_implied - f_stated = -0.0051

====================================================================================================
CONCLUSION
====================================================================================================
   The control CALIBRATES the method rather than passing or failing it: it
   sets how much residual is just rounding in a table printed to 2 decimals
   plus whatever cycle detail this 3-balance reduction omits.

   design                           f stated    f implied      delta f     residual
   Advanced 650 C (control)             0.41       0.4049      -0.0051   +1.0516 kJ/kg
   High-Performance 700 C               0.39       0.4097      +0.0197   -4.1666 kJ/kg

   noise floor from the control: 1.05 kJ/kg (delta f -0.0051)
   High-Performance residual is 4.0x that floor, and its delta f is 3.9x
   larger -- so the discrepancy is well outside the method's resolution.

   The tell: BOTH state tables independently encode f ~ 0.405-0.410.
   The Advanced design STATES 0.41 and its table agrees. The High-Performance
   design STATES 0.39 but its table encodes 0.4097 -- essentially the same
   value as the other designs. At that f, its two mixing streams differ by
   only +0.076 kJ/kg, i.e. the junction is very nearly isenthalpic, which is
   the hallmark of a properly optimised mixing point.

   READING: Table 10.1's f = 0.39 for the High-Performance design is not
   supported by Table 10.4's own state points. This is EVIDENCE, not proof --
   an alternative reading is that this design uses a slightly different
   topology or an off-optimum junction that the 3-balance reduction misses.

   CONSEQUENCE for VALIDATION.md 2.3.4: pinning f = 0.39 while comparing
   against Table 10.4's nodes may be mixing two different design points, which
   is a SECOND candidate cause of the MIXER_OUT / HTR_LP_OUT errors, separate
   from recuperator duty split. Testable directly: re-run pinned at f = 0.41.
```

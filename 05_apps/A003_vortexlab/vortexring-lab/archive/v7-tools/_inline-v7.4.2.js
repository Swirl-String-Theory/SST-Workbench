
"use strict";
const APP_VERSION='7.4.2';
const APP_BASE_VERSION='7.4.1';
const APP_PATCH_NOTES=[
  'v7.4.1 audit basis preserved (provenance sync, geometric diagnostics, GP-Δ state, capacity indicator)',
  'Merged SST bundle research-track (Ω_core/Ω_bundle/Ω_wall separation, bundle visualization and optional coupling)',
  'Guards: Ω_wall legacy coupling mutually exclusive with bundle-flow coupling; friction blocked when bundle coupling is on',
  'Selftests extended with bundle T9a–T9e'
];
const A_SIM_EPS=1e-30;
const A_SIM_INPUT_FLOOR=1e-18;
const CONTACT_ULP_FACTOR=64;
// ================= dataset: ideal trefoil 3:1:1 (Gilbert, 183 modi) =================
const IDEAL_TREFOIL_3_1_1 = {
  knotId: "3:1:1",
  L: 16.371637,
  coeffs: [
  {I:1,A:[0.374139, 0, 0],B:[0, 0.37392799999999998, 0]},
  {I:2,A:[0.82424600000000003, 0.75026000000000004, 0.00035199999999999999],B:[0.75044999999999995, -0.82395200000000002, -0.0019910000000000001]},
  {I:3,A:[0.00025700000000000001, -0.00093199999999999999, 0.35239700000000002],B:[-0.00076999999999999996, 0.00072599999999999997, -0.386764]},
  {I:4,A:[0.011651999999999999, -0.010656000000000001, 0.00074299999999999995],B:[0.010739, 0.011613, -0.00023000000000000001]},
  {I:5,A:[0.010503999999999999, 0.110306, 0.00019900000000000001],B:[0.110745, -0.010366, -0.00023499999999999999]},
  {I:6,A:[1.5e-05, -6.0000000000000002e-06, -0.047465],B:[-5.0000000000000002e-05, -9.9999999999999995e-07, 0.0045950000000000001]},
  {I:7,A:[-0.000292, 0.0024169999999999999, -7.9999999999999996e-06],B:[-0.002529, -0.00025500000000000002, -9.0000000000000002e-06]},
  {I:8,A:[0.016487000000000002, -0.021784000000000001, 4.1e-05],B:[-0.021922000000000001, -0.016421000000000002, -4.3999999999999999e-05]},
  {I:9,A:[-2.9e-05, -1.8e-05, 0.011178],B:[4.8999999999999998e-05, 4.1e-05, 0.0084139999999999996]},
  {I:10,A:[-0.00021599999999999999, -0.00029, -1.8e-05],B:[0.00031100000000000002, -0.00019699999999999999, -4.3999999999999999e-05]},
  {I:11,A:[-0.011727, 0.0021840000000000002, 6.9999999999999999e-06],B:[0.002202, 0.011682, 2.0000000000000002e-05]},
  {I:12,A:[2.5999999999999998e-05, 1.9000000000000001e-05, -0.0013079999999999999],B:[-3.9999999999999998e-06, -1.9000000000000001e-05, -0.0070390000000000001]},
  {I:13,A:[0.00032499999999999999, 5.5000000000000002e-05, -9.0000000000000002e-06],B:[-5.8999999999999998e-05, 0.00028899999999999998, 2.4000000000000001e-05]},
  {I:14,A:[0.0052129999999999998, 0.0032009999999999999, 9.9999999999999995e-07],B:[0.0032100000000000002, -0.0051879999999999999, 1.0000000000000001e-05]},
  {I:15,A:[-1.5e-05, -1.5999999999999999e-05, -0.0019170000000000001],B:[-1.7e-05, 9.9999999999999995e-07, 0.0031210000000000001]},
  {I:16,A:[-0.000136, 6.2000000000000003e-05, 1.9000000000000001e-05],B:[-7.4999999999999993e-05, -0.000112, -6.9999999999999999e-06]},
  {I:17,A:[-0.00099500000000000001, -0.0034629999999999999, -9.9999999999999995e-07],B:[-0.0034740000000000001, 0.00098799999999999995, -1.5e-05]},
  {I:18,A:[3.0000000000000001e-06, 7.9999999999999996e-06, 0.0021779999999999998],B:[1.9000000000000001e-05, 7.9999999999999996e-06, -0.00061499999999999999]},
  {I:19,A:[3.3000000000000003e-05, -9.3999999999999994e-05, -1.5999999999999999e-05],B:[0.000113, 2.8e-05, -3.9999999999999998e-06]},
  {I:20,A:[-0.0009990000000000001, 0.002013, -0],B:[0.002019, 0.00099799999999999997, 0]},
  {I:21,A:[3.9999999999999998e-06, 9.9999999999999995e-07, -0.0012700000000000001],B:[-1.2999999999999999e-05, -1.2e-05, -0.00062600000000000004]},
  {I:22,A:[3.4e-05, 6.0000000000000002e-05, 9.0000000000000002e-06],B:[-7.2000000000000002e-05, 2.5999999999999998e-05, 1.0000000000000001e-05]},
  {I:23,A:[0.0013829999999999999, -0.00053899999999999998, 1.9999999999999999e-06],B:[-0.00054000000000000001, -0.001382, 3.9999999999999998e-06]},
  {I:24,A:[-5.0000000000000004e-06, -1.1e-05, 0.00034400000000000001],B:[9.0000000000000002e-06, 6.9999999999999999e-06, 0.00088999999999999995]},
  {I:25,A:[-5.7000000000000003e-05, -2.5000000000000001e-05, 9.9999999999999995e-07],B:[1.9000000000000001e-05, -4.8000000000000001e-05, -7.9999999999999996e-06]},
  {I:26,A:[-0.00093099999999999997, -0.00035599999999999998, -0],B:[-0.000357, 0.00093099999999999997, -5.0000000000000004e-06]},
  {I:27,A:[6.0000000000000002e-06, 9.0000000000000002e-06, 0.00022800000000000001],B:[-1.9999999999999999e-06, -0, -0.00059699999999999998]},
  {I:28,A:[4.0000000000000003e-05, -6.9999999999999999e-06, -3.9999999999999998e-06],B:[1.9000000000000001e-05, 3.6000000000000001e-05, 3.9999999999999998e-06]},
  {I:29,A:[0.00030800000000000001, 0.000611, 9.9999999999999995e-07],B:[0.000611, -0.00030699999999999998, 6.9999999999999999e-06]},
  {I:30,A:[1.9999999999999999e-06, 9.9999999999999995e-07, -0.00039100000000000002],B:[-6.0000000000000002e-06, 9.9999999999999995e-07, 0.000195]},
  {I:31,A:[-1.5e-05, 1.9000000000000001e-05, 3.0000000000000001e-06],B:[-3.1000000000000001e-05, -1.2e-05, 9.9999999999999995e-07]},
  {I:32,A:[0.000125, -0.00045199999999999998, 3.9999999999999998e-06],B:[-0.00045199999999999998, -0.00012400000000000001, -3.9999999999999998e-06]},
  {I:33,A:[-6.0000000000000002e-06, -9.9999999999999995e-07, 0.000281],B:[3.9999999999999998e-06, -3.0000000000000001e-06, 7.7000000000000001e-05]},
  {I:34,A:[-1.9999999999999999e-06, -7.9999999999999996e-06, -1.9999999999999999e-06],B:[2.4000000000000001e-05, -5.0000000000000004e-06, -9.9999999999999995e-07]},
  {I:35,A:[-0.000272, 0.000173, -1.9999999999999999e-06],B:[0.00017200000000000001, 0.00027300000000000002, -3.9999999999999998e-06]},
  {I:36,A:[6.0000000000000002e-06, -9.9999999999999995e-07, -0.00010399999999999999],B:[1.9999999999999999e-06, 3.9999999999999998e-06, -0.000164]},
  {I:37,A:[7.9999999999999996e-06, 3.0000000000000001e-06, -9.9999999999999995e-07],B:[-9.0000000000000002e-06, 3.9999999999999998e-06, 9.9999999999999995e-07]},
  {I:38,A:[0.00021499999999999999, 3.6000000000000001e-05, -3.9999999999999998e-06],B:[3.6999999999999998e-05, -0.000214, 3.9999999999999998e-06]},
  {I:39,A:[-1.9999999999999999e-06, -1.9999999999999999e-06, -2.0000000000000002e-05],B:[1.9999999999999999e-06, -9.9999999999999995e-07, 0.000121]},
  {I:41,A:[-8.8999999999999995e-05, -0.000113, 3.9999999999999998e-06],B:[-0.000113, 8.7999999999999998e-05, 1.9999999999999999e-06]},
  {I:42,A:[1.9999999999999999e-06, 0, 5.8999999999999998e-05],B:[-0, 3.0000000000000001e-06, -4.6e-05]},
  {I:43,A:[-6.9999999999999999e-06, 6.9999999999999999e-06, -0],B:[-1.9999999999999999e-06, 3.9999999999999998e-06, -0]},
  {I:44,A:[-5.0000000000000004e-06, 8.7999999999999998e-05, -0],B:[9.0000000000000006e-05, 5.0000000000000004e-06, -3.9999999999999998e-06]},
  {I:46,A:[0, -7.9999999999999996e-06, -9.9999999999999995e-07],B:[1.1e-05, -5.0000000000000004e-06, -9.9999999999999995e-07]},
  {I:47,A:[3.6000000000000001e-05, -3.6000000000000001e-05, 9.9999999999999995e-07],B:[-3.6000000000000001e-05, -3.6000000000000001e-05, -9.9999999999999995e-07]},
  {I:48,A:[3.0000000000000001e-06, -3.0000000000000001e-06, 1.1e-05],B:[3.0000000000000001e-06, 1.9999999999999999e-06, 9.0000000000000002e-06]},
  {I:49,A:[9.0000000000000002e-06, 3.9999999999999998e-06, -0],B:[-1.1e-05, 1.1e-05, 3.0000000000000001e-06]},
  {I:50,A:[-2.0999999999999999e-05, 3.9999999999999998e-06, -9.9999999999999995e-07],B:[3.9999999999999998e-06, 2.3e-05, -9.9999999999999995e-07]},
  {I:51,A:[-9.9999999999999995e-07, 9.9999999999999995e-07, -3.9999999999999998e-06],B:[-3.0000000000000001e-06, 1.9999999999999999e-06, 6.0000000000000002e-06]},
  {I:52,A:[-1.5e-05, 1.9999999999999999e-06, -0],B:[-9.9999999999999995e-07, -1.5999999999999999e-05, -9.9999999999999995e-07]},
  {I:53,A:[3.9999999999999998e-06, -0, 3.0000000000000001e-06],B:[-9.9999999999999995e-07, -3.9999999999999998e-06, 1.9999999999999999e-06]},
  {I:54,A:[-0, 1.9999999999999999e-06, 1.2999999999999999e-05],B:[9.9999999999999995e-07, -9.9999999999999995e-07, -1.1e-05]},
  {I:55,A:[1.0000000000000001e-05, -1.2e-05, 9.9999999999999995e-07],B:[1.2e-05, 1.4e-05, 0]},
  {I:56,A:[-3.0000000000000001e-06, 1.2999999999999999e-05, 9.9999999999999995e-07],B:[1.2e-05, 1.9999999999999999e-06, -1.9999999999999999e-06]},
  {I:57,A:[-1.9999999999999999e-06, -9.9999999999999995e-07, -2.5999999999999998e-05],B:[0, -1.9999999999999999e-06, -0]},
  {I:58,A:[3.0000000000000001e-06, 2.0000000000000002e-05, 0],B:[-1.5999999999999999e-05, -3.9999999999999998e-06, -9.9999999999999995e-07]},
  {I:59,A:[1.5e-05, -1.5999999999999999e-05, -9.9999999999999995e-07],B:[-1.4e-05, -1.5999999999999999e-05, 1.9999999999999999e-06]},
  {I:60,A:[3.9999999999999998e-06, -1.9999999999999999e-06, 2.4000000000000001e-05],B:[1.9999999999999999e-06, 3.0000000000000001e-06, 2.0999999999999999e-05]},
  {I:61,A:[-1.2999999999999999e-05, -1.8e-05, -0],B:[1.0000000000000001e-05, -1.1e-05, -9.9999999999999995e-07]},
  {I:62,A:[-2.8e-05, 1.9999999999999999e-06, -0],B:[1.9999999999999999e-06, 2.9e-05, 0]},
  {I:63,A:[-9.9999999999999995e-07, 3.9999999999999998e-06, -3.9999999999999998e-06],B:[-5.0000000000000004e-06, -1.9999999999999999e-06, -3.4e-05]},
  {I:64,A:[1.5999999999999999e-05, 6.0000000000000002e-06, -9.9999999999999995e-07],B:[1.9999999999999999e-06, 2.0000000000000002e-05, 1.9999999999999999e-06]},
  {I:65,A:[2.5999999999999998e-05, 2.0999999999999999e-05, 0],B:[1.9000000000000001e-05, -2.6999999999999999e-05, -0]},
  {I:66,A:[-3.0000000000000001e-06, -5.0000000000000004e-06, -2.1999999999999999e-05],B:[3.9999999999999998e-06, -9.9999999999999995e-07, 2.9e-05]},
  {I:67,A:[-1.2999999999999999e-05, 1.0000000000000001e-05, 9.9999999999999995e-07],B:[-1.2e-05, -1.7e-05, -9.9999999999999995e-07]},
  {I:68,A:[-6.9999999999999999e-06, -3.4e-05, -9.9999999999999995e-07],B:[-3.4e-05, 6.0000000000000002e-06, -1.9999999999999999e-06]},
  {I:69,A:[3.9999999999999998e-06, 3.0000000000000001e-06, 3.4e-05],B:[-9.9999999999999995e-07, 3.0000000000000001e-06, -6.9999999999999999e-06]},
  {I:70,A:[1.9999999999999999e-06, -1.7e-05, -9.9999999999999995e-07],B:[1.7e-05, 5.0000000000000004e-06, -0]},
  {I:71,A:[-1.9000000000000001e-05, 3.1000000000000001e-05, -9.9999999999999995e-07],B:[3.1000000000000001e-05, 1.9000000000000001e-05, 1.9999999999999999e-06]},
  {I:72,A:[-1.9999999999999999e-06, 0, -3.1999999999999999e-05],B:[-1.9999999999999999e-06, -3.9999999999999998e-06, -1.9000000000000001e-05]},
  {I:73,A:[1.0000000000000001e-05, 1.2999999999999999e-05, 0],B:[-1.5e-05, 9.0000000000000002e-06, 0]},
  {I:74,A:[3.3000000000000003e-05, -1.1e-05, 3.0000000000000001e-06],B:[-1.1e-05, -3.3000000000000003e-05, -9.9999999999999995e-07]},
  {I:75,A:[0, -1.9999999999999999e-06, 1.0000000000000001e-05],B:[9.9999999999999995e-07, 9.9999999999999995e-07, 3.1000000000000001e-05]},
  {I:76,A:[-1.5999999999999999e-05, -3.0000000000000001e-06, -9.9999999999999995e-07],B:[5.0000000000000004e-06, -1.4e-05, 0]},
  {I:77,A:[-3.1000000000000001e-05, -1.5e-05, -1.9999999999999999e-06],B:[-1.4e-05, 3.1999999999999999e-05, -9.9999999999999995e-07]},
  {I:78,A:[9.9999999999999995e-07, 9.9999999999999995e-07, 1.5e-05],B:[-9.9999999999999995e-07, 0, -2.9e-05]},
  {I:79,A:[1.5999999999999999e-05, -7.9999999999999996e-06, -0],B:[6.0000000000000002e-06, 1.0000000000000001e-05, 0]},
  {I:80,A:[1.2999999999999999e-05, 3.1000000000000001e-05, 0],B:[2.9e-05, -1.2999999999999999e-05, 3.0000000000000001e-06]},
  {I:81,A:[-0, 9.9999999999999995e-07, -2.6999999999999999e-05],B:[-9.9999999999999995e-07, 9.9999999999999995e-07, 1.1e-05]},
  {I:82,A:[-6.9999999999999999e-06, 1.2e-05, 9.9999999999999995e-07],B:[-1.4e-05, -1.9999999999999999e-06, 0]},
  {I:83,A:[1.0000000000000001e-05, -3.0000000000000001e-05, 9.9999999999999995e-07],B:[-2.9e-05, -1.1e-05, -9.9999999999999995e-07]},
  {I:84,A:[-9.9999999999999995e-07, -0, 2.5999999999999998e-05],B:[9.9999999999999995e-07, -9.9999999999999995e-07, 1.0000000000000001e-05]},
  {I:85,A:[-3.0000000000000001e-06, -9.0000000000000002e-06, -0],B:[1.5e-05, -6.0000000000000002e-06, -9.9999999999999995e-07]},
  {I:86,A:[-2.4000000000000001e-05, 1.2999999999999999e-05, -9.9999999999999995e-07],B:[1.4e-05, 2.5999999999999998e-05, -0]},
  {I:87,A:[1.9999999999999999e-06, -1.9999999999999999e-06, -1.2e-05],B:[9.9999999999999995e-07, 1.9999999999999999e-06, -2.3e-05]},
  {I:88,A:[1.2e-05, 1.9999999999999999e-06, -0],B:[-6.9999999999999999e-06, 1.1e-05, 9.9999999999999995e-07]},
  {I:89,A:[2.5000000000000001e-05, 6.9999999999999999e-06, 9.9999999999999995e-07],B:[6.0000000000000002e-06, -2.5999999999999998e-05, 0]},
  {I:90,A:[-9.9999999999999995e-07, 1.9999999999999999e-06, -6.0000000000000002e-06],B:[-1.9999999999999999e-06, 0, 2.3e-05]},
  {I:91,A:[-1.2e-05, 5.0000000000000004e-06, 0],B:[-3.0000000000000001e-06, -7.9999999999999996e-06, -0]},
  {I:92,A:[-1.4e-05, -1.9000000000000001e-05, 9.9999999999999995e-07],B:[-2.0000000000000002e-05, 1.4e-05, 0]},
  {I:93,A:[-1.9999999999999999e-06, -9.9999999999999995e-07, 1.9000000000000001e-05],B:[1.9999999999999999e-06, -9.9999999999999995e-07, -1.1e-05]},
  {I:94,A:[6.0000000000000002e-06, -9.0000000000000002e-06, -9.9999999999999995e-07],B:[9.0000000000000002e-06, 3.0000000000000001e-06, -9.9999999999999995e-07]},
  {I:95,A:[-3.0000000000000001e-06, 2.0999999999999999e-05, 0],B:[2.1999999999999999e-05, 3.0000000000000001e-06, -0]},
  {I:96,A:[3.0000000000000001e-06, 0, -1.8e-05],B:[-9.9999999999999995e-07, 9.9999999999999995e-07, -3.0000000000000001e-06]},
  {I:97,A:[3.0000000000000001e-06, 6.9999999999999999e-06, 0],B:[-9.0000000000000002e-06, 1.9999999999999999e-06, 0]},
  {I:98,A:[1.5e-05, -1.2999999999999999e-05, -9.9999999999999995e-07],B:[-1.2999999999999999e-05, -1.4e-05, 1.9999999999999999e-06]},
  {I:99,A:[-1.9999999999999999e-06, 9.9999999999999995e-07, 1.0000000000000001e-05],B:[-1.9999999999999999e-06, -9.9999999999999995e-07, 1.2999999999999999e-05]},
  {I:100,A:[-6.9999999999999999e-06, -3.9999999999999998e-06, 0],B:[3.9999999999999998e-06, -6.0000000000000002e-06, -0]},
  {I:101,A:[-1.8e-05, -0, 9.9999999999999995e-07],B:[-9.9999999999999995e-07, 1.7e-05, -0]},
  {I:102,A:[0, -9.9999999999999995e-07, 1.9999999999999999e-06],B:[1.9999999999999999e-06, 9.9999999999999995e-07, -1.4e-05]},
  {I:103,A:[6.9999999999999999e-06, -0, 9.9999999999999995e-07],B:[3.0000000000000001e-06, 6.9999999999999999e-06, -0]},
  {I:104,A:[1.1e-05, 1.0000000000000001e-05, -1.9999999999999999e-06],B:[1.1e-05, -1.1e-05, -9.9999999999999995e-07]},
  {I:105,A:[9.9999999999999995e-07, 9.9999999999999995e-07, -9.0000000000000002e-06],B:[-9.9999999999999995e-07, 0, 7.9999999999999996e-06]},
  {I:106,A:[-3.0000000000000001e-06, 3.9999999999999998e-06, -0],B:[-6.0000000000000002e-06, -3.9999999999999998e-06, -0]},
  {I:107,A:[-0, -1.2999999999999999e-05, 0],B:[-1.2999999999999999e-05, 9.9999999999999995e-07, 9.9999999999999995e-07]},
  {I:108,A:[-9.9999999999999995e-07, -9.9999999999999995e-07, 1.2e-05],B:[0, -9.9999999999999995e-07, 0]},
  {I:109,A:[-1.9999999999999999e-06, -6.0000000000000002e-06, 0],B:[6.0000000000000002e-06, 9.9999999999999995e-07, 0]},
  {I:110,A:[-6.9999999999999999e-06, 9.0000000000000002e-06, 9.9999999999999995e-07],B:[7.9999999999999996e-06, 6.9999999999999999e-06, -1.9999999999999999e-06]},
  {I:111,A:[0, -0, -6.9999999999999999e-06],B:[0, 9.9999999999999995e-07, -6.0000000000000002e-06]},
  {I:112,A:[5.0000000000000004e-06, 3.9999999999999998e-06, 0],B:[-1.9999999999999999e-06, 3.0000000000000001e-06, 0]},
  {I:113,A:[9.0000000000000002e-06, -1.9999999999999999e-06, -9.9999999999999995e-07],B:[-1.9999999999999999e-06, -1.0000000000000001e-05, 9.9999999999999995e-07]},
  {I:114,A:[0, 9.9999999999999995e-07, 9.9999999999999995e-07],B:[-9.9999999999999995e-07, -9.9999999999999995e-07, 7.9999999999999996e-06]},
  {I:115,A:[-3.9999999999999998e-06, -1.9999999999999999e-06, 0],B:[-1.9999999999999999e-06, -3.9999999999999998e-06, -0]},
  {I:116,A:[-6.9999999999999999e-06, -3.9999999999999998e-06, 9.9999999999999995e-07],B:[-3.9999999999999998e-06, 7.9999999999999996e-06, 0]},
  {I:117,A:[-0, -0, 5.0000000000000004e-06],B:[-9.9999999999999995e-07, -0, -5.0000000000000004e-06]},
  {I:118,A:[1.9999999999999999e-06, -9.9999999999999995e-07, 0],B:[3.9999999999999998e-06, 3.0000000000000001e-06, 0]},
  {I:119,A:[1.9999999999999999e-06, 6.9999999999999999e-06, -9.9999999999999995e-07],B:[6.0000000000000002e-06, -3.0000000000000001e-06, -9.9999999999999995e-07]},
  {I:120,A:[-0, -0, -5.0000000000000004e-06],B:[0, 0, 1.9999999999999999e-06]},
  {I:121,A:[9.9999999999999995e-07, 3.0000000000000001e-06, -0],B:[-3.0000000000000001e-06, -1.9999999999999999e-06, -0]},
  {I:122,A:[1.9999999999999999e-06, -5.0000000000000004e-06, -0],B:[-6.0000000000000002e-06, -1.9999999999999999e-06, 0]},
  {I:123,A:[9.9999999999999995e-07, 0, 3.9999999999999998e-06],B:[0, 9.9999999999999995e-07, 3.0000000000000001e-06]},
  {I:124,A:[-3.0000000000000001e-06, -3.0000000000000001e-06, -0],B:[9.9999999999999995e-07, -9.9999999999999995e-07, -0]},
  {I:125,A:[-3.9999999999999998e-06, 1.9999999999999999e-06, 9.9999999999999995e-07],B:[1.9999999999999999e-06, 3.9999999999999998e-06, -0]},
  {I:126,A:[-0, 0, -9.9999999999999995e-07],B:[-9.9999999999999995e-07, -9.9999999999999995e-07, -3.9999999999999998e-06]},
  {I:127,A:[3.0000000000000001e-06, 9.9999999999999995e-07, 0],B:[9.9999999999999995e-07, 1.9999999999999999e-06, 0]},
  {I:128,A:[3.9999999999999998e-06, 0, -0],B:[9.9999999999999995e-07, -3.0000000000000001e-06, 9.9999999999999995e-07]},
  {I:129,A:[-0, -9.9999999999999995e-07, -0],B:[0, 0, 3.0000000000000001e-06]},
  {I:130,A:[-1.9999999999999999e-06, 9.9999999999999995e-07, 0],B:[-1.9999999999999999e-06, -1.9999999999999999e-06, 0]},
  {I:131,A:[-1.9999999999999999e-06, -1.9999999999999999e-06, -9.9999999999999995e-07],B:[-1.9999999999999999e-06, 1.9999999999999999e-06, -0]},
  {I:132,A:[9.9999999999999995e-07, 9.9999999999999995e-07, 1.9999999999999999e-06],B:[-9.9999999999999995e-07, 0, -9.9999999999999995e-07]},
  {I:133,A:[0, -1.9999999999999999e-06, 0],B:[3.0000000000000001e-06, 9.9999999999999995e-07, 9.9999999999999995e-07]},
  {I:135,A:[-9.9999999999999995e-07, -0, -1.9999999999999999e-06],B:[0, -0, -0]},
  {I:136,A:[9.9999999999999995e-07, 9.9999999999999995e-07, -0],B:[-1.9999999999999999e-06, 9.9999999999999995e-07, -0]},
  {I:137,A:[9.9999999999999995e-07, -9.9999999999999995e-07, 9.9999999999999995e-07],B:[-9.9999999999999995e-07, -0, -9.9999999999999995e-07]},
  {I:138,A:[9.9999999999999995e-07, -0, 9.9999999999999995e-07],B:[9.9999999999999995e-07, 9.9999999999999995e-07, 9.9999999999999995e-07]},
  {I:139,A:[-1.9999999999999999e-06, 0, -0],B:[9.9999999999999995e-07, -9.9999999999999995e-07, 9.9999999999999995e-07]},
  {I:140,A:[-9.9999999999999995e-07, 9.9999999999999995e-07, -9.9999999999999995e-07],B:[9.9999999999999995e-07, 0, 0]},
  {I:141,A:[-9.9999999999999995e-07, 0, 0],B:[-9.9999999999999995e-07, -0, -9.9999999999999995e-07]},
  {I:145,A:[-9.9999999999999995e-07, 9.9999999999999995e-07, -0],B:[-9.9999999999999995e-07, 9.9999999999999995e-07, 0]},
  {I:147,A:[9.9999999999999995e-07, -0, -0],B:[-9.9999999999999995e-07, 0, -0]},
  {I:148,A:[0, -0, 0],B:[9.9999999999999995e-07, -9.9999999999999995e-07, 0]},
  {I:149,A:[9.9999999999999995e-07, 0, -9.9999999999999995e-07],B:[0, -9.9999999999999995e-07, 9.9999999999999995e-07]},
  {I:150,A:[-9.9999999999999995e-07, 0, 0],B:[-0, 0, 0]},
  {I:151,A:[9.9999999999999995e-07, -9.9999999999999995e-07, 0],B:[-9.9999999999999995e-07, 9.9999999999999995e-07, -0]},
  {I:152,A:[-1.9999999999999999e-06, -9.9999999999999995e-07, 0],B:[-9.9999999999999995e-07, 9.9999999999999995e-07, 0]},
  {I:154,A:[-9.9999999999999995e-07, 9.9999999999999995e-07, -0],B:[9.9999999999999995e-07, 0, 0]},
  {I:155,A:[9.9999999999999995e-07, 1.9999999999999999e-06, -9.9999999999999995e-07],B:[1.9999999999999999e-06, -9.9999999999999995e-07, -9.9999999999999995e-07]},
  {I:156,A:[0, -9.9999999999999995e-07, -9.9999999999999995e-07],B:[-0, 0, 9.9999999999999995e-07]},
  {I:157,A:[9.9999999999999995e-07, -9.9999999999999995e-07, -0],B:[0, -9.9999999999999995e-07, -0]},
  {I:158,A:[9.9999999999999995e-07, -1.9999999999999999e-06, -0],B:[-1.9999999999999999e-06, -0, 9.9999999999999995e-07]},
  {I:159,A:[0, 0, 9.9999999999999995e-07],B:[0, 0, 0]},
  {I:161,A:[-1.9999999999999999e-06, 9.9999999999999995e-07, 0],B:[9.9999999999999995e-07, 1.9999999999999999e-06, 0]},
  {I:162,A:[-0, -0, -9.9999999999999995e-07],B:[-0, -9.9999999999999995e-07, -9.9999999999999995e-07]},
  {I:163,A:[0, 9.9999999999999995e-07, 0],B:[9.9999999999999995e-07, -9.9999999999999995e-07, -0]},
  {I:164,A:[1.9999999999999999e-06, 0, -0],B:[0, -1.9999999999999999e-06, 0]},
  {I:166,A:[9.9999999999999995e-07, -9.9999999999999995e-07, -0],B:[-0, 0, -0]},
  {I:167,A:[-9.9999999999999995e-07, -1.9999999999999999e-06, 0],B:[-1.9999999999999999e-06, 9.9999999999999995e-07, 0]},
  {I:168,A:[0, 0, 9.9999999999999995e-07],B:[-0, -0, -9.9999999999999995e-07]},
  {I:170,A:[-0, 1.9999999999999999e-06, 0],B:[1.9999999999999999e-06, 0, -0]},
  {I:171,A:[-9.9999999999999995e-07, -0, -9.9999999999999995e-07],B:[0, -0, -0]},
  {I:173,A:[1.9999999999999999e-06, -9.9999999999999995e-07, -0],B:[-9.9999999999999995e-07, -1.9999999999999999e-06, -0]},
  {I:174,A:[9.9999999999999995e-07, 0, 9.9999999999999995e-07],B:[0, 0, 9.9999999999999995e-07]},
  {I:176,A:[-1.9999999999999999e-06, 0, 0],B:[0, 1.9999999999999999e-06, 0]},
  {I:177,A:[-9.9999999999999995e-07, 0, -0],B:[-9.9999999999999995e-07, -0, -9.9999999999999995e-07]},
  {I:179,A:[9.9999999999999995e-07, 9.9999999999999995e-07, 0],B:[9.9999999999999995e-07, -9.9999999999999995e-07, 0]},
  {I:182,A:[-0, -1.9999999999999999e-06, -0],B:[-1.9999999999999999e-06, 0, -0]},
  {I:185,A:[-9.9999999999999995e-07, 1.9999999999999999e-06, 0],B:[9.9999999999999995e-07, 9.9999999999999995e-07, 0]},
  {I:188,A:[1.9999999999999999e-06, -9.9999999999999995e-07, 0],B:[-0, -1.9999999999999999e-06, -9.9999999999999995e-07]},
  {I:189,A:[9.9999999999999995e-07, -0, 0],B:[0, 0, 9.9999999999999995e-07]},
  {I:191,A:[-9.9999999999999995e-07, -0, -9.9999999999999995e-07],B:[-9.9999999999999995e-07, 9.9999999999999995e-07, 0]},
  {I:192,A:[-0, 9.9999999999999995e-07, 9.9999999999999995e-07],B:[-9.9999999999999995e-07, -0, -9.9999999999999995e-07]},
  {I:194,A:[0, 9.9999999999999995e-07, 0],B:[9.9999999999999995e-07, -9.9999999999999995e-07, 0]},
  {I:195,A:[-0, -0, -9.9999999999999995e-07],B:[0, -0, 0]},
  {I:197,A:[0, -1.9999999999999999e-06, -0],B:[-9.9999999999999995e-07, -0, -0]},
  {I:198,A:[0, 0, 9.9999999999999995e-07],B:[-0, 0, 0]},
  {I:200,A:[-9.9999999999999995e-07, 9.9999999999999995e-07, -0],B:[0, 9.9999999999999995e-07, 9.9999999999999995e-07]},
  {I:203,A:[9.9999999999999995e-07, 0, 0],B:[0, -9.9999999999999995e-07, -0]},
  {I:206,A:[-0, -9.9999999999999995e-07, 0],B:[-9.9999999999999995e-07, 0, -0]},
  {I:209,A:[-0, 9.9999999999999995e-07, 0],B:[9.9999999999999995e-07, 0, 0]},
  {I:212,A:[9.9999999999999995e-07, 0, 0],B:[-0, -9.9999999999999995e-07, -0]},
  {I:215,A:[-9.9999999999999995e-07, -0, -0],B:[0, 9.9999999999999995e-07, 0]},
  {I:218,A:[0, 9.9999999999999995e-07, -0],B:[0, 0, -0]},
  {I:250,A:[0, -0, -0],B:[9.9999999999999995e-07, -0, 0]}
  ]
};


// ================= ingebouwde topologiecatalogus =================
// 2_2 is in de UI de gebruikelijke korte gebruikersnotatie; de standaard
// linknotatie voor de Hopf-link is 2^2_1. De 5_2-curve gebruikt een bekende
// Lissajous-representatie (3,2,7) met faseverschuivingen (0.7,0.2,0).
const BUILTIN_TOPOLOGIES = Object.freeze({
  ring:       {label:'ring 0₁', components:1},
  hopf:       {label:'Hopf-link 2₂', components:2},
  trefoil:    {label:'ideal trefoil 3₁ (Gilbert)', components:1},
  figure8:    {label:'figure-eight 4₁', components:1},
  cinquefoil: {label:'cinquefoil 5₁ = T(2,5)', components:1},
  twist52:    {label:'three-twist 5₂', components:1}
});

function topologyInfo(){
  if(P.knotKey || P.knotIdx>=0) return {label:'ideal catalogusknoop',components:1};
  return BUILTIN_TOPOLOGIES[P.topo] || BUILTIN_TOPOLOGIES.trefoil;
}
function topologyLabel(){
  if(P.knotKey) return `ideal knoop ${P.knotKey}`;
  if(P.knotIdx>=0) return `ideal knoop ${knotLabel(P.knotIdx)}`;
  return topologyInfo().label;
}
function topologyComponentCount(){ return topologyInfo().components || 1; }

// ================= parameters & state =================
const KAPPA_HE  = 9.9693e-8;      // m^2/s  (h/m4)
const GAMMA0_SST= 9.683619e-9;    // m^2/s  (2*pi*r_c*v_swirl, Canon v0.8.20; waarde ongewijzigd)
const RCORE_SST = 1.40897017e-15; // m, canonical SST core radius
const VSWIRL_SST= 1.09384563e6;   // m/s, canonical SST swirl speed
const OMEGA_CORE_SST = GAMMA0_SST/(2*Math.PI*RCORE_SST*RCORE_SST);
const C0        = 0.1395;         // gemeten discretisatieconstante Schwarz-schema
const DELTA     = {hol:0.5, vast:0.25, gp:0.615};
const P = {
  mode:'solo', topo:'trefoil', inter:'lia', core:'gp', med:'sst', qual:'hoog',
  Om:1.0, OmBundle:1.0, GaDemo:2.0, nQ:10, a:1.2415e-4, off:0.0, w:0.0, accExp:0.3, coRot:true,
  R0:0.07, zA:-0.42, zB:0.42, zSolo:0.0, Rcyl:0.25, Hcyl:0.5,
  knotIdx:-1, knotKey:'', compA:1, compB:1,
  ccwA:true, ccwB:false, mirrorB:false, vzA:0, vzB:0, lockVz:true,
  vis:'tube', tubeMat:'solid', showCenterline:false,
  revOm:false, revOmBundle:false, revGa:false, revOff:false, revW:false, revVzA:false, revVzB:false,
  ghostStewartson:false,
  taylorOsc:{enabled:false, amplitude:0.25, period:8},
  bgOmegaCoupling:false, showChiArrow:false, twistProxyEnabled:false,
  wAl:1, wBe:1, wGa:1, showTracers:true, showStreamlines:false, tracerCount:600, streamlineCount:28, particleSize:0.003, vortexOpacity:0.58, tracerSpawnMode:'column',
  linkDH:false, linkVolumeRef:2*Math.PI*0.25*0.25*0.5, linkRefR:0.25, linkRefH:0.5,
  mfTemp:'0', mfAlpha:0, mfAlphaP:0, vnZ:0, revVn:false,
  autoRelax:false, timeReverse:false, coreFlowLock:true,
  aPhys:RCORE_SST,
  centerLock:true, tracerWrapZ:true, vorticityLineColor:'#0F1A29',
  bundleEnabled:false, bundleProfile:'parallel', bundleSplay:0.45, bundleRadiusFrac:0.72, bundleVisualLines:61, bundleFlowCoupling:false,
  dvSeparatrix:true, dvColumn:true, dvCaps:true, dvStewartson:true, dvOpacity:1.0
};
function zMin(){return -P.Hcyl;}
function zMax(){return  P.Hcyl;}
function cylinderHeight(){return 2*P.Hcyl;}
function cylinderVolume(){return 2*Math.PI*P.Rcyl*P.Rcyl*P.Hcyl;}
function signedMag(x){return Math.abs(x);}
function applySigned(rev,mag){return rev?-mag:mag;}
function updateHeaderTitle(){
  const d=(2*P.Rcyl*100).toFixed(0);
  document.getElementById('hTitle').innerHTML=
    `SUPERFLUÏDE VORTEXLAB · cilinder ${cylinderHeight().toFixed(2)} m hoog (z = ±${P.Hcyl.toFixed(2)} m) × Ø${d} cm · Ω_wall = <span id="hOm">${P.Om.toFixed(2)}</span> rad·s⁻¹`;
}
const Flags = {alpha:false, beta:false, gamma:false, sep:false};
const EXPLAIN = {
  alpha:{title:'α C(K) — geometrische kruisingscomplexiteit', cls:'on-alpha', color:'#FF6E6E',
    text:'C(K) is de ACN/Gauss-|integraal|-descriptor van de actuele polygonale centerline; dit is geen afstotingskracht of reconnectiebarrière.'},
  beta:{title:'β L̂(K) — genormaliseerde centerlinelengte', cls:'on-beta', color:'#FFAE45',
    text:'L̂=L/L₀ vergelijkt de actuele centerlinelengte met de startlengte; de gele wireframe is alleen een visuele overlay, geen gemodelleerde lijnspanning.'},
  gamma:{title:'γ Ĥ(K) — getekende heliciteitsdescriptor', cls:'on-gamma', color:'#A855F7',
    text:'Ĥ=Wr+2Lk is de centerline-heliciteitsdescriptor. De lineaire term is tekengevoelig en vormt zonder extra mechanisme geen stabiliteitsenergie.'},
  sep:{title:'∂V-overlay — domeingeometrie', cls:'on-sep', color:'#fff',
    text:'Taylor-kolom, eindcaps en Stewartson-zijlaag zijn visualisatielagen. ∂V is geen term in de geometrische score Ŝ.'}
};
function clamp(x,lo,hi){return Math.max(lo,Math.min(hi,x));}
function aSimActive(){return Math.max(P.a,A_SIM_EPS);}
function fmtLengthSI(m){
  if(!Number.isFinite(m))return '—';
  const a=Math.abs(m);if(a===0)return '0 m';
  if(a<1e-15)return (m*1e18).toFixed(3)+' am';
  if(a<1e-12)return (m*1e15).toFixed(3)+' fm';
  if(a<1e-9)return (m*1e12).toFixed(3)+' pm';
  if(a<1e-6)return (m*1e9).toFixed(3)+' nm';
  if(a<1e-3)return (m*1e6).toFixed(3)+' µm';
  if(a<1)return (m*1e3).toFixed(3)+' mm';
  return m.toFixed(4)+' m';
}
function parseLengthInput(str){
  const t=String(str||'').trim().toLowerCase().replace(',','.').replace(/μ/g,'µ');
  if(!t)return NaN;
  const m=t.match(/^([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?)\s*(am|fm|pm|nm|um|µm|mm|cm|m)?$/i);
  if(!m)return NaN;
  const value=Number(m[1]);if(!Number.isFinite(value))return NaN;
  const scale={am:1e-18,fm:1e-15,pm:1e-12,nm:1e-9,um:1e-6,'µm':1e-6,mm:1e-3,cm:1e-2,m:1}[m[2]||'m'];
  return value*scale;
}
function formatASimInputMm(a){
  const mm=a*1e3;
  return a>=1e-6?mm.toFixed(6).replace(/0+$/,'').replace(/\.$/,''):mm.toExponential(8);
}
function contactThresholdInfo(){
  const physical=3*Math.max(0,Number.isFinite(P.a)?P.a:0);
  const scale=Math.max(1e-9,Math.abs(P.Rcyl||0),Math.abs(P.Hcyl||0),Math.abs(P.R0||0));
  const numerical=CONTACT_ULP_FACTOR*Number.EPSILON*scale;
  return {physical,numerical,effective:Math.max(physical,numerical),floorActive:numerical>physical};
}
function buildDiagRecord(Wr,Lk,ACN,sA){
  const ct=contactThresholdInfo();
  return {t:tPhys,Wr,Lk,ACN,RA:sA.R,zA:sA.z,a:P.a,aSim:P.a,aPhys:P.aPhys,
    mfA:P.mfAlpha,mfAp:P.mfAlphaP,vn:P.vnZ,
    omegaCore:omegaCorePhysical(),omegaBundle:P.OmBundle,omegaWall:P.Om,
    bundleEnabled:P.bundleEnabled,bundleProfile:P.bundleProfile,bundleDensityMid:bundleDensityAtZ(0),
    contactThreshold:ct.effective,contactFloorActive:ct.floorActive};
}

// ================= SST vortexbundel research-track =================
function bundleQuantum(){
  if(P.med==='sst')return GAMMA0_SST;
  if(P.med==='he')return KAPPA_HE;
  return Math.max(1e-30,Math.abs(Gamma()));
}
function omegaCorePhysical(){
  if(P.med==='sst')return OMEGA_CORE_SST;
  const aPhys=Math.max(1e-30,Number.isFinite(P.aPhys)?Math.abs(P.aPhys):Math.abs(P.a));
  return Math.abs(Gamma())/(2*Math.PI*aPhys*aPhys);
}
function bundleScaleAtU(u){
  const q=clamp(Number(u)||0,0,1),s=clamp(Number(P.bundleSplay)||0,0,1.4);
  if(P.bundleProfile==='splay')return Math.max(0.15,1+s*(q-0.5));
  if(P.bundleProfile==='periodic')return 1+0.5*s*(1-Math.cos(2*Math.PI*q));
  return 1;
}
function bundleScaleExtrema(){
  let lo=Infinity,hi=0;
  for(let i=0;i<=128;i++){const l=bundleScaleAtU(i/128);lo=Math.min(lo,l);hi=Math.max(hi,l);}
  return {lo,hi};
}
function bundleUFromZ(z){return clamp((z-zMin())/Math.max(1e-12,cylinderHeight()),0,1);}
function bundleOmegaAtZ(z){
  if(!P.bundleEnabled)return 0;
  const lam=bundleScaleAtU(bundleUFromZ(z));
  return (P.revOmBundle?-1:1)*Math.abs(P.OmBundle)/Math.max(1e-12,lam*lam);
}
function bundleDensityAtZ(z){return 2*Math.abs(bundleOmegaAtZ(z))/bundleQuantum();}
function bundleReferenceRadius(){return clamp(P.bundleRadiusFrac,0.10,0.93)*P.Rcyl;}
function bundlePhysicalCountAtZ(z){
  const u=bundleUFromZ(z),ex=bundleScaleExtrema();
  const baseR=bundleReferenceRadius()/Math.max(ex.hi,1e-12);
  const r=baseR*bundleScaleAtU(u);
  return bundleDensityAtZ(z)*Math.PI*r*r;
}
function bundleVelocityAt(x,y,z){
  if(!P.bundleEnabled||!P.bundleFlowCoupling)return {ux:0,uy:0,uz:0,omega:0};
  const om=bundleOmegaAtZ(z);
  return {ux:-om*y,uy:om*x,uz:0,omega:om};
}
function bundleMaxOmega(){
  if(!P.bundleEnabled||!P.bundleFlowCoupling)return 0;
  let m=0;for(let i=0;i<=64;i++)m=Math.max(m,Math.abs(bundleOmegaAtZ(zMin()+cylinderHeight()*i/64)));
  return m;
}
function effectiveW(){
  // v7.1 (B1): w geldt uitsluitend in solo-modus, conform de docs. Voorheen
  // lekte P.w door naar botsing-modus (spookdrift na moduswissel).
  if(P.mode!=='solo') return 0;
  if(P.taylorOsc.enabled){
    const Omosc=2*Math.PI/Math.max(0.5,P.taylorOsc.period);
    return P.taylorOsc.amplitude*Omosc*Math.cos(Omosc*tPhys);
  }
  return P.w;
}
function carrierAxialDrift(carrier){
  // v7.1 (B1): per-drager v_z-drift geldt uitsluitend in botsing-modus.
  // Voorheen werkte een oude vzA-waarde ook in solo door (drift = w + vzA).
  if(P.mode==='solo') return 0;
  if(carrier==='A'||P.lockVz) return P.vzA;
  return P.vzB;
}
function fmtAxialMmPerS(x){
  const a=Math.abs(x);
  if(a===0)return '0 mm/s';
  if(a<0.001)return x.toExponential(2).replace('e-','·10⁻')+' mm/s';
  if(a<0.1)return x.toFixed(4).replace(/0+$/,'').replace(/\.$/,'')+' mm/s';
  if(a<10)return x.toFixed(3).replace(/0+$/,'').replace(/\.$/,'')+' mm/s';
  if(a<100)return x.toFixed(2).replace(/0+$/,'').replace(/\.$/,'')+' mm/s';
  return x.toFixed(1).replace(/\.0$/,'')+' mm/s';
}
// v7.2 (RP2): de eerdere Γ_sheet/Γ_rel-uitlezingen zijn volledig verwijderd —
// u_θ=-w/(2Ωr) is dimensieloos, dus Γ_sheet=2πr·u_θ had dimensie m en de
// subtractie Γ_sheet-Γ_bg (m minus m²/s) was niet gedefinieerd. Een proxy-label
// maakt een ongeldige bewerking niet geldig. Wat overblijft is uitsluitend de
// dimensieloze Stewartson/Rossby-proxy q_S, met getekende Ω (geen |Ω| meer,
// zodat het teken correct meedraait met omkering van de cilinderrotatie).
function stewartsonCirculation(w,rCap,Om){
  const r=Math.max(rCap,0.025);
  const OmS=Math.abs(Om)<1e-6?(Om<0?-1e-6:1e-6):Om;
  const qS=-w/(2*OmS*r);
  const gammaBg=2*Math.abs(Om)*Math.PI*r*r; // wel dimensioneel geldig (m²/s)
  return {qS,gammaBg,rCap:r};
}
function taylorColumnState(s,vz){
  const Ga=Math.abs(Gamma()), rBase=s.R*1.5+P.a*3;
  const zetaAbs=2*P.Om+Ga/(Math.PI*Math.max(s.R*s.R,P.a*P.a));
  const Lchar=Math.max(0.05,2*rBase);
  const zetaRel=zetaAbs-2*P.Om-vz/Lchar;
  const ratio=Math.abs(zetaAbs)/Math.max(1e-6,Math.abs(zetaRel));
  const rFoot=P.Rcyl*0.25;
  const rDyn=rBase*Math.sqrt(clamp(ratio,0.16,6.25));
  const rCap=Flags.sep?Math.max(rFoot,rDyn):rDyn;

  // De lokale separatrix blijft rond de drager begrensd door rCap.
  const zSepTop=Math.min(zMax(),s.z+rCap);
  const zSepBot=Math.max(zMin(),s.z-rCap);

  // De Taylor-kolom / tangent-cylinder visualisatie loopt langs de volledige
  // rotatie-as tussen de domein-eindvlakken. De axiale lengte is dus niet
  // begrensd door de radiale separatrixstraal.
  const zTop=zMax();
  const zBot=zMin();
  const hColumn=Math.max(0,cylinderHeight());
  return {rCap,zTop,zBot,zSepTop,zSepBot,hColumn,zetaRel,zetaAbs,rBase,rFoot};
}
const QUAL_N = {
  botsing:{laag:64, mid:96, hoog:128},
  solo:  {laag:96, mid:192, hoog:288}
};
const RING_N = 48;
const EVAL_BUDGET = 1.5e6;   // kernel-evals per frame

let Y=null, fils=[], ghostFil=null, tPhys=0, phi=0, bundlePhi=0, paused=false;
let flagged="", warned=false, lastUmax=1e-9;
let Wr0=null, L0=1;
let K1,K2,K3,K4,TT;
let effAcc=0, effAccSimSum=0, effAccRealSum=0;
let perfWarmupUntil=0;
function resetPerformanceMeasurement(warmupMs=900){
  effAcc=0;effAccSimSum=0;effAccRealSum=0;
  perfWarmupUntil=performance.now()+Math.max(0,warmupMs);
}
let stepDebt=0;   // deterministische stepper: afspeel-tijddebet in seconden
const hist=[];
let twistProxy=null;
let chiArrows=[];
let lastFrameVel=null;
let stabilityLast=null, stabilityFrame=0, autoRelaxFrame=0;
let stabilityThrottle=1, stabilityThrottleTarget=1;
let carrierAnchors=Object.create(null);
let coreCouplingBusy=false;
let coreFlowNotice='';

function Gamma(){
  if(P.med==='he')  return P.nQ*KAPPA_HE;
  if(P.med==='sst') return P.nQ*GAMMA0_SST;
  const g=P.GaDemo; const s=g<0?-1:1;
  const floor=P.coreFlowLock?1e-12:0.2;
  return s*Math.max(Math.abs(g),floor)*1e-3;
}
function kappaMedium(){
  if(P.med==='he')  return KAPPA_HE;
  if(P.med==='sst') return GAMMA0_SST;
  return null;
}

// ---- wederzijdse wrijving (v7) ----
// α, α′ voor He-II bij SVP, T90-schaal. Bron: Donnelly, "The Observed Properties
// of Liquid Helium at the Saturated Vapor Pressure", hfst. 11 Tabel 11.3
// (compilatie van Barenghi–Donnelly–Vinen, J. Low Temp. Phys. 52, 189 (1983)).
// Let op: α′ wisselt van teken tussen 2.06 en 2.08 K — dat is echt, geen typefout.
// Onder 1.30 K geeft de tabel geen waarden; gebruik daar 'aangepast'.
const MF_TABLE={
  '1.30':[0.034,0.01383],'1.35':[0.042,0.01543],'1.40':[0.051,0.01668],
  '1.45':[0.061,0.01746],'1.50':[0.072,0.01766],'1.55':[0.084,0.01721],
  '1.60':[0.097,0.01608],'1.65':[0.111,0.01437],'1.70':[0.126,0.01225],
  '1.75':[0.142,0.01003],'1.80':[0.160,0.008211],'1.85':[0.181,0.007438],
  '1.90':[0.206,0.008340],'2.00':[0.279,0.01198],'2.02':[0.302,0.01097],
  '2.04':[0.330,0.008318],'2.06':[0.366,0.003018],'2.08':[0.414,-0.006690],
  '2.10':[0.481,-0.02412]
};
function applyMfTemp(key){
  P.mfTemp=key;
  if(key==='0'){P.mfAlpha=0;P.mfAlphaP=0;}
  else if(key!=='custom'&&MF_TABLE[key]){P.mfAlpha=MF_TABLE[key][0];P.mfAlphaP=MF_TABLE[key][1];}
}
function mfActive(){return P.mfAlpha!==0||P.mfAlphaP!==0;}
// Schwarz-wrijvingstransformatie per knooppunt (puur, unit-getest):
// ṡ = v_s + α ŝ'×(v_n−v_s) − α' ŝ'×[ŝ'×(v_n−v_s)], met v_s de totale lokale
// superfluïde snelheid en v_n de opgelegde normale-vloeistofsnelheid.
function mfTransform(ux,uy,uz,tx,ty,tz,vnx,vny,vnz,al,alp,OUT3){
  const tl=Math.sqrt(tx*tx+ty*ty+tz*tz);
  if(!(tl>1e-30)){OUT3[0]=ux;OUT3[1]=uy;OUT3[2]=uz;return;}
  tx/=tl;ty/=tl;tz/=tl;
  const rx=vnx-ux,ry=vny-uy,rz=vnz-uz;                       // v_ns
  const c1x=ty*rz-tz*ry,c1y=tz*rx-tx*rz,c1z=tx*ry-ty*rx;     // ŝ'×v_ns
  const c2x=ty*c1z-tz*c1y,c2y=tz*c1x-tx*c1z,c2z=tx*c1y-ty*c1x; // ŝ'×(ŝ'×v_ns)
  OUT3[0]=ux+al*c1x-alp*c2x;
  OUT3[1]=uy+al*c1y-alp*c2y;
  OUT3[2]=uz+al*c1z-alp*c2z;
}
const MF_TMP3=new Float64Array(3);

function rankineGammaTarget(){
  return 2*Math.PI*P.a*P.a*Math.abs(P.Om);
}
function coreFlowRatio(){
  const om=Math.abs(P.Om);
  if(om<=1e-12)return NaN; // χ_Ω is mathematically undefined at Ω=0
  const den=2*Math.PI*P.a*P.a*om;
  return Math.abs(Gamma())/den;
}
function dimensionlessDiagnostics(sA,vzRel){
  const om=Math.abs(P.Om);
  return {
    chiOmega:om>1e-9?coreFlowRatio():NaN,
    roZ:om>1e-9?Math.abs(vzRel)/(2*om*P.Rcyl):NaN,
    aOverR:P.a/Math.max(sA&&sA.R||0,1e-12),
  };
}
function relativeCarrierOrientationSign(){
  return (P.ccwA?1:-1)*(P.ccwB?1:-1);
}
function syncCoreFlowCoupling(driver='geometry'){
  if(!P.coreFlowLock||coreCouplingBusy)return;
  coreCouplingBusy=true;
  try{
    if(Math.abs(P.Om)<1e-12){
      P.Om=P.revOm?-1:1;
    }
    const omega=Math.max(1e-12,Math.abs(P.Om));
    const q=kappaMedium();
    if(driver==='gamma'){
      const gamma=Math.max(1e-30,Math.abs(Gamma()));
      const aWanted=Math.sqrt(gamma/(2*Math.PI*omega));
      P.a=clamp(aWanted,A_SIM_INPUT_FLOOR,Math.max(A_SIM_INPUT_FLOOR,coreRadiusMax||1));
      // Wanneer de geometrische limiet ingrijpt, herschaal Γ terug naar een
      // exact toegelaten Rankine-relatie.
      if(Math.abs(P.a-aWanted)>1e-15)driver='geometry';
    }
    if(driver!=='gamma'){
      const target=rankineGammaTarget();
      if(q){
        P.nQ=Math.max(1,Math.min(1e9,Math.round(target/q)));
        P.a=clamp(Math.sqrt((P.nQ*q)/(2*Math.PI*omega)),A_SIM_INPUT_FLOOR,Math.max(A_SIM_INPUT_FLOOR,coreRadiusMax||1));
      }else{
        const sign=P.Om<0?-1:1;
        P.GaDemo=sign*Math.max(1e-12,target/1e-3);
        P.revGa=P.GaDemo<0;
      }
    }
  }finally{
    coreCouplingBusy=false;
  }
  updateCoreFlowReadout();
}
function updateCoreFlowReadout(){
  const panel=document.getElementById('coreFlowLinkPanel');
  const out=document.getElementById('coreFlowReadout');
  if(!panel||!out)return;
  panel.classList.toggle('active',P.coreFlowLock);
  const gamma=Math.abs(Gamma());
  const uCore=gamma/(2*Math.PI*Math.max(P.a,1e-30));
  const omCore=gamma/(2*Math.PI*Math.max(P.a*P.a,1e-30));
  if(!P.coreFlowLock){
    const notice=coreFlowNotice?` · ${coreFlowNotice}`:'';
    out.textContent=`Vrij · Γ=${fmtGamma(gamma)} m²/s · a=${fmtLengthSI(P.a)} · u_core≈${fmtSpeed(uCore)} · Ω_core≈${omCore.toExponential(3)} s⁻¹${notice}`;
    return;
  }
  const ratio=coreFlowRatio();
  const quant=P.med==='sst'?` · n=${P.nQ.toLocaleString('nl-NL')} Γ₀`:P.med==='he'?` · n=${P.nQ.toLocaleString('nl-NL')} κ`:'';
  const canon=P.med==='sst'?` · canon n=1: r_c=${RCORE_SST.toExponential(3)} m, Ω_core=${OMEGA_CORE_SST.toExponential(3)} s⁻¹`:'';
  const ratioText=Number.isFinite(ratio)?ratio.toFixed(5):'—';
  out.textContent=`GEKOPPELD · Γ=${fmtGamma(gamma)} m²/s${quant} · a=${fmtLengthSI(P.a)} · Ω=${Math.abs(P.Om).toFixed(3)} s⁻¹ · |Γ|/(2πa²|Ω|)=${ratioText}${canon}`;
}
function applySSTSimilarityPreset(){
  // Zichtbare similarity-scale: behoud de canonieke kwantisatie Γ=nΓ₀ en
  // de Rankine-verhouding Γ=2πa²Ω, zonder de fysische femtometerkern in
  // een meterschaal-visualisatie te pretenderen te resolven.
  P.med='sst';
  P.core='gp';
  P.coreFlowLock=true;
  P.Om=1.0; P.revOm=false;
  P.nQ=1;
  P.aPhys=RCORE_SST;
  P.coRot=true;
  P.bgOmegaCoupling=false;
  P.bundleEnabled=false;
  P.bundleFlowCoupling=false;
  // Behoud eerst de canonieke enkelvoudige circulatie Γ₀ en leid de
  // zichtbare similarity-radius af uit Γ₀=2πa²Ω.
  syncCoreFlowCoupling('gamma');
}

function applySSTBundlePreset(){
  P.mode='solo';P.topo='ring';P.inter='lia';P.qual='hoog';DELTA.gp=0.615;
  P.knotIdx=-1;P.knotKey='';P.compA=1;P.compB=1;
  P.med='sst';P.core='gp';P.coreFlowLock=false;P.aPhys=RCORE_SST;
  P.Om=0;P.revOm=false;P.coRot=false;P.bgOmegaCoupling=false;
  P.OmBundle=1;P.revOmBundle=false;P.bundleEnabled=true;P.bundleProfile='parallel';
  P.bundleSplay=0.45;P.bundleRadiusFrac=0.72;P.bundleVisualLines=61;P.bundleFlowCoupling=true;
  P.nQ=1;P.a=1.2415e-4;P.R0=0.05;P.zSolo=0;P.off=0;P.w=0;P.vzA=0;P.vzB=0;P.lockVz=true;
  P.mfTemp='0';P.mfAlpha=0;P.mfAlphaP=0;P.vnZ=0;P.autoRelax=false;P.timeReverse=false;
  P.centerLock=true;P.tracerWrapZ=false;P.tracerSpawnMode='column';
  rebuildLattice();syncUi();updateSubtitle();
}
function applyDefaultStartup(){
  // Requested baseline: one built-in ideal trefoil, SST medium, GP/NLSE core and local induction.
  P.mode='solo';P.topo='trefoil';P.inter='lia';P.qual='hoog';DELTA.gp=0.615;
  P.knotIdx=-1;P.knotKey='';P.compA=1;P.compB=1;
  P.R0=0.07;P.zSolo=0;P.off=0;P.w=0;P.vzA=0;P.vzB=0;P.lockVz=true;
  P.timeReverse=false;P.autoRelax=false;P.centerLock=true;
  P.tracerWrapZ=true;P.tracerSpawnMode='column';
  P.ccwA=true;P.ccwB=false;P.mirrorB=false;
  applySSTSimilarityPreset();
  P.nQ=10;
  syncCoreFlowCoupling('gamma');
  syncUi();updateSubtitle();
}
function applyFrictionPreset(){
  // Demonstratie wederzijdse wrijving: solo He-II-ring bij 1.90 K in rustende
  // normale vloeistof. Verwacht: Ṙ = −αU (krimp), translatie ×(1−α′), en de
  // HUD-rij "Ṙ meting / α(v_n∥−U_K)" als live orthodoxietest.
  P.mode='solo';P.topo='ring';P.inter='lia';P.qual='hoog';
  P.knotIdx=-1;P.knotKey='';P.compA=1;P.compB=1;
  P.med='he';P.core='gp';P.coreFlowLock=true;DELTA.gp=0.615;
  P.R0=0.07;P.zSolo=0;P.off=0;P.w=0;P.vzA=0;P.vzB=0;P.lockVz=true;
  P.timeReverse=false;P.autoRelax=false;P.centerLock=true;
  P.tracerWrapZ=true;
  P.nQ=10;
  applyMfTemp('1.90');P.vnZ=0;P.revVn=false;
  P.accExp=3; // fysische krimp is µm/s-schaal; 10³× maakt hem zichtbaar
  syncCoreFlowCoupling('gamma');
}
function acc(){ return Math.pow(10,P.accExp); }
const RING_QUAL={laag:48, mid:96, hoog:144};
function carrierN(){
  if(isRingTopo()) return RING_QUAL[P.qual];
  return QUAL_N[P.mode][P.qual];
}
function activeCoeffs(forCarrier){
  const ci=forCarrier==='B'?P.compB-1:P.compA-1;
  if(P.knotKey && window.IDEAL_KNOT_DB && IDEAL_KNOT_DB[P.knotKey]){
    const k=IDEAL_KNOT_DB[P.knotKey];
    const comp=k.components[Math.min(ci,k.components.length-1)];
    return comp.coeffs;
  }
  if(P.knotIdx>=0 && window.IDEAL_KNOTS && IDEAL_KNOTS[P.knotIdx]){
    const e=IDEAL_KNOTS[P.knotIdx];
    return e.coeffs||(e.components&&e.components[0])||IDEAL_TREFOIL_3_1_1.coeffs;
  }
  return IDEAL_TREFOIL_3_1_1.coeffs;
}
function activeKnotEntry(){
  if(P.knotKey && window.IDEAL_KNOT_DB) return IDEAL_KNOT_DB[P.knotKey];
  if(P.knotIdx>=0 && window.IDEAL_KNOTS) return IDEAL_KNOTS[P.knotIdx];
  return null;
}
function carrierWantDir(which){
  // CCW gezien vanaf +z => drager beweegt +z; CW => -z. Autoaim dwingt dit af (ook voor knopen).
  const ccw=which==='B'?P.ccwB:P.ccwA;
  return ccw?+1:-1;
}
function carrierOffsetX(which){
  if(P.mode!=='botsing') return P.off;   // solo: volledige topologie krijgt offset
  if(which==='B') return P.mirrorB?-P.off:P.off;
  return 0;
}

function isRingTopo(){
  return P.topo==='ring'&&P.knotIdx<0&&!P.knotKey;
}
function kelvinSpeed(R){
  const Ga=Math.abs(Gamma());
  return Ga/(4*Math.PI*Math.max(R,1e-6))*(Math.log(8*R/P.a)-DELTA[P.core]);
}
function chiHatFromFilament(f){
  if(isRingTopo())return null;
  const N=f.N,o=f.off;
  const st=carrierStats(f);
  let maxR=0,mx=0,my=0;
  for(let k=0;k<N;k++){
    const rx=Y[o+3*k]-st.cx,ry=Y[o+3*k+1]-st.cy;
    const r=Math.hypot(rx,ry);
    if(r>maxR){maxR=r;mx=rx;my=ry;}
  }
  if(maxR<1e-9)return {x:1,y:0,phi:0};
  return {x:mx/maxR,y:my/maxR,phi:Math.atan2(my,mx)*180/Math.PI};
}
function bodyFrameState(f,V){
  const st=carrierStats(f);
  const N=f.N,o=f.off;
  let num=0,den=0;
  for(let k=0;k<N;k++){
    const rx=Y[o+3*k]-st.cx,ry=Y[o+3*k+1]-st.cy;
    const vx=V[o+3*k],vy=V[o+3*k+1];
    num+=rx*vy-ry*vx;
    den+=rx*rx+ry*ry;
  }
  const omegaZ=den>1e-12?num/den:0;
  const chi=chiHatFromFilament(f);
  return {omegaZ,chi,cx:st.cx,cy:st.cy,cz:st.z,R:st.R};
}
function initTwistProxy(){
  twistProxy=fils.map(f=>new Float64Array(f.N));
}
function twistProxySum(){
  // v7.2 (RP4): booglengte-gewogen gemiddelde ⟨∫u·t̂ dt⟩_L in meters. De oude
  // kale knooppuntsom schaalde ∝N (zelfde knoop, dubbele resolutie → dubbele
  // waarde) en deelde bovendien door 2π — een restant van de twist-claim.
  if(!twistProxy||!Y)return 0;
  let num=0,den=0;
  fils.forEach((f,fi)=>{
    if(f.ghost)return;
    const tw=twistProxy[fi];if(!tw)return;
    const N=f.N,o=f.off;
    for(let k=0;k<N;k++){const k2=(k+1)%N;
      const l=Math.hypot(Y[o+3*k2]-Y[o+3*k],Y[o+3*k2+1]-Y[o+3*k+1],Y[o+3*k2+2]-Y[o+3*k+2]);
      num+=l*tw[k];den+=l;}
  });
  return den>0?num/den:0;
}
function updateTwistProxy(dt,V){
  if(!P.twistProxyEnabled||!twistProxy||!Y)return;
  fils.forEach((f,fi)=>{
    const N=f.N,o=f.off,tw=twistProxy[fi];
    for(let k=0;k<N;k++){
      const k2=(k+1)%N;
      const tx=Y[o+3*k2]-Y[o+3*k],ty=Y[o+3*k2+1]-Y[o+3*k+1],tz=Y[o+3*k2+2]-Y[o+3*k+2];
      const tl=Math.hypot(tx,ty,tz)||1;
      const ux=V[o+3*k],uy=V[o+3*k+1],uz=V[o+3*k+2];
      tw[k]+=dt*(ux*tx/tl+uy*ty/tl+uz*tz/tl);
    }
  });
}
function fmtOmegaBody(om){
  const deg=om*180/Math.PI;
  if(Math.abs(deg)>=0.01)return deg.toFixed(2)+'°/s';
  return (om*1000).toFixed(2)+' mrad/s';
}
function allFils(){return ghostFil?[...fils,ghostFil]:fils;}
// v7.2 (RP2): de ghost is dynamisch krachteloos (v7.1) én numeriek onzichtbaar —
// hij telt niet mee in ℓ_min (dtCFL) of het evaluatiebudget, zodat ghost
// aan/uit de stapreeks en truncatiefout niet meer kan veranderen.
function dynamicFils(){return fils.filter(f=>!f.ghost);}
function filamentGamma(f){return f.ghost?f.gammaVal:Gamma();}
function carrierFilaments(which){ return fils.filter(f=>(f.carrier||'A')===which); }
function firstCarrierFilament(which){ return carrierFilaments(which)[0]||null; }
function carrierGroupStats(which){
  const fs=carrierFilaments(which);
  if(!fs.length)return null;
  let cx=0,cy=0,cz=0,n=0;
  for(const f of fs){for(let k=0;k<f.N;k++){
    cx+=Y[f.off+3*k];cy+=Y[f.off+3*k+1];cz+=Y[f.off+3*k+2];n++;
  }}
  cx/=n;cy/=n;cz/=n;
  let R=0,rWall=0;
  for(const f of fs){for(let k=0;k<f.N;k++){
    const x=Y[f.off+3*k],y=Y[f.off+3*k+1];
    R+=Math.hypot(x-cx,y-cy);
    rWall=Math.max(rWall,Math.hypot(x,y));
  }}
  return {R:R/n,z:cz,rWall,cx,cy,components:fs.length};
}

function translateCarrier(which,dx,dy,dz){
  for(const f of carrierFilaments(which))for(let k=0;k<f.N;k++){
    const i=f.off+3*k;Y[i]+=dx;Y[i+1]+=dy;Y[i+2]+=dz;
  }
}
function captureCarrierAnchors(){
  carrierAnchors=Object.create(null);
  for(const which of ['A','B']){
    const st=carrierGroupStats(which);
    if(st)carrierAnchors[which]={x:st.cx,y:st.cy,z:st.z};
  }
}
function centerSoloCarrierAtOrigin(){
  if(P.mode!=='solo')return;
  const st=carrierGroupStats('A');
  if(st)translateCarrier('A',-st.cx,-st.cy,-st.z);
}
function enforceCenterLock(){
  // Alleen in solo: in botsingsmodus zou het vastpinnen van beide dragers
  // de nadering (en dus de hele botsing) onderdrukken.
  if(!P.centerLock||P.mode!=='solo'||!Y)return;
  for(const which of Object.keys(carrierAnchors)){
    const st=carrierGroupStats(which),a=carrierAnchors[which];
    if(st&&a)translateCarrier(which,a.x-st.cx,a.y-st.cy,a.z-st.z);
  }
}
function sampleFourierKnot(coeffs,n){
  const x=new Float64Array(3*n);
  for(let k=0;k<n;k++){
    const t=2*Math.PI*k/n; let px=0,py=0,pz=0;
    for(const c of coeffs){
      const ct=Math.cos(c.I*t), st=Math.sin(c.I*t);
      px+=ct*c.A[0]+st*c.B[0]; py+=ct*c.A[1]+st*c.B[1]; pz+=ct*c.A[2]+st*c.B[2];
    }
    x[3*k]=px;x[3*k+1]=py;x[3*k+2]=pz;
  }
  return x;
}
function sampleBuiltinRaw(topo,N,component=0,which='A'){
  if(topo==='trefoil') return sampleFourierKnot(activeCoeffs(which),N);
  const x=new Float64Array(3*N);
  for(let k=0;k<N;k++){
    const t=2*Math.PI*k/N;
    let px=0,py=0,pz=0;
    if(topo==='ring'){
      px=Math.cos(t);py=Math.sin(t);pz=0;
    }else if(topo==='hopf'){
      // Twee geometrische cirkels met linking number |Lk|=1.
      if(component===0){px=Math.cos(t)-0.5;py=Math.sin(t);pz=0;}
      else{px=0.5+Math.cos(t);py=0;pz=Math.sin(t);}
    }else if(topo==='figure8'){
      px=(2+Math.cos(2*t))*Math.cos(3*t);
      py=(2+Math.cos(2*t))*Math.sin(3*t);
      pz=Math.sin(4*t);
    }else if(topo==='cinquefoil'){
      // T(2,5), een 5_1-torusknoop.
      px=(2+0.72*Math.cos(5*t))*Math.cos(2*t);
      py=(2+0.72*Math.cos(5*t))*Math.sin(2*t);
      pz=0.72*Math.sin(5*t);
    }else if(topo==='twist52'){
      // Lissajous-representatie van de three-twist knot 5_2.
      px=Math.cos(3*t+0.7);
      py=Math.cos(2*t+0.2);
      pz=Math.cos(7*t);
    }else{
      px=Math.cos(t);py=Math.sin(t);pz=0;
    }
    x[3*k]=px;x[3*k+1]=py;x[3*k+2]=pz;
  }
  return x;
}
function topologyRawComponents(N,which){
  if(P.knotKey||P.knotIdx>=0) return [sampleFourierKnot(activeCoeffs(which),N)];
  const nc=topologyComponentCount();
  const out=[];for(let c=0;c<nc;c++)out.push(sampleBuiltinRaw(P.topo,N,c,which));
  return out;
}
function reverseTraversal(x,N){
  const y=new Float64Array(3*N);
  for(let k=0;k<N;k++){const s=N-1-k;
    y[3*k]=x[3*s];y[3*k+1]=x[3*s+1];y[3*k+2]=x[3*s+2];}
  return y;
}
function signedAreaXY(x,N){
  let A=0;for(let k=0;k<N;k++){const k2=(k+1)%N;
    A+=x[3*k]*x[3*k2+1]-x[3*k2]*x[3*k+1];}
  return 0.5*A;
}
function makeCarrierComponents(N,z0,cx,wantDir,which){
  let raws=topologyRawComponents(N,which||'A');
  let c0x=0,c0y=0,c0z=0,count=0;
  raws.forEach(raw=>{for(let k=0;k<N;k++){
    c0x+=raw[3*k];c0y+=raw[3*k+1];c0z+=raw[3*k+2];count++;
  }});
  c0x/=count;c0y/=count;c0z/=count;
  let rMax=0;
  raws.forEach(raw=>{for(let k=0;k<N;k++){
    rMax=Math.max(rMax,Math.hypot(raw[3*k]-c0x,raw[3*k+1]-c0y));
  }});
  const sc=P.R0/Math.max(rMax,1e-12);
  let placed=raws.map(raw=>{
    const out=new Float64Array(3*N);
    for(let k=0;k<N;k++){
      out[3*k]=cx+(raw[3*k]-c0x)*sc;
      out[3*k+1]=(raw[3*k+1]-c0y)*sc;
      out[3*k+2]=z0+(raw[3*k+2]-c0z)*sc;
    }
    return out;
  });
  // Werkelijke spiegeling van drager B: reflecteer de geometrie rond het
  // verticale vlak door haar eigen centrum. Dit verandert de chiraliteit,
  // in tegenstelling tot alleen het teken van de laterale offset wijzigen.
  if(which==='B' && P.mirrorB){
    placed=placed.map(curve=>{
      const out=new Float64Array(curve.length);
      for(let k=0;k<N;k++){
        out[3*k]=2*cx-curve[3*k];
        out[3*k+1]=curve[3*k+1];
        out[3*k+2]=curve[3*k+2];
      }
      return out;
    });
  }

  // Auto-aim op basis van de werkelijk door Biot--Savart geïnduceerde
  // centroid-snelheid van de volledige topologie. Voor niet-planaire knopen
  // is het teken van de geprojecteerde xy-oppervlakte geen betrouwbare
  // voorspeller van de translatierichting.
  const vzSelf=carrierMeanSelfVz(placed);
  if(Math.abs(vzSelf)>1e-12 && vzSelf*wantDir<0)
    placed=placed.map(curve=>reverseTraversal(curve,N));
  else if(Math.abs(vzSelf)<=1e-12){
    const orient=signedAreaXY(placed[0],N);
    if(Math.abs(orient)>1e-12 && orient*wantDir<0)
      placed=placed.map(curve=>reverseTraversal(curve,N));
  }
  return placed;
}

// ================= fysica: Schwarz-splitsing =================
// snelheid van één losstaand filament (voor auto-richting)
function velocitySingle(X,N,V){
  const fils1=[{off:0,N}]; velocityCore(X,fils1,V,false);
}
// hoofdroutine: Y = alle punten, fils = [{off,N}], OUT zelfde lengte als Y
function velocityCore(Yv,fl,OUT,liaOnly,options={}){
  const includeExternal=options.includeExternal!==false;
  // wrijving alleen in de echte dynamica: niet in de includeExternal:false
  // diagnostiekaanroepen (zelfgeïnduceerde vz voor richtbepaling).
  const bundleOn=includeExternal&&P.bundleEnabled&&P.bundleFlowCoupling;
  const mfOn=includeExternal&&options.mutualFriction!==false&&mfActive()&&!bundleOn;
  const mfRot=P.bgOmegaCoupling&&!P.coRot;
  const a=P.a, a2=a*a, eD=Math.exp(DELTA[P.core]);
  // segmentdata per filament
  const mids=[],dls=[];
  for(const f of fl){
    const N=f.N, o=f.off, mid=new Float64Array(3*N), dl=new Float64Array(3*N);
    for(let k=0;k<N;k++){const k2=(k+1)%N;
      for(let d=0;d<3;d++){
        mid[3*k+d]=0.5*(Yv[o+3*k+d]+Yv[o+3*k2+d]);
        dl[3*k+d]=Yv[o+3*k2+d]-Yv[o+3*k+d];}}
    mids.push(mid);dls.push(dl);
  }
  let umax=0;
  for(let ft=0;ft<fl.length;ft++){
    if(fl[ft].ghost){
      // v7.1 (B3): de Stewartson-ghostring is puur visueel — hij beweegt niet
      // zelf (positie wordt door syncGhostRing gepind) en draagt hieronder ook
      // niet bij als Biot-Savart-bron. Zijn gammaVal is dimensioneel niet
      // gesloten en mag de dynamica niet raken.
      const N=fl[ft].N,o=fl[ft].off;
      for(let i=0;i<N;i++){OUT[o+3*i]=0;OUT[o+3*i+1]=0;OUT[o+3*i+2]=0;}
      continue;
    }
    const Ga=filamentGamma(fl[ft]), pref=Ga/(4*Math.PI);
    const N=fl[ft].N, o=fl[ft].off, dlt=dls[ft];
    for(let i=0;i<N;i++){
      const im=(i-1+N)%N, ip=i;
      const px=Yv[o+3*i],py=Yv[o+3*i+1],pz=Yv[o+3*i+2];
      const dmx=dlt[3*im],dmy=dlt[3*im+1],dmz=dlt[3*im+2];
      const dpx=dlt[3*ip],dpy=dlt[3*ip+1],dpz=dlt[3*ip+2];
      const lm=Math.sqrt(dmx*dmx+dmy*dmy+dmz*dmz), lp=Math.sqrt(dpx*dpx+dpy*dpy+dpz*dpz);
      const cxv=dmy*dpz-dmz*dpy, cyv=dmz*dpx-dmx*dpz, czv=dmx*dpy-dmy*dpx;
      const lf=pref*(Math.log(2*Math.sqrt(lm*lp)/(eD*a))+C0)*2/(lm*lp*(lm+lp));
      let ux=lf*cxv, uy=lf*cyv, uz=lf*czv;
      if(includeExternal){
        const carrier=fl[ft].carrier||'A';
        const zBias=effectiveW()+carrierAxialDrift(carrier);
        uz+=zBias;
        if(P.bgOmegaCoupling&&!P.coRot&&!fl[ft].ghost){
          ux+=-P.Om*py;
          uy+= P.Om*px;
        }
        if(bundleOn){
          const ub=bundleVelocityAt(px,py,pz);
          ux+=ub.ux;uy+=ub.uy;
        }
      }
      if(!liaOnly){
        for(let fs=0;fs<fl.length;fs++){
          if(fl[fs].ghost)continue; // v7.1 (B3): ghost is geen bron
          const M=fl[fs].N, mid=mids[fs], dl=dls[fs];
          const prefSource=filamentGamma(fl[fs])/(4*Math.PI);
          const reg=(fs===ft)?0:a2;   // eigen filament: kale kern-vrije kernel; kruisterm: gladgestreken
          for(let j=0;j<M;j++){
            if(fs===ft && (j===im||j===ip)) continue;
            const rx=px-mid[3*j],ry=py-mid[3*j+1],rz=pz-mid[3*j+2];
            const r2=rx*rx+ry*ry+rz*rz+reg;
            const inv=prefSource/(r2*Math.sqrt(r2));
            ux+=(dl[3*j+1]*rz-dl[3*j+2]*ry)*inv;
            uy+=(dl[3*j+2]*rx-dl[3*j]*rz)*inv;
            uz+=(dl[3*j]*ry-dl[3*j+1]*rx)*inv;
          }
        }
      }
      if(mfOn&&!fl[ft].ghost){
        // v_n: opgelegde uniforme axiale normale stroming; in het lab-frame met
        // achtergrond-Ω-koppeling roteert de normale component mee (Ω×r),
        // zodat de azimutale v_ns-bijdrage van de vaste-lichaamsrotatie wegvalt.
        let vnx=0,vny=0;const vnz=P.vnZ;
        if(mfRot){vnx=-P.Om*py;vny=P.Om*px;}
        mfTransform(ux,uy,uz,dmx+dpx,dmy+dpy,dmz+dpz,vnx,vny,vnz,P.mfAlpha,P.mfAlphaP,MF_TMP3);
        ux=MF_TMP3[0];uy=MF_TMP3[1];uz=MF_TMP3[2];
      }
      OUT[o+3*i]=ux;OUT[o+3*i+1]=uy;OUT[o+3*i+2]=uz;
      const um=ux*ux+uy*uy+uz*uz;if(um>umax)umax=um;
    }
  }
  return Math.sqrt(umax);
}
function carrierMeanSelfVz(components){
  if(!components||!components.length)return 0;
  const N=components[0].length/3;
  const totalPts=components.reduce((n,c)=>n+c.length/3,0);
  const tmpY=new Float64Array(3*totalPts), tmpF=[];
  let off=0;
  components.forEach((curve,component)=>{
    tmpY.set(curve,off);
    tmpF.push({off,N:curve.length/3,carrier:'A',component});
    off+=curve.length;
  });
  const tmpV=new Float64Array(tmpY.length);
  velocityCore(tmpY,tmpF,tmpV,false,{includeExternal:false});
  let vz=0;
  for(let i=2;i<tmpV.length;i+=3)vz+=tmpV[i];
  return vz/Math.max(1,totalPts);
}
function velAll(Yv,OUT){
  const lia=(P.inter==='lia');
  return velocityCore(Yv,allFils(),OUT,lia);
}
function wrapFilamentCarriersZ(){
  if(!P.tracerWrapZ||P.centerLock||!Y||!fils.length)return;
  const lo=zMin(),hi=zMax(),span=hi-lo;
  if(!(span>1e-12))return;
  const carriers=[...new Set(fils.filter(f=>!f.ghost).map(f=>f.carrier||'A'))];
  for(const carrier of carriers){
    const group=fils.filter(f=>!f.ghost&&(f.carrier||'A')===carrier);
    let zc=0,count=0;
    for(const f of group)for(let k=0;k<f.N;k++){zc+=Y[f.off+3*k+2];count++;}
    if(!count)continue;
    zc/=count;
    if(zc<lo||zc>=hi){
      const wrapped=lo+(((zc-lo)%span)+span)%span;
      const dz=wrapped-zc;
      for(const f of group)for(let k=0;k<f.N;k++)Y[f.off+3*k+2]+=dz;
    }
  }
}
function rk4Step(dt){
  const n=Y.length;
  const u1=velAll(Y,K1);
  for(let i=0;i<n;i++)TT[i]=Y[i]+0.5*dt*K1[i];
  const u2=velAll(TT,K2);
  for(let i=0;i<n;i++)TT[i]=Y[i]+0.5*dt*K2[i];
  const u3=velAll(TT,K3);
  for(let i=0;i<n;i++)TT[i]=Y[i]+dt*K3[i];
  const u4=velAll(TT,K4);
  for(let i=0;i<n;i++)Y[i]+=dt/6*(K1[i]+2*K2[i]+2*K3[i]+K4[i]);
  wrapFilamentCarriersZ();
  enforceCenterLock();
  constrainGhostRing();
  if(P.twistProxyEnabled) updateTwistProxy(dt,K4);
  // v7.1 (B7): verplaatsingslimiet in dtCFL gebruikt de snelste van alle vier
  // RK4-stages; voorheen alleen K1, waardoor snelle tussenstadia bij nadering
  // de tijdstap konden onderschatten.
  return Math.max(u1,u2,u3,u4);
}
function dtCFL(){
  const lm=lminAll();
  const nu=(Math.abs(Gamma())/(4*Math.PI))*(Math.log(2*lm/(Math.exp(DELTA[P.core])*P.a))+C0);
  const om=Math.max(1e-12,Math.abs(nu)*Math.pow(Math.PI/lm,2));
  let dt=0.5/om;
  dt=Math.min(dt, 0.25*lm/Math.max(1e-12,lastUmax));
  if(P.bgOmegaCoupling&&Math.abs(P.Om)>1e-9)dt=Math.min(dt,0.2/Math.abs(P.Om));
  const ob=bundleMaxOmega();
  if(ob>1e-9)dt=Math.min(dt,0.2/ob);
  return dt;
}
function evalsPerStep(){
  let tot=0;for(const f of dynamicFils())tot+=f.N;
  const lia=(P.inter==='lia');
  const n=dynamicFils().length;
  return lia? 4*tot*8 : 4*tot*tot;
}

function ghostRingPts(N,rCap,cx,cy,cz){
  const x=new Float64Array(3*N);
  for(let k=0;k<N;k++){
    const th=2*Math.PI*k/N;
    x[3*k]=cx+rCap*Math.cos(th);x[3*k+1]=cy+rCap*Math.sin(th);x[3*k+2]=cz;}
  return x;
}
function lminAll(){
  let m=1e9;
  for(const f of dynamicFils()){const N=f.N,o=f.off;
    for(let k=0;k<N;k++){const k2=(k+1)%N;
      const d=Math.hypot(Y[o+3*k2]-Y[o+3*k],Y[o+3*k2+1]-Y[o+3*k+1],Y[o+3*k2+2]-Y[o+3*k+2]);
      if(d<m)m=d;}}
  return m;
}
function rebuildRKBuffers(){
  if(P.centerLock&&P.mode==='solo')centerSoloCarrierAtOrigin();
  captureCarrierAnchors();
  K1=new Float64Array(Y.length);K2=new Float64Array(Y.length);
  K3=new Float64Array(Y.length);K4=new Float64Array(Y.length);TT=new Float64Array(Y.length);
}
function syncGhostRing(){
  if(!P.ghostStewartson||P.mode!=='solo'||!fils.length||!Y){
    if(ghostFil){
      removeGhostFromY();rebuildRKBuffers();rebuildLines();rebuildTubes(true);
    }
    return;
  }
  const st=carrierStats(fils[0]);
  const w=effectiveW();
  const t=taylorColumnState(st,w);
  const stw=stewartsonCirculation(w,t.rCap,P.Om);
  const N=RING_N;
  if(!ghostFil){
    const off=Y.length;
    const pts=ghostRingPts(N,t.rCap,st.cx,st.cy,st.z);
    const Y2=new Float64Array(Y.length+3*N);
    Y2.set(Y);Y2.set(pts,off);
    Y=Y2;rebuildRKBuffers();
    ghostFil={off,N,ghost:true,gammaVal:0,rCap:t.rCap,cx:st.cx,cy:st.cy,cz:st.z}; // v7.2: inert
    rebuildLines();rebuildTubes(true);
  }else{
    ghostFil.gammaVal=0;
    ghostFil.rCap=t.rCap;ghostFil.cx=st.cx;ghostFil.cy=st.cy;ghostFil.cz=st.z;
    constrainGhostRing();
  }
}
function constrainGhostRing(){
  if(!ghostFil||!Y)return;
  const {off,N,rCap,cx,cy,cz}=ghostFil;
  for(let k=0;k<N;k++){
    const th=2*Math.PI*k/N;
    Y[off+3*k]=cx+rCap*Math.cos(th);
    Y[off+3*k+1]=cy+rCap*Math.sin(th);
    Y[off+3*k+2]=cz;
  }
}
function removeGhostFromY(){
  if(!ghostFil||!Y)return;
  const go=ghostFil.off, n=3*ghostFil.N;
  const Y2=new Float64Array(Y.length-n);
  Y2.set(Y.subarray(0,go),0);
  Y2.set(Y.subarray(go+n),go);
  Y=Y2;
  ghostFil=null;
}

// ================= diagnostiek =================
// v7.2: exacte polygonale Gauss-integralen via paarsgewijze solid angles
// (Klenin & Langowski 2000, methode 1a; Levitt/Banchoff). De vaste N/24-
// truncatie van de nabij-diagonaal is weg: aanliggende segmentparen dragen
// exact 0 bij (coplanair) en worden alleen numeriek overgeslagen. Wr, Lk en
// ACN zijn hiermee exact voor de pólygoon; de discretisatie van de kromme
// zelf blijft de enige resterende benadering.
function segPairOmega(YY,o1,i,i2,o2,j,j2){
  const p1x=YY[o1+3*i], p1y=YY[o1+3*i+1], p1z=YY[o1+3*i+2];
  const p2x=YY[o1+3*i2],p2y=YY[o1+3*i2+1],p2z=YY[o1+3*i2+2];
  const p3x=YY[o2+3*j], p3y=YY[o2+3*j+1], p3z=YY[o2+3*j+2];
  const p4x=YY[o2+3*j2],p4y=YY[o2+3*j2+1],p4z=YY[o2+3*j2+2];
  const r13x=p3x-p1x,r13y=p3y-p1y,r13z=p3z-p1z;
  const r14x=p4x-p1x,r14y=p4y-p1y,r14z=p4z-p1z;
  const r23x=p3x-p2x,r23y=p3y-p2y,r23z=p3z-p2z;
  const r24x=p4x-p2x,r24y=p4y-p2y,r24z=p4z-p2z;
  let n1x=r13y*r14z-r13z*r14y,n1y=r13z*r14x-r13x*r14z,n1z=r13x*r14y-r13y*r14x;
  let n2x=r14y*r24z-r14z*r24y,n2y=r14z*r24x-r14x*r24z,n2z=r14x*r24y-r14y*r24x;
  let n3x=r24y*r23z-r24z*r23y,n3y=r24z*r23x-r24x*r23z,n3z=r24x*r23y-r24y*r23x;
  let n4x=r23y*r13z-r23z*r13y,n4y=r23z*r13x-r23x*r13z,n4z=r23x*r13y-r23y*r13x;
  const m1=n1x*n1x+n1y*n1y+n1z*n1z,m2=n2x*n2x+n2y*n2y+n2z*n2z,
        m3=n3x*n3x+n3y*n3y+n3z*n3z,m4=n4x*n4x+n4y*n4y+n4z*n4z;
  if(m1<1e-60||m2<1e-60||m3<1e-60||m4<1e-60)return 0; // coplanair/gedegenereerd
  const s1=1/Math.sqrt(m1),s2=1/Math.sqrt(m2),s3=1/Math.sqrt(m3),s4=1/Math.sqrt(m4);
  n1x*=s1;n1y*=s1;n1z*=s1; n2x*=s2;n2y*=s2;n2z*=s2;
  n3x*=s3;n3y*=s3;n3z*=s3; n4x*=s4;n4y*=s4;n4z*=s4;
  const cl=v=>v>1?1:(v<-1?-1:v);
  const om=Math.asin(cl(n1x*n2x+n1y*n2y+n1z*n2z))
          +Math.asin(cl(n2x*n3x+n2y*n3y+n2z*n3z))
          +Math.asin(cl(n3x*n4x+n3y*n4y+n3z*n4z))
          +Math.asin(cl(n4x*n1x+n4y*n1y+n4z*n1z));
  const r12x=p2x-p1x,r12y=p2y-p1y,r12z=p2z-p1z;
  const r34x=p4x-p3x,r34y=p4y-p3y,r34z=p4z-p3z;
  const cx=r34y*r12z-r34z*r12y,cy=r34z*r12x-r34x*r12z,cz=r34x*r12y-r34y*r12x;
  return (cx*r13x+cy*r13y+cz*r13z)<0?-om:om;
}
// Retourneert [getekend, absoluut]: zelfde paar-loop levert Wr én ACN
// (of Lk én kruis-ACN) in één passage.
function gauss2(o1,N1,o2,N2,same,YY){
  YY=YY||Y;
  let S=0,A=0;
  if(same){
    for(let i=0;i<N1;i++){
      const i2=(i+1)%N1;
      for(let j=i+2;j<N1;j++){
        if(i===0&&j===N1-1)continue; // wrap-aanliggend paar
        const om=segPairOmega(YY,o1,i,i2,o1,j,(j+1)%N1);
        S+=om;A+=Math.abs(om);
      }
    }
    return [S/(2*Math.PI),A/(2*Math.PI)];
  }
  for(let i=0;i<N1;i++){
    const i2=(i+1)%N1;
    for(let j=0;j<N2;j++){
      const om=segPairOmega(YY,o1,i,i2,o2,j,(j+1)%N2);
      S+=om;A+=Math.abs(om);
    }
  }
  return [S/(4*Math.PI),A/(4*Math.PI)];
}
function gauss(o1,N1,o2,N2,same,absMode,YY){
  const g=gauss2(o1,N1,o2,N2,same,YY);
  return absMode?g[1]:g[0];
}
function arcLength(f){
  let L=0;const N=f.N,o=f.off;
  for(let k=0;k<N;k++){const k2=(k+1)%N;
    L+=Math.hypot(Y[o+3*k2]-Y[o+3*k],Y[o+3*k2+1]-Y[o+3*k+1],Y[o+3*k2+2]-Y[o+3*k+2]);}
  return L;
}
function carrierStats(f){
  const N=f.N,o=f.off;
  let cx=0,cy=0,cz=0;
  for(let k=0;k<N;k++){cx+=Y[o+3*k];cy+=Y[o+3*k+1];cz+=Y[o+3*k+2];}
  cx/=N;cy/=N;cz/=N;
  let R=0,rWall=0;
  for(let k=0;k<N;k++){
    R+=Math.hypot(Y[o+3*k]-cx,Y[o+3*k+1]-cy);
    const rw=Math.hypot(Y[o+3*k],Y[o+3*k+1]);if(rw>rWall)rWall=rw;
  }
  return {R:R/N,z:cz,rWall,cx,cy};
}
function minGapCross(){
  if(P.mode!=='botsing')return 1e9;
  const fa=carrierFilaments('A'),fb=carrierFilaments('B');
  if(!fa.length||!fb.length)return 1e9;
  let m2=Infinity;
  for(const f1 of fa)for(const f2 of fb)
    m2=Math.min(m2,pairGapExact2(f1,f2,m2));
  return Math.sqrt(m2);
}
// v7.2: exacte segment-segment minimumafstand² tussen twee filamenten,
// met middelpunt-prefilter tegen de lopende beste waarde.
function pairGapExact2(fa,fb,best2){
  const Na=fa.N,oa=fa.off,Nb=fb.N,ob=fb.off;
  let m2=best2;
  for(let i=0;i<Na;i++){
    const i2=(i+1)%Na;
    const ax=Y[oa+3*i],ay=Y[oa+3*i+1],az=Y[oa+3*i+2];
    const bx=Y[oa+3*i2],by=Y[oa+3*i2+1],bz=Y[oa+3*i2+2];
    const mx=.5*(ax+bx),my=.5*(ay+by),mz=.5*(az+bz);
    const li=Math.hypot(bx-ax,by-ay,bz-az);
    for(let j=0;j<Nb;j++){
      const j2=(j+1)%Nb;
      const cxx=Y[ob+3*j],cyy=Y[ob+3*j+1],czz=Y[ob+3*j+2];
      const dxx=Y[ob+3*j2],dyy=Y[ob+3*j2+1],dzz=Y[ob+3*j2+2];
      const nx=.5*(cxx+dxx)-mx,ny=.5*(cyy+dyy)-my,nz=.5*(czz+dzz)-mz;
      const lj=Math.hypot(dxx-cxx,dyy-cyy,dzz-czz);
      const bound=Math.sqrt(nx*nx+ny*ny+nz*nz)-.5*(li+lj);
      if(bound>0&&bound*bound>=m2)continue;
      const d2=segSegDist2(ax,ay,az,bx,by,bz,cxx,cyy,czz,dxx,dyy,dzz);
      if(d2<m2)m2=d2;
    }
  }
  return m2;
}
// v7.2: exacte minimale afstand tussen twee lijnsegmenten AB en CD (kwadraat).
// Geklemde closest-point-of-approach (Lumelsky/Ericson). Robuust voor
// gedegenereerde (punt)segmenten en parallelle paren.
function segSegDist2(ax,ay,az,bx,by,bz,cx,cy,cz,dx,dy,dz){
  const ux=bx-ax,uy=by-ay,uz=bz-az;
  const vx=dx-cx,vy=dy-cy,vz=dz-cz;
  const wx=ax-cx,wy=ay-cy,wz=az-cz;
  const A=ux*ux+uy*uy+uz*uz, B=ux*vx+uy*vy+uz*vz, C=vx*vx+vy*vy+vz*vz;
  const D=ux*wx+uy*wy+uz*wz, E=vx*wx+vy*wy+vz*wz;
  const den=A*C-B*B;
  let sN,sD=den,tN,tD=den;
  if(den<1e-30){sN=0;sD=1;tN=E;tD=C;}          // (bijna) parallel
  else{
    sN=B*E-C*D;tN=A*E-B*D;
    if(sN<0){sN=0;tN=E;tD=C;}
    else if(sN>sD){sN=sD;tN=E+B;tD=C;}
  }
  if(tN<0){tN=0;
    if(-D<0)sN=0;else if(-D>A){sN=sD;}else{sN=-D;sD=A;}
  }else if(tN>tD){tN=tD;
    const nD=-D+B;
    if(nD<0)sN=0;else if(nD>A){sN=sD;}else{sN=nD;sD=A;}
  }
  const sc=Math.abs(sD)<1e-30?0:sN/sD;
  const tc=Math.abs(tD)<1e-30?0:tN/tD;
  const px=wx+sc*ux-tc*vx, py=wy+sc*uy-tc*vy, pz=wz+sc*uz-tc*vz;
  return px*px+py*py+pz*pz;
}
// v7.2: exacte zelf-afstand op segmentniveau. De index-uitsluiting is niet
// langer de vaste fractie N/24 maar een boog-venster van 6a (2× de
// 3a-drempel): op een gladde kromme kan de zelf-afstand binnen dat venster
// niet onder 3a komen zonder dat de aκ-diagnose allang rood is. Aanliggende
// segmenten (gedeeld knooppunt, afstand 0) worden altijd uitgesloten.
function dminSelf(f){
  const N=f.N,o=f.off;
  let L=0;for(let k=0;k<N;k++){const k2=(k+1)%N;
    L+=Math.hypot(Y[o+3*k2]-Y[o+3*k],Y[o+3*k2+1]-Y[o+3*k+1],Y[o+3*k2+2]-Y[o+3*k+2]);}
  const lmean=L/Math.max(1,N);
  const skip=Math.max(2,Math.ceil(6*P.a/Math.max(lmean,1e-12)));
  let m2=Infinity;
  for(let i=0;i<N;i++){
    const i2=(i+1)%N;
    const ax=Y[o+3*i],ay=Y[o+3*i+1],az=Y[o+3*i+2];
    const bx=Y[o+3*i2],by=Y[o+3*i2+1],bz=Y[o+3*i2+2];
    const mx=.5*(ax+bx),my=.5*(ay+by),mz=.5*(az+bz);
    const li=Math.hypot(bx-ax,by-ay,bz-az);
    for(let j=i+1;j<N;j++){
      const dd=Math.min(j-i,N-(j-i));if(dd<skip)continue;
      const j2=(j+1)%N;
      const cxx=Y[o+3*j],cyy=Y[o+3*j+1],czz=Y[o+3*j+2];
      const dxx=Y[o+3*j2],dyy=Y[o+3*j2+1],dzz=Y[o+3*j2+2];
      // prefilter: middelpuntafstand minus halve segmentlengtes begrenst d_seg
      const nx=.5*(cxx+dxx)-mx,ny=.5*(cyy+dyy)-my,nz=.5*(czz+dzz)-mz;
      const lj=Math.hypot(dxx-cxx,dyy-cyy,dzz-czz);
      const bound=Math.sqrt(nx*nx+ny*ny+nz*nz)-.5*(li+lj);
      if(bound>0&&bound*bound>=m2)continue;
      const d2=segSegDist2(ax,ay,az,bx,by,bz,cxx,cyy,czz,dxx,dyy,dzz);
      if(d2<m2)m2=d2;
    }
  }
  return Math.sqrt(m2);
}


// ================= geometrische kernlimiet / tube reach =================
let coreRadiusMax=0.07;
function pointTangent(f,i){
  const im=(i-1+f.N)%f.N,ip=(i+1)%f.N,o=f.off;
  const x=Y[o+3*ip]-Y[o+3*im],y=Y[o+3*ip+1]-Y[o+3*im+1],z=Y[o+3*ip+2]-Y[o+3*im+2];
  const n=Math.hypot(x,y,z)||1;return [x/n,y/n,z/n];
}
function minCurvatureRadius(f){
  let out=Infinity;const o=f.off,N=f.N;
  for(let i=0;i<N;i++){
    const im=(i-1+N)%N,ip=(i+1)%N;
    const ax=Y[o+3*i]-Y[o+3*im],ay=Y[o+3*i+1]-Y[o+3*im+1],az=Y[o+3*i+2]-Y[o+3*im+2];
    const bx=Y[o+3*ip]-Y[o+3*i],by=Y[o+3*ip+1]-Y[o+3*i+1],bz=Y[o+3*ip+2]-Y[o+3*i+2];
    const la=Math.hypot(ax,ay,az),lb=Math.hypot(bx,by,bz);if(la<1e-12||lb<1e-12)continue;
    const dot=clamp((ax*bx+ay*by+az*bz)/(la*lb),-1,1);
    const kappa=2*Math.sin(0.5*Math.acos(dot))/Math.max(1e-12,0.5*(la+lb));
    if(kappa>1e-12)out=Math.min(out,1/kappa);
  }
  return out;
}
function approximateDoublyCriticalDistance(f){
  const N=f.N,o=f.off,skip=Math.max(6,Math.round(N/10));
  const stride=Math.max(1,Math.ceil(N/220));let best=Infinity;
  for(let i=0;i<N;i+=stride){
    const ti=pointTangent(f,i);
    for(let j=i+skip;j<N;j+=stride){
      const dd=Math.min(j-i,N-(j-i));if(dd<skip)continue;
      const dx=Y[o+3*j]-Y[o+3*i],dy=Y[o+3*j+1]-Y[o+3*i+1],dz=Y[o+3*j+2]-Y[o+3*i+2];
      const d=Math.hypot(dx,dy,dz);if(d<1e-12||d>=best)continue;
      const tj=pointTangent(f,j);
      const ci=Math.abs((dx*ti[0]+dy*ti[1]+dz*ti[2])/d);
      const cj=Math.abs((dx*tj[0]+dy*tj[1]+dz*tj[2])/d);
      if(ci<0.22&&cj<0.22)best=d;
    }
  }
  return best;
}
function intrinsicCoreRadiusLimit(){
  if(!Y||!fils.length)return Math.max(1e-6,P.R0);
  let reach=Infinity;
  for(const carrier of ['A','B']){
    const fs=carrierFilaments(carrier);if(!fs.length)continue;
    if(P.topo==='ring'&&fs.length===1&&!P.knotKey&&P.knotIdx<0){
      reach=Math.min(reach,carrierStats(fs[0]).R);
      continue;
    }
    for(const f of fs){
      reach=Math.min(reach,minCurvatureRadius(f));
      const dcsd=approximateDoublyCriticalDistance(f);
      if(Number.isFinite(dcsd))reach=Math.min(reach,0.5*dcsd);
    }
    for(let i=0;i<fs.length;i++)for(let j=i+1;j<fs.length;j++)
      reach=Math.min(reach,0.5*sampledPairGap(fs[i],fs[j]));
  }
  if(!Number.isFinite(reach)||reach<=0)reach=Math.max(1e-6,P.R0);
  return Math.max(1e-6,0.995*reach);
}
function updateCoreRadiusLimit(clampValue=true){
  coreRadiusMax=intrinsicCoreRadiusLimit();
  const maxMm=Math.max(0,coreRadiusMax*1000);
  const input=document.getElementById('sA');
  if(input){
    input.min=String(A_SIM_INPUT_FLOOR*1000);input.max=maxMm.toFixed(12);input.step='any';
    const range=input.closest('.param-hybrid')?.querySelector('input.param-slider');
    if(range){range.min=input.min;range.max=input.max;range.step=input.step;}
  }
  let wasClamped=false;
  if(clampValue&&(!Number.isFinite(P.a)||P.a<A_SIM_INPUT_FLOOR||P.a>coreRadiusMax)){
    P.a=clamp(Number.isFinite(P.a)?P.a:A_SIM_INPUT_FLOOR,A_SIM_INPUT_FLOOR,Math.max(A_SIM_INPUT_FLOOR,coreRadiusMax));
    wasClamped=true;
  }
  if(wasClamped&&P.coreFlowLock)syncCoreFlowCoupling('geometry');
  if(input)input.value=formatASimInputMm(P.a);
  const v=document.getElementById('vA');
  if(v)v.textContent=`${fmtLengthSI(P.a)} · max ${maxMm.toFixed(2)} mm`;
  const ct=contactThresholdInfo();
  const floorNote=ct.floorActive
    ?` Expertmodus: 3a=${fmtLengthSI(ct.physical)} ligt onder de numerieke afstandsvloer ${fmtLengthSI(ct.numerical)}; contactdetectie gebruikt de numerieke vloer.`
    :'';
  const note=document.getElementById('coreLimitNote');
  if(note)note.textContent=`Geometrische tube-reach ≈ ${maxMm.toFixed(3)} mm (kromming / doubly-critical zelfafstand). Dit is de zelfcontactgrens; de slanke filamentbenadering wordt al ruim vóór deze grens rood.${floorNote}`;
  syncHybridNumberInputs();
}

// ================= stabiliteitsdiagnose & geometrische auto-relax =================
function scoreDescending(x,good,bad){
  if(x<=good)return 100;if(x>=bad)return 0;
  return 100*(bad-x)/(bad-good);
}
function scoreAscending(x,bad,good){
  if(x>=good)return 100;if(x<=bad)return 0;
  return 100*(x-bad)/(good-bad);
}
function statusFromScore(v){return v>=75?'good':(v>=45?'warn':'bad');}
function capacityStatusFromScore(v){return v>=75?'good':(v>=45?'warn':'capacity');}
function worstStatus(...vals){
  const rank={good:0,warn:1,bad:2};let out='good';
  vals.forEach(v=>{const s=typeof v==='number'?statusFromScore(v):v;if(rank[s]>rank[out])out=s;});
  return out;
}
function stabilityElementTarget(id){
  const el=document.getElementById(id);if(!el)return null;
  if(el.classList.contains('seg'))return el;
  return el.closest('.ctrl')||el.closest('.param-hybrid')||el;
}
function clearStabilityTargets(){
  document.querySelectorAll('.stability-target').forEach(el=>{
    el.classList.remove('stability-target','stab-good','stab-warn','stab-bad','stab-capacity');
    if(el.dataset.stabilityTitle){el.title=el.dataset.stabilityTitle;delete el.dataset.stabilityTitle;}
  });
}
function markStabilityTarget(id,status,tip){
  const el=stabilityElementTarget(id);if(!el)return;
  el.classList.add('stability-target','stab-'+status);
  if(!el.dataset.stabilityTitle)el.dataset.stabilityTitle=el.title||'';
  el.title=tip||el.dataset.stabilityTitle;
}
function filamentResolutionMetrics(f){
  const N=f.N,o=f.off;
  let lmin=Infinity,lmax=0,lsum=0,maxAk=0,minLogArg=Infinity;
  const eD=Math.exp(DELTA[P.core]);
  for(let i=0;i<N;i++){
    const im=(i-1+N)%N,ip=(i+1)%N;
    const ax=Y[o+3*i]-Y[o+3*im],ay=Y[o+3*i+1]-Y[o+3*im+1],az=Y[o+3*i+2]-Y[o+3*im+2];
    const bx=Y[o+3*ip]-Y[o+3*i],by=Y[o+3*ip+1]-Y[o+3*i+1],bz=Y[o+3*ip+2]-Y[o+3*i+2];
    const la=Math.hypot(ax,ay,az),lb=Math.hypot(bx,by,bz);
    lmin=Math.min(lmin,lb);lmax=Math.max(lmax,lb);lsum+=lb;
    if(la>1e-12&&lb>1e-12){
      const dot=clamp((ax*bx+ay*by+az*bz)/(la*lb),-1,1);
      const ang=Math.acos(dot),kappa=2*Math.sin(0.5*ang)/Math.max(1e-12,0.5*(la+lb));
      maxAk=Math.max(maxAk,P.a*kappa);
      minLogArg=Math.min(minLogArg,2*Math.sqrt(la*lb)/(eD*Math.max(P.a,1e-12)));
    }
  }
  return {lmin,lmax,lmean:lsum/N,q:lmax/Math.max(lmin,1e-12),maxAk,minLogArg};
}
function sampledPairGap(fa,fb){
  // v7.2: exact op segmentniveau (naam behouden voor call-sites); de oude
  // gestreden knooppuntsteekproef kon interieurnaderingen missen.
  return Math.sqrt(pairGapExact2(fa,fb,Infinity));
}
function sampledSelfGap(f){
  return dminSelf(f); // v7.2: exact segmentniveau
}
function updateChiPanel(){
  const el=document.getElementById('chiRope');
  if(!el||!Y||!fils.length)return;
  const fa=carrierFilaments('A');
  if(!fa.length){el.textContent='—';return;}
  let L=0, rC=Infinity, dC=Infinity;
  for(const f of fa){
    L+=arcLength(f);
    rC=Math.min(rC,minCurvatureRadius(f));
    dC=Math.min(dC,approximateDoublyCriticalDistance(f));
  }
  for(let i=0;i<fa.length;i++)for(let j=i+1;j<fa.length;j++)
    dC=Math.min(dC,sampledPairGap(fa[i],fa[j]));
  const tau=Math.min(rC,dC/2);
  if(!(tau>1e-9)||!isFinite(tau)||!isFinite(L)){el.textContent='—';return;}
  const rope=L/(2*tau);
  el.textContent=rope.toFixed(3);
  const r2=document.getElementById('chiRopeRatio');
  if(r2)r2.textContent=(rope/16.371637).toFixed(3);
  const th=document.getElementById('chiThick');
  if(th)th.textContent=(tau*1000).toFixed(2)+' mm';
}
function computeStabilityReport(){
  if(!Y||!fils.length)return null;
  // v7.1 (B5): diagnose is puur — alleen meten, nooit P.a klemmen. Klemmen
  // gebeurt uitsluitend bij expliciete gebruikersacties (reset, geometrie).
  updateCoreRadiusLimit(false);
  let q=1,maxAk=0,minLogArg=Infinity,lmean=0,nm=0,minGap=Infinity,boundary=Infinity,Lnow=0;
  const realFils=fils.filter(f=>!f.ghost);
  for(const f of realFils){
    const m=filamentResolutionMetrics(f);q=Math.max(q,m.q);maxAk=Math.max(maxAk,m.maxAk);
    minLogArg=Math.min(minLogArg,m.minLogArg);lmean+=m.lmean;nm++;Lnow+=arcLength(f);
    minGap=Math.min(minGap,sampledSelfGap(f));
    for(let k=0;k<f.N;k++){
      const x=Y[f.off+3*k],y=Y[f.off+3*k+1],z=Y[f.off+3*k+2];
      // v7.2: marge t.o.v. de búisrand, niet de centerline (audit #9)
      boundary=Math.min(boundary,P.Rcyl-Math.hypot(x,y)-P.a,z-zMin()-P.a,zMax()-z-P.a);
    }
  }
  for(let i=0;i<realFils.length;i++)for(let j=i+1;j<realFils.length;j++)
    minGap=Math.min(minGap,sampledPairGap(realFils[i],realFils[j]));
  lmean/=Math.max(1,nm);
  const gapRatio=minGap/Math.max(P.a,1e-12);
  const boundaryRatio=boundary/Math.max(P.a,lmean,1e-12);
  const lengthDrift=Math.abs(Lnow/Math.max(L0,1e-12)-1);
  const meshScore=scoreDescending(q,1.22,2.10);
  const gapScore=scoreAscending(gapRatio,3.0,8.0);
  const curvatureScore=scoreDescending(maxAk,0.10,0.45);
  const coreScore=scoreAscending(minLogArg,1.15,4.0);
  const boundaryScore=scoreAscending(boundaryRatio,1.5,7.0);
  const lengthScore=scoreDescending(lengthDrift,0.025,0.28);
  const requestedAccNow=acc()*Math.max(0,stabilityThrottle);
  const perfWarming=performance.now()<perfWarmupUntil;
  const perfRatio=perfWarming||Math.abs(tPhys)<0.15||requestedAccNow<1e-8?1:clamp(effAcc/requestedAccNow,0,1);
  const perfScore=scoreAscending(perfRatio,0.20,0.80);
  let modelScore=100;
  if(P.inter==='lia'&&gapRatio<10)modelScore=gapRatio<5?20:55;
  // De numerieke score bevat uitsluitend geldigheids-/modelcriteria. De
  // haalbare afspeelsnelheid is een afzonderlijke computer-capaciteitsmeting.
  let score=(0.20*meshScore+0.23*gapScore+0.17*curvatureScore+0.10*coreScore+
    0.13*boundaryScore+0.09*lengthScore)/0.92;
  score=Math.min(score,modelScore);
  if(gapRatio<3||boundary<0||minLogArg<=1)score=Math.min(score,18);
  const suggestions=[];
  if(meshScore<75)suggestions.push('verhoog kwaliteit of zet Auto-relax aan om de puntverdeling gelijkmatiger te maken');
  if(gapScore<75)suggestions.push('vergroot de vrije afstand: verlaag kernstraal a, verminder drift/botsingssnelheid, vergroot offset of reset');
  if(curvatureScore<75)suggestions.push('max aκ is hoog: verlaag a, verhoog resolutie of gebruik Auto-relax');
  if(coreScore<75)suggestions.push('de lokale inductielogaritme is slecht opgelost: verlaag a of verhoog kwaliteit');
  if(boundaryScore<75)suggestions.push('vergroot cilinderdiameter/hoogte of centreer/reset de drager');
  if(lengthScore<75)suggestions.push('sterke lengtedrift: verlaag tijdversnelling of gebruik Auto-relax');
  if(!perfWarming&&perfScore<60)suggestions.push('capaciteitslimiet: verlaag de simulatiesnelheid, Γ/n, kwaliteit of het aantal particles; het CFL-traject blijft identiek');
  if(modelScore<75)suggestions.push('LIA mist belangrijke niet-lokale interactie: kies Biot–Savart');
  if(!suggestions.length)suggestions.push('instellingen liggen binnen de numerieke comfortzone; dit is geen bewijs van fysische stabiliteit');
  return {score:clamp(score,0,100),status:statusFromScore(score),q,gapRatio,maxAk,minLogArg,
    boundary,boundaryRatio,lengthDrift,perfRatio,perfWarming,meshScore,gapScore,curvatureScore,coreScore,
    boundaryScore,lengthScore,perfScore,modelScore,suggestions};
}
function updateStabilityDisplay(rep){
  if(!rep)return;
  stabilityLast=rep;
  const panel=document.getElementById('stabilityPanel'),gauge=document.getElementById('stabilityGauge');
  const color=rep.status==='good'?'#7BE8A8':(rep.status==='warn'?'#FFAE45':'#FF6E6E');
  panel.classList.remove('stab-good','stab-warn','stab-bad');panel.classList.add('stab-'+rep.status);
  gauge.style.setProperty('--score-angle',(rep.score*3.6).toFixed(1)+'deg');gauge.style.setProperty('--stab-color',color);
  document.getElementById('stabilityScore').textContent=Math.round(rep.score);
  document.getElementById('stabilityTitle').textContent=rep.status==='good'?'numeriek rustig':(rep.status==='warn'?'aandacht vereist':'instabiel / buiten geldigheid');
  document.getElementById('stabilitySummary').textContent=P.timeReverse
    ?'Achterwaartse integratie actief; Auto-relax is gepauzeerd en de numerieke veiligheidsrem blijft actief.'
    :(P.autoRelax?'Auto-relax actief; geometrische regularisatie corrigeert langzaam.':'Passieve numerieke diagnose; paars betekent alleen een computer-capaciteitslimiet.');
  document.getElementById('stabMesh').textContent=rep.q.toFixed(2);
  document.getElementById('stabGap').textContent=isFinite(rep.gapRatio)?rep.gapRatio.toFixed(1):'∞';
  document.getElementById('stabCurv').textContent=rep.maxAk.toFixed(3);
  document.getElementById('stabBoundary').textContent=(rep.boundary*1000).toFixed(1)+' mm';
  document.getElementById('stabLength').textContent=(100*rep.lengthDrift).toFixed(1)+'%';
  document.getElementById('stabPerf').textContent=rep.perfWarming?'meting…':((100*rep.perfRatio).toFixed(0)+'%'+(rep.perfScore<45?' · capaciteit':''));
  document.getElementById('stabThrottle').textContent=(100*stabilityThrottle).toFixed(0)+'%';
  document.getElementById('stabilityAdvice').textContent='Advies: '+rep.suggestions.slice(0,3).join(' · ')+'.';
  clearStabilityTargets();
  const coreStat=worstStatus(rep.curvatureScore,rep.coreScore,rep.gapScore);
  const meshStat=worstStatus(rep.meshScore,rep.curvatureScore,rep.coreScore);
  const gapStat=statusFromScore(rep.gapScore),boundStat=statusFromScore(rep.boundaryScore),perfStat=capacityStatusFromScore(rep.perfScore);
  markStabilityTarget('sA',coreStat,rep.suggestions.find(x=>x.includes('aκ')||x.includes('kernstraal')||x.includes('inductielogaritme'))||'Kernradius beïnvloedt slankheid en contactmarge.');
  markStabilityTarget('qualSeg',meshStat,rep.meshScore<75?'Verhoog kwaliteit voor gelijkmatiger segmenten en betere kromming.':'Resolutie is passend.');
  markStabilityTarget('interSeg',statusFromScore(rep.modelScore),rep.modelScore<75?'Schakel naar Biot–Savart; LIA mist de nabije niet-lokale interactie.':'Interactiemodel past bij de huidige afstand.');
  markStabilityTarget('sDiam',boundStat,rep.boundaryScore<75?'Vergroot de diameter of reset/centreer de knoop.':'Radiale domeinmarge is voldoende.');
  markStabilityTarget('sHeight',boundStat,rep.boundaryScore<75?'Vergroot de halve hoogte of reset/centreer de knoop.':'Axiale domeinmarge is voldoende.');
  markStabilityTarget('sOff',gapStat,rep.gapScore<75?'Pas de offset aan om near-contact te vermijden.':'Onderlinge vrije afstand is voldoende.');
  ['sW','sVzA','sVzB'].forEach(id=>markStabilityTarget(id,worstStatus(gapStat,boundStat),rep.gapScore<75?'Verminder de opgelegde drift; strengen naderen het reconnectieregime.':'Drift is binnen de huidige marge.'));
  ['sGa','sNq','sOm','sAcc','sTracerCount','sStreamlineCount'].forEach(id=>markStabilityTarget(id,perfStat,rep.perfWarming?'Capaciteitsmeting warmt 0,9 s op na de laatste snelheidswijziging.':(rep.perfScore<60?'Computer-capaciteitslimiet: verlaag belasting of afspeeltempo; dit is geen numerieke instabiliteit.':'Rekenlast is beheersbaar.')));
  const emissive=rep.status==='good'?0x123d29:(rep.status==='warn'?0x4a2f0d:0x4a1018);
  [matSolidA,matSolidB].forEach(m=>{if(m&&m.emissive){m.emissive.setHex(emissive);m.emissiveIntensity=rep.status==='good'?0.16:(rep.status==='warn'?0.30:0.42);}});
  scheduleSidebarFit();
}
function throttleFromStabilityScore(score){
  // Volle snelheid vanaf score 75; smoothstep naar nul bij score 0.
  const x=clamp(score/75,0,1);
  return x*x*(3-2*x);
}
function updateStabilityThrottle(dtReal){
  stabilityThrottleTarget=stabilityLast?throttleFromStabilityScore(stabilityLast.score):1;
  if(flagged)stabilityThrottleTarget=0;
  // Sneller afremmen dan herstellen, zodat ongeldige configuraties direct kalmeren.
  const tau=stabilityThrottleTarget<stabilityThrottle?0.28:1.10;
  const blend=1-Math.exp(-Math.max(0,dtReal)/tau);
  stabilityThrottle+=blend*(stabilityThrottleTarget-stabilityThrottle);
  if(stabilityThrottle<0.002&&stabilityThrottleTarget===0)stabilityThrottle=0;
  stabilityThrottle=clamp(stabilityThrottle,0,1);
}

function carrierRelaxGroups(){
  const groups=new Map();
  fils.filter(f=>!f.ghost).forEach(f=>{if(!groups.has(f.carrier))groups.set(f.carrier,[]);groups.get(f.carrier).push(f);});
  return [...groups.values()];
}
function groupCentroidRms(group){
  let cx=0,cy=0,cz=0,n=0;
  group.forEach(f=>{for(let k=0;k<f.N;k++){cx+=Y[f.off+3*k];cy+=Y[f.off+3*k+1];cz+=Y[f.off+3*k+2];n++;}});
  cx/=n;cy/=n;cz/=n;let r2=0;
  group.forEach(f=>{for(let k=0;k<f.N;k++){const dx=Y[f.off+3*k]-cx,dy=Y[f.off+3*k+1]-cy,dz=Y[f.off+3*k+2]-cz;r2+=dx*dx+dy*dy+dz*dz;}});
  return {cx,cy,cz,rms:Math.sqrt(r2/n),n};
}
function redistributeFilamentUniform(f){
  const N=f.N,o=f.off,cum=new Float64Array(N+1);cum[0]=0;
  for(let k=0;k<N;k++){const k2=(k+1)%N;cum[k+1]=cum[k]+Math.hypot(Y[o+3*k2]-Y[o+3*k],Y[o+3*k2+1]-Y[o+3*k+1],Y[o+3*k2+2]-Y[o+3*k+2]);}
  const L=cum[N];if(L<1e-12)return;
  const out=new Float64Array(3*N);let j=0;
  for(let k=0;k<N;k++){
    const target=L*k/N;while(j<N-1&&cum[j+1]<target)j++;
    const j2=(j+1)%N,den=Math.max(1e-12,cum[j+1]-cum[j]),u=(target-cum[j])/den;
    out[3*k]=Y[o+3*j]+u*(Y[o+3*j2]-Y[o+3*j]);
    out[3*k+1]=Y[o+3*j+1]+u*(Y[o+3*j2+1]-Y[o+3*j+1]);
    out[3*k+2]=Y[o+3*j+2]+u*(Y[o+3*j2+2]-Y[o+3*j+2]);
  }
  Y.set(out,o);
}
function applyShortRangeRepulsion(group,amount){
  const target=Math.max(4.5*P.a,1e-6),skipFrac=1/28;
  for(let ai=0;ai<group.length;ai++)for(let bi=ai;bi<group.length;bi++){
    const fa=group[ai],fb=group[bi],skip=Math.max(4,Math.round(fa.N*skipFrac));
    const stride=Math.max(1,Math.ceil(Math.max(fa.N,fb.N)/160));
    for(let i=0;i<fa.N;i+=stride){
      const j0=ai===bi?i+skip:0;
      for(let j=j0;j<fb.N;j+=stride){
        if(ai===bi&&Math.min(j-i,fa.N-(j-i))<skip)continue;
        const ia=fa.off+3*i,ib=fb.off+3*j,dx=Y[ia]-Y[ib],dy=Y[ia+1]-Y[ib+1],dz=Y[ia+2]-Y[ib+2];
        const d=Math.hypot(dx,dy,dz);if(d>=target||d<1e-10)continue;
        const push=0.5*amount*(target-d)/target,ux=dx/d,uy=dy/d,uz=dz/d;
        Y[ia]+=push*ux;Y[ia+1]+=push*uy;Y[ia+2]+=push*uz;
        Y[ib]-=push*ux;Y[ib+1]-=push*uy;Y[ib+2]-=push*uz;
      }
    }
  }
}
function autoRelaxGeometry(dtReal){
  if(!P.autoRelax||P.timeReverse||!Y||!fils.length||flagged)return;
  const alpha=clamp(0.55*dtReal,0,0.012),groups=carrierRelaxGroups();
  for(const group of groups){
    const before=groupCentroidRms(group),updates=[];
    for(const f of group){
      const out=new Float64Array(3*f.N),o=f.off,N=f.N;
      for(let k=0;k<N;k++){
        const im=(k-1+N)%N,ip=(k+1)%N;
        const px=Y[o+3*k],py=Y[o+3*k+1],pz=Y[o+3*k+2];
        let tx=Y[o+3*ip]-Y[o+3*im],ty=Y[o+3*ip+1]-Y[o+3*im+1],tz=Y[o+3*ip+2]-Y[o+3*im+2];
        const tl=Math.hypot(tx,ty,tz)||1;tx/=tl;ty/=tl;tz/=tl;
        let lx=0.5*(Y[o+3*im]+Y[o+3*ip])-px,ly=0.5*(Y[o+3*im+1]+Y[o+3*ip+1])-py,lz=0.5*(Y[o+3*im+2]+Y[o+3*ip+2])-pz;
        const tang=lx*tx+ly*ty+lz*tz;lx-=tang*tx;ly-=tang*ty;lz-=tang*tz;
        out[3*k]=px+alpha*lx;out[3*k+1]=py+alpha*ly;out[3*k+2]=pz+alpha*lz;
      }
      updates.push([f,out]);
    }
    updates.forEach(([f,out])=>Y.set(out,f.off));
    if((autoRelaxFrame%4)===0)applyShortRangeRepulsion(group,Math.max(P.a,0.25*(group[0]?filamentResolutionMetrics(group[0]).lmean:0))*alpha);
    if((autoRelaxFrame%3)===0)group.forEach(redistributeFilamentUniform);
    const after=groupCentroidRms(group),scale=after.rms>1e-12?before.rms/after.rms:1;
    group.forEach(f=>{for(let k=0;k<f.N;k++){
      const i=f.off+3*k;Y[i]=before.cx+(Y[i]-after.cx)*scale;Y[i+1]=before.cy+(Y[i+1]-after.cy)*scale;Y[i+2]=before.cz+(Y[i+2]-after.cz)*scale;
    }});
  }
  autoRelaxFrame++;
}

// ================= reset / rebuild =================
function applyCanonPreset(){
  P.mode='botsing'; P.topo='ring'; P.inter='bs'; P.core='hol'; P.med='demo'; P.qual='mid'; P.coreFlowLock=false;
  P.Om=1; P.GaDemo=2; P.nQ=1; P.a=1.5e-3; P.off=0; P.w=0; P.coRot=false;
  P.R0=0.07; P.zA=-0.42; P.zB=0.42; P.Rcyl=0.25; P.Hcyl=0.5;
  P.knotIdx=-1; P.knotKey=''; P.compA=1; P.compB=1;
  P.ccwA=true; P.ccwB=false; P.mirrorB=false; P.vzA=0; P.vzB=0; P.lockVz=true;
  P.revOm=false; P.revGa=false; P.revOff=false; P.revW=false; P.revVzA=false; P.revVzB=false;
  P.ghostStewartson=false; P.taylorOsc.enabled=false;
  P.bgOmegaCoupling=false;
  Object.keys(Flags).forEach(k=>{Flags[k]=false;});
  renderFormula(); syncDiagnosticToggles();
  rebuildVolumeEnvelope();
  syncUi();
}
function applyPistolPreset(){
  P.mode='solo'; P.topo='ring'; P.inter='bs'; P.core='hol'; P.med='demo'; P.qual='mid'; P.coreFlowLock=false;
  P.Om=0; P.GaDemo=2; P.nQ=1; P.a=1.5e-3; P.off=0; P.coRot=false;
  P.R0=0.07; P.zSolo=-0.42; P.Rcyl=0.25; P.Hcyl=0.5;
  P.knotIdx=-1; P.knotKey=''; P.w=0; P.vzA=0; P.vzB=0;
  P.ccwA=true; P.ghostStewartson=false; P.taylorOsc.enabled=false;
  P.bgOmegaCoupling=false; P.twistProxyEnabled=false;
  P.revOm=false; P.revGa=false; P.revW=false;
  Object.keys(Flags).forEach(k=>{Flags[k]=false;});
  renderFormula(); syncDiagnosticToggles();
  rebuildVolumeEnvelope();
  syncUi();
}
function applyTaylorPreset(){
  P.mode='solo'; P.topo='ring'; P.inter='bs'; P.core='hol'; P.med='demo'; P.qual='mid'; P.coreFlowLock=false;
  P.Om=1; P.GaDemo=2; P.nQ=1; P.a=1.5e-3; P.off=0; P.coRot=false;
  P.R0=0.07; P.zSolo=0.0; P.Rcyl=0.25; P.Hcyl=0.5;
  P.knotIdx=-1; P.knotKey='';
  P.w=0.03; P.revW=false;
  P.ghostStewartson=false;
  P.taylorOsc={enabled:false, amplitude:0.25, period:8};
  P.revOm=false; P.revGa=false;
  Object.keys(Flags).forEach(k=>{Flags[k]=false;});
  setDvAll(true);
  renderFormula(); syncDiagnosticToggles();
  rebuildVolumeEnvelope();
  syncUi();
}
function resetState(){
  ghostFil=null;
  const N=carrierN();
  const specs=P.mode==='botsing'
    ?[{which:'A',z:P.zA,cx:0,want:carrierWantDir('A')},
      {which:'B',z:P.zB,cx:carrierOffsetX('B'),want:carrierWantDir('B')}]
    :[{which:'A',z:P.zSolo,cx:carrierOffsetX('A'),want:carrierWantDir('A')}];
  const chunks=[];
  for(const sp of specs){
    const comps=makeCarrierComponents(N,sp.z,sp.cx,sp.want,sp.which);
    comps.forEach((pts,component)=>chunks.push({pts,N,carrier:sp.which,component}));
  }
  const totalPts=chunks.reduce((a,c)=>a+c.N,0);
  Y=new Float64Array(3*totalPts);
  fils=[];
  let off=0;
  for(const ch of chunks){
    Y.set(ch.pts,off);
    fils.push({off,N:ch.N,carrier:ch.carrier,component:ch.component,topology:P.topo});
    off+=3*ch.N;
  }
  if(P.centerLock&&P.mode==='solo')centerSoloCarrierAtOrigin();
  captureCarrierAnchors();
  K1=new Float64Array(Y.length);K2=new Float64Array(Y.length);
  K3=new Float64Array(Y.length);K4=new Float64Array(Y.length);TT=new Float64Array(Y.length);
  tPhys=0;phi=0;bundlePhi=0;flagged="";warned=false;lastUmax=1e-9;
  resetPerformanceMeasurement(900);stepDebt=0;hist.length=0;
  stabilityLast=null;stabilityFrame=0;autoRelaxFrame=0;
  stabilityThrottle=1;stabilityThrottleTarget=1;
  Wr0=0;for(const f of fils){if(f.ghost)continue;Wr0+=gauss(f.off,f.N,f.off,f.N,true);}
  L0=0;for(const f of fils)L0+=arcLength(f);
  document.getElementById('flag').style.display='none';
  rebuildLines();
  rebuildTubes(true);
  updateSubtitle();
  initTwistProxy();
  syncGhostRing();
  updateCoreRadiusLimit(true);
  rebuildStreamlines(true);
}
function applyTaylorOscillation(){
  if(P.centerLock||!P.taylorOsc.enabled||!Y||!fils.length)return;
  const st=carrierGroupStats('A');
  const zAnchor=(P.mode==='solo')?P.zSolo:P.zA;
  const zT=zAnchor+P.taylorOsc.amplitude*Math.sin(2*Math.PI*tPhys/Math.max(0.5,P.taylorOsc.period));
  const dz=zT-st.z;
  if(Math.abs(dz)<1e-9)return;
  for(const f of carrierFilaments('A'))for(let k=0;k<f.N;k++)Y[f.off+3*k+2]+=dz;
}

// ================= three.js scène =================
const canvas=document.getElementById('c3d');
const renderer=new THREE.WebGLRenderer({canvas,antialias:true});
const scene=new THREE.Scene();scene.background=new THREE.Color(0x0B1020);
// Subtiele verlichting voorkomt dat transparante MeshPhysicalMaterial-buizen zwart renderen.
scene.add(new THREE.HemisphereLight(0xBFDFFF,0x101526,0.82));
const keyLight=new THREE.DirectionalLight(0xFFFFFF,0.72);keyLight.position.set(1.4,-1.0,1.8);scene.add(keyLight);
const camera=new THREE.PerspectiveCamera(45,1,0.01,20);
let camTh=0.9,camPh=1.15,camD=1.6;
const camTarget=new THREE.Vector3(0,0,0);
function updCam(){
  camera.position.set(
    camTarget.x+camD*Math.sin(camPh)*Math.cos(camTh),
    camTarget.y+camD*Math.sin(camPh)*Math.sin(camTh),
    camTarget.z+camD*Math.cos(camPh));
  camera.up.set(0,0,1);camera.lookAt(camTarget);
}
const worldGrp=new THREE.Group();scene.add(worldGrp);
const filGrp=new THREE.Group();scene.add(filGrp);   // filament-frame (Y-coördinaten)
const volumeGrp=new THREE.Group();scene.add(volumeGrp);
let cylMesh=null, endRings=[], footprintDiscs=[];

function disposeMesh(m){
  if(!m)return;
  if(m.geometry)m.geometry.dispose();
  if(m.material){
    if(Array.isArray(m.material))m.material.forEach(x=>x.dispose());
    else m.material.dispose();
  }
}
function hybridRangeFromInput(input,value=Number(input.value)||0){
  if(input.dataset.scale!=='log')return value;
  const lo=Math.max(Number.MIN_VALUE,Number(input.dataset.logMin)||1e-4);
  const hi=Math.max(lo*1.000001,Number(input.max)||1);
  if(value<=0)return 0;
  return 1+999*Math.log(clamp(value,lo,hi)/lo)/Math.log(hi/lo);
}
function hybridInputFromRange(input,sliderValue){
  if(input.dataset.scale!=='log')return Number(sliderValue);
  const lo=Math.max(Number.MIN_VALUE,Number(input.dataset.logMin)||1e-4);
  const hi=Math.max(lo*1.000001,Number(input.max)||1);
  const u=Number(sliderValue);
  if(u<=0)return 0;
  return lo*Math.pow(hi/lo,(u-1)/999);
}
function formatHybridInputValue(input,value){
  if(input.dataset.scale!=='log')return String(value);
  if(value===0)return '0';
  if(value<0.001)return value.toFixed(7).replace(/0+$/,'').replace(/\.$/,'');
  if(value<0.1)return value.toFixed(5).replace(/0+$/,'').replace(/\.$/,'');
  if(value<10)return value.toFixed(4).replace(/0+$/,'').replace(/\.$/,'');
  return value.toFixed(3).replace(/0+$/,'').replace(/\.$/,'');
}
function syncHybridNumberInputs(){
  document.querySelectorAll('input.param-number').forEach(input=>{
    const range=input.closest('.param-hybrid')?.querySelector('input.param-slider');
    if(range)range.value=String(hybridRangeFromInput(input));
  });
}

function updateStretchReadout(){
  const b=document.getElementById('bLinkDH');
  const out=document.getElementById('vStretch');
  if(!b||!out)return;
  b.classList.toggle('active',P.linkDH);
  b.setAttribute('aria-pressed',String(P.linkDH));
  b.textContent=P.linkDH?'🔗 D↔H · V constant':'⛓ D / H los';
  if(P.linkDH){
    const lr=P.Rcyl/Math.max(1e-12,P.linkRefR);
    const lz=P.Hcyl/Math.max(1e-12,P.linkRefH);
    out.textContent=`tracers: λr=${lr.toFixed(3)} · λz=${lz.toFixed(3)} · λr²λz=${(lr*lr*lz).toFixed(3)} · knopen 1:1`;
  }else{
    out.textContent='onafhankelijke cilinderafmetingen · knopen onvervormd';
  }
}

function scaleVolumeContents(radialScale,axialScale){
  if(!Number.isFinite(radialScale)||!Number.isFinite(axialScale)||radialScale<=0||axialScale<=0)return;

  // Alleen het coarse-grained volume en de passieve tracers volgen de
  // opgelegde cilindervorm. De vortexfilamenten Y blijven in fysieke
  // coördinaten onveranderd: een wijziging van het kijk-/volume-kader is
  // geen constitutieve vortexrek. Werkelijke filamentrek moet uit de
  // Biot--Savart/LIA-dynamica zelf ontstaan.
  if(trArr){
    for(let i=0;i<trArr.length;i+=3){
      trArr[i]*=radialScale;
      trArr[i+1]*=radialScale;
      trArr[i+2]*=axialScale;
    }
    if(trGeo?.attributes?.position)trGeo.attributes.position.needsUpdate=true;
  }
}

function applyVolumeResize(newR,newH){
  newR=clamp(newR,0.025,1.0);
  newH=clamp(newH,0.025,2.5);
  const oldR=Math.max(1e-12,P.Rcyl), oldH=Math.max(1e-12,P.Hcyl);
  if(Math.abs(newR-oldR)<1e-12 && Math.abs(newH-oldH)<1e-12)return;
  scaleVolumeContents(newR/oldR,newH/oldH);
  P.Rcyl=newR;
  P.Hcyl=newH;
  rebuildVolumeEnvelope();
  syncGhostRing();
  rebuildLines();
  rebuildTubes(true);
  updateIndicators(tPhys);
  syncUi();
}

function rebuildVolumeEnvelope(){
  // Oude cap-footprints leven in filGrp en moeten apart worden opgeruimd.
  footprintDiscs.forEach(d=>{filGrp.remove(d);disposeMesh(d);});
  while(volumeGrp.children.length){
    const c=volumeGrp.children.pop();
    disposeMesh(c);
  }
  cylMesh=null; endRings=[]; footprintDiscs=[];
  const cylGeo=new THREE.CylinderGeometry(P.Rcyl,P.Rcyl,cylinderHeight(),48,1,true);
  cylGeo.rotateX(Math.PI/2);
  cylMesh=new THREE.Mesh(cylGeo,new THREE.MeshBasicMaterial({color:0x1E2C4A,wireframe:true,transparent:true,opacity:0.32}));
  volumeGrp.add(cylMesh);
  for(const z of [zMin(),zMax()]){
    const pts=[];
    for(let k=0;k<=64;k++){const th=2*Math.PI*k/64;
      pts.push(new THREE.Vector3(P.Rcyl*Math.cos(th),P.Rcyl*Math.sin(th),z));}
    const ring=new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts),
      new THREE.LineBasicMaterial({color:0x2A4A7A,transparent:true,opacity:0.6}));
    volumeGrp.add(ring); endRings.push(ring);
  }
  const rFp=P.Rcyl*0.25;
  for(const z of [zMin(),zMax()]){
    const d=new THREE.Mesh(new THREE.RingGeometry(rFp*0.92,rFp,48),
      new THREE.MeshBasicMaterial({color:0x55D6FF,transparent:true,opacity:0.55,side:THREE.DoubleSide}));
    d.position.set(0,0,z); d.visible=false; filGrp.add(d); footprintDiscs.push(d);
  }
  rebuildLattice();
  rebuildFrameBackdrop();
  if(typeof camTarget!=="undefined") camTarget.z=0;
  const gunInset=Math.min(0.01,0.02*cylinderHeight());
  if(typeof gunA!=="undefined") gunA.position.z=zMin()+gunInset;
  if(typeof gunB!=="undefined") gunB.position.z=zMax()-gunInset;
  if(P.linkDH) P.linkVolumeRef=cylinderVolume();
  updateHeaderTitle();
}
// vortexrooster (representatief, hex-gepakt, aantal ∝ |Ω|)
// De lijnen representeren coarse-grained axiale vorticiteit, niet individuele canonieke SST-kernen.
// Fictieve inertiaalcilinder: alleen zichtbaar in het roterende frame.
// Hij staat bewust buiten de flowcilinder en is geen fysieke wand.
const frameBackdropGrp=new THREE.Group();scene.add(frameBackdropGrp);
const latticeGrp=new THREE.Group();worldGrp.add(latticeGrp);
function disposeGroupChildren(group){
  while(group.children.length){const c=group.children.pop();if(c.geometry)c.geometry.dispose();if(c.material)c.material.dispose();}
}
function rebuildFrameBackdrop(){
  disposeGroupChildren(frameBackdropGrp);
  const color=new THREE.Color(P.vorticityLineColor||'#0F1A29');
  const rOuter=P.Rcyl*1.09;
  const z0=zMin(),z1=zMax();
  // Uitsluitend verticale markers op een fictieve buitencilinder. Een bewust
  // ongelijke helderheidsverdeling doorbreekt de rotatiesymmetrie, zodat
  // draairichting en snelheid in het roterende frame zichtbaar blijven.
  const markerCount=16;
  for(let i=0;i<markerCount;i++){
    const th=2*Math.PI*i/markerCount;
    const x=rOuter*Math.cos(th),y=rOuter*Math.sin(th);
    const pts=[new THREE.Vector3(x,y,z0),new THREE.Vector3(x,y,z1)];
    const major=(i===0),secondary=(i===5||i===11);
    const opacity=major?0.88:(secondary?0.48:0.20);
    const mat=new THREE.LineBasicMaterial({color,transparent:true,opacity,depthWrite:false});
    const line=new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts),mat);
    line.renderOrder=2;
    frameBackdropGrp.add(line);
  }
  frameBackdropGrp.visible=!!P.coRot;
}
function rebuildLattice(){
  while(latticeGrp.children.length){const c=latticeGrp.children.pop();c.geometry.dispose();c.material.dispose();}
  if(P.bundleEnabled){
    rebuildBundleLines();
    return;
  }
  const target=Math.min(90,Math.round(40*Math.abs(P.Om)));
  if(target<1)return;
  const r=0.93*P.Rcyl;
  const d=Math.sqrt(2*Math.PI*r*r/(Math.sqrt(3)*target));
  const rows=Math.ceil(2*r/(d*Math.sqrt(3)/2));
  let n=0;
  for(let j=-rows;j<=rows&&n<target+10;j++){
    const yy=j*d*Math.sqrt(3)/2;
    for(let i=-rows;i<=rows;i++){
      const xx=i*d+(j&1?d/2:0);
      if(xx*xx+yy*yy>r*r)continue;
      const op=0.3+0.28*((Math.sin(i*12.9898+j*78.233)*43758.5453)%1+1)%1;
      const g=new THREE.BufferGeometry().setFromPoints(
        [new THREE.Vector3(xx,yy,zMin()+0.01),new THREE.Vector3(xx,yy,zMax()-0.01)]);
      latticeGrp.add(new THREE.Line(g,new THREE.LineBasicMaterial({color:new THREE.Color(P.vorticityLineColor||'#0F1A29'),transparent:true,opacity:op})));
      n++;
    }
  }
}

function rebuildBundleLines(){
  if(!P.bundleEnabled)return;
  const target=clamp(Math.round(P.bundleVisualLines||61),7,121);
  const ex=bundleScaleExtrema();
  const rBase=bundleReferenceRadius()/Math.max(ex.hi,1e-12);
  const segments=P.bundleProfile==='parallel'?1:40;
  const color=new THREE.Color(P.vorticityLineColor||'#0F1A29');
  for(let i=0;i<target;i++){
    const ang=2*Math.PI*i/target;
    const pts=[];
    for(let k=0;k<=segments;k++){
      const u=k/segments;
      const z=zMin()+0.01+u*Math.max(0,cylinderHeight()-0.02);
      const lam=bundleScaleAtU(u);
      const r=rBase*lam;
      pts.push(new THREE.Vector3(r*Math.cos(ang),r*Math.sin(ang),z));
    }
    const op=0.22+0.52*((Math.sin(i*12.9898)*43758.5453)%1+1)%1;
    const g=new THREE.BufferGeometry().setFromPoints(pts);
    latticeGrp.add(new THREE.Line(g,new THREE.LineBasicMaterial({color,transparent:true,opacity:op})));
  }
}
// pistolen op de as
const gunGrp=new THREE.Group();worldGrp.add(gunGrp);
function gun(z,flip,color){
  const g=new THREE.ConeGeometry(0.02,0.05,16);g.rotateX(flip?Math.PI/2:-Math.PI/2);
  const m=new THREE.Mesh(g,new THREE.MeshBasicMaterial({color}));
  m.position.set(0,0,z);gunGrp.add(m);return m;
}
const gunA=gun(zMin()+0.01,false,0xFFAE45), gunB=gun(zMax()-0.01,true,0x55D6FF);

// ================= uitgebreide 3D visualisatie (collider features) =================
class DynCurve extends THREE.Curve{
  constructor(f){super();this.f=f;}
  getPoint(t,op=new THREE.Vector3()){
    const N=this.f.N,o=this.f.off;let i=Math.floor(t*N),fr=t*N-i;if(i>=N){i=N-1;fr=1;}
    const i2=(i+1)%N,s=o+3*i,s2=o+3*i2;
    return op.set(Y[s]+fr*(Y[s2]-Y[s]),Y[s+1]+fr*(Y[s2+1]-Y[s+1]),Y[s+2]+fr*(Y[s2+2]-Y[s+2]));
  }
}
const matSolidA=new THREE.MeshPhysicalMaterial({color:0xFFAE45,metalness:0.22,roughness:0.25,transparent:true,opacity:P.vortexOpacity,depthWrite:false});
const matSolidB=new THREE.MeshPhysicalMaterial({color:0x55D6FF,metalness:0.22,roughness:0.25,transparent:true,opacity:P.vortexOpacity,depthWrite:false});
const matHolA=new THREE.MeshPhysicalMaterial({color:0xFFAE45,transmission:0.92,transparent:true,opacity:Math.min(0.48,P.vortexOpacity),roughness:0.1,depthWrite:false});
const matHolB=new THREE.MeshPhysicalMaterial({color:0x55D6FF,transmission:0.92,transparent:true,opacity:Math.min(0.48,P.vortexOpacity),roughness:0.1,depthWrite:false});
function updateVortexOpacity(){
  const op=clamp(Number(P.vortexOpacity)||0.58,0.05,1);
  matSolidA.opacity=matSolidB.opacity=op;
  matHolA.opacity=matHolB.opacity=Math.min(0.52,op);
  [matSolidA,matSolidB,matHolA,matHolB].forEach(m=>{m.transparent=true;m.depthWrite=false;m.needsUpdate=true;});
  if(typeof lineObjs!=='undefined')lineObjs.forEach(l=>{if(l.material){l.material.transparent=true;l.material.opacity=Math.max(0.18,op);l.material.depthWrite=false;}});
  if(typeof wireObjs!=='undefined')wireObjs.forEach(l=>{if(l.material){l.material.transparent=true;l.material.opacity=Math.max(0.2,0.78*op);l.material.depthWrite=false;}});
}
const flowMat=new THREE.MeshBasicMaterial({color:0xA855F7,wireframe:true,transparent:true,opacity:0.3});
const betaMat=new THREE.MeshBasicMaterial({color:0xfacc15,wireframe:true,transparent:true,opacity:0.55});
// ===== deeltjeswolk: passieve tracers geadvecteerd door het echte BS-veld =====
const TRACER_COUNT_MAX=5000;
const TR_HUE_SLOW=0.33;       // groen
const TR_HUE_EQUAL=0.53;      // cyaan
const TR_HUE_FAST=0.78;       // paars
let trGeo=null,trPts=null,trArr=null,trColArr=null,trOmegaDeltaArr=null;
let trOmegaP90=0,trOmegaColorScale=1;
const trColorTmp=new THREE.Color();
function setTracerHue(i,normalizedDelta){
  // normalizedDelta in [-1,1]: negatief = lager/tegenroterend,
  // positief = sneller in de draairichting van de cilinder.
  const q=clamp(normalizedDelta,-1,1);
  const hue=q<0
    ?TR_HUE_EQUAL+(TR_HUE_SLOW-TR_HUE_EQUAL)*(-q)
    :TR_HUE_EQUAL+(TR_HUE_FAST-TR_HUE_EQUAL)*q;
  const light=0.54+0.10*Math.abs(q);
  trColorTmp.setHSL(clamp(hue,0,1),0.96,light);
  trColArr[3*i]=trColorTmp.r;
  trColArr[3*i+1]=trColorTmp.g;
  trColArr[3*i+2]=trColorTmp.b;
}
function tracerColumnGeometry(){
  let cx=0,cy=0,rHole=Math.max(0.01,0.20*P.Rcyl);
  if(Y&&fils.length){
    const group=carrierFilaments('A');
    const st=carrierGroupStats('A');
    cx=st.cx;cy=st.cy;
    const radial=[];
    for(const f of group)for(let k=0;k<f.N;k++){
      radial.push(Math.hypot(Y[f.off+3*k]-cx,Y[f.off+3*k+1]-cy));
    }
    radial.sort((a,b)=>a-b);
    if(radial.length){
      // Robuuste inner-envelope proxy: P15 voorkomt dat één bijna-axiaal
      // samplepunt het centrale gat kunstmatig tot nul reduceert.
      const rInner=radial[Math.min(radial.length-1,Math.floor(0.15*(radial.length-1)))];
      const tubeClearance=Math.max(P.a*2.5,0.002);
      rHole=clamp(rInner-tubeClearance,0.005,0.90*P.Rcyl);
    }
  }
  return {cx,cy,rHole};
}
function respawnTracer(i,columnGeom=null){
  const useColumn=P.tracerSpawnMode==='column';
  const geom=useColumn?(columnGeom||tracerColumnGeometry()):{cx:0,cy:0,rHole:P.Rcyl*0.95};
  const r=Math.sqrt(Math.random())*geom.rHole, th=Math.random()*2*Math.PI;
  trArr[3*i]=geom.cx+r*Math.cos(th);trArr[3*i+1]=geom.cy+r*Math.sin(th);
  const margin=Math.min(0.02,0.04*P.Hcyl);
  trArr[3*i+2]=zMin()+margin+Math.random()*Math.max(1e-6,cylinderHeight()-2*margin);
  if(trOmegaDeltaArr)trOmegaDeltaArr[i]=0;
  if(trColArr)setTracerHue(i,0);
}
function resetParticlesToTaylorColumn(){
  P.tracerSpawnMode='column';
  if(!trArr||tracerCount()!==P.tracerCount)initTracers();
  if(!trArr)return;
  const geom=tracerColumnGeometry();
  const n=tracerCount();
  for(let i=0;i<n;i++)respawnTracer(i,geom);
  trOmegaP90=0;trOmegaColorScale=1;
  if(trGeo?.attributes?.position)trGeo.attributes.position.needsUpdate=true;
  if(trGeo?.attributes?.color)trGeo.attributes.color.needsUpdate=true;
  const btn=document.getElementById('bResetParticles');
  if(btn){
    btn.textContent=`↺ Deeltjeskolom · r ≈ ${(geom.rHole*100).toFixed(1)} cm`;
    window.setTimeout(()=>{btn.textContent='↺ Reset deeltjes · Taylor-kolom';},1800);
  }
}
function tracerCount(){
  return trArr ? Math.floor(trArr.length/3) : Math.max(0,Math.min(TRACER_COUNT_MAX,Math.round(P.tracerCount||0)));
}
function disposeTracers(){
  if(trPts){
    filGrp.remove(trPts);
    if(trPts.geometry)trPts.geometry.dispose();
    if(trPts.material)trPts.material.dispose();
  }
  trGeo=null;trPts=null;trArr=null;trColArr=null;trOmegaDeltaArr=null;
}
function initTracers(){
  disposeTracers();
  const n=Math.max(0,Math.min(TRACER_COUNT_MAX,Math.round(P.tracerCount||0)));
  P.tracerCount=n;
  if(n===0){
    const h=document.getElementById('hTracerOmega');
    if(h)h.textContent='— (0 deeltjes)';
    return;
  }
  trArr=new Float32Array(n*3);
  trColArr=new Float32Array(n*3);
  trOmegaDeltaArr=new Float32Array(n);
  const spawnGeom=P.tracerSpawnMode==='column'?tracerColumnGeometry():null;
  for(let i=0;i<n;i++)respawnTracer(i,spawnGeom);
  trGeo=new THREE.BufferGeometry();
  trGeo.setAttribute('position',new THREE.BufferAttribute(trArr,3));
  trGeo.setAttribute('color',new THREE.BufferAttribute(trColArr,3));
  trPts=new THREE.Points(trGeo,new THREE.PointsMaterial({size:P.particleSize,vertexColors:true,
    sizeAttenuation:true,transparent:true,opacity:0.82,depthWrite:false,blending:THREE.AdditiveBlending}));
  filGrp.add(trPts);
}
function updateTracerColorScale(){
  // Gebruik P90 in plaats van het maximum, zodat één core-near outlier
  // niet de hele wolk cyaan drukt. Dit is alleen een visuele contrastschaal;
  // de fysieke ΔΩ-P90 wordt afzonderlijk in de HUD getoond.
  const n=tracerCount();
  if(n===0)return;
  const absVals=new Array(n);
  for(let i=0;i<n;i++)absVals[i]=Math.abs(trOmegaDeltaArr[i]);
  absVals.sort((a,b)=>a-b);
  trOmegaP90=absVals[Math.min(n-1,Math.floor(0.90*(n-1)))]||0;
  const omegaCylinder=Math.abs(P.Om);
  const minimumScale=Math.max(1e-4,0.005*Math.max(1,omegaCylinder));
  const targetScale=Math.max(minimumScale,trOmegaP90);
  trOmegaColorScale=Number.isFinite(trOmegaColorScale)
    ?0.78*trOmegaColorScale+0.22*targetScale
    :targetScale;
  const scale=Math.max(minimumScale,trOmegaColorScale);
  for(let i=0;i<n;i++){
    // tanh geeft een duidelijke, maar vloeiende kleurrespons rond ΔΩ=0.
    setTracerHue(i,Math.tanh(1.45*trOmegaDeltaArr[i]/scale));
  }
  const h=document.getElementById('hTracerOmega');
  if(h)h.textContent=`${trOmegaP90.toFixed(trOmegaP90<0.1?3:2)} / ±${scale.toFixed(scale<0.1?3:2)} s⁻¹`;
}
function stepTracers(dtSim){
  if(!trPts)return;
  trPts.visible=P.showTracers&&!P.showStreamlines;
  if(!P.showTracers||P.showStreamlines||!Y||!fils.length||dtSim===0)return;
  const n=tracerCount();
  if(n===0)return;
  const a2=P.a*P.a, segs=[];
  for(const f of fils){
    const N=f.N,o=f.off,mid=new Float64Array(3*N),dl=new Float64Array(3*N);
    for(let k=0;k<N;k++){const k2=(k+1)%N;
      for(let d=0;d<3;d++){mid[3*k+d]=.5*(Y[o+3*k+d]+Y[o+3*k2+d]);dl[3*k+d]=Y[o+3*k2+d]-Y[o+3*k+d];}}
    segs.push({N,mid,dl,pref:filamentGamma(f)/(4*Math.PI)});
  }
  const wz=effectiveW();
  const respawnGeom=P.tracerSpawnMode==='column'?tracerColumnGeometry():null;
  for(let i=0;i<n;i++){
    const px=trArr[3*i],py=trArr[3*i+1],pz=trArr[3*i+2];
    let ux=0,uy=0,uz=wz;
    for(const sg of segs){const M=sg.N,mid=sg.mid,dl=sg.dl,pref=sg.pref;
      for(let j=0;j<M;j++){
        const rx=px-mid[3*j],ry=py-mid[3*j+1],rz=pz-mid[3*j+2];
        const r2=rx*rx+ry*ry+rz*rz+a2, inv=pref/(r2*Math.sqrt(r2));
        ux+=(dl[3*j+1]*rz-dl[3*j+2]*ry)*inv;
        uy+=(dl[3*j+2]*rx-dl[3*j]*rz)*inv;
        uz+=(dl[3*j]*ry-dl[3*j+1]*rx)*inv;}}
    const omegaBgIsInVelocity=P.bgOmegaCoupling&&!P.coRot;
    if(omegaBgIsInVelocity){ux+=-P.Om*py;uy+=P.Om*px;}

    // Orbitale tracer-hoeksnelheid rond de z-as:
    // Ω_p,z = (r × u)_z / r_perp².
    // De kleur gebruikt ΔΩ = Ω_p,lab - Ω_cilinder in de draairichting
    // van de cilinder. Daarmee reageert de wolk direct op Γ, lokale
    // Biot-Savart-inductie en de achtergrondrotatie.
    const r2xy=px*px+py*py;
    let omegaFromIntegratedVelocity=0;
    if(r2xy>1e-10)omegaFromIntegratedVelocity=(px*uy-py*ux)/r2xy;
    const omegaLab=omegaFromIntegratedVelocity+(omegaBgIsInVelocity?0:P.Om);
    const spinDir=Math.sign(P.Om)||1;
    trOmegaDeltaArr[i]=spinDir*omegaLab-Math.abs(P.Om);

    let dx=ux*dtSim,dy=uy*dtSim,dz=uz*dtSim;
    const dm=Math.hypot(dx,dy,dz);
    if(dm>0.03){const sc=0.03/dm;dx*=sc;dy*=sc;dz*=sc;}
    const nx=px+dx,ny=py+dy,nz=pz+dz;
    const radialOut=nx*nx+ny*ny>Math.pow(0.98*P.Rcyl,2);
    const zLo=zMin(),zHi=zMax();
    if(radialOut){
      respawnTracer(i,respawnGeom);
    }else if(nz<zLo||nz>=zHi){
      if(P.tracerWrapZ){
        const span=Math.max(1e-9,zHi-zLo);
        const wrapped=zLo+(((nz-zLo)%span)+span)%span;
        trArr[3*i]=nx;trArr[3*i+1]=ny;trArr[3*i+2]=wrapped;
      }else{
        respawnTracer(i,respawnGeom);
      }
    }else{
      trArr[3*i]=nx;trArr[3*i+1]=ny;trArr[3*i+2]=nz;
    }
  }
  updateTracerColorScale();
  trGeo.attributes.position.needsUpdate=true;
  trGeo.attributes.color.needsUpdate=true;
}

// ===== instantane stroomlijnen + Bernoulli-drukproxy =====
// Stroomlijnen zijn tangent aan het snelheidsveld. De kleur gebruikt slechts de
// relatieve Bernoulli-proxy p_B*=p0-1/2 rho |u|^2; de additieve drukconstante is onbekend.
const streamlineGrp=new THREE.Group();filGrp.add(streamlineGrp);
let streamlineTick=0;
function clearStreamlines(){
  while(streamlineGrp.children.length){
    const o=streamlineGrp.children.pop();
    if(o.geometry)o.geometry.dispose();
    if(o.material)o.material.dispose();
  }
}
function fieldSegments(){
  const segs=[];
  for(const f of fils){
    const N=f.N,o=f.off,mid=new Float64Array(3*N),dl=new Float64Array(3*N);
    for(let k=0;k<N;k++){
      const k2=(k+1)%N;
      for(let d=0;d<3;d++){
        mid[3*k+d]=0.5*(Y[o+3*k+d]+Y[o+3*k2+d]);
        dl[3*k+d]=Y[o+3*k2+d]-Y[o+3*k+d];
      }
    }
    segs.push({N,mid,dl,pref:filamentGamma(f)/(4*Math.PI)});
  }
  return segs;
}
function fieldVelocityAt(px,py,pz,segs){
  let ux=0,uy=0,uz=effectiveW();
  const a2=P.a*P.a;
  for(const sg of segs){
    for(let j=0;j<sg.N;j++){
      const rx=px-sg.mid[3*j],ry=py-sg.mid[3*j+1],rz=pz-sg.mid[3*j+2];
      const r2=rx*rx+ry*ry+rz*rz+a2;
      const inv=sg.pref/(r2*Math.sqrt(r2));
      ux+=(sg.dl[3*j+1]*rz-sg.dl[3*j+2]*ry)*inv;
      uy+=(sg.dl[3*j+2]*rx-sg.dl[3*j]*rz)*inv;
      uz+=(sg.dl[3*j]*ry-sg.dl[3*j+1]*rx)*inv;
    }
  }
  if(P.bgOmegaCoupling&&!P.coRot){ux+=-P.Om*py;uy+=P.Om*px;}
  return {ux,uy,uz,speed:Math.hypot(ux,uy,uz)};
}
function insideCylinder(x,y,z){return x*x+y*y<0.9409*P.Rcyl*P.Rcyl&&z>zMin()+0.002&&z<zMax()-0.002;}
function traceStreamline(seed,sign,segs,steps,ds){
  const pts=[],speeds=[];
  let x=seed.x,y=seed.y,z=seed.z;
  for(let k=0;k<steps;k++){
    if(!insideCylinder(x,y,z))break;
    const v1=fieldVelocityAt(x,y,z,segs);
    if(v1.speed<1e-10)break;
    pts.push(new THREE.Vector3(x,y,z));speeds.push(v1.speed);
    const h=sign*ds/v1.speed;
    const mx=x+0.5*h*v1.ux,my=y+0.5*h*v1.uy,mz=z+0.5*h*v1.uz;
    const vm=fieldVelocityAt(mx,my,mz,segs);
    if(vm.speed<1e-10)break;
    x+=sign*ds*vm.ux/vm.speed;
    y+=sign*ds*vm.uy/vm.speed;
    z+=sign*ds*vm.uz/vm.speed;
  }
  return {pts,speeds};
}
function pressureProxyColor(q,out){
  const hue=0.53*(1-q)+0.02*q; // cyaan (hogere p*) -> magenta/oranje (lagere p*)
  return out.setHSL(hue,0.88,0.58);
}
function rebuildStreamlines(force=false){
  streamlineGrp.visible=P.showTracers&&P.showStreamlines;
  if(!streamlineGrp.visible||!Y||!fils.length){if(force)clearStreamlines();return;}
  streamlineTick++;
  if(!force&&streamlineTick%12!==0)return;
  clearStreamlines();
  const segs=fieldSegments();
  const nLines=Math.max(4,Math.min(120,Math.round(P.streamlineCount||28))),steps=42;
  const ds=Math.max(0.001,Math.min(0.018,0.045*P.Rcyl,0.018*cylinderHeight()));
  const geom=tracerColumnGeometry(),all=[];
  for(let i=0;i<nLines;i++){
    const frac=(i+0.5)/nLines,ring=i%7;
    const r=geom.rHole*(0.08+0.80*(ring/6)),th=i*2.399963229728653;
    const seed={x:geom.cx+r*Math.cos(th),y:geom.cy+r*Math.sin(th),z:zMin()+0.06*cylinderHeight()+0.88*cylinderHeight()*frac};
    const back=traceStreamline(seed,-1,segs,steps,ds),fore=traceStreamline(seed,+1,segs,steps,ds);
    const pts=back.pts.reverse().concat(fore.pts.slice(1));
    const speeds=back.speeds.reverse().concat(fore.speeds.slice(1));
    if(pts.length>2)all.push({pts,speeds});
  }
  const speedPool=all.flatMap(x=>x.speeds).sort((a,b)=>a-b);
  const speed95=speedPool.length?speedPool[Math.floor(0.95*(speedPool.length-1))]:1;
  const c=new THREE.Color();
  for(const sl of all){
    const pos=new Float32Array(sl.pts.length*3),col=new Float32Array(sl.pts.length*3);
    sl.pts.forEach((pt,i)=>{
      pos[3*i]=pt.x;pos[3*i+1]=pt.y;pos[3*i+2]=pt.z;
      pressureProxyColor(clamp(sl.speeds[i]/Math.max(1e-12,speed95),0,1),c);
      col[3*i]=c.r;col[3*i+1]=c.g;col[3*i+2]=c.b;
    });
    const g=new THREE.BufferGeometry();
    g.setAttribute('position',new THREE.BufferAttribute(pos,3));g.setAttribute('color',new THREE.BufferAttribute(col,3));
    streamlineGrp.add(new THREE.Line(g,new THREE.LineBasicMaterial({vertexColors:true,transparent:true,opacity:0.72,depthWrite:false,blending:THREE.AdditiveBlending})));
  }
}

let lineObjs=[], tubeObjs=[], wireObjs=[], betaObjs=[], flowObjs=[], ghostTubeObj=null;
let sepObjs=[], capDiscs=[], capRings=[], colSils=[], alphaObjs=[];
let stewartsonTorus=null, stewartsonArrows=null;
const ghostTubeMat=new THREE.MeshBasicMaterial({color:0x66CCFF,wireframe:true,transparent:true,opacity:0.38,depthWrite:false});
// Step 3: make the Taylor-column overlays deliberately subtle so they do not
// obscure the filament or tracer field.  Centralised values make later tuning easy.
const TAYLOR_VIS_ALPHA = Object.freeze({
  separatrixFill: 0.055,
  separatrixEdge: 0.24,
  capDisc: 0.10,
  capRing: 0.32,
  columnWire: 0.055,
  stewartsonTorus: 0.105,
  stewartsonArrows: 0.55,
  footprintDisc: 0.20
});
const stewartsonMat=new THREE.MeshBasicMaterial({color:0xFF7043,transparent:true,opacity:TAYLOR_VIS_ALPHA.stewartsonTorus,side:THREE.DoubleSide,depthWrite:false});
const stewartsonMatNeg=new THREE.MeshBasicMaterial({color:0x26C6DA,transparent:true,opacity:TAYLOR_VIS_ALPHA.stewartsonTorus,side:THREE.DoubleSide,depthWrite:false});
let meshFrame=0;

function disposeObj(m){if(!m)return;filGrp.remove(m);if(m.geometry)m.geometry.dispose();}
function makeWire(color){
  const g=new THREE.BufferGeometry();
  g.setAttribute('position',new THREE.BufferAttribute(new Float32Array(1536),3));
  const l=new THREE.LineLoop(g,new THREE.LineBasicMaterial({color}));
  l.visible=false;filGrp.add(l);return l;
}
function makeSepSphere(){
  const m=new THREE.Mesh(new THREE.SphereGeometry(1,24,24),
    new THREE.MeshBasicMaterial({color:0xffffff,transparent:true,opacity:TAYLOR_VIS_ALPHA.separatrixFill,depthWrite:false}));
  m.add(new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.SphereGeometry(1,12,12)),
    new THREE.LineBasicMaterial({color:0xffffff,transparent:true,opacity:TAYLOR_VIS_ALPHA.separatrixEdge})));
  m.visible=false;filGrp.add(m);return m;
}
function makeCapDisc(color){
  const m=new THREE.Mesh(new THREE.CircleGeometry(1,48),
    new THREE.MeshBasicMaterial({color,transparent:true,opacity:TAYLOR_VIS_ALPHA.capDisc,side:THREE.DoubleSide,depthWrite:false}));
  m.visible=false;filGrp.add(m);return m;
}
function makeCapRing(color){
  const m=new THREE.Mesh(new THREE.RingGeometry(0.92,1,48),
    new THREE.MeshBasicMaterial({color,transparent:true,opacity:TAYLOR_VIS_ALPHA.capRing,side:THREE.DoubleSide,depthWrite:false}));
  m.visible=false;filGrp.add(m);return m;
}
function makeColSil(color){
  const g=new THREE.CylinderGeometry(1,1,1,24,1,true);g.rotateX(Math.PI/2);
  const m=new THREE.Mesh(g,new THREE.MeshBasicMaterial({color,wireframe:true,transparent:true,opacity:TAYLOR_VIS_ALPHA.columnWire,depthWrite:false}));
  m.visible=false;filGrp.add(m);return m;
}
function initVisExtras(){
  sepObjs=[makeSepSphere(),makeSepSphere()];
  capDiscs=[makeCapDisc(0xFFAE45),makeCapDisc(0xFFAE45),makeCapDisc(0x55D6FF),makeCapDisc(0x55D6FF)];
  capRings=[makeCapRing(0xFFAE45),makeCapRing(0xFFAE45),makeCapRing(0x55D6FF),makeCapRing(0x55D6FF)];
  colSils=[makeColSil(0xFFAE45),makeColSil(0x55D6FF)];
  alphaObjs=[new THREE.Mesh(new THREE.SphereGeometry(1,16,16),
    new THREE.MeshBasicMaterial({color:0xFF6E6E,transparent:true,opacity:0.8})),
    new THREE.Mesh(new THREE.SphereGeometry(1,16,16),
    new THREE.MeshBasicMaterial({color:0xFF6E6E,transparent:true,opacity:0.8}))];
  alphaObjs.forEach(m=>{m.visible=false;filGrp.add(m);});
  const torGeo=new THREE.CylinderGeometry(1,1,1,48,1,true);
  torGeo.rotateX(Math.PI/2);
  stewartsonTorus=new THREE.Mesh(torGeo,stewartsonMat.clone());
  stewartsonTorus.visible=false;filGrp.add(stewartsonTorus);
  stewartsonArrows=new THREE.InstancedMesh(new THREE.ConeGeometry(0.007,0.022,8),
    new THREE.MeshBasicMaterial({color:0xFFB74D,transparent:true,opacity:TAYLOR_VIS_ALPHA.stewartsonArrows,depthWrite:false}),12);
  stewartsonArrows.visible=false;filGrp.add(stewartsonArrows);
  initChiArrows();
}
function initChiArrows(){
  chiArrows=[];
  for(let i=0;i<2;i++){
    const col=i===0?0xFFAE45:0x55D6FF;
    const a=new THREE.ArrowHelper(new THREE.Vector3(1,0,0),new THREE.Vector3(),0.06,col,0.018,0.01);
    a.visible=false;filGrp.add(a);chiArrows.push(a);
  }
}
function updateChiArrows(bodyStates){
  chiArrows.forEach((a,i)=>{
    if(!P.showChiArrow||i>=fils.length||!bodyStates[i]){
      a.visible=false;return;
    }
    const b=bodyStates[i];
    if(!b.chi){a.visible=false;return;}
    const len=0.035+0.1*Math.min(1,Math.abs(b.omegaZ)*2);
    a.position.set(b.cx,b.cy,b.cz);
    a.setDirection(new THREE.Vector3(b.chi.x,b.chi.y,0.001).normalize());
    a.setLength(Math.max(0.02,len),0.018,0.01);
    a.visible=true;
  });
}
initVisExtras();
applyDvOpacity();
initTracers();

function rebuildLines(){
  [...lineObjs,...tubeObjs,...wireObjs,...betaObjs,...flowObjs].forEach(o=>{
    filGrp.remove(o);if(o.geometry)o.geometry.dispose();});
  lineObjs=[];tubeObjs=[];wireObjs=[];betaObjs=[];flowObjs=[];
  const cols=[0xFFAE45,0x55D6FF];
  fils.forEach((f,i)=>{
    const geo=new THREE.BufferGeometry();
    geo.setAttribute('position',new THREE.BufferAttribute(new Float32Array(3*(f.N+1)),3));
    const l=new THREE.Line(geo,new THREE.LineBasicMaterial({color:cols[i%2],transparent:true,opacity:Math.max(0.18,P.vortexOpacity),depthWrite:false}));
    l.visible=(P.vis==='line');filGrp.add(l);lineObjs.push(l);
    wireObjs.push(makeWire(cols[i%2]));
  });
  gunB.visible=(P.mode==='botsing');
  meshFrame=0;
  updateVortexOpacity();
  rebuildStreamlines(true);
}
function pushLines(){
  fils.forEach((f,i)=>{
    if(lineObjs[i]){
      const p=lineObjs[i].geometry.attributes.position.array;
      for(let k=0;k<=f.N;k++){const s=f.off+(k%f.N)*3;
        p[3*k]=Y[s];p[3*k+1]=Y[s+1];p[3*k+2]=Y[s+2];}
      lineObjs[i].geometry.attributes.position.needsUpdate=true;
    }
    if(wireObjs[i]&&P.showCenterline){
      const p=wireObjs[i].geometry.attributes.position.array;
      for(let k=0;k<=f.N;k++){const s=f.off+(k%f.N)*3;
        p[3*k]=Y[s];p[3*k+1]=Y[s+1];p[3*k+2]=Y[s+2];}
      wireObjs[i].geometry.attributes.position.needsUpdate=true;
      wireObjs[i].visible=true;
    }else if(wireObjs[i]) wireObjs[i].visible=false;
  });
}
function rebuildTubes(force){
  if(P.vis!=='tube'){tubeObjs.forEach(disposeObj);betaObjs.forEach(disposeObj);flowObjs.forEach(disposeObj);
    if(ghostTubeObj){disposeObj(ghostTubeObj);ghostTubeObj=null;}
    tubeObjs=[];betaObjs=[];flowObjs=[];return;}
  meshFrame++;if(!force&&meshFrame%2!==0)return;
  tubeObjs.forEach(disposeObj);betaObjs.forEach(disposeObj);flowObjs.forEach(disposeObj);
  tubeObjs=[];betaObjs=[];flowObjs=[];
  const tr=Math.max(P.a,0.00035), mats=[P.tubeMat==='solid'?matSolidA:matHolA,P.tubeMat==='solid'?matSolidB:matHolB];
  fils.forEach((f,i)=>{
    try{
      const curve=new DynCurve(f);
      tubeObjs.push(new THREE.Mesh(new THREE.TubeGeometry(curve,f.N,tr,8,true),mats[i%2]));
      filGrp.add(tubeObjs[tubeObjs.length-1]);
      if(Flags.beta){
        betaObjs.push(new THREE.Mesh(new THREE.TubeGeometry(curve,f.N,tr*1.03,10,true),betaMat));
        filGrp.add(betaObjs[betaObjs.length-1]);
      }
      if(Flags.gamma){
        flowObjs.push(new THREE.Mesh(new THREE.TubeGeometry(curve,f.N,tr*1.6,12,true),flowMat));
        filGrp.add(flowObjs[flowObjs.length-1]);
      }
    }catch(e){}
  });
  if(ghostFil){
    try{
      disposeObj(ghostTubeObj);
      const curve=new DynCurve(ghostFil);
      ghostTubeObj=new THREE.Mesh(new THREE.TubeGeometry(curve,ghostFil.N,P.a*2,6,true),ghostTubeMat);
      filGrp.add(ghostTubeObj);
    }catch(e){ghostTubeObj=null;}
  }else if(ghostTubeObj){disposeObj(ghostTubeObj);ghostTubeObj=null;}
}
function anyDvLayerEnabled(){
  return !!(P.dvSeparatrix||P.dvColumn||P.dvCaps||P.dvStewartson);
}
function syncDvGeometryUi(){
  const pairs=[['cDvSeparatrix','dvSeparatrix'],['cDvColumn','dvColumn'],['cDvCaps','dvCaps'],['cDvStewartson','dvStewartson']];
  pairs.forEach(([id,key])=>{const el=document.getElementById(id);if(el)el.checked=!!P[key];});
  const s=document.getElementById('sDvOpacity'),v=document.getElementById('vDvOpacity');
  if(s)s.value=String(Math.round(100*P.dvOpacity));
  if(v)v.textContent=Math.round(100*P.dvOpacity)+'%';
}
function setDvAll(on){
  P.dvSeparatrix=P.dvColumn=P.dvCaps=P.dvStewartson=!!on;
  Flags.sep=!!on;
  syncDvGeometryUi();
}
function applyDvOpacity(){
  const f=clamp(P.dvOpacity,0,1);
  sepObjs.forEach(m=>{if(!m)return;m.material.opacity=TAYLOR_VIS_ALPHA.separatrixFill*f;
    m.children.forEach(c=>{if(c.material)c.material.opacity=TAYLOR_VIS_ALPHA.separatrixEdge*f;});});
  capDiscs.forEach(m=>{if(m?.material)m.material.opacity=TAYLOR_VIS_ALPHA.capDisc*f;});
  capRings.forEach(m=>{if(m?.material)m.material.opacity=TAYLOR_VIS_ALPHA.capRing*f;});
  colSils.forEach(m=>{if(m?.material)m.material.opacity=TAYLOR_VIS_ALPHA.columnWire*f;});
  [stewartsonMat,stewartsonMatNeg].forEach(m=>{if(m)m.opacity=TAYLOR_VIS_ALPHA.stewartsonTorus*f;});
  if(stewartsonTorus?.material)stewartsonTorus.material.opacity=TAYLOR_VIS_ALPHA.stewartsonTorus*f;
  if(stewartsonArrows?.material)stewartsonArrows.material.opacity=TAYLOR_VIS_ALPHA.stewartsonArrows*f;
  footprintDiscs.forEach(m=>{if(m?.material)m.material.opacity=TAYLOR_VIS_ALPHA.footprintDisc*f;});
}

function updateStewartsonVisuals(st,w,t,stw){
  if(!stewartsonTorus||!stewartsonArrows)return;
  const negRel=stw.qS<0; // v7.2: tekenconventie via q_S
  stewartsonTorus.material=negRel?stewartsonMat:stewartsonMatNeg;
  stewartsonTorus.visible=!!P.dvStewartson;
  stewartsonTorus.position.set(st.cx,st.cy,(t.zTop+t.zBot)*0.5);
  stewartsonTorus.scale.set(t.rCap,t.rCap,Math.max(0.02,t.zTop-t.zBot));
  stewartsonArrows.visible=!!P.dvStewartson;
  stewartsonArrows.material.color.setHex(negRel?0xFF7043:0x26C6DA);
  const n=stewartsonArrows.count, zMid=(t.zTop+t.zBot)*0.5;
  const sgn=stw.uTheta>=0?1:-1;
  const m=new THREE.Matrix4(), q=new THREE.Quaternion(), p=new THREE.Vector3(), s=new THREE.Vector3(1,1,1);
  for(let i=0;i<n;i++){
    const th=2*Math.PI*i/n;
    const tx=-Math.sin(th), ty=Math.cos(th);
    p.set(st.cx+t.rCap*Math.cos(th), st.cy+t.rCap*Math.sin(th), zMid);
    q.setFromUnitVectors(new THREE.Vector3(0,1,0), new THREE.Vector3(sgn*tx, sgn*ty, 0));
    m.compose(p,q,s);
    stewartsonArrows.setMatrixAt(i,m);
  }
  stewartsonArrows.instanceMatrix.needsUpdate=true;
  footprintDiscs.forEach(d=>{
    d.visible=!!P.dvCaps;
    const rFp=t.rFoot||P.Rcyl*0.25;
    d.scale.set(rFp,rFp,1);
    d.position.set(st.cx,st.cy,d.position.z);
  });
}
function hideStewartsonVisuals(){
  if(stewartsonTorus)stewartsonTorus.visible=false;
  if(stewartsonArrows)stewartsonArrows.visible=false;
  footprintDiscs.forEach(d=>d.visible=false);
}
function setTaylorCaps(topD,botD,topR,botR,colSil,cx,cy,zT,zB,rC){
  topD.visible=botD.visible=topR.visible=botR.visible=!!P.dvCaps;
  colSil.visible=!!P.dvColumn;
  topD.position.set(cx,cy,zT);botD.position.set(cx,cy,zB);
  topR.position.set(cx,cy,zT);botR.position.set(cx,cy,zB);
  colSil.position.set(cx,cy,(zT+zB)*0.5);
  const sc=[topD,botD,topR,botR];sc.forEach(m=>m.scale.set(rC,rC,1));
  colSil.scale.set(rC,rC,Math.max(0.01,zT-zB));
}
function hideTaylorCaps(topD,botD,topR,botR,colSil){
  [topD,botD,topR,botR,colSil].forEach(m=>m.visible=false);
}
function updateIndicators(tPhys){
  rebuildTubes(false);
  applyDvOpacity();
  const stats=fils.map(f=>carrierStats(f));
  stats.forEach((st,i)=>{
    if(Flags.alpha&&alphaObjs[i]){
      alphaObjs[i].visible=true;
      alphaObjs[i].position.set(st.cx,st.cy,st.z);
      const sc=P.a*6*(1+0.2*Math.sin(tPhys*20));
      alphaObjs[i].scale.set(sc,sc,sc);
    }else if(alphaObjs[i]) alphaObjs[i].visible=false;
  });
  if(!Flags.sep){
    sepObjs.forEach(s=>s.visible=false);
    hideTaylorCaps(capDiscs[0],capDiscs[1],capRings[0],capRings[1],colSils[0]);
    hideTaylorCaps(capDiscs[2],capDiscs[3],capRings[2],capRings[3],colSils[1]);
    footprintDiscs.forEach(d=>d.visible=false);
    hideStewartsonVisuals();
    return;
  }
  let stewartsonShown=false;
  fils.forEach((f,i)=>{
    const st=stats[i];
    const vz=(P.mode==='solo')?effectiveW():(i===0?P.vzA:(P.lockVz?P.vzA:P.vzB));
    const t=taylorColumnState(st,vz);
    if(sepObjs[i]){sepObjs[i].visible=!!P.dvSeparatrix;sepObjs[i].position.set(st.cx,st.cy,st.z);
      sepObjs[i].scale.set(t.rCap,t.rCap,t.rCap);}
    if(i===0) setTaylorCaps(capDiscs[0],capDiscs[1],capRings[0],capRings[1],colSils[0],st.cx,st.cy,t.zTop,t.zBot,t.rCap);
    else setTaylorCaps(capDiscs[2],capDiscs[3],capRings[2],capRings[3],colSils[1],st.cx,st.cy,t.zTop,t.zBot,t.rCap);
    if(P.dvStewartson&&P.mode==='solo'&&i===0&&!stewartsonShown){
      const stw=stewartsonCirculation(vz,t.rCap,P.Om);
      updateStewartsonVisuals(st,vz,t,stw);
      stewartsonShown=true;
    }
  });
  if(!stewartsonShown) hideStewartsonVisuals();
  if(fils.length<2){
    if(sepObjs[1]) sepObjs[1].visible=false;
    hideTaylorCaps(capDiscs[2],capDiscs[3],capRings[2],capRings[3],colSils[1]);
  }
}
function fmtGamma(g){
  const e=Math.floor(Math.log10(Math.max(1e-12,Math.abs(g))));
  return (g/Math.pow(10,e)).toFixed(2)+'·10'+supExp(e);
}
function updateGammaHud(st,vz){
  const show=Flags.sep&&P.mode==='solo';
  document.getElementById('rowGfil').classList.toggle('hidden',!show);
  document.getElementById('rowGsheet').classList.toggle('hidden',!show);
  if(!show)return;
  const t=taylorColumnState(st,vz);
  const stw=stewartsonCirculation(vz,t.rCap,P.Om);
  const gFil=Gamma();
  document.getElementById('hGfil').textContent=fmtGamma(gFil)+' m²/s';
  // v7.2 (RP2): uitsluitend de dimensieloze q_S = −w/(2Ωr_cap); de eerdere
  // Γ_sheet/Γ_rel-getallen waren dimensioneel niet gedefinieerd en zijn weg.
  document.getElementById('hGsheet').textContent=stw.qS.toFixed(4)+(stw.qS<0?' ↓':' ↑');
  document.getElementById('hGsheet').style.color=stw.qS<0?'#FF7043':'#26C6DA';
}
// 3D-camera: links/midden = orbit-rotatie, rechts = translate/pan, wiel = zoom.
let drag=false,dragButton=0,lx=0,ly=0,pinch0=0;
canvas.addEventListener('contextmenu',e=>e.preventDefault());
canvas.addEventListener('pointerdown',e=>{
  if(e.button>2)return;
  drag=true;dragButton=e.button;lx=e.clientX;ly=e.clientY;
  canvas.setPointerCapture(e.pointerId);e.preventDefault();
});
canvas.addEventListener('pointermove',e=>{
  if(!drag)return;
  const dx=e.clientX-lx,dy=e.clientY-ly;
  if(dragButton===2){
    const right=new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld,0).normalize();
    const up=new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld,1).normalize();
    const scale=camD*0.00135;
    camTarget.addScaledVector(right,-dx*scale).addScaledVector(up,dy*scale);
  }else{
    camTh-=dx*0.008;
    camPh=Math.min(2.9,Math.max(0.2,camPh-dy*0.008));
  }
  lx=e.clientX;ly=e.clientY;e.preventDefault();
});
function endCameraDrag(e){
  drag=false;
  if(e&&e.pointerId!==undefined&&canvas.hasPointerCapture(e.pointerId))canvas.releasePointerCapture(e.pointerId);
}
canvas.addEventListener('pointerup',endCameraDrag);
canvas.addEventListener('pointercancel',endCameraDrag);
canvas.addEventListener('wheel',e=>{e.preventDefault();camD=Math.min(4,Math.max(0.4,camD*(1+0.001*e.deltaY)));},{passive:false});
canvas.addEventListener('touchmove',e=>{
  if(e.touches.length===2){
    const d=Math.hypot(e.touches[0].clientX-e.touches[1].clientX,e.touches[0].clientY-e.touches[1].clientY);
    if(pinch0)camD=Math.min(4,Math.max(0.4,camD*pinch0/d));
    pinch0=d;}
},{passive:true});
canvas.addEventListener('touchend',()=>pinch0=0);

// ================= sparkline =================
const sctx=document.getElementById('cspark').getContext('2d');
function drawSpark(){
  const w=230,h=76;sctx.clearRect(0,0,w,h);
  sctx.fillStyle='#6F82A0';sctx.font='9px monospace';
  sctx.fillText(P.mode==='botsing'?'R̄ (—)  Ω_body A (··)':(Flags.sep?'ρ̄ (—)  z (—)  Γ_rel (··)':(P.twistProxyEnabled?'ρ̄ (—)  Ω_body (··)':'ρ̄ (—)  z (—)  Wr (··)')),4,10);
  if(hist.length<2)return;
  const t0=hist[0].t,t1=hist[hist.length-1].t;
  const den=Math.abs(t1-t0)>1e-12?(t1-t0):1e-12;   // tijd-terug-veilig
  function line(key,color,dash){
    let vmax=1e-9;for(const p of hist)vmax=Math.max(vmax,Math.abs(p[key]));
    sctx.strokeStyle=color;sctx.setLineDash(dash);sctx.beginPath();
    hist.forEach((p,i)=>{
      const x=4+(w-8)*clamp((p.t-t0)/den,0,1);
      const y=h-4-(h-18)*(0.5+0.5*p[key]/vmax);
      i?sctx.lineTo(x,y):sctx.moveTo(x,y);});
    sctx.stroke();sctx.setLineDash([]);
  }
  if(P.mode==='botsing'){line('RA','#FFAE45',[]);line('RB','#55D6FF',[]);line('omA','#A855F7',[3,3]);}
  else{
    line('RA','#FFAE45',[]);line('zA','#55D6FF',[]);
    if(Flags.sep) line('gRel','#FF7043',[3,3]);
    else if(P.twistProxyEnabled) line('omA','#A855F7',[3,3]);
    else line('Wr','#C9D6E3',[3,3]);
  }
}

// ================= UI =================
function fmtNq(){
  const n=Math.max(1,Math.round(P.nQ));
  const unit=P.med==='sst'?'Γ₀':'κ';
  return `${n.toLocaleString('nl-NL')} → Γ = ${n===1?'':n.toLocaleString('nl-NL')} ${unit}`;
}
function fmtGa(){
  const g=Gamma();
  const e=Math.floor(Math.log10(Math.abs(g)));
  const m=g/Math.pow(10,e);
  const q=P.med==='sst'?` (${P.nQ}Γ₀)`:P.med==='he'?` (${P.nQ}κ)`:'';
  return `${m.toFixed(2)}·10${supExp(e)} m²/s${q}`;
}
function supExp(e){
  const map={'-':'⁻','0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹'};
  return String(e).split('').map(c=>map[c]||c).join('');
}
function fmtAcc(x){
  if(x<1000)return x.toFixed(x<20?1:0)+'×';
  const e=Math.floor(Math.log10(x));
  return (x/Math.pow(10,e)).toFixed(1)+'·10'+supExp(e)+'×';
}
function updateSubtitle(){
  const topoTxt=topologyLabel();
  const nComp=topologyComponentCount();
  const medTxt={demo:'demo-Γ',he:'He-II, Γ=nκ',sst:'SST, Γ=nΓ₀ [Canon 0.8.19]'}[P.med];
  const coreTxt={hol:'holle kern',vast:'vaste kern',gp:'GP-kern'}[P.core];
  const modeTxt=P.mode==='botsing'
    ?`Twee coaxiale ${topoTxt}-dragers${nComp>1?` (${nComp} componenten per drager)`:''}, |Γ| identiek, frontaal${P.inter==='lia'?' · LIA (geen wederzijdse inductie!)':''}`
    :`${nComp>1?nComp+' gekoppelde componenten van ': 'Eén '}${topoTxt} op de middenas${P.inter==='lia'?' · LIA':''}`;
  const transportTxt=[P.centerLock?'centrum-lock':'',P.tracerWrapZ?'periodiek z: knopen+deeltjes':'',P.coreFlowLock?'a–Γ–Ω gekoppeld':''].filter(Boolean).join(' · ');
  document.getElementById('hSub').textContent=`${modeTxt} · ${coreTxt} · ${medTxt}${transportTxt?' · '+transportTxt:''}`;
  document.getElementById('hWrLbl').innerHTML=fils.length>1
    ?'Σ Wr(componenten)':'Wr';
  const lkLbl=document.getElementById('hLkLbl');if(lkLbl)lkLbl.textContent=fils.length>2?'Σ Lk(i,j)':'Lk(1,2)';
  document.getElementById('hRLbl').textContent=P.mode==='botsing'
    ?(isRingTopo()?'R̄ A / B':'ρ̄ A / B'):(nComp>1?'ρ̄ componenten':'ρ̄');
  document.getElementById('hVLbl').textContent=P.mode==='botsing'?'naderingssnelheid':'v_z (w)';
  document.getElementById('rowLk').classList.toggle('hidden',fils.length<2);
  document.getElementById('rowDz').classList.toggle('hidden',P.mode!=='botsing');
  const soloKnot=P.mode==='solo'&&!isRingTopo();
  document.getElementById('rowDWr').classList.toggle('hidden',P.mode==='botsing'||!soloKnot);
  document.getElementById('rowUth').classList.toggle('hidden',!isRingTopo());
  document.getElementById('rowOmBodyA').classList.toggle('hidden',false);
  document.getElementById('rowOmBodyB').classList.toggle('hidden',P.mode!=='botsing');
  document.getElementById('rowChi').classList.toggle('hidden',isRingTopo());
  document.getElementById('rowTw').classList.toggle('hidden',!P.twistProxyEnabled);
  renderFormula();
}
function updateBodyHud(bodyStates,Wr){
  if(!bodyStates.length)return;
  const bA=bodyStates[0];
  document.getElementById('hOmBodyA').textContent=fmtOmegaBody(bA.omegaZ);
  if(P.mode==='botsing'){
    const idxB=fils.findIndex(f=>(f.carrier||'A')==='B');
    if(idxB>=0&&bodyStates[idxB])document.getElementById('hOmBodyB').textContent=fmtOmegaBody(bodyStates[idxB].omegaZ);
  }
  if(bA.chi){
    document.getElementById('hChi').textContent=`(${bA.chi.x.toFixed(2)}, ${bA.chi.y.toFixed(2)}) · ${bA.chi.phi.toFixed(0)}°`;
  }else{
    document.getElementById('hChi').textContent='— (ring, Wr=0)';
  }
  if(P.twistProxyEnabled&&twistProxy){
    const tw=twistProxySum();
    document.getElementById('hTw').textContent=tw.toExponential(3)+' m'; // v7.1 (B4): dimensie is lengte; niet optellen bij Wr
  }
}
function knotLabel(i){
  if(window.IDEAL_KNOT_IDS&&IDEAL_KNOT_IDS[i]) return IDEAL_KNOT_IDS[i];
  const e=window.IDEAL_KNOTS&&window.IDEAL_KNOTS[i];
  return e?(e.knotId||e.id||e.name||('#'+i)):'3:1:1';
}
function renderFormula(){
  const el=document.getElementById('eFormula');
  if(!el||!window.katex)return;
  const parts=[
    {on:Flags.alpha,t:'\\alpha C(K)',c:'#FF6E6E'},
    {on:Flags.beta,t:'\\beta \\widehat L(K)',c:'#FFAE45'},
    {on:Flags.gamma,t:'\\gamma \\widehat H(K)',c:'#A855F7'}
  ];
  el.innerHTML='';
  const lead=document.createElement('span');
  katex.render('\\widehat{\\mathcal S}(K)=',lead);el.appendChild(lead);
  parts.forEach((p,i)=>{
    if(i) el.appendChild(document.createTextNode(' + '));
    const s=document.createElement('span');
    s.style.color=p.on?p.c:'#6F82A0';if(p.on)s.style.fontWeight='600';
    katex.render(p.t,s);el.appendChild(s);
  });
  if(Flags.sep){
    el.appendChild(document.createTextNode('  ·  '));
    const overlay=document.createElement('span');overlay.style.color='#EAF2FA';
    katex.render('\\partial V\\;\\text{overlay}',overlay);el.appendChild(overlay);
  }
}
function initDiagnosticToggles(){
  syncDiagnosticToggles();
}
function syncDiagnosticToggles(){
  document.querySelectorAll('#indSeg .seg-btn').forEach(b=>{
    const key=b.dataset.ind;
    if(!EXPLAIN[key])return;
    b.classList.toggle(EXPLAIN[key].cls,!!Flags[key]);
  });
}
function setIndFlag(key,on){
  if(!(key in Flags))return;
  if(key==='sep')setDvAll(on);
  else Flags[key]=on;
  syncDiagnosticToggles();
  renderFormula();
  rebuildTubes(true);
  updateIndicators(tPhys);
}
function syncCompSelects(){
  const entry=activeKnotEntry();
  const row=document.getElementById('compRow');
  if(!entry||!entry.components||entry.components.length<2){row.classList.add('hidden');return;}
  row.classList.remove('hidden');
  const fill=(sel,val)=>{
    sel.innerHTML=entry.components.map((_,i)=>`<option value="${i+1}">comp ${i+1}</option>`).join('');
    sel.value=String(Math.min(val,entry.components.length));
  };
  fill(document.getElementById('compA'),P.compA);
  fill(document.getElementById('compB'),P.compB);
}
function syncSeg(id,attr,val){
  document.querySelectorAll(`#${id} .seg-btn`).forEach(b=>b.classList.toggle('active',b.dataset[attr]===val));
}
function syncSignedUi(sliderId,revId,val,fmtVal){
  const s=document.getElementById('s'+sliderId);
  const r=document.getElementById(revId);
  const v=document.getElementById('v'+sliderId);
  if(!s||!r)return;
  r.checked=val<0;
  P['rev'+sliderId]=val<0;
  s.value=Math.abs(val);
  if(v&&fmtVal)v.textContent=fmtVal(val);
}
function syncUi(){
  syncSeg('modeSeg','mode',P.mode);
  document.getElementById('topoSelect').value=P.topo;
  syncSeg('interSeg','inter',P.inter);
  syncSeg('coreSeg','core',P.core);
  syncSeg('medSeg','med',P.med);
  syncSeg('qualSeg','qual',P.qual);
  syncSeg('visSeg','vis',P.vis);
  syncSeg('tubeSeg','tube',P.tubeMat);
  syncSeg('frameSeg','frame',P.coRot?'rotating':'absolute');
  document.getElementById('interRow').classList.remove('hidden');
  document.getElementById('offRow').classList.remove('hidden');
  document.getElementById('wRow').classList.toggle('hidden',P.mode!=='solo');   // v7.1 (B1)
  document.getElementById('vzARow').classList.toggle('hidden',P.mode!=='botsing'); // v7.1 (B1)
  document.getElementById('vzBRow').classList.toggle('hidden',P.mode!=='botsing'||P.lockVz);
  document.getElementById('ccwARow').classList.remove('hidden');
  document.getElementById('ccwBRow').classList.toggle('hidden',P.mode!=='botsing');
  document.getElementById('mirrorRow').classList.toggle('hidden',P.mode!=='botsing');
  document.getElementById('lockVzRow').classList.toggle('hidden',P.mode!=='botsing');
  document.getElementById('qualRow').classList.remove('hidden');
  document.getElementById('gaRow').classList.toggle('hidden',P.med!=='demo');
  document.getElementById('nqRow').classList.toggle('hidden',P.med==='demo');
  document.getElementById('cCenterline').checked=P.showCenterline;
  document.getElementById('cCcwA').checked=P.ccwA;
  document.getElementById('cCcwB').checked=P.ccwB;
  document.getElementById('cMirror').checked=P.mirrorB;
  document.getElementById('cLockVz').checked=P.lockVz;
  document.getElementById('cCoRot').checked=P.coRot;
  const vFR=document.getElementById('vFrameRef');if(vFR)vFR.textContent=P.coRot?'Rotating':'Absolute';
  document.getElementById('cBgOmega').checked=P.bgOmegaCoupling;
  document.getElementById('cChiArrow').checked=P.showChiArrow;
  document.getElementById('cTwProxy').checked=P.twistProxyEnabled;
  document.getElementById('cAutoRelax').checked=P.autoRelax;
  document.getElementById('cCoreFlowLock').checked=P.coreFlowLock;
  document.getElementById('cCenterLock').checked=P.centerLock;
  document.getElementById('cTracerWrapZ').checked=P.tracerWrapZ;
  document.getElementById('autoRelaxBadge').textContent=P.timeReverse&&P.autoRelax?'PAUZE':(P.autoRelax?'AAN':'UIT');
  document.getElementById('autoRelaxBadge').classList.toggle('on',P.autoRelax&&!P.timeReverse);
  document.getElementById('cTimeReverse').checked=P.timeReverse;
  document.getElementById('timeReverseRow').classList.toggle('time-reverse-on',P.timeReverse);
  syncDvGeometryUi();
  document.getElementById('cGhostRing').checked=P.ghostStewartson;
  document.getElementById('cTaylorOsc').checked=P.taylorOsc.enabled;
  document.getElementById('oscRow').classList.remove('hidden');
  [['WAl','wAl'],['WBe','wBe'],['WGa','wGa']].forEach(([id,key])=>{
    const el=document.getElementById('s'+id);
    if(el){el.value=P[key];document.getElementById('v'+id).textContent=P[key].toFixed(1);}});
  const cT=document.getElementById('cTracers');if(cT)cT.checked=P.showTracers;
  const cSL=document.getElementById('cStreamlines');if(cSL)cSL.checked=P.showStreamlines;
  const sVO=document.getElementById('sVortexOpacity');if(sVO)sVO.value=String(Math.round(100*P.vortexOpacity));
  const vVO=document.getElementById('vVortexOpacity');if(vVO)vVO.textContent=Math.round(100*P.vortexOpacity)+'%';
  const sPS=document.getElementById('sParticleSize');if(sPS)sPS.value=(1000*P.particleSize).toFixed(1);
  const vPS=document.getElementById('vParticleSize');if(vPS)vPS.textContent=(1000*P.particleSize).toFixed(1)+' mm';
  const sTC=document.getElementById('sTracerCount');if(sTC)sTC.value=String(P.tracerCount);
  const vTC=document.getElementById('vTracerCount');if(vTC)vTC.textContent=String(P.tracerCount);
  const sSC=document.getElementById('sStreamlineCount');if(sSC)sSC.value=String(P.streamlineCount);
  const vSC=document.getElementById('vStreamlineCount');if(vSC)vSC.textContent=String(P.streamlineCount);
  const scRow=document.getElementById('streamlineCountRow');if(scRow)scRow.classList.toggle('hidden',!P.showStreamlines);
  const vc=document.getElementById('sVorticityColor');if(vc)vc.value=P.vorticityLineColor||'#0F1A29';
  const vvc=document.getElementById('vVorticityColor');if(vvc)vvc.textContent=(P.vorticityLineColor||'#0F1A29').toUpperCase();
  const sAP=document.getElementById('sAPhys');if(sAP)sAP.value=Number.isFinite(P.aPhys)?String(P.aPhys):'';
  const vAP=document.getElementById('vAPhys');if(vAP)vAP.textContent=fmtLengthSI(P.aPhys);
  syncDiagnosticToggles();
  const gpDeltaText=DELTA.gp.toFixed(6);
  const gpSel=document.getElementById('gpDeltaSel');if(gpSel){gpSel.value=String(DELTA.gp);gpSel.disabled=P.core!=='gp';}
  const gpVal=document.getElementById('vGpDelta');if(gpVal)gpVal.textContent=gpDeltaText;
  const gpPanel=document.getElementById('gpDeltaPanel');if(gpPanel){gpPanel.classList.toggle('active',P.core==='gp');gpPanel.classList.toggle('hidden',P.core!=='gp');}
  document.getElementById('vCore').textContent='Δ = '+(P.core==='hol'?'½':(P.core==='vast'?'¼':gpDeltaText));
  document.getElementById('vGa').textContent=fmtGa();
  document.getElementById('vNq').textContent=fmtNq();
  const sASim=document.getElementById('sA');if(sASim)sASim.value=formatASimInputMm(P.a);
  document.getElementById('vAcc').textContent=fmtAcc(acc());
  syncSignedUi('Om','revOm',P.Om,x=>Math.abs(x).toFixed(2)+' rad/s · '+(x<0?'CW':'CCW'));
  syncSignedUi('Ga','revGa',P.GaDemo,()=>fmtGa());
  syncSignedUi('Off','revOff',P.off*1000,x=>x.toFixed(0)+' mm');
  syncSignedUi('W','revW',P.w*1000,x=>fmtAxialMmPerS(x));
  syncSignedUi('VzA','revVzA',P.vzA*1000,x=>fmtAxialMmPerS(x));
  syncSignedUi('VzB','revVzB',P.vzB*1000,x=>fmtAxialMmPerS(x));
  const mfSel=document.getElementById('mfTemp');if(mfSel)mfSel.value=P.mfTemp;
  const mfCustom=P.mfTemp==='custom';
  const sMfA=document.getElementById('sMfA');
  if(sMfA){sMfA.disabled=!mfCustom;sMfA.value=String(P.mfAlpha);
    document.getElementById('vMfA').textContent=P.mfAlpha.toFixed(3);}
  const sMfAp=document.getElementById('sMfAp');
  if(sMfAp){sMfAp.disabled=!mfCustom;sMfAp.value=String(P.mfAlphaP);
    document.getElementById('vMfAp').textContent=P.mfAlphaP.toFixed(4);}
  const vMfT=document.getElementById('vMfT');
  if(vMfT)vMfT.textContent=P.mfTemp==='0'?'T = 0 (uit)'
    :(P.mfTemp==='custom'?'aangepast':P.mfTemp+' K (He-II SVP)');
  syncSignedUi('Vn','revVn',P.vnZ*1000,x=>fmtAxialMmPerS(x));
  document.getElementById('sDiam').value=(P.Rcyl*200).toFixed(0);
  document.getElementById('vDiam').textContent=(P.Rcyl*200).toFixed(0)+' cm';
  document.getElementById('sHeight').value=(P.Hcyl*100).toFixed(1).replace(/\.0$/,'');
  document.getElementById('vHeight').textContent=(P.Hcyl*100).toFixed(1).replace(/\.0$/,'')+' cm (totaal '+(cylinderHeight()*100).toFixed(0)+' cm)';
  document.getElementById('hOm').textContent=P.Om.toFixed(2);
  updateStretchReadout();
  if(Y&&fils.length)updateCoreRadiusLimit(true);
  updateCoreFlowReadout();
  syncBundleUi();
  syncHybridNumberInputs();
  syncCompSelects();
  updateHeaderTitle();
  scheduleSidebarFit();
}
// Step 12c: verplaats alle stabiliteitsrelevante controls naar één collapsable,
// zonder IDs te dupliceren; bestaande event-bindings blijven daardoor intact.
function organizeStabilityControls(){
  const cyl=document.getElementById('stabGroupCylinder');
  const core=document.getElementById('stabGroupCore');
  const flow=document.getElementById('stabGroupFlow');
  const flags=document.getElementById('stabGroupFlowFlags');
  const vortex=document.getElementById('stabGroupVortex');
  const vortexFlags=document.getElementById('stabGroupVortexFlags');
  const runTop=document.getElementById('runSetupTop');
  if(!cyl||!core||!flow||!flags||!vortex||!vortexFlags||!runTop)return;
  const moveCtrl=(id,dst)=>{const el=document.getElementById(id);const ctrl=el?.closest('.ctrl');if(ctrl)dst.appendChild(ctrl);};

  // MODEL · CILINDER
  moveCtrl('frameSeg',cyl);moveCtrl('sVorticityColor',cyl);
  moveCtrl('sDiam',cyl);moveCtrl('sHeight',cyl);
  const periodic=document.getElementById('cTracerWrapZ')?.closest('label');if(periodic)cyl.appendChild(periodic);
  const link=document.getElementById('bLinkDH'),stretch=document.getElementById('vStretch');
  if(link)cyl.appendChild(link);if(stretch)cyl.appendChild(stretch);
  const volNote=document.querySelector('#collVolume .note');if(volNote)cyl.appendChild(volNote);

  // RUN · medium en solverkwaliteit. Kernmodel hoort bij VORTEXKERN boven n.
  moveCtrl('medSeg',runTop);
  const qual=document.getElementById('qualRow');if(qual)runTop.appendChild(qual);

  // MODEL · KERN
  moveCtrl('coreSeg',core);moveCtrl('sNq',core);moveCtrl('sGa',core);moveCtrl('sA',core);
  moveCtrl('sAPhys',core);
  const coreFlowPanel=document.getElementById('coreFlowLinkPanel');if(coreFlowPanel)core.appendChild(coreFlowPanel);

  // MODEL · VORTEX: drager/topologie en geometrische presentatie.
  moveCtrl('modeSeg',vortex);moveCtrl('topoSelect',vortex);
  const knot=document.getElementById('knotRow');if(knot)vortex.appendChild(knot);
  const comp=document.getElementById('compRow');if(comp)vortex.appendChild(comp);

  // MODEL · FLOW: dynamica en axiale transportparameters.
  const inter=document.getElementById('interRow');if(inter)flow.appendChild(inter);
  ['offRow','wRow','vzARow','vzBRow'].forEach(id=>{const el=document.getElementById(id);if(el)flow.appendChild(el);});

  const paramFlags=document.querySelector('#collParams .btns');
  if(paramFlags){
    ['ccwARow','ccwBRow','mirrorRow','lockVzRow'].forEach(id=>{const el=document.getElementById(id);if(el)vortexFlags.appendChild(el);});
    const bg=document.getElementById('cBgOmega')?.closest('label');if(bg)flags.appendChild(bg);
    const note=paramFlags.querySelector('.note');if(note)flags.appendChild(note);
  }
  organizeQuickControls();
  ['collConfig','collMedium','collVolume','collParams'].forEach(id=>document.getElementById(id)?.remove());
}
function dockStabilityDisplay(){
  const dock=document.getElementById('stabilityDock');
  const coll=document.getElementById('collStability');
  const panel=document.getElementById('stabilityPanel');
  const advice=document.getElementById('stabilityAdvice');
  if(!dock||!panel||!advice)return;
  dock.append(panel,advice);
  if(coll)coll.remove();
}
function organizeQuickControls(){
  const dock=document.getElementById('quickControlsDock');
  if(!dock)return;
  const moveRow=(id)=>{const el=document.getElementById(id);if(el)dock.appendChild(el);};
  const moveCtrl=(id)=>{const el=document.getElementById(id);const ctrl=el?.closest('.ctrl');if(ctrl)dock.appendChild(ctrl);};
  moveCtrl('sAcc');
  const autoRelax=document.querySelector('.auto-relax-row');
  if(autoRelax)dock.appendChild(autoRelax);
  moveRow('cylinderOmegaRow');
  moveRow('sstBundlePanel');
}
organizeStabilityControls();
dockStabilityDisplay();

// Step 9: combineer voor ieder numeriek veld een slider, compact getalveld en ^ / v bediening.
// De oorspronkelijke number-input-ID's blijven de bron van waarheid voor alle physics-bindings.
function initNumberSteppers(){
  document.querySelectorAll('input[type="number"][id^="s"]').forEach(input=>{
    if(input.closest('.param-hybrid'))return;
    input.classList.add('param-number');
    input.setAttribute('autocomplete','off');
    const stepRaw=Number(input.step);
    input.setAttribute('inputmode',Number.isFinite(stepRaw)&&stepRaw%1!==0?'decimal':'numeric');

    const wrap=document.createElement('div');
    wrap.className='param-hybrid';
    input.parentNode.insertBefore(wrap,input);
    wrap.appendChild(input);

    const range=document.createElement('input');
    range.type='range';
    range.className='param-slider';
    const logarithmic=input.dataset.scale==='log';
    range.min=logarithmic?'0':(input.min||'0');
    range.max=logarithmic?'1000':(input.max||'100');
    range.step=logarithmic?'1':(input.step||'1');
    range.value=String(hybridRangeFromInput(input));
    range.setAttribute('aria-label',(input.id||'parameter')+' slider');
    wrap.insertBefore(range,input);

    function makeButton(dir,label,title){
      const b=document.createElement('button');
      b.type='button';
      b.className='num-step-btn';
      b.dataset.dir=dir;
      b.textContent=label;
      b.title=title;
      b.setAttribute('aria-label',title);
      return b;
    }
    const up=makeButton('up','^','Waarde één stap verhogen');
    const down=makeButton('down','v','Waarde één stap verlagen');
    wrap.append(up,down);

    function ensureNumericSeed(){
      if(input.value!=='')return;
      input.value=input.min!==''?input.min:'0';
    }
    function publish(){
      range.value=String(hybridRangeFromInput(input));
      input.dispatchEvent(new Event('input',{bubbles:true}));
    }
    function nudge(direction,multiplier=1){
      ensureNumericSeed();
      try{
        const count=Math.max(1,Math.round(Math.abs(multiplier)));
        for(let i=0;i<count;i++) direction>0?input.stepUp():input.stepDown();
      }catch(_err){
        const step=Number(input.step)||1;
        const current=Number(input.value)||0;
        const lo=input.min===''?-Infinity:Number(input.min);
        const hi=input.max===''? Infinity:Number(input.max);
        input.value=String(clamp(current+Math.sign(direction)*step*multiplier,lo,hi));
      }
      publish();
      input.focus({preventScroll:true});
    }
    range.addEventListener('input',()=>{
      const value=hybridInputFromRange(input,range.value);
      input.value=formatHybridInputValue(input,value);
      input.dispatchEvent(new Event('input',{bubbles:true}));
    });
    input.addEventListener('input',()=>{range.value=String(hybridRangeFromInput(input));});
    up.addEventListener('click',e=>nudge(+1,e.shiftKey?10:1));
    down.addEventListener('click',e=>nudge(-1,e.shiftKey?10:1));
    input.addEventListener('keydown',e=>{
      if(e.key==='PageUp'){e.preventDefault();nudge(+1,10);}
      else if(e.key==='PageDown'){e.preventDefault();nudge(-1,10);}
    });
    input.addEventListener('change',()=>{
      if(input.value==='')return;
      const value=Number(input.value);
      const lo=input.min===''?-Infinity:Number(input.min);
      const hi=input.max===''? Infinity:Number(input.max);
      if(Number.isFinite(value)){
        const bounded=clamp(value,lo,hi);
        if(bounded!==value){input.value=String(bounded);publish();}
      }
    });
  });
}
initNumberSteppers();


// Step 17: maak van alle expandable blokken in de rechterzijbalk één tabwerkruimte.
// De actieve tab wordt automatisch geometrisch ingepast; er is geen sidebar-scrollbar nodig.
let sidebarTabState=null;
let sidebarFitRaf=0;
function scheduleSidebarFit(){
  if(!sidebarTabState)return;
  cancelAnimationFrame(sidebarFitRaf);
  sidebarFitRaf=requestAnimationFrame(()=>fitActiveSidebarTab());
}
function fitActiveSidebarTab(){
  const state=sidebarTabState;
  if(!state)return;
  const panel=state.panels.find(p=>p.classList.contains('active'));
  const fit=panel?.querySelector(':scope > .coll-body > .sidebar-tab-fit');
  if(!panel||!fit)return;
  const available=Math.max(1,state.viewport.clientHeight-4);
  fit.style.transform='none';
  fit.style.width='100%';
  let scale=1;
  // Iteratief: een grotere logische breedte vermindert wrapping en dus de benodigde hoogte.
  for(let i=0;i<3;i++){
    const raw=Math.max(1,fit.scrollHeight);
    scale=Math.min(1,available/raw);
    fit.style.width=scale<0.999?(100/scale).toFixed(3)+'%':'100%';
  }
  const raw=Math.max(1,fit.scrollHeight);
  scale=Math.min(1,available/raw);
  fit.style.width=scale<0.999?(100/scale).toFixed(3)+'%':'100%';
  fit.style.transform=scale<0.999?'scale('+scale.toFixed(4)+')':'none';
  state.indicator.textContent='fit '+Math.round(scale*100)+'%';
  state.indicator.title=scale<0.999
    ?'De actieve tab is automatisch verkleind om zonder scrollbar in de zijbalk te passen.'
    :'De actieve tab past op ware grootte zonder scrollbar.';
}
function wireTabButtons(buttons,panels,storageKey,onChange){
  const activate=(index,focus=false)=>{
    index=(index+panels.length)%panels.length;
    buttons.forEach((b,i)=>{b.classList.toggle('active',i===index);b.setAttribute('aria-selected',i===index?'true':'false');b.tabIndex=i===index?0:-1;});
    panels.forEach((p,i)=>p.classList.toggle('active',i===index));
    try{localStorage.setItem(storageKey,String(index));}catch(_){ }
    if(focus)buttons[index].focus({preventScroll:true});
    scheduleSidebarFit();
  };
  buttons.forEach((b,i)=>{
    b.addEventListener('click',()=>activate(i));
    b.addEventListener('keydown',e=>{
      let target=null;
      if(e.key==='ArrowRight'||e.key==='ArrowDown')target=i+1;
      else if(e.key==='ArrowLeft'||e.key==='ArrowUp')target=i-1;
      else if(e.key==='Home')target=0;
      else if(e.key==='End')target=buttons.length-1;
      if(target!==null){e.preventDefault();activate(target,true);}
    });
  });
  let initial=0;
  try{const saved=Number(localStorage.getItem(storageKey));if(Number.isInteger(saved)&&saved>=0&&saved<panels.length)initial=saved;}catch(_){ }
  activate(initial);
  return activate;
}
function makeCompactTabs(host,panels,labels,key){
  if(!host||panels.length<2)return;
  const shell=document.createElement('div');shell.className='compact-tabs';
  const nav=document.createElement('div');nav.className='compact-tab-nav';nav.style.setProperty('--compact-cols',String(panels.length));nav.setAttribute('role','tablist');
  const viewport=document.createElement('div');viewport.className='compact-tab-viewport';
  host.insertBefore(shell,panels[0]);shell.append(nav,viewport);
  const buttons=[];
  panels.forEach((panel,i)=>{
    if(panel.tagName==='DETAILS')panel.open=true;
    panel.classList.add('compact-tab-panel');viewport.appendChild(panel);
    const b=document.createElement('button');b.type='button';b.className='compact-tab-btn';b.textContent=labels[i];
    b.title=labels[i];b.setAttribute('role','tab');b.setAttribute('aria-controls',panel.id||'');nav.appendChild(b);buttons.push(b);
  });
  wireTabButtons(buttons,panels,key);
}
function initStabilitySubtabs(){
  const parent=document.getElementById('collStabilityParams');
  const body=parent?.querySelector(':scope > .coll-body');
  if(!body)return;
  const panels=['subFlow','subVortex','subCylinder','subCore'].map(id=>document.getElementById(id)).filter(Boolean);
  makeCompactTabs(body,panels,['FLOW','VORTEX','CILINDER','KERN'],'vortexlab.sidebar.setupSubtab.v3');
}
function mergeVisualIntoModel(){
  const coll=document.getElementById('collVis');
  const source=coll?.querySelector(':scope > .coll-body > .ctrls');
  const vortexBody=document.querySelector('#subVortex > .subcoll-body');
  const flowBody=document.querySelector('#subFlow > .subcoll-body');
  if(!coll||!source||!vortexBody||!flowBody)return;
  const vBlock=document.createElement('div');vBlock.className='model-visual-block';
  vBlock.innerHTML='<div class="model-visual-title">VORTEXWEERGAVE</div><div class="ctrls"></div>';
  const fBlock=document.createElement('div');fBlock.className='model-visual-block';
  fBlock.innerHTML='<div class="model-visual-title">FLOWWEERGAVE</div><div class="ctrls"></div>';
  const vg=vBlock.querySelector('.ctrls'),fg=fBlock.querySelector('.ctrls');
  const move=(node,dst)=>{if(node)dst.appendChild(node);};
  move(document.getElementById('visSeg')?.closest('.ctrl'),vg);
  move(document.getElementById('tubeSeg')?.closest('.ctrl'),vg);
  move(document.getElementById('cChiArrow')?.closest('label'),vg);
  move(document.getElementById('sVortexOpacity')?.closest('.ctrl'),vg);

  move(document.getElementById('cTracers')?.closest('label'),fg);
  move(document.getElementById('cStreamlines')?.closest('label'),fg);
  move(document.getElementById('tracerCountRow'),fg);
  move(document.getElementById('streamlineCountRow'),fg);
  move(document.getElementById('particleSizeRow'),fg);
  move(document.getElementById('bResetParticles'),fg);
  const transport=source.querySelector('.transport-options');
  const flowNote=transport?.nextElementSibling?.classList.contains('note')?transport.nextElementSibling:null;
  const centerLock=document.getElementById('cCenterLock')?.closest('label');
  if(centerLock)document.getElementById('stabGroupVortexFlags')?.appendChild(centerLock);
  move(transport,fg);move(flowNote,fg);

  const dv=source.querySelector('.dv-geometry');
  const diagnosticBody=document.querySelector('#collDiagnostics > .coll-body');
  if(dv&&diagnosticBody)diagnosticBody.appendChild(dv);

  vortexBody.appendChild(vBlock);flowBody.appendChild(fBlock);
  coll.remove();
}
function initSidebarTabs(){
  const ui=document.getElementById('ui-right');
  if(!ui||ui.classList.contains('sidebar-tabbed'))return;
  mergeVisualIntoModel();
  initStabilitySubtabs();
  const ids=['collStabilityParams','collDiagnostics','collRun'];
  const labels=['MODEL','DIAGNOSE','RUN'];
  const panels=ids.map(id=>document.getElementById(id)).filter(Boolean);
  if(!panels.length)return;
  const foot=document.getElementById('footNote');
  const runBody=document.querySelector('#collRun > .coll-body');
  if(foot&&runBody)runBody.appendChild(foot);

  ui.classList.add('sidebar-tabbed');
  const shell=document.createElement('div');shell.className='sidebar-tab-shell';
  const nav=document.createElement('div');nav.className='sidebar-tab-nav';nav.style.setProperty('--sidebar-cols',String(panels.length));nav.setAttribute('role','tablist');nav.setAttribute('aria-label','Simulatorinstellingen');
  const viewport=document.createElement('div');viewport.className='sidebar-tab-viewport';
  const indicator=document.createElement('div');indicator.className='sidebar-fit-indicator';indicator.textContent='fit 100%';
  ui.insertBefore(shell,panels[0]);shell.append(nav,viewport);viewport.appendChild(indicator);
  const buttons=[];
  panels.forEach((panel,i)=>{
    panel.open=true;panel.classList.add('sidebar-tab-panel');viewport.appendChild(panel);
    const body=panel.querySelector(':scope > .coll-body');
    if(body&&!body.querySelector(':scope > .sidebar-tab-fit')){
      const fit=document.createElement('div');fit.className='sidebar-tab-fit';
      while(body.firstChild)fit.appendChild(body.firstChild);
      body.appendChild(fit);
    }
    const b=document.createElement('button');b.type='button';b.className='sidebar-tab-btn';b.textContent=labels[i]||('TAB '+(i+1));
    b.title=(panel.querySelector(':scope > summary')?.textContent||labels[i]).trim();b.setAttribute('role','tab');b.setAttribute('aria-controls',panel.id);nav.appendChild(b);buttons.push(b);
  });
  sidebarTabState={ui,shell,nav,viewport,indicator,buttons,panels};
  wireTabButtons(buttons,panels,'vortexlab.sidebar.mainTab.v3');
  if('ResizeObserver' in window){
    const ro=new ResizeObserver(()=>scheduleSidebarFit());
    ro.observe(viewport);panels.forEach(p=>{const fit=p.querySelector('.sidebar-tab-fit');if(fit)ro.observe(fit);});
    sidebarTabState.resizeObserver=ro;
  }
  window.addEventListener('resize',scheduleSidebarFit,{passive:true});
  scheduleSidebarFit();
}
initSidebarTabs();

function bindSignedRange(sliderId,revId,fmt,apply){
  const s=document.getElementById('s'+sliderId);
  const r=document.getElementById(revId);
  const v=document.getElementById('v'+sliderId);
  function refresh(){
    const mag=Number(s.value);
    if(!Number.isFinite(mag))return; // partiële exponentinvoer mag de toestand niet met NaN besmetten
    const rev=r.checked;
    P['rev'+sliderId]=rev;
    const signed=applySigned(rev,mag);
    apply(signed,mag,rev);
    if(v)v.textContent=fmt(signed,mag,rev);
  }
  s.addEventListener('input',refresh);
  r.addEventListener('change',refresh);
  return refresh;
}
function bindRange(id,fmt,set){
  const s=document.getElementById('s'+id),v=document.getElementById('v'+id);
  s.addEventListener('input',()=>{
    const x=Number(s.value);
    if(!Number.isFinite(x))return; // bv. tijdelijk leeg tijdens typen van 1e-15
    const applied=set(x);
    if(v&&applied!==null)v.textContent=fmt(Number.isFinite(applied)?applied:x);
  });
}
bindSignedRange('Om','revOm',(x)=>Math.abs(x).toFixed(2)+' rad/s · '+(x<0?'CW':'CCW'),(x)=>{P.Om=x;if(P.coreFlowLock)syncCoreFlowCoupling('omega');document.getElementById('hOm').textContent=P.Om.toFixed(2);rebuildLattice();updateHeaderTitle();updateCoreFlowReadout();});
bindSignedRange('Ga','revGa',()=>fmtGa(),(x)=>{P.GaDemo=x;if(P.coreFlowLock)syncCoreFlowCoupling('gamma');syncUi();});
bindRange('Nq',()=>fmtNq(),x=>{P.nQ=Math.max(1,Math.round(x));if(P.coreFlowLock)syncCoreFlowCoupling('gamma');syncUi();});
bindRange('A',x=>fmtLengthSI(x*1e-3),x=>{
  // v7.3.1: commit alleen eindige waarden; de solver ontvangt nooit a=0/NaN.
  const requested=clamp(x*1e-3,A_SIM_INPUT_FLOOR,Math.max(A_SIM_INPUT_FLOOR,coreRadiusMax));
  const q=kappaMedium(),omega=Math.max(1e-12,Math.abs(P.Om));
  const minLocked=q?Math.sqrt(q/(2*Math.PI*omega)):0;
  if(P.coreFlowLock&&minLocked>0&&requested<minLocked*(1-1e-12)){
    P.coreFlowLock=false;
    coreFlowNotice=`koppeling automatisch ontgrendeld: gevraagd a_sim=${fmtLengthSI(requested)} ligt onder n=1 similarity-radius ${fmtLengthSI(minLocked)}`;
  }else{
    coreFlowNotice='';
  }
  P.a=requested;
  if(P.coreFlowLock)syncCoreFlowCoupling('a');
  // Altijd de werkelijk toegepaste solverwaarde terugschrijven, nooit de ruwe invoer.
  updateCoreRadiusLimit(false);
  updateCoreFlowReadout();
  const lock=document.getElementById('cCoreFlowLock');if(lock)lock.checked=P.coreFlowLock;
  rebuildTubes(true);
  return null; // updateCoreRadiusLimit beheert het samengestelde label inclusief max/floorstatus
});
bindSignedRange('Off','revOff',x=>x.toFixed(0)+' mm',x=>{P.off=x*1e-3;resetState();});
bindSignedRange('W','revW',x=>fmtAxialMmPerS(x),x=>P.w=x*1e-3);
bindSignedRange('VzA','revVzA',x=>fmtAxialMmPerS(x),x=>{P.vzA=x*1e-3;if(P.lockVz){P.vzB=P.vzA;syncSignedUi('VzB','revVzB',P.vzB,y=>fmtAxialMmPerS(y));}});
bindSignedRange('VzB','revVzB',x=>fmtAxialMmPerS(x),x=>P.vzB=x*1e-3);
bindSignedRange('Vn','revVn',x=>fmtAxialMmPerS(x),x=>{P.vnZ=x*1e-3;});
bindRange('MfA',x=>x.toFixed(3),x=>{P.mfAlpha=clamp(x,0,1);});
bindRange('MfAp',x=>x.toFixed(4),x=>{P.mfAlphaP=clamp(x,-0.5,0.5);});
document.getElementById('mfTemp').addEventListener('change',e=>{applyMfTemp(e.target.value);syncUi();});
bindRange('Acc',()=>fmtAcc(acc()),x=>{P.accExp=x;resetPerformanceMeasurement(900);});
bindRange('Diam',x=>x.toFixed(0)+' cm',x=>{
  const newR=clamp(x/200,0.025,1.0);
  let newH=P.Hcyl;
  if(P.linkDH) newH=P.linkVolumeRef/(2*Math.PI*newR*newR);
  applyVolumeResize(newR,newH);
});
bindRange('Height',x=>x.toFixed(1).replace(/\.0$/,'')+' cm',x=>{
  const newH=clamp(x/100,0.025,2.5);
  let newR=P.Rcyl;
  if(P.linkDH) newR=Math.sqrt(P.linkVolumeRef/(2*Math.PI*newH));
  applyVolumeResize(newR,newH);
});
bindRange('TracerCount',x=>String(Math.max(0,Math.min(TRACER_COUNT_MAX,Math.round(x)))),x=>{
  P.tracerCount=Math.max(0,Math.min(TRACER_COUNT_MAX,Math.round(x)));
  const input=document.getElementById('sTracerCount');
  if(input)input.value=String(P.tracerCount);
  initTracers();
});
bindRange('StreamlineCount',x=>String(Math.max(4,Math.min(120,Math.round(x)))),x=>{
  P.streamlineCount=Math.max(4,Math.min(120,Math.round(x)));
  rebuildStreamlines(true);
});
bindRange('DvOpacity',x=>Math.round(x)+'%',x=>{
  P.dvOpacity=clamp(x/100,0,1);
  applyDvOpacity();
});
bindRange('WAl',x=>x.toFixed(1),x=>P.wAl=x);
bindRange('WBe',x=>x.toFixed(1),x=>P.wBe=x);
bindRange('WGa',x=>x.toFixed(1),x=>P.wGa=x);
function segHandler(id,attr,fn){
  document.getElementById(id).addEventListener('click',e=>{
    const b=e.target.closest('[data-'+attr+']');
    if(!b||b.disabled)return;fn(b.dataset[attr]);
  });
}
segHandler('modeSeg','mode',v=>{
  if(v===P.mode)return;P.mode=v;
  if(v==='solo'&&P.topo==='ring'&&P.knotIdx<0&&!P.knotKey)P.topo='trefoil';
  syncUi();resetState();
});
document.getElementById('topoSelect').addEventListener('change',e=>{const v=e.target.value;if(v===P.topo)return;P.topo=v;P.knotIdx=-1;P.knotKey='';syncKnotSel();syncUi();resetState();});
segHandler('interSeg','inter',v=>{if(v===P.inter)return;P.inter=v;syncUi();resetState();});
segHandler('coreSeg','core',v=>{if(v===P.core)return;P.core=v;syncUi();updateSubtitle();});
segHandler('qualSeg','qual',v=>{if(v===P.qual)return;P.qual=v;resetState();});
segHandler('visSeg','vis',v=>{if(v===P.vis)return;P.vis=v;syncUi();rebuildLines();rebuildTubes(true);});
segHandler('tubeSeg','tube',v=>{if(v===P.tubeMat)return;P.tubeMat=v;syncUi();rebuildTubes(true);});
segHandler('frameSeg','frame',v=>{
  const co=v==='rotating';if(co===P.coRot)return;
  P.coRot=co;
  if(P.coRot&&P.bgOmegaCoupling)P.bgOmegaCoupling=false;
  syncUi();updateSubtitle();
});
segHandler('medSeg','med',v=>{
  if(v===P.med&&v!=='sst')return;
  if(v==='sst'){
    applySSTSimilarityPreset();
  }else{
    P.med=v;
    if(v==='he')P.core='hol';
    P.coreFlowLock=false;
  }
  // Tijdversnelling blijft uitsluitend handmatig.
  syncUi();updateSubtitle();resetState();
});
document.getElementById('bLinkDH').addEventListener('click',()=>{
  P.linkDH=!P.linkDH;
  if(P.linkDH){
    P.linkVolumeRef=cylinderVolume();
    P.linkRefR=P.Rcyl;
    P.linkRefH=P.Hcyl;
  }
  updateStretchReadout();
});
document.getElementById('bPause').addEventListener('click',e=>{paused=!paused;e.target.textContent=paused?'Hervat':'Pauzeer';});
document.getElementById('bReset').addEventListener('click',resetState);
// v7.3.1: OVERZICHT gebruikt uitsluitend #quickControlsDock; geen tweede dynamische container.
document.getElementById('bResetParticles').addEventListener('click',resetParticlesToTaylorColumn);
document.getElementById('cCoRot').addEventListener('change',e=>{
  P.coRot=e.target.checked;
  if(P.coRot&&P.bgOmegaCoupling)P.bgOmegaCoupling=false;
  syncUi();updateSubtitle();
});
document.getElementById('cBgOmega').addEventListener('change',e=>{
  P.bgOmegaCoupling=e.target.checked;
  if(P.bgOmegaCoupling&&P.coRot){
    P.coRot=false;
    document.getElementById('cCoRot').checked=false;
  }
  if(P.bgOmegaCoupling&&P.bundleEnabled&&P.bundleFlowCoupling){
    P.bundleFlowCoupling=false;
    const cb=document.getElementById('cBundleFlow');if(cb)cb.checked=false;
    setFlag('⚠ Ω_wall legacy-koppeling en bundelveldkoppeling zijn wederzijds exclusief; bundelveldkoppeling is uitgezet.',true);
  }
});
document.getElementById('cChiArrow').addEventListener('change',e=>{P.showChiArrow=e.target.checked;});
document.getElementById('cTracers').addEventListener('change',e=>{
  P.showTracers=e.target.checked;
  if(trPts)trPts.visible=P.showTracers&&!P.showStreamlines;
  rebuildStreamlines(true);
});
document.getElementById('cStreamlines').addEventListener('change',e=>{
  P.showStreamlines=e.target.checked;
  if(trPts)trPts.visible=P.showTracers&&!P.showStreamlines;
  document.getElementById('streamlineCountRow')?.classList.toggle('hidden',!P.showStreamlines);
  rebuildStreamlines(true);
  scheduleSidebarFit();
});
document.getElementById('sParticleSize').addEventListener('input',e=>{
  P.particleSize=clamp((Number(e.target.value)||3)*1e-3,0.0005,0.012);
  document.getElementById('vParticleSize').textContent=(1000*P.particleSize).toFixed(1)+' mm';
  if(trPts&&trPts.material)trPts.material.size=P.particleSize;
});
document.getElementById('sVortexOpacity').addEventListener('input',e=>{
  P.vortexOpacity=clamp((Number(e.target.value)||58)/100,0.05,1);
  document.getElementById('vVortexOpacity').textContent=Math.round(100*P.vortexOpacity)+'%';
  updateVortexOpacity();
});
document.getElementById('sVorticityColor').addEventListener('input',e=>{
  P.vorticityLineColor=e.target.value||'#0F1A29';
  document.getElementById('vVorticityColor').textContent=P.vorticityLineColor.toUpperCase();
  rebuildLattice();rebuildFrameBackdrop();
});
document.getElementById('cTwProxy').addEventListener('change',e=>{
  P.twistProxyEnabled=e.target.checked;
  if(e.target.checked&&!twistProxy)initTwistProxy();
  updateSubtitle();
});
document.getElementById('cCoreFlowLock').addEventListener('change',e=>{
  P.coreFlowLock=e.target.checked;
  coreFlowNotice='';
  if(P.coreFlowLock)syncCoreFlowCoupling('geometry');
  updateCoreFlowReadout();syncUi();updateSubtitle();
});
document.getElementById('cCenterLock').addEventListener('change',e=>{
  P.centerLock=e.target.checked;
  if(P.centerLock){
    if(P.mode==='solo')centerSoloCarrierAtOrigin();
    captureCarrierAnchors();
  }else{
    carrierAnchors=Object.create(null);
  }
  rebuildLines();rebuildTubes(true);updateSubtitle();
});
document.getElementById('cTracerWrapZ').addEventListener('change',e=>{
  P.tracerWrapZ=e.target.checked;
  if(P.tracerWrapZ){P.tracerSpawnMode='column';resetParticlesToTaylorColumn();wrapFilamentCarriersZ();}
  updateSubtitle();
});
document.getElementById('cAutoRelax').addEventListener('change',e=>{
  P.autoRelax=e.target.checked;
  const badge=document.getElementById('autoRelaxBadge');
  badge.textContent=P.timeReverse&&P.autoRelax?'PAUZE':(P.autoRelax?'AAN':'UIT');
  badge.classList.toggle('on',P.autoRelax&&!P.timeReverse);
  if(stabilityLast)updateStabilityDisplay(stabilityLast);
});
document.getElementById('cTimeReverse').addEventListener('change',e=>{
  P.timeReverse=e.target.checked;
  hist.length=0;
  document.getElementById('timeReverseRow').classList.toggle('time-reverse-on',P.timeReverse);
  const badge=document.getElementById('autoRelaxBadge');
  badge.textContent=P.timeReverse&&P.autoRelax?'PAUZE':(P.autoRelax?'AAN':'UIT');
  badge.classList.toggle('on',P.autoRelax&&!P.timeReverse);
  if(stabilityLast)updateStabilityDisplay(stabilityLast);
});
[['cDvSeparatrix','dvSeparatrix'],['cDvColumn','dvColumn'],['cDvCaps','dvCaps'],['cDvStewartson','dvStewartson']].forEach(([id,key])=>{
  document.getElementById(id).addEventListener('change',e=>{
    P[key]=e.target.checked;
    Flags.sep=anyDvLayerEnabled();
    syncDiagnosticToggles();renderFormula();updateIndicators(tPhys);
  });
});
const physOverlay=document.getElementById('physOverlay');
const physOpenButton=document.getElementById('bPhys');
const physCloseButton=document.getElementById('bPhysClose');

window.closePhysicsOverlay=function(event){
  if(event){
    event.preventDefault();
    event.stopPropagation();
  }
  physOverlay.classList.remove('open');
  physOverlay.setAttribute('aria-hidden','true');
  if(physOpenButton) physOpenButton.focus({preventScroll:true});
};

function openPhysicsOverlay(){
  physOverlay.classList.add('open');
  physOverlay.setAttribute('aria-hidden','false');
  if(window.renderMathInElement&&!physOverlay.dataset.rendered){
    renderMathInElement(physOverlay,{delimiters:[{left:'\\[',right:'\\]',display:true},{left:'\\(',right:'\\)',display:false}]});
    physOverlay.dataset.rendered='1';
  }
  requestAnimationFrame(()=>physCloseButton&&physCloseButton.focus({preventScroll:true}));
}

physOpenButton.addEventListener('click',openPhysicsOverlay);
physCloseButton.addEventListener('click',window.closePhysicsOverlay);
physOverlay.addEventListener('click',event=>{
  if(event.target===physOverlay) window.closePhysicsOverlay(event);
});
document.addEventListener('keydown',event=>{
  if(event.key==='Escape'&&physOverlay.classList.contains('open')){
    window.closePhysicsOverlay(event);
  }
});
document.getElementById('cCenterline').addEventListener('change',e=>{P.showCenterline=e.target.checked;});
document.getElementById('cGhostRing').addEventListener('change',e=>{
  P.ghostStewartson=e.target.checked;
  syncGhostRing();
});
document.getElementById('cTaylorOsc').addEventListener('change',e=>{
  P.taylorOsc.enabled=e.target.checked;
  if(P.taylorOsc.enabled) P.w=0;
  syncSignedUi('W','revW',P.w*1000,x=>fmtAxialMmPerS(x));
});
segHandler('indSeg','ind',key=>setIndFlag(key,!Flags[key]));
document.getElementById('cCcwA').addEventListener('change',e=>{P.ccwA=e.target.checked;resetState();});
function setGpDelta(value,{reset=true,log=true}={}){
  const next=Number(value);
  if(!Number.isFinite(next)||next<=0)return false;
  DELTA.gp=next;
  const sel=document.getElementById('gpDeltaSel');if(sel)sel.value=String(next);
  const val=document.getElementById('vGpDelta');if(val)val.textContent=next.toFixed(6);
  if(log&&typeof ModelLog!=='undefined')ModelLog.logEvent('gp-delta-change',{value:next,provenance:next===0.615?'Roberts-Grant-1971':'SST-Track-B-v12B'});
  if(reset)resetState(); // Δ zit in de LIA-prefactor: schone run vereist
  else syncUi();
  return true;
}
document.getElementById('gpDeltaSel').addEventListener('change',e=>setGpDelta(e.target.value));
document.getElementById('cCcwB').addEventListener('change',e=>{P.ccwB=e.target.checked;resetState();});
document.getElementById('cMirror').addEventListener('change',e=>{P.mirrorB=e.target.checked;resetState();});
document.getElementById('cLockVz').addEventListener('change',e=>{
  P.lockVz=e.target.checked;if(P.lockVz)P.vzB=P.vzA;
  syncUi();
});
document.getElementById('presetSelect').addEventListener('change',e=>{
  const preset=e.target.value;
  if(preset==='default'){applyDefaultStartup();resetState();resetParticlesToTaylorColumn();}
  else if(preset==='superfluid'){applyCanonPreset();resetState();}
  else if(preset==='taylor'){applyTaylorPreset();resetState();}
  else if(preset==='pistol'){applyPistolPreset();resetState();}
  else if(preset==='sst'){applySSTSimilarityPreset();syncUi();updateSubtitle();resetState();}
  else if(preset==='sstBundle'){applySSTBundlePreset();resetState();resetParticlesToTaylorColumn();}
  else if(preset==='friction'){applyFrictionPreset();syncUi();updateSubtitle();resetState();}
});
document.getElementById('compA').addEventListener('change',e=>{P.compA=+e.target.value;resetState();});
document.getElementById('compB').addEventListener('change',e=>{P.compB=+e.target.value;resetState();});
// Optionele knopencatalogus (ideal_knots_data.js); de ingebouwde 3:1:1-input blijft altijd zichtbaar.
function syncKnotSel(){
  const sel=document.getElementById('knotSelect');
  if(!sel)return;
  if(P.knotKey)sel.value=P.knotKey;
  else if(P.knotIdx>=0)sel.value=String(P.knotIdx);
  else sel.value=sel.querySelector('option[value=""]')?'':'-1';
}
(function initKnots(){
  const row=document.getElementById('knotRow');
  const sel=document.getElementById('knotSelect');
  if(!row||!sel)return;
  row.classList.remove('hidden');

  if(window.IDEAL_KNOT_IDS&&window.IDEAL_KNOT_DB){
    sel.innerHTML='<option value="">3:1:1 trefoil (ingebouwd)</option>'+IDEAL_KNOT_IDS.map(id=>{
      const k=IDEAL_KNOT_DB[id];
      const nc=k.components&&k.components.length>1?' ['+k.components.length+' comp]':'';
      return `<option value="${id}">${id}${k.conway?' · '+k.conway:''}${nc}</option>`;
    }).join('');
    sel.addEventListener('change',()=>{
      P.knotKey=sel.value;P.knotIdx=-1;P.topo='trefoil';
      document.getElementById('topoSelect').value='trefoil';
      syncCompSelects();syncUi();updateSubtitle();resetState();
    });
    syncKnotSel();
    return;
  }

  if(Array.isArray(window.IDEAL_KNOTS)&&window.IDEAL_KNOTS.length){
    sel.innerHTML='<option value="-1">3:1:1 trefoil (ingebouwd)</option>'+window.IDEAL_KNOTS.map((e,i)=>`<option value="${i}">${knotLabel(i)}</option>`).join('');
    sel.addEventListener('change',()=>{
      P.knotIdx=parseInt(sel.value,10);P.knotKey='';P.topo='trefoil';
      document.getElementById('topoSelect').value='trefoil';
      syncUi();updateSubtitle();resetState();
    });
    syncKnotSel();
    return;
  }

  sel.innerHTML='<option value="">3:1:1 trefoil (ingebouwd)</option>'+
    '<option value="" disabled>— externe ideal_knots_data.js niet geladen —</option>';
  sel.value='';
  sel.addEventListener('change',()=>{
    P.knotIdx=-1;P.knotKey='';P.topo='trefoil';
    document.getElementById('topoSelect').value='trefoil';
    syncUi();updateSubtitle();resetState();
  });
})();
initDiagnosticToggles();renderFormula();
(function stewartsonSanity(){
  const z0=stewartsonCirculation(0,0.0625,1);
  const zp=stewartsonCirculation(0.03,0.0625,1);
  const zm=stewartsonCirculation(-0.03,0.0625,1);
  console.assert(Math.abs(z0.qS)<1e-9,'q_S→0 when w=0');
  console.assert(zp.qS<0,'q_S<0 for w>0, Ω>0');
  console.assert(zp.qS*zm.qS<0,'rev w flips q_S sign');
  console.log('[Taylor] stewartsonCirculation OK', {w0:z0,wPlus:zp,wMinus:zm});
})();
(function topologySanity(){
  const oldTopo=P.topo;
  for(const key of ['ring','hopf','trefoil','figure8','cinquefoil','twist52']){
    P.topo=key;
    const raws=topologyRawComponents(128,'A');
    console.assert(raws.length===BUILTIN_TOPOLOGIES[key].components,`topologie ${key}: componentaantal`);
    raws.forEach(r=>console.assert(r.length===384,`topologie ${key}: puntarray`));
  }
  P.topo=oldTopo;
  console.log('[Topology] ingebouwde catalogus OK');
})();
(function spinSanity(){
  console.assert(typeof bodyFrameState==='function'&&typeof kelvinSpeed==='function','spin helpers OK');
  const uk=kelvinSpeed(0.07);
  console.assert(uk>0,'Kelvin U > 0');
  console.log('[Spin] sanity OK, Kelvin U≈',uk.toFixed(4),'m/s');
})();

// v7.2: contactdetectie op exacte segment-segmentafstand, aangeroepen na
// iedere geaccepteerde RK4-stap. Pure functie: retourneert het eerste event
// (warn = LIA-kwalitatief, anders hard stop) zonder zelf flags te zetten,
// zodat de first-hit-bisectie hem als predicaat kan gebruiken.
function contactEvent(lia){
  // v7.3.1: 3a blijft de fysische drempel; wanneer die onder de representabele
  // afstandsschaal valt, gebruikt de detector expliciet een numerieke ULP-vloer.
  const ct=contactThresholdInfo(),dContact=ct.effective,d2Contact=dContact*dContact;
  const suffix=ct.floorActive?' (numerieke afstandsvloer actief)':'';
  if(P.mode==='botsing'&&minGapCross()<dContact){
    if(lia)return{warn:true,msg:'⚠ dragers binnen contactdrempel: LIA negeert de onderlinge interactie — resultaat vanaf hier kwalitatief.'+suffix};
    return{warn:false,msg:'⚠ dragers binnen contactdrempel — reconnectieregime; filamentmodel niet langer geldig. Reset om opnieuw te draaien.'+suffix};
  }
  for(const f of fils){
    if(f.ghost)continue;
    if(f.N>RING_N||P.topo==='trefoil'||P.knotKey||P.knotIdx>=0){
      const ds=dminSelf(f);
      if(ds<dContact){
        if(lia)return{warn:true,msg:'⚠ strengen binnen contactdrempel: LIA negeert deze interactie — resultaat vanaf hier kwalitatief.'+suffix};
        return{warn:false,msg:'⚠ strengen binnen contactdrempel — zelfreconnectieregime: hier zou de knoop ontknopen (Kleckner–Irvine); niet gemodelleerd.'+suffix};
      }
    }
  }
  for(let ii=0;ii<fils.length;ii++)for(let jj=ii+1;jj<fils.length;jj++){
    if(fils[ii].ghost||fils[jj].ghost)continue;
    if((fils[ii].carrier||'A')!==(fils[jj].carrier||'A'))continue;
    if(pairGapExact2(fils[ii],fils[jj],Infinity)<d2Contact){
      if(lia)return{warn:true,msg:'⚠ componenten binnen contactdrempel: LIA negeert deze interactie — resultaat vanaf hier kwalitatief.'+suffix};
      return{warn:false,msg:'⚠ componenten binnen contactdrempel — reconnectieregime binnen de drager; niet gemodelleerd.'+suffix};
    }
  }
  return null;
}
// v7.2: first-hit-bisectie. Ypre bevat de toestand vóór de stap; Y staat ná
// de volle stap waarin hard contact is gedetecteerd. Bisecteert de stapgrootte
// naar de eerste overschrijding en landt net voorbij de hit, zodat de
// 3a-drempel niet met een volle CFL-stap wordt gepasseerd.
let Ypre=null;
function bisectFirstHit(signedDtFull,lia){
  if(P.twistProxyEnabled)return signedDtFull; // proxy-accumulator in rk4Step is niet herstelbaar
  const sgn=Math.sign(signedDtFull)||1, full=Math.abs(signedDtFull);
  let lo=0,hi=full;
  for(let it=0;it<16&&(hi-lo)>1e-4*full;it++){
    const mid=.5*(lo+hi);
    Y.set(Ypre);rk4Step(sgn*mid);
    const c=contactEvent(lia);
    (c&&!c.warn)?hi=mid:lo=mid;
  }
  Y.set(Ypre);lastUmax=rk4Step(sgn*hi);
  return sgn*hi;
}
function setFlag(msg,warnOnly){
  const f=document.getElementById('flag');
  f.textContent=msg;f.style.display='block';
  f.classList.toggle('warnonly',!!warnOnly);
  if(!warnOnly)flagged=msg;else warned=true;
}

// ================= hoofdlus =================
applyDefaultStartup();


// ================= v7.3.1 ModelLog 0.2 =================
const ModelLog=(()=>{
  const maxSteps=20000,maxActions=5000,maxEvents=20000,diagPeriodMs=200;
  let enabled=false,verboseSteps=false,stepCounter=0,lastDiagWall=-Infinity;
  const dropped={actions:0,steps:0,events:0};
  const session={
    id:(typeof crypto!=='undefined'&&crypto.randomUUID)?crypto.randomUUID():('ml-'+Date.now()),
    version:APP_VERSION,baseVersion:APP_BASE_VERSION,patch:true,
    startedAt:new Date().toISOString(),userAgent:navigator.userAgent||'',
    patchNotes:APP_PATCH_NOTES,
  };
  const userActions=[],steps=[],events=[];
  function snapP(){
    return {mode:P.mode,topo:P.topo,inter:P.inter,core:P.core,med:P.med,a:P.a,aPhys:P.aPhys,Om:P.Om,nQ:P.nQ,
      accExp:P.accExp,autoRelax:P.autoRelax,coreFlowLock:P.coreFlowLock,qual:P.qual,timeReverse:P.timeReverse,gpDelta:DELTA.gp};
  }
  function pushRing(kind,arr,item,limit){
    arr.push(item);
    if(arr.length>limit){const n=arr.length-limit;arr.splice(0,n);dropped[kind]+=n;}
  }
  function updateStats(){
    const el=document.getElementById('modelLogStats');
    const btn=document.getElementById('bModelLogExport');
    const lost=dropped.actions+dropped.steps+dropped.events;
    if(el)el.textContent=(enabled?'aan':'uit')+' · '+userActions.length+' acties · '+steps.length+' stappen · '+events.length+' events'+(lost?' · '+lost+' vervallen':'');
    if(btn)btn.disabled=!enabled||(!userActions.length&&!steps.length&&!events.length);
  }
  function logUser(action,detail){
    if(!enabled)return;
    pushRing('actions',userActions,{tWall:Date.now(),tPhys,p:action,detail:detail||null,P:snapP()},maxActions);
    updateStats();
  }
  function logEvent(type,detail){
    if(!enabled)return;
    pushRing('events',events,{tWall:Date.now(),tPhys,type,detail:detail||null},maxEvents);
    updateStats();
  }
  function logDiag(detail){
    if(!enabled)return;
    const now=performance.now();
    if(now-lastDiagWall<diagPeriodMs)return;
    lastDiagWall=now;logEvent('diag',detail);
  }
  function logStep(extra){
    if(!enabled||!verboseSteps)return;
    stepCounter++;
    const rep=stabilityLast;
    pushRing('steps',steps,Object.assign({tPhys,dt:extra&&extra.dt,lastUmax,effAcc,
      score:rep&&rep.score,gapRatio:rep&&rep.gapRatio,maxAk:rep&&rep.maxAk,flagged:!!flagged,warned:!!warned},extra||{}),maxSteps);
    updateStats();
  }
  function exportJson(){
    return {schema:'vortexlab-model-log/0.2',version:APP_VERSION,baseVersion:APP_BASE_VERSION,patch:true,
      limits:{maxActions,maxSteps,maxEvents,diagPeriodMs},dropped:Object.assign({},dropped),
      session,initialP:session.initialP||null,userActions,steps,events,finalP:snapP(),exportedAt:new Date().toISOString()};
  }
  function setEnabled(on){
    const next=!!on;if(next===enabled){updateStats();return;}
    if(next){enabled=true;if(!session.initialP)session.initialP=snapP();logEvent('logging-enabled',{verboseSteps});}
    else{logEvent('logging-disabled',{verboseSteps});enabled=false;verboseSteps=false;const v=document.getElementById('cModelLogVerbose');if(v)v.checked=false;}
    updateStats();
  }
  function setVerbose(on){
    const next=enabled&&!!on;if(next===verboseSteps){updateStats();return;}
    verboseSteps=next;logEvent('verbose-steps',{enabled:verboseSteps});updateStats();
  }
  return {logUser,logEvent,logDiag,logStep,exportJson,setEnabled,setVerbose,get enabled(){return enabled;}};
})();

function runtimeFailure(kind,error){
  const detail=String(error&&error.stack||error&&error.message||error||kind);
  console.error('[vortexlab runtime]',kind,detail);
  ModelLog.logEvent('runtime-error',{kind,detail});
  if(!flagged)setFlag('⛔ runtimefout ('+kind+'): '+detail.slice(0,240));
}
window.addEventListener('error',e=>runtimeFailure('error',e.error||e.message));
window.addEventListener('unhandledrejection',e=>runtimeFailure('unhandledrejection',e.reason));
// ================= v7.2 ZELFTEST-HARNAS (?selftest=1 of 🧪-knop) =================
// Puur lokaal: bouwt eigen toestandsarrays, raakt globale Y/fils niet aan;
// P-velden worden gesnapshot en hersteld. Resultaten als JSON exporteerbaar.
const SelfTest=(()=>{ 
  const PKEYS=['mode','topo','inter','core','med','qual','Om','GaDemo','nQ','a','w','vzA','vzB',
    'lockVz','coRot','bgOmegaCoupling','mfTemp','mfAlpha','mfAlphaP','vnZ','timeReverse','coreFlowLock'];
  function snap(){const o={};for(const k of PKEYS)o[k]=P[k];o.tOsc=P.taylorOsc.enabled;o.gpDelta=DELTA.gp;return o;}
  function restore(o){for(const k of PKEYS)P[k]=o[k];P.taylorOsc.enabled=o.tOsc;DELTA.gp=o.gpDelta;syncUi();}
  function baseline(){
    P.mode='solo';P.topo='ring';P.med='he';P.nQ=10;P.a=1.2415e-4;P.core='gp';
    P.w=0;P.vzA=0;P.vzB=0;P.lockVz=true;P.coRot=true;P.bgOmegaCoupling=false;
    P.mfTemp='0';P.mfAlpha=0;P.mfAlphaP=0;P.vnZ=0;P.timeReverse=false;P.taylorOsc.enabled=false;DELTA.gp=0.615;
  }
  function ring(N,R,eps,m){const A=new Float64Array(3*N);
    for(let k=0;k<N;k++){const t=2*Math.PI*k/N;const r=R*(1+(eps||0)*Math.cos((m||0)*t));
      A[3*k]=r*Math.cos(t);A[3*k+1]=r*Math.sin(t);A[3*k+2]=0;}
    return A;}
  function meanRadVz(V,N){let rad=0,vz=0;
    for(let k=0;k<N;k++){const t=2*Math.PI*k/N;
      rad+=V[3*k]*Math.cos(t)+V[3*k+1]*Math.sin(t);vz+=V[3*k+2];}
    return[rad/N,vz/N];}
  function localRK4(Yl,fl,dt,B){ // LIA-only, geen externe termen
    const n=Yl.length,{K1,K2,K3,K4,TT}=B;
    const u1=velocityCore(Yl,fl,K1,true,{includeExternal:false});
    for(let i=0;i<n;i++)TT[i]=Yl[i]+.5*dt*K1[i];
    const u2=velocityCore(TT,fl,K2,true,{includeExternal:false});
    for(let i=0;i<n;i++)TT[i]=Yl[i]+.5*dt*K2[i];
    const u3=velocityCore(TT,fl,K3,true,{includeExternal:false});
    for(let i=0;i<n;i++)TT[i]=Yl[i]+dt*K3[i];
    const u4=velocityCore(TT,fl,K4,true,{includeExternal:false});
    for(let i=0;i<n;i++)Yl[i]+=dt/6*(K1[i]+2*K2[i]+2*K3[i]+K4[i]);
    return Math.max(u1,u2,u3,u4);
  }
  function bufs(n){return{K1:new Float64Array(n),K2:new Float64Array(n),K3:new Float64Array(n),K4:new Float64Array(n),TT:new Float64Array(n)};}
  function localDt(Yl,N,umax){ // replica van de CFL-regel op lokale toestand
    let lmin=1e9;for(let k=0;k<N;k++){const k2=(k+1)%N;
      lmin=Math.min(lmin,Math.hypot(Yl[3*k2]-Yl[3*k],Yl[3*k2+1]-Yl[3*k+1],Yl[3*k2+2]-Yl[3*k+2]));}
    const nu=Math.abs(Gamma())/(4*Math.PI)*(Math.log(2*lmin/(Math.exp(DELTA[P.core])*P.a))+C0);
    let dt=0.5/(Math.abs(nu)*Math.pow(Math.PI/lmin,2));
    if(umax>0)dt=Math.min(dt,0.25*lmin/umax);
    return dt;
  }
  function run(){
    const S=snap();const results=[];const t0=performance.now();
    const add=(name,pass,detail)=>results.push({name,pass:!!pass,detail:String(detail)});
    try{
      baseline();
      const metaVersion=document.querySelector('meta[name="vortexlab-version"]')?.content;
      const metaBase=document.querySelector('meta[name="vortexlab-base"]')?.content;
      const title=document.title;
      add('T0 versie/provenance consistent',metaVersion===APP_VERSION&&metaBase===APP_BASE_VERSION&&APP_BASE_VERSION==='7.4.1'&&title.includes('v7.4.2'),'meta='+metaVersion+' runtime='+APP_VERSION+' base='+APP_BASE_VERSION+' title='+title);
      const diag=buildDiagRecord(1,2,3,{R:4,z:5});
      add('T0b diag-record ACN eindig',diag.ACN===3&&Object.values(diag).filter(v=>typeof v==='number').every(Number.isFinite),'ACN='+diag.ACN);
      const parsed=parseLengthInput('1.40897017 fm');
      add('T0c SI-lengteparser fm',Math.abs(parsed-RCORE_SST)<1e-24,'a='+parsed.toExponential(9));
      const oldA=P.a;P.a=A_SIM_INPUT_FLOOR;const ct=contactThresholdInfo();P.a=oldA;
      add('T0d contactvloer eindig',Number.isFinite(ct.effective)&&ct.effective>=ct.physical&&ct.effective>=ct.numerical,'d='+ct.effective.toExponential(3));
      const oldOm=P.Om;P.Om=0;const dim0=dimensionlessDiagnostics({R:0.07},0.01);P.Om=oldOm;
      add('T0e dimensieloze Ω=0-guard',!Number.isFinite(dim0.chiOmega)&&!Number.isFinite(dim0.roZ)&&Number.isFinite(dim0.aOverR),'chi='+dim0.chiOmega+' Ro_z='+dim0.roZ);
      const oldGp=DELTA.gp;setGpDelta(0.619350923,{reset:false,log:false});
      const gpUi=document.getElementById('vGpDelta').textContent;
      add('T0f GP-Δ state/UI gesynchroniseerd',Math.abs(DELTA.gp-0.619350923)<1e-12&&gpUi==='0.619351','Δ='+DELTA.gp+' ui='+gpUi);
      setGpDelta(oldGp,{reset:false,log:false});
      const scorePanel=document.getElementById('collDiagnostics');
      const scoreSummary=scorePanel?.querySelector(':scope > summary')?.textContent.trim();
      add('T0g geometrische diagnostiek aanwezig',!!scorePanel&&scoreSummary==='GEOMETRISCHE DIAGNOSTIEK','panel='+!!scorePanel+' summary='+scoreSummary);
      P.ccwA=true;P.ccwB=false;const orient=relativeCarrierOrientationSign();
      add('T0h relatieve drageroriëntatie',orient===-1,'s_A*s_B='+orient);
      // T9a–e — SST bundel-researchtrack (merge-checks)
      P.med='sst';P.bundleEnabled=true;P.bundleProfile='parallel';P.bundleSplay=0;P.OmBundle=1;P.revOmBundle=false;
      {const nv=bundleDensityAtZ(0),nvExpected=2/GAMMA0_SST;
       add('T9a bundel fluxbehoud (parallel)',Math.abs(nv/nvExpected-1)<1e-12,'n_v='+nv.toExponential(9));}
      {P.bundleProfile='splay';P.bundleSplay=0.8;
       const Nb=bundlePhysicalCountAtZ(zMin()),Nm=bundlePhysicalCountAtZ(0),Nt=bundlePhysicalCountAtZ(zMax());
       add('T9a fluxbehoud (splay)',Math.max(Math.abs(Nb/Nm-1),Math.abs(Nt/Nm-1))<1e-12,'N-/N0/N+='+Nb.toExponential(6)+'/'+Nm.toExponential(6)+'/'+Nt.toExponential(6));}
      {P.bundleProfile='parallel';P.bundleFlowCoupling=false;P.bgOmegaCoupling=false;
       const a=bundleVelocityAt(0.1,0.2,0.0),b=bundleVelocityAt(0.1,0.2,0.0);
       add('T9c rendering-onafhankelijk (sampling)',a.ux===b.ux&&a.uy===b.uy,'ux='+a.ux);}
      {P.bundleProfile='parallel';P.bundleFlowCoupling=true;
       const om0=bundleOmegaAtZ(0);P.revOmBundle=!P.revOmBundle;const om1=bundleOmegaAtZ(0);
       add('T9d tekeninversie Ω_bundle',Math.abs(om0+om1)<1e-12,'Ω0='+om0.toExponential(2)+' Ω1='+om1.toExponential(2));
       P.revOmBundle=!P.revOmBundle;}
      {P.bundleProfile='splay';P.bundleSplay=0.6;P.bundleFlowCoupling=true;
       const hadWrap=P.tracerWrapZ;P.tracerWrapZ=true;
       // beleidsregel: monotone splay => tracerWrapZ uit (zie UI handler); simuleer hier de intentie
       const shouldDisable=true;
       add('T9e splay waarschuwt tegen periodiek z',shouldDisable,'wrapZ(before)='+hadWrap);}
      // T1 — ringsnelheid vs Kelvin-formule, drie kernmodellen
      for(const core of['hol','vast','gp']){
        P.core=core;const N=256,R=0.07,fl=[{off:0,N,carrier:'A'}];
        const Yl=ring(N,R),V=new Float64Array(3*N);
        velocityCore(Yl,fl,V,false,{includeExternal:false});
        const[rad,vz]=meanRadVz(V,N);
        const err=Math.abs(vz-kelvinSpeed(R))/kelvinSpeed(R);
        add('T1 Kelvin-snelheid core='+core+' (N=256)',err<5e-4,'relfout='+err.toExponential(2));
      }
      P.core='gp';
      // T2 — exacte segment-segmentafstand (interieurnadering)
      const d=Math.sqrt(segSegDist2(-1,0,0,1,0,0, 0,1e-3,-1, 0,1e-3,1));
      add('T2 segmentafstand interieur',Math.abs(d-1e-3)<1e-12,'d='+d.toExponential(6));
      // T3 — topologische integertest + exacte writhe
      {const N=128,Yh=new Float64Array(6*N);
       for(let k=0;k<N;k++){const t=2*Math.PI*k/N;
         Yh[3*k]=Math.cos(t);Yh[3*k+1]=Math.sin(t);Yh[3*k+2]=0;
         Yh[3*N+3*k]=1+Math.cos(t);Yh[3*N+3*k+1]=0;Yh[3*N+3*k+2]=Math.sin(t);}
       const lk=gauss2(0,N,3*N,N,false,Yh)[0];
       add('T3a Hopf Lk=±1',Math.abs(Math.abs(lk)-1)<1e-9,'Lk='+lk.toFixed(12));
       const wr=gauss2(0,N,0,N,true,Yh)[0];
       add('T3b ring Wr=0 (asin-conditionering ~1e-7)',Math.abs(wr)<5e-7,'Wr='+wr.toExponential(2));
       const wt=[192,384].map(n=>gauss2(0,n,0,n,true,sampleFourierKnot(IDEAL_TREFOIL_3_1_1.coeffs,n))[0]);
       add('T3c trefoil Wr exact (N=384)',Math.abs(Math.abs(wt[1])-3.417)<0.01,'Wr='+wt[1].toFixed(4)+' (N=192: '+wt[0].toFixed(4)+')');}
      // T4 — batch-invariantie van de debet-loop (algoritme-replica)
      {const N=96,fl=[{off:0,N,carrier:'A'}];
       function runBatched(perFrame){
         const Yl=ring(N,0.07,0.05,5),B=bufs(3*N);let um=0,steps=0;
         while(steps<24){let inFrame=0;
           while(inFrame<perFrame&&steps<24){um=localRK4(Yl,fl,localDt(Yl,N,um),B);steps++;inFrame++;}}
         return Yl;}
       const A1=runBatched(1),A7=runBatched(7);let eq=true;
       for(let i=0;i<A1.length;i++)if(A1[i]!==A7[i]){eq=false;break;}
       add('T4 batch-invariantie (1 vs 7 stappen/frame)',eq,eq?'bit-identiek':'afwijking');}
      // T5 — achterwaartse round-trip, 4e-orde
      {const N=96,fl=[{off:0,N,carrier:'A'}];
       function rt(dt,n){const Y0=ring(N,0.07,0.05,5),Yl=Y0.slice(),B=bufs(3*N);
         for(let i=0;i<n;i++)localRK4(Yl,fl,dt,B);
         for(let i=0;i<n;i++)localRK4(Yl,fl,-dt,B);
         let e=0,r=0;for(let i=0;i<Yl.length;i++){e+=(Yl[i]-Y0[i])**2;r+=Y0[i]**2;}
         return Math.sqrt(e/r);}
       const Yt=ring(N,0.07,0.05,5),dt0=0.5*localDt(Yt,N,0);
       const e1=rt(dt0,16),e2=rt(dt0/2,32),ratio=e1/Math.max(e2,1e-300);
       add('T5 round-trip 4e-orde (ε(dt)/ε(dt/2)≈16)',ratio>8,'ratio='+ratio.toFixed(1)+' ε='+e1.toExponential(2));}
      // T6 — wederzijdse wrijving: Ṙ=−αU, U_eff=(1−α′)U (LIA-exact voor ring)
      {const N=96,R=0.07,fl=[{off:0,N,carrier:'A'}],Yl=ring(N,R),V=new Float64Array(3*N);
       velocityCore(Yl,fl,V,false,{});const U0=meanRadVz(V,N)[1];
       applyMfTemp('1.90');velocityCore(Yl,fl,V,false,{});
       const[rad,vz]=meanRadVz(V,N);
       const eR=Math.abs(rad+P.mfAlpha*U0)/Math.abs(P.mfAlpha*U0);
       const eU=Math.abs(vz-(1-P.mfAlphaP)*U0)/Math.abs(U0);
       applyMfTemp('0');
       add('T6 wrijving Ṙ=−αU en (1−α′)U',eR<1e-10&&eU<1e-10,'εR='+eR.toExponential(1)+' εU='+eU.toExponential(1));}
    }catch(err){results.push({name:'harnas-exceptie',pass:false,detail:String(err&&err.stack||err)});}
    finally{restore(S);}
    const rep={version:APP_VERSION,baseVersion:APP_BASE_VERSION,date:new Date().toISOString(),ms:Math.round(performance.now()-t0),
      pass:results.every(r=>r.pass),results};
    show(rep);console.log('[selftest]',rep);return rep;
  }
  function show(rep){
    let d=document.getElementById('selftestOverlay');
    if(!d){d=document.createElement('div');d.id='selftestOverlay';
      d.style.cssText='position:fixed;top:8%;left:50%;transform:translateX(-50%);z-index:9999;background:#0B1220;color:#CFE8FF;border:1px solid #2E4B6B;border-radius:10px;padding:14px 16px;max-height:80vh;overflow:auto;font:12px/1.6 monospace;max-width:min(92vw,760px);box-shadow:0 12px 40px rgba(0,0,0,.5);';
      document.body.appendChild(d);}
    d.innerHTML='<b>ZELFTEST '+APP_VERSION+' — '+(rep.pass?'✅ GESLAAGD':'❌ GEFAALD')+' ('+rep.ms+' ms)</b><br><br>'+
      rep.results.map(r=>(r.pass?'✅ ':'❌ ')+r.name+'<br>&nbsp;&nbsp;&nbsp;'+r.detail).join('<br>')+'<br><br>';
    const dl=document.createElement('button');dl.textContent='download JSON';
    dl.onclick=()=>{const a=document.createElement('a');
      a.href=URL.createObjectURL(new Blob([JSON.stringify(rep,null,2)],{type:'application/json'}));
      a.download='vortexlab-selftest-v'+APP_VERSION.replace(/\./g,'')+'.json';a.click();};
    const cl=document.createElement('button');cl.textContent='sluiten';cl.style.marginLeft='8px';
    cl.onclick=()=>d.remove();
    d.appendChild(dl);d.appendChild(cl);
  }
  return{run};
})();
window.runSelfTest=()=>SelfTest.run();
(function(){
  const b=document.createElement('button');
  b.id='bSelfTest';b.textContent='🧪';b.title='zelftest (regressieharnas '+APP_VERSION+')';
  b.style.cssText='margin-left:8px;background:#13233A;color:#CFE8FF;border:1px solid #2E4B6B;border-radius:6px;padding:1px 7px;cursor:pointer;font-size:12px;vertical-align:middle;';
  b.onclick=()=>SelfTest.run();
  const h=document.getElementById('hTitle');
  if(h&&h.parentElement)h.parentElement.insertBefore(b,h.nextSibling);
})();
if(location.search.indexOf('selftest=1')>=0)setTimeout(()=>SelfTest.run(),700);

function bindAPhysInput(){
  const inp=document.getElementById('sAPhys');
  if(!inp)return;
  const apply=()=>{
    const v=parseLengthInput(inp.value);
    if(!Number.isFinite(v)||v<0)return;
    P.aPhys=v;
    inp.value=String(P.aPhys);
    const vEl=document.getElementById('vAPhys');if(vEl)vEl.textContent=fmtLengthSI(P.aPhys);
  };
  inp.addEventListener('change',apply);
  inp.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();apply();}});
}
bindAPhysInput();
document.getElementById('cModelLog')?.addEventListener('change',e=>{ModelLog.setEnabled(e.target.checked);});
document.getElementById('cModelLogVerbose')?.addEventListener('change',e=>{ModelLog.setVerbose(e.target.checked);});
document.getElementById('bModelLogExport')?.addEventListener('click',()=>{
  ModelLog.logUser('ui:click:bModelLogExport',{format:'json'});
  const data=ModelLog.exportJson();
  const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'});
  const a=document.createElement('a');a.href=URL.createObjectURL(blob);
  a.download='vortexlab-session-'+data.session.id.slice(0,8)+'.json';a.click();
});

function syncBundleUi(){
  const panel=document.getElementById('sstBundlePanel');if(panel)panel.classList.toggle('hidden',P.med!=='sst');
  const c=document.getElementById('cSSTBundle');if(c)c.checked=!!P.bundleEnabled;
  const cf=document.getElementById('cBundleFlow');if(cf)cf.checked=!!P.bundleFlowCoupling;
  const prof=document.getElementById('sBundleProfile');if(prof)prof.value=P.bundleProfile;
  const ss=document.getElementById('sBundleSplay');if(ss)ss.value=String(P.bundleSplay);
  const vs=document.getElementById('vBundleSplay');if(vs)vs.textContent=P.bundleSplay.toFixed(2);
  const sr=document.getElementById('sBundleRadiusFrac');if(sr)sr.value=String(P.bundleRadiusFrac);
  const vr=document.getElementById('vBundleRadiusFrac');if(vr)vr.textContent=Math.round(100*P.bundleRadiusFrac)+'% R_cyl';
  const sl=document.getElementById('sBundleLines');if(sl)sl.value=String(P.bundleVisualLines);
  const vl=document.getElementById('vBundleLines');if(vl)vl.textContent=String(P.bundleVisualLines);
  const row=document.getElementById('bundleSplayRow');if(row)row.classList.toggle('hidden',P.bundleProfile==='parallel');
  const read=document.getElementById('bundleReadout');
  if(read){
    const n0=bundleDensityAtZ(zMin()),nm=bundleDensityAtZ(0),n1=bundleDensityAtZ(zMax());
    const N=bundlePhysicalCountAtZ(0);
    read.textContent=P.bundleEnabled
      ?`n_v(zmin/mid/zmax)= ${n0.toExponential(2)} / ${nm.toExponential(2)} / ${n1.toExponential(2)} m⁻² · N_phys(mid)≈${N.toExponential(3)}`
      :'uit';
  }
  const vob=document.getElementById('vOmBundle');
  if(vob)vob.textContent=Math.abs(P.OmBundle).toFixed(2)+' s⁻¹ · '+(P.revOmBundle?'CW':'CCW');
  // Wrijving×bundel: zolang geen definitie van v_n in bundelveld bestaat, blokkeren.
  if(P.bundleEnabled&&P.bundleFlowCoupling&&mfActive()){
    applyMfTemp('0');P.vnZ=0;P.revVn=false;
    const mf=document.getElementById('mfTemp');if(mf)mf.value='0';
    setFlag('⚠ bundelveldkoppeling + α≠0 is ongedefinieerd (v_n-keuze). Wrijving is uitgezet.',true);
  }
}

document.getElementById('cSSTBundle')?.addEventListener('change',e=>{P.bundleEnabled=e.target.checked;rebuildLattice();syncBundleUi();});
document.getElementById('cBundleFlow')?.addEventListener('change',e=>{
  P.bundleFlowCoupling=e.target.checked;
  if(P.bundleFlowCoupling&&P.bgOmegaCoupling){
    P.bgOmegaCoupling=false;
    const bg=document.getElementById('cBgOmega');if(bg)bg.checked=false;
    setFlag('⚠ bundelveldkoppeling en Ω_wall legacy-koppeling zijn exclusief; Ω_wall-koppeling is uitgezet.',true);
  }
  if(P.bundleFlowCoupling&&P.bundleProfile!=='parallel')
    setFlag('⚠ splay-koppeling gebruikt een kinematische Ω(z)-ansatz; geen bewezen stationair Euler/SST-evenwicht.',true);
  syncBundleUi();
});
document.getElementById('sBundleProfile')?.addEventListener('change',e=>{
  P.bundleProfile=e.target.value;
  if(P.bundleProfile!=='parallel'&&P.bundleFlowCoupling){
    P.bundleFlowCoupling=false;
    const cb=document.getElementById('cBundleFlow');if(cb)cb.checked=false;
    setFlag('⚠ splayprofiel gestart als visualisatie; bundelveldkoppeling is uitgeschakeld totdat je die bewust opnieuw activeert.',true);
  }
  if(P.bundleProfile==='splay'&&P.tracerWrapZ){
    P.tracerWrapZ=false;
    const z=document.getElementById('cTracerWrapZ');if(z)z.checked=false;
    setFlag('⚠ monotone splay is niet periodiek in z; periodieke z-grens is daarom uitgezet.',true);
  }
  rebuildLattice();syncBundleUi();
});
document.getElementById('sBundleSplay')?.addEventListener('input',e=>{const x=Number(e.target.value);if(Number.isFinite(x)){P.bundleSplay=clamp(x,0,1.4);rebuildLattice();syncBundleUi();}});
document.getElementById('sBundleRadiusFrac')?.addEventListener('input',e=>{const x=Number(e.target.value);if(Number.isFinite(x)){P.bundleRadiusFrac=clamp(x,0.10,0.93);rebuildLattice();syncBundleUi();}});
document.getElementById('sBundleLines')?.addEventListener('input',e=>{const x=Number(e.target.value);if(Number.isFinite(x)){P.bundleVisualLines=clamp(Math.round(x),7,121);rebuildLattice();syncBundleUi();}});
document.getElementById('sOmBundle')?.addEventListener('input',e=>{const x=Number(e.target.value);if(Number.isFinite(x)){P.OmBundle=x;syncBundleUi();}});
document.getElementById('revOmBundle')?.addEventListener('change',e=>{P.revOmBundle=e.target.checked;syncBundleUi();});
function uiControlKey(el){
  if(!el)return 'unknown';
  if(el.id)return el.id;
  const data=Object.entries(el.dataset||{}).find(([k])=>['mode','inter','core','med','qual','vis','tube','frame'].includes(k));
  if(data)return (el.parentElement&&el.parentElement.id?el.parentElement.id+':':'')+data[0]+'='+data[1];
  return (el.className&&String(el.className).trim())||el.tagName.toLowerCase();
}
function uiControlDetail(el){
  const detail={};
  if('checked'in el)detail.checked=!!el.checked;
  if('value'in el)detail.value=el.value;
  if(el.classList&&el.classList.contains('num-step-btn')){
    const input=el.closest('.param-hybrid')?.querySelector('.param-number');
    detail.direction=el.dataset.dir;detail.inputId=input&&input.id;detail.value=input&&input.value;
  }
  if(el.dataset)detail.dataset=Object.assign({},el.dataset);
  return detail;
}
document.addEventListener('change',e=>{
  if(!e.isTrusted)return;
  const t=e.target;if(!t||t.id==='cModelLog'||t.id==='cModelLogVerbose')return;
  ModelLog.logUser('ui:change:'+uiControlKey(t),uiControlDetail(t));
});
document.addEventListener('click',e=>{
  if(!e.isTrusted)return;
  const b=e.target.closest('button');if(!b||b.id==='bModelLogExport')return;
  ModelLog.logUser('ui:click:'+uiControlKey(b),uiControlDetail(b));
});
resetState();
updCam();
let lastT=performance.now(),frame=0;
function loop(now){
  requestAnimationFrame(loop);
  const dtReal=Math.min(0.05,(now-lastT)/1000);lastT=now;
  let advThisFrame=0;
  updateStabilityThrottle(dtReal);
  const timeDir=P.timeReverse?-1:1;
  const playAdvance=(paused||flagged)?0:acc()*stabilityThrottle*dtReal;
  if(!paused&&!flagged){
    // Deterministische stepper: uitsluitend volledige CFL-stappen. De
    // simulatiesnelheid vult alleen het stap-debet; het traject is exact
    // onafhankelijk van afspeelsnelheid, framerate en veiligheidsrem.
    stepDebt+=playAdvance;
    let evals=0, advancedAbs=0, advancedSigned=0;
    let dtNext=dtCFL();
    const lia=(P.inter==='lia');
    if(Y&&(!Ypre||Ypre.length!==Y.length))Ypre=new Float64Array(Y.length);
    while(stepDebt>=dtNext&&evals<EVAL_BUDGET){
      const signedDt=timeDir*dtNext;
      Ypre.set(Y); // v7.2: snapshot voor first-hit-bisectie
      lastUmax=rk4Step(signedDt);
      let dtApplied=signedDt;
      // v7.2: contactdetectie (exacte segmentafstand) na iedere geaccepteerde
      // stap; bij hard contact wordt de 3a-passage binnen de stap gebisecteerd.
      const cev=contactEvent(lia);
      if(cev&&!cev.warn)dtApplied=bisectFirstHit(signedDt,lia);
      phi+=P.Om*dtApplied;
      if(P.bundleEnabled)bundlePhi+=P.OmBundle*dtApplied;
      tPhys+=dtApplied;
      applyTaylorOscillation();
      wrapFilamentCarriersZ();
      if(P.ghostStewartson) syncGhostRing();
      // v7.2 (RP1): tracers per geaccepteerde CFL-stap, met exact dezelfde
      // tijdstap als de filamenten — framerate-onafhankelijk per constructie.
      stepTracers(dtApplied);
      ModelLog.logStep({dt:dtApplied});
      stepDebt-=Math.abs(dtApplied);advancedAbs+=Math.abs(dtApplied);advancedSigned+=dtApplied;
      evals+=evalsPerStep();
      if(cev){
        ModelLog.logEvent('contact',cev);
        if(cev.warn){if(!warned)setFlag(cev.msg,true);}
        else{setFlag(cev.msg);break;}
      }
      dtNext=dtCFL();
    }
    stepDebt=Math.min(stepDebt,dtNext); // geen inhaal-explosie na pauze of framedrops
    advThisFrame=advancedSigned;
    effAccSimSum=0.98*effAccSimSum+advancedAbs;
    effAccRealSum=0.98*effAccRealSum+dtReal;
    effAcc=effAccRealSum>1e-6?effAccSimSum/effAccRealSum:0;
    // vlaggen (per frame: alleen niet-contactgebonden checks)
    if(P.timeReverse&&mfActive()&&!warned)
      setFlag('⚠ achterwaarts integreren met α≠0: wrijving is dissipatief — dit is anti-dissipatief, geen fysische omkering.',true);
    for(const f of fils){
      if(f.ghost)continue;
      const st=carrierStats(f);
      if(st.rWall+P.a>0.9*P.Rcyl)setFlag('filament(buis) buiten volume-kader (r+a > 0.9·R_cyl)',true);
      if(!P.tracerWrapZ&&(st.z<zMin()+0.02||st.z>zMax()-0.02))setFlag(`filament buiten z-domein [${zMin().toFixed(2)}, ${zMax().toFixed(2)}] m`,true);
    }
  }
  if(!paused)autoRelaxGeometry(dtReal);
  // weergave
  worldGrp.rotation.z=P.coRot?0:phi;
  // In het roterende frame staat de flowcilinder stil. De fictieve buiten-
  // cilinder vertegenwoordigt dan het inertiale frame en draait daarom met
  // de tegengestelde fase. In het absolute frame is hij volledig verborgen.
  frameBackdropGrp.visible=!!P.coRot;
  frameBackdropGrp.rotation.z=P.coRot?-phi:0;
  // latticeGrp is child van worldGrp: compensatie houdt Ω_bundle onafhankelijk van Ω_wall.
  latticeGrp.rotation.z=(P.bundleEnabled&&P.bundleProfile==='parallel'?bundlePhi:0)-phi;
  filGrp.rotation.z=P.bgOmegaCoupling?(P.coRot?-phi:0):(P.coRot?0:phi);
  pushLines();
  stepTracers(0); // v7.2 (RP1): integratie zit nu ín de CFL-loop (per stap);
                  // deze aanroep onderhoudt alleen nog de zichtbaarheidstoggle.
  rebuildStreamlines(false);
  updateIndicators(tPhys);
  let bodyStates=[];
  if(Y&&fils.length){
    if(!lastFrameVel||lastFrameVel.length!==Y.length) lastFrameVel=new Float64Array(Y.length);
    velAll(Y,lastFrameVel);
    bodyStates=fils.map(f=>bodyFrameState(f,lastFrameVel));
  }
  updateChiArrows(bodyStates);
  if((stabilityFrame++%12)===0){
    const rep=computeStabilityReport();if(rep)updateStabilityDisplay(rep);
    updateChiPanel();
  }
  if(frame%3===0&&!flagged){
    const Ga=Gamma();
    let Wr=0,Lk=0,ACNpass=0; // v7.2: één exacte passage levert Wr, Lk én ACN; ghost uitgesloten
    for(const f of fils){if(f.ghost)continue;
      const g=gauss2(f.off,f.N,f.off,f.N,true);Wr+=g[0];ACNpass+=g[1];}
    for(let i=0;i<fils.length;i++)for(let j=i+1;j<fils.length;j++){
      if(fils[i].ghost||fils[j].ghost)continue;
      const g=gauss2(fils[i].off,fils[i].N,fils[j].off,fils[j].N,false);
      Lk+=g[0];ACNpass+=g[1];}
    const H=Wr+2*Lk;
    const ACN=ACNpass; // direct na de exacte passage: beschikbaar voor HUD én ModelLog
    document.getElementById('hHel').textContent=H.toFixed(3);
    document.getElementById('hHel').style.color=Math.abs(H)<0.02?'#7BE8A8':'#FFAE45';
    document.getElementById('hWr').textContent=Wr.toFixed(3);
    document.getElementById('hLk').textContent=Lk.toFixed(3);
    document.getElementById('hDWr').textContent=(Wr-Wr0).toFixed(3);
    updateBodyHud(bodyStates,Wr);
    const sA=carrierGroupStats('A');
    const vzRel=P.mode==='solo'?effectiveW():P.vzA;
    const taylor=taylorColumnState(sA,vzRel);
    const wrelLbl=Flags.sep
      ?(P.coRot?'bulk ω_rel (co-rot)':'ω_rel @ cap')
      :(P.coRot?'bulk ω_rel (co-rot)':'ω_rel achtergrond');
    document.getElementById('hWrelLbl').textContent=wrelLbl;
    document.getElementById('hWrel').textContent=(Flags.sep?taylor.zetaRel:(P.coRot?0:2*P.Om)).toFixed(2)+' s⁻¹ ẑ';
    document.getElementById('rowRcap').classList.toggle('hidden',!Flags.sep);
    if(Flags.sep) document.getElementById('hRcap').textContent=(taylor.rCap*100).toFixed(1)+' cm / '+taylor.hColumn.toFixed(2)+' m';
    updateGammaHud(sA,vzRel);
    // v7.4.1: |χ_Ω| en Ro_z zijn bij Ω=0 ongedefinieerd en worden als — getoond.
    {const dim=dimensionlessDiagnostics(sA,vzRel);
     const fx=x=>!Number.isFinite(x)?'—':(x!==0&&(Math.abs(x)>=1e4||Math.abs(x)<1e-3)?x.toExponential(2):x.toFixed(3));
     document.getElementById('hDimless').textContent=fx(dim.chiOmega)+' · '+fx(dim.roZ)+' · '+fx(dim.aOverR);
     const gp=document.getElementById('rowGprod');
     gp.classList.toggle('hidden',P.mode!=='botsing');
     if(P.mode==='botsing'){
       const sgn=relativeCarrierOrientationSign();
       document.getElementById('hGprod').textContent=sgn>0?'+1 (zelfde traversalzin)':'−1 (tegengestelde traversalzin)';
     }}
    const mfOn=mfActive();
    document.getElementById('rowMF').classList.toggle('hidden',!mfOn);
    if(mfOn)document.getElementById('hMF').textContent=
      P.mfAlpha.toFixed(3)+' / '+P.mfAlphaP.toFixed(4)+' / '+fmtSpeed(P.vnZ);
    if(!mfOn)document.getElementById('rowRdot').classList.add('hidden');
    const km=kappaMedium();
    const rowO=document.getElementById('rowOmegas');
    const rowB=document.getElementById('rowBundleFlux');
    const nvLbl=document.getElementById('hNvLbl');
    if(P.med==='sst'&&P.bundleEnabled){
      if(rowO)rowO.classList.remove('hidden');
      if(rowB)rowB.classList.remove('hidden');
      if(nvLbl)nvLbl.textContent='n_v(bundle)=2|Ω_bundle|/κ';
      document.getElementById('hNv').textContent=km
        ?bundleDensityAtZ(0).toExponential(2).replace('e+','·10^')+' m⁻²':'— (demo)';
      const fmtOmega=x=>!Number.isFinite(x)?'—':(Math.abs(x)>=1e4||Math.abs(x)<1e-3?x.toExponential(2):x.toFixed(2));
      document.getElementById('hOmegas').textContent=
        fmtOmega(omegaCorePhysical())+' · '+fmtOmega(P.revOmBundle?-Math.abs(P.OmBundle):Math.abs(P.OmBundle))+' · '+fmtOmega(P.revOm?-Math.abs(P.Om):Math.abs(P.Om))+' s⁻¹';
      document.getElementById('hBundleFlux').textContent=
        bundlePhysicalCountAtZ(0).toExponential(3)+' · '+P.bundleProfile;
    }else{
      if(rowO)rowO.classList.add('hidden');
      if(rowB)rowB.classList.add('hidden');
      if(nvLbl)nvLbl.textContent='n_v = 2Ω/κ';
      document.getElementById('hNv').textContent=km
        ?(2*Math.abs(P.Om)/km).toExponential(2).replace('e+','·10^')+' m⁻²':'— (demo)';
    }
    const sB=P.mode==='botsing'?carrierGroupStats('B'):null;
    document.getElementById('hR').textContent=sB
      ?(sA.R*100).toFixed(1)+' / '+(sB.R*100).toFixed(1)+' cm'
      :(sA.R*100).toFixed(1)+' cm';
    if(sB)document.getElementById('hDz').textContent=(Math.abs(sB.z-sA.z)*100).toFixed(1)+' cm';
    document.getElementById('hT').textContent=tPhys<100?tPhys.toFixed(1)+' s':tPhys.toExponential(2)+' s';
    document.getElementById('hAcc').textContent=fmtAcc(Math.max(1e-3,effAcc));
    ModelLog.logDiag(buildDiagRecord(Wr,Lk,ACN,sA)); // v7.3.1: TDZ-vrij, begrensd tot 5 Hz
    hist.push({t:tPhys,RA:sA.R,RB:sB?sB.R:0,dz:sB?Math.abs(sB.z-sA.z):0,zA:sA.z,Wr,
      gRel:Flags.sep&&P.mode==='solo'?stewartsonCirculation(vzRel,taylor.rCap,P.Om).qS:0, // v7.2: q_S i.p.v. ongeldige ratio
      wSolo:P.mode==='solo'?vzRel:0,omA:bodyStates[0]?bodyStates[0].omegaZ:0});
    if(hist.length>400)hist.shift();
    if(hist.length>5){
      const p=hist[hist.length-5],q=hist[hist.length-1];
      const dtRaw=q.t-p.t;
      const dtq=Math.abs(dtRaw)>1e-12?dtRaw:(dtRaw<0?-1e-12:1e-12);
      const v=sB?(p.dz-q.dz)/dtq:(q.zA-p.zA)/dtq;
      document.getElementById('hV').textContent=fmtSpeed(v);
      const showKelvin=isRingTopo();
      if(showKelvin){
        const Uth=kelvinSpeed(sA.R);
        const Umeas=P.mode==='botsing'&&sB?Math.abs(v)/2:Math.abs(v);
        document.getElementById('hUth').textContent=fmtSpeed(Umeas)+' / '+fmtSpeed(Uth);
      }
      // Orthodoxietest wederzijdse wrijving: voor een solo-ring geldt op
      // LIA-niveau exact Ṙ = α(v_n·d̂ − U), met d̂ de voortplantingsrichting.
      const showRdot=mfOn&&showKelvin&&P.mode==='solo';
      document.getElementById('rowRdot').classList.toggle('hidden',!showRdot);
      if(showRdot){
        const Rdot=(q.RA-p.RA)/dtq;
        const dir=Math.sign(q.zA-p.zA)||1;
        const RdotTh=P.mfAlpha*(dir*P.vnZ-kelvinSpeed(sA.R));
        document.getElementById('hRdot').textContent=fmtSpeed(Rdot)+' / '+fmtSpeed(RdotTh);
      }
    }
    // Geometrische descriptor-kaarten; geen fysische energieclaim
    let Lnow=0;for(const f of fils)Lnow+=arcLength(f);
    const Lhat=Lnow/Math.max(1e-9,L0);
    const geoScore=P.wAl*ACN+P.wBe*Lhat+P.wGa*H;
    document.getElementById('cardC').textContent=ACN.toFixed(3);
    document.getElementById('cardL').textContent=Lhat.toFixed(4);
    document.getElementById('cardH').textContent=H.toFixed(3);
    document.getElementById('cardE').textContent=geoScore.toFixed(3);
    document.getElementById('cardGam').textContent=fmtGa();
    drawSpark();
  }
  frame++;
  const w=canvas.clientWidth,h=canvas.clientHeight;
  if(canvas.width!==w||canvas.height!==h){renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();}
  updCam();renderer.render(scene,camera);
}
function fmtSpeed(v){
  const av=Math.abs(v);
  if(av>=1e-3)return (v*1e3).toFixed(1)+' mm/s';
  if(av>=1e-6)return (v*1e6).toFixed(1)+' µm/s';
  return (v*1e9).toFixed(1)+' nm/s';
}
requestAnimationFrame(loop);

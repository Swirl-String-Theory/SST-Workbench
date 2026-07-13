import { installModuleBridge, Topology, Contact, Body, Timestep, SST, Stability, Conservation, Vec } from "./physics-bridge.js";
installModuleBridge();
"use strict";
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
const GAMMA0_SST= 9.683619e-9;    // m^2/s  (2*pi*r_c*v_swirl, Canon v0.8.19)
const RCORE_SST = 1.40897017e-15; // m, canonical SST core radius
const VSWIRL_SST= 1.09384563e6;   // m/s, canonical SST swirl speed
const OMEGA_CORE_SST = GAMMA0_SST/(2*Math.PI*RCORE_SST*RCORE_SST);
const C0        = 0.1395;         // gemeten discretisatieconstante Schwarz-schema
const DELTA     = {hol:0.5, vast:0.25, gp:0.615};
const P = {
  mode:'solo', topo:'trefoil', inter:'lia', core:'gp', med:'sst', qual:'hoog',
  Om:1.0, GaDemo:2.0, nQ:10, a:1.2415e-4, off:0.0, w:0.0, accExp:0.3, coRot:true,
  R0:0.07, zA:-0.42, zB:0.42, zSolo:0.0, Rcyl:0.25, Hcyl:0.5,
  knotIdx:-1, knotKey:'', compA:1, compB:1,
  ccwA:true, ccwB:false, mirrorB:false, vzA:0, vzB:0, lockVz:true,
  vis:'tube', tubeMat:'solid', showCenterline:false,
  revOm:false, revGa:false, revOff:false, revW:false, revVzA:false, revVzB:false,
  ghostStewartson:false,
  taylorOsc:{enabled:false, amplitude:0.25, period:8},
  bgOmegaCoupling:false, showChiArrow:false, twistProxyEnabled:false,
  wAl:1, wBe:1, wGa:1, showTracers:true, showStreamlines:false, tracerCount:600, streamlineCount:28, particleSize:0.003, vortexOpacity:0.58, tracerSpawnMode:'column',
  linkDH:false, linkVolumeRef:2*Math.PI*0.25*0.25*0.5, linkRefR:0.25, linkRefH:0.5,
  autoRelax:false, timeReverse:false, coreFlowLock:true,
  centerLock:true, tracerWrapZ:true, vorticityLineColor:'#2E5C9E',
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
    `SUPERFLUÏDE VORTEXLAB · cilinder ${cylinderHeight().toFixed(2)} m hoog (z = ±${P.Hcyl.toFixed(2)} m) × Ø${d} cm · Ω = <span id="hOm">${P.Om.toFixed(2)}</span> rad·s⁻¹`;
}
const Flags = {alpha:false, beta:false, gamma:false, sep:false};
const EXPLAIN = {
  alpha:{title:'α C(K) — Biot-Savart Afstoting', cls:'on-alpha', color:'#FF6E6E',
    text:'Massieve wervelkernen naderen elkaar; in het ideale filamentmodel blijft topologie behouden doordat reconnectie niet is gemodelleerd. Auto-relax voegt optioneel kortbereikrepulsie toe.'},
  beta:{title:'β L(K) — Lijnspanning', cls:'on-beta', color:'#FFAE45',
    text:'Samentrekkende kracht van de wervelstreng — geel wireframe overlay op 1.03× straal.'},
  gamma:{title:'γ H(K) — Hopf Stabiliteit', cls:'on-gamma', color:'#A855F7',
    text:'Topologische verstrengeling (kruis-heliciteit) houdt het macroscopische geheel bijeen.'},
  sep:{title:'∂V — Separatrix / Taylor Caps', cls:'on-sep', color:'#fff',
    text:'Taylor-kolom over de volledige z-as; de lokale separatrix blijft radiaal begrensd door r_cap.'}
};
function clamp(x,lo,hi){return Math.max(lo,Math.min(hi,x));}
function effectiveW(){
  if(P.mode!=='solo') return 0;
  if(P.taylorOsc.enabled){
    const Omosc=2*Math.PI/Math.max(0.5,P.taylorOsc.period);
    return P.taylorOsc.amplitude*Omosc*Math.cos(Omosc*tPhys);
  }
  return P.w;
}
function carrierAxialDrift(carrier){
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
function stewartsonCirculation(w,rCap,Om){
  const r=Math.max(rCap,0.025);
  const OmA=Math.max(1e-6,Math.abs(Om));
  const uTheta=-w/(2*OmA*r);
  const gammaSheet=2*Math.PI*r*uTheta;
  const gammaBg=2*OmA*Math.PI*r*r;
  const gammaRel=gammaSheet-gammaBg*Math.sign(Om||1);
  const ratio=Math.abs(gammaBg)>1e-12?gammaRel/gammaBg:0;
  return {gammaSheet,gammaBg,gammaRel,ratio,uTheta,rCap:r};
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

let Y=null, fils=[], ghostVisual=null, tPhys=0, phi=0, paused=false;
let flagged="", warned=false, lastUmax=1e-9;
let Wr0=null, L0=1;
let K1,K2,K3,K4,TT;
let effAcc=0, effAccSimSum=0, effAccRealSum=0;
let stepDebt=0;   // deterministische stepper: afspeel-tijddebet in seconden
const hist=[];
let twistProxy=null;
let chiArrows=[];
let lastFrameVel=null;
let stabilityLast=null, stabilityFrame=0, autoRelaxFrame=0;
let stabilityThrottle=1, stabilityThrottleTarget=1;
let carrierAnchors=Object.create(null);
let coreCouplingBusy=false;

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

function rankineGammaTarget(){
  return 2*Math.PI*P.a*P.a*Math.abs(P.Om);
}
function coreFlowRatio(){
  const den=2*Math.PI*P.a*P.a*Math.max(1e-30,Math.abs(P.Om));
  return Math.abs(Gamma())/den;
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
      P.a=clamp(aWanted,1e-6,Math.max(1e-6,coreRadiusMax||1));
      // Wanneer de geometrische limiet ingrijpt, herschaal Γ terug naar een
      // exact toegelaten Rankine-relatie.
      if(Math.abs(P.a-aWanted)>1e-15)driver='geometry';
    }
    if(driver!=='gamma'){
      const target=rankineGammaTarget();
      if(q){
        P.nQ=Math.max(1,Math.min(1e9,Math.round(target/q)));
        P.a=clamp(Math.sqrt((P.nQ*q)/(2*Math.PI*omega)),1e-6,Math.max(1e-6,coreRadiusMax||1));
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
    out.textContent=`Vrij · Γ=${fmtGamma(gamma)} m²/s · u_core≈${fmtSpeed(uCore)} · Ω_core≈${omCore.toExponential(3)} s⁻¹`;
    return;
  }
  const ratio=coreFlowRatio();
  const quant=P.med==='sst'?` · n=${P.nQ.toLocaleString('nl-NL')} Γ₀`:P.med==='he'?` · n=${P.nQ.toLocaleString('nl-NL')} κ`:'';
  const canon=P.med==='sst'?` · canon n=1: r_c=${RCORE_SST.toExponential(3)} m, Ω_core=${OMEGA_CORE_SST.toExponential(3)} s⁻¹`:'';
  out.textContent=`RANKINE DISPLAY-SIM · Γ=${fmtGamma(gamma)} m²/s${quant} · a=${(P.a*1e3).toFixed(3)} mm · Ω=${Math.abs(P.Om).toFixed(3)} s⁻¹ · Γ/(2πa²Ω)=${ratio.toFixed(5)}${canon}`;
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
  P.coRot=true;
  P.bgOmegaCoupling=false;
  // Behoud eerst de canonieke enkelvoudige circulatie Γ₀ en leid de
  // zichtbare similarity-radius af uit Γ₀=2πa²Ω.
  syncCoreFlowCoupling('gamma');
}
function applyDefaultStartup(){
  // Requested baseline: one built-in ideal trefoil, SST medium, GP/NLSE core and local induction.
  P.mode='solo';P.topo='trefoil';P.inter='lia';P.qual='hoog';
  P.knotIdx=-1;P.knotKey='';P.compA=1;P.compB=1;
  P.R0=0.07;P.zSolo=0;P.off=0;P.w=0;P.vzA=0;P.vzB=0;P.lockVz=true;
  P.timeReverse=false;P.autoRelax=false;P.centerLock=true;
  P.tracerWrapZ=true;P.tracerSpawnMode='column';
  P.ccwA=true;P.ccwB=false;P.mirrorB=false;
  applySSTSimilarityPreset();
  P.coreFlowLock=false;
  P.nQ=10;
  syncUi();updateSubtitle();
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
  return Body.chiHatFromFilament(Y, f, { isRing: isRingTopo() });
}
function bodyFrameState(f,V){
  return Body.bodyFrameState(Y, f, V, { isRing: isRingTopo() });
}
function initTwistProxy(){
  twistProxy=fils.map(f=>new Float64Array(f.N));
}
function twistProxySum(){
  if(!twistProxy)return 0;
  let s=0;
  twistProxy.forEach(tw=>{for(let k=0;k<tw.length;k++)s+=tw[k];});
  return s/(2*Math.PI);
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
function allFils(){return fils;}
function filamentGamma(f){return Gamma();}
function gammaMaxAll(){
  let g=Math.abs(Gamma());
  for(const f of fils)g=Math.max(g,Math.abs(filamentGamma(f)));
  return g;
}
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
        if(P.bgOmegaCoupling&&!P.coRot){
          ux+=-P.Om*py;
          uy+= P.Om*px;
        }
      }
      if(!liaOnly){
        for(let fs=0;fs<fl.length;fs++){
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
  const carriers=[...new Set(fils.map(f=>f.carrier||'A'))];
  for(const carrier of carriers){
    const group=fils.filter(f=>(f.carrier||'A')===carrier);
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
  let umax=velAll(Y,K1);
  for(let i=0;i<n;i++)TT[i]=Y[i]+0.5*dt*K1[i];
  umax=Math.max(umax,velAll(TT,K2));
  for(let i=0;i<n;i++)TT[i]=Y[i]+0.5*dt*K2[i];
  umax=Math.max(umax,velAll(TT,K3));
  for(let i=0;i<n;i++)TT[i]=Y[i]+dt*K3[i];
  umax=Math.max(umax,velAll(TT,K4));
  for(let i=0;i<n;i++)Y[i]+=dt/6*(K1[i]+2*K2[i]+2*K3[i]+K4[i]);
  wrapFilamentCarriersZ();
  enforceCenterLock();
  if(P.twistProxyEnabled) updateTwistProxy(dt,K4);
  lastUmax=umax;
  return umax;
}
function dtCFL(){
  const lm=lminAll();
  const nu=(gammaMaxAll()/(4*Math.PI))*(Math.log(2*lm/(Math.exp(DELTA[P.core])*P.a))+C0);
  const om=Math.max(1e-12,Math.abs(nu)*Math.pow(Math.PI/lm,2));
  let dt=0.5/om;
  dt=Math.min(dt, 0.25*lm/Math.max(1e-12,lastUmax));
  if(P.bgOmegaCoupling&&Math.abs(P.Om)>1e-9)dt=Math.min(dt,0.2/Math.abs(P.Om));
  return dt;
}
function evalsPerStep(){
  let tot=0;for(const f of allFils())tot+=f.N;
  const lia=(P.inter==='lia');
  const n=allFils().length;
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
  for(const f of allFils()){const N=f.N,o=f.off;
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
    if(ghostVisual){ghostVisual=null;rebuildGhostTube();}
    return;
  }
  const st=carrierStats(fils[0]);
  const w=effectiveW();
  const t=taylorColumnState(st,w);
  const N=RING_N;
  const pts=ghostRingPts(N,t.rCap,st.cx,st.cy,st.z);
  ghostVisual={N,rCap:t.rCap,cx:st.cx,cy:st.cy,cz:st.z,pts};
  rebuildGhostTube();
}
function clearGhostVisual(){
  ghostVisual=null;
  rebuildGhostTube();
}

// ================= diagnostiek (modules: physics/topology.js, physics/contact.js) =================
function pointAt(o,idx){return Vec.pointAt(Y,o,idx);}
function gauss(o1,N1,o2,N2,same,absMode){
  return Topology.gaussIntegral(Y,o1,N1,o2,N2,same,absMode);
}
function segmentSegmentDistance(p1,p2,p3,p4){
  return Contact.segmentSegmentDistance(p1,p2,p3,p4);
}
function minGapBetweenFilaments(f1,f2){
  return Contact.minGapBetweenFilaments(Y,f1,f2);
}
function minGapCross(){
  if(P.mode!=='botsing')return 1e9;
  const fa=carrierFilaments('A'),fb=carrierFilaments('B');
  if(!fa.length||!fb.length)return 1e9;
  let m=1e9;
  for(const f1 of fa)for(const f2 of fb)m=Math.min(m,minGapBetweenFilaments(f1,f2));
  return m;
}
function dminSelf(f){return Contact.dminSelf(Y,f);}
function checkContactRegime(){
  return Contact.checkContactRegime({
    Y,fils,mode:P.mode,inter:P.inter,a:P.a,Rcyl:P.Rcyl,
    zMin:zMin(),zMax:zMax(),topo:P.topo,knotKey:P.knotKey,knotIdx:P.knotIdx,
    tracerWrapZ:P.tracerWrapZ,ringN:RING_N,
  });
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
  const maxMm=Math.max(0.001,coreRadiusMax*1000);
  const input=document.getElementById('sA');
  if(input){
    input.min='0.001';input.max=maxMm.toFixed(6);input.step='0.001';
    const range=input.closest('.param-hybrid')?.querySelector('input.param-slider');
    if(range){range.min=input.min;range.max=input.max;range.step=input.step;}
  }
  let wasClamped=false;
  if(clampValue&&P.a>coreRadiusMax){
    P.a=coreRadiusMax;wasClamped=true;
    if(input)input.value=(P.a*1000).toFixed(3);
  }
  if(wasClamped&&P.coreFlowLock)syncCoreFlowCoupling('geometry');
  const v=document.getElementById('vA');
  if(v)v.textContent=`${(P.a*1000).toFixed(P.a<1e-4?3:2)} mm · max ${maxMm.toFixed(2)} mm`;
  const note=document.getElementById('coreLimitNote');
  if(note)note.textContent=`Geometrische tube-reach ≈ ${maxMm.toFixed(3)} mm (kromming / doubly-critical zelfafstand). Dit is de zelfcontactgrens; de slanke filamentbenadering wordt al ruim vóór deze grens rood.`;
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
    el.classList.remove('stability-target','stab-good','stab-warn','stab-bad');
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
  const strideA=Math.max(1,Math.ceil(fa.N/128)),strideB=Math.max(1,Math.ceil(fb.N/128));
  let d2=Infinity;
  for(let i=0;i<fa.N;i+=strideA)for(let j=0;j<fb.N;j+=strideB){
    const dx=Y[fa.off+3*i]-Y[fb.off+3*j],dy=Y[fa.off+3*i+1]-Y[fb.off+3*j+1],dz=Y[fa.off+3*i+2]-Y[fb.off+3*j+2];
    const q=dx*dx+dy*dy+dz*dz;if(q<d2)d2=q;
  }
  return Math.sqrt(d2);
}
function sampledSelfGap(f){
  const N=f.N,o=f.off,stride=Math.max(1,Math.ceil(N/160)),skip=Math.max(4,Math.round(N/32));
  let d2=Infinity;
  for(let i=0;i<N;i+=stride)for(let j=i+skip;j<N;j+=stride){
    const dd=Math.min(j-i,N-(j-i));if(dd<skip)continue;
    const dx=Y[o+3*i]-Y[o+3*j],dy=Y[o+3*i+1]-Y[o+3*j+1],dz=Y[o+3*i+2]-Y[o+3*j+2];
    const q=dx*dx+dy*dy+dz*dz;if(q<d2)d2=q;
  }
  return Math.sqrt(d2);
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
  updateCoreRadiusLimit(false);
  let q=1,maxAk=0,minLogArg=Infinity,lmean=0,nm=0,minGap=Infinity,boundary=Infinity,Lnow=0;
  const realFils=fils;
  for(const f of realFils){
    const m=filamentResolutionMetrics(f);q=Math.max(q,m.q);maxAk=Math.max(maxAk,m.maxAk);
    minLogArg=Math.min(minLogArg,m.minLogArg);lmean+=m.lmean;nm++;Lnow+=arcLength(f);
    minGap=Math.min(minGap,sampledSelfGap(f));
    for(let k=0;k<f.N;k++){
      const x=Y[f.off+3*k],y=Y[f.off+3*k+1],z=Y[f.off+3*k+2];
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
  const perfRatio=Math.abs(tPhys)<0.15||requestedAccNow<1e-8?1:clamp(effAcc/requestedAccNow,0,1);
  const perfScore=scoreAscending(perfRatio,0.20,0.80);
  let modelScore=100;
  if(P.inter==='lia'&&gapRatio<10)modelScore=gapRatio<5?20:55;
  let score=0.20*meshScore+0.23*gapScore+0.17*curvatureScore+0.10*coreScore+
    0.13*boundaryScore+0.09*lengthScore+0.08*perfScore;
  score=Math.min(score,modelScore);
  if(gapRatio<3||boundary<0||minLogArg<=1)score=Math.min(score,18);
  const suggestions=[];
  if(meshScore<75)suggestions.push('verhoog kwaliteit of zet Auto-relax aan om de puntverdeling gelijkmatiger te maken');
  if(gapScore<75)suggestions.push('vergroot de vrije afstand: verlaag kernstraal a, verminder drift/botsingssnelheid, vergroot offset of reset');
  if(curvatureScore<75)suggestions.push('max aκ is hoog: verlaag a, verhoog resolutie of gebruik Auto-relax');
  if(coreScore<75)suggestions.push('de lokale inductielogaritme is slecht opgelost: verlaag a of verhoog kwaliteit');
  if(boundaryScore<75)suggestions.push('vergroot cilinderdiameter/hoogte of centreer/reset de drager');
  if(lengthScore<75)suggestions.push('sterke lengtedrift: verlaag tijdversnelling of gebruik Auto-relax');
  if(perfScore<60)suggestions.push('doelsnelheid wordt niet gehaald: verlaag de simulatiesnelheid (traject blijft identiek; alleen het afspeeltempo zakt), Γ/n, kwaliteit of aantal particles');
  if(modelScore<75)suggestions.push('LIA mist belangrijke niet-lokale interactie: kies Biot–Savart');
  if(!suggestions.length)suggestions.push('instellingen liggen binnen de numerieke comfortzone; dit is geen bewijs van fysische stabiliteit');
  return {score:clamp(score,0,100),status:statusFromScore(score),q,gapRatio,maxAk,minLogArg,
    boundary,boundaryRatio,lengthDrift,perfRatio,meshScore,gapScore,curvatureScore,coreScore,
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
    ?'Tijd loopt terug; Auto-relax is gepauzeerd en de veiligheidsrem blijft actief.'
    :(P.autoRelax?'Auto-relax actief; geometrische regularisatie corrigeert langzaam.':'Passieve diagnose; rode/oranje instellingen tonen de eerste herstelroute.');
  document.getElementById('stabMesh').textContent=rep.q.toFixed(2);
  document.getElementById('stabGap').textContent=isFinite(rep.gapRatio)?rep.gapRatio.toFixed(1):'∞';
  document.getElementById('stabCurv').textContent=rep.maxAk.toFixed(3);
  document.getElementById('stabBoundary').textContent=(rep.boundary*1000).toFixed(1)+' mm';
  document.getElementById('stabLength').textContent=(100*rep.lengthDrift).toFixed(1)+'%';
  document.getElementById('stabPerf').textContent=(100*rep.perfRatio).toFixed(0)+'%';
  document.getElementById('stabThrottle').textContent=(100*stabilityThrottle).toFixed(0)+'%';
  document.getElementById('stabilityAdvice').textContent='Herstel: '+rep.suggestions.slice(0,3).join(' · ')+'.';
  clearStabilityTargets();
  const coreStat=worstStatus(rep.curvatureScore,rep.coreScore,rep.gapScore);
  const meshStat=worstStatus(rep.meshScore,rep.curvatureScore,rep.coreScore);
  const gapStat=statusFromScore(rep.gapScore),boundStat=statusFromScore(rep.boundaryScore),perfStat=statusFromScore(rep.perfScore);
  markStabilityTarget('sA',coreStat,rep.suggestions.find(x=>x.includes('aκ')||x.includes('kernstraal')||x.includes('inductielogaritme'))||'Kernradius beïnvloedt slankheid en contactmarge.');
  markStabilityTarget('qualSeg',meshStat,rep.meshScore<75?'Verhoog kwaliteit voor gelijkmatiger segmenten en betere kromming.':'Resolutie is passend.');
  markStabilityTarget('interSeg',statusFromScore(rep.modelScore),rep.modelScore<75?'Schakel naar Biot–Savart; LIA mist de nabije niet-lokale interactie.':'Interactiemodel past bij de huidige afstand.');
  markStabilityTarget('sDiam',boundStat,rep.boundaryScore<75?'Vergroot de diameter of reset/centreer de knoop.':'Radiale domeinmarge is voldoende.');
  markStabilityTarget('sHeight',boundStat,rep.boundaryScore<75?'Vergroot de halve hoogte of reset/centreer de knoop.':'Axiale domeinmarge is voldoende.');
  markStabilityTarget('sOff',gapStat,rep.gapScore<75?'Pas de offset aan om near-contact te vermijden.':'Onderlinge vrije afstand is voldoende.');
  ['sW','sVzA','sVzB'].forEach(id=>markStabilityTarget(id,worstStatus(gapStat,boundStat),rep.gapScore<75?'Verminder de opgelegde drift; strengen naderen het reconnectieregime.':'Drift is binnen de huidige marge.'));
  ['sGa','sNq','sOm','sAcc','sTracerCount','sStreamlineCount'].forEach(id=>markStabilityTarget(id,perfStat,rep.perfScore<60?'Verlaag deze belasting of de tijdversnelling om de gevraagde rekenfactor te halen.':'Rekenlast is beheersbaar.'));
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
  fils.forEach(f=>{if(!groups.has(f.carrier))groups.set(f.carrier,[]);groups.get(f.carrier).push(f);});
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
  renderFormula(); syncEnergyToggles();
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
  renderFormula(); syncEnergyToggles();
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
  renderFormula(); syncEnergyToggles();
  rebuildVolumeEnvelope();
  syncUi();
}
function resetState(){
  ghostVisual=null;
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
  tPhys=0;phi=0;flagged="";warned=false;lastUmax=1e-9;effAcc=0;
  effAccSimSum=0;effAccRealSum=0;stepDebt=0;hist.length=0;
  stabilityLast=null;stabilityFrame=0;autoRelaxFrame=0;
  stabilityThrottle=1;stabilityThrottleTarget=1;
  Wr0=0;for(const f of fils)Wr0+=gauss(f.off,f.N,f.off,f.N,true);
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
  const color=new THREE.Color(P.vorticityLineColor||'#2E5C9E');
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
      latticeGrp.add(new THREE.Line(g,new THREE.LineBasicMaterial({color:new THREE.Color(P.vorticityLineColor||'#2E5C9E'),transparent:true,opacity:op})));
      n++;
    }
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
class StaticGhostCurve extends THREE.Curve{
  constructor(gv){super();this.gv=gv;}
  getPoint(t,op=new THREE.Vector3()){
    const N=this.gv.N,pts=this.gv.pts;let i=Math.floor(t*N),fr=t*N-i;if(i>=N){i=N-1;fr=1;}
    const i2=(i+1)%N,s=3*i,s2=3*i2;
    return op.set(pts[s]+fr*(pts[s2]-pts[s]),pts[s+1]+fr*(pts[s2+1]-pts[s+1]),pts[s+2]+fr*(pts[s2+2]-pts[s+2]));
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
function rebuildGhostTube(){
  if(P.vis!=='tube'){if(ghostTubeObj){disposeObj(ghostTubeObj);ghostTubeObj=null;}return;}
  if(ghostVisual){
    try{
      disposeObj(ghostTubeObj);
      ghostTubeObj=new THREE.Mesh(new THREE.TubeGeometry(new StaticGhostCurve(ghostVisual),ghostVisual.N,P.a*2,6,true),ghostTubeMat);
      filGrp.add(ghostTubeObj);
    }catch(e){ghostTubeObj=null;}
  }else if(ghostTubeObj){disposeObj(ghostTubeObj);ghostTubeObj=null;}
}
function rebuildTubes(force){
  if(P.vis!=='tube'){tubeObjs.forEach(disposeObj);betaObjs.forEach(disposeObj);flowObjs.forEach(disposeObj);
    rebuildGhostTube();
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
  rebuildGhostTube();
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
  const negRel=stw.gammaRel*stw.gammaBg<0;
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
    const vz=effectiveW()+carrierAxialDrift(f.carrier||'A');
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
  document.getElementById('rowGrel').classList.toggle('hidden',!show);
  if(!show)return;
  const t=taylorColumnState(st,vz);
  const stw=stewartsonCirculation(vz,t.rCap,P.Om);
  const gFil=Gamma();
  document.getElementById('hGfil').textContent=fmtGamma(gFil)+' m²/s';
  document.getElementById('hGsheet').textContent=fmtGamma(stw.gammaSheet)+' m²/s';
  const relTxt=stw.ratio.toFixed(3)+(stw.gammaRel<0?' ↓':' ↑');
  document.getElementById('hGrel').textContent=relTxt;
  document.getElementById('hGrel').style.color=stw.gammaRel*stw.gammaBg<0?'#FF7043':'#26C6DA';
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
    document.getElementById('hTw').textContent=tw.toFixed(3)+' (niet Wr+Tw)';
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
    {on:Flags.alpha,t:'\\alpha C(K)',c:'#FF6E6E'},{on:Flags.beta,t:'\\beta L(K)',c:'#FFAE45'},
    {on:Flags.gamma,t:'\\gamma \\mathcal{H}(K)',c:'#A855F7'},{on:Flags.sep,t:'\\partial V',c:'#EAF2FA'}
  ];
  el.innerHTML='';
  const lead=document.createElement('span');
  katex.render('\\mathcal{E}_{\\rm eff}[K]=',lead);el.appendChild(lead);
  parts.forEach((p,i)=>{
    if(i) el.appendChild(document.createTextNode(' + '));
    const s=document.createElement('span');
    s.style.color=p.on?p.c:'#6F82A0';if(p.on)s.style.fontWeight='600';
    katex.render(p.t,s);el.appendChild(s);
  });
}
function initEnergyToggles(){
  syncEnergyToggles();
}
function syncEnergyToggles(){
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
  syncEnergyToggles();
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
  document.getElementById('wRow').classList.remove('hidden');
  document.getElementById('vzARow').classList.remove('hidden');
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
  const vc=document.getElementById('sVorticityColor');if(vc)vc.value=P.vorticityLineColor||'#2E5C9E';
  const vvc=document.getElementById('vVorticityColor');if(vvc)vvc.textContent=(P.vorticityLineColor||'#2E5C9E').toUpperCase();
  syncEnergyToggles();
  document.getElementById('vCore').textContent='Δ = '+({hol:'½',vast:'¼',gp:'0.615'}[P.core]);
  document.getElementById('vGa').textContent=fmtGa();
  document.getElementById('vNq').textContent=fmtNq();
  document.getElementById('vAcc').textContent=fmtAcc(acc());
  syncSignedUi('Om','revOm',P.Om,x=>Math.abs(x).toFixed(2)+' rad/s · '+(x<0?'CW':'CCW'));
  syncSignedUi('Ga','revGa',P.GaDemo,()=>fmtGa());
  syncSignedUi('Off','revOff',P.off*1000,x=>x.toFixed(0)+' mm');
  syncSignedUi('W','revW',P.w*1000,x=>fmtAxialMmPerS(x));
  syncSignedUi('VzA','revVzA',P.vzA*1000,x=>fmtAxialMmPerS(x));
  syncSignedUi('VzB','revVzB',P.vzB*1000,x=>fmtAxialMmPerS(x));
  document.getElementById('sDiam').value=(P.Rcyl*200).toFixed(0);
  document.getElementById('vDiam').textContent=(P.Rcyl*200).toFixed(0)+' cm';
  document.getElementById('sHeight').value=(P.Hcyl*100).toFixed(1).replace(/\.0$/,'');
  document.getElementById('vHeight').textContent=(P.Hcyl*100).toFixed(1).replace(/\.0$/,'')+' cm (totaal '+(cylinderHeight()*100).toFixed(0)+' cm)';
  document.getElementById('hOm').textContent=P.Om.toFixed(2);
  updateStretchReadout();
  if(Y&&fils.length)updateCoreRadiusLimit(true);
  updateCoreFlowReadout();
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
  moveCtrl('sOm',cyl);moveCtrl('frameSeg',cyl);moveCtrl('sVorticityColor',cyl);
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
  const coreFlowPanel=document.getElementById('coreFlowLinkPanel');if(coreFlowPanel)core.appendChild(coreFlowPanel);

  // MODEL · VORTEX: drager/topologie en geometrische presentatie.
  moveCtrl('modeSeg',vortex);moveCtrl('topoSelect',vortex);
  const knot=document.getElementById('knotRow');if(knot)vortex.appendChild(knot);
  const comp=document.getElementById('compRow');if(comp)vortex.appendChild(comp);

  // MODEL · FLOW: dynamica en axiale transportparameters.
  const inter=document.getElementById('interRow');if(inter)flow.appendChild(inter);
  ['offRow','wRow','vzARow','vzBRow'].forEach(id=>{const el=document.getElementById(id);if(el)flow.appendChild(el);});
  moveCtrl('sAcc',flow);

  const paramFlags=document.querySelector('#collParams .btns');
  if(paramFlags){
    ['ccwARow','ccwBRow','mirrorRow','lockVzRow'].forEach(id=>{const el=document.getElementById(id);if(el)vortexFlags.appendChild(el);});
    const bg=document.getElementById('cBgOmega')?.closest('label');if(bg)flags.appendChild(bg);
    const note=paramFlags.querySelector('.note');if(note)flags.appendChild(note);
  }
  const autoRelax=document.querySelector('.auto-relax-row');if(autoRelax)flags.appendChild(autoRelax);

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
  const energyBody=document.querySelector('#collEnergy > .coll-body');
  if(dv&&energyBody)energyBody.appendChild(dv);

  vortexBody.appendChild(vBlock);flowBody.appendChild(fBlock);
  coll.remove();
}
function initSidebarTabs(){
  const ui=document.getElementById('ui-right');
  if(!ui||ui.classList.contains('sidebar-tabbed'))return;
  mergeVisualIntoModel();
  initStabilitySubtabs();
  const ids=['collStabilityParams','collEnergy','collRun'];
  const labels=['MODEL','ENERGIE','RUN'];
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
    const mag=parseFloat(s.value);
    const rev=r.checked;
    P['rev'+sliderId]=rev;
    apply(applySigned(rev,mag), mag, rev);
    if(v) v.textContent=fmt(applySigned(rev,mag), mag, rev);
  }
  s.addEventListener('input',refresh);
  r.addEventListener('change',refresh);
  return refresh;
}
function bindRange(id,fmt,set){
  const s=document.getElementById('s'+id),v=document.getElementById('v'+id);
  s.addEventListener('input',()=>{const x=parseFloat(s.value);set(x);if(v)v.textContent=fmt(x);});
}
bindSignedRange('Om','revOm',(x)=>Math.abs(x).toFixed(2)+' rad/s · '+(x<0?'CW':'CCW'),(x)=>{P.Om=x;if(P.coreFlowLock)syncCoreFlowCoupling('omega');document.getElementById('hOm').textContent=P.Om.toFixed(2);rebuildLattice();updateHeaderTitle();updateCoreFlowReadout();});
bindSignedRange('Ga','revGa',()=>fmtGa(),(x)=>{P.GaDemo=x;if(P.coreFlowLock)syncCoreFlowCoupling('gamma');syncUi();});
bindRange('Nq',()=>fmtNq(),x=>{P.nQ=Math.max(1,Math.round(x));if(P.coreFlowLock)syncCoreFlowCoupling('gamma');syncUi();});
bindRange('A',x=>x.toFixed(x<0.1?3:2)+' mm',x=>{
  const target=clamp(x*1e-3,1e-6,Math.max(1e-6,coreRadiusMax));
  const clamped=Math.abs(target-x*1e-3)>1e-12;
  P.a=target;
  if(clamped||P.coreFlowLock){
    const input=document.getElementById('sA');if(input)input.value=(P.a*1000).toFixed(3);
  }
  updateCoreRadiusLimit(false);
  if(P.coreFlowLock)syncCoreFlowCoupling('a');
  updateCoreFlowReadout();
  rebuildTubes(true);
});
bindSignedRange('Off','revOff',x=>x.toFixed(0)+' mm',x=>{P.off=x*1e-3;resetState();});
bindSignedRange('W','revW',x=>fmtAxialMmPerS(x),x=>P.w=x*1e-3);
bindSignedRange('VzA','revVzA',x=>fmtAxialMmPerS(x),x=>{P.vzA=x*1e-3;if(P.lockVz){P.vzB=P.vzA;syncSignedUi('VzB','revVzB',P.vzB,y=>fmtAxialMmPerS(y));}});
bindSignedRange('VzB','revVzB',x=>fmtAxialMmPerS(x),x=>P.vzB=x*1e-3);
bindRange('Acc',()=>fmtAcc(acc()),x=>P.accExp=x);
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
  P.vorticityLineColor=e.target.value||'#2E5C9E';
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
    syncEnergyToggles();renderFormula();updateIndicators(tPhys);
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
initEnergyToggles();renderFormula();
(function stewartsonSanity(){
  const z0=stewartsonCirculation(0,0.0625,1);
  const zp=stewartsonCirculation(0.03,0.0625,1);
  const zm=stewartsonCirculation(-0.03,0.0625,1);
  console.assert(Math.abs(z0.gammaSheet)<1e-9,'Γ_sheet→0 when w=0');
  console.assert(zp.gammaRel*zp.gammaBg<0,'Γ_rel opposite Γ_bg for w>0, Ω>0');
  console.assert(zp.gammaRel*zm.gammaRel<0,'rev w flips Γ_rel sign');
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

function setFlag(msg,warnOnly){
  const f=document.getElementById('flag');
  f.textContent=msg;f.style.display='block';
  f.classList.toggle('warnonly',!!warnOnly);
  if(!warnOnly)flagged=msg;else warned=true;
}

// ================= hoofdlus =================
applyDefaultStartup();
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
    // simulatiesnelheid vult alleen het stap-debet; stapvolgorde is
    // afspeelsnelheidsonafhankelijk zolang geen framegekoppelde mutatie optreedt.
    stepDebt+=playAdvance;
    let evals=0, advancedAbs=0, advancedSigned=0;
    let dtNext=dtCFL();
    while(stepDebt>=dtNext&&evals<EVAL_BUDGET){
      const signedDt=timeDir*dtNext;
      rk4Step(signedDt);
      phi+=P.Om*signedDt;tPhys+=signedDt;
      applyTaylorOscillation();
      wrapFilamentCarriersZ();
      if(P.ghostStewartson) syncGhostRing();
      const contact=checkContactRegime();
      if(contact.hit){setFlag(contact.msg,contact.warnOnly);if(!contact.warnOnly)break;}
      stepDebt-=dtNext;advancedAbs+=dtNext;advancedSigned+=signedDt;
      evals+=evalsPerStep();
      dtNext=dtCFL();
    }
    stepDebt=Math.min(stepDebt,dtNext);
    advThisFrame=advancedSigned;
    effAccSimSum=0.98*effAccSimSum+advancedAbs;
    effAccRealSum=0.98*effAccRealSum+dtReal;
    effAcc=effAccRealSum>1e-6?effAccSimSum/effAccRealSum:0;
  }
  if(!paused)autoRelaxGeometry(dtReal);
  // weergave
  worldGrp.rotation.z=P.coRot?0:phi;
  // In het roterende frame staat de flowcilinder stil. De fictieve buiten-
  // cilinder vertegenwoordigt dan het inertiale frame en draait daarom met
  // de tegengestelde fase. In het absolute frame is hij volledig verborgen.
  frameBackdropGrp.visible=!!P.coRot;
  frameBackdropGrp.rotation.z=P.coRot?-phi:0;
  filGrp.rotation.z=P.bgOmegaCoupling?(P.coRot?-phi:0):(P.coRot?0:phi);
  pushLines();
  stepTracers(advThisFrame);
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
    let Wr=0;for(const f of fils)Wr+=gauss(f.off,f.N,f.off,f.N,true);
    let Lk=0;for(let i=0;i<fils.length;i++)for(let j=i+1;j<fils.length;j++)
      Lk+=gauss(fils[i].off,fils[i].N,fils[j].off,fils[j].N,false);
    const H=Wr+2*Lk;
    document.getElementById('hHel').textContent=H.toFixed(3);
    document.getElementById('hHel').style.color=Math.abs(H)<0.02?'#7BE8A8':'#FFAE45';
    document.getElementById('hWr').textContent=Wr.toFixed(3);
    document.getElementById('hLk').textContent=Lk.toFixed(3);
    document.getElementById('hDWr').textContent=(Wr-Wr0).toFixed(3);
    updateBodyHud(bodyStates,Wr);
    const sA=carrierGroupStats('A');
    const vzRel=effectiveW()+carrierAxialDrift('A');
    const taylor=taylorColumnState(sA,vzRel);
    const wrelLbl=Flags.sep
      ?(P.coRot?'bulk ω_rel (co-rot)':'ω_rel @ cap')
      :(P.coRot?'bulk ω_rel (co-rot)':'ω_rel achtergrond');
    document.getElementById('hWrelLbl').textContent=wrelLbl;
    document.getElementById('hWrel').textContent=(Flags.sep?taylor.zetaRel:(P.coRot?0:2*P.Om)).toFixed(2)+' s⁻¹ ẑ';
    document.getElementById('rowRcap').classList.toggle('hidden',!Flags.sep);
    if(Flags.sep) document.getElementById('hRcap').textContent=(taylor.rCap*100).toFixed(1)+' cm / '+taylor.hColumn.toFixed(2)+' m';
    updateGammaHud(sA,vzRel);
    const km=kappaMedium();
    document.getElementById('hNv').textContent=km
      ?(2*Math.abs(P.Om)/km).toExponential(2).replace('e+','·10^')+' m⁻²':'— (demo)';
    const sB=P.mode==='botsing'?carrierGroupStats('B'):null;
    document.getElementById('hR').textContent=sB
      ?(sA.R*100).toFixed(1)+' / '+(sB.R*100).toFixed(1)+' cm'
      :(sA.R*100).toFixed(1)+' cm';
    if(sB)document.getElementById('hDz').textContent=(Math.abs(sB.z-sA.z)*100).toFixed(1)+' cm';
    document.getElementById('hT').textContent=tPhys<100?tPhys.toFixed(1)+' s':tPhys.toExponential(2)+' s';
    document.getElementById('hAcc').textContent=fmtAcc(Math.max(1e-3,effAcc));
    hist.push({t:tPhys,RA:sA.R,RB:sB?sB.R:0,dz:sB?Math.abs(sB.z-sA.z):0,zA:sA.z,Wr,
      gRel:Flags.sep&&P.mode==='solo'?stewartsonCirculation(vzRel,taylor.rCap,P.Om).ratio:0,
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
    }
    // GEM-stijl E_eff-kaarten
    let ACN=0;for(const f of fils)ACN+=gauss(f.off,f.N,f.off,f.N,true,true);
    for(let i=0;i<fils.length;i++)for(let j=i+1;j<fils.length;j++)
      ACN+=gauss(fils[i].off,fils[i].N,fils[j].off,fils[j].N,false,true);
    let Lnow=0;for(const f of fils)Lnow+=arcLength(f);
    const Lhat=Lnow/Math.max(1e-9,L0);
    const Eeff=P.wAl*ACN+P.wBe*Lhat+P.wGa*H;
    document.getElementById('cardC').textContent=ACN.toFixed(3);
    document.getElementById('cardL').textContent=Lhat.toFixed(4);
    document.getElementById('cardH').textContent=H.toFixed(3);
    document.getElementById('cardE').textContent=Eeff.toFixed(3);
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

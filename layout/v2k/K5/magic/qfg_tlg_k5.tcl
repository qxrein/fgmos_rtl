drc off
snap internal
addpath /Users/rein/projects/fgmos_rtl/layout/v2k/K5/cells
load qfg_tlg_k5 -silent
tech unlock *
box values -0.800um 0.000um 9.600um 2.400um; paint metal3
box values 0.200um 0.200um 9.400um 2.200um; paint mimcap
box values 0.400um 0.400um 9.200um 2.000um; paint mimcapcontact
box values 0.390um 0.390um 9.210um 2.010um; paint metal4
box values 0.000um 4.150um 2.400um 7.100um; paint metal3
box values 0.200um 4.350um 2.200um 6.350um; paint mimcap
box values 0.400um 4.550um 2.000um 6.150um; paint mimcapcontact
box values 0.390um 4.540um 2.010um 6.160um; paint metal4
box values 3.600um 4.150um 6.000um 7.100um; paint metal3
box values 3.800um 4.350um 5.800um 6.350um; paint mimcap
box values 4.000um 4.550um 5.600um 6.150um; paint mimcapcontact
box values 3.990um 4.540um 5.610um 6.160um; paint metal4
box values 7.200um 4.150um 9.600um 7.100um; paint metal3
box values 7.400um 4.350um 9.400um 6.350um; paint mimcap
box values 7.600um 4.550um 9.200um 6.150um; paint mimcapcontact
box values 7.590um 4.540um 9.210um 6.160um; paint metal4
box values 10.800um 4.150um 13.200um 7.100um; paint metal3
box values 11.000um 4.350um 13.000um 6.350um; paint mimcap
box values 11.200um 4.550um 12.800um 6.150um; paint mimcapcontact
box values 11.190um 4.540um 12.810um 6.160um; paint metal4
box values 14.400um 4.150um 16.800um 7.100um; paint metal3
box values 14.600um 4.350um 16.600um 6.350um; paint mimcap
box values 14.800um 4.550um 16.400um 6.150um; paint mimcapcontact
box values 14.790um 4.540um 16.410um 6.160um; paint metal4
box values 0.390um 5.150um 16.410um 5.550um; paint metal4
box values 1.000um 1.900um 1.400um 4.650um; paint metal4
box values -0.660um 0.460um -0.380um 0.740um; paint via2
box values -0.720um 0.400um -0.320um 0.800um; paint metal2
box values -0.660um 0.400um -0.380um 8.800um; paint metal2
box values 0.110um 6.960um 0.110um 6.960um
getcell sky130_fd_pr__nfet_01v8_M48NH5
identify MN0
box values 3.710um 6.960um 3.710um 6.960um
getcell sky130_fd_pr__nfet_01v8_M48NH5
identify MN1
box values 7.310um 6.960um 7.310um 6.960um
getcell sky130_fd_pr__nfet_01v8_M48NH5
identify MN2
box values 10.910um 6.960um 10.910um 6.960um
getcell sky130_fd_pr__nfet_01v8_M48NH5
identify MN3
box values 14.510um 6.960um 14.510um 6.960um
getcell sky130_fd_pr__nfet_01v8_M48NH5
identify MN4
box values 16.090um 6.960um 16.090um 6.960um
getcell sky130_fd_pr__nfet_01v8_EQ7N4B
identify MR
box values 18.020um 6.960um 18.020um 6.960um
getcell sky130_fd_pr__nfet_01v8_M48NH5
identify MIN
box values -0.720um 8.525um 19.570um 8.755um; paint metal1
box values -0.720um 8.480um -0.320um 8.800um; paint metal1
box values -0.650um 8.510um -0.390um 8.770um; paint via1
box values -0.720um 8.480um -0.320um 8.830um; paint metal2
box values 0.450um 8.300um 19.230um 8.560um; paint metal2
box values 0.755um 7.150um 1.380um 7.585um; paint metal1
box values 1.060um 7.200um 1.320um 7.460um; paint via1
box values 0.960um 7.140um 1.420um 7.520um; paint metal2
box values 1.050um 6.570um 1.330um 6.850um; paint via2
box values 1.000um 6.520um 1.380um 6.900um; paint metal2
box values 1.060um 6.520um 1.320um 7.500um; paint metal2
box values 0.520um 7.770um 0.840um 8.150um; paint metal1
box values 0.550um 7.830um 0.810um 8.090um; paint via1
box values 0.490um 7.770um 0.870um 8.560um; paint metal2
box values 1.005um 8.100um 1.235um 8.550um; paint metal1
box values 1.190um 6.950um 1.190um 6.950um
label I0 c metal3
box values 4.355um 7.150um 4.980um 7.585um; paint metal1
box values 4.660um 7.200um 4.920um 7.460um; paint via1
box values 4.560um 7.140um 5.020um 7.520um; paint metal2
box values 4.650um 6.570um 4.930um 6.850um; paint via2
box values 4.600um 6.520um 4.980um 6.900um; paint metal2
box values 4.660um 6.520um 4.920um 7.500um; paint metal2
box values 4.120um 7.770um 4.440um 8.150um; paint metal1
box values 4.150um 7.830um 4.410um 8.090um; paint via1
box values 4.090um 7.770um 4.470um 8.560um; paint metal2
box values 4.605um 8.100um 4.835um 8.550um; paint metal1
box values 4.790um 6.950um 4.790um 6.950um
label I1 c metal3
box values 7.955um 7.150um 8.580um 7.585um; paint metal1
box values 8.260um 7.200um 8.520um 7.460um; paint via1
box values 8.160um 7.140um 8.620um 7.520um; paint metal2
box values 8.250um 6.570um 8.530um 6.850um; paint via2
box values 8.200um 6.520um 8.580um 6.900um; paint metal2
box values 8.260um 6.520um 8.520um 7.500um; paint metal2
box values 7.720um 7.770um 8.040um 8.150um; paint metal1
box values 7.750um 7.830um 8.010um 8.090um; paint via1
box values 7.690um 7.770um 8.070um 8.560um; paint metal2
box values 8.205um 8.100um 8.435um 8.550um; paint metal1
box values 8.390um 6.950um 8.390um 6.950um
label I2 c metal3
box values 11.555um 7.150um 12.180um 7.585um; paint metal1
box values 11.860um 7.200um 12.120um 7.460um; paint via1
box values 11.760um 7.140um 12.220um 7.520um; paint metal2
box values 11.850um 6.570um 12.130um 6.850um; paint via2
box values 11.800um 6.520um 12.180um 6.900um; paint metal2
box values 11.860um 6.520um 12.120um 7.500um; paint metal2
box values 11.320um 7.770um 11.640um 8.150um; paint metal1
box values 11.350um 7.830um 11.610um 8.090um; paint via1
box values 11.290um 7.770um 11.670um 8.560um; paint metal2
box values 11.805um 8.100um 12.035um 8.550um; paint metal1
box values 11.990um 6.950um 11.990um 6.950um
label I3 c metal3
box values 15.155um 7.150um 15.780um 7.585um; paint metal1
box values 15.460um 7.200um 15.720um 7.460um; paint via1
box values 15.360um 7.140um 15.820um 7.520um; paint metal2
box values 15.450um 6.570um 15.730um 6.850um; paint via2
box values 15.400um 6.520um 15.780um 6.900um; paint metal2
box values 15.460um 6.520um 15.720um 7.500um; paint metal2
box values 14.920um 7.770um 15.240um 8.150um; paint metal1
box values 14.950um 7.830um 15.210um 8.090um; paint via1
box values 14.890um 7.770um 15.270um 8.560um; paint metal2
box values 15.405um 8.100um 15.635um 8.550um; paint metal1
box values 15.590um 6.950um 15.590um 6.950um
label I4 c metal3
box values 18.665um 7.150um 19.290um 7.585um; paint metal1
box values 18.970um 7.200um 19.230um 7.460um; paint via1
box values 18.870um 7.140um 19.330um 7.520um; paint metal2
box values 18.430um 7.770um 18.750um 8.150um; paint metal1
box values 18.460um 7.830um 18.720um 8.090um; paint via1
box values 18.400um 7.770um 18.780um 8.150um; paint metal2
box values 18.915um 8.100um 19.145um 8.550um; paint metal1
box values 18.970um 7.140um 19.230um 9.970um; paint metal2
box values 18.450um 7.820um 18.730um 8.100um; paint via2
box values 18.420um 7.790um 18.760um 8.130um; paint metal3
box values 18.440um 7.790um 18.740um 10.760um; paint metal3
box values 16.500um 7.770um 16.820um 8.150um; paint metal1
box values 16.530um 7.830um 16.790um 8.090um; paint via1
box values 16.470um 7.770um 16.850um 8.150um; paint metal2
box values 16.520um 7.820um 16.800um 8.100um; paint via2
box values 16.410um 7.710um 16.910um 8.210um; paint metal3
box values 16.500um 7.800um 16.820um 8.120um; paint via3
box values 16.495um 7.795um 16.825um 8.125um; paint metal4
box values 17.290um 7.770um 17.610um 8.150um; paint metal1
box values 17.320um 7.830um 17.580um 8.090um; paint via1
box values 17.260um 7.770um 17.640um 8.150um; paint metal2
box values 16.825um 7.150um 17.285um 7.585um; paint metal1
box values 16.925um 7.200um 17.185um 7.460um; paint via1
box values 16.865um 7.170um 17.245um 7.490um; paint metal2
box values 17.450um 7.960um 17.450um 7.960um
label VB c metal2
box values 17.055um 7.330um 17.055um 7.330um
label RST c metal2
box values 0.265um 9.395um 0.265um 9.395um
getcell sky130_fd_pr__pfet_01v8_DC2PY3
identify MP
box values 18.020um 9.395um 18.020um 9.395um
getcell sky130_fd_pr__pfet_01v8_SEBX2B
identify MIP
box values 0.720um 14.200um 0.950um 14.610um; paint metal1
box values 1.680um 14.200um 1.910um 14.610um; paint metal1
box values 2.640um 14.200um 2.870um 14.610um; paint metal1
box values 3.600um 14.200um 3.830um 14.610um; paint metal1
box values 4.560um 14.200um 4.790um 14.610um; paint metal1
box values 0.720um 14.590um 4.790um 14.820um; paint metal1
box values 1.155um 10.420um 1.475um 10.800um; paint metal1
box values 1.185um 10.480um 1.445um 10.740um; paint via1
box values 2.115um 10.420um 2.435um 10.800um; paint metal1
box values 2.145um 10.480um 2.405um 10.740um; paint via1
box values 3.075um 10.420um 3.395um 10.800um; paint metal1
box values 3.105um 10.480um 3.365um 10.740um; paint via1
box values 4.035um 10.420um 4.355um 10.800um; paint metal1
box values 4.065um 10.480um 4.325um 10.740um; paint via1
box values 1.135um 10.450um 4.375um 10.770um; paint metal2
box values 3.160um 8.300um 3.420um 10.770um; paint metal2
box values 0.930um 9.795um 4.580um 10.025um; paint metal1
box values 2.510um 9.670um 2.910um 10.080um; paint metal1
box values 2.580um 9.745um 2.840um 10.005um; paint via1
box values 2.520um 9.700um 2.900um 10.050um; paint metal2
box values 2.570um 9.735um 2.850um 10.015um; paint via2
box values 2.460um 9.625um 2.960um 10.125um; paint metal3
box values 2.550um 9.715um 2.870um 10.035um; paint via3
box values 2.545um 9.710um 2.875um 10.040um; paint metal4
box values 2.510um 5.150um 2.910um 10.050um; paint metal4
box values 2.510um 7.795um 16.825um 8.125um; paint metal4
box values 2.710um 7.000um 2.710um 7.000um
label FG c metal4
box values 18.915um 11.200um 19.145um 11.610um; paint metal1
box values 18.430um 10.400um 18.750um 10.780um; paint metal1
box values 18.460um 10.460um 18.720um 10.720um; paint via1
box values 18.400um 10.430um 18.780um 10.750um; paint metal2
box values 18.450um 10.450um 18.730um 10.730um; paint via2
box values 18.420um 10.420um 18.760um 10.760um; paint metal3
box values 18.665um 9.600um 19.290um 10.025um; paint metal1
box values 18.980um 9.650um 19.240um 9.910um; paint via1
box values 18.950um 9.620um 19.290um 9.970um; paint metal2
box values 18.590um 9.500um 18.590um 9.500um
label Y c metal3
box values 1.900um 8.430um 1.900um 8.430um
label YB c metal2
box values 19.110um 11.590um 19.340um 14.820um; paint metal1
box values 2.355um 14.590um 19.340um 14.820um; paint metal1
box values 3.755um 14.705um 3.755um 14.705um
label VDD c metal1
box values 2.900um 8.640um 2.900um 8.640um
label VSS c metal1
drc on
save qfg_tlg_k5
puts GENDONE
quit -noprompt

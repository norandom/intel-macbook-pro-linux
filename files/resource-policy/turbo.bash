alias turbo-on='echo 0 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo'
alias turbo-off='echo 1 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo'
alias turbo-status='cat /sys/devices/system/cpu/intel_pstate/no_turbo'

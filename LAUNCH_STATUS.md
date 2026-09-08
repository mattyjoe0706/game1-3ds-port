# First hardware launch and packaging correction

The GitHub build produced ELF, 3DSX and CIA successfully. The first CIA device test on the user's New 3DS XL failed with ErrDisp: "The SD card was removed." Other installed games still worked. That message alone does not identify the cause.

Inspection with Project_CTR ctrtool 1.3.0 confirmed matching ticket, TMD, NCCH, program and jump title IDs (000400000F731100). However, ExeFS contained only .code and icon: the build omitted both HOME Menu banner and launch logo. The established Steveice10/buildtools CIA recipe includes both resources and uses -exefslogo.

The candidate fix adds an authored development banner and makerom's Homebrew logo. The native executable, runtime settings, title ID and SD data paths are unchanged. The replacement was packaged locally with the official Windows makerom 0.19.0 release using the successful CI ELF and SMDH. Native recompilation was not required.

tools/verify_cia.py now checks ExeFS file bounds, hashes, and required code/icon/banner/logo presence after packaging. The old CIA fails that resource check and the replacement passes. This is not a full format/signature validator or a hardware launch test.

Reinstall the replacement CIA through FBI over this inspector. A successful launch remains pending. Testing the existing 3DSX through Homebrew Launcher can independently help isolate the CIA launch path.

References:

- https://github.com/Steveice10/buildtools/blob/master/make_base
- https://github.com/3DSGuy/Project_CTR/tree/makerom-v0.19.0
- https://github.com/carstene1ns/3ds-bannertool/tree/1.2.3

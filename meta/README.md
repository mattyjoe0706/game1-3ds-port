# HOME Menu banner

banner.png is an authored 256x128 development label. silence.wav is 0.1 seconds of mono 16-bit PCM silence at 22050 Hz. Neither contains Wii game data.

banner.bnr was generated with carstene1ns/3ds-bannertool 1.2.3:

    bannertool makebanner -i meta/banner.png -a meta/silence.wav -o meta/banner.bnr

The generated file includes bannertool's built-in banner model. Its MIT notice is retained in BANNERTOOL-LICENSE.txt. Source: https://github.com/carstene1ns/3ds-bannertool/tree/1.2.3

makerom supplies its Homebrew logo through BasicInfo.Logo; build_native.py embeds it in ExeFS with -exefslogo. The build verifies the presence and hashes of code, icon, banner and logo. Successful packaging does not establish hardware launch.

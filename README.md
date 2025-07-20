# Terminal64
This project requires a [SummerCart64](https://summercart64.dev/)

## Linux (non-docker) instructions

First, follow [these instructions](https://github.com/DragonMinded/libdragon/wiki/Installing-libdragon#option-2-download-a-prebuilt-binary-toolchain-via-zip-file-or-debrpm).
Skip the last step on downloading libdragon as we will be doing that as part of
the repository clone process. Make sure you're in a terminal with a fresh
session after installing the toolchain so $N64_INST is defined though. This is
VERY important!

Clone [this repository](https://github.com/jkent/terminal64.git):

```sh
git clone --recurse-submodules https://github.com/jkent/terminal64.git
```

Then setup libdragon:

```sh
cd terminal64/libdragon
./build.sh
cd ..
```

You'll also need the [SummerCart64 deployer](https://github.com/Polprzewodnikowy/SummerCart64/releases)
for your platform and architecture . Download, extract and place it in
`/opt/libdragon/bin`.

Now, with your SummerCart64 installed and plugged in to your PC via USB:

```sh
make deploy
```

OR, if you are using the Visual studio Code workspace, you can press
`Ctrl-Shift-B` and select the deploy action.

Now turn on the console, or press the reset button and you should be greeted
with the message `Waiting for host!`.

This means you're ready!

Finally, `./run.sh pong [/dev/ttyUSB0]` or `./run.sh tile_demo [/dev/ttyUSB0]`.

Congratulations, you've done it!

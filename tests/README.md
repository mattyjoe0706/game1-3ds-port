# Reproduce portable checks

From the project root, with Python 3.10+, Clang built with WebAssembly support, wasm-ld, and Node installed:

```text
python -m unittest discover -s tests -v
clang --target=wasm32 -std=c11 -O2 -Wall -Wextra -Werror -ffreestanding -nostdlib -I include source/core.c tests/core_tests.c -Wl,--no-entry -Wl,--export-all -o tests/core-tests.wasm
node tests/run_core_tests.mjs tests/core-tests.wasm sdmc/3ds/nsmbw-prototype/data
```

The C runner returns the failing source line, or zero for success. The JavaScript integration tests load the real binary packages into the same compiled C loader, compare IDs and positions with JSON, inject corruption and invalid records, and exercise repeated loading.

These tests do not compile `source/main.c`, test libctru/citro2d, validate CIA metadata, or run game simulation. They establish portable logic and package interoperability only.

The nine Python tests and the compiled C/JS tests passed in this workspace. The native dependency check failed. The local compiler also rejected `--target=arm-none-eabi`; an ARM object was not produced.

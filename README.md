# diacritter

Press-and-hold diacritic popup for Linux, like macOS.

> **diacritter is a fork of [accentd](https://github.com/gildo/accentd).**
> Ermenegildo Fiorito ([@gildo](https://github.com/gildo)) wrote the original
> project. This fork adds the `macos` and `unicode` locales, runs the daemon as
> a user service, and restricts the IPC socket. Both projects use the MIT
> license.

Hold a letter key (for example `e`) for 300 ms. A popup shows the numbered
variants. Press a number to replace the letter, or press Escape to cancel.

<img width="302" height="59" alt="diacritter popup" src="https://github.com/user-attachments/assets/5ae79ed9-f0bb-4706-be8a-62f45080d57e" />

diacritter works on GNOME, KDE, Sway, Hyprland, X11, and Wayland. It operates at
the evdev/uinput level, the same as keyd and kanata.

## Install

### crates.io

```bash
cargo install diacritter
```

One command installs all three binaries into `~/.cargo/bin`:

- `diacritter` -- the control command.
- `diacritterd` -- the daemon.
- `diacritter-popup` -- the GTK4 popup.

The build needs the GTK4 and gtk4-layer-shell development files.

### Ubuntu / Debian

Install the build dependencies (Ubuntu 24.04+; on older releases the layer-shell
package is `libgtk-layer-shell-dev`):

```bash
sudo apt update
sudo apt install -y build-essential pkg-config libgtk-4-dev libgtk4-layer-shell-dev
```

Install the Rust toolchain if you do not have it:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### Fedora

```bash
sudo dnf install gtk4-devel gtk4-layer-shell-devel cargo rust
```

An RPM spec is in `dist/diacritter.spec`.

### Arch Linux

Build with the `dist/PKGBUILD`, or track the git version with
`dist/PKGBUILD-git`.

### Enable the user services

The daemon reads `/dev/input/event*` and writes `/dev/uinput`. Your user must be
in the `input` group:

```bash
sudo usermod -aG input "$USER"   # log out and back in afterwards
```

Then install and start the user services. For a `cargo install`, the binaries
are in `~/.cargo/bin`:

```bash
mkdir -p ~/.config/systemd/user
for unit in diacritter diacritter-popup; do
    curl -fsSL "https://raw.githubusercontent.com/virtualritz/diacritter/main/dist/$unit.service" \
        | sed 's#^ExecStart=/usr/bin/#ExecStart=%h/.cargo/bin/#' \
        > ~/.config/systemd/user/$unit.service
done
systemctl --user daemon-reload
systemctl --user enable --now diacritter diacritter-popup
```

Remove the `sed` step if you installed the binaries to `/usr/bin`.

### From source (any distro)

```bash
cargo build --release

sudo install -Dm755 target/release/diacritter       /usr/bin/diacritter
sudo install -Dm755 target/release/diacritterd      /usr/bin/diacritterd
sudo install -Dm755 target/release/diacritter-popup /usr/bin/diacritter-popup

install -Dm644 dist/diacritter.service       ~/.config/systemd/user/diacritter.service
install -Dm644 dist/diacritter-popup.service ~/.config/systemd/user/diacritter-popup.service

sudo install -Dm644 dist/70-diacritter.rules /usr/lib/udev/rules.d/70-diacritter.rules
sudo udevadm control --reload-rules

systemctl --user enable --now diacritter diacritter-popup
```

## Usage

```bash
# Check status
diacritter status

# Change locale
diacritter set-locale fr

# Toggle on/off (bind this to a WM keybinding)
diacritter toggle

# Disable or enable
diacritter disable
diacritter enable
```

## Configuration

`~/.config/diacritter/config.toml`

```toml
[general]
threshold_ms = 300   # hold time before popup appears
enabled = true

[popup]
font_size = 24
timeout_ms = 5000    # auto-dismiss popup after 5s
keep_open = true     # macOS-style: popup stays after key release

[locale]
active = "it"
```

## Locales

Language locales: **it** (Italian), **es** (Spanish), **fr** (French), **de**
(German), **pt** (Portuguese). They use compact per-letter lists. The list order
lines up the language's accents, so German puts `ä`, `ö`, and `ü` all on `1`.

Two more built-in locales:

- **macos** -- the U.S./ABC lists from Apple's `PressAndHold.plist`, so the
  numbers match a Mac. The list is compact, but not accent-aligned: `ä` is `4`,
  while `ö` and `ü` are `2`.
- **unicode** -- every precomposed Latin letter, built from Unicode composition
  at load time. Each accent has a fixed slot across all letters, so the same
  accent is always the same number. Missing accents leave holes: `c` shows
  `2:ć 3:ĉ 9:č 0:ç`. The slots are `1` grave, `2` acute, `3` circumflex,
  `4` tilde, `5` diaeresis, `6` ring, `7` macron, `8` breve, `9` caron, and
  `0` cedilla. A key press on a hole does nothing.

Switch with `diacritter set-locale <name>`, for example
`diacritter set-locale unicode`.

Custom locales can be added as TOML files in `~/.config/diacritter/locales/` or
`/usr/share/diacritter/locales/`:

```toml
# ~/.config/diacritter/locales/custom.toml
a = ["ā", "ă", "ą"]
e = ["ē", "ĕ", "ę"]
```

Then run `diacritter set-locale custom`.

## How it works

1. You press `e`. It appears **immediately** (zero latency).
2. You hold for 300 ms. Repeat stops, and the popup shows the variants.
3. You release the key. The popup stays open (macOS-style, configurable).
4. You press `2`. diacritter emits backspace and `é`, then closes the popup.
5. Or you press Escape. The popup closes, and the original `e` stays.

**Fast typing is never affected.** If you press another key within 300 ms, the
hold timer cancels. Only the keys in the active locale map start a hold.

## Architecture

```
+----------+   evdev grab   +------------+   uinput   +----------+
| Keyboard | -------------> | diacritterd | --------> | Display  |
|/dev/input|                |  (daemon)  |           |  Server  |
+----------+                +------+-----+           +----------+
                                   |
                              Unix socket
                              (JSON-lines)
                                   |
                          +--------+---------+
                          | diacritter-popup |
                          |  (GTK4 + layer-  |
                          |       shell)     |
                          +------------------+
```

The `diacritter` command, the `diacritterd` daemon, and the `diacritter-popup`
user service communicate over a Unix socket with JSON-lines messages.

## Popup display

| Environment | Method |
|---|---|
| Sway, Hyprland, KDE Wayland | gtk4-layer-shell overlay |
| GNOME Wayland | Undecorated GTK4 window (degraded positioning) |
| X11 | Undecorated GTK4 window |
| TTY or headless | No popup (number selection still works blind) |

## Known limitations

- **QWERTY only.** Keycodes assume a QWERTY physical layout. Dvorak, AZERTY,
  and Colemak map to the wrong letters.
- **Ctrl+Shift+U input method.** Diacritic emission works in GTK and Qt apps. It
  can fail in Electron apps, some terminal emulators, and other toolkits that do
  not support this input method.
- **GNOME Wayland.** The popup uses wlr-layer-shell for overlay positioning.
  GNOME does not support this protocol, so the popup falls back to a regular
  window with degraded positioning.
- **Uppercase multi-code-point variants.** A few precomposed letters uppercase
  to two code points (`ǰ` -> `J̌`). diacritter emits only the first code point,
  so a shifted selection of those letters drops the mark.

## Resilience

- **Daemon crashes** -- evdev releases the grab automatically (fd close), and
  the keyboard returns to normal.
- **Popup crashes** -- the daemon keeps working, and systemd restarts the popup.
- **Multiple keyboards** -- one state machine per device.
- **Panic key combo** -- press Backspace, Escape, and Enter in quick succession
  to force-exit the daemon and release the keyboard grab. This is a safety
  escape hatch if the daemon hangs.

## Security

diacritter uses EVIOCGRAB to exclusively grab keyboard input devices, the same
mechanism as keyd, kanata, and other input remapping daemons. The daemon has
full access to all keyboard input while it runs.

- The daemon runs as a user service, not as root.
- It only reads key events and emits diacritics through uinput.
- The IPC socket is owner-only (`0600`), and the daemon checks the peer uid with
  `SO_PEERCRED`.
- It rejects unsafe locale names, so a client cannot escape the locale
  directories.

This is the same trust model as keyd and kanata.

## Credits

- Original project: [accentd](https://github.com/gildo/accentd) by Ermenegildo
  Fiorito ([@gildo](https://github.com/gildo)).
- RPM spec adapted from the pull request by
  [Joshua Stone](https://github.com/joshua-stone).
- The `macos` lists come from Apple's `PressAndHold.plist`, cross-checked
  against the casouri gist and the TXOTY pressandhold project.

## License

MIT. See [LICENSE](LICENSE).

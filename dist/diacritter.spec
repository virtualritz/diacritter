# RPM spec adapted from the accentd spec by Joshua Stone <joshua.gage.stone@gmail.com>
# (upstream pull request "Add RPM spec file").
#
# Generate sources with the following:
# export TAG=0.1.0
# git clone --depth=1 --branch=v${TAG} https://github.com/virtualritz/diacritter diacritter-${TAG}/
# cd diacritter-${TAG}/ && cargo vendor && cd -
# tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner --pax-option='delete=atime,delete=ctime' -cvf diacritter-${TAG}.tar.gz diacritter-${TAG}/

# Setting up build dependencies can be done with the following:
# dnf install --setopt install_weak_deps=0 rpm-build
# dnf build-dep --setopt install_weak_deps=0 ./dist/diacritter.spec

Name:           diacritter
Version:        0.1.0
Release:        1%{?dist}
Summary:        Press-and-hold diacritic popup for Linux (macOS-style)

License:        MIT
URL:            https://github.com/virtualritz/diacritter

Source0:        %{url}/archive/v%{version}/%{name}-%{version}.tar.gz

Requires:       gtk4
Requires:       gtk4-layer-shell

BuildRequires:  cargo-rpm-macros
BuildRequires:  crate(cairo-rs)
BuildRequires:  crate(gdk-pixbuf)
BuildRequires:  crate(graphene-sys)
BuildRequires:  crate(gtk4-sys)
BuildRequires:  crate(pango)
BuildRequires:  crate(unicode-normalization)
BuildRequires:  gtk4-layer-shell-devel
BuildRequires:  systemd-rpm-macros


%description
Press-and-hold diacritic popup for Linux, like macOS.

Hold a letter key (e.g. 'e') for 300ms and a popup appears with numbered variants.

Press a number to replace the letter. Press ESC to cancel.

Works on any desktop environment and display server: GNOME, KDE, Sway, Hyprland, X11, Wayland. Operates at the evdev/uinput level, same as keyd and kanata.


%prep
%autosetup -n %{name}-%{version}
%cargo_prep -v vendor


%build
%cargo_build
%cargo_license_summary
%cargo_vendor_manifest


%install
install -Dm0755 target/release/diacritter       "%{buildroot}%{_bindir}/diacritter"
install -Dm0755 target/release/diacritterd      "%{buildroot}%{_bindir}/diacritterd"
install -Dm0755 target/release/diacritter-popup "%{buildroot}%{_bindir}/diacritter-popup"

install -Dm644 dist/diacritter.service       "%{buildroot}%{_userunitdir}/diacritter.service"
install -Dm644 dist/diacritter-popup.service "%{buildroot}%{_userunitdir}/diacritter-popup.service"
install -Dm644 dist/70-diacritter.rules      "%{buildroot}/usr/lib/udev/rules.d/70-diacritter.rules"

install -dm755 "%{buildroot}/%{_datadir}/%{NAME}/locales"
install -Dm644 data/locales/*.toml      "%{buildroot}/%{_datadir}/%{NAME}/locales/"
install -Dm644 data/config.default.toml "%{buildroot}/%{_datadir}/%{NAME}/config.default.toml"


%check
%cargo_test


%post
%systemd_user_post diacritter.service diacritter-popup.service

udevadm control --reload-rules ||:


%preun
%systemd_user_preun diacritter.service diacritter-popup.service


%postun
%systemd_user_postun_with_restart diacritter.service diacritter-popup.service

udevadm control --reload-rules ||:


%files
%license LICENSE
%license cargo-vendor.txt
%doc README.md
%{_bindir}/diacritter
%{_bindir}/diacritterd
%{_bindir}/diacritter-popup
%{_userunitdir}/diacritter.service
%{_userunitdir}/diacritter-popup.service
%config %{_datadir}/%{NAME}/locales/*.toml
%config %{_datadir}/%{NAME}/config.default.toml
/usr/lib/udev/rules.d/70-diacritter.rules

%changelog
* Sat Oct 11 2026 Moritz Moeller <virtualritz@protonmail.com> - 0.1.0-1
- Fork of accentd as diacritter. Add macOS/unicode locales, run as a user
  service, and use the diacritter/diacritterd/diacritter-popup binaries.
* Thu May 21 2026 Joshua Stone <joshua.gage.stone@gmail.com> - 0.2.1-1
- Initial package

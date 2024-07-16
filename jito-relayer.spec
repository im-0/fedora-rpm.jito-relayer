# Used only on x86_64:
#
# Available CPUs and features: `llc -march=x86-64 -mattr=help`.
# x86-64-v3 (close to Haswell):
#   AVX, AVX2, BMI1, BMI2, F16C, FMA, LZCNT, MOVBE, XSAVE
%global target_cpu x86-64-v3
%global target_cpu_mtune generic

Name:       jito-relayer
Version:    0.1.15
Release:    1%{?dist}
Summary:    Jito Foundation's Transaction Relayer

License:    Apache-2.0
URL:        https://github.com/jito-foundation/jito-relayer
Source0:    https://github.com/jito-foundation/jito-relayer/archive/v%{version}/%{name}-%{version}.tar.gz

# Contains jito-relayer-$VERSION/vendor/* plus git submodules.
#     $ cargo vendor
#     $ git submodule update --init --recursive --depth 1
#     $ mkdir jito-relayer-X.Y.Z
#     $ mv vendor jito-relayer-X.Y.Z/
#     $ mkdir jito-relayer-X.Y.Z/jito-protos
#     $ mv jito-protos/protos jito-relayer-X.Y.Z/jito-protos/
#     $ tar vcJf jito-relayer-X.Y.Z.cargo-vendor.tar.xz jito-relayer-X.Y.Z
Source1:    %{name}-%{version}.cargo-vendor.tar.xz

Source100:  config.toml
Source101:  jito-transaction-relayer@.service
Source102:  example.conf

ExclusiveArch:  %{rust_arches}

BuildRequires:  findutils
BuildRequires:  rust-packaging
BuildRequires:  systemd-rpm-macros
BuildRequires:  gcc
BuildRequires:  clang
BuildRequires:  make
BuildRequires:  pkgconf-pkg-config
BuildRequires:  protobuf-compiler >= 3.15.0
BuildRequires:  protobuf-devel >= 3.15.0
BuildRequires:  perl
BuildRequires:  systemd-devel


%description
Jito Relayer acts as a transaction processing unit (TPU) proxy for Solana
validators.


%prep
%setup -q -D -T -b0 -n %{name}-%{version}
%setup -q -D -T -b1 -n %{name}-%{version}

mkdir .cargo
cp %{SOURCE100} .cargo/config.toml

# Fix Fedora's shebang mangling errors:
#     *** ERROR: ./usr/src/debug/solana-testnet-1.10.0-1.fc35.x86_64/vendor/ascii/src/ascii_char.rs has shebang which doesn't start with '/' ([cfg_attr(rustfmt, rustfmt_skip)])
find . -type f -name "*.rs" -exec chmod 0644 "{}" ";"


%build
export PROTOC=/usr/bin/protoc
export PROTOC_INCLUDE=/usr/include

export CC=clang
export CXX=clang++

grep -q "^ *\[profile.release\] *$" Cargo.toml
grep -q "^ *lto *= *\"thin\" *$" Cargo.toml
sed -i "s,^\( *lto *= *\"\)thin\(\" *\)$,\1fat\2," Cargo.toml

# Check https://pagure.io/fedora-rust/rust2rpm/blob/main/f/data/macros.rust for
# rust-specific variables.
export RUSTC_BOOTSTRAP=1

%ifarch x86_64
%global cpu_cflags -march=%{target_cpu} -mtune=%{target_cpu_mtune}
%global cpu_rustflags -Ctarget-cpu=%{target_cpu}

export RUSTFLAGS='%{build_rustflags} -Ccodegen-units=1 -Copt-level=3 %{cpu_rustflags}'
export CFLAGS="-O3 %{cpu_cflags}"
export CXXFLAGS="-O3 %{cpu_cflags}"
export LDFLAGS="-O3 %{cpu_cflags}"
%else
export RUSTFLAGS='%{build_rustflags} -Ccodegen-units=1 -Copt-level=3'
export CFLAGS="-O3"
export CXXFLAGS="-O3"
export LDFLAGS="-O3"
%endif
cargo build %{__cargo_common_opts} --release --frozen


%install
mkdir -p %{buildroot}/opt/%{name}/bin
mkdir -p %{buildroot}/%{_unitdir}
mkdir -p %{buildroot}%{_sysconfdir}/%{name}

find ./target/release/ -mindepth 1 -maxdepth 1 -type d -exec rm -r "{}" \;
rm ./target/release/*.d
rm ./target/release/*.rlib

mv ./target/release/* \
        %{buildroot}/opt/%{name}/bin/

cp %{SOURCE101} %{buildroot}/%{_unitdir}/
cp %{SOURCE102} %{buildroot}%{_sysconfdir}/%{name}/


%files
%attr(0750,root,%{name}) %dir %{_sysconfdir}/%{name}
%dir /opt/%{name}
%dir /opt/%{name}/bin
/opt/%{name}/bin/jito-transaction-relayer
%{_unitdir}/jito-transaction-relayer@.service
%attr(0640,root,%{name}) %{_sysconfdir}/%{name}/example.conf


%pre
getent group %{name} >/dev/null || groupadd -r %{name}
getent passwd %{name} >/dev/null || \
        useradd -r -s /sbin/nologin -d /etc/%{name} -M \
        -c "Jito Foundation's Transaction Relayer" -g %{name} %{name}
exit 0


%post
%systemd_post jito-transaction-relayer@.service


%preun
%systemd_preun 'jito-transaction-relayer@*.service'


%postun
%systemd_postun 'jito-transaction-relayer@*.service'


%changelog
* Tue Jul 16 2024 Ivan Mironov <mironov.ivan@gmail.com> - 0.1.15-1
- Update to 0.1.15

* Tue May 14 2024 Ivan Mironov <mironov.ivan@gmail.com> - 0.1.14-1
- Update to 0.1.14

* Mon Apr 29 2024 Ivan Mironov <mironov.ivan@gmail.com> - 0.1.13-1
- Update to 0.1.13

* Wed Apr 17 2024 Ivan Mironov <mironov.ivan@gmail.com> - 0.1.12-1
- Update to 0.1.12

* Thu Apr 11 2024 Ivan Mironov <mironov.ivan@gmail.com> - 0.1.11-1
- Update to 0.1.11

* Sun Mar 31 2024 Ivan Mironov <mironov.ivan@gmail.com> - 0.1.8-1
- Update to 0.1.8

* Mon Mar 11 2024 Ivan Mironov <mironov.ivan@gmail.com> - 0.1.7-1
- Update to 0.1.7

* Fri Feb 23 2024 Ivan Mironov <mironov.ivan@gmail.com> - 0.1.6-1
- Update to 0.1.6

* Sat Feb 10 2024 Ivan Mironov <mironov.ivan@gmail.com> - 0.1.5-1
- Initial packaging

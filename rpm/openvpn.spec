Name:       openvpn

%{!?_pkgdocdir: %global _pkgdocdir %{_docdir}/%{name}-%{version}}

Summary:    A full-featured SSL VPN solution
Version:    2.4.5
Release:    1
Group:      Applications/Internet
License:    GPLv2
URL:        http://openvpn.net/
Source0:    http://swupdate.openvpn.org/community/releases/%{name}-%{version}.tar.xz
Requires:   iproute
Requires:   net-tools
Requires(pre): /usr/sbin/useradd
BuildRequires:  pkgconfig(openssl) >= 0.9.6
BuildRequires:  pkgconfig(libpkcs11-helper-1)
BuildRequires:  lzo-devel
BuildRequires:  pam-devel
BuildRequires:  iproute

%description
OpenVPN is a robust and highly flexible tunneling application that uses all
of the encryption, authentication, and certification features of the
OpenSSL library to securely tunnel IP networks over a single UDP or TCP
port.  It can use the Marcus Franz Xaver Johannes Oberhumer's LZO library
for compression.

%prep
%setup -q -n %{name}-%{version}/openvpn

%build

autoreconf -vfi

%configure --disable-static \
    --enable-password-save \
    --enable-iproute2 \
    --enable-plugins \
    --enable-plugin-down-root \
    --enable-plugin-auth-pam \
    --enable-x509-alt-username \
    --docdir=%{_pkgdocdir}

make %{?jobs:-j%jobs}


%install
rm -rf %{buildroot}
%make_install

rm -rf $RPM_BUILD_ROOT

install -d -m 0755 $RPM_BUILD_ROOT%{_sysconfdir}/%{name}

mkdir -p $RPM_BUILD_ROOT%{_datadir}/%{name}

%{__make} install DESTDIR=$RPM_BUILD_ROOT
find $RPM_BUILD_ROOT -name '*.la' | xargs rm -f

%check
# Test Crypto:
./src/openvpn/openvpn --genkey --secret key
./src/openvpn/openvpn --test-crypto --secret key
# Randomize ports for tests to avoid conflicts on the build servers.
cport=$[ 50000 + ($RANDOM % 15534) ]
sport=$[ $cport + 1 ]
sed -e 's/^\(rport\) .*$/\1 '$sport'/' \
-e 's/^\(lport\) .*$/\1 '$cport'/' \
< sample/sample-config-files/loopback-client \
> %{_tmppath}/%{name}-%{version}-%{release}-%(%{__id_u})-loopback-client
sed -e 's/^\(rport\) .*$/\1 '$cport'/' \
-e 's/^\(lport\) .*$/\1 '$sport'/' \
< sample/sample-config-files/loopback-server \
> %{_tmppath}/%{name}-%{version}-%{release}-%(%{__id_u})-loopback-server

pushd sample
# Test SSL/TLS negotiations (runs for 2 minutes):
../src/openvpn/openvpn --config \
%{_tmppath}/%{name}-%{version}-%{release}-%(%{__id_u})-loopback-client &
../src/openvpn/openvpn --config \
%{_tmppath}/%{name}-%{version}-%{release}-%(%{__id_u})-loopback-server
wait
popd

rm -f %{_tmppath}/%{name}-%{version}-%{release}-%(%{__id_u})-loopback-client \
%{_tmppath}/%{name}-%{version}-%{release}-%(%{__id_u})-loopback-server

%pre
getent group openvpn >/dev/null 2>&1 || groupadd -r openvpn || :
getent passwd openvpn >/dev/null 2>&1 || /usr/sbin/useradd -r -g openvpn -s /sbin/nologin -c OpenVPN -d /etc/openvpn openvpn || :

%files
%defattr(-,root,root,0755)
%{_pkgdocdir}
%exclude %{_pkgdocdir}/README.IPv6
%exclude %{_pkgdocdir}/README.mbedtls
%exclude %{_pkgdocdir}/management-notes.txt
%{_sbindir}/%{name}
%{_includedir}/openvpn-plugin.h
%{_includedir}/openvpn-msg.h
%{_libdir}/%{name}/
%config %dir %{_sysconfdir}/%{name}/
%exclude %{_mandir}/man8/%{name}.8*


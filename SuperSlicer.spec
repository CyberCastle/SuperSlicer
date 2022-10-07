#
# spec file for package SuperSlicer
#
# Copyright (c) 2022 SUSE LLC
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via https://bugs.opensuse.org/
#


%define __builder ninja
Name:           SuperSlicer
Version:        2.4.58.3+149.ge74cb02c1
Release:        0
Summary:        G-code generator for 3D printers (RepRap, Makerbot, Ultimaker etc.)
License:        AGPL-3.0-only
Group:          Hardware/Printing
URL:            https://github.com/supermerill/SuperSlicer
Source0:        SuperSlicer-%{version}.tar.xz
# PATCH-FIX-UPSTREAM PrusaSlicer-boost1.79.patch -- gh#prusa3d/PrusaSlicer#8238
Patch0:         PrusaSlicer-boost1.79.patch
Patch1:         PrusaSlicer-cereal.patch
Patch2:         fix-wx-locale.patch
Patch11:        fix-gcodeviewer-simlink.patch
Patch12:        fix-6396.patch
BuildRequires:  blosc-devel
BuildRequires:  cereal-devel
BuildRequires:  cgal-devel >= 4.13.2
BuildRequires:  cmake
BuildRequires:  dbus-1-devel
BuildRequires:  eigen3-devel >= 3
BuildRequires:  expat
BuildRequires:  fdupes
BuildRequires:  gcc-c++
BuildRequires:  gtest >= 1.7
BuildRequires:  hicolor-icon-theme
BuildRequires:  ilmbase-devel
BuildRequires:  libboost_atomic-devel
BuildRequires:  libboost_filesystem-devel
BuildRequires:  libboost_iostreams-devel
BuildRequires:  libboost_locale-devel
BuildRequires:  libboost_log-devel
BuildRequires:  libboost_regex-devel
BuildRequires:  libboost_system-devel
BuildRequires:  libboost_thread-devel
BuildRequires:  libcurl-devel
BuildRequires:  libexpat-devel
BuildRequires:  libudev-devel
BuildRequires:  memory-constraints
BuildRequires:  ninja
BuildRequires:  nlopt-devel
BuildRequires:  openvdb-devel >= 5
BuildRequires:  tbb-devel
BuildRequires:  update-desktop-files
BuildRequires:  wxGTK3-devel >= 3.1
BuildRequires:  zlib-devel-static
# For now, use bundled GLEW because of gh#prusa3d/PrusaSlicer#6396
#!BuildIgnore:  glew-devel

%description
SuperSlicer takes 3D models (STL, OBJ, AMF) and converts them into G-code
instructions for FFF printers or PNG layers for mSLA 3D printers. It's
compatible with any modern printer based on the RepRap toolchain, including
all those based on the Marlin, Prusa, Sprinter and Repetier firmware.
It also works with Mach3, LinuxCNC and Machinekit controllers.

%prep
%autosetup -p1 -n %{name}-%{version}
%if 0%{?suse_version}
sed -i 's/UNKNOWN/%{release}-%{?is_opensuse:open}SUSE-0%{?suse_version}/' version.inc
%endif

%build
%limit_build -m 4096
# sse2 flags: see upstream github issue#3781
%cmake -DSLIC3R_FHS=1 \
       -DSLIC3R_BUILD_TESTS=0 \
       -DSLIC3R_GTK=3 \
       -DSLIC3R_WX_STABLE=0 \
       -DOPENVDB_FIND_MODULE_PATH=%{_libdir}/cmake/OpenVDB \
%ifarch i686 i586 i386
       -DCMAKE_C_FLAGS:STRING="%{optflags} -mfpmath=sse -msse2" \
       -DCMAKE_CXX_FLAGS:STRING="%{optflags}  -mfpmath=sse -msse2"
%endif

%cmake_build
%cmake_build gettext_po_to_mo

%install
%cmake_install

%if 0%{?suse_version} > 1500
    %suse_update_desktop_file -i %{name}
    %suse_update_desktop_file -i %{name}-Gcodeviewer
%else
    # Non Tumbleweed versions do not like the chosen categories
    %suse_update_desktop_file -i -r %{name} Graphics 3DGraphics
    %suse_update_desktop_file -i -r %{name}-Gcodeviewer Graphics 3DGraphics
%endif

rm -rf %{buildroot}%{_prefix}/lib/cmake/Angelscript
rm -rf %{buildroot}%{_includedir}
rm -rf %{buildroot}%{_prefix}/lib/libangelscript.a
#
rm -rf %{buildroot}%{_datadir}/%{name}/data
rm -rf %{buildroot}%{_datadir}/%{name}/applications

# Copied and adapted from Fedora package:
# https://src.fedoraproject.org/rpms/prusa-slicer
# Upstream installs the translation source files when they probably shouldn't
rm %{buildroot}%{_datadir}/%{name}/localization/{README.md,list.txt,pom_merger.py,settings.ini,update_all.py}
find %{buildroot}%{_datadir}/%{name}/localization/ -name \*.po -delete
find %{buildroot}%{_datadir}/%{name}/localization/ -name settings.ini -delete

# Copied and adapted from Fedora package:
# https://src.fedoraproject.org/rpms/prusa-slicer
# Handle locale files.  The find_lang macro doesn't work because it doesn't
# understand the directory structure.  This copies part of the funtionality of
# find-lang.sh by:
#   * Getting a listing of all files
#   * removing the buildroot prefix
#   * inserting the proper 'lang' tag
#   * removing everything that doesn't have a lang tag
#   * A list of lang-specific directories is also added
# The resulting file is included in the files list, where we must be careful to
# exclude that directory.
 find %{buildroot}%{_datadir}/%{name}/localization -type f -o -type l | sed '
     s:'"%{buildroot}"'::
     s:\(.*/%{name}/localization/\)\([^/_]\+\)\(.*\.mo$\):%%lang(\2) \1\2\3:
     s:^\([^%].*\)::
     s:%lang(C) ::
     /^$/d
 ' > lang-files
 find %{buildroot}%{_datadir}/%{name}/localization -type d | sed '
     s:'"%{buildroot}"'::
     s:\(.*\):%dir \1:
 ' >> lang-files

%fdupes %{buildroot}%{_datadir}

%files -f lang-files
%{_bindir}/superslicer*
%dir %{_datadir}/%{name}/
%{_prefix}/lib/udev/rules.d/90-3dconnexion.rules
%{_datadir}/%{name}/{fonts,icons,models,profiles,shaders,udev,ui_layout,calibration,splashscreen,shapes}/
%{_datadir}/icons/hicolor/*/apps/%{name}*.png
%{_datadir}/applications/%{name}*.desktop
%license LICENSE
%doc README.md doc/

%changelog

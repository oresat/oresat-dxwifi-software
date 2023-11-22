#!/bin/bash
set -x
PKG_NAME=oresat-dxwifi-software-server
PKG_VERS=0.0.0.2
VCAN_SERVICE=oresat-vcan-iface.service
MON_SERVICE=oresat-mon-iface.service
PY3_VERS='3.9.2-3'
PIP3_VERS='20.3.4-4+deb11u1'
PYBIND_VERS='2.6.2-1'
ARCH=$(dpkg --print-architecture)
function err_exit(){
  echo "Error: There was an issue with $*, exiting." >&2
  exit 1;
}
mkdir -p $PKG_NAME-$PKG_VERS/{DEBIAN,usr/local/sbin/,lib/systemd/system,oresat-live-output/{frames,videos}} || err_exit "making the dkpg-deb dirs"
sudo chown -Rf root:root $PKG_NAME-$PKG_VERS/oresat-live-output/{frames,videos} || err_exit "chowning output dir to root:root"
sh -c "cat > $PKG_NAME-$PKG_VERS/DEBIAN/control <<EOF
Architecture: $ARCH
Depends: pybind11-dev (=$PYBIND_VERS), python3-pip  (=$PIP3_VERS), python3 (=$PY3_VERS)
Description: Oresat DXWIFI Software Server: serves video via CAN bus
Homepage: https://github.com/oresat/oresat-dxwifi-software
Maintainer: PSAS <oresat@pdx.edu>
Package: $PKG_NAME
Priority: optional
Section: net
Version: $PKG_VERS
EOF" || err_exit "writing to DEBIAN control file"
sh -c "cat > $PKG_NAME-$PKG_VERS/DEBIAN/postinst <<EOF
#!/bin/sh
set -e
if [ \"\\\$1\" = \"configure\" ]; then
    # Enable and start the systemd services
    systemctl daemon-reload
    systemctl enable $VCAN_SERVICE
    systemctl start $VCAN_SERVICE
    systemctl enable $MON_SERVICE
    systemctl start $MON_SERVICE
    systemctl enable ${PKG_NAME}.service
    systemctl start $PKG_NAME.service
fi
EOF" || err_exit "writing to DEBIAN postinst file"
chmod 755 $PKG_NAME-$PKG_VERS/DEBIAN/postinst || err_exit "chmodding the postinst file"
cp -ar kill-olaf start-vcan oresat_dxwifi/ $PKG_NAME-$PKG_VERS/usr/local/sbin || err_exit "copying service files to destination dir usr/local/sbin"
cp $VCAN_SERVICE $MON_SERVICE $PKG_NAME.service $PKG_NAME-$PKG_VERS/lib/systemd/system/ || err_exit "copying systemd service files to destination dir lib/systemd/system/"
dpkg-deb --build $PKG_NAME-$PKG_VERS/  || err_exit "dpkg-deb"
set +x

#!/bin/bash
set -x

PKG_NAME="oresat-dxwifi-software-server"
PKG_VERS="0.0.0.6"
VCAN_SERVICE="oresat-vcan-iface.service"
MON_SERVICE="oresat-mon-iface.service"

# @TODO Try to avoid such strict dependencies, as they may interact negatively
#       with other systems.
PY3_VERS="3.9.2-3"
PIP3_VERS="20.3.4-4+deb11u1"
PYBIND_VERS="2.6.2-1"

ARCH=$(dpkg --print-architecture)

DEBIAN_DIR="DEBIAN"
SBIN_DIR="usr/local/sbin"
SYSTEMD_DIR="lib/systemd/system"

OUTPUT_DIR="oresat-live-output"
FRAME_DIR="$OUTPUT_DIR/frames"
VIDEO_DIR="$OUTPUT_DIR/videos"

function err_exit(){
  echo "Error: There was an issue with $*, exiting." >&2
  exit 1;
}

for d in "$DEBIAN_DIR" "$SBIN_DIR" "$SYSTEMD_DIR" "$FRAME_DIR" "$VIDEO_DIR"; do
    mkdir -p "$PKG_NAME-$PKG_VERS/$d" || err_exit "making the dkpg-deb dirs"
done

for d in "$FRAME_DIR" "$VIDEO_DIR"; do
    sudo chown -Rf root:root "$PKG_NAME-$PKG_VERS/$d" \
    || err_exit "chowning output dir to root:root"
done

sh -c "cat > $PKG_NAME-$PKG_VERS/$DEBIAN_DIR/control <<EOF
Architecture: $ARCH
Depends: pybind11-dev (=$PYBIND_VERS), python3-pip (=$PIP3_VERS), python3 (=$PY3_VERS)
Description: Oresat DXWIFI Software Server: serves video via CAN bus
Homepage: https://github.com/oresat/oresat-dxwifi-software
Maintainer: PSAS <oresat@pdx.edu>
Package: $PKG_NAME
Priority: optional
Section: net
Version: $PKG_VERS
EOF" || err_exit "writing to DEBIAN control file"

sh -c "cat > $PKG_NAME-$PKG_VERS/$DEBIAN_DIR/postinst <<EOF
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

chmod 755 "$PKG_NAME-$PKG_VERS/$DEBIAN_DIR/postinst" \
    || err_exit "chmodding the postinst file"

cp -ar startmonitor.sh kill-olaf start-vcan oresat_dxwifi/ \
    "$PKG_NAME-$PKG_VERS/$SBIN_DIR" \
    || err_exit "copying service files to destination dir $SBIN_DIR"

cp "$VCAN_SERVICE" "$MON_SERVICE" "$PKG_NAME.service" \
    "$PKG_NAME-$PKG_VERS/$SYSTEMD_DIR" \
    || err_exit "copying systemd service files to destination dir $SYSTEMD_DIR"

dpkg-deb --build "$PKG_NAME-$PKG_VERS/" || err_exit "dpkg-deb"

set +x

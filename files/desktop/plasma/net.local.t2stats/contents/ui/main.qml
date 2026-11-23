// Managed by t2-mac-kde (desktop). Compact panel items as in iStat Menus, one per mode:
//   cpu / mem: bar history of the last minute + label over percent
//   net:       upload over download ("12 KB/s", "1.4 MB/s")
//   temp:      hottest CPU sensor as a number, coloured as Waybar's hypr-thermal (85 / 95 °C)
// Fixed widths, so the panel doesn't shift as the numbers change.
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.components as PC3
import org.kde.kirigami as Kirigami
import org.kde.ksysguard.sensors as Sensors

PlasmoidItem {
    id: root
    readonly property string mode: Plasmoid.configuration.mode
    readonly property int samples: 30          // 30 x 2 s = the last minute
    property var history: []

    preferredRepresentation: fullRepresentation
    toolTipMainText: ({cpu: "CPU", mem: "Memory", net: "Network", temp: "CPU temperature"})[mode] || mode
    toolTipSubText: mode == "net" ? "↑ " + up.formattedValue + "   ↓ " + down.formattedValue
                                  : main.formattedValue

    Sensors.Sensor {
        id: main
        sensorId: ({cpu: "cpu/all/usage", mem: "memory/physical/usedPercent",
                    temp: "cpu/all/maximumTemperature"})[root.mode] || ""
        updateRateLimit: 2000
    }
    Sensors.Sensor { id: up; sensorId: root.mode == "net" ? "network/all/upload" : ""; updateRateLimit: 1000 }
    Sensors.Sensor { id: down; sensorId: root.mode == "net" ? "network/all/download" : ""; updateRateLimit: 1000 }

    Timer {
        running: root.mode == "cpu" || root.mode == "mem"
        interval: 2000; repeat: true; triggeredOnStart: true
        onTriggered: {
            var h = root.history.slice(-(root.samples - 1));
            h.push(Math.max(0, Math.min(100, main.value || 0)));
            root.history = h;
        }
    }

    // iStat style: "0 KB/s", "12 KB/s", "1.4 MB/s", "35 MB/s" (at most 3 digits)
    function rate(bytes) {
        var units = ["KB/s", "MB/s", "GB/s"], v = Math.max(0, bytes || 0) / 1024, i = 0;
        while (v >= 1000 && i < units.length - 1) { v /= 1024; i++; }
        return (v < 10 && i > 0 ? v.toLocaleString(Qt.locale(), "f", 1) : Math.round(v)) + " " + units[i];
    }
    // hypr-thermal's classes: warning from 85 °C, critical from 95 °C
    function tempColor(t) {
        return t >= 95 ? "#c0605a" : t >= 85 ? "#a87a2f" : Kirigami.Theme.textColor;
    }

    fullRepresentation: Item {
        id: rep
        readonly property int px: Math.max(8, Math.floor(height * 0.36))
        readonly property bool graph: root.mode == "cpu" || root.mode == "mem"
        Layout.minimumWidth: row.implicitWidth + 4
        Layout.preferredWidth: Layout.minimumWidth
        Layout.fillHeight: true

        TextMetrics { id: rateWidth; font.pixelSize: rep.px; text: "999 KB/s" }
        TextMetrics { id: pctWidth; font.pixelSize: rep.px; text: "100%" }

        RowLayout {
            id: row
            anchors.centerIn: parent
            spacing: 3

            // bar history: one column per sample, newest on the right
            Rectangle {
                visible: rep.graph
                Layout.preferredWidth: root.samples + 2
                Layout.preferredHeight: Math.round(rep.height * 0.7)
                color: "transparent"
                border.width: 1
                border.color: Qt.rgba(Kirigami.Theme.textColor.r, Kirigami.Theme.textColor.g, Kirigami.Theme.textColor.b, 0.25)
                Row {
                    anchors { right: parent.right; bottom: parent.bottom; margins: 1 }
                    Repeater {
                        model: root.history
                        Rectangle {
                            width: 1
                            anchors.bottom: parent.bottom
                            height: Math.max(modelData > 0 ? 1 : 0, Math.round((rep.height * 0.7 - 2) * modelData / 100))
                            color: root.mode == "cpu" ? "#3daee9" : "#6fae5c"
                        }
                    }
                }
            }
            // label over value (cpu, mem)
            ColumnLayout {
                visible: rep.graph
                spacing: 0
                PC3.Label { text: root.mode.toUpperCase(); font.pixelSize: rep.px; opacity: 0.7 }
                PC3.Label {
                    text: Math.round(main.value || 0) + "%"; font.pixelSize: rep.px
                    horizontalAlignment: Text.AlignRight; Layout.preferredWidth: pctWidth.width
                }
            }
            // upload over download (net)
            GridLayout {
                visible: root.mode == "net"
                columns: 2; rowSpacing: 0; columnSpacing: 2
                PC3.Label { text: "↑"; color: "#e9783d"; font.pixelSize: rep.px; font.bold: true }
                PC3.Label { text: root.rate(up.value); font.pixelSize: rep.px
                            horizontalAlignment: Text.AlignRight; Layout.preferredWidth: rateWidth.width }
                PC3.Label { text: "↓"; color: "#3daee9"; font.pixelSize: rep.px; font.bold: true }
                PC3.Label { text: root.rate(down.value); font.pixelSize: rep.px
                            horizontalAlignment: Text.AlignRight; Layout.preferredWidth: rateWidth.width }
            }
            // number only (temp)
            PC3.Label {
                visible: root.mode == "temp"
                text: Math.round(main.value || 0) + "°"
                color: root.tempColor(main.value || 0)
                font.pixelSize: Math.round(rep.px * 1.3)
            }
        }
    }
}

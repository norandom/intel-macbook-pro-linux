// Managed by t2-mac-kde (desktop). The rabbit in KDE's panel, as in Waybar: click = choose a
// screen filter, right-click = off. hypr-nightmode stores the choice (shared with Hyprland);
// the t2rabbit KWin effect draws it. Colours as Waybar's #custom-nightmode.
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.components as PC3
import org.kde.plasma.extras as PlasmaExtras
import org.kde.plasma.plasma5support as P5Support
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: root
    property string mode: "off"
    readonly property string tool: "$HOME/.local/bin/hypr-nightmode"
    readonly property var modes: [
        ["off", "Off — original colors"], ["green", "Green — night filter"],
        ["dark", "Dark — reduced glare"], ["grayscale", "Grayscale — smooth gray"],
        ["monochrome", "Retro LCD — charcoal / gray-green"], ["warmwhite", "Warm whites — muted cream"]]
    // rabbit colour and background per mode (waybar style.css)
    readonly property var look: ({
        off: [Kirigami.Theme.textColor, "transparent"], green: ["#3a8e6f", "transparent"],
        dark: ["#fff8f0", "#1a2a3f"], grayscale: ["#444444", "#dddddd"],
        monochrome: ["#1f2b21", "#bac4a3"], warmwhite: ["#79522b", "#fff2d6"]})

    preferredRepresentation: fullRepresentation
    toolTipMainText: "Screen filter"
    toolTipSubText: (modes.find(m => m[0] == mode) || modes[0])[1] + "\nclick: choose / right-click: off"

    P5Support.DataSource {
        id: shell
        engine: "executable"
        interval: 0
        onNewData: (source, data) => {
            if (source.indexOf("cat ") == 0) {
                var m = (data.stdout || "").trim();
                root.mode = root.look[m] ? m : "off";
            }
            disconnectSource(source);
        }
    }
    function readMode() { shell.connectSource("cat \"$HOME/.local/state/hypr-nightmode\" 2>/dev/null || echo off"); }
    function setMode(m) {
        root.mode = m;
        shell.connectSource("sh -c '" + tool + " " + m + "' #" + Date.now());
    }
    Timer { interval: 2000; running: true; repeat: true; triggeredOnStart: true; onTriggered: root.readMode() }

    fullRepresentation: Item {
        Layout.minimumWidth: Math.round(height * 1.1)
        Layout.preferredWidth: Layout.minimumWidth
        Layout.fillHeight: true
        Rectangle {
            anchors.fill: parent
            anchors.margins: 2
            radius: 3
            color: root.look[root.mode][1]
            border.width: root.mode == "monochrome" ? 1 : 0
            border.color: "#1f2b21"
        }
        PC3.Label {
            anchors.centerIn: parent
            text: "\u{F0907}"          // nf-md-rabbit, as in Waybar
            font.family: "FiraCode Nerd Font"
            font.pixelSize: Math.round(parent.height * 0.55)
            color: root.look[root.mode][0]
        }
        MouseArea {
            id: area
            anchors.fill: parent
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            onClicked: (mouse) => {
                if (mouse.button == Qt.RightButton) root.setMode("off");
                else menu.openRelative();
            }
        }
        // a native popup menu (a Qt Quick Menu would be clipped to the panel's window)
        PlasmaExtras.Menu {
            id: menu
            visualParent: area
            placement: PlasmaExtras.Menu.BottomPosedLeftAlignedPopup
            PlasmaExtras.MenuItem {
                text: root.modes[0][1] + (root.mode == root.modes[0][0] ? "  ✓" : "")
                onClicked: root.setMode(root.modes[0][0])
            }
            PlasmaExtras.MenuItem {
                text: root.modes[1][1] + (root.mode == root.modes[1][0] ? "  ✓" : "")
                onClicked: root.setMode(root.modes[1][0])
            }
            PlasmaExtras.MenuItem {
                text: root.modes[2][1] + (root.mode == root.modes[2][0] ? "  ✓" : "")
                onClicked: root.setMode(root.modes[2][0])
            }
            PlasmaExtras.MenuItem {
                text: root.modes[3][1] + (root.mode == root.modes[3][0] ? "  ✓" : "")
                onClicked: root.setMode(root.modes[3][0])
            }
            PlasmaExtras.MenuItem {
                text: root.modes[4][1] + (root.mode == root.modes[4][0] ? "  ✓" : "")
                onClicked: root.setMode(root.modes[4][0])
            }
            PlasmaExtras.MenuItem {
                text: root.modes[5][1] + (root.mode == root.modes[5][0] ? "  ✓" : "")
                onClicked: root.setMode(root.modes[5][0])
            }
        }
    }
}

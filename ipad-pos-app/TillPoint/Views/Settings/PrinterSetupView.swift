import SwiftUI

struct PrinterSetupView: View {
    @EnvironmentObject private var printerManager: BluetoothPrinterManager

    var body: some View {
        List {
            Section("Status") {
                HStack {
                    Text("Bluetooth")
                    Spacer()
                    Text(printerManager.isBluetoothPoweredOn ? "On" : "Off")
                        .foregroundStyle(printerManager.isBluetoothPoweredOn ? .green : .red)
                }
                HStack {
                    Text("Printer")
                    Spacer()
                    Text(connectionLabel)
                        .foregroundStyle(printerManager.connectionState == .connected ? .green : .secondary)
                }
            }

            Section {
                Button(printerManager.isScanning ? "Scanning\u{2026}" : "Scan for Printers") {
                    printerManager.startScan()
                }
                .disabled(!printerManager.isBluetoothPoweredOn || printerManager.isScanning)

                ForEach(printerManager.discoveredPrinters) { printer in
                    Button {
                        printerManager.connect(to: printer)
                    } label: {
                        HStack {
                            Text(printer.name)
                            Spacer()
                            if printerManager.connectedPrinter?.id == printer.id {
                                Image(systemName: "checkmark.circle.fill").foregroundStyle(.green)
                            }
                        }
                    }
                }
            } header: {
                Text("Nearby Devices")
            } footer: {
                Text("Pair your BLE thermal printer here. Most budget 58mm/80mm Bluetooth Low Energy printers work without any special pairing in iOS Settings \u{2014} just select them here. The cash drawer connects to the printer's drawer port (RJ11) and is triggered automatically by the printer.")
            }

            if printerManager.connectionState == .connected {
                Section("Test") {
                    Button("Test Print") { testPrint() }
                    Button("Test Open Cash Drawer") { printerManager.openCashDrawer() }
                    Button("Disconnect", role: .destructive) { printerManager.disconnect() }
                }
            }

            if let error = printerManager.lastError {
                Section("Error") {
                    Text(error).foregroundStyle(.red)
                }
            }
        }
        .navigationTitle("Printer & Cash Drawer")
    }

    private var connectionLabel: String {
        switch printerManager.connectionState {
        case .disconnected: return "Not connected"
        case .connecting: return "Connecting\u{2026}"
        case .connected: return printerManager.connectedPrinter?.name ?? "Connected"
        case .failed(let message): return "Failed: \(message)"
        }
    }

    private func testPrint() {
        var bytes: [UInt8] = []
        bytes += ESCPOS.initializePrinter
        bytes += ESCPOS.alignCenter
        bytes += ESCPOS.boldOn
        bytes += ESCPOS.line("TillPoint Test Print")
        bytes += ESCPOS.boldOff
        bytes += ESCPOS.line("If you can read this, your")
        bytes += ESCPOS.line("printer is connected correctly.")
        bytes += ESCPOS.lineFeed(3)
        bytes += ESCPOS.cutPaperPartial
        printerManager.send(bytes)
    }
}

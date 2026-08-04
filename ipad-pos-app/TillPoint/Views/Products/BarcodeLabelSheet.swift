import SwiftUI

struct BarcodeLabelSheet: View {
    let code: String
    let productName: String

    @EnvironmentObject private var printerManager: BluetoothPrinterManager
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            VStack(spacing: 20) {
                Text(productName).font(.headline)
                if let image = BarcodeGenerator.code128Image(from: code) {
                    Image(uiImage: image)
                        .interpolation(.none)
                        .resizable()
                        .frame(width: 280, height: 100)
                }
                Text(code).font(.system(.body, design: .monospaced))

                Button {
                    printLabel()
                } label: {
                    Label("Print Label", systemImage: "printer")
                        .frame(maxWidth: .infinity)
                        .padding()
                }
                .buttonStyle(.borderedProminent)
                .disabled(printerManager.connectionState != .connected)
            }
            .padding()
            .navigationTitle("Barcode Label")
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }
                }
            }
        }
    }

    private func printLabel() {
        var bytes: [UInt8] = []
        bytes += ESCPOS.initializePrinter
        bytes += ESCPOS.alignCenter
        bytes += ESCPOS.line(productName)
        bytes += ESCPOS.barcodeCode128(code)
        bytes += ESCPOS.lineFeed(3)
        bytes += ESCPOS.cutPaperPartial
        printerManager.send(bytes)
    }
}
